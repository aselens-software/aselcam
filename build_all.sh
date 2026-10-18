#!/usr/bin/env bash
# AselCam - Android APK ve Masaüstü Doğrulama Derleme Betiği
set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "=== [1/2] Android APK Derleniyor... ==="
cd "$BASE_DIR/android"
JAVA_HOME=/usr/lib/jvm/java-21-openjdk ./gradlew assembleRelease --no-daemon

echo "=== [2/2] APK Ana Dizine Kopyalanıyor... ==="
cp "$BASE_DIR/android/app/build/outputs/apk/release/app-release.apk" "$BASE_DIR/AselCam.apk"

echo "=== [Tamamlandı] AselCam.apk hazır: $BASE_DIR/AselCam.apk ==="
ls -lh "$BASE_DIR/AselCam.apk"
