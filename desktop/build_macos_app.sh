#!/usr/bin/env bash
# AselCam Desktop - Standalone macOS Application Bundle Builder (.app) via PyInstaller
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== [1/3] Installing build dependencies... ==="
python3 -m pip install --upgrade pip pyinstaller -r requirements.txt

echo "=== [2/3] Building AselCam.app with PyInstaller... ==="
pyinstaller --noconfirm --onedir --windowed \
    --name "AselCam" \
    --osx-bundle-identifier "com.aselcam.desktop" \
    --add-data "aselcam:aselcam" \
    --hidden-import "PyQt6" \
    --hidden-import "numpy" \
    --hidden-import "pyvirtualcam" \
    --hidden-import "cv2" \
    aselcam/main.py

echo "=== [3/3] Build finished! App bundle available at: $SCRIPT_DIR/dist/AselCam.app ==="
ls -lh dist/
