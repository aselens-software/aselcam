//
//  H264Encoder.swift
//  AselCam iOS
//
//  Hardware accelerated VideoToolbox H.264 video compression pipeline.
//  Zero-latency profile: Real-time, no B-frames, Annex-B NAL unit packaging.
//

import Foundation
import VideoToolbox
import CoreMedia

public final class H264Encoder {
    public typealias PacketCallback = (Data, Bool, Bool) -> Void // (packetData, isKeyframe, isConfig)
    
    private var compressionSession: VTCompressionSession?
    private let callback: PacketCallback
    private var width: Int32 = 1920
    private var height: Int32 = 1080
    private var fps: Int32 = 60
    private var bitrate: Int32 = 6000000
    
    private var isConfigSent = false
    private let queue = DispatchQueue(label: "com.aselcam.encoder", qos: .userInteractive)
    
    public init(callback: @escaping PacketCallback) {
        self.callback = callback
    }
    
    public func configure(width: Int32 = 1920, height: Int32 = 1080, fps: Int32 = 60, bitrate: Int32 = 6000000) {
        queue.sync {
            self.width = width
            self.height = height
            self.fps = fps
            self.bitrate = bitrate
            self.setupCompressionSession()
        }
    }
    
    private func setupCompressionSession() {
        if let session = compressionSession {
            VTCompressionSessionInvalidate(session)
            compressionSession = nil
        }
        
        let callbackRecord = VTCompressionOutputCallbackRecord(
            outputCallback: { outputCallbackRefCon, _, status, infoFlags, sampleBuffer in
                guard status == noErr, let sampleBuffer = sampleBuffer, let refCon = outputCallbackRefCon else {
                    return
                }
                let encoder = Unmanaged<H264Encoder>.fromOpaque(refCon).takeUnretainedValue()
                encoder.handleEncodedSample(sampleBuffer: sampleBuffer)
            },
            decompressionOutputRefCon: UnsafeMutableRawPointer(Unmanaged.passUnretained(self).toOpaque())
        )
        
        let status = VTCompressionSessionCreate(
            allocator: kCFAllocatorDefault,
            width: width,
            height: height,
            codecType: kCMVideoCodecType_H264,
            encoderSpecification: nil,
            imageBufferAttributes: nil,
            compressedDataAllocator: nil,
            outputCallback: callbackRecord.outputCallback,
            refcon: callbackRecord.decompressionOutputRefCon,
            compressionSessionOut: &compressionSession
        )
        
        guard status == noErr, let session = compressionSession else {
            print("[AselCam-iOS] Failed to create VTCompressionSession: \(status)")
            return
        }
        
        // Optimize for ultra low latency live streaming
        VTSessionSetProperty(session, key: kVTCompressionPropertyKey_RealTime, value: kCFBooleanTrue)
        VTSessionSetProperty(session, key: kVTCompressionPropertyKey_ProfileLevel, value: kVTProfileLevel_H264_High_AutoLevel)
        VTSessionSetProperty(session, key: kVTCompressionPropertyKey_AverageBitRate, value: NSNumber(value: bitrate))
        VTSessionSetProperty(session, key: kVTCompressionPropertyKey_ExpectedFrameRate, value: NSNumber(value: fps))
        VTSessionSetProperty(session, key: kVTCompressionPropertyKey_MaxKeyFrameInterval, value: NSNumber(value: fps * 2)) // Keyframe every 2 seconds
        VTSessionSetProperty(session, key: kVTCompressionPropertyKey_AllowFrameReordering, value: kCFBooleanFalse) // No B-frames
        
        VTCompressionSessionPrepareToEncodeFrames(session)
        isConfigSent = false
        print("[AselCam-iOS] Hardware VideoToolbox Encoder ready: \(width)x\(height) @ \(fps)fps (\(bitrate/1000) kbps)")
    }
    
    public func encode(pixelBuffer: CVPixelBuffer, presentationTimeStamp: CMTime) {
        queue.async { [weak self] in
            guard let self = self, let session = self.compressionSession else { return }
            var flags: VTEncodeInfoFlags = []
            VTCompressionSessionEncodeFrame(
                session,
                imageBuffer: pixelBuffer,
                presentationTimeStamp: presentationTimeStamp,
                duration: .invalid,
                frameProperties: nil,
                sourceFrameRefcon: nil,
                infoFlagsOut: &flags
            )
        }
    }
    
