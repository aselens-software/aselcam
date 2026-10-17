@echo off
REM AselCam Desktop - Standalone Windows Executable Builder via PyInstaller
title Building AselCam Standalone Windows Executable...

echo [1/3] Installing build dependencies...
python -m pip install --upgrade pip pyinstaller -r requirements.txt

echo [2/3] Compiling AselCam.exe with PyInstaller...
pyinstaller --noconfirm --onedir --windowed ^
    --name "AselCam" ^
    --add-data "aselcam;aselcam" ^
    --hidden-import "PyQt6" ^
    --hidden-import "numpy" ^
    --hidden-import "pyvirtualcam" ^
    --hidden-import "cv2" ^
    aselcam/main.py

echo [3/3] Build finished! Executable available at dist\AselCam\AselCam.exe
pause
