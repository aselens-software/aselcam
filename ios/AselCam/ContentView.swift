//
//  ContentView.swift
//  AselCam iOS
//
//  Obsidian Dark Neumorphic UI for iOS.
//  Matches AselCam Desktop and Android mobile styling.
//

import SwiftUI

public struct ContentView: View {
    @StateObject private var viewModel = AselCamViewModel()
    @State private var selectedLanguage: String = "auto"
    
    // Localization dictionary
    private let strings: [String: [String: String]] = [
        "en": [
            "app_name": "AselCam",
            "status_live": "LIVE",
            "status_standby": "STANDBY",
            "torch": "Torch",
            "flip": "Flip",
            "mic": "Mic",
            "blackout": "Blackout",
            "mirror": "Mirror",
            "stop_mirror": "Stop Mirror",
            "zoom_title": "OPTICAL & HARDWARE ZOOM",
            "clients": "Clients",
            "bitrate": "kbps",
            "ip_title": "Wi-Fi IP"
        ],
        "tr": [
            "app_name": "AselCam",
            "status_live": "CANLI",
            "status_standby": "BEKLEMEDE",
            "torch": "Flaş",
            "flip": "Çevir",
            "mic": "Mikrofon",
            "blackout": "Karart",
            "mirror": "Yansıt",
            "stop_mirror": "Durdur",
            "zoom_title": "DONANIMSAL ZOOM",
            "clients": "İstemci",
            "bitrate": "kbps",
            "ip_title": "Wi-Fi IP"
        ],
        "de": [
            "app_name": "AselCam",
            "status_live": "LIVE",
            "status_standby": "STANDBY",
            "torch": "Licht",
            "flip": "Kamera",
            "mic": "Mikrofon",
            "blackout": "Abdunkeln",
            "mirror": "Spiegeln",
            "stop_mirror": "Stopp",
            "zoom_title": "HARDWARE-ZOOM",
            "clients": "Clients",
            "bitrate": "kbps",
            "ip_title": "WLAN-IP"
        ],
        "fr": [
            "app_name": "AselCam",
            "status_live": "EN DIRECT",
            "status_standby": "EN ATTENTE",
            "torch": "Torche",
            "flip": "Changer",
            "mic": "Micro",
            "blackout": "Écran noir",
            "mirror": "Miroir",
            "stop_mirror": "Arrêter",
            "zoom_title": "ZOOM MATÉRIEL",
            "clients": "Clients",
            "bitrate": "kbps",
            "ip_title": "IP Wi-Fi"
        ],
        "es": [
            "app_name": "AselCam",
            "status_live": "EN VIVO",
            "status_standby": "EN ESPERA",
            "torch": "Linterna",
            "flip": "Cambiar",
            "mic": "Mic",
            "blackout": "Oscurecer",
            "mirror": "Reflejar",
            "stop_mirror": "Detener",
            "zoom_title": "ZOOM HARDWARE",
            "clients": "Clientes",
            "bitrate": "kbps",
            "ip_title": "IP Wi-Fi"
        ]
    ]
    
    private var lang: String {
        if selectedLanguage != "auto" { return selectedLanguage }
        let preferred = Locale.preferredLanguages.first?.prefix(2).lowercased() ?? "en"
        return strings.keys.contains(preferred) ? preferred : "en"
    }
    
    private func tr(_ key: String) -> String {
        return strings[lang]?[key] ?? strings["en"]?[key] ?? key
    }
    
    public init() {}
    
