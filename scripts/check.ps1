param(
    [switch]$RequireDocker
)

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

function Require-Command {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [string]$InstallHint
    )

    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $command) {
        throw "$Name is required. $InstallHint"
    }
    return $command.Source
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$repoRequirements = Join-Path $repoRoot "requirements-repo.lock"
$pythonRoot = Join-Path $repoRoot "exercises/python-ticket-api"
$goRoot = Join-Path $repoRoot "exercises/go-ticket-api"
$composeFile = Join-Path $repoRoot "exercises/infrastructure/docker-compose.yml"
$env:GOCACHE = Join-Path $repoRoot ".go-cache"

$python = Require-Command -Name "python" -InstallHint "Install Python 3.11+ and ensure python is on PATH."
$go = Require-Command -Name "go" -InstallHint "Install Go 1.22+ and ensure go is on PATH."
$gofmt = Require-Command -Name "gofmt" -InstallHint "gofmt is installed with Go. Check your Go PATH/setup."
$git = Require-Command -Name "git" -InstallHint "Install Git and ensure git is on PATH."
$dockerCommand = Get-Command docker -ErrorAction SilentlyContinue

if (-not (Test-Path $repoRequirements)) {
    throw "Repository dependency lock missing: $repoRequirements"
}

Write-Host "Checking Python version..."
Invoke-NativeChecked -FilePath $python -ArgumentList @(
    "-c",
    "import sys; assert sys.version_info >= (3, 11), f'Python 3.11+ required, got {sys.version}'"
)

Write-Host "Checking required Python development packages..."
try {
    Invoke-NativeChecked -FilePath $python -ArgumentList @("-m", "pytest", "--version")
    Invoke-NativeChecked -FilePath $python -ArgumentList @("-m", "ruff", "--version")
} catch {
    throw "Python repository dependencies are missing. Run: python -m pip install -r requirements-repo.lock; python -m pip install --no-deps -e exercises/python-ticket-api"
}

Write-Host "Checking Git whitespace..."
Invoke-NativeChecked -FilePath $git -ArgumentList @("-C", $repoRoot, "diff", "--check")

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
$unformatted = @(& $gofmt -l @goFiles)
if ($LASTEXITCODE -ne 0) {
    throw "gofmt failed with exit code $LASTEXITCODE"
}
if ($unformatted) {
    throw "Unformatted Go files:`n$($unformatted -join [Environment]::NewLine)"
}

Push-Location $goRoot
try {
    Invoke-NativeChecked -FilePath $go -ArgumentList @("vet", "./...")
    $cgoEnabled = (& $go env CGO_ENABLED | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) {
        throw "go env CGO_ENABLED failed with exit code $LASTEXITCODE"
    }

    if ($cgoEnabled -eq "1") {
        Invoke-NativeChecked -FilePath $go -ArgumentList @("test", "-race", "./...")
    } else {
        Write-Warning "CGO is disabled locally; running standard Go tests. CI still requires go test -race ./..."
        Invoke-NativeChecked -FilePath $go -ArgumentList @("test", "./...")
    }
} finally {
    Pop-Location
}

if ($dockerCommand) {
    Write-Host "Checking Docker Compose rendering..."
    Invoke-NativeChecked -FilePath $dockerCommand.Source -ArgumentList @("compose", "-f", $composeFile, "config", "--quiet")
} elseif ($RequireDocker) {
    throw "Docker is required because -RequireDocker was specified. Install/start Docker Desktop and retry."
} else {
    Write-Warning "Docker is not available; skipping the local Compose rendering check. CI still runs Docker/PostgreSQL/Redis integration checks. Use -RequireDocker to make this a local failure."
}

Write-Host "Core local checks passed."
if (-not $dockerCommand) {
    Write-Host "Docker-dependent checks were not run locally; use CI or rerun with Docker available."
}
