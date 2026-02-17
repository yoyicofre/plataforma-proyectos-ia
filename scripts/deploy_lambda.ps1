param(
  [Parameter(Mandatory = $false)]
  [string]$FunctionName = "plataforma-ia-api",

  [Parameter(Mandatory = $false)]
  [string]$RoleName = "plataforma-ia-lambda-role",

  [Parameter(Mandatory = $false)]
  [string]$Region = "us-east-1",

  [Parameter(Mandatory = $false)]
  [string]$ZipPath = ".build/lambda/package.zip",

  [Parameter(Mandatory = $false)]
  [string]$LayerName = "plataforma-ia-deps",

  [Parameter(Mandatory = $false)]
  [string]$LayerZipPath = ".build/lambda/layer.zip",

  [Parameter(Mandatory = $false)]
  [int]$LayerVersionsToKeep = 5,

  [Parameter(Mandatory = $false)]
  [int]$Timeout = 30,

  [Parameter(Mandatory = $false)]
  [int]$MemorySize = 1024
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $false
$aws = [Environment]::GetEnvironmentVariable("AWS_CLI_PATH")
if (-not $aws) {
  $awsCmd = Get-Command aws -ErrorAction SilentlyContinue
  if ($awsCmd) {
    $aws = $awsCmd.Source
  }
}
if (-not $aws) {
  $windowsDefault = "C:\Program Files\Amazon\AWSCLIV2\aws.exe"
  if (Test-Path $windowsDefault) {
    $aws = $windowsDefault
  }
}
if (-not $aws) {
  throw "AWS CLI not found. Add aws to PATH or set AWS_CLI_PATH."
}

if (-not (Test-Path $ZipPath)) {
  throw "Zip package not found: $ZipPath. Run scripts/package_lambda.ps1 first."
}
if (-not (Test-Path $LayerZipPath)) {
  throw "Layer zip not found: $LayerZipPath. Run scripts/package_lambda_layer.ps1 first."
}

function Get-EnvValueOrEmpty([string]$name) {
  $val = [Environment]::GetEnvironmentVariable($name)
  if ($null -eq $val) { return "" }
  return $val
}

Write-Host "Ensuring IAM role exists: $RoleName"
$roleArn = ""
$roleLookup = $null
$roleExit = 1
$previousErrorAction = $ErrorActionPreference
try {
  $ErrorActionPreference = "Continue"
  $roleLookup = & $aws iam get-role --role-name $RoleName --query "Role.Arn" --output text 2>$null
  $roleExit = $LASTEXITCODE
} finally {
  $ErrorActionPreference = $previousErrorAction
}

if ($roleExit -eq 0 -and $roleLookup) {
  $roleArn = $roleLookup.Trim()
} else {
  $trustPolicy = @'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "lambda.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }
  ]
}
'@
  $tmpTrust = ".build/lambda/trust-policy.json"
  New-Item -ItemType Directory -Path ".build/lambda" -Force | Out-Null
  $trustPolicy | Out-File -FilePath $tmpTrust -Encoding ascii

  $roleArn = (& $aws iam create-role --role-name $RoleName --assume-role-policy-document file://$tmpTrust --query "Role.Arn" --output text).Trim()
  & $aws iam attach-role-policy --role-name $RoleName --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
  Start-Sleep -Seconds 10
}

$envVars = @{
  APP_NAME = Get-EnvValueOrEmpty "APP_NAME"
  ENVIRONMENT = Get-EnvValueOrEmpty "ENVIRONMENT"
  LOG_LEVEL = Get-EnvValueOrEmpty "LOG_LEVEL"
  DB_HOST = Get-EnvValueOrEmpty "DB_HOST"
  DB_PORT = Get-EnvValueOrEmpty "DB_PORT"
  DB_USER = Get-EnvValueOrEmpty "DB_USER"
  DB_PASSWORD = Get-EnvValueOrEmpty "DB_PASSWORD"
  DB_NAME = Get-EnvValueOrEmpty "DB_NAME"
  JWT_SECRET = Get-EnvValueOrEmpty "JWT_SECRET"
  JWT_ALGORITHM = Get-EnvValueOrEmpty "JWT_ALGORITHM"
  JWT_ISSUER = Get-EnvValueOrEmpty "JWT_ISSUER"
  JWT_AUDIENCE = Get-EnvValueOrEmpty "JWT_AUDIENCE"
  JWT_EXP_MINUTES = Get-EnvValueOrEmpty "JWT_EXP_MINUTES"
  DEV_BOOTSTRAP_KEY = Get-EnvValueOrEmpty "DEV_BOOTSTRAP_KEY"
  OPENAI_API_KEY = Get-EnvValueOrEmpty "OPENAI_API_KEY"
  OPENAI_MODEL_TEXT = Get-EnvValueOrEmpty "OPENAI_MODEL_TEXT"
  OPENAI_MODEL_IMAGE = Get-EnvValueOrEmpty "OPENAI_MODEL_IMAGE"
  GEMINI_API_KEY = Get-EnvValueOrEmpty "GEMINI_API_KEY"
  GEMINI_MODEL_TEXT = Get-EnvValueOrEmpty "GEMINI_MODEL_TEXT"
  GEMINI_MODEL_IMAGE = Get-EnvValueOrEmpty "GEMINI_MODEL_IMAGE"
  OPENAI_TEXT_INPUT_COST_PER_1K = Get-EnvValueOrEmpty "OPENAI_TEXT_INPUT_COST_PER_1K"
  OPENAI_TEXT_OUTPUT_COST_PER_1K = Get-EnvValueOrEmpty "OPENAI_TEXT_OUTPUT_COST_PER_1K"
  GEMINI_TEXT_INPUT_COST_PER_1K = Get-EnvValueOrEmpty "GEMINI_TEXT_INPUT_COST_PER_1K"
  GEMINI_TEXT_OUTPUT_COST_PER_1K = Get-EnvValueOrEmpty "GEMINI_TEXT_OUTPUT_COST_PER_1K"
  OPENAI_IMAGE_COST_PER_IMAGE = Get-EnvValueOrEmpty "OPENAI_IMAGE_COST_PER_IMAGE"
  GEMINI_IMAGE_COST_PER_IMAGE = Get-EnvValueOrEmpty "GEMINI_IMAGE_COST_PER_IMAGE"
}

