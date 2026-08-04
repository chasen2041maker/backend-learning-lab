$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot

Write-Host "Checking Git whitespace..."
git -C $repoRoot diff --check

Write-Host "Checking Python syntax..."
$pythonRoot = Join-Path $repoRoot "exercises/python-ticket-api"
$python = Join-Path $pythonRoot ".venv/Scripts/python.exe"
if (Test-Path $python) {
    & $python -m compileall -q (Join-Path $pythonRoot "app")
    & $python -m ruff check $pythonRoot
    & $python -m pytest $pythonRoot
} else {
    Write-Host "Python virtual environment not found; syntax/test step skipped."
}

Write-Host "Checking Go..."
$goRoot = Join-Path $repoRoot "exercises/go-ticket-api"
if (Get-Command go -ErrorAction SilentlyContinue) {
    $goFiles = Get-ChildItem $goRoot -Recurse -Filter *.go -File | Select-Object -ExpandProperty FullName
    $unformatted = gofmt -l $goFiles
    if ($unformatted) {
        throw "Unformatted Go files:`n$unformatted"
    }
    Push-Location $goRoot
    try {
        go vet ./...
        go test ./...
    } finally {
        Pop-Location
    }
} else {
    Write-Host "Go not found; Go checks skipped."
}

Write-Host "Checking for private key material..."
$privateKeyMarker = "BEGIN" + " PRIVATE KEY"
$privateKeyHits = Get-ChildItem $repoRoot -Recurse -File |
    Where-Object { $_.FullName -notmatch "\\.git\\|\\.venv\\" } |
    Select-String -SimpleMatch $privateKeyMarker -ErrorAction SilentlyContinue
if ($privateKeyHits) {
    throw "Possible private key material found."
}

Write-Host "Checks completed. Review skipped steps before publishing."
