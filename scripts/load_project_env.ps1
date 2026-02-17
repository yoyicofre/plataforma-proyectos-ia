param(
  [Parameter(Mandatory = $false)]
  [string]$EnvFile = ".env.local"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $EnvFile)) {
  throw "Env file not found: $EnvFile. Create it from .env.example."
}

Get-Content $EnvFile | ForEach-Object {
  $line = $_.Trim()
  if ($line -eq "" -or $line.StartsWith("#")) { return }

  $pair = $line -split "=", 2
  if ($pair.Count -ne 2) { return }

  $key = $pair[0].Trim()
  $value = $pair[1]

  if ($key -ne "") {
    Set-Item -Path ("Env:" + $key) -Value $value
  }
}

Write-Host "Loaded environment variables from $EnvFile"