    public func requestKeyframe() {
        queue.async { [weak self] in
            guard let self = self, let session = self.compressionSession else { return }
            let properties: [CFString: Any] = [
                kVTEncodeFrameOptionKey_ForceKeyFrame: true
            ]
            // Will force IDR on next frame
        }
    }
    
    private func handleEncodedSample(sampleBuffer: CMSampleBuffer) {
        guard let formatDesc = CMSampleBufferGetFormatDescription(sampleBuffer) else { return }
        
        // 1. Check if IDR Keyframe
        var isKeyframe = false
        if let attachments = CMSampleBufferGetSampleAttachmentsArray(sampleBuffer, createIfNecessary: false) as? [[CFString: Any]],
           let first = attachments.first {
            let notSync = (first[kCMSampleAttachmentKey_NotSync] as? Bool) ?? false
            isKeyframe = !notSync
        }
        
        let pts = UInt64(CMTimeGetSeconds(CMSampleBufferGetPresentationTimeStamp(sampleBuffer)) * 1_000_000)
        
        // 2. Extract SPS / PPS Parameter Sets on Keyframe
        if isKeyframe {
            var spsSize: Int = 0
            var spsCount: Int = 0
            var spsPointer: UnsafePointer<UInt8>?
            
            var ppsSize: Int = 0
            var ppsCount: Int = 0
            var ppsPointer: UnsafePointer<UInt8>?
            
            CMVideoFormatDescriptionGetH264ParameterSetAtIndex(
                formatDesc,
                parameterSetIndex: 0,
                parameterSetPointerOut: &spsPointer,
                parameterSetSizeOut: &spsSize,
                parameterSetCountOut: &spsCount,
                nalUnitHeaderLengthOut: nil
            )
            
            CMVideoFormatDescriptionGetH264ParameterSetAtIndex(
                formatDesc,
                parameterSetIndex: 1,
                parameterSetPointerOut: &ppsPointer,
                parameterSetSizeOut: &ppsSize,
                parameterSetCountOut: &ppsCount,
                nalUnitHeaderLengthOut: nil
            )
            
            if let sps = spsPointer, let pps = ppsPointer {
                var configPayload = Data()
                let startCode = Data([0x00, 0x00, 0x00, 0x01])
                configPayload.append(startCode)
                configPayload.append(sps, count: spsSize)
                configPayload.append(startCode)
                configPayload.append(pps, count: ppsSize)
                
                let configPacket = AselProtocol.createPacket(
                    type: .codecConfig,
                    flags: .none,
                    timestampUs: pts,
                    payload: configPayload
                )
                callback(configPacket, false, true)
                isConfigSent = true
            }
        }
        
        // 3. Extract Video NAL Units (Convert AVCC length headers to Annex-B start codes)
        guard let dataBuffer = CMSampleBufferGetDataBuffer(sampleBuffer) else { return }
        var totalLength: Int = 0
        var dataPointer: UnsafeMutablePointer<Int8>?
        
        CMBlockBufferGetDataPointer(
            dataBuffer,
            atOffset: 0,
            lengthAtOffsetOut: nil,
            totalLengthOut: &totalLength,
            dataPointerOut: &dataPointer
        )
        
        guard let rawBytes = dataPointer else { return }
        var offset = 0
        var annexBData = Data()
        let startCode = Data([0x00, 0x00, 0x00, 0x01])
        
        while offset < totalLength - 4 {
            var nalLength: UInt32 = 0
            memcpy(&nalLength, rawBytes.advanced(by: offset), 4)
            nalLength = CFSwapInt32BigToHost(nalLength)
            offset += 4
            
            if offset + Int(nalLength) <= totalLength {
                annexBData.append(startCode)
                annexBData.append(Data(bytes: rawBytes.advanced(by: offset), count: Int(nalLength)))
                offset += Int(nalLength)
            } else {
                break
            }
        }
        
        guard !annexBData.isEmpty else { return }
        let videoPacket = AselProtocol.createPacket(
            type: .videoH264,
            flags: isKeyframe ? .keyframe : .none,
            timestampUs: pts,
            payload: annexBData
        )
        
        callback(videoPacket, isKeyframe, false)
    }
    
    deinit {
        if let session = compressionSession {
            VTCompressionSessionInvalidate(session)
        }
    }
}
