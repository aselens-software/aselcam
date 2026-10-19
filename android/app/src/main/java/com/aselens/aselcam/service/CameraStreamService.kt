package com.aselens.aselcam.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.net.wifi.WifiManager
import android.os.BatteryManager
import android.os.Binder
import android.os.Build
import android.os.IBinder
import android.os.PowerManager
import android.util.Log
import android.util.Size
import android.view.OrientationEventListener
import android.view.Surface
import androidx.core.app.NotificationCompat
import com.aselens.aselcam.MainActivity
import com.aselens.aselcam.R
import com.aselens.aselcam.camera.CameraManagerHelper
import com.aselens.aselcam.camera.CameraSession
import com.aselens.aselcam.encoder.AudioEncoder
import com.aselens.aselcam.encoder.EglVideoPipeline
import com.aselens.aselcam.encoder.VideoEncoder
import com.aselens.aselcam.network.CommandListener
import com.aselens.aselcam.network.CommandServer
import com.aselens.aselcam.network.StreamServer
import com.aselens.aselcam.screen.ScreenMirrorManager
import com.aselens.aselcam.ui.BlackoutActivity
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import org.json.JSONArray
import org.json.JSONObject

class CameraStreamService : Service(), CommandListener {

    private val TAG = "AselCam_Service"
    private val NOTIFICATION_ID = 47471
    private val CHANNEL_ID = "aselcam_stream_channel"

    private val binder = LocalBinder()

    private var wakeLock: PowerManager.WakeLock? = null
    private var wifiLock: WifiManager.WifiLock? = null
    private var orientationListener: OrientationEventListener? = null

    lateinit var streamServer: StreamServer
        private set
    lateinit var commandServer: CommandServer
        private set
    lateinit var videoEncoder: VideoEncoder
        private set
    lateinit var audioEncoder: AudioEncoder
        private set
    lateinit var cameraSession: CameraSession
        private set
    lateinit var eglPipeline: EglVideoPipeline
        private set
    lateinit var screenMirrorManager: ScreenMirrorManager
        private set

    private val _isStreaming = MutableStateFlow(false)
    val isStreaming: StateFlow<Boolean> = _isStreaming

    private val pipelineLock = Any()

    @Volatile
    var userStoppedManually: Boolean = false

    inner class LocalBinder : Binder() {
        fun getService(): CameraStreamService = this@CameraStreamService
    }

    override fun onBind(intent: Intent?): IBinder = binder

    override fun onCreate() {
        super.onCreate()
        Log.i(TAG, "Creating CameraStreamService")

        streamServer = StreamServer(4747)
        commandServer = CommandServer(4748, this)
        videoEncoder = VideoEncoder(streamServer)
        audioEncoder = AudioEncoder(streamServer)
        cameraSession = CameraSession(this)
        eglPipeline = EglVideoPipeline()
        screenMirrorManager = ScreenMirrorManager(this)

        streamServer.onClientConnected = {
            videoEncoder.requestKeyFrame()
        }
        streamServer.onNeedKeyFrame = {
            videoEncoder.requestKeyFrame()
        }
        eglPipeline.hasActiveClients = { streamServer.clientCount.get() > 0 }

        orientationListener = object : OrientationEventListener(this) {
            override fun onOrientationChanged(orientation: Int) {
                if (orientation == ORIENTATION_UNKNOWN) return
                val current = eglPipeline.deviceOrientationDegrees
                val newOrientation = when {
                    orientation >= 330 || orientation < 30 -> 0
                    orientation in 60..120 -> 90
                    orientation in 150..210 -> 180
                    orientation in 240..300 -> 270
                    else -> current
                }
                if (newOrientation != current) {
                    eglPipeline.deviceOrientationDegrees = newOrientation
                    deviceOrientationGlobal.value = newOrientation
                }
            }
        }
        if (orientationListener?.canDetectOrientation() == true) {
            orientationListener?.enable()
        }

        commandServer.start()
        streamServer.start()
        instance = this
        acquireLocks()
        createNotificationChannel()
    }

    private fun acquireLocks() {
        val powerManager = getSystemService(Context.POWER_SERVICE) as PowerManager
        wakeLock = powerManager.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "AselCam:StreamingWakeLock").apply {
            setReferenceCounted(false)
            acquire(12 * 60 * 60 * 1000L) // 12 hours max
        }

