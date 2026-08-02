param(
    [switch]$SkipInstaller,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvDir = Join-Path $ProjectRoot ".venv-build"
$Python = Join-Path $VenvDir "Scripts\python.exe"
$DistDir = Join-Path $ProjectRoot "dist"
$WorkDir = Join-Path $ProjectRoot "build\pyinstaller-work"
$SpecFile = Join-Path $ProjectRoot "build\Teggy.spec"
$InstallerScript = Join-Path $ProjectRoot "build\installer\Teggy.iss"
$ReleaseDir = Join-Path $ProjectRoot "release"

$PlaywrightPackageDir = Join-Path $VenvDir "Lib\site-packages\playwright\driver\package"
$PlaywrightSource = Join-Path $PlaywrightPackageDir ".local-browsers"
$PlaywrightDestination = Join-Path $DistDir "Teggy\_internal\playwright\driver\package\.local-browsers"
$BundledFfmpeg = Join-Path $DistDir "Teggy\ffmpeg.exe"

Set-Location $ProjectRoot

if ($Clean) {
    Write-Host "Cleaning previous build..." -ForegroundColor Cyan
    Remove-Item $DistDir -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item $WorkDir -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item $ReleaseDir -Recurse -Force -ErrorAction SilentlyContinue
}

if (-not (Test-Path $Python)) {
    Write-Host "Creating build virtual environment..." -ForegroundColor Cyan
    py -3 -m venv $VenvDir
}

Write-Host "Installing Python dependencies..." -ForegroundColor Cyan
& $Python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    throw "pip upgrade failed."
}

& $Python -m pip install -r (Join-Path $ProjectRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) {
    throw "Runtime dependency installation failed."
}

& $Python -m pip install -r (Join-Path $ProjectRoot "requirements-build.txt")
if ($LASTEXITCODE -ne 0) {
    throw "Build dependency installation failed."
}

$FfmpegCommand = Get-Command ffmpeg.exe -ErrorAction SilentlyContinue
if (-not $FfmpegCommand) {
    $FfmpegCommand = Get-Command ffmpeg -ErrorAction SilentlyContinue
}
if (-not $FfmpegCommand) {
    throw "System ffmpeg.exe was not found. Install FFmpeg before building Teggy."
}
$FfmpegSource = $FfmpegCommand.Source
if (-not (Test-Path $FfmpegSource -PathType Leaf)) {
    throw "Resolved FFmpeg path is invalid: $FfmpegSource"
}
Write-Host "FFmpeg found: $FfmpegSource" -ForegroundColor Cyan

# Install Chromium inside the Playwright package so it can be copied into dist.
$PreviousBrowsersPath = $env:PLAYWRIGHT_BROWSERS_PATH
$env:PLAYWRIGHT_BROWSERS_PATH = "0"

try {
    Write-Host "Installing Playwright Chromium..." -ForegroundColor Cyan
    & $Python -m playwright install chromium
    if ($LASTEXITCODE -ne 0) {
        throw "Playwright Chromium installation failed."
    }
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
    throw "Playwright browser directory was not found: $PlaywrightSource"
}

Write-Host "Building Teggy with PyInstaller..." -ForegroundColor Cyan
& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --distpath $DistDir `
    --workpath $WorkDir `
    $SpecFile

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed."
}

$Executable = Join-Path $DistDir "Teggy\Teggy.exe"
if (-not (Test-Path $Executable)) {
    throw "Teggy.exe was not created: $Executable"
}

Write-Host "Copying FFmpeg into the application bundle..." -ForegroundColor Cyan
Copy-Item -Path $FfmpegSource -Destination $BundledFfmpeg -Force
if (-not (Test-Path $BundledFfmpeg -PathType Leaf)) {
    throw "ffmpeg.exe was not copied into the build: $BundledFfmpeg"
}

Write-Host "Copying Chromium into the application bundle..." -ForegroundColor Cyan
$PlaywrightDestinationParent = Split-Path -Parent $PlaywrightDestination
New-Item -ItemType Directory -Path $PlaywrightDestinationParent -Force | Out-Null

if (Test-Path $PlaywrightDestination) {
    Remove-Item $PlaywrightDestination -Recurse -Force
}

Copy-Item -Path $PlaywrightSource -Destination $PlaywrightDestination -Recurse -Force

$ChromiumExecutable = Get-ChildItem `
    -Path $PlaywrightDestination `
    -Recurse `
    -Filter "chrome.exe" `
    -ErrorAction SilentlyContinue |
    Select-Object -First 1

$HeadlessExecutable = Get-ChildItem `
    -Path $PlaywrightDestination `
    -Recurse `
    -Filter "chrome-headless-shell.exe" `
    -ErrorAction SilentlyContinue |
    Select-Object -First 1

if (-not $ChromiumExecutable) {
    throw "Playwright chrome.exe was not copied into the build."
}

if (-not $HeadlessExecutable) {
    Write-Warning "chrome-headless-shell.exe was not found. Visible Chromium is bundled, but headless mode may fail."
}

Write-Host "Application built: $Executable" -ForegroundColor Green
Write-Host "Bundled FFmpeg: $BundledFfmpeg" -ForegroundColor Green
Write-Host "Bundled Chromium: $($ChromiumExecutable.FullName)" -ForegroundColor Green

if ($SkipInstaller) {
    exit 0
}

$IsccCandidates = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)

$Iscc = $IsccCandidates |
    Where-Object { Test-Path $_ } |
    Select-Object -First 1

if (-not $Iscc -and (Test-Path "X:\")) {
    $Iscc = Get-ChildItem `
        -Path "X:\" `
        -Filter "ISCC.exe" `
        -Recurse `
        -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -like "*Inno Setup 6*" } |
        Select-Object -First 1 -ExpandProperty FullName
}

if (-not $Iscc) {
    throw "Inno Setup 6 was not found. Install it or run build.ps1 with -SkipInstaller."
}

New-Item -ItemType Directory -Path $ReleaseDir -Force | Out-Null

Write-Host "Building installer..." -ForegroundColor Cyan
& $Iscc $InstallerScript
if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup failed."
}

$Installer = Get-ChildItem `
    -Path $ReleaseDir `
    -Filter "TeggySetup-*.exe" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (-not $Installer) {
    throw "Installer was not found in $ReleaseDir"
}

Write-Host "Installer built: $($Installer.FullName)" -ForegroundColor Green
