[CmdletBinding()]
param(
  [switch]$SkipResetRuntime,
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

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$envPath = Join-Path $repoRoot ".env"
$migrationPath = Join-Path $repoRoot "infra\postgres\migrations\001_initial.sql"
$workerRoot = Join-Path $repoRoot "apps\ai-worker"
$seedScript = Join-Path $workerRoot "scripts\seed_properties_from_csv.py"
$collectorSmokeScript = Join-Path $repoRoot "apps\zalo-collector\scripts\smoke-insert-raw-message.js"
$routerServer = Join-Path $env:APPDATA "npm\node_modules\9router\app\server.js"
$routerDb = Join-Path $env:APPDATA "9router\db.json"
$routerOutLog = Join-Path $repoRoot "var\logs\9router.out.log"
$routerErrLog = Join-Path $repoRoot "var\logs\9router.err.log"

Load-DotEnv $envPath

$databaseUrl = $env:DATABASE_URL
if (-not $databaseUrl) {
  throw "DATABASE_URL is missing in .env"
}

$python = Resolve-ToolPath "python.exe" "C:\Users\Admin\AppData\Local\Python\pythoncore-3.14-64\python.exe"
$node = Resolve-ToolPath "node.exe" "C:\Program Files\nodejs\node.exe"
$psql = Resolve-ToolPath "psql.exe" "C:\Program Files\PostgreSQL\18\bin\psql.exe"

Write-Step "Checking local toolchain"
Write-Host "python : $python"
Write-Host "node   : $node"
Write-Host "psql   : $psql"

& $python -c "import psycopg, httpx, rapidfuzz, pydantic, pydantic_settings; print('python deps ok')"

if (-not $SkipStart9Router) {
  Write-Step "Ensuring 9router is running"
  if (-not (Test-HttpOk "http://127.0.0.1:20128/v1/models")) {
    if (-not (Test-Path -LiteralPath $routerServer)) {
      throw "9router is not installed. Install it first, or rerun with -SkipStart9Router."
    }

    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $routerOutLog) | Out-Null
    Start-Process -FilePath $node `
      -ArgumentList @($routerServer) `
      -WindowStyle Hidden `
      -RedirectStandardOutput $routerOutLog `
      -RedirectStandardError $routerErrLog | Out-Null

    if (-not (Wait-ForHttp "http://127.0.0.1:20128/v1/models" 30)) {
      throw "9router did not become ready on http://127.0.0.1:20128/v1/models"
    }
  }

  Write-Host "9router API is reachable at http://127.0.0.1:20128/v1"

  if (Test-Path -LiteralPath $routerDb) {
    $routerState = Get-Content -LiteralPath $routerDb -Raw | ConvertFrom-Json
    $providerCount = @($routerState.providerConnections).Count + @($routerState.providerNodes).Count + @($routerState.proxyPools).Count
    if ($providerCount -eq 0) {
      Write-Warning "9router is running but has no configured providers. Worker may fail when it reaches the LLM call."
      Write-Warning "Open http://localhost:20128/dashboard and connect at least one provider."
    }
  }
}

Write-Step "Applying schema migration"
& $psql $databaseUrl -v ON_ERROR_STOP=1 -f $migrationPath

if ($ReseedProperties) {
  Write-Step "Resetting runtime tables and properties"
  & $psql $databaseUrl -v ON_ERROR_STOP=1 -c "TRUNCATE TABLE deal_rooms, hotel_deals, rejected_deals, match_attempts, ai_call_logs, processing_events, raw_messages, properties RESTART IDENTITY CASCADE;"
} elseif (-not $SkipResetRuntime) {
  Write-Step "Resetting runtime tables"
  & $psql $databaseUrl -v ON_ERROR_STOP=1 -c "TRUNCATE TABLE deal_rooms, hotel_deals, rejected_deals, match_attempts, ai_call_logs, processing_events, raw_messages RESTART IDENTITY CASCADE;"
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

Write-Step "Inserting smoke raw message"
Push-Location (Join-Path $repoRoot "apps\zalo-collector")
try {
  & $node $collectorSmokeScript
} finally {
  Pop-Location
}

Write-Step "Running worker for one batch"
Push-Location $workerRoot
try {
  & $python -m app.main --once --limit 1
} finally {
  Pop-Location
}

Write-Step "Summary"
Write-Host "properties count: $propertyCount"
& $psql $databaseUrl -P pager=off `
  -c "SELECT status, COUNT(*) AS count FROM raw_messages GROUP BY status ORDER BY status;" `
  -c "SELECT hotel_name, property_name, match_score, verification_method, created_at FROM hotel_deals ORDER BY created_at DESC LIMIT 3;" `
  -c "SELECT reason, created_at FROM rejected_deals ORDER BY created_at DESC LIMIT 3;" `
  -c "SELECT id, sender_name, status, processing_attempts, COALESCE(last_error, '') AS last_error FROM raw_messages ORDER BY captured_at DESC LIMIT 3;"

Write-Host ""
Write-Host "Smoke test finished." -ForegroundColor Green
