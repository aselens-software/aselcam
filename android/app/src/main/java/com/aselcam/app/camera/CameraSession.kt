package com.aselcam.app.camera

import android.annotation.SuppressLint
import android.content.Context
import android.graphics.Rect
import android.hardware.camera2.*
import android.hardware.camera2.params.OutputConfiguration
import android.hardware.camera2.params.SessionConfiguration
import android.os.Build
import android.os.Handler
import android.os.HandlerThread
import android.util.Log
import android.util.Range
import android.util.Size
import android.view.Surface
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicBoolean

class CameraSession(
    private val context: Context
) {
    private val TAG = "AselCam_CameraSession"

    private val cameraManager = context.getSystemService(Context.CAMERA_SERVICE) as CameraManager
    private var cameraDevice: CameraDevice? = null
    private var captureSession: CameraCaptureSession? = null
    private var previewRequestBuilder: CaptureRequest.Builder? = null

    private var backgroundThread: HandlerThread? = null
    private var backgroundHandler: Handler? = null

    var currentCameraId: String = "0"
        private set
    var currentResolution: Size = Size(1920, 1080)
        private set
    var currentFps: Int = 30
        private set

    private var encoderSurface: Surface? = null
    var previewSurface: Surface? = null
        private set

    @Volatile
    var isPreviewEnabled: Boolean = true
        private set

    @Volatile
    var isTorchEnabled: Boolean = false
        private set

    @Volatile
    var currentZoom: Float = 1.0f
        private set

    val maxZoom: Float
        get() {
            try {
                val devId = cameraDevice?.id ?: currentCameraId
                val chars = cameraManager.getCameraCharacteristics(devId)
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                    val range = chars.get(CameraCharacteristics.CONTROL_ZOOM_RATIO_RANGE)
                    if (range != null) return range.upper
                }
                return chars.get(CameraCharacteristics.SCALER_AVAILABLE_MAX_DIGITAL_ZOOM) ?: 1.0f
            } catch (e: Exception) {
                return 1.0f
            }
        }

    private val isSessionActive = AtomicBoolean(false)

    private fun startBackgroundThread() {
        if (backgroundThread == null) {
            backgroundThread = HandlerThread("AselCam-CameraBackground").apply {
                start()
                backgroundHandler = Handler(looper)
            }
        }
    }

    private fun stopBackgroundThread() {
        backgroundThread?.quitSafely()
        try {
            backgroundThread?.join()
        } catch (e: Exception) {}
        backgroundThread = null
        backgroundHandler = null
    }

    @SuppressLint("MissingPermission")
    @Synchronized
    fun startCamera(
        cameraId: String,
        encoderSurface: Surface,
        previewSurface: Surface?,
        targetResolution: Size,
        targetFps: Int,
        onOpened: (() -> Unit)? = null
    ) {
        stopCamera()
        startBackgroundThread()

        this.currentCameraId = cameraId
        this.encoderSurface = encoderSurface
        if (previewSurface != null) {
            this.previewSurface = previewSurface
        }
        this.currentResolution = targetResolution
        this.currentFps = targetFps

        Log.i(TAG, "Opening camera $cameraId for ${targetResolution.width}x${targetResolution.height} @ $targetFps fps")

        cameraManager.openCamera(cameraId, object : CameraDevice.StateCallback() {
            override fun onOpened(camera: CameraDevice) {
                cameraDevice = camera
                isSessionActive.set(true)
                createCaptureSession()
                onOpened?.invoke()
            }

            override fun onDisconnected(camera: CameraDevice) {
                Log.w(TAG, "Camera disconnected: $cameraId")
                camera.close()
                cameraDevice = null
                isSessionActive.set(false)
            }

            override fun onError(camera: CameraDevice, error: Int) {
                Log.e(TAG, "Camera open error: $error, scheduling self-healing retry...")
                try {
                    camera.close()
                } catch (e: Exception) {}
                cameraDevice = null
                isSessionActive.set(false)

                // Self-healing auto-recovery: retry opening camera if surface is valid
                val enc = encoderSurface
                if (enc != null && enc.isValid) {
                    backgroundHandler?.postDelayed({
                        if (!isSessionActive.get() && encoderSurface?.isValid == true) {
                            try {
                                Log.i(TAG, "Attempting auto-recovery for camera $cameraId...")
                                startCamera(currentCameraId, encoderSurface!!, previewSurface, currentResolution, currentFps, onOpened)
                            } catch (e: Exception) {
                                Log.e(TAG, "Auto-recovery error: ${e.message}")
                            }
                        }
                    }, 400)
                }
            }
        }, backgroundHandler)
    }

    private fun createCaptureSession() {
        val device = cameraDevice ?: return
        val encSurface = encoderSurface ?: return
        if (!encSurface.isValid) {
            Log.e(TAG, "Camera pipeline surface is not valid, skipping createCaptureSession")
            return
        }

        try {
            captureSession = null
            val surfaces = listOf(encSurface)

            val requestBuilder = device.createCaptureRequest(CameraDevice.TEMPLATE_RECORD)
            requestBuilder.addTarget(encSurface)

            // Continuous video autofocus & exposure
            requestBuilder.set(CaptureRequest.CONTROL_AF_MODE, CaptureRequest.CONTROL_AF_MODE_CONTINUOUS_VIDEO)
            requestBuilder.set(CaptureRequest.CONTROL_AE_MODE, CaptureRequest.CONTROL_AE_MODE_ON)

            // Target FPS range
            val characteristics = cameraManager.getCameraCharacteristics(device.id)
            val camInfo = CameraInfo(
                id = device.id,
                name = "",
                isFacingBack = true,
                sensorOrientation = 0,
                supportedResolutions = emptyList(),
                supportedFpsRanges = characteristics.get(CameraCharacteristics.CONTROL_AE_AVAILABLE_TARGET_FPS_RANGES)?.toList() ?: emptyList(),
                maxZoom = 1.0f,
                hasFlash = false
            )
            val fpsRange = CameraManagerHelper.findBestFpsRange(camInfo, currentFps)
            requestBuilder.set(CaptureRequest.CONTROL_AE_TARGET_FPS_RANGE, fpsRange)

            // Apply torch & zoom
            applyTorch(requestBuilder, isTorchEnabled)
            applyZoom(requestBuilder, currentZoom)

            previewRequestBuilder = requestBuilder

            val stateCallback = object : CameraCaptureSession.StateCallback() {
                override fun onConfigured(session: CameraCaptureSession) {
                    if (!isSessionActive.get() || cameraDevice == null) return
                    captureSession = session
                    updateRepeatingRequest()
                    Log.i(TAG, "Capture session configured on GL pipeline surface")
                }

                override fun onConfigureFailed(session: CameraCaptureSession) {
                    Log.e(TAG, "Camera session configuration failed, retrying...")
                    captureSession = null
                    backgroundHandler?.postDelayed({
                        if (isSessionActive.get() && cameraDevice != null && encoderSurface?.isValid == true) {
                            try {
                                createCaptureSession()
                            } catch (e: Exception) {
                                Log.e(TAG, "Retry createCaptureSession failed: ${e.message}")
                            }
                        }
                    }, 300)
                }
            }

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                val outputConfigs = surfaces.map { OutputConfiguration(it) }
                val executor = Executors.newSingleThreadExecutor()
                val sessionConfig = SessionConfiguration(
                    SessionConfiguration.SESSION_REGULAR,
                    outputConfigs,
                    executor,
                    stateCallback
                )
                device.createCaptureSession(sessionConfig)
            } else {
                @Suppress("DEPRECATION")
                device.createCaptureSession(surfaces, stateCallback, backgroundHandler)
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error creating capture session: ${e.message}")
        }
    }

    private fun updateRepeatingRequest() {
        val session = captureSession ?: return
        val builder = previewRequestBuilder ?: return

        try {
            session.setRepeatingRequest(builder.build(), null, backgroundHandler)
        } catch (e: IllegalStateException) {
            Log.w(TAG, "Session closed during updateRepeatingRequest: ${e.message}")
        } catch (e: CameraAccessException) {
            Log.w(TAG, "CameraAccessException during updateRepeatingRequest: ${e.message}")
        } catch (e: Exception) {
            Log.e(TAG, "Error updating repeating request: ${e.message}")
        }
    }

    @Synchronized
    fun setPreviewSurface(surface: Surface?) {
        this.previewSurface = surface
    }

    @Synchronized
    fun setPreviewEnabled(enabled: Boolean) {
        this.isPreviewEnabled = enabled
    }

    @Synchronized
    fun setTorch(enabled: Boolean) {
        this.isTorchEnabled = enabled
        val builder = previewRequestBuilder
        if (builder != null && captureSession != null) {
            applyTorch(builder, enabled)
            updateRepeatingRequest()
        } else {
            try {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                    cameraManager.setTorchMode(currentCameraId, enabled)
                }
            } catch (e: Exception) {
                Log.w(TAG, "Standby setTorchMode failed: ${e.message}")
            }
        }
    }

    private fun applyTorch(builder: CaptureRequest.Builder, enabled: Boolean) {
        try {
            val deviceId = cameraDevice?.id ?: return
            val characteristics = cameraManager.getCameraCharacteristics(deviceId)
            val hasFlash = characteristics.get(CameraCharacteristics.FLASH_INFO_AVAILABLE) ?: false
            if (hasFlash) {
                if (enabled) {
                    builder.set(CaptureRequest.CONTROL_AE_MODE, CaptureRequest.CONTROL_AE_MODE_ON)
                    builder.set(CaptureRequest.FLASH_MODE, CaptureRequest.FLASH_MODE_TORCH)
                } else {
                    builder.set(CaptureRequest.FLASH_MODE, CaptureRequest.FLASH_MODE_OFF)
                }
            }
        } catch (e: Exception) {
            Log.w(TAG, "applyTorch error: ${e.message}")
        }
    }

    @Synchronized
    fun setZoom(zoom: Float) {
        this.currentZoom = zoom
        val builder = previewRequestBuilder ?: return
        applyZoom(builder, zoom)
        updateRepeatingRequest()
    }

    private fun applyZoom(builder: CaptureRequest.Builder, zoom: Float) {
        try {
            val deviceId = cameraDevice?.id ?: return
            val characteristics = cameraManager.getCameraCharacteristics(deviceId)

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                val maxZoom = characteristics.get(CameraCharacteristics.CONTROL_ZOOM_RATIO_RANGE)
                if (maxZoom != null) {
                    val clamped = zoom.coerceIn(maxZoom.lower, maxZoom.upper)
                    builder.set(CaptureRequest.CONTROL_ZOOM_RATIO, clamped)
                    return
                }
            }

            // Fallback for older APIs: crop region
            val maxDigitalZoom = characteristics.get(CameraCharacteristics.SCALER_AVAILABLE_MAX_DIGITAL_ZOOM) ?: 1.0f
            val activeArray = characteristics.get(CameraCharacteristics.SENSOR_INFO_ACTIVE_ARRAY_SIZE) ?: return
            val clampedZoom = zoom.coerceIn(1.0f, maxDigitalZoom)

            val cropW = (activeArray.width() / clampedZoom).toInt()
            val cropH = (activeArray.height() / clampedZoom).toInt()
            val cropX = (activeArray.width() - cropW) / 2
            val cropY = (activeArray.height() - cropH) / 2

            val cropRect = Rect(cropX, cropY, cropX + cropW, cropY + cropH)
            builder.set(CaptureRequest.SCALER_CROP_REGION, cropRect)
        } catch (e: Exception) {}
    }

    @Synchronized
    fun stopCamera() {
        isSessionActive.set(false)
        try {
            captureSession?.stopRepeating()
            captureSession?.abortCaptures()
            captureSession?.close()
        } catch (e: Exception) {}
        captureSession = null

        try {
            cameraDevice?.close()
        } catch (e: Exception) {}
        cameraDevice = null

        stopBackgroundThread()
        Log.i(TAG, "Camera stopped")
    }
}
