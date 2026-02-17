param(
  [Parameter(Mandatory = $false)]
  [string]$OutputZip = ".build/lambda/package.zip",

  [Parameter(Mandatory = $false)]
  [string]$BuildDir = ".build/lambda/build",

  [Parameter(Mandatory = $false)]
  [string]$PythonExe = "python",

  [Parameter(Mandatory = $false)]
  [switch]$LinuxCompatible = $true
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

Write-Host "Installing project dependencies into build folder..."
& $PythonExe -m pip install -U pip

if ($LinuxCompatible) {
  Write-Host "Installing manylinux wheels for Lambda runtime (python3.12)..."
  & $PythonExe -m pip install `
    --target $BuildDir `
    --platform manylinux2014_x86_64 `
    --implementation cp `
    --python-version 3.12 `
    --only-binary=:all: `
    --upgrade `
    fastapi pydantic pyyaml sqlalchemy pymysql pyjwt httpx mangum
} else {
  & $PythonExe -m pip install . --target $BuildDir
}

Write-Host "Copying application source..."
Copy-Item "src" -Destination $BuildDir -Recurse -Force
Copy-Item "lambda_handler.py" -Destination $BuildDir -Force

Write-Host "Creating deployment ZIP..."
if (Test-Path $OutputZip) {
  Remove-Item $OutputZip -Force
}
Compress-Archive -Path "$BuildDir\*" -DestinationPath $OutputZip -Force

Write-Host "Lambda package created: $OutputZip"