        val wifiManager = applicationContext.getSystemService(Context.WIFI_SERVICE) as WifiManager
        wifiLock = wifiManager.createWifiLock(WifiManager.WIFI_MODE_FULL_HIGH_PERF, "AselCam:StreamingWifiLock").apply {
            setReferenceCounted(false)
            acquire()
        }
    }

    private fun releaseLocks() {
        try {
            if (wakeLock?.isHeld == true) wakeLock?.release()
        } catch (e: Exception) {}
        wakeLock = null

        try {
            if (wifiLock?.isHeld == true) wifiLock?.release()
        } catch (e: Exception) {}
        wifiLock = null
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                getString(R.string.channel_name),
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = getString(R.string.channel_desc)
                setShowBadge(false)
            }
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(channel)
        }
    }

    private fun buildNotification(): Notification {
        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_SINGLE_TOP
        }
        val pendingIntent = PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val stopIntent = Intent(this, CameraStreamService::class.java).apply {
            action = ACTION_STOP
        }
        val stopPendingIntent = PendingIntent.getService(
            this, 1, stopIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("AselCam Canlı Akış")
            .setContentText("Kamera ve mikrofon yayında (4747 / 4748)")
            .setSmallIcon(R.drawable.ic_launcher)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .addAction(R.drawable.ic_launcher, getString(R.string.stop_service), stopPendingIntent)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACTION_STOP) {
            userStoppedManually = true
            stopStreaming()
            stopSelf()
            return START_NOT_STICKY
        }
        return START_STICKY
    }

    fun startStreaming(
        cameraId: String = "0",
        width: Int = 1920,
        height: Int = 1080,
        fps: Int = 30,
        bitrate: Int = 4_000_000,
        codec: String = "h264",
        previewSurface: Surface? = null
    ) {
        synchronized(pipelineLock) {
            if (_isStreaming.value) return
        userStoppedManually = false

        Log.i(TAG, "Starting streaming: cam=$cameraId, ${width}x${height} @ ${fps}fps, bitrate=$bitrate, cameraEnabled=${isCameraEnabledGlobal.value}")

        try {
            val notification = buildNotification()
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                startForeground(
                    NOTIFICATION_ID,
                    notification,
                    ServiceInfo.FOREGROUND_SERVICE_TYPE_CAMERA or ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE
                )
            } else {
                startForeground(NOTIFICATION_ID, notification)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error starting foreground service: ${e.message}")
        }

        try {
            streamServer.start()
            commandServer.start()

            val cameras = CameraManagerHelper.getAvailableCameras(this)
            val targetCam = cameras.find { it.id == cameraId } ?: cameras.firstOrNull()
            val effectiveCamId = targetCam?.id ?: cameraId

            val activePreview = previewSurface ?: cameraSession.previewSurface
            cameraSession.setPreviewSurface(activePreview)

            if (isCameraEnabledGlobal.value) {
                // Start encoder at the exact requested dimensions & aspect ratio
                val encSurface = videoEncoder.start(width, height, fps, bitrate, codec)
                val actualEncW = videoEncoder.currentWidth
                val actualEncH = videoEncoder.currentHeight

                val sensorRes = if (targetCam != null) {
                    CameraManagerHelper.findBestMatchingResolution(targetCam, actualEncW, actualEncH)
                } else {
                    Size(maxOf(actualEncW, actualEncH), minOf(actualEncW, actualEncH))
                }

                eglPipeline.sensorOrientation = targetCam?.sensorOrientation ?: 90
                eglPipeline.isFacingBack = targetCam?.isFacingBack ?: true
                eglPipeline.isPreviewEnabled = isPreviewGlobal.value

                val glCameraSurface = eglPipeline.start(
                    sensorW = sensorRes.width,
                    sensorH = sensorRes.height,
                    encW = actualEncW,
                    encH = actualEncH,
                    encoderSurface = encSurface,
                    previewSurface = activePreview
                )

                cameraSession.startCamera(
                    cameraId = effectiveCamId,
                    encoderSurface = glCameraSurface,
                    previewSurface = activePreview,
                    targetResolution = sensorRes,
                    targetFps = fps,
                    onOpened = {
                        videoEncoder.requestKeyFrame()
                    }
                )

                currentResolutionGlobal.value = "${actualEncW}x${actualEncH}"
                currentCodecGlobal.value = videoEncoder.currentCodec
            } else {
                Log.i(TAG, "Camera is disabled, skipping video pipeline setup to conserve power")
            }

            if (!isMutedGlobal.value) {
                try {
                    audioEncoder.start()
                } catch (e: Exception) {
                    Log.w(TAG, "AudioEncoder could not start: ${e.message}")
                }
            }

            _isStreaming.value = true
            isStreamingGlobal.value = true
            currentCameraIdGlobal.value = effectiveCamId
            currentFpsGlobal.value = fps
            currentBitrateMbpsGlobal.value = bitrate / 1_000_000f
        } catch (e: Exception) {
            Log.e(TAG, "Failed to start streaming: ${e.message}", e)
            _isStreaming.value = false
            isStreamingGlobal.value = false
        }
    }
}

    fun stopStreaming() {
        synchronized(pipelineLock) {
            if (!_isStreaming.value) return
            Log.i(TAG, "Stopping streaming")

            cameraSession.stopCamera()
            eglPipeline.stop()
            screenMirrorManager.stop()
            videoEncoder.stop()
            audioEncoder.stop()

            _isStreaming.value = false
            isStreamingGlobal.value = false
            isScreenMirroringGlobal.value = false
            try {
                stopForeground(STOP_FOREGROUND_REMOVE)
            } catch (e: Exception) {}
        }
    }

    fun setPreviewSurface(surface: Surface?) = synchronized(pipelineLock) {
        cameraSession.setPreviewSurface(surface)
        eglPipeline.setPreviewSurface(surface)
    }

    override fun onDestroy() {
        try {
            orientationListener?.disable()
        } catch (_: Exception) {}
        orientationListener = null
        stopStreaming()
        streamServer.stop()
        commandServer.stop()
        releaseLocks()
        if (instance === this) {
            instance = null
        }
        super.onDestroy()
        Log.i(TAG, "CameraStreamService destroyed")
    }

    // CommandListener implementations (Remote PC control)

    override fun onGetDeviceInfo(): JSONObject {
        val root = JSONObject()
        root.put("device_model", "${Build.MANUFACTURER} ${Build.MODEL}")
        root.put("android_version", Build.VERSION.RELEASE)

        // Battery
        val batteryManager = getSystemService(Context.BATTERY_SERVICE) as BatteryManager
        val batteryLevel = batteryManager.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
        root.put("battery_level", batteryLevel)

        // Active telemetry
        root.put("fps", streamServer.currentFps.get())
        root.put("bitrate_bps", streamServer.currentBitrateBps.get())
        root.put("clients", streamServer.clientCount.get())
        root.put("is_streaming", _isStreaming.value)
        root.put("current_camera", cameraSession.currentCameraId)
        root.put("current_width", videoEncoder.currentWidth)
        root.put("current_height", videoEncoder.currentHeight)
        root.put("current_fps", videoEncoder.currentFps)
        root.put("current_bitrate", videoEncoder.currentBitrate)
        root.put("current_codec", videoEncoder.currentCodec)
        root.put("is_muted", audioEncoder.isMuted)
        root.put("audio_gain", audioEncoder.gain)
        root.put("is_camera_enabled", isCameraEnabledGlobal.value)
        root.put("preview_enabled", cameraSession.isPreviewEnabled)
        root.put("torch_enabled", cameraSession.isTorchEnabled)
        root.put("zoom", cameraSession.currentZoom)
        root.put("max_zoom", cameraSession.maxZoom)
        root.put("blackout_enabled", isBlackoutGlobal.value)
        root.put("device_orientation", eglPipeline.deviceOrientationDegrees)
        root.put("is_screen_mirroring", isScreenMirroringGlobal.value)

        // Cameras list
        val cameras = CameraManagerHelper.getAvailableCameras(this)
        val camsArray = JSONArray()
        for (cam in cameras) {
            val cObj = JSONObject()
            cObj.put("id", cam.id)
            cObj.put("name", cam.name)
            cObj.put("is_back", cam.isFacingBack)
            cObj.put("max_zoom", cam.maxZoom)
            cObj.put("has_flash", cam.hasFlash)

            val resArray = JSONArray()
            for (res in cam.supportedResolutions) {
                resArray.put("${res.width}x${res.height}")
            }
            cObj.put("resolutions", resArray)

            val fpsArray = JSONArray()
            for (fps in cam.supportedFpsRanges) {
                fpsArray.put("[${fps.lower}, ${fps.upper}]")
            }
            cObj.put("fps_ranges", fpsArray)
            camsArray.put(cObj)
        }
        root.put("cameras", camsArray)

        return root
    }

    override fun onSwitchCamera(cameraId: String) = synchronized(pipelineLock) {
        currentCameraIdGlobal.value = cameraId
        if (!_isStreaming.value) {
            startStreaming(
                cameraId = cameraId,
                width = videoEncoder.currentWidth,
                height = videoEncoder.currentHeight,
                fps = videoEncoder.currentFps,
                bitrate = videoEncoder.currentBitrate,
                codec = videoEncoder.currentCodec,
                previewSurface = cameraSession.previewSurface
            )
            return@synchronized
        }

        val glCameraSurface = eglPipeline.cameraSurface ?: return@synchronized
        val cameras = CameraManagerHelper.getAvailableCameras(this)
        val targetCam = cameras.find { it.id == cameraId } ?: return@synchronized
        if (!targetCam.hasFlash) {
            isTorchGlobal.value = false
        }
        val sensorRes = CameraManagerHelper.findBestMatchingResolution(
            targetCam,
            videoEncoder.currentWidth,
            videoEncoder.currentHeight
        )
        val bestFps = CameraManagerHelper.findBestFpsRange(targetCam, videoEncoder.currentFps).upper

        streamServer.clearQueues()
        eglPipeline.updateCameraBufferSize(
            sensorW = sensorRes.width,
            sensorH = sensorRes.height,
            orientation = targetCam.sensorOrientation,
            facingBack = targetCam.isFacingBack
        )

        cameraSession.startCamera(
            cameraId = cameraId,
            encoderSurface = glCameraSurface,
            previewSurface = cameraSession.previewSurface,
            targetResolution = sensorRes,
            targetFps = bestFps,
            onOpened = {
                videoEncoder.requestKeyFrame()
            }
        )
    }

    override fun onSetTorch(enabled: Boolean) = synchronized(pipelineLock) {
        cameraSession.setTorch(enabled)
        isTorchGlobal.value = enabled
    }

    override fun onSetZoom(zoom: Float) = synchronized(pipelineLock) {
        cameraSession.setZoom(zoom)
    }

    override fun onSetConfig(width: Int, height: Int, fps: Int, bitrate: Int, codec: String) = synchronized(pipelineLock) {
        currentBitrateMbpsGlobal.value = bitrate / 1_000_000f
        currentCodecGlobal.value = if (codec.lowercase() == "hevc" || codec.lowercase() == "h265") "hevc" else "h264"

        if (!_isStreaming.value) {
            startStreaming(
                cameraId = currentCameraIdGlobal.value,
                width = width,
                height = height,
                fps = fps,
                bitrate = bitrate,
                codec = codec,
                previewSurface = cameraSession.previewSurface
            )
            return@synchronized
        }

        val normalizedCodec = if (codec.lowercase() == "hevc" || codec.lowercase() == "h265") "hevc" else "h264"
        // If only bitrate changed, apply dynamically to MediaCodec without restarting encoder or camera
        if (width == videoEncoder.currentWidth &&
            height == videoEncoder.currentHeight &&
            fps == videoEncoder.currentFps &&
            normalizedCodec == videoEncoder.currentCodec
        ) {
            videoEncoder.setBitrate(bitrate)
            videoEncoder.requestKeyFrame()
            return@synchronized
        }

        val cameras = CameraManagerHelper.getAvailableCameras(this)
        val targetCam = cameras.find { it.id == cameraSession.currentCameraId } ?: cameras.firstOrNull()

        try {
            streamServer.clearQueues()
            val encSurface = videoEncoder.start(width, height, fps, bitrate, codec)
            val actualEncW = videoEncoder.currentWidth
            val actualEncH = videoEncoder.currentHeight

            eglPipeline.setEncoderSurface(encSurface, actualEncW, actualEncH)

            val sensorRes = if (targetCam != null) {
                CameraManagerHelper.findBestMatchingResolution(targetCam, actualEncW, actualEncH)
            } else {
                Size(maxOf(actualEncW, actualEncH), minOf(actualEncW, actualEncH))
            }

            val glCameraSurface = eglPipeline.cameraSurface
            if (glCameraSurface != null && (sensorRes != cameraSession.currentResolution || fps != cameraSession.currentFps)) {
                eglPipeline.updateCameraBufferSize(
                    sensorW = sensorRes.width,
                    sensorH = sensorRes.height,
                    orientation = targetCam?.sensorOrientation ?: 90,
                    facingBack = targetCam?.isFacingBack ?: true
                )
                cameraSession.startCamera(
                    cameraId = cameraSession.currentCameraId,
                    encoderSurface = glCameraSurface,
                    previewSurface = cameraSession.previewSurface,
                    targetResolution = sensorRes,
                    targetFps = fps,
                    onOpened = {
                        videoEncoder.requestKeyFrame()
                    }
                )
            } else {
                videoEncoder.requestKeyFrame()
            }

            currentResolutionGlobal.value = "${actualEncW}x${actualEncH}"
            currentFpsGlobal.value = fps
            currentCodecGlobal.value = videoEncoder.currentCodec
        } catch (e: Exception) {
            Log.e(TAG, "onSetConfig error: ${e.message}", e)
        }
    }

    override fun onSetMute(muted: Boolean) = synchronized(pipelineLock) {
        audioEncoder.setMuted(muted, _isStreaming.value)
        isMutedGlobal.value = muted
    }

    override fun onSetAudioGain(gain: Float) = synchronized(pipelineLock) {
        audioEncoder.gain = gain
    }

    override fun onSetPreviewEnabled(enabled: Boolean) = synchronized(pipelineLock) {
        cameraSession.setPreviewEnabled(enabled)
        eglPipeline.setPreviewEnabledState(enabled)
        isPreviewGlobal.value = enabled
    }

    override fun onSetCameraEnabled(enabled: Boolean) {
        synchronized(pipelineLock) {
            if (isCameraEnabledGlobal.value == enabled) return
            isCameraEnabledGlobal.value = enabled
            if (!_isStreaming.value) return

            if (!enabled) {
                // Physically power down camera sensor and MediaCodec encoder
                cameraSession.stopCamera()
                eglPipeline.stop()
                videoEncoder.stop()
                streamServer.clearQueues()
                Log.i(TAG, "Camera & video pipeline physically stopped to save power")
            } else {
                // Power on camera sensor and MediaCodec encoder
                Log.i(TAG, "Camera & video pipeline powering back on...")
                try {
                    val cameras = CameraManagerHelper.getAvailableCameras(this)
                    val targetCam = cameras.find { it.id == currentCameraIdGlobal.value } ?: cameras.firstOrNull()
                    val effectiveCamId = targetCam?.id ?: currentCameraIdGlobal.value

                    val encSurface = videoEncoder.start(
                        videoEncoder.currentWidth,
                        videoEncoder.currentHeight,
                        videoEncoder.currentFps,
                        videoEncoder.currentBitrate,
                        videoEncoder.currentCodec
                    )
                    val actualEncW = videoEncoder.currentWidth
                    val actualEncH = videoEncoder.currentHeight

                    val sensorRes = if (targetCam != null) {
                        CameraManagerHelper.findBestMatchingResolution(targetCam, actualEncW, actualEncH)
                    } else {
                        Size(maxOf(actualEncW, actualEncH), minOf(actualEncW, actualEncH))
                    }

                    val activePreview = cameraSession.previewSurface
                    eglPipeline.sensorOrientation = targetCam?.sensorOrientation ?: 90
                    eglPipeline.isFacingBack = targetCam?.isFacingBack ?: true
                    eglPipeline.isPreviewEnabled = isPreviewGlobal.value

                    val glCameraSurface = eglPipeline.start(
                        sensorW = sensorRes.width,
                        sensorH = sensorRes.height,
                        encW = actualEncW,
                        encH = actualEncH,
                        encoderSurface = encSurface,
                        previewSurface = activePreview
                    )

                    cameraSession.startCamera(
                        cameraId = effectiveCamId,
                        encoderSurface = glCameraSurface,
                        previewSurface = activePreview,
                        targetResolution = sensorRes,
                        targetFps = videoEncoder.currentFps,
                        onOpened = {
                            videoEncoder.requestKeyFrame()
                        }
                    )
                } catch (e: Exception) {
                    Log.e(TAG, "Failed to power on camera pipeline: ${e.message}", e)
                }
            }
        }
    }

    override fun onSetBlackout(enabled: Boolean) {
        isBlackoutGlobal.value = enabled
        if (!enabled) {
            val intent = Intent(BlackoutActivity.ACTION_DISMISS).apply {
                setPackage(packageName)
            }
            sendBroadcast(intent)
        }
    }

    override fun onStartStream() {
        startStreaming(
            cameraId = currentCameraIdGlobal.value,
            width = videoEncoder.currentWidth,
            height = videoEncoder.currentHeight,
            fps = videoEncoder.currentFps,
            bitrate = videoEncoder.currentBitrate,
            codec = videoEncoder.currentCodec,
            previewSurface = cameraSession.previewSurface
        )
    }

    override fun onStopStream() {
        userStoppedManually = true
        stopStreaming()
    }

    @Synchronized
    fun startScreenMirroring(resultCode: Int, data: Intent): Boolean {
        if (isScreenMirroringGlobal.value) return true
        Log.i(TAG, "Starting screen mirroring...")

        // Promote foreground service to include mediaProjection on Android 14+ (API 34+)
        try {
            val notification = buildNotification()
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                var type = ServiceInfo.FOREGROUND_SERVICE_TYPE_CAMERA or ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
                    type = type or ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION
                }
                startForeground(NOTIFICATION_ID, notification, type)
            }
        } catch (e: Exception) {
            Log.w(TAG, "Error updating foreground service type: ${e.message}")
        }

        // Ensure servers are running
        streamServer.start()
        commandServer.start()
        _isStreaming.value = true
        isStreamingGlobal.value = true

        // Stop camera session & eglPipeline to release camera hardware completely
        try {
            cameraSession.stopCamera()
            eglPipeline.stop()
        } catch (e: Exception) {
            Log.w(TAG, "Error stopping camera pipeline: ${e.message}")
        }

        // Freshly restart videoEncoder so VirtualDisplay connects to a brand-new clean Surface!
        try {
            videoEncoder.stop()
        } catch (e: Exception) {
            Log.w(TAG, "Error stopping videoEncoder before screen mirror: ${e.message}")
        }
        streamServer.clearQueues()

        val metrics = resources.displayMetrics
        val isPortrait = metrics.heightPixels >= metrics.widthPixels
        val encW = if (isPortrait) 1080 else 1920
        val encH = if (isPortrait) 1920 else 1080
        val densityDpi = metrics.densityDpi

        val encSurface = videoEncoder.start(
            width = encW,
            height = encH,
            fps = 30,
            bitrate = 6_000_000,
            codec = videoEncoder.currentCodec
        )

        currentResolutionGlobal.value = "${encW}x${encH}"

        screenMirrorManager.onMirrorStopped = {
            Log.i(TAG, "Screen mirror stopped callback received")
            isScreenMirroringGlobal.value = false
            if (_isStreaming.value && !userStoppedManually) {
                stopScreenMirroring()
            }
        }

        val started = screenMirrorManager.start(
            resultCode = resultCode,
            data = data,
            targetSurface = encSurface,
            width = encW,
            height = encH,
            densityDpi = densityDpi
        )

        if (started) {
            isScreenMirroringGlobal.value = true
            videoEncoder.requestKeyFrame()
            Log.i(TAG, "Screen mirror active!")
            return true
        } else {
            isScreenMirroringGlobal.value = false
            Log.e(TAG, "Screen mirror failed to start")
            stopScreenMirroring()
            return false
        }
    }

    @Synchronized
    fun stopScreenMirroring() {
        if (!isScreenMirroringGlobal.value && !screenMirrorManager.isMirroring) return
        Log.i(TAG, "Stopping screen mirroring and restoring camera...")

        screenMirrorManager.stop()
        isScreenMirroringGlobal.value = false

        // Revert foreground service type back to camera|microphone
        try {
            val notification = buildNotification()
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                startForeground(
                    NOTIFICATION_ID,
                    notification,
                    ServiceInfo.FOREGROUND_SERVICE_TYPE_CAMERA or ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE
                )
            }
        } catch (e: Exception) {
            Log.w(TAG, "Error reverting foreground service type: ${e.message}")
        }

        // Restore camera stream if streaming is active
        if (_isStreaming.value && isCameraEnabledGlobal.value) {
            try {
                videoEncoder.stop()
                streamServer.clearQueues()

                val cameras = CameraManagerHelper.getAvailableCameras(this)
                val targetCam = cameras.find { it.id == currentCameraIdGlobal.value } ?: cameras.firstOrNull()
                val effectiveCamId = targetCam?.id ?: currentCameraIdGlobal.value

                val encSurface = videoEncoder.start(
                    width = 1920,
                    height = 1080,
                    fps = currentFpsGlobal.value,
                    bitrate = (currentBitrateMbpsGlobal.value * 1_000_000).toInt(),
                    codec = currentCodecGlobal.value
                )
                val actualEncW = videoEncoder.currentWidth
                val actualEncH = videoEncoder.currentHeight

                currentResolutionGlobal.value = "${actualEncW}x${actualEncH}"

                val sensorRes = if (targetCam != null) {
                    CameraManagerHelper.findBestMatchingResolution(targetCam, actualEncW, actualEncH)
                } else {
                    Size(maxOf(actualEncW, actualEncH), minOf(actualEncW, actualEncH))
                }

                val activePreview = cameraSession.previewSurface
                eglPipeline.sensorOrientation = targetCam?.sensorOrientation ?: 90
                eglPipeline.isFacingBack = targetCam?.isFacingBack ?: true
                eglPipeline.isPreviewEnabled = isPreviewGlobal.value

                val glCameraSurface = eglPipeline.start(
                    sensorW = sensorRes.width,
                    sensorH = sensorRes.height,
                    encW = actualEncW,
                    encH = actualEncH,
                    encoderSurface = encSurface,
                    previewSurface = activePreview
                )

                cameraSession.startCamera(
                    cameraId = effectiveCamId,
                    encoderSurface = glCameraSurface,
                    previewSurface = activePreview,
                    targetResolution = sensorRes,
                    targetFps = videoEncoder.currentFps,
                    onOpened = {
                        videoEncoder.requestKeyFrame()
                    }
                )
            } catch (e: Exception) {
                Log.e(TAG, "Failed to restore camera pipeline: ${e.message}", e)
            }
        }
    }

    override fun onSetScreenMirror(enabled: Boolean) {
        Log.i(TAG, "onSetScreenMirror: enabled=$enabled")
        if (enabled) {
            val intent = Intent(this, MainActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP
                putExtra(MainActivity.EXTRA_REQUEST_SCREEN_CAPTURE, true)
            }
            startActivity(intent)
        } else {
            stopScreenMirroring()
        }
    }

    companion object {
        const val ACTION_STOP = "com.aselens.aselcam.ACTION_STOP"
        var instance: CameraStreamService? = null
        val isStreamingGlobal = MutableStateFlow(false)
        val isScreenMirroringGlobal = MutableStateFlow(false)
        var mediaProjectionResultCode: Int? = null
        var mediaProjectionData: Intent? = null
        val currentCameraIdGlobal = MutableStateFlow("0")
        val isTorchGlobal = MutableStateFlow(false)
        val isPreviewGlobal = MutableStateFlow(true)
        val isCameraEnabledGlobal = MutableStateFlow(true)
        val isMutedGlobal = MutableStateFlow(false)
        val isBlackoutGlobal = MutableStateFlow(false)
        val currentResolutionGlobal = MutableStateFlow("1920x1080")
        val currentFpsGlobal = MutableStateFlow(30)
        val currentBitrateMbpsGlobal = MutableStateFlow(4f)
        val currentCodecGlobal = MutableStateFlow("h264")
        val deviceOrientationGlobal = MutableStateFlow(0)
    }
}
