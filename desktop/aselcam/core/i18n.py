import os
import sys
import locale
from typing import Dict, Any, Optional, Callable, List

SUPPORTED_LANGUAGES = {
    "en": "English",
    "tr": "Türkçe",
    "de": "Deutsch",
    "fr": "Français",
    "es": "Español"
}

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        # Title & Tabs
        "app_title": "AselCam - Ultra Low-Latency Virtual Camera Studio",
        "tab_studio": "Studio",
        "version_tag": "v1.2",

        # Telemetry & Status
        "status_offline": "● OFFLINE",
        "status_connecting": "● CONNECTING",
        "status_live": "● LIVE",
        "status_standby": "● STANDBY",
        "device_info": "DEVICE: {model}",
        "battery_info": "BATTERY: {pct}%",
        "ping_info": "PING: {ms} ms",
        "waiting_stream": "Waiting for camera stream...",
        "waiting_screen": "Waiting for screen stream...",
        "waiting_subtext": "Start stream on mobile or click 'Start Camera' above.",
        "screen_permission_hint": "Please confirm 'Start now' screen recording prompt on your phone.",
        "screen_mirror_active": "Screen Mirroring Active",
        "live_preview": "LIVE PREVIEW",
        "background_streaming": "● Background Stream Active",
        "power_saving_mode": "● GPU & Display energy saving mode active",

        # Window Controls
        "win_min": "Minimize",
        "win_max": "Maximize / Restore",
        "win_close": "Close",

        # Language Selector
        "lang_label": "Language",
        "lang_auto": "Auto",

        # Connection Panel
        "conn_header": "CONNECTION",
        "conn_usb": "USB (ADB - Low Latency)",
        "conn_wifi": "Wi-Fi (Wireless Network)",
        "conn_ip_placeholder": "Phone IP (e.g. 192.168.1.50)",
        "conn_btn_start": "Start Camera",
        "conn_btn_stop": "Stop Camera",
        "conn_auto_connect": "Auto-connect when phone detected",
        "conn_screen_mirror": "Mirror Screen",
        "conn_stop_mirror": "Stop Mirror",
        "device_found": "Device detected: {desc}",
        "no_device": "No USB device found",
        "searching_devices": "Scanning for devices...",
        "refresh": "Refresh",
        "driver_ready": "● Driver Ready",
        "driver_missing": "● Driver Standby",

        # Camera Quick Controls
        "ctrl_switch_cam": "Switch Camera",
        "ctrl_torch": "Flashlight",
        "ctrl_blackout": "Mute Video",
        "ctrl_audio": "Microphone",
        "preview_toggle_off": "Hide Preview",
        "preview_toggle_on": "Show Preview",
        "preview_tooltip": "Toggles video viewfinder. Disabling drops GPU/CPU consumption to near zero.",
        "blackout_toggle_on": "Mute Video",
        "blackout_toggle_off": "Unmute Video",
        "mic_toggle_off": "Mute Mic",
        "mic_toggle_on": "Unmute Mic",
        "front_cam": "Front Camera",
        "back_cam": "Back Camera",

        # Hardware Zoom
        "zoom_header": "OPTICAL & HARDWARE ZOOM",
        "zoom_wide": "1x Wide",
        "zoom_tele": "3x Telephoto",
        "zoom_periscope": "10x Periscope",
        "zoom_space": "100x Space Zoom",
        "zoom_level": "{level:.1f}x Zoom",

        # RAW & Color Science
        "raw_header": "RAW SENSOR & COLOR SCIENCE",
        "color_profiles": "Color Profile",
        "profile_standard": "Standard (Natural)",
        "profile_vivid": "Vivid Stream (Punchy)",
        "profile_cinema": "Cinematic Warm (Cine)",
        "profile_portrait": "Studio Portrait (Soft)",
        "profile_lowlight": "Low Light / Night",
        "profile_vintage": "Retro / Vintage Film",
        "profile_bw": "Monochrome B&W",
        "profile_custom": "Custom Tuning",

        "tone_curve": "Tone Curve",
        "curve_linear": "Linear",
        "curve_film": "Film S-Curve",
        "curve_portrait": "Portrait (Smooth)",
        "curve_vivid": "Vivid Contrast",
        "curve_vintage": "Vintage Matte",

        "raw_exposure": "Exposure",
        "raw_highlights": "Highlights",
        "raw_shadows": "Shadows",
        "raw_whites": "Whites",
        "raw_blacks": "Blacks",
        "raw_contrast": "Contrast",
        "raw_brightness": "Brightness",
        "raw_temp": "Temperature",
        "raw_tint": "Tint",
        "raw_saturation": "Saturation",
        "raw_vibrance": "Vibrance",
        "raw_sharpness": "Laplacian Sharpness",

        "rgb_balance": "RGB Channel Balance",
        "red_gain": "Red Gain",
        "green_gain": "Green Gain",
        "blue_gain": "Blue Gain",
        "btn_reset_filters": "Reset All Color Settings",

        # AI Focus & Background
        "focus_header": "AI PORTRAIT & BACKGROUND FOCUS",
        "focus_enable": "Enable AI Subject Isolation",
        "focus_mode_blur": "Bokeh Lens Blur",
        "focus_mode_studio": "Studio Spotlight",
        "focus_mode_custom": "Custom Virtual Background",
        "focus_choose_img": "Select Image...",
        "focus_blur_amount": "Blur Intensity",
        "focus_radius": "Focus Depth",

        # Audio Sink
        "audio_sink_label": "AUDIO",
        "audio_level": "Level",
        "audio_muted": "Muted",
        "audio_active": "Active",

        # Messages & Dialogs
        "dialog_img_filter": "Image Files (*.png *.jpg *.jpeg *.webp *.bmp)",
        "dialog_select_bg": "Select Virtual Background Image",
        "err_connection_failed": "Failed to connect to phone stream.",
        "err_adb_not_found": "ADB executable not found. Please install Android Platform Tools.",
        "vcam_ready": "Virtual Camera Ready: {dev}",
        "vcam_active": "Broadcasting to {dev}"
    },
    "tr": {
        # Title & Tabs
        "app_title": "AselCam - Ultra Düşük Gecikmeli Sanal Kamera Stüdyosu",
        "tab_studio": "Stüdyo",
        "version_tag": "v1.2",

        # Telemetry & Status
        "status_offline": "● ÇEVRİMDIŞI",
        "status_connecting": "● BAĞLANILIYOR",
        "status_live": "● CANLI",
        "status_standby": "● BEKLEMEDE",
        "device_info": "CİHAZ: {model}",
        "battery_info": "PİL: {pct}%",
        "ping_info": "PING: {ms} ms",
        "waiting_stream": "Kamera akışı bekleniyor...",
        "waiting_screen": "Telefon ekran akışı bekleniyor...",
        "waiting_subtext": "Mobilde yayını başlatın veya yukarıdaki 'Bağlan' butonuna basın.",
        "screen_permission_hint": "Telefonda açılan ekranda 'Şimdi başlat' iznini onaylayın.",
        "screen_mirror_active": "Ekran Paylaşımı Aktif",
        "live_preview": "CANLI ÖNİZLEME",
        "background_streaming": "● Arka Planda Canlı Yayın Devam Ediyor",
        "power_saving_mode": "● GPU ve Ekran tasarruf modu devrede",

        # Window Controls
        "win_min": "Simge Durumuna Küçült",
        "win_max": "Ekranı Kapla / Geri Yükle",
        "win_close": "Kapat",

        # Language Selector
        "lang_label": "Dil",
        "lang_auto": "Otomatik",

        # Connection Panel
        "conn_header": "BAĞLANTI",
        "conn_usb": "USB (ADB - Düşük Gecikme)",
        "conn_wifi": "Wi-Fi (Kablosuz)",
        "conn_ip_placeholder": "Telefon IP (örn: 192.168.1.50)",
        "conn_btn_start": "Bağlan",
        "conn_btn_stop": "Bağlantıyı Kes",
        "conn_auto_connect": "Telefon algılandığında otomatik bağlan",
        "conn_screen_mirror": "Ekranı Yansıt",
        "conn_stop_mirror": "Yayını Durdur",
        "device_found": "Cihaz bulundu: {desc}",
        "no_device": "USB cihazı bulunamadı",
        "searching_devices": "Cihazlar taranıyor...",
        "refresh": "Yenile",
        "driver_ready": "● Sürücü Hazır",
        "driver_missing": "● Sürücü Beklemede",

        # Camera Quick Controls
        "ctrl_switch_cam": "Kamera Değiştir",
        "ctrl_torch": "Flaş Işığı",
        "ctrl_blackout": "Görüntüyü Karart",
        "ctrl_audio": "Mikrofon",
        "preview_toggle_off": "Önizlemeyi Kapat",
        "preview_toggle_on": "Önizlemeyi Aç",
        "preview_tooltip": "Bilgisayarda ekran önizlemesini açıp kapatır. Kapatıldığında GPU ve CPU yükü sıfıra iner.",
        "blackout_toggle_on": "Kamerayı Karart",
        "blackout_toggle_off": "Görüntüyü Aç",
        "mic_toggle_off": "Mikrofonu Kapat",
        "mic_toggle_on": "Mikrofonu Aç",
        "front_cam": "Ön Kamera",
        "back_cam": "Arka Kamera",

        # Hardware Zoom
        "zoom_header": "DONANIMSAL ZOOM",
        "zoom_wide": "1x Geniş",
        "zoom_tele": "3x Telefoto",
        "zoom_periscope": "10x Periskop",
        "zoom_space": "100x Uzay Zoom",
        "zoom_level": "{level:.1f}x Zoom",

        # RAW & Color Science
        "raw_header": "RAW SENSÖR & RENK BİLİMİ",
        "color_profiles": "Renk Profili",
        "profile_standard": "Standart (Doğal)",
        "profile_vivid": "Canlı Yayın (Vivid)",
        "profile_cinema": "Sinematik Sıcak (Cine)",
        "profile_portrait": "Stüdyo Portre (Yumuşak)",
        "profile_lowlight": "Düşük Işık / Gece",
        "profile_vintage": "Retro / Vintage",
        "profile_bw": "Siyah & Beyaz (B&W Mono)",
        "profile_custom": "Özel Ayar",

        "tone_curve": "Ton Eğrisi",
        "curve_linear": "Doğrusal",
        "curve_film": "Film S-Eğrisi",
        "curve_portrait": "Portre (Pürüzsüz)",
        "curve_vivid": "Canlı Kontrast",
        "curve_vintage": "Vintage Mat",

        "raw_exposure": "Pozlama",
        "raw_highlights": "Açık Tonlar",
        "raw_shadows": "Gölgeler",
        "raw_whites": "Beyaz Noktası",
        "raw_blacks": "Siyah Noktası",
        "raw_contrast": "Kontrast",
        "raw_brightness": "Parlaklık",
        "raw_temp": "Renk Sıcaklığı",
        "raw_tint": "Renk Tonu (Tint)",
        "raw_saturation": "Doygunluk",
        "raw_vibrance": "Canlılık (Vibrance)",
        "raw_sharpness": "Laplacian Keskinlik",

        "rgb_balance": "RGB Denge Ayarı",
        "red_gain": "Kırmızı Denge",
        "green_gain": "Yeşil Denge",
        "blue_gain": "Mavi Denge",
        "btn_reset_filters": "Tüm Ayarları Sıfırla",

        # AI Focus & Background
        "focus_header": "YAPAY ZEKA PORTRE & ODAK",
        "focus_enable": "Yapay Zeka Odaklama Sistemini Aç",
        "focus_mode_blur": "Portre Bokeh Bulanıklığı",
        "focus_mode_studio": "Stüdyo Işığı (Vinyet)",
        "focus_mode_custom": "Özel Sanal Arka Plan",
        "focus_choose_img": "Görsel Seç...",
        "focus_blur_amount": "Bulanıklık Miktarı",
        "focus_radius": "Odak Derinliği",

        # Audio Sink
        "audio_sink_label": "SES",
        "audio_level": "Düzey",
        "audio_muted": "Sessiz",
        "audio_active": "Aktif",

        # Messages & Dialogs
        "dialog_img_filter": "Resim Dosyaları (*.png *.jpg *.jpeg *.webp *.bmp)",
        "dialog_select_bg": "Sanal Arkaplan Görseli Seçin",
        "err_connection_failed": "Telefon video akışına bağlanılamadı.",
        "err_adb_not_found": "ADB bulunamadı. Lütfen Android Platform Araçlarını kurun.",
        "vcam_ready": "Sanal Kamera Hazır: {dev}",
        "vcam_active": "Yayınlanıyor: {dev}"
    },
    "de": {
        # Title & Tabs
        "app_title": "AselCam - Ultra-Latenzfreies Virtuelles Kamera-Studio",
        "tab_studio": "Studio",
        "version_tag": "v1.2",

        # Telemetry & Status
        "status_offline": "● OFFLINE",
        "status_connecting": "● VERBINDEN",
        "status_live": "● LIVE",
        "status_standby": "● BEREIT",
        "device_info": "GERÄT: {model}",
        "battery_info": "AKKU: {pct}%",
        "ping_info": "PING: {ms} ms",
        "waiting_stream": "Warten auf Kamerastream...",
        "waiting_screen": "Warten auf Bildschirmübertragung...",
        "waiting_subtext": "Stream auf dem Smartphone starten oder oben auf 'Verbinden' klicken.",
        "screen_permission_hint": "Bitte 'Jetzt starten' auf dem Smartphone bestätigen.",
        "screen_mirror_active": "Bildschirmübertragung aktiv",
        "live_preview": "LIVE-VORSCHAU",
        "background_streaming": "● Hintergrund-Stream aktiv",
        "power_saving_mode": "● GPU- und Display-Energiesparmodus aktiv",

        # Window Controls
        "win_min": "Minimieren",
        "win_max": "Maximieren / Wiederherstellen",
        "win_close": "Schließen",

        # Language Selector
        "lang_label": "Sprache",
        "lang_auto": "Automatisch",

        # Connection Panel
        "conn_header": "VERBINDUNG",
        "conn_usb": "USB (ADB - Geringe Latenz)",
        "conn_wifi": "WLAN (Drahtlos)",
        "conn_ip_placeholder": "Smartphone-IP (z.B. 192.168.1.50)",
        "conn_btn_start": "Verbinden",
        "conn_btn_stop": "Trennen",
        "conn_auto_connect": "Automatisch verbinden bei Erkennung",
        "conn_screen_mirror": "Bildschirm spiegeln",
        "conn_stop_mirror": "Spiegelung stoppen",
        "device_found": "Gerät gefunden: {desc}",
        "no_device": "Kein USB-Gerät gefunden",
        "searching_devices": "Geräte werden gesucht...",
        "refresh": "Aktualisieren",
        "driver_ready": "● Treiber bereit",
        "driver_missing": "● Treiber Standby",

        # Camera Quick Controls
        "ctrl_switch_cam": "Kamera wechseln",
        "ctrl_torch": "Taschenlampe",
        "ctrl_blackout": "Video stummschalten",
        "ctrl_audio": "Mikrofon",
        "preview_toggle_off": "Vorschau ausblenden",
        "preview_toggle_on": "Vorschau anzeigen",
        "preview_tooltip": "Schaltet die Videovorschau ein/aus. Spart GPU/CPU.",
        "blackout_toggle_on": "Video stummschalten",
        "blackout_toggle_off": "Video aktivieren",
        "mic_toggle_off": "Mikrofon stummschalten",
        "mic_toggle_on": "Mikrofon aktivieren",
        "front_cam": "Frontkamera",
        "back_cam": "Hauptkamera",

        # Hardware Zoom
        "zoom_header": "OPTISCHER & HARDWARE-ZOOM",
        "zoom_wide": "1x Weitwinkel",
        "zoom_tele": "3x Teleobjektiv",
        "zoom_periscope": "10x Periskop",
        "zoom_space": "100x Space-Zoom",
        "zoom_level": "{level:.1f}x Zoom",

        # RAW & Color Science
        "raw_header": "RAW-SENSOR & FARBWISSENSCHAFT",
        "color_profiles": "Farbprofil",
        "profile_standard": "Standard (Natürlich)",
        "profile_vivid": "Lebendig (Vivid Stream)",
        "profile_cinema": "Kino Warm (Cine)",
        "profile_portrait": "Studio-Porträt (Sanft)",
        "profile_lowlight": "Schwachlicht / Nacht",
        "profile_vintage": "Retro / Vintage Film",
        "profile_bw": "Monochrom S&W",
        "profile_custom": "Benutzerdefiniert",

        "tone_curve": "Gradationskurve",
        "curve_linear": "Linear",
        "curve_film": "Film S-Kurve",
        "curve_portrait": "Porträt (Glatt)",
        "curve_vivid": "Lebendiger Kontrast",
        "curve_vintage": "Vintage Matt",

        "raw_exposure": "Belichtung",
        "raw_highlights": "Lichter",
        "raw_shadows": "Schatten",
        "raw_whites": "Weißtöne",
        "raw_blacks": "Schwarztöne",
        "raw_contrast": "Kontrast",
        "raw_brightness": "Helligkeit",
        "raw_temp": "Farbtemperatur",
        "raw_tint": "Farbtönung",
        "raw_saturation": "Sättigung",
        "raw_vibrance": "Dynamik",
        "raw_sharpness": "Laplace-Schärfe",

        "rgb_balance": "RGB-Farbabgleich",
        "red_gain": "Rot-Verstärkung",
        "green_gain": "Grün-Verstärkung",
        "blue_gain": "Blau-Verstärkung",
        "btn_reset_filters": "Einstellungen zurücksetzen",

        # AI Focus & Background
        "focus_header": "KI-PORTRÄT & HINTERGRUND",
        "focus_enable": "KI-Subjekttrennung aktivieren",
        "focus_mode_blur": "Bokeh-Unschärfe",
        "focus_mode_studio": "Studio-Spotlight",
        "focus_mode_custom": "Virtueller Hintergrund",
        "focus_choose_img": "Bild auswählen...",
        "focus_blur_amount": "Unschärfe-Intensität",
        "focus_radius": "Fokustiefe",

        # Audio Sink
        "audio_sink_label": "AUDIO",
        "audio_level": "Pegel",
        "audio_muted": "Stumm",
        "audio_active": "Aktiv",

        # Messages & Dialogs
        "dialog_img_filter": "Bilddateien (*.png *.jpg *.jpeg *.webp *.bmp)",
        "dialog_select_bg": "Hintergrundbild auswählen",
        "err_connection_failed": "Verbindung zum Smartphone-Stream fehlgeschlagen.",
        "err_adb_not_found": "ADB nicht gefunden. Bitte Android Platform Tools installieren.",
        "vcam_ready": "Virtuelle Kamera bereit: {dev}",
        "vcam_active": "Sendet an {dev}"
    },
    "fr": {
        # Title & Tabs
        "app_title": "AselCam - Studio de Caméra Virtuelle Ultra Faible Latence",
        "tab_studio": "Studio",
        "version_tag": "v1.2",

        # Telemetry & Status
        "status_offline": "● HORS LIGNE",
        "status_connecting": "● CONNEXION",
        "status_live": "● EN DIRECT",
        "status_standby": "● VEILLE",
        "device_info": "APPAREIL: {model}",
        "battery_info": "BATTERIE: {pct}%",
        "ping_info": "PING: {ms} ms",
        "waiting_stream": "En attente du flux vidéo...",
        "waiting_screen": "En attente du flux d'écran...",
        "waiting_subtext": "Démarrez le flux sur mobile ou cliquez sur 'Connecter'.",
        "screen_permission_hint": "Veuillez confirmer 'Commencer maintenant' sur le téléphone.",
        "screen_mirror_active": "Partage d'écran actif",
        "live_preview": "APERÇU EN DIRECT",
        "background_streaming": "● Diffusion en arrière-plan active",
        "power_saving_mode": "● Mode économie d'énergie GPU et écran actif",

        # Window Controls
        "win_min": "Réduire",
        "win_max": "Agrandir / Restaurer",
        "win_close": "Fermer",

        # Language Selector
        "lang_label": "Langue",
        "lang_auto": "Automatique",

        # Connection Panel
        "conn_header": "CONNEXION",
        "conn_usb": "USB (ADB - Faible Latence)",
        "conn_wifi": "Wi-Fi (Sans fil)",
        "conn_ip_placeholder": "IP du smartphone (ex: 192.168.1.50)",
        "conn_btn_start": "Connecter",
        "conn_btn_stop": "Déconnecter",
        "conn_auto_connect": "Connexion auto dès détection",
        "conn_screen_mirror": "Miroir d'écran",
        "conn_stop_mirror": "Arrêter miroir",
        "device_found": "Appareil détecté: {desc}",
        "no_device": "Aucun appareil USB détecté",
        "searching_devices": "Recherche d'appareils...",
        "refresh": "Actualiser",
        "driver_ready": "● Pilote prêt",
        "driver_missing": "● Pilote en veille",

        # Camera Quick Controls
        "ctrl_switch_cam": "Changer de caméra",
        "ctrl_torch": "Lampe torche",
        "ctrl_blackout": "Masquer la vidéo",
        "ctrl_audio": "Microphone",
        "preview_toggle_off": "Masquer l'aperçu",
        "preview_toggle_on": "Afficher l'aperçu",
        "preview_tooltip": "Bascule l'aperçu vidéo. Économise le GPU et CPU.",
        "blackout_toggle_on": "Masquer la vidéo",
        "blackout_toggle_off": "Afficher la vidéo",
        "mic_toggle_off": "Couper le micro",
        "mic_toggle_on": "Activer le micro",
        "front_cam": "Caméra avant",
        "back_cam": "Caméra arrière",

        # Hardware Zoom
        "zoom_header": "ZOOM OPTIQUE & MATÉRIEL",
        "zoom_wide": "1x Grand angle",
        "zoom_tele": "3x Téléobjectif",
        "zoom_periscope": "10x Périscope",
        "zoom_space": "100x Space Zoom",
        "zoom_level": "{level:.1f}x Zoom",

        # RAW & Color Science
        "raw_header": "CAPTEUR RAW & SCIENCE DES COULEURS",
        "color_profiles": "Profil de couleur",
        "profile_standard": "Standard (Naturel)",
        "profile_vivid": "Éclatant (Vivid)",
        "profile_cinema": "Cinéma Chaud (Cine)",
        "profile_portrait": "Portrait Studio (Doux)",
        "profile_lowlight": "Basse lumière / Nuit",
        "profile_vintage": "Rétro / Vintage Film",
        "profile_bw": "Noir & Blanc",
        "profile_custom": "Personnalisé",

        "tone_curve": "Courbe de tonalité",
        "curve_linear": "Linéaire",
        "curve_film": "Courbe Film S",
        "curve_portrait": "Portrait (Lisse)",
        "curve_vivid": "Contraste Éclatant",
        "curve_vintage": "Vintage Mat",

        "raw_exposure": "Exposition",
        "raw_highlights": "Hautes lumières",
        "raw_shadows": "Ombres",
        "raw_whites": "Blancs",
        "raw_blacks": "Noirs",
        "raw_contrast": "Contraste",
        "raw_brightness": "Luminosité",
        "raw_temp": "Température de couleur",
        "raw_tint": "Teinte",
        "raw_saturation": "Saturation",
        "raw_vibrance": "Vibrance",
        "raw_sharpness": "Netteté Laplacienne",

        "rgb_balance": "Balance RVB",
        "red_gain": "Gain Rouge",
        "green_gain": "Gain Vert",
        "blue_gain": "Gain Bleu",
        "btn_reset_filters": "Réinitialiser les réglages",

        # AI Focus & Background
        "focus_header": "PORTRAIT IA & ARRIÈRE-PLAN",
        "focus_enable": "Activer le détourage IA du sujet",
        "focus_mode_blur": "Flou bokeh d'objectif",
        "focus_mode_studio": "Éclairage Studio",
        "focus_mode_custom": "Arrière-plan personnalisé",
        "focus_choose_img": "Choisir une image...",
        "focus_blur_amount": "Intensité du flou",
        "focus_radius": "Profondeur de champ",

        # Audio Sink
        "audio_sink_label": "AUDIO",
        "audio_level": "Niveau",
        "audio_muted": "Muet",
        "audio_active": "Actif",

        # Messages & Dialogs
        "dialog_img_filter": "Fichiers image (*.png *.jpg *.jpeg *.webp *.bmp)",
        "dialog_select_bg": "Sélectionner une image d'arrière-plan",
        "err_connection_failed": "Échec de connexion au flux vidéo.",
        "err_adb_not_found": "ADB introuvable. Veuillez installer Android Platform Tools.",
        "vcam_ready": "Caméra virtuelle prête: {dev}",
        "vcam_active": "Diffusion vers {dev}"
    },
    "es": {
        # Title & Tabs
        "app_title": "AselCam - Estudio de Cámara Virtual de Ultra Baja Latencia",
        "tab_studio": "Estudio",
        "version_tag": "v1.2",

        # Telemetry & Status
        "status_offline": "● DESCONECTADO",
        "status_connecting": "● CONECTANDO",
        "status_live": "● EN VIVO",
        "status_standby": "● EN ESPERA",
        "device_info": "DISPOSITIVO: {model}",
        "battery_info": "BATERÍA: {pct}%",
        "ping_info": "PING: {ms} ms",
        "waiting_stream": "Esperando transmisión de cámara...",
        "waiting_screen": "Esperando transmisión de pantalla...",
        "waiting_subtext": "Inicie la transmisión en el móvil o pulse 'Conectar'.",
        "screen_permission_hint": "Confirme 'Iniciar ahora' en el móvil.",
        "screen_mirror_active": "Reflejo de pantalla activo",
        "live_preview": "VISTA PREVIA EN VIVO",
        "background_streaming": "● Transmisión en segundo plano activa",
        "power_saving_mode": "● Modo de ahorro de energía GPU y pantalla activo",

        # Window Controls
        "win_min": "Minimizar",
        "win_max": "Maximizar / Restaurar",
        "win_close": "Cerrar",

        # Language Selector
        "lang_label": "Idioma",
        "lang_auto": "Automático",

        # Connection Panel
        "conn_header": "CONEXIÓN",
        "conn_usb": "USB (ADB - Baja Latencia)",
        "conn_wifi": "Wi-Fi (Inalámbrico)",
        "conn_ip_placeholder": "IP del móvil (ej. 192.168.1.50)",
        "conn_btn_start": "Conectar",
        "conn_btn_stop": "Desconectar",
        "conn_auto_connect": "Conexión auto si se detecta",
        "conn_screen_mirror": "Reflejar Pantalla",
        "conn_stop_mirror": "Detener Reflejo",
        "device_found": "Dispositivo detectado: {desc}",
        "no_device": "No se encontró dispositivo USB",
        "searching_devices": "Buscando dispositivos...",
        "refresh": "Actualizar",
        "driver_ready": "● Controlador listo",
        "driver_missing": "● Controlador en espera",

        # Camera Quick Controls
        "ctrl_switch_cam": "Cambiar Cámara",
        "ctrl_torch": "Linterna",
        "ctrl_blackout": "Silenciar Video",
        "ctrl_audio": "Micrófono",
        "preview_toggle_off": "Ocultar vista previa",
        "preview_toggle_on": "Mostrar vista previa",
        "preview_tooltip": "Alterna la vista previa de video. Reduce uso de GPU y CPU.",
        "blackout_toggle_on": "Silenciar Video",
        "blackout_toggle_off": "Activar Video",
        "mic_toggle_off": "Silenciar Micrófono",
        "mic_toggle_on": "Activar Micrófono",
        "front_cam": "Cámara Frontal",
        "back_cam": "Cámara Trasera",

        # Hardware Zoom
        "zoom_header": "ZOOM ÓPTICO Y HARDWARE",
        "zoom_wide": "1x Gran angular",
        "zoom_tele": "3x Teleobjetivo",
        "zoom_periscope": "10x Periscopio",
        "zoom_space": "100x Space Zoom",
        "zoom_level": "{level:.1f}x Zoom",

        # RAW & Color Science
        "raw_header": "SENSOR RAW Y CIENCIA DEL COLOR",
        "color_profiles": "Perfil de Color",
        "profile_standard": "Estándar (Natural)",
        "profile_vivid": "Vívido (Punchy Stream)",
        "profile_cinema": "Cinematográfico Cálido",
        "profile_portrait": "Retrato de Estudio (Suave)",
        "profile_lowlight": "Poca Luz / Noche",
        "profile_vintage": "Retro / Película Vintage",
        "profile_bw": "Blanco y Negro (B&N)",
        "profile_custom": "Personalizado",

        "tone_curve": "Curva de Tono",
        "curve_linear": "Lineal",
        "curve_film": "Película Curva S",
        "curve_portrait": "Retrato (Suave)",
        "curve_vivid": "Contraste Vívido",
        "curve_vintage": "Mate Vintage",

        "raw_exposure": "Exposición",
        "raw_highlights": "Altas Luces",
        "raw_shadows": "Sombras",
        "raw_whites": "Blancos",
        "raw_blacks": "Negros",
        "raw_contrast": "Contraste",
        "raw_brightness": "Brillo",
        "raw_temp": "Temperatura de Color",
        "raw_tint": "Tinte",
        "raw_saturation": "Saturación",
        "raw_vibrance": "Intensidad",
        "raw_sharpness": "Nitidez Laplaciana",

        "rgb_balance": "Balance RGB",
        "red_gain": "Ganancia Roja",
        "green_gain": "Ganancia Verde",
        "blue_gain": "Ganancia Azul",
        "btn_reset_filters": "Restablecer Ajustes",

        # AI Focus & Background
        "focus_header": "RETRATO IA Y ENFOQUE DE FONDO",
        "focus_enable": "Activar aislamiento IA del sujeto",
        "focus_mode_blur": "Desenfoque bokeh",
        "focus_mode_studio": "Foco de Estudio",
        "focus_mode_custom": "Fondo virtual personalizado",
        "focus_choose_img": "Elegir imagen...",
        "focus_blur_amount": "Intensidad de desenfoque",
        "focus_radius": "Profundidad de enfoque",

        # Audio Sink
        "audio_sink_label": "AUDIO",
        "audio_level": "Nivel",
        "audio_muted": "Silenciado",
        "audio_active": "Activo",

        # Messages & Dialogs
        "dialog_img_filter": "Archivos de imagen (*.png *.jpg *.jpeg *.webp *.bmp)",
        "dialog_select_bg": "Seleccionar imagen de fondo",
        "err_connection_failed": "Error al conectar con la transmisión del móvil.",
        "err_adb_not_found": "ADB no encontrado. Instale Android Platform Tools.",
        "vcam_ready": "Cámara virtual lista: {dev}",
        "vcam_active": "Transmitiendo a {dev}"
    }
}

