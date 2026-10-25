# AselCam v1.5.2 - Official Downloads & Release Packages 🚀

All release packages are pre-built, tested, and ready to share or deploy across all operating systems with official AselCam branding, 8-language localization, dynamic auto-sizing, and native app icons.

---

## 📦 Official Download Links & Checksums

| Platform | Target OS | File Name | Size | SHA256 Checksum |
| :--- | :--- | :--- | :--- | :--- |
| **🪟 Windows (Installer)** | Windows 10 / 11 (64-bit) | [`AselCam-v1.5.2-Windows-Setup.exe`](releases/windows/AselCam-v1.5.2-Windows-Setup.exe) | **149 MB** | `91bfd3d4818917b30f7782d0b2327480f0be5b0126c8866d4fa413a2871973a8` |
| **🪟 Windows (Portable)** | Windows 10 / 11 (64-bit) | [`AselCam-v1.5.2-Windows-x64.zip`](releases/windows/AselCam-v1.5.2-Windows-x64.zip) | **222 MB** | `0afb67e7aebdda8e99b4ea344fb67e09e1295c5fcc7c568edb4759b500fd47cb` |
| **🍎 macOS** | macOS 11+ (Intel & Apple Silicon) | [`AselCam-v1.5.2-macOS.zip`](releases/macos/AselCam-v1.5.2-macOS.zip) | **1.7 MB** | `8f68c29dc239fc4315c840de8de328e7bf63ac9de9772748d4e470ba7756bd95` |
| **📱 iOS** | iOS 15.0+ (Sideload / AltStore) | [`AselCam-v1.5.2-iOS.ipa`](releases/ios/AselCam-v1.5.2-iOS.ipa) | **263 KB** | `ce681243acc9770b9c6b547df63dd1d058ba4e95144f7b9904b4a3fa741dc0ea` |
| **🛠️ iOS** | iOS 15.0+ (Xcode Source Project) | [`AselCam-v1.5.2-iOS-Xcode.zip`](releases/ios/AselCam-v1.5.2-iOS-Xcode.zip) | **292 KB** | `b1e4ecd8505351d03196d719acb1069a528049b817e1370261baa15f5a016dd3` |
| **🤖 Android** | Android 8.0 to 16+ | [`AselCam-v1.5.2-Android.apk`](releases/android/AselCam-v1.5.2-Android.apk) | **8.7 MB** | `1f5312f505da9ca2d02b2dc1d00b323f1f1550d6799a6ce6ca3b34f1df6c5bfa` |

---

## 📝 Changelog & Release Notes

### 🚀 AselCam v1.5.2 (25.10.2026)

#### 🤖 Android & Google Play Store Modernization
- **Safe R8 DEX Code Optimization (50.76% Reduction):** Enabled R8 minification and DEX optimization safely using compatibility mode (`-dontoptimize`, `android.enableR8.fullMode=false`), keeping all Jetpack Compose runtime classes, Kotlin reflection metadata, ViewModels, and Coroutines intact. Reduces APK package size to **8.7 MB** (AAB 13 MB) and passes Google Play's 25% minimum DEX optimization benchmark with 100% crash-free stability.
- **Large Screen & Multi-Window Compliance:** Removed restrictive portrait orientation locks (`screenOrientation="portrait"` removed from `MainActivity` and `BlackoutActivity`) and enabled `android:resizeableActivity="true"`, fully complying with Google Play's tablet, foldable, and desktop form factor guidelines.
- **Target SDK 36 (Android 16):** Upgraded Android target SDK to Android 16 (API 36) with Android 8.0 (API 26) backward compatibility and Fragment 1.8.6.
- **Diagnostic Crash Reporting (`CrashReportActivity`):** Integrated an in-app uncaught exception handler displaying full stack traces with a clean copy-button UI, preventing silent force closes.
- **Screen Mirroring & Background Lifecycle Fixes:** Resolved background freeze when switching between apps or locking the device during screen mirroring; guarded remote trigger and lifecycle handlers against concurrent swipe death.
- **Manual Broadcast Guard:** Cold-launch auto-start removed; broadcasting requires explicit user tap.
- **Upgrade Versioning Compatibility:** Version name set to `1.5.2`, version code set to `1520` (ensuring monotonic increase from previous `1491`/`1492`/`1493` builds for Google Play Console compatibility).

