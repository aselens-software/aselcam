//
//  StreamServer.swift
//  AselCam iOS
//
//  Ultra low-latency TCP streaming server on port 4747.
//  Sends H.264/H.265 video packets and raw PCM audio packets to desktop receivers.
//

import Foundation
import Network

public final class StreamServer {
    public static let defaultPort: UInt16 = 4747
    
    private var listener: NWListener?
    private let queue = DispatchQueue(label: "com.aselens.aselcam.streamserver", qos: .userInteractive)
    private var connections: [NWConnection] = []
    
    // Cached codec configuration and latest keyframe for instant handshake
    private var latestConfigPacket: Data?
    private var latestKeyframePacket: Data?
    
    public var onClientConnected: (() -> Void)?
    public var onNeedKeyframe: (() -> Void)?
    
    // Telemetry
    public private(set) var clientCount: Int = 0
    public private(set) var currentFps: Double = 0
    public private(set) var currentBitrateKbps: Double = 0
    
    private var frameCount: Int = 0
    private var bytesSent: Int = 0
    private var lastTelemetryUpdate: TimeInterval = Date().timeIntervalSince1970
    
    public init() {}
    
    public func start(port: UInt16 = defaultPort) {
        queue.async { [weak self] in
            guard let self = self else { return }
            do {
                let params = NWParameters.tcp
                params.prohibitExpensivePaths = false
                if let tcpOptions = params.defaultProtocolStack.transportProtocol as? NWProtocolTCP.Options {
                    tcpOptions.noDelay = true // Disable Nagle's algorithm for sub-10ms latency
                    tcpOptions.enableKeepalive = true
                }
                
                guard let nwPort = NWEndpoint.Port(rawValue: port) else { return }
                let listener = try NWListener(using: params, on: nwPort)
                
                listener.stateUpdateHandler = { state in
                    switch state {
                    case .ready:
                        print("[AselCam-iOS] StreamServer listening on port \(port)")
                    case .failed(let error):
                        print("[AselCam-iOS] StreamServer failed: \(error)")
                    default:
                        break
                    }
                }
                
                listener.newConnectionHandler = { [weak self] connection in
                    self?.handleNewConnection(connection)
                }
                
                listener.start(queue: self.queue)
                self.listener = listener
            } catch {
                print("[AselCam-iOS] Failed to start StreamServer: \(error)")
            }
        }
    }
    
    public func stop() {
        queue.async { [weak self] in
            guard let self = self else { return }
            self.listener?.cancel()
            self.listener = nil
            for conn in self.connections {
                conn.cancel()
            }
            self.connections.removeAll()
            self.clientCount = 0
        }
    }
    
    private func handleNewConnection(_ connection: NWConnection) {
        connection.start(queue: queue)
        connections.append(connection)
        clientCount = connections.count
        print("[AselCam-iOS] Desktop client connected. Total clients: \(clientCount)")
        
        // Immediately send cached SPS/PPS codec config & latest IDR keyframe
        if let config = latestConfigPacket {
            connection.send(content: config, completion: .idempotent)
        }
        if let keyframe = latestKeyframePacket {
            connection.send(content: keyframe, completion: .idempotent)
        }
        
        onClientConnected?()
        onNeedKeyframe?()
        
        connection.stateUpdateHandler = { [weak self, weak connection] state in
            guard let self = self, let connection = connection else { return }
            switch state {
            case .failed, .cancelled:
                self.queue.async {
                    self.connections.removeAll(where: { $0 === connection })
                    self.clientCount = self.connections.count
                    print("[AselCam-iOS] Desktop client disconnected. Remaining: \(self.clientCount)")
                }
            default:
                break
            }
        }
    }
    
    public func sendPacket(_ packet: Data, isKeyframe: Bool = false, isConfig: Bool = false) {
        queue.async { [weak self] in
            guard let self = self else { return }
            
            if isConfig {
                self.latestConfigPacket = packet
            }
            if isKeyframe {
                self.latestKeyframePacket = packet
            }
            
            guard !self.connections.isEmpty else { return }
            
            self.bytesSent += packet.count
            self.frameCount += 1
            
            // Broadcast packet to all connected desktop clients
            for connection in self.connections {
                connection.send(content: packet, completion: .contentProcessed({ error in
                    if let error = error {
                        print("[AselCam-iOS] Send error: \(error)")
                    }
                }))
            }
            
            // Update telemetry once per second
            let now = Date().timeIntervalSince1970
            let elapsed = now - self.lastTelemetryUpdate
            if elapsed >= 1.0 {
                self.currentFps = Double(self.frameCount) / elapsed
                self.currentBitrateKbps = (Double(self.bytesSent) * 8.0) / (elapsed * 1000.0)
                self.frameCount = 0
                self.bytesSent = 0
                self.lastTelemetryUpdate = now
            }
        }
    }
}
