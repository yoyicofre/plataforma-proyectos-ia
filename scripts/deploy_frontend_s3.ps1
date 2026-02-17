param(
  [Parameter(Mandatory = $true)]
  [string]$BucketName,

  [Parameter(Mandatory = $false)]
  [string]$DistributionId = "",

  [Parameter(Mandatory = $false)]
  [string]$FrontendDir = "frontend"
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
  throw "AWS CLI not found. Install and configure AWS CLI first."
}

if (-not (Test-Path $FrontendDir)) {
  throw "Frontend directory not found: $FrontendDir"
}

Write-Host "Installing frontend dependencies..."
Push-Location $FrontendDir
npm install

Write-Host "Building frontend..."
npm run build
Pop-Location

$distPath = Join-Path $FrontendDir "dist"
if (-not (Test-Path $distPath)) {
  throw "Build output not found: $distPath"
}

Write-Host "Uploading assets to s3://$BucketName ..."
aws s3 sync "$distPath" "s3://$BucketName" --delete

if ($DistributionId -ne "") {
  Write-Host "Creating CloudFront invalidation for distribution $DistributionId ..."
  aws cloudfront create-invalidation --distribution-id $DistributionId --paths "/*"
}

Write-Host "Frontend deploy completed."
