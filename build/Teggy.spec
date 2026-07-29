# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


PROJECT_ROOT = Path(SPECPATH).parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
FFMPEG_CANDIDATES = (
    PROJECT_ROOT / "tools" / "ffmpeg.exe",
    PROJECT_ROOT / "ffmpeg.exe",
)


datas = []
if ASSETS_DIR.is_dir():
    datas.append((str(ASSETS_DIR), "assets"))

binaries = []
for candidate in FFMPEG_CANDIDATES:
    if candidate.is_file():
        binaries.append((str(candidate), "."))
        break

hiddenimports = collect_submodules("PySide6")

analysis = Analysis(
    [str(PROJECT_ROOT / "main.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="Teggy",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

collection = COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Teggy",
)
