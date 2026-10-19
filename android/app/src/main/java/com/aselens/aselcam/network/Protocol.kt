package com.aselens.aselcam.network

import java.io.ByteArrayOutputStream
import java.io.DataOutputStream
import java.nio.ByteBuffer

object Protocol {
    val MAGIC = byteArrayOf(0x41.toByte(), 0x53.toByte(), 0x45.toByte(), 0x4C.toByte()) // "ASEL"

    const val TYPE_VIDEO_H264: Byte = 0x01
    const val TYPE_VIDEO_H265: Byte = 0x02
    const val TYPE_AUDIO_PCM: Byte = 0x03
    const val TYPE_CODEC_CONFIG: Byte = 0x04

    const val FLAG_KEYFRAME: Byte = 0x01
    const val FLAG_NONE: Byte = 0x00

    const val HEADER_SIZE = 18 // 4 (magic) + 1 (type) + 1 (flags) + 8 (ts) + 4 (length)

    fun createPacket(type: Byte, flags: Byte, timestampUs: Long, payload: ByteArray): ByteArray {
        val buffer = ByteBuffer.allocate(HEADER_SIZE + payload.size)
        buffer.put(MAGIC)
        buffer.put(type)
        buffer.put(flags)
        buffer.putLong(timestampUs)
        buffer.putInt(payload.size)
        buffer.put(payload)
        return buffer.array()
    }
}
