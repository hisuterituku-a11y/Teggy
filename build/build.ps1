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

Set-Location $ProjectRoot

if ($Clean) {
    Remove-Item $DistDir -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item $WorkDir -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item $ReleaseDir -Recurse -Force -ErrorAction SilentlyContinue
}

if (-not (Test-Path $Python)) {
    py -3 -m venv $VenvDir
}

& $Python -m pip install --upgrade pip
& $Python -m pip install -r (Join-Path $ProjectRoot "requirements.txt")
& $Python -m pip install -r (Join-Path $ProjectRoot "requirements-build.txt")

& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --distpath $DistDir `
    --workpath $WorkDir `
    $SpecFile

$Executable = Join-Path $DistDir "Teggy\Teggy.exe"
if (-not (Test-Path $Executable)) {
    throw "Сборка завершилась без Teggy.exe: $Executable"
}

Write-Host "Приложение собрано: $Executable" -ForegroundColor Green

if ($SkipInstaller) {
    exit 0
}

$IsccCandidates = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)
$Iscc = $IsccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $Iscc) {
    throw "Inno Setup 6 не найден. Установи его или запусти .\build\build.ps1 -SkipInstaller"
}

New-Item -ItemType Directory -Path $ReleaseDir -Force | Out-Null
& $Iscc $InstallerScript

$Installer = Get-ChildItem $ReleaseDir -Filter "TeggySetup-*.exe" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $Installer) {
    throw "Установщик не найден в $ReleaseDir"
}

Write-Host "Установщик готов: $($Installer.FullName)" -ForegroundColor Green