    public var body: some View {
        ZStack {
            // Obsidian Black Background
            Color(red: 0.05, green: 0.05, blue: 0.06)
                .ignoresSafeArea()
            
            if viewModel.isBlackout {
                // True AMOLED Blackout Mode
                Color.black.ignoresSafeArea()
                    .overlay(
                        VStack(spacing: 12) {
                            Image(systemName: "moon.fill")
                                .font(.system(size: 36))
                                .foregroundColor(Color(red: 0.4, green: 0.4, blue: 0.4))
                            Text("AMOLED Power Saving Mode Active")
                                .font(.subheadline)
                                .foregroundColor(.gray)
                            Text("Double tap screen to wake")
                                .font(.caption2)
                                .foregroundColor(Color(red: 0.3, green: 0.3, blue: 0.3))
                        }
                    )
                    .onTapGesture(count: 2) {
                        viewModel.toggleBlackout()
                    }
            } else {
                VStack(spacing: 16) {
                    // 1. Header & Telemetry
                    headerView
                    
                    // 2. Viewfinder / Stream Status Card
                    viewfinderView
                    
                    // 3. Quick Action Neumorphic Buttons
                    quickActionsView
                    
                    // 4. Hardware Zoom Controller
                    zoomControllerView
                    
                    Spacer()
                }
                .padding(.horizontal, 16)
                .padding(.top, 8)
            }
        }
    }
    
    // MARK: - Header
    private var headerView: some View {
        HStack {
            HStack(spacing: 8) {
                Circle()
                    .fill(viewModel.clientCount > 0 ? Color.green : Color.orange)
                    .frame(width: 8, height: 8)
                Text(tr("app_name"))
                    .font(.system(size: 20, weight: .bold, design: .rounded))
                    .foregroundColor(.white)
                Text("v1.2")
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundColor(Color.cyan)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(Color.cyan.opacity(0.15))
                    .cornerRadius(6)
            }
            
            Spacer()
            
            // Language selector
            Picker("", selection: $selectedLanguage) {
                Text("🌐 Auto").tag("auto")
                Text("EN").tag("en")
                Text("TR").tag("tr")
                Text("DE").tag("de")
                Text("FR").tag("fr")
                Text("ES").tag("es")
            }
            .pickerStyle(.menu)
            .tint(.white.opacity(0.7))
            
            // Battery Pill
            HStack(spacing: 4) {
                Image(systemName: "battery.100")
                    .font(.system(size: 12))
                Text("\(viewModel.batteryLevel)%")
                    .font(.system(size: 12, weight: .medium))
            }
            .foregroundColor(.white.opacity(0.8))
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(Color.white.opacity(0.06))
            .cornerRadius(8)
        }
    }
    
