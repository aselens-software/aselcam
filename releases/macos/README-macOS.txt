========================================================================
                      AselCam Studio - macOS Edition
========================================================================

SYSTEM REQUIREMENTS:
- macOS 11.0 (Big Sur), 12.0 (Monterey), 13.0 (Ventura), 14.0 (Sonoma), 15.0 (Sequoia) or newer
- Apple Silicon (M1 / M2 / M3 / M4) and Intel (x86_64) Macs supported
- Python 3.10+ (Installed via Homebrew: 'brew install python')

HOW TO RUN:
Option 1:
Double-click "Install_macOS.command" to automatically configure security
permissions, install direct virtual drivers, and launch AselCam Studio.

Option 2:
Drag "AselCam.app" to your "/Applications" folder and double-click it.
The application automatically completes the setup upon launch.

DIRECT VIRTUAL CAMERA & MICROPHONE (AUTOMATED SETUP):
When AselCam launches, it automatically sets up and activates its direct
virtual camera and microphone devices:
- Virtual Camera: Direct CoreMedia DAL plugin installed automatically to
  your user Library (~/Library/CoreMediaIO/Plug-Ins/DAL). Recognized immediately
  by Zoom, Discord, Google Meet, Microsoft Teams, FaceTime, and browsers.
- Virtual Microphone: Direct audio driver that routes your smartphone's
  studio microphone with ultra-low latency directly into all voice chat
  and meeting applications.
- Zero configuration needed: Setup completes automatically on launch! No OBS Studio required.

GATEKEEPER SECURITY NOTE:
Because this application is distributed outside the Mac App Store, macOS
Gatekeeper might display an "unidentified developer" warning.
To allow it:
1. Right-click (or Control-click) "AselCam.app" and choose "Open".
   -OR-
2. Open Terminal and run:
   xattr -cr /Applications/AselCam.app
========================================================================
