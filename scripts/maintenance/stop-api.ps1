$ErrorActionPreference = "Stop"

if (-not $env:API_PORT) {
  $env:API_PORT = "8000"
}

# Improved Port Detection
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

$processId = Get-ListeningProcessId -Port ([int]$env:API_PORT)

if (-not $processId) {
  Write-Host "[stop-api] no process is listening on port $env:API_PORT"
  exit 0
}

Write-Host "[stop-api] stopping PID=$processId on port $env:API_PORT"
Stop-Process -Id $processId -Force