    // MARK: - Viewfinder Area
    private var viewfinderView: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 16)
                .fill(Color(red: 0.08, green: 0.08, blue: 0.10))
                .overlay(
                    RoundedRectangle(cornerRadius: 16)
                        .stroke(Color.white.opacity(0.06), lineWidth: 1)
                )
                .frame(height: 260)
            
            if viewModel.isScreenMirroring {
                VStack(spacing: 8) {
                    Image(systemName: "iphone.badge.play")
                        .font(.system(size: 40))
                        .foregroundColor(Color.cyan)
                    Text("Screen Mirroring Active")
                        .font(.headline)
                        .foregroundColor(.white)
                    Text("Streaming display at native resolution")
                        .font(.caption)
                        .foregroundColor(.gray)
                }
            } else {
                VStack(spacing: 8) {
                    Image(systemName: "video.fill")
                        .font(.system(size: 40))
                        .foregroundColor(viewModel.clientCount > 0 ? Color.green : Color.gray)
                    Text(viewModel.clientCount > 0 ? tr("status_live") : tr("status_standby"))
                        .font(.headline)
                        .foregroundColor(.white)
                    Text("\(tr("ip_title")): \(viewModel.deviceIP):4747")
                        .font(.caption)
                        .foregroundColor(.gray)
                }
            }
            
            // HUD Overlay at Bottom of Viewfinder
            VStack {
                Spacer()
                HStack {
                    HStack(spacing: 4) {
                        Image(systemName: "person.2.fill")
                            .font(.system(size: 11))
                        Text("\(viewModel.clientCount) \(tr("clients"))")
                            .font(.system(size: 11, weight: .semibold))
                    }
                    .foregroundColor(.white.opacity(0.9))
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color.black.opacity(0.6))
                    .cornerRadius(6)
                    
                    Spacer()
                    
                    Text("\(Int(viewModel.currentFps)) FPS • \(Int(viewModel.currentBitrateKbps)) \(tr("bitrate"))")
                        .font(.system(size: 11, weight: .semibold, design: .monospaced))
                        .foregroundColor(Color.cyan)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(Color.black.opacity(0.6))
                        .cornerRadius(6)
                }
                .padding(12)
            }
        }
        .frame(height: 260)
    }
    
    // MARK: - Quick Actions Bar
    private var quickActionsView: some View {
        HStack(spacing: 12) {
            actionButton(
                icon: viewModel.isTorchOn ? "flashlight.on.fill" : "flashlight.off.fill",
                title: tr("torch"),
                isActive: viewModel.isTorchOn
            ) {
                viewModel.toggleTorch()
            }
            
            actionButton(
                icon: "camera.rotate.fill",
                title: tr("flip"),
                isActive: viewModel.isFrontCamera
            ) {
                viewModel.switchCamera()
            }
            
            actionButton(
                icon: viewModel.isAudioMuted ? "mic.slash.fill" : "mic.fill",
                title: tr("mic"),
                isActive: !viewModel.isAudioMuted
            ) {
                viewModel.toggleAudioMute()
            }
            
            actionButton(
                icon: "moon.fill",
                title: tr("blackout"),
                isActive: viewModel.isBlackout
            ) {
                viewModel.toggleBlackout()
            }
            
            actionButton(
                icon: viewModel.isScreenMirroring ? "stop.circle.fill" : "rectangle.dashed.badge.record",
                title: viewModel.isScreenMirroring ? tr("stop_mirror") : tr("mirror"),
                isActive: viewModel.isScreenMirroring
            ) {
                viewModel.toggleScreenMirror()
            }
        }
    }
    
    private func actionButton(icon: String, title: String, isActive: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            VStack(spacing: 6) {
                Image(systemName: icon)
                    .font(.system(size: 18))
                Text(title)
                    .font(.system(size: 10, weight: .medium))
            }
            .foregroundColor(isActive ? Color.cyan : Color.white.opacity(0.8))
            .frame(maxWidth: .infinity)
            .padding(.vertical, 12)
            .background(
                RoundedRectangle(cornerRadius: 12)
                    .fill(isActive ? Color.cyan.opacity(0.12) : Color.white.opacity(0.04))
                    .overlay(
                        RoundedRectangle(cornerRadius: 12)
                            .stroke(isActive ? Color.cyan.opacity(0.4) : Color.white.opacity(0.08), lineWidth: 1)
                    )
            )
        }
    }
    
    // MARK: - Zoom Controller
    private var zoomControllerView: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text(tr("zoom_title"))
                    .font(.system(size: 12, weight: .bold))
                    .foregroundColor(Color.white.opacity(0.6))
                Spacer()
                Text(String(format: "%.1fx", viewModel.zoomFactor))
                    .font(.system(size: 13, weight: .bold, design: .monospaced))
                    .foregroundColor(Color.cyan)
            }
            
            // Zoom Slider
            Slider(value: Binding(
                get: { viewModel.zoomFactor },
                set: { viewModel.setZoom($0) }
            ), in: 1.0...100.0, step: 0.1)
            .tint(Color.cyan)
            
            // Preset Zoom Buttons
            HStack(spacing: 8) {
                ForEach([1.0, 3.0, 10.0, 100.0], id: \.self) { z in
                    Button(action: {
                        viewModel.setZoom(Float(z))
                    }) {
                        Text("\(Int(z))x")
                            .font(.system(size: 11, weight: .bold))
                            .foregroundColor(abs(Double(viewModel.zoomFactor) - z) < 0.2 ? Color.black : Color.white)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 6)
                            .background(
                                RoundedRectangle(cornerRadius: 8)
                                    .fill(abs(Double(viewModel.zoomFactor) - z) < 0.2 ? Color.cyan : Color.white.opacity(0.06))
                            )
                    }
                }
            }
        }
        .padding(14)
        .background(
            RoundedRectangle(cornerRadius: 14)
                .fill(Color(red: 0.08, green: 0.08, blue: 0.10))
                .overlay(
                    RoundedRectangle(cornerRadius: 14)
                        .stroke(Color.white.opacity(0.06), lineWidth: 1)
                )
        )
    }
}
