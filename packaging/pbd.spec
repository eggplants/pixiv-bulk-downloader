from __future__ import annotations

from pathlib import Path

from PyInstaller.utils.hooks import copy_metadata

SPEC_DIR = Path(SPECPATH)  # noqa: F821
ROOT = SPEC_DIR.parent

# `pbd --version` reads the distribution metadata, which is not
# package content and so would otherwise be left behind.
datas = copy_metadata("pixiv-bulk-downloader")
binaries = []
hiddenimports = []

a = Analysis(  # noqa: F821
    [str(SPEC_DIR / "entrypoint.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["pytest", "tkinter"],
)
pyz = PYZ(a.pure)  # noqa: F821
exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="pbd",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
