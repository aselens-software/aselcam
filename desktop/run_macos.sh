#!/usr/bin/env bash
# AselCam Desktop - macOS Launcher
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v python3 &>/dev/null; then
    echo "[ERROR] python3 not found. Install via Homebrew: 'brew install python'"
    exit 1
fi

echo "[AselCam] Checking Python dependencies..."
python3 -m pip install -q -r "$SCRIPT_DIR/requirements.txt"

echo "[AselCam] Launching AselCam Studio on macOS..."
export PYTHONPATH="$SCRIPT_DIR"
exec python3 -m aselcam.main
