Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
if ($PSVersionTable.PSVersion -ge [Version]"7.3") {
    $PSNativeCommandUseErrorActionPreference = $true
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonRoot = Join-Path $repoRoot "exercises/python-ticket-api"
$python = Join-Path $pythonRoot ".venv/Scripts/python.exe"
$goRoot = Join-Path $repoRoot "exercises/go-ticket-api"
$composeFile = Join-Path $repoRoot "exercises/infrastructure/docker-compose.yml"

if (-not (Test-Path $python)) {
    throw "Python venv missing. Create exercises/python-ticket-api/.venv and install requirements-dev.lock."
}
if (-not (Get-Command go -ErrorAction SilentlyContinue)) {
    throw "Go is required for the repository check."
}
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker is required to validate Compose."
}

Write-Host "Checking Git whitespace..."
git -C $repoRoot diff --check

Write-Host "Checking repository contracts, links, and private data..."
& $python (Join-Path $repoRoot "scripts/validate_contracts.py")
& $python (Join-Path $repoRoot "scripts/check_markdown_links.py")
& $python (Join-Path $repoRoot "scripts/scan_secrets.py")

Write-Host "Checking Python formatting, lint, and tests..."
& $python -m ruff format --check `
    $pythonRoot `
    (Join-Path $repoRoot "exercises/redis-lab") `
    (Join-Path $repoRoot "exercises/reliability-labs") `
    (Join-Path $repoRoot "scripts")
& $python -m ruff check `
    $pythonRoot `
    (Join-Path $repoRoot "exercises/redis-lab") `
    (Join-Path $repoRoot "exercises/reliability-labs") `
    (Join-Path $repoRoot "scripts")
& $python -m pytest $pythonRoot
& $python -m unittest discover -s (Join-Path $repoRoot "exercises/reliability-labs/tests") -v

Write-Host "Checking Go formatting, vet, and tests..."
$goFiles = Get-ChildItem $goRoot -Recurse -Filter *.go -File | Select-Object -ExpandProperty FullName
$unformatted = gofmt -l $goFiles
if ($unformatted) {
    throw "Unformatted Go files:`n$unformatted"
}
Push-Location $goRoot
try {
    go vet ./...
    if ((go env CGO_ENABLED) -eq "1") {
        go test -race ./...
    } else {
        Write-Host "CGO is disabled locally; running standard Go tests. CI still requires -race."
        go test ./...
    }
} finally {
    Pop-Location
}

Write-Host "Checking Compose rendering..."
docker compose -f $composeFile config --quiet

Write-Host "All local checks passed."
