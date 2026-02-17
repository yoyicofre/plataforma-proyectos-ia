param(
  [Parameter(Mandatory = $false)]
  [string]$OutputZip = ".build/lambda/package.zip",

  [Parameter(Mandatory = $false)]
  [string]$BuildDir = ".build/lambda/build"
)

$ErrorActionPreference = "Stop"

Write-Host "Preparing Lambda build directory..."
if (Test-Path $BuildDir) {
  Remove-Item $BuildDir -Recurse -Force
}
New-Item -ItemType Directory -Path $BuildDir -Force | Out-Null

$zipDir = Split-Path -Parent $OutputZip
if (-not (Test-Path $zipDir)) {
  New-Item -ItemType Directory -Path $zipDir -Force | Out-Null
}

Write-Host "Copying application source..."
New-Item -ItemType Directory -Path (Join-Path $BuildDir "app") -Force | Out-Null
Copy-Item "src" -Destination (Join-Path $BuildDir "app") -Recurse -Force
Copy-Item "lambda_handler.py" -Destination $BuildDir -Force

Write-Host "Creating deployment ZIP..."
if (Test-Path $OutputZip) {
  Remove-Item $OutputZip -Force
}
Compress-Archive -Path "$BuildDir\*" -DestinationPath $OutputZip -Force

Write-Host "Lambda package created: $OutputZip"
