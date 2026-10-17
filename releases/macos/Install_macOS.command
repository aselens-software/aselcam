#!/usr/bin/env bash
# AselCam macOS One-Click Installer & Runner
# Double-click this file in Finder to set permissions and launch AselCam.

cd "$(dirname "$0")"

echo "=========================================================="
echo "          AselCam Studio - macOS Setup Utility           "
echo "=========================================================="
echo ""

# 1. Clear Gatekeeper quarantine flag if downloaded from browser
echo "[1/3] Configuring macOS security permissions..."
xattr -cr "AselCam.app" 2>/dev/null || true
chmod +x "AselCam.app/Contents/MacOS/AselCam"

# 2. Check for Homebrew / Python 3
echo "[2/3] Checking Python 3..."
if ! command -v python3 &>/dev/null && [ ! -x "/opt/homebrew/bin/python3" ]; then
    echo "(!) Python 3 was not detected."
    echo "Installing Homebrew Python is recommended:"
    echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    echo "  brew install python"
fi

# 3. Launching
echo "[3/3] Launching AselCam Studio..."
open "AselCam.app"

echo ""
echo "AselCam has been launched! You can drag 'AselCam.app' to your /Applications folder."
echo "=========================================================="
