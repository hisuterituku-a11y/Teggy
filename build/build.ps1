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

$PlaywrightPackageDir = Join-Path `
    $VenvDir `
    "Lib\site-packages\playwright\driver\package"
$PlaywrightSource = Join-Path $PlaywrightPackageDir ".local-browsers"
$PlaywrightDestination = Join-Path `
    $DistDir `
    "Teggy\_internal\playwright\driver\package\.local-browsers"

Set-Location $ProjectRoot

if ($Clean) {
    Write-Host "Очистка предыдущей сборки..." -ForegroundColor Cyan
    Remove-Item $DistDir -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item $WorkDir -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item $ReleaseDir -Recurse -Force -ErrorAction SilentlyContinue
}

if (-not (Test-Path $Python)) {
    Write-Host "Создание окружения сборки..." -ForegroundColor Cyan
    py -3 -m venv $VenvDir
}

& $Python -m pip install --upgrade pip
& $Python -m pip install -r (Join-Path $ProjectRoot "requirements.txt")
& $Python -m pip install -r (Join-Path $ProjectRoot "requirements-build.txt")

# Храним Chromium внутри установленного пакета Playwright, чтобы его можно было
# перенести в готовую сборку без установки браузера на компьютере пользователя.
$PreviousBrowsersPath = $env:PLAYWRIGHT_BROWSERS_PATH
$env:PLAYWRIGHT_BROWSERS_PATH = "0"

try {
    Write-Host "Установка Chromium для Playwright..." -ForegroundColor Cyan
    & $Python -m playwright install chromium

    if ($LASTEXITCODE -ne 0) {
        throw "Не удалось установить Chromium для Playwright."
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
    throw "Браузеры Playwright не найдены: $PlaywrightSource"
}

Write-Host "Сборка Teggy через PyInstaller..." -ForegroundColor Cyan
& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --distpath $DistDir `
    --workpath $WorkDir `
    $SpecFile

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller завершился с ошибкой."
}

$Executable = Join-Path $DistDir "Teggy\Teggy.exe"
if (-not (Test-Path $Executable)) {
    throw "Сборка завершилась без Teggy.exe: $Executable"
}

Write-Host "Добавление Chromium в сборку..." -ForegroundColor Cyan
New-Item `
    -ItemType Directory `
    -Path (Split-Path -Parent $PlaywrightDestination) `
    -Force | Out-Null

if (Test-Path $PlaywrightDestination) {
    Remove-Item $PlaywrightDestination -Recurse -Force
}

Copy-Item `
    -Path $PlaywrightSource `
    -Destination $PlaywrightDestination `
    -Recurse `
    -Force

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
    throw "В сборку не попал chrome.exe Playwright."
}

if (-not $HeadlessExecutable) {
    Write-Warning (
        "chrome-headless-shell.exe не найден. " +
        "Обычный Chromium добавлен, но headless-режим может не работать."
    )
}

Write-Host "Приложение собрано: $Executable" -ForegroundColor Green
Write-Host "Chromium добавлен: $($ChromiumExecutable.FullName)" -ForegroundColor Green

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
    throw (
        "Inno Setup 6 не найден. Установи его или запусти " +
        ".\build\build.ps1 -SkipInstaller"
    )
}

New-Item -ItemType Directory -Path $ReleaseDir -Force | Out-Null

Write-Host "Сборка установщика..." -ForegroundColor Cyan
& $Iscc $InstallerScript

if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup завершился с ошибкой."
}

$Installer = Get-ChildItem `
    -Path $ReleaseDir `
    -Filter "TeggySetup-*.exe" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (-not $Installer) {
    throw "Установщик не найден в $ReleaseDir"
}

Write-Host "Установщик готов: $($Installer.FullName)" -ForegroundColor Green
