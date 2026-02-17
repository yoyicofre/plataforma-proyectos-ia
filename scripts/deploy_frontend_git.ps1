param(
  [string]$RepoPath = "",
  [string[]]$Files = @(
    "frontend/src/App.tsx",
    "frontend/src/App.css"
  ),
  [string]$CommitMessage = "feat(frontend): update ui",
  [string]$Branch = "main",
  [switch]$All
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepoPath)) {
  $RepoPath = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

Push-Location $RepoPath
try {
  $insideRepo = git rev-parse --is-inside-work-tree 2>$null
  if ($LASTEXITCODE -ne 0 -or $insideRepo -ne "true") {
    throw "La ruta '$RepoPath' no es un repositorio git valido."
  }

  if ($All) {
    Write-Host "Staging: todos los cambios del repositorio..."
    git add -A
  } else {
    Write-Host "Staging: $($Files -join ', ')"
    git add -- $Files
  }

  $stagedFiles = git diff --cached --name-only
  if ([string]::IsNullOrWhiteSpace(($stagedFiles -join ""))) {
    Write-Host "No hay cambios staged para commit."
    exit 0
  }

  Write-Host "Commit: $CommitMessage"
  git commit -m $CommitMessage

  Write-Host "Push: origin/$Branch"
  git push origin $Branch

  Write-Host "Listo: cambios publicados en GitHub."
} finally {
  Pop-Location
}
