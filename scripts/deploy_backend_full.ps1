param(
  [Parameter(Mandatory = $false)]
  [string]$EnvFile = ".env.local",

  [Parameter(Mandatory = $false)]
  [string]$FunctionName = "plataforma-ia-api",

  [Parameter(Mandatory = $false)]
  [string]$Region = "us-east-1",

  [Parameter(Mandatory = $false)]
  [int]$LayerVersionsToKeep = 5,

  [Parameter(Mandatory = $false)]
  [int]$Timeout = 30,

  [Parameter(Mandatory = $false)]
  [int]$MemorySize = 1024
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$loadEnvScript = Join-Path $PSScriptRoot "load_project_env.ps1"
$packageLayerScript = Join-Path $PSScriptRoot "package_lambda_layer.ps1"
$packageLambdaScript = Join-Path $PSScriptRoot "package_lambda.ps1"
$deployLambdaScript = Join-Path $PSScriptRoot "deploy_lambda.ps1"

Push-Location $repoRoot
try {
  Write-Host "Step 1/4: loading env vars from $EnvFile"
  & $loadEnvScript -EnvFile $EnvFile

  Write-Host "Step 2/4: packaging Lambda layer"
  & $packageLayerScript

  Write-Host "Step 3/4: packaging Lambda code"
  & $packageLambdaScript

  Write-Host "Step 4/4: deploying Lambda function $FunctionName in $Region"
  & $deployLambdaScript `
    -FunctionName $FunctionName `
    -Region $Region `
    -LayerVersionsToKeep $LayerVersionsToKeep `
    -Timeout $Timeout `
    -MemorySize $MemorySize

  Write-Host "Backend deployment finished successfully."
} finally {
  Pop-Location
}
