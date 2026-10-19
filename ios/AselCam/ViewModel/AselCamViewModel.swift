//
//  AselCamViewModel.swift
//  AselCam iOS
//
//  Central coordinator binding AVFoundation, VideoToolbox, Audio, ReplayKit,
//  and Network Servers together. Implements the CommandDelegate.
//

import Foundation
import Combine
import UIKit
import CoreMedia

public final class AselCamViewModel: ObservableObject, CommandDelegate {
    @Published public var isStreaming: Bool = false
    @Published public var clientCount: Int = 0
    @Published public var currentFps: Double = 0
    @Published public var currentBitrateKbps: Double = 0
    @Published public var isTorchOn: Bool = false
    @Published public var zoomFactor: Float = 1.0
    @Published public var isFrontCamera: Bool = false
    @Published public var isBlackout: Bool = false
    @Published public var isScreenMirroring: Bool = false
    @Published public var isAudioMuted: Bool = false
    @Published public var isPreviewHidden: Bool = false
    @Published public var deviceIP: String = "127.0.0.1"
    @Published public var batteryLevel: Int = 100
    
    public let streamServer = StreamServer()
    public let commandServer = CommandServer()
    
    private var cameraManager: CameraManager?
    private var encoder: H264Encoder?
    private var audioCapture: AudioCaptureManager?
    private var screenMirrorManager: ScreenMirrorManager?
    
    private var telemetryTimer: Timer?
    
    public init() {
        setupServers()
        setupMediaPipeline()
        updateDeviceIP()
        UIDevice.current.isBatteryMonitoringEnabled = true
        batteryLevel = Int(UIDevice.current.batteryLevel * 100)
    }
    
