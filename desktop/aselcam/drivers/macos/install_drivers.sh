#!/usr/bin/env bash
# AselCam Studio - macOS Virtual Camera & Audio Driver Automated Setup
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================================"
echo "       AselCam Studio - macOS Driver Auto-Installer     "
echo "========================================================"

# 1. Install CoreMediaIO DAL Virtual Camera Plugin
USER_DAL="$HOME/Library/CoreMediaIO/Plug-Ins/DAL"
SYSTEM_DAL="/Library/CoreMediaIO/Plug-Ins/DAL"

mkdir -p "$USER_DAL"
if [ -d "$DIR/obs-mac-virtualcam.plugin" ]; then
    echo "[*] Installing AselCam CoreMedia Virtual Camera Plugin..."
    rm -rf "$USER_DAL/obs-mac-virtualcam.plugin"
    cp -R "$DIR/obs-mac-virtualcam.plugin" "$USER_DAL/"
    xattr -cr "$USER_DAL/obs-mac-virtualcam.plugin" 2>/dev/null || true
    echo "[OK] CoreMedia virtual camera plugin installed to user DAL directory."
fi

# 2. Install BlackHole Virtual Audio Driver
SYSTEM_HAL="/Library/Audio/Plug-Ins/HAL"
if [ -d "$DIR/BlackHole2ch.driver" ]; then
    if [ ! -d "$SYSTEM_HAL/BlackHole2ch.driver" ]; then
        echo "[*] Installing BlackHole Virtual Audio Driver..."
        if [ "$EUID" -eq 0 ]; then
            cp -R "$DIR/BlackHole2ch.driver" "$SYSTEM_HAL/"
            killall -9 coreaudiod 2>/dev/null || true
        else
            # Try user-prompted osascript or package install if root is required
            if [ -f "$DIR/BlackHole2ch-0.7.1.pkg" ]; then
                osascript -e "do shell script \"installer -pkg '$DIR/BlackHole2ch-0.7.1.pkg' -target /\" with administrator privileges" 2>/dev/null || true
            else
                osascript -e "do shell script \"cp -R '$DIR/BlackHole2ch.driver' '$SYSTEM_HAL/' && killall -9 coreaudiod\" with administrator privileges" 2>/dev/null || true
            fi
        fi
    fi
fi

echo "[OK] AselCam macOS virtual camera and audio drivers configured."
exit 0
