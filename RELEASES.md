# AselCam v1.4.7 - Official Downloads & Release Packages 🚀

All release packages are pre-built, tested, and ready to share or deploy across all operating systems with official AselCam branding, 8-language localization, dynamic auto-sizing, and native app icons.

---

## 📦 Official Download Links & Checksums

| Platform | Target OS | File Name | Size | SHA256 Checksum |
| :--- | :--- | :--- | :--- | :--- |
| **🪟 Windows** | Windows 10 / 11 (64-bit) | [`AselCam-v1.4.7-Windows-x64.zip`](releases/windows/AselCam-v1.4.7-Windows-x64.zip) | **98 MB** | `a1cb66027f069a2a64a6d86516da7101b77a12bb1a92373e5a205610cb811560` |
| **🍎 macOS** | macOS 11+ (Intel & Apple Silicon) | [`AselCam-v1.4.7-macOS.zip`](releases/macos/AselCam-v1.4.7-macOS.zip) | **1.4 MB** | `07dbcd4beab6f594f6141f9414dc666f94a1992e99099e3026e4a53e72ff575c` |
| **📱 iOS** | iOS 15.0+ (Sideload / AltStore) | [`AselCam-v1.4.7-iOS.ipa`](releases/ios/AselCam-v1.4.7-iOS.ipa) | **263 KB** | `ce681243acc9770b9c6b547df63dd1d058ba4e95144f7b9904b4a3fa741dc0ea` |
| **🛠️ iOS** | iOS 15.0+ (Xcode Source Project) | [`AselCam-v1.4.7-iOS-Xcode.zip`](releases/ios/AselCam-v1.4.7-iOS-Xcode.zip) | **283 KB** | `5170f940e88db289d7873fd9ca73c6f52cb50e6cea4ca3631450cb9894103eb2` |
| **🤖 Android** | Android 8.0 to 15+ | [`AselCam-v1.4.7-Android.apk`](releases/android/AselCam-v1.4.7-Android.apk) | **13 MB** | `eb566cf0c9b231ea8ca67ceee27f9e54309eacd1482a18f4081dfe50da1bbc6b` |

---

## 📝 Changelog & Release Notes (17.10.2026 23:45 — 18.10.2026)

### 🎨 Official Branding & High-Resolution Logo Rendering
- **Pixel-Perfect Logo Integration**: Replaced vector SVG rasterization inside Qt's `QSvgWidget` / `QPixmap` with direct 1024x300 lossless PNG (`aselcam_logo_horz.png`), completely eliminating gradient rendering distortion and color artifacts in the viewfinder and performance slates.
- **Full Icon Pack**: Embedded high-resolution icon suites across 16x16, 24x24, 32x32, 48x48, 64x64, 128x128, 256x256, and 512x512 for Desktop (`.ico` / `.png`), macOS (`.icns`), Android (`mipmap`), and iOS (`AppIcon.appiconset`).
- **Linux Alt Panel (Dock / Taskbar) Icon Fix**: Deployed icons to `~/.local/share/icons/hicolor/{16..512}/apps/aselcam.png`, registered `StartupWMClass=aselcam` in `aselcam.desktop`, and updated GTK icon caches so native Linux desktop docks display the authentic app logo rather than a generic camera placeholder.

### 🌐 Complete 8-Language Localization (i18n)
- **8 Supported Languages**: Turkish (TR), English (EN), German (DE), French (FR), Spanish (ES), Russian (RU), Japanese (JA), and Arabic (AR) with interactive national flag selectors.
- **Dynamic Language Reversion Fix**: Eliminated the critical bug where toggle buttons and telemetry slots reverted to hardcoded Turkish after clicks. Rewrote all event handlers (`_toggle_preview`, `_toggle_camera_pause`, `_toggle_mic_mute`, `_remote_toggle_torch`, `_remote_toggle_blackout`, `_remote_toggle_screen_mirror`, `_on_telemetry_updated`) to track internal boolean states and query dynamic localized strings.
- **Detay & Geometri (Section 6) Fully Localized**: Translated Laplacian Sharpness, Horizontal Mirror, Vertical Flip, Black & White, Invert Colors, Rotation, and Reset All RAW & Color Settings across all 8 languages.
- **Audio "SES" Indicator**: Localized the viewfinder audio monitor label (`audio_label`: SES / AUDIO / АУДИО / 音声 / صوت).
- **All Dropdown Menus Localized**: Dynamic multi-language retranslation for Camera selections, Aspect Ratio presets, Video Codecs, Resolutions, Bitrates, and Device fallback notices.
- **Mobile Streamer Localization**: Localized viewfinder HUD status (`MobileI18n.tr("hud_live")` / `"hud_idle"`), Camera selector (Front/Back), and Aspect ratio presets.

