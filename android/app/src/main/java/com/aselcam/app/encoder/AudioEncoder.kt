package com.aselcam.app.encoder

import android.annotation.SuppressLint
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.media.audiofx.AcousticEchoCanceler
import android.media.audiofx.NoiseSuppressor
import android.util.Log
import com.aselcam.app.network.Protocol
import com.aselcam.app.network.StreamServer
import java.util.concurrent.atomic.AtomicBoolean
import kotlin.concurrent.thread

class AudioEncoder(
    private val streamServer: StreamServer
) {
    private val TAG = "AselCam_AudioEncoder"

    private var audioRecord: AudioRecord? = null
    private var echoCanceler: AcousticEchoCanceler? = null
    private var noiseSuppressor: NoiseSuppressor? = null

    private val isRunning = AtomicBoolean(false)
    private var recordThread: Thread? = null

    @Volatile
    var isMuted: Boolean = false
        private set

    @Volatile
    var gain: Float = 1.0f

    val sampleRate = 24000
    val channelConfig = AudioFormat.CHANNEL_IN_MONO
    val audioFormat = AudioFormat.ENCODING_PCM_16BIT

    @Synchronized
    fun setMuted(muted: Boolean, shouldBeRunning: Boolean) {
        isMuted = muted
        if (muted) {
            stop()
            Log.i(TAG, "Microphone muted -> AudioRecord hardware stopped & released")
        } else if (shouldBeRunning) {
            start()
            Log.i(TAG, "Microphone unmuted -> AudioRecord hardware started")
        }
    }

    @SuppressLint("MissingPermission")
    @Synchronized
    fun start() {
        if (isMuted) {
            Log.i(TAG, "Microphone is muted, skipping AudioRecord start")
            return
        }
        if (isRunning.getAndSet(true)) return

        val minBufferSize = AudioRecord.getMinBufferSize(sampleRate, channelConfig, audioFormat)
        val bufferSize = Math.max(minBufferSize, 2048)

        try {
            val record = AudioRecord(
                MediaRecorder.AudioSource.VOICE_COMMUNICATION,
                sampleRate,
                channelConfig,
                audioFormat,
                bufferSize
            )

            if (record.state != AudioRecord.STATE_INITIALIZED) {
                Log.e(TAG, "AudioRecord failed to initialize")
                isRunning.set(false)
                return
            }

            // Attach hardware acoustic effects if supported
            val audioSessionId = record.audioSessionId
            if (AcousticEchoCanceler.isAvailable()) {
                try {
                    echoCanceler = AcousticEchoCanceler.create(audioSessionId)?.apply {
                        enabled = true
                    }
                } catch (e: Exception) {}
            }
            if (NoiseSuppressor.isAvailable()) {
                try {
                    noiseSuppressor = NoiseSuppressor.create(audioSessionId)?.apply {
                        enabled = true
                    }
                } catch (e: Exception) {}
            }

            record.startRecording()
            audioRecord = record

            recordThread = thread(name = "AselCam-AudioRecord") {
                val audioBuffer = ShortArray(960) // 40ms per chunk at 24kHz mono (25 packets/sec)
                val byteBuffer = ByteArray(audioBuffer.size * 2)

                while (isRunning.get() && !isMuted) {
                    val readSamples = record.read(audioBuffer, 0, audioBuffer.size)
                    if (readSamples > 0) {
                        if (streamServer.clientCount.get() <= 0) {
                            continue
                        }
                        val currentGain = gain
                        val timeUs = System.nanoTime() / 1000L

                        var byteIdx = 0
                        for (i in 0 until readSamples) {
                            var sample = audioBuffer[i]
                            if (currentGain != 1.0f) {
                                val amplified = (sample * currentGain).toInt()
                                sample = amplified.coerceIn(Short.MIN_VALUE.toInt(), Short.MAX_VALUE.toInt()).toShort()
                            }

                            byteBuffer[byteIdx++] = (sample.toInt() and 0xFF).toByte()
                            byteBuffer[byteIdx++] = ((sample.toInt() shr 8) and 0xFF).toByte()
                        }

                        val payload = byteBuffer.copyOf(byteIdx)
                        val packet = Protocol.createPacket(
                            Protocol.TYPE_AUDIO_PCM,
                            Protocol.FLAG_NONE,
                            timeUs,
                            payload
                        )
                        streamServer.sendAudioPacket(packet)
                    }
                }
            }
            Log.i(TAG, "Audio encoder started at $sampleRate Hz (Mono)")
        } catch (e: Exception) {
            Log.e(TAG, "Audio start error: ${e.message}")
            isRunning.set(false)
        }
    }

    @Synchronized
    fun stop() {
        if (!isRunning.getAndSet(false)) return

        try {
            audioRecord?.stop()
        } catch (e: Exception) {}

        try {
            recordThread?.interrupt()
            recordThread?.join(400)
        } catch (e: Exception) {}
        recordThread = null

        try {
            audioRecord?.release()
        } catch (e: Exception) {}
        audioRecord = null

        try {
            echoCanceler?.release()
            noiseSuppressor?.release()
        } catch (e: Exception) {}
        echoCanceler = null
        noiseSuppressor = null
        Log.i(TAG, "Audio encoder stopped")
    }
}
