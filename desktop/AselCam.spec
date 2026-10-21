# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['aselcam/main.py'],
    pathex=[],
    binaries=[('aselcam/bin/ffmpeg.exe', '.')],
    datas=[('aselcam', 'aselcam')],
    hiddenimports=['PyQt6', 'numpy', 'pyvirtualcam', 'PIL', 'cv2', 'imageio_ffmpeg'],
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
    [],
    exclude_binaries=True,
    name='AselCam',
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
    icon='aselcam/assets/aselcam_icon.ico',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AselCam',
)
