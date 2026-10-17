package com.aselcam.app.encoder

import android.media.MediaCodec
import android.media.MediaCodecInfo
import android.media.MediaFormat
import android.os.Bundle
import android.util.Log
import android.view.Surface
import com.aselcam.app.network.Protocol
import com.aselcam.app.network.StreamServer
import java.nio.ByteBuffer
import java.util.concurrent.atomic.AtomicBoolean
import kotlin.concurrent.thread

class VideoEncoder(
    private val streamServer: StreamServer
) {
    private val TAG = "AselCam_VideoEncoder"

    private var mediaCodec: MediaCodec? = null
    private var inputSurface: Surface? = null
    private val isRunning = AtomicBoolean(false)
    private var drainThread: Thread? = null

    var currentWidth: Int = 1920
        private set
    var currentHeight: Int = 1080
        private set
    var currentFps: Int = 30
        private set
    var currentBitrate: Int = 4_000_000
        private set
    var currentCodec: String = "h264"
        private set

    @Volatile
    private var codecConfigBytes: ByteArray? = null

    fun getInputSurface(): Surface? = inputSurface
    fun isRunning(): Boolean = isRunning.get()

    @Synchronized
    fun start(
        width: Int = 1920,
        height: Int = 1080,
        fps: Int = 30,
        bitrate: Int = 4_000_000,
        codec: String = "h264"
    ): Surface {
        stop()

        val requestedCodec = codec.lowercase()
        val primaryMime = if (requestedCodec == "hevc" || requestedCodec == "h265") {
            MediaFormat.MIMETYPE_VIDEO_HEVC
        } else {
            MediaFormat.MIMETYPE_VIDEO_AVC
        }

        // Candidate configurations in order of preference (preserving aspect ratio)
        val alignedW = (width / 16) * 16
        val alignedH = (height / 16) * 16
        val isPortrait = height > width
        val isSquare = width == height
        val candidates = mutableListOf(
            Triple(width, height, primaryMime),
            Triple(if (alignedW >= 320) alignedW else 640, if (alignedH >= 240) alignedH else 480, primaryMime)
        ).apply {
            if (isSquare) {
                add(Triple(1080, 1080, primaryMime))
                add(Triple(720, 720, primaryMime))
                add(Triple(720, 720, MediaFormat.MIMETYPE_VIDEO_AVC))
            } else if (isPortrait) {
                val aspect = width.toFloat() / height.toFloat()
                if (aspect > 0.65f) {
                    // 3:4 Portrait fallbacks
                    add(Triple(720, 960, primaryMime))
                    add(Triple(720, 960, MediaFormat.MIMETYPE_VIDEO_AVC))
                } else {
                    // 9:16 Portrait fallbacks (including 608x1080 for encoders with maxHeight=1088)
                    add(Triple(720, 1280, primaryMime))
                    add(Triple(720, 1280, MediaFormat.MIMETYPE_VIDEO_AVC))
                    add(Triple(608, 1080, MediaFormat.MIMETYPE_VIDEO_AVC))
                }
            } else {
                val aspect = width.toFloat() / height.toFloat()
                if (aspect < 1.5f) {
                    // 4:3 Landscape fallbacks
                    add(Triple(1440, 1080, MediaFormat.MIMETYPE_VIDEO_AVC))
                    add(Triple(960, 720, MediaFormat.MIMETYPE_VIDEO_AVC))
                }
                add(Triple(1920, 1080, MediaFormat.MIMETYPE_VIDEO_AVC))
                add(Triple(1280, 720, MediaFormat.MIMETYPE_VIDEO_AVC))
            }
        }.distinct()

        var configuredEncoder: MediaCodec? = null
        var configuredSurface: Surface? = null
        var activeMime = primaryMime

        for ((candW, candH, candMime) in candidates) {
            // Stage A: Try low-latency configuration
            val lowLatencyFormat = createMediaFormat(candMime, candW, candH, fps, bitrate, lowLatency = true)
            val resultA = tryConfigureEncoder(candMime, lowLatencyFormat)
            if (resultA != null) {
                configuredEncoder = resultA.first
                configuredSurface = resultA.second
                currentWidth = candW
                currentHeight = candH
                activeMime = candMime
                break
            }

            // Stage B: Try baseline standard configuration (without optional keys that some SoCs reject)
            val baselineFormat = createMediaFormat(candMime, candW, candH, fps, bitrate, lowLatency = false)
            val resultB = tryConfigureEncoder(candMime, baselineFormat)
            if (resultB != null) {
                configuredEncoder = resultB.first
                configuredSurface = resultB.second
                currentWidth = candW
                currentHeight = candH
                activeMime = candMime
                break
            }
        }

        if (configuredEncoder == null || configuredSurface == null) {
            throw IllegalStateException("Failed to configure MediaCodec for any candidate resolution")
        }

        currentFps = fps
        currentBitrate = bitrate
        currentCodec = if (activeMime == MediaFormat.MIMETYPE_VIDEO_HEVC) "hevc" else "h264"
        codecConfigBytes = null

        mediaCodec = configuredEncoder
        inputSurface = configuredSurface
        isRunning.set(true)

        Log.i(TAG, "MediaCodec started: ${currentWidth}x${currentHeight} @ $currentFps fps, $currentBitrate bps ($activeMime)")

        drainThread = thread(name = "AselCam-VideoDrain") {
            drainEncoder(configuredEncoder, activeMime)
        }

        return configuredSurface
    }

    private fun createMediaFormat(
        mimeType: String,
        width: Int,
        height: Int,
        fps: Int,
        bitrate: Int,
        lowLatency: Boolean
    ): MediaFormat {
        return MediaFormat.createVideoFormat(mimeType, width, height).apply {
            setInteger(MediaFormat.KEY_COLOR_FORMAT, MediaCodecInfo.CodecCapabilities.COLOR_FormatSurface)
            setInteger(MediaFormat.KEY_BIT_RATE, bitrate)
            setInteger(MediaFormat.KEY_FRAME_RATE, fps)
            setInteger(MediaFormat.KEY_I_FRAME_INTERVAL, 1) // 1 second keyframe interval for rapid sync
            // Ensures frames are continuously produced even when the screen is static (Screen Mirroring)
            setLong(MediaFormat.KEY_REPEAT_PREVIOUS_FRAME_AFTER, (1_000_000L / fps.coerceAtLeast(15)).toLong())
            if (lowLatency) {
                setInteger(MediaFormat.KEY_BITRATE_MODE, MediaCodecInfo.EncoderCapabilities.BITRATE_MODE_VBR)
                setInteger(MediaFormat.KEY_LATENCY, 0)
                setInteger(MediaFormat.KEY_PRIORITY, 0)
            }
        }
    }

    private fun tryConfigureEncoder(mimeType: String, format: MediaFormat): Pair<MediaCodec, Surface>? {
        var encoder: MediaCodec? = null
        return try {
            encoder = MediaCodec.createEncoderByType(mimeType)
            encoder.configure(format, null, null, MediaCodec.CONFIGURE_FLAG_ENCODE)
            val surface = encoder.createInputSurface()
            encoder.start()
            Pair(encoder, surface)
        } catch (e: Exception) {
            Log.w(TAG, "MediaCodec configure attempt failed ($format): ${e.message}")
            try {
                encoder?.release()
            } catch (_: Exception) {}
            null
        }
    }

    private fun extractCsdFromFormat(format: MediaFormat): ByteArray? {
        return try {
            val csd0 = format.getByteBuffer("csd-0")
            val csd1 = format.getByteBuffer("csd-1")
            val chunks = mutableListOf<ByteArray>()
            if (csd0 != null && csd0.remaining() > 0) {
                val b0 = ByteArray(csd0.remaining())
                csd0.duplicate().get(b0)
                chunks.add(ensureAnnexB(b0))
            }
            if (csd1 != null && csd1.remaining() > 0) {
                val b1 = ByteArray(csd1.remaining())
                csd1.duplicate().get(b1)
                chunks.add(ensureAnnexB(b1))
            }
            if (chunks.isEmpty()) null else chunks.reduce { acc, bytes -> acc + bytes }
        } catch (e: Exception) {
            null
        }
    }

    private fun drainEncoder(encoder: MediaCodec, mimeType: String) {
        val bufferInfo = MediaCodec.BufferInfo()
        val isHevc = mimeType == MediaFormat.MIMETYPE_VIDEO_HEVC
        val videoType = if (isHevc) Protocol.TYPE_VIDEO_H265 else Protocol.TYPE_VIDEO_H264

        while (isRunning.get()) {
            try {
                val outputBufferIndex = encoder.dequeueOutputBuffer(bufferInfo, 15_000) // 15ms timeout
                if (outputBufferIndex == MediaCodec.INFO_OUTPUT_FORMAT_CHANGED) {
                    val csd = extractCsdFromFormat(encoder.outputFormat)
                    if (csd != null && csd.isNotEmpty()) {
                        codecConfigBytes = csd
                        val configPacket = Protocol.createPacket(
                            Protocol.TYPE_CODEC_CONFIG,
                            Protocol.FLAG_KEYFRAME,
                            System.nanoTime() / 1000L,
                            csd
                        )
                        streamServer.setCodecConfig(configPacket)
                    }
                } else if (outputBufferIndex >= 0) {
                    val isConfig = (bufferInfo.flags and MediaCodec.BUFFER_FLAG_CODEC_CONFIG) != 0
                    val hasClients = streamServer.clientCount.get() > 0
                    val outputBuffer = encoder.getOutputBuffer(outputBufferIndex)
                    if (outputBuffer != null && bufferInfo.size > 0 && (isConfig || hasClients)) {
                        outputBuffer.position(bufferInfo.offset)
                        outputBuffer.limit(bufferInfo.offset + bufferInfo.size)

                        val rawPayload = ByteArray(bufferInfo.size)
                        outputBuffer.get(rawPayload)
                        val payload = ensureAnnexB(rawPayload)

                        val isKeyframe = (bufferInfo.flags and MediaCodec.BUFFER_FLAG_KEY_FRAME) != 0

                        if (isConfig) {
                            codecConfigBytes = payload
                            val configPacket = Protocol.createPacket(
                                Protocol.TYPE_CODEC_CONFIG,
                                Protocol.FLAG_KEYFRAME,
                                bufferInfo.presentationTimeUs,
                                payload
                            )
                            streamServer.setCodecConfig(configPacket)
                        } else if (hasClients) {
                            // Prepend cached SPS/PPS to every keyframe so each keyframe is self-contained
                            val cfg = codecConfigBytes
                            val framePayload = if (isKeyframe && cfg != null) {
                                cfg + payload
                            } else {
                                payload
                            }
                            val packet = Protocol.createPacket(
                                videoType,
                                if (isKeyframe) Protocol.FLAG_KEYFRAME else Protocol.FLAG_NONE,
                                bufferInfo.presentationTimeUs,
                                framePayload
                            )
                            streamServer.sendVideoFrame(packet, isKeyframe = isKeyframe)
                        }
                    }
                    encoder.releaseOutputBuffer(outputBufferIndex, false)
                }
            } catch (e: Exception) {
                if (isRunning.get()) {
                    Log.e(TAG, "Drain error: ${e.message}")
                }
                break
            }
        }
    }

    private fun ensureAnnexB(bytes: ByteArray): ByteArray {
        if (bytes.size >= 4 && bytes[0] == 0.toByte() && bytes[1] == 0.toByte() && bytes[2] == 0.toByte() && bytes[3] == 1.toByte()) {
            return bytes
        }
        if (bytes.size >= 3 && bytes[0] == 0.toByte() && bytes[1] == 0.toByte() && bytes[2] == 1.toByte()) {
            return bytes
        }
        val out = ByteArray(bytes.size + 4)
        out[0] = 0
        out[1] = 0
        out[2] = 0
        out[3] = 1
        System.arraycopy(bytes, 0, out, 4, bytes.size)
        return out
    }

    fun requestKeyFrame() {
        try {
            val params = Bundle().apply {
                putInt(MediaCodec.PARAMETER_KEY_REQUEST_SYNC_FRAME, 0)
            }
            mediaCodec?.setParameters(params)
            Log.d(TAG, "Requested sync keyframe from encoder")
        } catch (e: Exception) {
            Log.w(TAG, "Failed to request sync keyframe: ${e.message}")
        }
    }

    @Synchronized
    fun setBitrate(newBitrate: Int) {
        currentBitrate = newBitrate
        try {
            val params = Bundle().apply {
                putInt(MediaCodec.PARAMETER_KEY_VIDEO_BITRATE, newBitrate)
            }
            mediaCodec?.setParameters(params)
            Log.i(TAG, "Updated encoder bitrate dynamically to $newBitrate bps")
        } catch (e: Exception) {
            Log.w(TAG, "Failed to update bitrate dynamically: ${e.message}")
        }
    }

    @Synchronized
    fun stop() {
        if (!isRunning.getAndSet(false)) return

        try {
            drainThread?.interrupt()
            drainThread?.join(500)
        } catch (e: Exception) {}
        drainThread = null

        try {
            mediaCodec?.stop()
        } catch (e: Exception) {}
        try {
            mediaCodec?.release()
        } catch (e: Exception) {}
        mediaCodec = null

        try {
            inputSurface?.release()
        } catch (e: Exception) {}
        inputSurface = null
        codecConfigBytes = null
        Log.i(TAG, "Video encoder stopped")
    }
}
