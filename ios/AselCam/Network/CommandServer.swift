//
//  CommandServer.swift
//  AselCam iOS
//
//  Bi-directional JSON Control Protocol server on port 4748.
//  Matches AselCam Desktop and Android command schemas.
//

import Foundation
import Network
import UIKit

public protocol CommandDelegate: AnyObject {
    func onGetDeviceInfo() -> [String: Any]
    func onSwitchCamera(cameraId: String)
    func onSetTorch(enabled: Bool)
    func onSetZoom(zoom: Float)
    func onSetConfig(width: Int, height: Int, fps: Int, bitrate: Int, codec: String)
    func onSetMute(muted: Bool)
    func onSetAudioGain(gain: Float)
    func onSetPreviewEnabled(enabled: Bool)
    func onSetCameraEnabled(enabled: Bool)
    func onSetBlackout(enabled: Bool)
    func onSetScreenMirror(enabled: Bool)
    func onStartStream()
    func onStopStream()
}

public final class CommandServer {
    public static let defaultPort: UInt16 = 4748
    
    private var listener: NWListener?
    private let queue = DispatchQueue(label: "com.aselcam.cmdserver", qos: .userInitiated)
    private var connections: [NWConnection] = []
    
    public weak var delegate: CommandDelegate?
    
    public init() {}
    
    public func start(port: UInt16 = defaultPort) {
        queue.async { [weak self] in
            guard let self = self else { return }
            do {
                let params = NWParameters.tcp
                if let tcpOptions = params.defaultProtocolStack.transportProtocol as? NWProtocolTCP.Options {
                    tcpOptions.noDelay = true
                    tcpOptions.enableKeepalive = true
                }
                
                guard let nwPort = NWEndpoint.Port(rawValue: port) else { return }
                let listener = try NWListener(using: params, on: nwPort)
                
                listener.stateUpdateHandler = { state in
                    switch state {
                    case .ready:
                        print("[AselCam-iOS] CommandServer listening on port \(port)")
                    case .failed(let error):
                        print("[AselCam-iOS] CommandServer failed: \(error)")
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
                print("[AselCam-iOS] Failed to start CommandServer: \(error)")
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
        }
    }
    
    private func handleNewConnection(_ connection: NWConnection) {
        connection.start(queue: queue)
        connections.append(connection)
        
        connection.stateUpdateHandler = { [weak self, weak connection] state in
            guard let self = self, let connection = connection else { return }
            switch state {
            case .failed, .cancelled:
                self.queue.async {
                    self.connections.removeAll(where: { $0 === connection })
                }
            default:
                break
            }
        }
        
        readNextMessage(connection)
    }
    
    private func readNextMessage(_ connection: NWConnection) {
        connection.receive(minimumIncompleteLength: 1, maximumLength: 65536) { [weak self, weak connection] content, _, isComplete, error in
            guard let self = self, let connection = connection else { return }
            
            if let data = content, let text = String(data: data, encoding: .utf8) {
                let lines = text.components(separatedBy: .newlines)
                for line in lines where !line.trimmingCharacters(in: .whitespaces).isEmpty {
                    self.processCommand(line, connection: connection)
                }
            }
            
            if !isComplete && error == nil {
                self.readNextMessage(connection)
            }
        }
    }
    
    private func processCommand(_ jsonString: String, connection: NWConnection) {
        guard let data = jsonString.data(using: .utf8),
              let json = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any],
              let cmd = json["cmd"] as? String else {
            return
        }
        
        var reply: [String: Any] = ["reply_to": cmd, "status": "ok"]
        
        DispatchQueue.main.sync {
            switch cmd {
            case "get_info":
                reply["data"] = self.delegate?.onGetDeviceInfo() ?? [:]
            case "switch_camera":
                let camId = json["camera_id"] as? String ?? "0"
                self.delegate?.onSwitchCamera(cameraId: camId)
            case "set_torch":
                let enabled = json["enabled"] as? Bool ?? false
                self.delegate?.onSetTorch(enabled: enabled)
            case "set_zoom":
                let zoom = (json["zoom"] as? NSNumber)?.floatValue ?? 1.0
                self.delegate?.onSetZoom(zoom: zoom)
            case "set_config":
                let width = json["width"] as? Int ?? 1920
                let height = json["height"] as? Int ?? 1080
                let fps = json["fps"] as? Int ?? 30
                let bitrate = json["bitrate"] as? Int ?? 6000000
                let codec = json["codec"] as? String ?? "h264"
                self.delegate?.onSetConfig(width: width, height: height, fps: fps, bitrate: bitrate, codec: codec)
            case "set_mute":
                let muted = json["muted"] as? Bool ?? false
                self.delegate?.onSetMute(muted: muted)
            case "set_audio_gain":
                let gain = (json["gain"] as? NSNumber)?.floatValue ?? 1.0
                self.delegate?.onSetAudioGain(gain: gain)
            case "set_preview":
                let enabled = json["enabled"] as? Bool ?? true
                self.delegate?.onSetPreviewEnabled(enabled: enabled)
            case "set_camera_enabled":
                let enabled = json["enabled"] as? Bool ?? true
                self.delegate?.onSetCameraEnabled(enabled: enabled)
            case "blackout":
                let enabled = json["enabled"] as? Bool ?? false
                self.delegate?.onSetBlackout(enabled: enabled)
            case "set_screen_mirror":
                let enabled = json["enabled"] as? Bool ?? false
                self.delegate?.onSetScreenMirror(enabled: enabled)
            case "start_stream":
                self.delegate?.onStartStream()
            case "stop_stream":
                self.delegate?.onStopStream()
            case "ping":
                reply["status"] = "pong"
                reply["timestamp"] = UInt64(Date().timeIntervalSince1970 * 1000)
            default:
                reply["status"] = "error"
                reply["message"] = "Unknown command: \(cmd)"
            }
        }
        
        if let replyData = try? JSONSerialization.data(withJSONObject: reply),
           var replyString = String(data: replyData, encoding: .utf8) {
            replyString += "\n"
            if let outData = replyString.data(using: .utf8) {
                connection.send(content: outData, completion: .contentProcessed({ _ in }))
            }
        }
    }
}
