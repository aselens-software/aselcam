package com.aselens.aselcam.network

import android.util.Log
import java.io.OutputStream
import java.net.ServerSocket
import java.net.Socket
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.LinkedBlockingQueue
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicLong
import kotlin.concurrent.thread

class StreamServer(private val port: Int = 4747) {

    private val TAG = "AselCam_StreamServer"
    private var serverSocket: ServerSocket? = null
    private val isRunning = AtomicBoolean(false)
    private val clients = CopyOnWriteArrayList<ClientHandler>()

    // Latest SPS/PPS codec configuration packet and IDR keyframe to send to newly connected clients immediately
    @Volatile
    private var latestConfigPacket: ByteArray? = null

    @Volatile
    private var latestKeyframePacket: ByteArray? = null

    var onClientConnected: (() -> Unit)? = null
    var onNeedKeyFrame: (() -> Unit)? = null

    // Real-time telemetry
    val clientCount = AtomicInteger(0)
    val currentFps = AtomicInteger(0)
    val currentBitrateBps = AtomicLong(0)

    private var framesSentCount = 0
    private var bytesSentCount = 0L
    private var lastStatsTime = System.currentTimeMillis()

    fun start() {
        if (isRunning.getAndSet(true)) return

        thread(name = "AselCam-StreamServer-Acceptor") {
            try {
                serverSocket = ServerSocket(port)
                serverSocket?.reuseAddress = true
                Log.i(TAG, "Stream server listening on port $port")

                while (isRunning.get()) {
                    val socket = serverSocket?.accept() ?: break
                    socket.tcpNoDelay = true
                    socket.sendBufferSize = 128 * 1024 // Low-latency 128 KB send buffer

                    Log.i(TAG, "New client connected from ${socket.remoteSocketAddress}")
                    val handler = ClientHandler(socket)

                    // Enqueue cached codec config and latest keyframe BEFORE adding to broadcast list
                    // so the client guaranteed receives SPS/PPS + IDR as the very first packets.
                    latestConfigPacket?.let { cfg ->
                        handler.enqueuePacket(cfg, isKeyframe = true)
                    }
                    latestKeyframePacket?.let { kf ->
                        handler.enqueuePacket(kf, isKeyframe = true)
                    }

                    clients.add(handler)
                    clientCount.incrementAndGet()
                    handler.start()

                    try {
                        onClientConnected?.invoke()
                    } catch (e: Exception) {
                        Log.w(TAG, "onClientConnected callback error: ${e.message}")
                    }
                }
            } catch (e: Exception) {
                if (isRunning.get()) {
                    Log.e(TAG, "Server socket error: ${e.message}")
                }
            }
        }
    }

    fun clearQueues() {
        for (client in clients) {
            client.clearPending()
        }
    }

    fun stop() {
        isRunning.set(false)
        try {
            serverSocket?.close()
        } catch (e: Exception) {
            e.printStackTrace()
        }
        serverSocket = null

        for (client in clients) {
            client.close()
        }
        clients.clear()
        clientCount.set(0)
        currentFps.set(0)
        currentBitrateBps.set(0)
        Log.i(TAG, "Stream server stopped")
    }

    fun setCodecConfig(configPacket: ByteArray) {
        latestConfigPacket = configPacket
        latestKeyframePacket = null
        clearQueues()
        broadcastPacket(configPacket, isKeyframe = true)
    }

    fun sendVideoFrame(packet: ByteArray, isKeyframe: Boolean) {
        if (isKeyframe) {
            latestKeyframePacket = packet
        }

        // Telemetry update (always track encoder output rate)
        synchronized(this) {
            framesSentCount++
            bytesSentCount += packet.size
            val now = System.currentTimeMillis()
            val elapsed = now - lastStatsTime
            if (elapsed >= 1000) {
                currentFps.set((framesSentCount * 1000L / elapsed).toInt())
                currentBitrateBps.set((bytesSentCount * 8000L / elapsed))
                framesSentCount = 0
                bytesSentCount = 0L
                lastStatsTime = now
            }
        }

        if (clients.isEmpty()) return
        broadcastPacket(packet, isKeyframe = isKeyframe)
    }

    fun sendAudioPacket(packet: ByteArray) {
        if (clients.isEmpty()) return
        broadcastPacket(packet, isKeyframe = false)
    }

    private fun broadcastPacket(packet: ByteArray, isKeyframe: Boolean) {
        val deadClients = mutableListOf<ClientHandler>()
        for (client in clients) {
            if (!client.enqueuePacket(packet, isKeyframe)) {
                deadClients.add(client)
            }
        }

        if (deadClients.isNotEmpty()) {
            for (dead in deadClients) {
                dead.close()
                clients.remove(dead)
                clientCount.set(clients.size)
            }
        }
    }

    inner class ClientHandler(private val socket: Socket) {
        private val outputQueue = LinkedBlockingQueue<ByteArray>(16) // Ultra-low latency queue (max 16 packets)
        private val isClientRunning = AtomicBoolean(true)
        private var workerThread: Thread? = null

        fun start() {
            workerThread = thread(name = "AselCam-Client-${socket.port}") {
                var outputStream: OutputStream? = null
                try {
                    outputStream = socket.getOutputStream()
                    while (isClientRunning.get() && isRunning.get()) {
                        val packet = outputQueue.take()
                        outputStream.write(packet)
                        if (outputQueue.isEmpty()) {
                            outputStream.flush()
                        }
                    }
                } catch (e: Exception) {
                    Log.d(TAG, "Client disconnected: ${socket.remoteSocketAddress} (${e.message})")
                } finally {
                    close()
                    clients.remove(this)
                    clientCount.set(clients.size)
                }
            }
        }

        @Synchronized
        fun clearPending() {
            outputQueue.clear()
        }

        @Synchronized
        fun enqueuePacket(packet: ByteArray, isKeyframe: Boolean): Boolean {
            if (!isClientRunning.get()) return false

            if (isKeyframe) {
                // When a new keyframe arrives, if old P-frames are backed up (>3 packets),
                // drop stale backlog so latency immediately snaps back to 0ms!
                if (outputQueue.size > 3) {
                    outputQueue.clear()
                    latestConfigPacket?.let { cfg ->
                        if (cfg !== packet) outputQueue.offer(cfg)
                    }
                }
                outputQueue.offer(packet)
                return true
            }

            // If queue is full on a non-keyframe, flush stale backlog and request an immediate IDR frame
            if (outputQueue.remainingCapacity() == 0) {
                outputQueue.clear()
                latestConfigPacket?.let { cfg -> outputQueue.offer(cfg) }
                try {
                    onNeedKeyFrame?.invoke()
                } catch (_: Exception) {}
                return true
            }
            outputQueue.offer(packet)
            return isClientRunning.get()
        }

        fun close() {
            if (isClientRunning.getAndSet(false)) {
                try {
                    socket.close()
                } catch (e: Exception) {
                    // Ignore
                }
                outputQueue.clear()
                workerThread?.interrupt()
            }
        }
    }
}
