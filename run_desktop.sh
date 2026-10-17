#!/usr/bin/env bash
# AselCam Masaüstü Başlatıcı
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$BASE_DIR/desktop:$PYTHONPATH"
exec -a AselCam python3 "$BASE_DIR/desktop/aselcam/main.py" "$@"
