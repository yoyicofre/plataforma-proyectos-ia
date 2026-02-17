param(
  [Parameter(Mandatory = $false)]
  [string]$RepoPath = "",

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
  [int]$MemorySize = 1024,

  [Parameter(Mandatory = $false)]
  [string]$Branch = "main",

  [Parameter(Mandatory = $false)]
  [string]$CommitMessage = "chore(release): full frontend/backend deploy",

  [Parameter(Mandatory = $false)]
  [string]$ApiBaseUrl = "https://api.mktautomations.com",

  [Parameter(Mandatory = $false)]
  [string]$AppOrigin = "https://app.mktautomations.com",

  [switch]$FrontendAll,
  [switch]$SkipFrontend,
  [switch]$SkipBackend,
  [switch]$SkipChecks
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepoPath)) {
  $RepoPath = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

$frontendScript = Join-Path $PSScriptRoot "deploy_frontend_git.ps1"
$backendScript = Join-Path $PSScriptRoot "deploy_backend_full.ps1"

Push-Location $RepoPath
try {
  if (-not $SkipFrontend) {
    Write-Host "Step 1/3: publishing frontend changes to GitHub..."
    $frontendArgs = @{
      RepoPath = $RepoPath
      Branch = $Branch
      CommitMessage = $CommitMessage
    }
    if ($FrontendAll) {
      $frontendArgs["All"] = $true
    }
    & $frontendScript @frontendArgs
  } else {
    Write-Host "Step 1/3: skipped frontend publish."
  }

  if (-not $SkipBackend) {
    Write-Host "Step 2/3: deploying backend Lambda..."
    & $backendScript `
      -EnvFile $EnvFile `
      -FunctionName $FunctionName `
      -Region $Region `
      -LayerVersionsToKeep $LayerVersionsToKeep `
      -Timeout $Timeout `
      -MemorySize $MemorySize
  } else {
    Write-Host "Step 2/3: skipped backend deploy."
  }

  if (-not $SkipChecks) {
    Write-Host "Step 3/3: running API checks..."

    $healthCode = (& curl.exe -s -o NUL -w "%{http_code}" "$ApiBaseUrl/health").Trim()
    if ($healthCode -ne "200") {
      throw "Health check failed: $ApiBaseUrl/health returned $healthCode"
    }

    $preflightCode = (
      & curl.exe -s -o NUL -w "%{http_code}" -X OPTIONS "$ApiBaseUrl/auth/login" `
        -H "Origin: $AppOrigin" `
        -H "Access-Control-Request-Method: POST" `
        -H "Access-Control-Request-Headers: content-type"
    ).Trim()
    if (($preflightCode -ne "200") -and ($preflightCode -ne "204")) {
      throw "CORS preflight check failed: OPTIONS /auth/login returned $preflightCode"
    }

    Write-Host "Checks OK: /health=$healthCode, preflight=$preflightCode"
  } else {
    Write-Host "Step 3/3: skipped API checks."
  }

  Write-Host "Full release finished successfully."
} finally {
  Pop-Location
}
