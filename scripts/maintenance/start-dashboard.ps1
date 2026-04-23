[CmdletBinding()]
param(
  [switch]$CleanBuildCache
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$dashboardDir = Join-Path $repoRoot "apps\dashboard"
$npmCmd = "C:\Program Files\nodejs\npm.cmd"
$nodeModulesDir = Join-Path $dashboardDir "node_modules"
$nextBuildDir = Join-Path $dashboardDir ".next"

if (-not (Test-Path $npmCmd)) {
  throw "npm.cmd not found: $npmCmd"
}
if (-not (Test-Path $nodeModulesDir)) {
  throw "Missing dashboard dependencies: $nodeModulesDir"
}

$env:Path = "C:\Program Files\nodejs;$env:Path"
if (-not $env:NEXT_PUBLIC_API_BASE_URL) {
  $env:NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000"
}

if ($CleanBuildCache -and (Test-Path $nextBuildDir)) {
  Write-Host "[start-dashboard] removing $nextBuildDir"
  Remove-Item -LiteralPath $nextBuildDir -Recurse -Force
}

Set-Location $dashboardDir
Write-Host "[start-dashboard] cwd=$dashboardDir"
Write-Host "[start-dashboard] api=$env:NEXT_PUBLIC_API_BASE_URL"

& $npmCmd run dev
