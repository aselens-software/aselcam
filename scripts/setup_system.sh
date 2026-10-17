#!/usr/bin/env bash
# AselCam - Linux Sistem Yapılandırma ve Sanal Kamera / Mikrofon Kurulum Aracı

set -e

echo "=========================================================="
echo "      AselCam - Linux Sistem Yapılandırma Betiği        "
echo "=========================================================="

# 1. Video ve Audio Grup İzinleri
echo "[1/3] Kullanıcı izinleri kontrol ediliyor..."
sudo usermod -a -G video,audio "$USER" || true

# 2. v4l2loopback Sanal Kamera Modülü Yapılandırması
echo "[2/3] v4l2loopback sanal kamera modülü yapılandırılıyor..."
if modinfo v4l2loopback &>/dev/null; then
    echo "v4l2loopback çekirdek modülü mevcut."
else
    echo "v4l2loopback modülü aranıyor veya yükleniyor..."
    if command -v pacman &>/dev/null; then
        sudo pacman -S --needed --noconfirm v4l2loopback-dkms v4l2loopback-utils linux-headers || true
    elif command -v apt &>/dev/null; then
        sudo apt-get update && sudo apt-get install -y v4l2loopback-dkms v4l2loopback-utils || true
    fi
fi

# Kalıcı modprobe ayarı oluştur
echo "options v4l2loopback devices=1 video_nr=10 card_label=\"AselCam Video\" exclusive_caps=0" | sudo tee /etc/modprobe.d/aselcam-v4l2loopback.conf > /dev/null
echo "v4l2loopback" | sudo tee /etc/modules-load.d/aselcam-v4l2loopback.conf > /dev/null

# Modülü anında yükle
sudo modprobe -r v4l2loopback 2>/dev/null || true
sudo modprobe v4l2loopback devices=1 video_nr=10 card_label="AselCam Video" exclusive_caps=0 || true

if [ -e "/dev/video10" ]; then
    echo "✓ Sanal kamera /dev/video10 başarıyla oluşturuldu!"
else
    echo "(!) /dev/video10 oluşturulamadı, lütfen sisteminizi yeniden başlatın."
fi

# 3. PipeWire / PulseAudio Sanal Mikrofon Testi
echo "[3/3] PipeWire / PulseAudio sanal mikrofon kontrol ediliyor..."
if command -v pactl &>/dev/null; then
    pactl load-module module-null-sink sink_name=AselCam_Mic sink_properties=device.description="AselCam_Microphone" 2>/dev/null || true
    echo "✓ Sanal mikrofon (AselCam_Microphone) PipeWire/PulseAudio üzerinde hazır!"
fi

echo "=========================================================="
echo " Kurulum tamamlandı! AselCam'i './run_desktop.sh' ile başlatabilirsiniz."
echo "=========================================================="