    private func setupServers() {
        commandServer.delegate = self
        commandServer.start()
        
        streamServer.onNeedKeyframe = { [weak self] in
            self?.encoder?.requestKeyframe()
        }
        streamServer.start()
        
        telemetryTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] _ in
            guard let self = self else { return }
            self.clientCount = self.streamServer.clientCount
            self.currentFps = self.streamServer.currentFps
            self.currentBitrateKbps = self.streamServer.currentBitrateKbps
            let lvl = Int(UIDevice.current.batteryLevel * 100)
            if lvl >= 0 { self.batteryLevel = lvl }
        }
    }
    
    private func setupMediaPipeline() {
        encoder = H264Encoder { [weak self] (packet, isKeyframe, isConfig) in
            self?.streamServer.sendPacket(packet, isKeyframe: isKeyframe, isConfig: isConfig)
        }
        encoder?.configure(width: 1920, height: 1080, fps: 60, bitrate: 6000000)
        
        cameraManager = CameraManager { [weak self] (pixelBuffer, pts) in
            guard let self = self, !self.isScreenMirroring else { return }
            self.encoder?.encode(pixelBuffer: pixelBuffer, presentationTimeStamp: pts)
        }
        
        audioCapture = AudioCaptureManager { [weak self] audioPacket in
            self?.streamServer.sendPacket(audioPacket, isKeyframe: false, isConfig: false)
        }
        
        screenMirrorManager = ScreenMirrorManager { [weak self] (pixelBuffer, pts) in
            guard let self = self, self.isScreenMirroring else { return }
            self.encoder?.encode(pixelBuffer: pixelBuffer, presentationTimeStamp: pts)
        }
        
        cameraManager?.startSession(preset: .hd1920x1080, targetFps: 60.0)
        audioCapture?.start()
        isStreaming = true
    }
    
    public func startStreaming() {
        cameraManager?.startSession(preset: .hd1920x1080, targetFps: 60.0)
        audioCapture?.start()
        isStreaming = true
    }
    
    public func stopStreaming() {
        cameraManager?.stopSession()
        audioCapture?.stop()
        isStreaming = false
    }
    
    public func toggleTorch() {
        isTorchOn.toggle()
        cameraManager?.setTorch(enabled: isTorchOn)
    }
    
    public func switchCamera() {
        cameraManager?.switchCamera()
        isFrontCamera.toggle()
    }
    
    public func setZoom(_ factor: Float) {
        zoomFactor = factor
        cameraManager?.setZoom(factor: factor)
    }
    
    public func toggleBlackout() {
        isBlackout.toggle()
    }
    
    public func toggleScreenMirror() {
        if isScreenMirroring {
            screenMirrorManager?.stopMirroring { [weak self] in
                DispatchQueue.main.async {
                    self?.isScreenMirroring = false
                }
            }
        } else {
            screenMirrorManager?.startMirroring { [weak self] success, _ in
                DispatchQueue.main.async {
                    if success {
                        self?.isScreenMirroring = true
                    }
                }
            }
        }
    }
    
    public func toggleAudioMute() {
        isAudioMuted.toggle()
        audioCapture?.isMuted = isAudioMuted
    }
    
    // MARK: - CommandDelegate
    public func onGetDeviceInfo() -> [String : Any] {
        return [
            "model": UIDevice.current.model,
            "name": UIDevice.current.name,
            "system_version": UIDevice.current.systemVersion,
            "battery_level": batteryLevel,
            "is_charging": UIDevice.current.batteryState == .charging || UIDevice.current.batteryState == .full,
            "camera_id": isFrontCamera ? "1" : "0",
            "is_screen_mirroring": isScreenMirroring,
            "is_torch_on": isTorchOn,
            "current_zoom": zoomFactor,
            "max_hardware_zoom": 100.0,
            "supported_codecs": ["h264", "hevc"]
        ]
    }
    
    public func onSwitchCamera(cameraId: String) {
        switchCamera()
    }
    
    public func onSetTorch(enabled: Bool) {
        isTorchOn = enabled
        cameraManager?.setTorch(enabled: enabled)
    }
    
    public func onSetZoom(zoom: Float) {
        setZoom(zoom)
    }
    
    public func onSetConfig(width: Int, height: Int, fps: Int, bitrate: Int, codec: String) {
        encoder?.configure(width: Int32(width), height: Int32(height), fps: Int32(fps), bitrate: Int32(bitrate))
    }
    
    public func onSetMute(muted: Bool) {
        isAudioMuted = muted
        audioCapture?.isMuted = muted
    }
    
    public func onSetAudioGain(gain: Float) {
        audioCapture?.audioGain = gain
    }
    
    public func onSetPreviewEnabled(enabled: Bool) {
        isPreviewHidden = !enabled
    }
    
    public func onSetCameraEnabled(enabled: Bool) {
        if enabled {
            cameraManager?.startSession()
        } else {
            cameraManager?.stopSession()
        }
    }
    
    public func onSetBlackout(enabled: Bool) {
        isBlackout = enabled
    }
    
    public func onSetScreenMirror(enabled: Bool) {
        if enabled != isScreenMirroring {
            toggleScreenMirror()
        }
    }
    
    public func onStartStream() {
        isStreaming = true
    }
    
    public func onStopStream() {
        isStreaming = false
    }
    
    private func updateDeviceIP() {
        var address: String?
        var ifaddr: UnsafeMutablePointer<ifaddrs>?
        guard getifaddrs(&ifaddr) == 0 else { return }
        guard let firstAddr = ifaddr else { return }
        
        for ptr in sequence(first: firstAddr, next: { $0.pointee.ifa_next }) {
            let interface = ptr.pointee
            let addrFamily = interface.ifa_addr.pointee.sa_family
            if addrFamily == UInt8(AF_INET) {
                let name = String(cString: interface.ifa_name)
                if name == "en0" { // Wi-Fi adapter
                    var hostname = [CChar](repeating: 0, count: Int(NI_MAXHOST))
                    getnameinfo(interface.ifa_addr, socklen_t(interface.ifa_addr.pointee.sa_len),
                                &hostname, socklen_t(hostname.count),
                                nil, socklen_t(0), NI_NUMERICHOST)
                    address = String(cString: hostname)
                }
            }
        }
        freeifaddrs(ifaddr)
        if let addr = address {
            self.deviceIP = addr
        }
    }
}
