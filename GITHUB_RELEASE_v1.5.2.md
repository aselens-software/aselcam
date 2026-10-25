# AselCam v1.5.2 — Safe R8 DEX Optimization, Windows Inno Setup & Google Play Modernization 🚀

Turn your smartphone into an ultra low-latency 4K 60 FPS virtual webcam and studio microphone for Linux, Windows, and macOS.

AselCam **v1.5.2** delivers safe R8 DEX code optimization for Google Play, an all-new Windows automated installer with virtual camera/audio drivers, rate-limiting socket security hardening, large screen / foldable support, diagnostic crash reporting, and synchronized multiplatform releases.

---

## 📦 Official Release Downloads & Checksums

| Platform | Target OS | Package Name | Size | SHA-256 Checksum |
| :--- | :--- | :--- | :--- | :--- |
| **🪟 Windows (Installer)** | Windows 10 / 11 (64-bit) | [`AselCam-v1.5.2-Windows-Setup.exe`](releases/windows/AselCam-v1.5.2-Windows-Setup.exe) | **149 MB** | `91bfd3d4818917b30f7782d0b2327480f0be5b0126c8866d4fa413a2871973a8` |
| **🪟 Windows (Portable)** | Windows 10 / 11 (64-bit) | [`AselCam-v1.5.2-Windows-x64.zip`](releases/windows/AselCam-v1.5.2-Windows-x64.zip) | **222 MB** | `0afb67e7aebdda8e99b4ea344fb67e09e1295c5fcc7c568edb4759b500fd47cb` |
| **🤖 Android (Play Store)**| Android 8.0 to 16+ | [`AselCam-v1.5.2.aab`](releases/android/AselCam-v1.5.2.aab) | **13 MB** | `3f80813fe22a3e20f857c545fb4d79fc10b1de5650a0a9e435cbcfde8be37d05` |
| **🤖 Android (APK)** | Android 8.0 to 16+ | [`AselCam-v1.5.2-Android.apk`](releases/android/AselCam-v1.5.2-Android.apk) | **8.7 MB** | `1f5312f505da9ca2d02b2dc1d00b323f1f1550d6799a6ce6ca3b34f1df6c5bfa` |
| **🍎 macOS (Universal)** | macOS 11+ (Intel & Apple Silicon) | [`AselCam-v1.5.2-macOS.zip`](releases/macos/AselCam-v1.5.2-macOS.zip) | **1.7 MB** | `8f68c29dc239fc4315c840de8de328e7bf63ac9de9772748d4e470ba7756bd95` |
| **📱 iOS (Sideload)** | iOS 15.0+ (AltStore / Sideloadly) | [`AselCam-v1.5.2-iOS.ipa`](releases/ios/AselCam-v1.5.2-iOS.ipa) | **263 KB** | `ce681243acc9770b9c6b547df63dd1d058ba4e95144f7b9904b4a3fa741dc0ea` |
| **🛠️ iOS (Xcode)** | iOS 15.0+ (Source Project) | [`AselCam-v1.5.2-iOS-Xcode.zip`](releases/ios/AselCam-v1.5.2-iOS-Xcode.zip) | **292 KB** | `b1e4ecd8505351d03196d719acb1069a528049b817e1370261baa15f5a016dd3` |

---

## 🌟 What's New Since v1.4.7

### 🤖 Android & Google Play Modernization
* **Safe R8 DEX Code Optimization (50.76% Reduction):** Implemented targeted ProGuard/R8 obfuscation and shrinking rules in compatibility mode (`-dontoptimize`, `android.enableR8.fullMode=false`). Safely preserves Jetpack Compose runtime internals, Coroutines, Kotlin reflection, and ViewModels. Reduced standalone APK footprint to **8.7 MB** while passing Google Play's 25% minimum DEX optimization benchmark with 100% crash-free launch stability.
* **Large Screen & Multi-Window Compliance:** Removed hardcoded portrait orientation locks (`screenOrientation="portrait"` removed from `MainActivity` and `BlackoutActivity`) and enabled `android:resizeableActivity="true"`, ensuring full compliance with Google Play's tablet, foldable, and Chromebook guidelines.
* **Target SDK 36 (Android 16):** Upgraded Android target SDK to Android 16 (API 36) with Android 8.0 (API 26) backward compatibility and Fragment 1.8.6.
* **Diagnostic Crash Reporting (`CrashReportActivity`):** Integrated an in-app uncaught exception handler displaying clean stack traces with a 1-click clipboard copy button, replacing silent force-closes.
* **Screen Mirroring & Background Lifecycle Hardening:** Fixed background freeze when switching apps or locking devices during screen mirroring; safeguarded remote mirror triggers against concurrent swipe death.
* **Manual Start Guard:** Prevented accidental background streaming on cold launch; explicit user tap required.
* **Version Upgrade Compatibility:** Version code set to `1520` (`versionName = 1.5.2`), allowing smooth Google Play Store updates over earlier `1491`, `1492`, and `1493` builds.