#### 🪟 Windows Desktop & Driver Installation
- **Automated Inno Setup 6 Installer (`AselCam-v1.5.2-Windows-Setup.exe`):** Compiles an automated Windows installer that automatically registers DirectShow Virtual Camera filters (`UnityCaptureFilter64.dll`) and Virtual Audio Drivers without needing command-line scripts or manual admin permissions.
- **Portable Windows Package (`AselCam-v1.5.2-Windows-x64.zip`):** Standalone zero-install portable zip archive for quick deployment.
- **Header Version Badge Sync:** Synchronized title bar badge and localized `"version_tag"` across all 8 supported languages to `v1.5.2`.

#### 🛡️ Security & Vibe-Check Hardening
- **Secret & Keystore Protection:** Untracked keystores (`*.keystore`, `KEYSTORE_INFO.txt`) from Git history, added `.gitignore` rules, and removed hardcoded passwords from Gradle build scripts in favor of environment variables (`KEYSTORE_PASSWORD`) and git-ignored `local.properties`.
- **Sliding-Window Socket Rate Limiter:** Added thread-safe sliding window rate limiting in `CommandServer.kt` (default safe limit: 30 commands/sec) with `set_rate_limit` and `get_rate_limit` RPC controls to protect against socket flooding and denial-of-service.
- **Android Unit Testing & Automated CI/CD:** Added JUnit tests in `CommandServerTest.kt` verifying command server functionality and rate limiting. Created `.github/workflows/ci.yml` running automated tests and Gitleaks credential scanning on every push.
- **Web Security Headers:** Added hardened HTTP security headers (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`) in `site/.htaccess`.

#### 💰 Google AdMob Monetization (Android & iOS)
- Integrated Google AdMob SDK on Android with adaptive banner ads and session-end full-screen interstitial ads.
- Added AdMob framework on iOS with real app unit IDs (`ca-app-pub-3011996181892691~1501320244`).

#### 🌐 Web Site, Privacy & AI Agent Compatibility
- **Standalone Apple-Style Privacy Policy:** Created standalone `/privacy` page (`site/privacy.html`, `site/privacy/index.html`) with complete 8-language localization.
- **Support Contact:** Added developer support contact (`support@aselens.com`) across all privacy and landing footers.
- **AI Bot Directives:** Created `site/llms.txt`, `site/robots.txt` (explicit permissions for GPTBot, ClaudeBot, PerplexityBot, Google-Extended, Bingbot), and `site/sitemap.xml`.
- **Structured Metadata:** Added Open Graph, Twitter Cards, and Schema.org JSON-LD tags in English.
- **Buy Me a Coffee:** Added community sponsorship banner across landing page, privacy policy, and README.

#### 🍎 macOS & iOS Updates
- Updated macOS `Info.plist` (v1.5.2 / build 152) and packaged universal zip with driver installer.
- Updated iOS `ContentView.swift` (badge `v1.5.2`), `Info.plist`, and `project.pbxproj` (1.5.2 / 152), and packaged `AselCam-v1.5.2-iOS-Xcode.zip` and `AselCam-v1.5.2-iOS.ipa`.

---

### 📦 AselCam v1.4.7 (18.10.2026)

### 🎨 Official Branding & High-Resolution Logo Rendering
- **Authentic Vector-to-PNG Conversion**: Converted `aselcam_logo-horz-white.svg` directly using Linux's native `rsvg-convert` engine to produce ultra-crisp, multi-resolution PNGs (`128px`, `256px`, `440px`, `512px`, `1024px`) with 100% gradient fidelity and zero lens distortion across all desktop platforms.
- **Pixel-Perfect Logo Integration**: Replaced vector SVG rasterization inside Qt's `QSvgWidget` / `QPixmap` with direct lossless PNGs (`aselcam_logo_horz.png`), completely eliminating gradient rendering distortion and color artifacts in the viewfinder and performance slates.
- **Full Icon Pack**: Embedded high-resolution icon suites across 16x16, 24x24, 32x32, 48x48, 64x64, 128x128, 256x256, and 512x512 for Desktop (`.ico` / `.png`), macOS (`.icns`), Android (`mipmap`), and iOS (`AppIcon.appiconset`).
- **Linux Alt Panel (Dock / Taskbar) Icon Fix**: Deployed icons to `~/.local/share/icons/hicolor/{16..512}/apps/aselcam.png`, registered `StartupWMClass=aselcam` in `aselcam.desktop`, and updated GTK icon caches so native Linux desktop docks display the authentic app logo rather than a generic camera placeholder.

### 🌐 Complete 8-Language Localization (i18n)
- **8 Supported Languages**: Turkish (TR), English (EN), German (DE), French (FR), Spanish (ES), Russian (RU), Japanese (JA), and Arabic (AR) with interactive national flag selectors.
- **RAW Color Profile Chips Localized**: Full localization for all color profile preset chips ("Doğal", "Canlı", "Sinematik", "Portre", "Gece", "B&W" / "Natural", "Vivid", "Cinema", "Portrait", "Night", "B&W" / etc.) across all 8 languages, with dynamic auto-sizing to eliminate text clipping.
- **Default 0 Value Badges Localized**: Renk Sıcaklığı and Renk Tonu default to localized "Doğal" / "Natural" / "Natürlich" / etc., and Gerçek Keskinlik defaults to localized "Kapalı" / "Off" / "Aus" / "Désactivé" / etc., with adaptive badge width expansion.
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
- **V4L2 Loopback Feeder**: Continuous background feed keeping `/dev/video10` ready for instant consumption by Discord, Zoom, OBS, and Google Meet.
- **Direct Virtual Camera & Audio (Windows & macOS)**: Fully direct, standalone virtual camera and microphone creation without needing OBS Studio or third-party apps. On Windows, DirectShow virtual camera filters and signed Virtual Audio Drivers are automatically registered on startup. On macOS, CoreMediaIO DAL virtual camera plugin and BlackHole CoreAudio drivers are automatically initialized upon launching AselCam.

---

## 🚀 Quick Installation Guide by Platform

### 🪟 Windows (Installer & Portable)
1. Recommended: Download and run [`AselCam-v1.5.2-Windows-Setup.exe`](releases/windows/AselCam-v1.5.2-Windows-Setup.exe) for automated driver setup.
2. Standalone: Download and extract [`AselCam-v1.5.2-Windows-x64.zip`](releases/windows/AselCam-v1.5.2-Windows-x64.zip) and launch `AselCam.exe`.
3. *(Optional)* Run `CREATE_DESKTOP_SHORTCUT.bat` to create an AselCam icon shortcut directly on your Windows desktop.
- *Zero setup required: Python and all graphical/video libraries are pre-packaged.*

### 🍎 macOS (Apple Silicon M1/M2/M3/M4 & Intel)
1. Download and extract [`AselCam-v1.5.2-macOS.zip`](releases/macos/AselCam-v1.5.2-macOS.zip).
2. Double-click `Install_macOS.command` or move `AselCam.app` to your `/Applications` directory.
3. If macOS Gatekeeper shows a security prompt:
   - Right-click `AselCam.app` and choose **Open**, or run:
     ```bash
     xattr -cr /Applications/AselCam.app
     ```

### 📱 iOS (iPhone & iPad)
- **Option 1 (Direct Sideload via AltStore / Sideloadly / TrollStore)**:
  - Connect your iPhone and drag [`AselCam-v1.5.2-iOS.ipa`](releases/ios/AselCam-v1.5.2-iOS.ipa) into Sideloadly or AltStore to install directly without a Mac.
- **Option 2 (Xcode)**:
  - Extract [`AselCam-v1.5.2-iOS-Xcode.zip`](releases/ios/AselCam-v1.5.2-iOS-Xcode.zip).
  - Open `AselCam.xcodeproj` in Xcode, select your Apple ID team under Signing, and press **Run (`⌘R`)**.

### 🤖 Android
- Download [`AselCam-v1.5.2-Android.apk`](releases/android/AselCam-v1.5.2-Android.apk) to your device and tap to install.
- Make sure "Install unknown apps" permission is granted if prompted.

---

Developed by Aselens Software [https://aselens.com]
