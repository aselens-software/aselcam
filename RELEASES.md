# AselCam v1.2 - Official Downloads & Release Packages 🚀

All release packages are pre-built, tested, and ready to share or deploy across all operating systems with official AselCam branding and icons.

---

## 📦 Download Links & Checksums

| Platform | Target OS | File Name | Size | SHA256 Checksum |
| :--- | :--- | :--- | :--- | :--- |
| **🪟 Windows** | Windows 10 / 11 (64-bit) | [`AselCam-v1.2-Windows-x64.zip`](releases/windows/AselCam-v1.2-Windows-x64.zip) | **92 MB** | `de7f8983a96745788b0fca3b5a631014b16353f313ccdd6a2352a2d425e44405` |
| **🍎 macOS** | macOS 11+ (Intel & Apple Silicon) | [`AselCam-v1.2-macOS.zip`](releases/macos/AselCam-v1.2-macOS.zip) | **855 KB** | `44e98a4cfd7a476dd3a4e165df9b94123ffcfa97abc60593e8c3b310bf93b9bd` |
| **📱 iOS** | iOS 15.0+ (Sideload / AltStore) | [`AselCam-v1.2-iOS.ipa`](releases/ios/AselCam-v1.2-iOS.ipa) | **263 KB** | `ce681243acc9770b9c6b547df63dd1d058ba4e95144f7b9904b4a3fa741dc0ea` |
| **🛠️ iOS** | iOS 15.0+ (Xcode Source Project) | [`AselCam-v1.2-iOS-Xcode.zip`](releases/ios/AselCam-v1.2-iOS-Xcode.zip) | **284 KB** | `3862cf67f5c74e300baee9c94d9f4314dc6107436bfaaffef81ace113f617b05` |
| **🤖 Android** | Android 8.0 to 15+ | [`AselCam-v1.2-Android.apk`](releases/android/AselCam-v1.2-Android.apk) | **12.4 MB** | `20c0ce30ef68420e6bfc4ae507e6e8fe5c9d3b1c6b7e6ad77d458ee2bcf25f1b` |

---

## 🚀 Quick Installation Guide by Platform

### 🪟 Windows (Standalone x64)
1. Download and extract [`AselCam-v1.2-Windows-x64.zip`](releases/windows/AselCam-v1.2-Windows-x64.zip).
2. Double-click `AselCam.exe` to run immediately.
3. *(Optional)* Run `CREATE_DESKTOP_SHORTCUT.bat` to create an AselCam icon shortcut directly on your Windows desktop.
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
