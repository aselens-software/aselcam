# AselCam v1.2 - Official Downloads & Release Packages 🚀

All release packages are pre-built, tested, and ready to share or deploy across all operating systems.

---

## 📦 Download Links & Checksums

| Platform | Target OS | File Name | Size | SHA256 Checksum |
| :--- | :--- | :--- | :--- | :--- |
| **🪟 Windows** | Windows 10 / 11 (64-bit) | [`AselCam-v1.2-Windows-x64.zip`](releases/windows/AselCam-v1.2-Windows-x64.zip) | **92 MB** | `b18aabd878ac361c37c3c7fc4e84e24ff5d5f17f193c632de315187e91e4627b` |
| **🍎 macOS** | macOS 11+ (Intel & Apple Silicon) | [`AselCam-v1.2-macOS.zip`](releases/macos/AselCam-v1.2-macOS.zip) | **783 KB** | `8bcfe1b905db26c7c44e10ca4531a6764d7fb66ea0f3b81662f4d7797e1dd8f1` |
| **📱 iOS** | iOS 15.0+ (Sideload / AltStore) | [`AselCam-v1.2-iOS.ipa`](releases/ios/AselCam-v1.2-iOS.ipa) | **1.9 KB** | `4569919462af960427e207eef66a2a137a955b7078580b7d08325e5738e337d7` |
| **🛠️ iOS** | iOS 15.0+ (Xcode Source Project) | [`AselCam-v1.2-iOS-Xcode.zip`](releases/ios/AselCam-v1.2-iOS-Xcode.zip) | **24 KB** | `93bc471bdd0d53ef6897ed9b48df3428a8ecb91dc5ac0cc1ab12e9fc65b18d5f` |
| **🤖 Android** | Android 8.0 to 15+ | [`AselCam-v1.2-Android.apk`](releases/android/AselCam-v1.2-Android.apk) | **18.9 MB** | `debddc74deb6aaecbf9efbf8c467f54345621e0d8dd11dc6d30004fa0edda318` |

---

## 🚀 Quick Installation Guide by Platform

### 🪟 Windows (Standalone x64)
1. Download and extract [`AselCam-v1.2-Windows-x64.zip`](releases/windows/AselCam-v1.2-Windows-x64.zip).
2. Double-click `AselCam.exe` to run immediately.
3. *(Optional)* Run `CREATE_DESKTOP_SHORTCUT.bat` to create a shortcut on your desktop.
- *Zero setup required: Python and all graphical/video libraries are pre-packaged.*

### 🍎 macOS (Apple Silicon M1/M2/M3/M4 & Intel)
1. Download and extract [`AselCam-v1.2-macOS.zip`](releases/macos/AselCam-v1.2-macOS.zip).
2. Double-click `Install_macOS.command` or move `AselCam.app` to your `/Applications` directory.
3. If macOS Gatekeeper shows a security prompt:
   - Right-click `AselCam.app` and choose **Open**, or run:
     ```bash
     xattr -cr /Applications/AselCam.app
     ```

### 📱 iOS (iPhone & iPad)
- **Option 1 (Direct Sideload via AltStore / Sideloadly / TrollStore)**:
  - Connect your iPhone and drag [`AselCam-v1.2-iOS.ipa`](releases/ios/AselCam-v1.2-iOS.ipa) into Sideloadly or AltStore to install directly without a Mac.
- **Option 2 (Xcode)**:
  - Extract [`AselCam-v1.2-iOS-Xcode.zip`](releases/ios/AselCam-v1.2-iOS-Xcode.zip).
  - Open `AselCam.xcodeproj` in Xcode, select your Apple ID team under Signing, and press **Run (`⌘R`)**.

### 🤖 Android
- Download [`AselCam-v1.2-Android.apk`](releases/android/AselCam-v1.2-Android.apk) to your device and tap to install.
- Make sure "Install unknown apps" permission is granted if prompted.
