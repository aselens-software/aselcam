//
//  ScreenMirrorManager.swift
//  AselCam iOS
//
//  Ultra-fast screen broadcasting via Apple ReplayKit framework.
//  Streams iOS device screen in real-time to desktop AselCam virtual webcam.
//

import Foundation
import ReplayKit

public final class ScreenMirrorManager {
    public typealias ScreenFrameCallback = (CVPixelBuffer, CMTime) -> Void
    
    private let recorder = RPScreenRecorder.shared()
    private let frameCallback: ScreenFrameCallback
    public private(set) var isMirroring: Bool = false
    
    public init(frameCallback: @escaping ScreenFrameCallback) {
        self.frameCallback = frameCallback
    }
    
    public func startMirroring(completion: @escaping (Bool, String?) -> Void) {
        guard recorder.isAvailable else {
            completion(false, "ReplayKit is not available on this device")
            return
        }
        
        guard !isMirroring else {
            completion(true, nil)
            return
        }
        
        recorder.startCapture(handler: { [weak self] (sampleBuffer, sampleBufferType, error) in
            guard let self = self, error == nil else { return }
            
            if sampleBufferType == .video {
                guard let pixelBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }
                let pts = CMSampleBufferGetPresentationTimeStamp(sampleBuffer)
                self.frameCallback(pixelBuffer, pts)
            }
        }) { [weak self] error in
            if let error = error {
                print("[AselCam-iOS] Screen capture start failed: \(error)")
                completion(false, error.localizedDescription)
            } else {
                self?.isMirroring = true
                print("[AselCam-iOS] Screen capture started successfully")
                completion(true, nil)
            }
        }
    }
    
    public func stopMirroring(completion: @escaping () -> Void) {
        guard isMirroring else {
            completion()
            return
        }
        
        recorder.stopCapture { [weak self] error in
            self?.isMirroring = false
            if let error = error {
                print("[AselCam-iOS] Screen capture stop warning: \(error)")
            } else {
                print("[AselCam-iOS] Screen capture stopped")
            }
            completion()
        }
    }
}
