# -*- mode: python ; coding: utf-8 -*-
# Empaqueta la app de escritorio junto con el build estático de React.
# Requiere haber corrido `npm --prefix gui/frontend run build` antes.

a = Analysis(
    ['gui/backend/app.py'],
    pathex=[],
    binaries=[],
    datas=[('gui/frontend/dist', 'dist'), ('packaging/icon.png', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='pdf-chapter-splitter-gui',
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
)
