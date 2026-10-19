//
//  AudioCaptureManager.swift
//  AselCam iOS
//
//  Microphone capture using AVAudioEngine with real-time resampling to 24 kHz Mono Int16 PCM.
//  Matching desktop AudioSink specifications.
//

import Foundation
import AVFoundation

public final class AudioCaptureManager {
    public typealias AudioPacketCallback = (Data) -> Void
    
    private let audioEngine = AVAudioEngine()
    private var audioConverter: AVAudioConverter?
    private let targetFormat: AVAudioFormat
    private let callback: AudioPacketCallback
    
    public var isMuted: Bool = false
    public var audioGain: Float = 1.0
    
    private let queue = DispatchQueue(label: "com.aselens.aselcam.audiocapture", qos: .userInteractive)
    
    public init(callback: @escaping AudioPacketCallback) {
        self.callback = callback
        
        // Target: 24,000 Hz, 1 Channel (Mono), Linear PCM Int16
        self.targetFormat = AVAudioFormat(
            commonFormat: .pcmFormatInt16,
            sampleRate: 24000,
            channels: 1,
            interleaved: true
        )!
    }
    
    public func start() {
        queue.async { [weak self] in
            guard let self = self else { return }
            
            let audioSession = AVAudioSession.sharedInstance()
            do {
                try audioSession.setCategory(.playAndRecord, mode: .videoChat, options: [.defaultToSpeaker, .allowBluetooth])
                try audioSession.setActive(true)
                
                let inputNode = self.audioEngine.inputNode
                let inputFormat = inputNode.outputFormat(forBus: 0)
                
                self.audioConverter = AVAudioConverter(from: inputFormat, to: self.targetFormat)
                
                inputNode.removeTap(onBus: 0)
                inputNode.installTap(onBus: 0, bufferSize: 1024, format: inputFormat) { [weak self] (buffer, time) in
                    self?.processAudioBuffer(buffer: buffer, time: time)
                }
                
                self.audioEngine.prepare()
                try self.audioEngine.start()
                print("[AselCam-iOS] Audio capture started @ 24kHz Mono")
            } catch {
                print("[AselCam-iOS] Failed to start audio engine: \(error)")
            }
        }
    }
    
    public func stop() {
        queue.async { [weak self] in
            guard let self = self else { return }
            self.audioEngine.inputNode.removeTap(onBus: 0)
            self.audioEngine.stop()
            try? AVAudioSession.sharedInstance().setActive(false)
            print("[AselCam-iOS] Audio capture stopped")
        }
    }
    
    private func processAudioBuffer(buffer: AVAudioPCMBuffer, time: AVAudioTime) {
        guard !isMuted, let converter = audioConverter else { return }
        
        // Calculate output buffer capacity based on sample rate ratio
        let sampleRateRatio = targetFormat.sampleRate / buffer.format.sampleRate
        let outputFrameCapacity = AVAudioFrameCount(Double(buffer.frameLength) * sampleRateRatio + 100)
        
        guard let outputBuffer = AVAudioPCMBuffer(pcmFormat: targetFormat, frameCapacity: outputFrameCapacity) else { return }
        
        var error: NSError?
        var isConsumed = false
        
        let status = converter.convert(to: outputBuffer, error: &error) { _, outStatus in
            if !isConsumed {
                isConsumed = true
                outStatus.pointee = .haveData
                return buffer
            } else {
                outStatus.pointee = .noDataNow
                return nil
            }
        }
        
        guard status != .error, error == nil, outputBuffer.frameLength > 0 else { return }
        
        // Apply audio gain if needed
        if let channelData = outputBuffer.int16ChannelData {
            let samples = channelData[0]
            let count = Int(outputBuffer.frameLength)
            
            if audioGain != 1.0 {
                let gain = audioGain
                for i in 0..<count {
                    let scaled = Float(samples[i]) * gain
                    samples[i] = Int16(clamping: Int(scaled))
                }
            }
            
            let dataLength = count * MemoryLayout<Int16>.size
            let payload = Data(bytes: samples, count: dataLength)
            
            let pts = UInt64(Date().timeIntervalSince1970 * 1_000_000)
            let packet = AselProtocol.createPacket(
                type: .audioPCM,
                flags: .none,
                timestampUs: pts,
                payload: payload
            )
            
            callback(packet)
        }
    }
}
