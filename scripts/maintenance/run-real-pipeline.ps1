[CmdletBinding()]
param(
  [switch]$ResetRuntime,
  [switch]$ReseedProperties,
  [switch]$SkipStart9Router
)

$ErrorActionPreference = "Stop"

function Write-Step($message) {
  Write-Host ""
  Write-Host "==> $message" -ForegroundColor Cyan
}

function Load-DotEnv([string]$path) {
  if (-not (Test-Path -LiteralPath $path)) {
    throw "Missing .env file: $path"
  }

  Get-Content -LiteralPath $path | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) {
      return
    }

    $parts = $line -split "=", 2
    $key = $parts[0].Trim()
    $value = $parts[1].Trim().Trim("'`"")
    if ($key) {
      [Environment]::SetEnvironmentVariable($key, $value, "Process")
    }
  }
}

function Resolve-ToolPath([string]$commandName, [string]$fallbackPath) {
  $command = Get-Command $commandName -ErrorAction SilentlyContinue
  if ($command) {
    return $command.Source
  }
  if (Test-Path -LiteralPath $fallbackPath) {
    return $fallbackPath
  }
  throw "Required tool not found: $commandName"
}

function Test-HttpOk([string]$url, [int]$timeoutSec = 5) {
  try {
    $response = Invoke-WebRequest -UseBasicParsing $url -TimeoutSec $timeoutSec
    return $response.StatusCode -ge 200 -and $response.StatusCode -lt 300
  } catch {
    return $false
  }
}

function Wait-ForHttp([string]$url, [int]$timeoutSec = 30) {
  $deadline = (Get-Date).AddSeconds($timeoutSec)
  while ((Get-Date) -lt $deadline) {
    if (Test-HttpOk -url $url -timeoutSec 5) {
      return $true
    }
    Start-Sleep -Seconds 1
  }
  return $false
}

function Ensure-ProcessStopped([string]$pidFilePath) {
  if (-not (Test-Path -LiteralPath $pidFilePath)) {
    return
  }

  $pidValue = (Get-Content -LiteralPath $pidFilePath -Raw).Trim()
  if (-not $pidValue) {
    Remove-Item -LiteralPath $pidFilePath -Force -ErrorAction SilentlyContinue
    return
  }

  $proc = Get-Process -Id ([int]$pidValue) -ErrorAction SilentlyContinue
  if ($proc) {
    Stop-Process -Id $proc.Id -Force -ErrorAction Stop
    Start-Sleep -Seconds 1
  }

  Remove-Item -LiteralPath $pidFilePath -Force -ErrorAction SilentlyContinue
}

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$envPath = Join-Path $repoRoot ".env"
$migrationPath = Join-Path $repoRoot "infra\postgres\migrations\001_initial.sql"
$workerRoot = Join-Path $repoRoot "apps\ai-worker"
$collectorRoot = Join-Path $repoRoot "apps\zalo-collector"
$seedScript = Join-Path $workerRoot "scripts\seed_properties_from_csv.py"
$routerServer = Join-Path $env:APPDATA "npm\node_modules\9router\app\server.js"
$routerDb = Join-Path $env:APPDATA "9router\db.json"
$logsDir = Join-Path $repoRoot "var\logs"
$runDir = Join-Path $repoRoot "var\run"
$workerOutLog = Join-Path $logsDir "ai-worker.out.log"
$workerErrLog = Join-Path $logsDir "ai-worker.err.log"
$collectorLog = Join-Path $logsDir "zalo-collector.log"
$routerOutLog = Join-Path $logsDir "9router.out.log"
$routerErrLog = Join-Path $logsDir "9router.err.log"
$workerPidFile = Join-Path $runDir "ai-worker.pid"
$routerPidFile = Join-Path $runDir "9router.pid"

New-Item -ItemType Directory -Force -Path $logsDir | Out-Null
New-Item -ItemType Directory -Force -Path $runDir | Out-Null

Load-DotEnv $envPath

$databaseUrl = $env:DATABASE_URL
if (-not $databaseUrl) {
  throw "DATABASE_URL is missing in .env"
}

$python = Resolve-ToolPath "python.exe" "C:\Users\Admin\AppData\Local\Python\pythoncore-3.14-64\python.exe"
$node = Resolve-ToolPath "node.exe" "C:\Program Files\nodejs\node.exe"
$npm = Resolve-ToolPath "npm.cmd" "C:\Program Files\nodejs\npm.cmd"
$psql = Resolve-ToolPath "psql.exe" "C:\Program Files\PostgreSQL\18\bin\psql.exe"

