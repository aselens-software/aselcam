# AselCam for iOS

Native Apple iOS client for **AselCam**, providing ultra low-latency 4K/1080p 60 FPS virtual webcam and 24 kHz microphone streaming from your iPhone or iPad directly to Linux, Windows, and macOS desktop computers.

---

## 🌟 Key Features

- **Hardware Video Acceleration**: Built directly on Apple's `VideoToolbox` framework (`VTCompressionSession`) producing zero-latency Annex-B H.264 streams.
- **AVFoundation Camera Control**: Supports Ultra-Wide, Wide, and Telephoto multi-lens switching, 60 FPS capture, and up to 100x hardware/digital zoom.
- **ReplayKit Screen Mirroring**: Real-time display broadcasting directly to the desktop virtual camera.
- **24 kHz Mono Audio**: High-fidelity microphone capture via `AVAudioEngine` with hardware echo cancellation.
- **True AMOLED Blackout Mode**: Disables display rendering to minimize battery consumption and prevent overheating.
- **Multi-Language Support**: Automatic locale detection with English, Turkish, German, French, and Spanish.

---

## 📱 System Requirements

- **iOS Version**: iOS 15.0 or newer
- **Supported Devices**: iPhone 8 and newer, iPad 6th generation and newer, iPad Pro, iPad Air
- **Xcode Version**: Xcode 14.0 or newer (macOS Sonoma / Ventura)

---

## 🛠️ Build and Installation

### Option 1: Open in Xcode
1. Double-click `AselCam.xcodeproj` to open the project in Xcode.
2. Under **Signing & Capabilities**, select your Apple Developer Team (Free Personal Team or Paid Account).
3. Connect your iPhone via USB or select a physical device destination.
4. Click **Run** (`⌘R`) to build and deploy to your device.

### Option 2: Build with Command-Line (`xcodebuild`)
```bash
# Debug build for iOS Device
xcodebuild -project AselCam.xcodeproj \
           -scheme AselCam \
           -configuration Debug \
           -destination 'generic/platform=iOS' \
           build

# Archive for Ad-Hoc / TestFlight distribution
xcodebuild -project AselCam.xcodeproj \
           -scheme AselCam \
           -configuration Release \
           -archivePath build/AselCam.xcarchive \
           archive
```

---

## 🔒 Permissions & Security

AselCam requires the following permissions declared in `Info.plist`:
- `NSCameraUsageDescription`: Capturing live camera feed for virtual webcam streaming.
- `NSMicrophoneUsageDescription`: Streaming microphone audio to the computer.
- `NSLocalNetworkUsageDescription`: Connecting directly over local Wi-Fi to the desktop application.
- `UIBackgroundModes`: `audio` (for background audio streaming when the device is locked or blacked out).

---

## 💰 Google AdMob Integration

AselCam iOS integrates Google AdMob for:
- **Banner Ads**: Displayed at the bottom of the screen.
- **Interstitial Ads**: Preloaded in the background and triggered on the **"Start Stream / Yayını Başlat"** action button.

### AdMob Identifiers:
- **Application ID**: `ca-app-pub-3011996181892691~1501320244` (configured in `Info.plist`)
- **Banner Ad Unit ID**: `ca-app-pub-3011996181892691/3349588537`
- **Interstitial Ad Unit ID**: `ca-app-pub-3011996181892691/5905178693`

### Adding the Google Mobile Ads SDK via Xcode (Swift Package Manager):
1. In Xcode, select **File > Add Package Dependencies...**
2. Paste the official repository URL:
   `https://github.com/googleads/swift-package-manager-google-mobile-ads.git`
3. Select **GoogleMobileAds** and add it to the **AselCam** target.
4. *Note: If building without the framework linked, `AdMobManager.swift` automatically falls back to ad-free execution safely via `#if canImport(GoogleMobileAds)`.*

---

## 🌐 Network Protocol

- **TCP Port 4747**: Low-latency video (H.264 NALUs) & audio (24 kHz PCM) wire protocol with 18-byte `ASEL` binary header.
- **TCP Port 4748**: Bi-directional JSON control protocol (`get_info`, `switch_camera`, `set_torch`, `set_zoom`, `blackout`, `set_screen_mirror`, `ping`).
