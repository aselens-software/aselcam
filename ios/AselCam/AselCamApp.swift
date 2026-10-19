//
//  AselCamApp.swift
//  AselCam iOS
//
//  Application lifecycle entry point for AselCam on iOS.
//

import SwiftUI

@main
struct AselCamApp: App {
    init() {
        // Prevent screen from sleeping during active webcam streaming
        UIApplication.shared.isIdleTimerDisabled = true
        // Initialize Google Mobile Ads SDK
        AdMobManager.shared.initialize()
    }
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .preferredColorScheme(.dark)
        }
    }
}
