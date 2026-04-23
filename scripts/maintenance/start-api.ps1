[CmdletBinding()]
param(
  [switch]$Restart,
  [string]$Port = "8000"
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$apiDir = Join-Path $repoRoot "apps\api"
$packageDir = Join-Path $apiDir ".packages"

# 1. Improved Port Detection
function Get-ListeningProcessId([int]$Port) {
  # Use netstat to find LISTENING processes on the specific port
  $netstat = netstat -ano | Select-String "LISTENING" | Select-String ":$Port\s+"
  if ($netstat) {
    $line = $netstat[0].ToString().Trim()
    $parts = $line -split "\s+"
    if ($parts.Count -ge 5) {
      $foundPid = [int]$parts[-1]
      if ($foundPid -gt 0) { return $foundPid }
    }
  }
  return $null
}

# 2. Robust Python Detection
function Get-PythonPath {
  # Priority 1: .venv inside apps\api
  $venvPath = Join-Path $apiDir ".venv\Scripts\python.exe"
  if (Test-Path $venvPath) { return $venvPath }

  # Priority 2: python in PATH
  $pathPython = Get-Command python -ErrorAction SilentlyContinue
  if ($pathPython) { return $pathPython.Source }

  # Priority 3: Hardcoded fallback (if it exists)
  $fallback = "C:\Users\Admin\AppData\Local\Python\pythoncore-3.14-64\python.exe"
  if (Test-Path $fallback) { return $fallback }

  return $null
}

$pythonExe = Get-PythonPath
if (-not $pythonExe) {
  throw "Python executable not found. Please ensure Python is installed or a .venv exists in $apiDir"
}

Write-Host "[start-api] using python: $pythonExe"

if (-not (Test-Path $packageDir)) {
  Write-Warning "Missing API local packages: $packageDir. If imports fail, run an install script first."
}

# 3. Environment Setup
$env:PYTHONPATH = "$packageDir;$apiDir"
$env:HOTEL_INTEL_USE_SELECTOR_LOOP = "1"
if (-not $env:API_HOST) { $env:API_HOST = "0.0.0.0" }
if (-not $env:API_PORT) { $env:API_PORT = $Port }

# 4. Handle Existing Process
$existingProcessId = Get-ListeningProcessId -Port ([int]$env:API_PORT)
if ($existingProcessId) {
  if ($Restart) {
    Write-Host "[start-api] stopping existing process on port $env:API_PORT (PID=$existingProcessId)"
    Stop-Process -Id $existingProcessId -Force
    Start-Sleep -Seconds 1
  } else {
    Write-Host "[start-api] port $env:API_PORT is already in use by PID $existingProcessId (LISTENING)"
    Write-Host "[start-api] API is likely already running. Use stop-api.cmd first, or rerun with -Restart."
    exit 0
  }
}

# 5. Launch
Set-Location $apiDir
Write-Host "[start-api] cwd=$apiDir"
Write-Host "[start-api] host=$env:API_HOST port=$env:API_PORT"

# Check if uvicorn is available
$checkUvicorn = & $pythonExe -m uvicorn --version 2>&1
if ($LASTEXITCODE -ne 0) {
  Write-Error "uvicorn module not found in $pythonExe. PYTHONPATH was: $env:PYTHONPATH"
  exit 1
}

& $pythonExe -m uvicorn app.main:app --host $env:API_HOST --port $env:API_PORT
