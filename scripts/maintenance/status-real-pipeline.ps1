[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

function Show-ProcessStatus([string]$pidFilePath, [string]$label) {
  if (-not (Test-Path -LiteralPath $pidFilePath)) {
    Write-Host "$label : not started by script"
    return
  }

  $pidValue = (Get-Content -LiteralPath $pidFilePath -Raw).Trim()
  $proc = Get-Process -Id ([int]$pidValue) -ErrorAction SilentlyContinue
  if ($proc) {
    Write-Host "$label : running (pid $pidValue)"
  } else {
    Write-Host "$label : pid file exists but process is not running"
  }
}

function Load-DotEnv([string]$path) {
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

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$envPath = Join-Path $repoRoot ".env"
$runDir = Join-Path $repoRoot "var\run"
$logsDir = Join-Path $repoRoot "var\logs"
$psqlPath = "C:\Program Files\PostgreSQL\18\bin\psql.exe"
$psql = Get-Command psql.exe -ErrorAction SilentlyContinue
if ($psql) {
  $psqlPath = $psql.Source
}

Load-DotEnv $envPath

Write-Host "Ports"
netstat -ano | Select-String ':5432|:20128' | ForEach-Object { $_.Line }

Write-Host ""
Write-Host "Processes"
Show-ProcessStatus (Join-Path $runDir "ai-worker.pid") "ai-worker"
Show-ProcessStatus (Join-Path $runDir "9router.pid") "9router"

Write-Host ""
Write-Host "Database"
& $psqlPath $env:DATABASE_URL -P pager=off `
  -c "SELECT status, COUNT(*) AS count FROM raw_messages GROUP BY status ORDER BY status;" `
  -c "SELECT id, sender_name, status, processing_attempts, COALESCE(last_error, '') AS last_error FROM raw_messages ORDER BY captured_at DESC LIMIT 10;"

Write-Host ""
Write-Host "Logs"
Get-Item (Join-Path $logsDir "zalo-collector.log"), (Join-Path $logsDir "ai-worker.out.log"), (Join-Path $logsDir "ai-worker.err.log"), (Join-Path $logsDir "9router.out.log"), (Join-Path $logsDir "9router.err.log") -ErrorAction SilentlyContinue |
  Select-Object FullName, LastWriteTime, Length
