# -*- mode: python ; coding: utf-8 -*-
# 4R022 SAAT - PyInstaller derleme tanimi (spec) dosyasi
#
# Kullanim:
#   pyinstaller 4R022_Saat.spec
#
# Windows'ta tek dosyalik, konsolsuz bir .exe uretir ve assets/icon.ico
# simgesini hem .exe dosyasina hem de calisma zamaninda pencere/gorev
# cubugu simgesine gomer.

import sys
from pathlib import Path

block_cipher = None
# PyInstaller spec dosyalarinda __file__ tanimli degildir; bunun yerine
# PyInstaller'in kendiliginden sagladigi SPECPATH degiskenini kullaniyoruz.
project_dir = Path(SPECPATH).resolve()

a = Analysis(
    ['4R022_Saat.py'],
    pathex=[str(project_dir)],
    binaries=[],
    datas=[
        (str(project_dir / 'assets' / 'icon.ico'), 'assets'),
        (str(project_dir / 'assets' / 'icon.png'), 'assets'),
    ],
    hiddenimports=[
        'plyer.platforms.win.notification',
        'plyer.platforms.linux.notification',
        'plyer.platforms.macosx.notification',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='4R022_Saat',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_dir / 'assets' / 'icon.ico') if sys.platform == 'win32' else None,
)
