#!/usr/bin/env bash
# AselCam macOS One-Click Installer & Runner
# Double-click this file in Finder to set permissions, configure direct drivers, and launch AselCam.

cd "$(dirname "$0")"

echo "=========================================================="
echo "          AselCam Studio - macOS Setup Utility           "
echo "=========================================================="
echo ""

# 1. Clear Gatekeeper quarantine flag if downloaded from browser
echo "[1/4] Configuring macOS security permissions..."
xattr -cr "AselCam.app" 2>/dev/null || true
chmod +x "AselCam.app/Contents/MacOS/AselCam"

# 2. Check for Homebrew / Python 3 / FFmpeg
echo "[2/4] Checking Python 3 and FFmpeg..."
if ! command -v python3 &>/dev/null && [ ! -x "/opt/homebrew/bin/python3" ]; then
    echo "(!) Python 3 was not detected."
    echo "Installing Homebrew Python is recommended:"
    echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    echo "  brew install python"
fi
if ! command -v ffmpeg &>/dev/null && [ ! -x "/opt/homebrew/bin/ffmpeg" ]; then
    echo "(!) FFmpeg is required for real-time video decoding."
    if command -v brew &>/dev/null; then
        echo "[*] Installing ffmpeg via Homebrew..."
        brew install ffmpeg 2>/dev/null || true
    else
        echo "Please install ffmpeg (brew install ffmpeg)."
    fi
fi

# 3. Configure Direct Virtual Camera & Audio Drivers
echo "[3/4] Configuring Direct CoreMedia Virtual Camera..."
USER_DAL="$HOME/Library/CoreMediaIO/Plug-Ins/DAL"
mkdir -p "$USER_DAL"
if [ -d "AselCam.app/Contents/Resources/aselcam/drivers/macos/obs-mac-virtualcam.plugin" ]; then
    rm -rf "$USER_DAL/obs-mac-virtualcam.plugin"
    cp -R "AselCam.app/Contents/Resources/aselcam/drivers/macos/obs-mac-virtualcam.plugin" "$USER_DAL/"
    xattr -cr "$USER_DAL/obs-mac-virtualcam.plugin" 2>/dev/null || true
    echo "[OK] Direct Virtual Camera plugin configured in user DAL."
fi

# Configure Virtual Audio Driver if pkg exists
PKG="AselCam.app/Contents/Resources/aselcam/drivers/macos/BlackHole2ch-0.7.1.pkg"
if [ -f "$PKG" ] && [ ! -d "/Library/Audio/Plug-Ins/HAL/BlackHole2ch.driver" ]; then
    echo "[*] Setting up Direct Virtual Microphone Driver (BlackHole 2ch)..."
    sudo installer -pkg "$PKG" -target / 2>/dev/null || true
fi

# 4. Launching
echo "[4/4] Launching AselCam Studio..."
open "AselCam.app"

echo ""
echo "AselCam has been launched! You can drag 'AselCam.app' to your /Applications folder."
echo "=========================================================="