### 🪟 Windows Desktop & Driver Installation
* **Automated Inno Setup 6 Installer (`AselCam-v1.5.2-Windows-Setup.exe`):** Compiles an automated Windows installer that automatically installs and registers DirectShow Virtual Camera filters (`UnityCaptureFilter64.dll`) and Virtual Audio Drivers into the Windows system without requiring command prompt commands or manual driver registration.
* **Portable Windows Archive (`AselCam-v1.5.2-Windows-x64.zip`):** Standalone zero-install portable zip archive for immediate execution.
* **Header Version Synchronization:** Updated title bar version badges across `main_window.py` and all 8 languages in `i18n.py` to `v1.5.2`.

### 🛡️ Security & Vibe-Check Audit Hardening
* **Secret & Keystore Protection:** Keystores (`*.keystore`, `KEYSTORE_INFO.txt`) untracked from Git history, added to `.gitignore`, and hardcoded passwords removed from Gradle build scripts in favor of dynamic environment variables (`KEYSTORE_PASSWORD`) and git-ignored `local.properties`.
* **Sliding-Window Command Rate Limiter:** Added a thread-safe sliding window rate limiter in `CommandServer.kt` (default safe limit: 30 commands/sec) with `set_rate_limit` and `get_rate_limit` RPC controls to protect mobile sockets against flooding.
* **Automated CI/CD Pipeline:** Added `.github/workflows/ci.yml` running automated Android unit tests (`CommandServerTest.kt`), Python test suites, and Gitleaks secret scanning on every commit.
* **Web Security Headers:** Configured strict HTTP security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `Referrer-Policy`, `Permissions-Policy`) in `site/.htaccess`.

### 💰 Google AdMob Monetization (Android & iOS)
* **Android:** Integrated Google Mobile Ads SDK with non-intrusive adaptive banner and session-end interstitial ads.
* **iOS:** Integrated Google Mobile Ads framework with official AdMob unit ID (`ca-app-pub-3011996181892691~1501320244`).

### 🌐 Web Site, Privacy & AI Agent Compatibility
* **Standalone Apple Liquid Glass Privacy Policy:** Launched `/privacy` with complete 8-language localization and legal clauses.
* **Support Email:** Added official developer contact (`support@aselens.com`) across all footers.
* **AI Bot & LLM Directives:** Published `site/llms.txt`, updated `site/robots.txt` explicitly permitting GPTBot, ClaudeBot, PerplexityBot, Google-Extended, and Bingbot, and updated `site/sitemap.xml`.
* **Buy Me a Coffee:** Embedded community sponsorship banner across landing page, privacy policy, and README.

### 🍎 macOS & iOS Updates
* Updated macOS `Info.plist` (v1.5.2 / build 152) and packaged universal zip with driver installer.
* Updated iOS `ContentView.swift` (badge `v1.5.2`), `Info.plist`, and `project.pbxproj` (1.5.2 / 152), and packaged `AselCam-v1.5.2-iOS-Xcode.zip` and `AselCam-v1.5.2-iOS.ipa`.

---

## 🛠️ Quick Installation Guide

### 🪟 Windows
1. **Recommended:** Run `AselCam-v1.5.2-Windows-Setup.exe` to automatically install the app and virtual camera/audio drivers.
2. **Portable:** Extract `AselCam-v1.5.2-Windows-x64.zip` and run `AselCam.exe`.

### 🍎 macOS
1. Extract `AselCam-v1.5.2-macOS.zip` and drag `AselCam.app` to `/Applications`.
2. Double-click `Install_macOS.command` to initialize CoreMediaIO DAL virtual camera plugin and BlackHole audio drivers.

### 🤖 Android
- Download `AselCam-v1.5.2-Android.apk` and tap to install on any device running Android 8.0 to Android 16.
- For Google Play Console release management, upload `AselCam-v1.5.2.aab`.

### 📱 iOS
- Sideload `AselCam-v1.5.2-iOS.ipa` via AltStore, Sideloadly, or TrollStore.
- Or open `AselCam-v1.5.2-iOS-Xcode.zip` in Xcode and deploy with your Apple ID.

---

**Full Commit History**: https://github.com/aselens-software/aselcam/compare/v1.4.7...v1.5.2