$nonEmptyEnv = @{}
foreach ($k in $envVars.Keys) {
  if ($envVars[$k] -ne "") {
    $nonEmptyEnv[$k] = $envVars[$k]
  }
}
$envJson = @{ Variables = $nonEmptyEnv } | ConvertTo-Json -Compress
$tmpEnv = ".build/lambda/lambda-env.json"
$envJson | Out-File -FilePath $tmpEnv -Encoding ascii

Write-Host "Publishing Lambda layer: $LayerName"
$layerArn = (
  & $aws lambda publish-layer-version `
    --layer-name $LayerName `
    --zip-file fileb://$LayerZipPath `
    --compatible-runtimes python3.12 `
    --region $Region `
    --query "LayerVersionArn" `
    --output text
).Trim()

if ($LayerVersionsToKeep -lt 1) {
  $LayerVersionsToKeep = 1
}
$currentLayerVersion = [int]($layerArn.Split(":")[-1])
Write-Host "Applying layer retention policy (keep last $LayerVersionsToKeep versions)..."
$rawVersions = (
  & $aws lambda list-layer-versions `
    --layer-name $LayerName `
    --region $Region `
    --query "LayerVersions[].Version" `
    --output text
)
$versions = @()
if ($rawVersions) {
  foreach ($v in ($rawVersions -split "\s+")) {
    if ($v -and $v.Trim() -match "^\d+$") {
      $versions += [int]$v.Trim()
    }
  }
}
$versions = $versions | Sort-Object -Descending
$keep = $versions | Select-Object -First $LayerVersionsToKeep
$toDelete = $versions | Where-Object { $_ -notin $keep -and $_ -ne $currentLayerVersion }
foreach ($ver in $toDelete) {
  Write-Host "Deleting old layer version: $LayerName:$ver"
  & $aws lambda delete-layer-version `
    --layer-name $LayerName `
    --version-number $ver `
    --region $Region | Out-Null
}

Write-Host "Creating/updating Lambda function: $FunctionName"
$lambdaGetExit = 1
$previousErrorAction = $ErrorActionPreference
try {
  $ErrorActionPreference = "Continue"
  & $aws lambda get-function --function-name $FunctionName --region $Region 1>$null 2>$null
  $lambdaGetExit = $LASTEXITCODE
} finally {
  $ErrorActionPreference = $previousErrorAction
}

if ($lambdaGetExit -eq 0) {
  & $aws lambda update-function-code --function-name $FunctionName --zip-file fileb://$ZipPath --region $Region | Out-Null
  & $aws lambda wait function-updated --function-name $FunctionName --region $Region
  & $aws lambda update-function-configuration `
    --function-name $FunctionName `
    --handler lambda_handler.handler `
    --runtime python3.12 `
    --timeout $Timeout `
    --memory-size $MemorySize `
    --layers $layerArn `
    --environment file://$tmpEnv `
    --region $Region | Out-Null
} else {
  & $aws lambda create-function `
    --function-name $FunctionName `
    --runtime python3.12 `
    --handler lambda_handler.handler `
    --role $roleArn `
    --zip-file fileb://$ZipPath `
    --timeout $Timeout `
    --memory-size $MemorySize `
    --layers $layerArn `
    --environment file://$tmpEnv `
    --region $Region | Out-Null
}

Write-Host "Ensuring public function URL exists..."
$url = ""
$urlGetExit = 1
$previousErrorAction = $ErrorActionPreference
try {
  $ErrorActionPreference = "Continue"
  $url = (& $aws lambda get-function-url-config --function-name $FunctionName --region $Region --query "FunctionUrl" --output text 2>$null)
  $urlGetExit = $LASTEXITCODE
} finally {
  $ErrorActionPreference = $previousErrorAction
}

if ($urlGetExit -ne 0 -or -not $url) {
  $url = (& $aws lambda create-function-url-config --function-name $FunctionName --auth-type NONE --region $Region --query "FunctionUrl" --output text).Trim()
  & $aws lambda add-permission `
    --function-name $FunctionName `
    --statement-id FunctionUrlPublicAccess `
    --action lambda:InvokeFunctionUrl `
    --principal "*" `
    --function-url-auth-type NONE `
    --region $Region 2>$null | Out-Null
}

Write-Host "Lambda deploy completed."
Write-Host "Function URL: $url"
