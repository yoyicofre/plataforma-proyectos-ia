param(
  [Parameter(Mandatory = $false)]
  [string]$OutputZip = ".build/lambda/layer.zip",

  [Parameter(Mandatory = $false)]
  [string]$LayerBuildDir = ".build/lambda/layer",

  [Parameter(Mandatory = $false)]
  [string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"

Write-Host "Preparing Lambda layer build directory..."
if (Test-Path $LayerBuildDir) {
  Remove-Item $LayerBuildDir -Recurse -Force
}
New-Item -ItemType Directory -Path (Join-Path $LayerBuildDir "python") -Force | Out-Null

$zipDir = Split-Path -Parent $OutputZip
if (-not (Test-Path $zipDir)) {
  New-Item -ItemType Directory -Path $zipDir -Force | Out-Null
}

Write-Host "Installing manylinux dependencies for Lambda layer (python3.12)..."
& $PythonExe -m pip install -U pip
& $PythonExe -m pip install `
  --target (Join-Path $LayerBuildDir "python") `
  --platform manylinux2014_x86_64 `
  --implementation cp `
  --python-version 3.12 `
  --only-binary=:all: `
  --upgrade `
  fastapi pydantic pyyaml sqlalchemy pymysql pyjwt httpx mangum

Write-Host "Creating layer ZIP..."
if (Test-Path $OutputZip) {
  Remove-Item $OutputZip -Force
}
Compress-Archive -Path "$LayerBuildDir\*" -DestinationPath $OutputZip -Force

Write-Host "Lambda layer package created: $OutputZip"