Write-Step "Checking local toolchain"
Write-Host "python : $python"
Write-Host "node   : $node"
Write-Host "npm    : $npm"
Write-Host "psql   : $psql"

& $python -c "import psycopg, httpx, rapidfuzz, pydantic, pydantic_settings; print('python deps ok')"

if (-not (Test-Path -LiteralPath (Join-Path $collectorRoot "node_modules"))) {
  throw "Collector dependencies are missing. Run npm install in apps/zalo-collector first."
}

if (-not $SkipStart9Router) {
  Write-Step "Ensuring 9router is running"
  if (-not (Test-HttpOk "http://127.0.0.1:20128/v1/models")) {
    if (-not (Test-Path -LiteralPath $routerServer)) {
      throw "9router is not installed. Install it first, then rerun."
    }

    Ensure-ProcessStopped $routerPidFile

    $routerProc = Start-Process -FilePath $node `
      -ArgumentList @($routerServer) `
      -PassThru `
      -WindowStyle Hidden `
      -RedirectStandardOutput $routerOutLog `
      -RedirectStandardError $routerErrLog

    Set-Content -LiteralPath $routerPidFile -Value $routerProc.Id

    if (-not (Wait-ForHttp "http://127.0.0.1:20128/v1/models" 30)) {
      throw "9router did not become ready on http://127.0.0.1:20128/v1/models"
    }
  }

  Write-Host "9router API is reachable at http://127.0.0.1:20128/v1"

  if (Test-Path -LiteralPath $routerDb) {
    $routerState = Get-Content -LiteralPath $routerDb -Raw | ConvertFrom-Json
    $providerCount = @($routerState.providerConnections).Count + @($routerState.providerNodes).Count + @($routerState.proxyPools).Count
    if ($providerCount -eq 0) {
      throw "9router is running but has no connected providers. Open http://localhost:20128/dashboard and connect one provider before testing the real flow."
    }
  }
}

Write-Step "Applying schema migration"
& $psql $databaseUrl -v ON_ERROR_STOP=1 -f $migrationPath | Out-Host

if ($ReseedProperties) {
  Write-Step "Resetting runtime tables and properties"
  & $psql $databaseUrl -v ON_ERROR_STOP=1 -c "TRUNCATE TABLE deal_rooms, hotel_deals, rejected_deals, match_attempts, ai_call_logs, processing_events, raw_messages, properties RESTART IDENTITY CASCADE;" | Out-Host
} elseif ($ResetRuntime) {
  Write-Step "Resetting runtime tables"
  & $psql $databaseUrl -v ON_ERROR_STOP=1 -c "TRUNCATE TABLE deal_rooms, hotel_deals, rejected_deals, match_attempts, ai_call_logs, processing_events, raw_messages RESTART IDENTITY CASCADE;" | Out-Host
}

$propertyCount = (& $psql $databaseUrl -t -A -c "SELECT COUNT(*) FROM properties;").Trim()
if ($ReseedProperties -or $propertyCount -eq "0") {
  Write-Step "Seeding properties"
  Push-Location $workerRoot
  try {
    & $python $seedScript
  } finally {
    Pop-Location
  }
  $propertyCount = (& $psql $databaseUrl -t -A -c "SELECT COUNT(*) FROM properties;").Trim()
}

Write-Step "Starting ai-worker in background"
Ensure-ProcessStopped $workerPidFile

$workerProc = Start-Process -FilePath $python `
  -ArgumentList @("-m", "app.main") `
  -PassThru `
  -WindowStyle Hidden `
  -WorkingDirectory $workerRoot `
  -RedirectStandardOutput $workerOutLog `
  -RedirectStandardError $workerErrLog

Set-Content -LiteralPath $workerPidFile -Value $workerProc.Id

Write-Host "ai-worker PID : $($workerProc.Id)"
Write-Host "worker logs   : $workerOutLog"

Write-Step "Ready for real Zalo flow"
Write-Host "properties count : $propertyCount"
Write-Host "9router dashboard: http://localhost:20128/dashboard"
Write-Host "collector log    : $collectorLog"
Write-Host "status command   : .\scripts\maintenance\status-real-pipeline.ps1"
Write-Host "stop command     : .\scripts\maintenance\stop-real-pipeline.ps1"
Write-Host ""
Write-Host "Next step: scan the QR below in the collector terminal, then send or wait for a real group message." -ForegroundColor Yellow

Push-Location $collectorRoot
try {
  & $node "src\main.js" 2>&1 | Tee-Object -FilePath $collectorLog -Append
} finally {
  Pop-Location
}