### 📏 Adaptive Auto-Size UI Engine
- **Intelligent Layout Resizing (`auto_size_ui`)**: Dynamically measures `QFontMetrics` on every language change.
- **Zero-Clipping Buttons**: Automatically computes and applies minimum widths to action buttons, quick docks, and control panels so longer languages (German, Russian, French) never clip text or truncate with ellipses (`...`).
- **Dynamic Splitter & Window Bounds**: Automatically expands window width and redistributes splitter container proportions whenever longer translations require additional horizontal space.

### 🎛️ Desktop Studio UI Polish
- **Hub #1 Header Button Fix**: Fixed CSS padding and sizing on `btn_collapse_hub` (`padding: 0px !important; margin: 0px; 26x26px`), ensuring the collapse button icon (`✕`) is rendered sharply and centered without getting clipped by global button padding.
- **Header Clean-Up**: Removed "Stüdyo" clutter text, stripped colored background boxes behind `v1.4.7` and `Yayında / Çevrimdışı` badges for seamless dark integration with the window canvas.
- **Interactive Keyboard Trackbars (`ValueBadgeEdit`)**: Added direct numeric keyboard entry with automatic clamping to all parameter sliders.
- **Filled Trackbar Visuals**: Added distinct slider tracks and fills to provide clear visual boundaries for sliding limits.
- **System Tray Background Persistence**: Window close ("X") minimizes cleanly to the system tray while maintaining virtual camera background broadcasting.
- **Enhanced Telemetry Footer**: Displays live FPS, bitrate, end-to-end network latency (ping), packet loss percentage, and active virtual camera node (`/dev/video10`).

### 📱 Mobile Companion App Modernization
- **Dual AMOLED + LED Blackout**: Combines a 100% black AMOLED surface overlay with programmatic hardware screen backlight reduction to zero, maximizing battery life and eliminating thermal throttling on both OLED and LCD screens.
- **Clean Mobile Header**: Removed duplicate "Beklemede/Yayında" badges and "Companion Streamer" text from top bar, maintaining a clean, professional camera HUD.
- **Ergonomic Spacing**: Added 14.dp separation between the language selector dropdown and the blackout toggle button.
- **Stream Standby Slate**: Viewfinder properly transitions to "Yayın Bekleniyor..." / "Waiting for Stream..." when broadcasting is stopped rather than freezing on the last captured frame.

### ⚡ Core Architecture, Concurrency & Hardware
- **Zero-Latency Video Pipeline**: MediaCodec (Android) & VideoToolbox (iOS) hardware encoders paired with FFmpeg 9.0.2 hardware-accelerated decoding.
- **Concurrency Deadlock Fix**: Resolved frame freezing when simultaneous control commands were dispatched concurrently from PC and mobile.
- **PipeWire & PulseAudio Virtual Mic**: Automatic creation of `module-null-sink` and `module-remap-source` virtual microphone devices with 24 kHz linear PCM pass-through.
- **V4L2 Loopback Feeder**: Continuous background feed keeping `/dev/video10` ready for instant consumption by Discord, Zoom, OBS, and Google Meet.

---

## 🚀 Quick Installation Guide by Platform

### 🪟 Windows (Standalone x64)
1. Download and extract [`AselCam-v1.4.7-Windows-x64.zip`](releases/windows/AselCam-v1.4.7-Windows-x64.zip).
2. Double-click `AselCam.exe` to run immediately.
3. *(Optional)* Run `CREATE_DESKTOP_SHORTCUT.bat` to create an AselCam icon shortcut directly on your Windows desktop.
- *Zero setup required: Python and all graphical/video libraries are pre-packaged.*

### 🍎 macOS (Apple Silicon M1/M2/M3/M4 & Intel)
1. Download and extract [`AselCam-v1.4.7-macOS.zip`](releases/macos/AselCam-v1.4.7-macOS.zip).
2. Double-click `Install_macOS.command` or move `AselCam.app` to your `/Applications` directory.
3. If macOS Gatekeeper shows a security prompt:
   - Right-click `AselCam.app` and choose **Open**, or run:
     ```bash
     xattr -cr /Applications/AselCam.app
     ```

### 📱 iOS (iPhone & iPad)
- **Option 1 (Direct Sideload via AltStore / Sideloadly / TrollStore)**:
  - Connect your iPhone and drag [`AselCam-v1.4.7-iOS.ipa`](releases/ios/AselCam-v1.4.7-iOS.ipa) into Sideloadly or AltStore to install directly without a Mac.
- **Option 2 (Xcode)**:
  - Extract [`AselCam-v1.4.7-iOS-Xcode.zip`](releases/ios/AselCam-v1.4.7-iOS-Xcode.zip).
  - Open `AselCam.xcodeproj` in Xcode, select your Apple ID team under Signing, and press **Run (`⌘R`)**.

### 🤖 Android
- Download [`AselCam-v1.4.7-Android.apk`](releases/android/AselCam-v1.4.7-Android.apk) to your device and tap to install.
- Make sure "Install unknown apps" permission is granted if prompted.

---

Developed by Aselens Software [https://aselens.com]
