package com.aselens.aselcam.network

import android.os.BatteryManager
import android.os.Build
import android.util.Log
import org.json.JSONArray
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.PrintWriter
import java.net.ServerSocket
import java.net.Socket
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.atomic.AtomicBoolean
import kotlin.concurrent.thread

interface CommandListener {
    fun onGetDeviceInfo(): JSONObject
    fun onSwitchCamera(cameraId: String)
    fun onSetTorch(enabled: Boolean)
    fun onSetZoom(zoom: Float)
    fun onSetConfig(width: Int, height: Int, fps: Int, bitrate: Int, codec: String)
    fun onSetMute(muted: Boolean)
    fun onSetAudioGain(gain: Float)
    fun onSetPreviewEnabled(enabled: Boolean)
    fun onSetCameraEnabled(enabled: Boolean)
    fun onSetBlackout(enabled: Boolean)
    fun onSetScreenMirror(enabled: Boolean)
    fun onStartStream()
    fun onStopStream()
}

class CommandServer(
    private val port: Int = 4748,
    private val listener: CommandListener
) {
    companion object {
        const val DEFAULT_MAX_COMMANDS_PER_SEC = 30
    }

    private val TAG = "AselCam_CommandServer"
    private var serverSocket: ServerSocket? = null
    private val isRunning = AtomicBoolean(false)
    private val clients = CopyOnWriteArrayList<Socket>()

    @Volatile
    var maxCommandsPerSecond: Int = DEFAULT_MAX_COMMANDS_PER_SEC

    fun start() {
        if (isRunning.getAndSet(true)) return

        thread(name = "AselCam-CmdServer") {
            try {
                serverSocket = ServerSocket(port)
                serverSocket?.reuseAddress = true
                Log.i(TAG, "Command server listening on port $port")

                while (isRunning.get()) {
                    val socket = serverSocket?.accept() ?: break
                    clients.add(socket)
                    thread(name = "AselCam-CmdClient-${socket.port}") {
                        handleClient(socket)
                    }
                }
            } catch (e: Exception) {
                if (isRunning.get()) {
                    Log.e(TAG, "Command server error: ${e.message}")
                }
            }
        }
    }

    fun stop() {
        isRunning.set(false)
        try {
            serverSocket?.close()
        } catch (e: Exception) {
            // Ignore
        }
        serverSocket = null
        for (client in clients) {
            try {
                client.close()
            } catch (e: Exception) {}
        }
        clients.clear()
    }

    private fun handleClient(socket: Socket) {
        try {
            socket.tcpNoDelay = true
            val reader = BufferedReader(InputStreamReader(socket.getInputStream()))
            val writer = PrintWriter(socket.getOutputStream(), true)

            var windowStartMs = System.currentTimeMillis()
            var commandsInWindow = 0
            var line: String? = null

            while (isRunning.get() && reader.readLine().also { line = it } != null) {
                val input = line?.trim() ?: continue
                if (input.isEmpty()) continue

                val now = System.currentTimeMillis()
                if (now - windowStartMs >= 1000L) {
                    windowStartMs = now
                    commandsInWindow = 0
                }

                val limit = maxCommandsPerSecond
                if (limit in 1..commandsInWindow) {
                    val rateLimitErr = JSONObject().apply {
                        put("status", "error")
                        put("message", "Rate limit exceeded (max $limit commands/sec)")
                    }
                    writer.println(rateLimitErr.toString())
                    continue
                }
                commandsInWindow++

                val response = processCommand(input)
                writer.println(response)
            }
        } catch (e: Exception) {
            Log.d(TAG, "Command client closed: ${e.message}")
        } finally {
            try {
                socket.close()
            } catch (e: Exception) {}
            clients.remove(socket)
        }
    }

    internal fun processCommand(jsonStr: String): String {
        return try {
            val req = JSONObject(jsonStr)
            val cmd = req.optString("cmd")

            val res = JSONObject()
            res.put("reply_to", cmd)

            when (cmd) {
                "get_info" -> {
                    val info = listener.onGetDeviceInfo()
                    res.put("status", "ok")
                    res.put("data", info)
                }
                "switch_camera" -> {
                    val camId = req.getString("camera_id")
                    listener.onSwitchCamera(camId)
                    res.put("status", "ok")
                }
                "set_torch" -> {
                    val enabled = if (req.has("enabled")) (req.optBoolean("enabled", false) || req.optString("enabled").lowercase() == "true" || req.optInt("enabled", 0) == 1) else false
                    listener.onSetTorch(enabled)
                    res.put("status", "ok")
                }
                "set_zoom" -> {
                    val zoom = req.getDouble("zoom").toFloat()
                    listener.onSetZoom(zoom)
                    res.put("status", "ok")
                }
                "set_config" -> {
                    val width = req.getInt("width")
                    val height = req.getInt("height")
                    val fps = req.getInt("fps")
                    val bitrate = req.getInt("bitrate")
                    val codec = req.optString("codec", "h264")
                    listener.onSetConfig(width, height, fps, bitrate, codec)
                    res.put("status", "ok")
                }
                "set_mute" -> {
                    val muted = req.getBoolean("muted")
                    listener.onSetMute(muted)
                    res.put("status", "ok")
                }
                "set_audio_gain" -> {
                    val gain = req.getDouble("gain").toFloat()
                    listener.onSetAudioGain(gain)
                    res.put("status", "ok")
                }
                "set_preview" -> {
                    val enabled = req.getBoolean("enabled")
                    listener.onSetPreviewEnabled(enabled)
                    res.put("status", "ok")
                }
                "set_camera_enabled" -> {
                    val enabled = req.getBoolean("enabled")
                    listener.onSetCameraEnabled(enabled)
                    res.put("status", "ok")
                }
                "blackout" -> {
                    val enabled = req.getBoolean("enabled")
                    listener.onSetBlackout(enabled)
                    res.put("status", "ok")
                }
                "set_screen_mirror" -> {
                    val enabled = req.getBoolean("enabled")
                    listener.onSetScreenMirror(enabled)
                    res.put("status", "ok")
                }
                "start_stream" -> {
                    listener.onStartStream()
                    res.put("status", "ok")
                }
                "stop_stream" -> {
                    listener.onStopStream()
                    res.put("status", "ok")
                }
                "set_rate_limit" -> {
                    val limit = req.getInt("limit")
                    if (limit in 1..500) {
                        maxCommandsPerSecond = limit
                        res.put("status", "ok")
                        res.put("limit", limit)
                    } else {
                        res.put("status", "error")
                        res.put("message", "Limit must be between 1 and 500")
                    }
                }
                "get_rate_limit" -> {
                    res.put("status", "ok")
                    res.put("limit", maxCommandsPerSecond)
                }
                "ping" -> {
                    res.put("status", "pong")
                    res.put("timestamp", System.currentTimeMillis())
                }
                else -> {
                    res.put("status", "error")
                    res.put("message", "Unknown command: $cmd")
                }
            }
            res.toString()
        } catch (e: Exception) {
            val err = JSONObject()
            err.put("status", "error")
            err.put("message", e.message)
            err.toString()
        }
    }
}
