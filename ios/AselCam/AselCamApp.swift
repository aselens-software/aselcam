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
    }
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .preferredColorScheme(.dark)
        }
    }
}
