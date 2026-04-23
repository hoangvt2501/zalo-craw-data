[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

function Stop-FromPidFile([string]$pidFilePath, [string]$label) {
  if (-not (Test-Path -LiteralPath $pidFilePath)) {
    Write-Host "${label}: no pid file"
    return
  }

  $pidValue = (Get-Content -LiteralPath $pidFilePath -Raw).Trim()
  if (-not $pidValue) {
    Remove-Item -LiteralPath $pidFilePath -Force -ErrorAction SilentlyContinue
    Write-Host "${label}: empty pid file removed"
    return
  }

  $proc = Get-Process -Id ([int]$pidValue) -ErrorAction SilentlyContinue
  if ($proc) {
    Stop-Process -Id $proc.Id -Force
    Write-Host "${label}: stopped pid $pidValue"
  } else {
    Write-Host "${label}: pid $pidValue already not running"
  }

  Remove-Item -LiteralPath $pidFilePath -Force -ErrorAction SilentlyContinue
}

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$runDir = Join-Path $repoRoot "var\run"

Stop-FromPidFile (Join-Path $runDir "ai-worker.pid") "ai-worker"
Stop-FromPidFile (Join-Path $runDir "9router.pid") "9router"
