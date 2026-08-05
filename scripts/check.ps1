Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
if ($PSVersionTable.PSVersion -ge [Version]"7.3") {
    $PSNativeCommandUseErrorActionPreference = $true
}

function Invoke-NativeChecked {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [Parameter(Mandatory = $false)]
        [object[]]$ArgumentList = @()
    )

    & $FilePath @ArgumentList
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        throw "Native command failed with exit code ${exitCode}: $FilePath $($ArgumentList -join ' ')"
    }
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonRoot = Join-Path $repoRoot "exercises/python-ticket-api"
$python = Join-Path $pythonRoot ".venv/Scripts/python.exe"
$repoRequirements = Join-Path $repoRoot "requirements-repo.lock"
$goRoot = Join-Path $repoRoot "exercises/go-ticket-api"
$composeFile = Join-Path $repoRoot "exercises/infrastructure/docker-compose.yml"
$env:GOCACHE = Join-Path $repoRoot ".go-cache"

if (-not (Test-Path $python)) {
    throw "Python venv missing. Create exercises/python-ticket-api/.venv and install requirements-repo.lock."
}
if (-not (Test-Path $repoRequirements)) {
    throw "Repository dependency lock missing: $repoRequirements"
}
if (-not (Get-Command go -ErrorAction SilentlyContinue)) {
    throw "Go is required for the repository check."
}
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker is required to validate Compose."
}

Write-Host "Checking Git whitespace..."
Invoke-NativeChecked -FilePath "git" -ArgumentList @("-C", $repoRoot, "diff", "--check")

Write-Host "Checking repository contracts, links, and private data..."
Invoke-NativeChecked -FilePath $python -ArgumentList @(Join-Path $repoRoot "scripts/validate_contracts.py")
Invoke-NativeChecked -FilePath $python -ArgumentList @(Join-Path $repoRoot "scripts/check_markdown_links.py")
Invoke-NativeChecked -FilePath $python -ArgumentList @(Join-Path $repoRoot "scripts/scan_secrets.py")

Write-Host "Checking Python formatting, lint, and tests..."
Invoke-NativeChecked -FilePath $python -ArgumentList @(
    "-m", "ruff", "format", "--check",
    $pythonRoot,
    (Join-Path $repoRoot "exercises/redis-lab"),
    (Join-Path $repoRoot "exercises/reliability-labs"),
    (Join-Path $repoRoot "scripts")
)
Invoke-NativeChecked -FilePath $python -ArgumentList @(
    "-m", "ruff", "check",
    $pythonRoot,
    (Join-Path $repoRoot "exercises/redis-lab"),
    (Join-Path $repoRoot "exercises/reliability-labs"),
    (Join-Path $repoRoot "scripts")
)
Push-Location $pythonRoot
try {
    Invoke-NativeChecked -FilePath $python -ArgumentList @("-m", "pytest")
} finally {
    Pop-Location
}
Invoke-NativeChecked -FilePath $python -ArgumentList @(
    "-m", "unittest", "discover", "-s", (Join-Path $repoRoot "exercises/reliability-labs/tests"), "-v"
)
Invoke-NativeChecked -FilePath $python -ArgumentList @(
    "-m", "unittest", "discover", "-s", (Join-Path $repoRoot "exercises/redis-lab/tests"), "-v"
)

Write-Host "Checking Go formatting, vet, and tests..."
$goFiles = Get-ChildItem $goRoot -Recurse -Filter *.go -File | Select-Object -ExpandProperty FullName
$unformatted = @(Invoke-NativeChecked -FilePath "gofmt" -ArgumentList (@("-l") + $goFiles))
if ($unformatted) {
    throw "Unformatted Go files:`n$unformatted"
}
Push-Location $goRoot
try {
    Invoke-NativeChecked -FilePath "go" -ArgumentList @("vet", "./...")
    $cgoEnabled = (Invoke-NativeChecked -FilePath "go" -ArgumentList @("env", "CGO_ENABLED") | Out-String).Trim()
    if ($cgoEnabled -eq "1") {
        Invoke-NativeChecked -FilePath "go" -ArgumentList @("test", "-race", "./...")
    } else {
        Write-Host "CGO is disabled locally; running standard Go tests. CI still requires -race."
        Invoke-NativeChecked -FilePath "go" -ArgumentList @("test", "./...")
    }
} finally {
    Pop-Location
}

Write-Host "Checking Compose rendering..."
Invoke-NativeChecked -FilePath "docker" -ArgumentList @("compose", "-f", $composeFile, "config", "--quiet")

Write-Host "All local checks passed."
