//
//  CameraManager.swift
//  AselCam iOS
//
//  High-performance AVFoundation Camera Capture Engine.
//  Supports 4K/1080p/720p @ 60/30 FPS, hardware optical/digital zoom, torch, and multi-lens switching.
//

import Foundation
import AVFoundation
import UIKit

public final class CameraManager: NSObject, AVCaptureVideoDataOutputSampleBufferDelegate {
    public typealias VideoFrameCallback = (CVPixelBuffer, CMTime) -> Void
    
    private let captureSession = AVCaptureSession()
    private let videoOutput = AVCaptureVideoDataOutput()
    private let sessionQueue = DispatchQueue(label: "com.aselcam.camera.session", qos: .userInteractive)
    
    private var currentDevice: AVCaptureDevice?
    private var currentInput: AVCaptureDeviceInput?
    private var isFrontFacing: Bool = false
    
    private let frameCallback: VideoFrameCallback
    
    public var onCameraSwitched: ((String) -> Void)?
    
    public init(frameCallback: @escaping VideoFrameCallback) {
        self.frameCallback = frameCallback
        super.init()
    }
    
    public func startSession(preset: AVCaptureSession.Preset = .hd1920x1080, targetFps: Double = 60.0) {
        sessionQueue.async { [weak self] in
            guard let self = self else { return }
            self.captureSession.beginConfiguration()
            
            if self.captureSession.canSetSessionPreset(preset) {
                self.captureSession.sessionPreset = preset
            } else {
                self.captureSession.sessionPreset = .high
            }
            
            // Default to back wide-angle camera
            let device = self.getDevice(position: .back) ?? AVCaptureDevice.default(for: .video)
            guard let videoDevice = device,
                  let input = try? AVCaptureDeviceInput(device: videoDevice) else {
                self.captureSession.commitConfiguration()
                return
            }
            
            self.currentDevice = videoDevice
            self.currentInput = input
            self.isFrontFacing = (videoDevice.position == .front)
            
            if self.captureSession.canAddInput(input) {
                self.captureSession.addInput(input)
            }
            
            self.videoOutput.alwaysDiscardsLateVideoFrames = true
            self.videoOutput.videoSettings = [
                kCVPixelBufferPixelFormatTypeKey as String: Int(kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange)
            ]
            self.videoOutput.setSampleBufferDelegate(self, queue: self.sessionQueue)
            
            if self.captureSession.canAddOutput(self.videoOutput) {
                self.captureSession.addOutput(self.videoOutput)
            }
            
            if let connection = self.videoOutput.connection(with: .video) {
                if connection.isVideoOrientationSupported {
                    connection.videoOrientation = .portrait
                }
                if connection.isVideoMirroringSupported {
                    connection.isVideoMirrored = self.isFrontFacing
                }
            }
            
            self.captureSession.commitConfiguration()
            self.setFrameRate(fps: targetFps)
            self.captureSession.startRunning()
            print("[AselCam-iOS] Camera session started with preset: \(preset.rawValue)")
        }
    }
    
    public func stopSession() {
        sessionQueue.async { [weak self] in
            guard let self = self else { return }
            if self.captureSession.isRunning {
                self.captureSession.stopRunning()
            }
        }
    }
    
    public func switchCamera() {
        sessionQueue.async { [weak self] in
            guard let self = self else { return }
            let newPosition: AVCaptureDevice.Position = self.isFrontFacing ? .back : .front
            guard let newDevice = self.getDevice(position: newPosition),
                  let newInput = try? AVCaptureDeviceInput(device: newDevice) else {
                return
            }
            
            self.captureSession.beginConfiguration()
            if let currentInput = self.currentInput {
                self.captureSession.removeInput(currentInput)
            }
            
            if self.captureSession.canAddInput(newInput) {
                self.captureSession.addInput(newInput)
                self.currentInput = newInput
                self.currentDevice = newDevice
                self.isFrontFacing = (newPosition == .front)
            }
            
            if let connection = self.videoOutput.connection(with: .video) {
                if connection.isVideoOrientationSupported {
                    connection.videoOrientation = .portrait
                }
                if connection.isVideoMirroringSupported {
                    connection.isVideoMirrored = self.isFrontFacing
                }
            }
            
            self.captureSession.commitConfiguration()
            self.setFrameRate(fps: 60.0)
            
            let camDesc = self.isFrontFacing ? "Front Camera" : "Back Camera"
            print("[AselCam-iOS] Switched camera to: \(camDesc)")
            DispatchQueue.main.async {
                self.onCameraSwitched?(camDesc)
            }
        }
    }
    
    public func setZoom(factor: Float) {
        sessionQueue.async { [weak self] in
            guard let self = self, let device = self.currentDevice else { return }
            do {
                try device.lockForConfiguration()
                let maxZoom = Float(min(device.activeFormat.videoMaxZoomFactor, 100.0))
                let clamped = max(1.0, min(factor, maxZoom))
                device.videoZoomFactor = CGFloat(clamped)
                device.unlockForConfiguration()
            } catch {
                print("[AselCam-iOS] Failed to set zoom: \(error)")
            }
        }
    }
    
    public func setTorch(enabled: Bool) {
        sessionQueue.async { [weak self] in
            guard let self = self, let device = self.currentDevice, device.hasTorch else { return }
            do {
                try device.lockForConfiguration()
                device.torchMode = enabled ? .on : .off
                device.unlockForConfiguration()
            } catch {
                print("[AselCam-iOS] Failed to set torch: \(error)")
            }
        }
    }
    
    public func setFrameRate(fps: Double) {
        guard let device = currentDevice else { return }
        do {
            try device.lockForConfiguration()
            var selectedFormat: AVCaptureDevice.Format?
            var selectedRange: AVFrameRateRange?
            
            for format in device.formats {
                for range in format.videoSupportedFrameRateRanges {
                    if range.maxFrameRate >= fps && range.minFrameRate <= fps {
                        selectedFormat = format
                        selectedRange = range
                        break
                    }
                }
            }
            
            if let range = selectedRange {
                device.activeVideoMinFrameDuration = CMTime(value: 1, timescale: CMTimeScale(range.maxFrameRate))
                device.activeVideoMaxFrameDuration = CMTime(value: 1, timescale: CMTimeScale(range.maxFrameRate))
            }
            device.unlockForConfiguration()
        } catch {
            print("[AselCam-iOS] Failed to configure framerate: \(error)")
        }
    }
    
    private func getDevice(position: AVCaptureDevice.Position) -> AVCaptureDevice? {
        let discoverySession = AVCaptureDevice.DiscoverySession(
            deviceTypes: [.builtInTripleCamera, .builtInDualWideCamera, .builtInWideAngleCamera],
            mediaType: .video,
            position: position
        )
        return discoverySession.devices.first
    }
    
    // MARK: - AVCaptureVideoDataOutputSampleBufferDelegate
    public func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection) {
        guard let pixelBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }
        let pts = CMSampleBufferGetPresentationTimeStamp(sampleBuffer)
        frameCallback(pixelBuffer, pts)
    }
}
