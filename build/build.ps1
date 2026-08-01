param(
    [switch]$SkipInstaller,
    [switch]$Clean,
    [string]$IsccPath
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvDir = Join-Path $ProjectRoot ".venv-build"
$Python = Join-Path $VenvDir "Scripts\python.exe"
$DistDir = Join-Path $ProjectRoot "dist"
$WorkDir = Join-Path $ProjectRoot "build\pyinstaller-work"
$SpecFile = Join-Path $ProjectRoot "build\Teggy.spec"
$InstallerScript = Join-Path $ProjectRoot "build\installer\Teggy.iss"
$ReleaseDir = Join-Path $ProjectRoot "release"
$AppDir = Join-Path $DistDir "Teggy"
$Executable = Join-Path $AppDir "Teggy.exe"

$PlaywrightSource = Join-Path $VenvDir "Lib\site-packages\playwright\driver\package\.local-browsers"
$PlaywrightDestination = Join-Path $AppDir "_internal\playwright\driver\package\.local-browsers"

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,

        [Parameter(Mandatory = $false)]
        [string[]]$Arguments = @(),

        [Parameter(Mandatory = $true)]
        [string]$ErrorMessage
    )

    & $FilePath @Arguments

    if ($LASTEXITCODE -ne 0) {
        throw "$ErrorMessage Exit code: $LASTEXITCODE"
    }
}

Set-Location $ProjectRoot

if ($Clean) {
    Write-Host "Cleaning previous build..." -ForegroundColor Cyan
    Remove-Item $DistDir -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item $WorkDir -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item $ReleaseDir -Recurse -Force -ErrorAction SilentlyContinue
}

if (-not (Test-Path $Python)) {
    Write-Host "Creating build virtual environment..." -ForegroundColor Cyan
    & py -3 -m venv $VenvDir

    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $Python)) {
        throw "Failed to create build virtual environment: $VenvDir"
    }
}

Invoke-Checked -FilePath $Python -Arguments @(
    "-m", "pip", "install", "--upgrade", "pip"
) -ErrorMessage "Failed to upgrade pip."

Invoke-Checked -FilePath $Python -Arguments @(
    "-m", "pip", "install", "-r", (Join-Path $ProjectRoot "requirements.txt")
) -ErrorMessage "Failed to install runtime requirements."

Invoke-Checked -FilePath $Python -Arguments @(
    "-m", "pip", "install", "-r", (Join-Path $ProjectRoot "requirements-build.txt")
) -ErrorMessage "Failed to install build requirements."

$PreviousBrowsersPath = $env:PLAYWRIGHT_BROWSERS_PATH
$env:PLAYWRIGHT_BROWSERS_PATH = "0"

try {
    Write-Host "Installing Playwright Chromium..." -ForegroundColor Cyan
    Invoke-Checked -FilePath $Python -Arguments @(
        "-m", "playwright", "install", "chromium"
    ) -ErrorMessage "Failed to install Playwright Chromium."
}
finally {
    if ($null -eq $PreviousBrowsersPath) {
        Remove-Item Env:PLAYWRIGHT_BROWSERS_PATH -ErrorAction SilentlyContinue
    }
    else {
        $env:PLAYWRIGHT_BROWSERS_PATH = $PreviousBrowsersPath
    }
}

if (-not (Test-Path $PlaywrightSource)) {
    throw "Playwright browser directory was not created: $PlaywrightSource"
}

Write-Host "Building Teggy with PyInstaller..." -ForegroundColor Cyan
Invoke-Checked -FilePath $Python -Arguments @(
    "-m", "PyInstaller",
    "--noconfirm",
    "--clean",
    "--distpath", $DistDir,
    "--workpath", $WorkDir,
    $SpecFile
) -ErrorMessage "PyInstaller failed."

if (-not (Test-Path $Executable)) {
    throw "Build completed without Teggy.exe: $Executable"
}

Write-Host "Bundling Playwright browsers..." -ForegroundColor Cyan

$PlaywrightParent = Split-Path -Parent $PlaywrightDestination
New-Item -ItemType Directory -Path $PlaywrightParent -Force | Out-Null

if (Test-Path $PlaywrightDestination) {
    Remove-Item $PlaywrightDestination -Recurse -Force
}

Copy-Item -Path $PlaywrightSource -Destination $PlaywrightDestination -Recurse -Force

$ChromiumExecutable = Get-ChildItem -Path $PlaywrightDestination -Recurse -Filter "chrome.exe" -File -ErrorAction SilentlyContinue | Select-Object -First 1
$HeadlessExecutable = Get-ChildItem -Path $PlaywrightDestination -Recurse -Filter "chrome-headless-shell.exe" -File -ErrorAction SilentlyContinue | Select-Object -First 1

if (-not $ChromiumExecutable) {
    throw "Bundled Playwright Chromium does not contain chrome.exe."
}

if (-not $HeadlessExecutable) {
    throw "Bundled Playwright Chromium does not contain chrome-headless-shell.exe."
}

Write-Host "Application ready: $Executable" -ForegroundColor Green
Write-Host "Chromium: $($ChromiumExecutable.FullName)" -ForegroundColor DarkGreen
Write-Host "Headless shell: $($HeadlessExecutable.FullName)" -ForegroundColor DarkGreen

if ($SkipInstaller) {
    Write-Host "Installer step skipped." -ForegroundColor Yellow
    exit 0
}

if (-not (Test-Path $InstallerScript)) {
    throw "Inno Setup script not found: $InstallerScript"
}

$IsccCandidates = @()

if ($IsccPath) {
    $IsccCandidates += $IsccPath
}

if ($env:INNO_SETUP_ISCC) {
    $IsccCandidates += $env:INNO_SETUP_ISCC
}

$IsccCandidates += @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)

# Matches paths such as X:\<folder>\Inno Setup 6\ISCC.exe without
# hard-coding a non-ASCII folder name into this PowerShell script.
$CustomIscc = Get-ChildItem -Path "X:\*\Inno Setup 6\ISCC.exe" -File -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName

if ($CustomIscc) {
    $IsccCandidates = @($CustomIscc) + $IsccCandidates
}

$Iscc = $IsccCandidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1

if (-not $Iscc) {
    throw "Inno Setup 6 was not found. Pass -IsccPath or set INNO_SETUP_ISCC."
}

New-Item -ItemType Directory -Path $ReleaseDir -Force | Out-Null

Write-Host "Building installer with: $Iscc" -ForegroundColor Cyan
Invoke-Checked -FilePath $Iscc -Arguments @($InstallerScript) -ErrorMessage "Inno Setup failed."

$Installer = Get-ChildItem -Path $ReleaseDir -Filter "TeggySetup-*.exe" -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1

if (-not $Installer) {
    throw "Installer was not created in: $ReleaseDir"
}

Write-Host "Installer ready: $($Installer.FullName)" -ForegroundColor Green