def detect_system_language() -> str:
    """
    Detects operating system language automatically.
    Falls back to 'en' if not in supported languages.
    """
    # 1. Environment variables (Linux / macOS / POSIX)
    for env in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        val = os.environ.get(env, "")
        if val:
            prefix = val.split(".")[0].split("_")[0].lower()
            if prefix in SUPPORTED_LANGUAGES:
                return prefix

    # 2. Python locale
    try:
        loc = locale.getdefaultlocale()[0]
        if loc:
            prefix = loc.split("_")[0].lower()
            if prefix in SUPPORTED_LANGUAGES:
                return prefix
    except Exception:
        pass

    # 3. Qt QLocale if PyQt6 is present
    try:
        from PyQt6.QtCore import QLocale
        prefix = QLocale.system().name().split("_")[0].lower()
        if prefix in SUPPORTED_LANGUAGES:
            return prefix
    except Exception:
        pass

    return "en"

class I18nManager:
    """
    Centralized Internationalization & Localization Manager for AselCam.
    Supports dynamic language switching and system language auto-detection.
    """
    _instance: Optional['I18nManager'] = None

    def __init__(self, initial_lang: str = "auto"):
        self._configured_lang = initial_lang
        self._current_lang = self._resolve_lang(initial_lang)
        self._listeners: List[Callable[[str], None]] = []

    @classmethod
    def get_instance(cls) -> 'I18nManager':
        if cls._instance is None:
            cls._instance = I18nManager()
        return cls._instance

    def _resolve_lang(self, lang: str) -> str:
        if lang == "auto" or not lang or lang not in SUPPORTED_LANGUAGES:
            return detect_system_language()
        return lang

    @property
    def current_language(self) -> str:
        return self._current_lang

    @property
    def configured_language(self) -> str:
        return self._configured_lang

    def set_language(self, lang_code: str):
        self._configured_lang = lang_code
        self._current_lang = self._resolve_lang(lang_code)
        for listener in list(self._listeners):
            try:
                listener(self._current_lang)
            except Exception as e:
                print(f"[I18n] Error notifying listener: {e}")

    def add_listener(self, callback: Callable[[str], None]):
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[str], None]):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def t(self, key: str, **kwargs) -> str:
        lang_dict = TRANSLATIONS.get(self._current_lang, TRANSLATIONS["en"])
        template = lang_dict.get(key) or TRANSLATIONS["en"].get(key, key)
        if kwargs:
            try:
                return template.format(**kwargs)
            except Exception:
                return template
        return template

# Global helper functions
def _t(key: str, **kwargs) -> str:
    return I18nManager.get_instance().t(key, **kwargs)

def tr(key: str, **kwargs) -> str:
    return I18nManager.get_instance().t(key, **kwargs)
