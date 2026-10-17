//
//  Protocol.swift
//  AselCam iOS
//
//  Binary wire protocol matching AselCam Desktop and Android implementations.
//  Header Size: 18 bytes:
//  [4 bytes: Magic "ASEL"] [1 byte: Type] [1 byte: Flags] [8 bytes: Timestamp µs (Big-Endian)] [4 bytes: Length (Big-Endian)] [Payload]
//

import Foundation

public enum PacketType: UInt8 {
    case videoH264 = 0x01
    case videoH265 = 0x02
    case audioPCM = 0x03
    case codecConfig = 0x04
}

public struct PacketFlags: OptionSet {
    public let rawValue: UInt8
    public init(rawValue: UInt8) {
        self.rawValue = rawValue
    }

    public static let none = PacketFlags([])
    public static let keyframe = PacketFlags(rawValue: 0x01)
}

public enum AselProtocol {
    public static let magic = Data([0x41, 0x53, 0x45, 0x4C]) // "ASEL"
    public static let headerSize = 18

    public static func createPacket(type: PacketType, flags: PacketFlags = .none, timestampUs: UInt64, payload: Data) -> Data {
        var data = Data(capacity: headerSize + payload.count)
        data.append(magic)
        data.append(type.rawValue)
        data.append(flags.rawValue)

        var beTimestamp = timestampUs.bigEndian
        withUnsafeBytes(of: &beTimestamp) { data.append(contentsOf: $0) }

        var beLength = UInt32(payload.count).bigEndian
        withUnsafeBytes(of: &beLength) { data.append(contentsOf: $0) }

        data.append(payload)
        return data
    }
}
