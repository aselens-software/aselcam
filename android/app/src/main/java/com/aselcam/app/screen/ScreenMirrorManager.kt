package com.aselcam.app.screen

import android.content.Context
import android.content.Intent
import android.hardware.display.DisplayManager
import android.hardware.display.VirtualDisplay
import android.media.projection.MediaProjection
import android.media.projection.MediaProjectionManager
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.view.Surface

class ScreenMirrorManager(private val context: Context) {
    private val TAG = "AselCam_ScreenMirror"

    private val projectionManager: MediaProjectionManager by lazy {
        context.getSystemService(Context.MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
    }

    private var mediaProjection: MediaProjection? = null
    private var virtualDisplay: VirtualDisplay? = null

    @Volatile
    var isMirroring: Boolean = false
        private set

    var onMirrorStopped: (() -> Unit)? = null

    @Synchronized
    fun start(
        resultCode: Int,
        data: Intent,
        targetSurface: Surface,
        width: Int,
        height: Int,
        densityDpi: Int
    ): Boolean {
        stop()
        try {
            Log.i(TAG, "Starting screen mirror virtual display: ${width}x${height} @ ${densityDpi}dpi")
            val mp = projectionManager.getMediaProjection(resultCode, data) ?: run {
                Log.e(TAG, "getMediaProjection returned null")
                return false
            }

            val mainHandler = Handler(Looper.getMainLooper())

            // Register mandatory callback for Android 14+ (API 34+)
            mp.registerCallback(object : MediaProjection.Callback() {
                override fun onStop() {
                    Log.i(TAG, "MediaProjection was stopped by user or system")
                    stop()
                    onMirrorStopped?.invoke()
                }
            }, mainHandler)

            val vd = mp.createVirtualDisplay(
                "AselCam-ScreenMirror",
                width,
                height,
                densityDpi,
                DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
                targetSurface,
                object : VirtualDisplay.Callback() {
                    override fun onPaused() {
                        Log.i(TAG, "VirtualDisplay onPaused")
                    }
                    override fun onResumed() {
                        Log.i(TAG, "VirtualDisplay onResumed")
                    }
                    override fun onStopped() {
                        Log.i(TAG, "VirtualDisplay onStopped")
                    }
                },
                mainHandler
            ) ?: run {
                Log.e(TAG, "createVirtualDisplay returned null")
                mp.stop()
                return false
            }

            mediaProjection = mp
            virtualDisplay = vd
            isMirroring = true
            Log.i(TAG, "Screen mirroring active on virtual display")
            return true
        } catch (e: Exception) {
            Log.e(TAG, "Failed to start screen mirroring: ${e.message}", e)
            stop()
            return false
        }
    }

    @Synchronized
    fun stop() {
        if (!isMirroring && virtualDisplay == null && mediaProjection == null) return
        Log.i(TAG, "Stopping screen mirroring")
        try {
            virtualDisplay?.release()
        } catch (e: Exception) {
            Log.w(TAG, "Error releasing virtual display: ${e.message}")
        }
        virtualDisplay = null

        try {
            mediaProjection?.stop()
        } catch (e: Exception) {
            Log.w(TAG, "Error stopping media projection: ${e.message}")
        }
        mediaProjection = null
        isMirroring = false
    }
}
