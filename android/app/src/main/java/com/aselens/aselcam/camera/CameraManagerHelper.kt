package com.aselens.aselcam.camera

import android.content.Context
import android.graphics.ImageFormat
import android.hardware.camera2.CameraCharacteristics
import android.hardware.camera2.CameraManager
import android.hardware.camera2.params.StreamConfigurationMap
import android.media.MediaCodec
import android.os.Build
import android.util.Range
import android.util.Size

data class CameraInfo(
    val id: String,
    val name: String,
    val isFacingBack: Boolean,
    val sensorOrientation: Int,
    val supportedResolutions: List<Size>,
    val supportedFpsRanges: List<Range<Int>>,
    val maxZoom: Float,
    val hasFlash: Boolean
)

object CameraManagerHelper {

    fun getAvailableCameras(context: Context): List<CameraInfo> {
        val result = mutableListOf<CameraInfo>()
        try {
            val cameraManager = context.getSystemService(Context.CAMERA_SERVICE) as? CameraManager
                ?: return fallbackCameras()

            val cameraIds = try {
                cameraManager.cameraIdList
            } catch (t: Throwable) {
                emptyArray<String>()
            }

            for (cameraId in cameraIds) {
                try {
                    val characteristics = cameraManager.getCameraCharacteristics(cameraId)
                    val facing = characteristics.get(CameraCharacteristics.LENS_FACING) ?: continue

                    val isBack = facing == CameraCharacteristics.LENS_FACING_BACK
                    val name = if (isBack) "Arka Kamera ($cameraId)" else "Ön Kamera ($cameraId)"
                    val orientation = characteristics.get(CameraCharacteristics.SENSOR_ORIENTATION) ?: 90

                    val map = characteristics.get(CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP)
                    val resolutions = mutableListOf<Size>()

                    if (map != null) {
                        val mediaCodecSizes = map.getOutputSizes(MediaCodec::class.java) ?: emptyArray()
                        val surfaceSizes = map.getOutputSizes(ImageFormat.PRIVATE) ?: emptyArray()
                        val allSizes = (mediaCodecSizes.toList() + surfaceSizes.toList())
                            .distinctBy { "${it.width}x${it.height}" }
                            .filter { it.width >= 640 && it.height >= 360 }
                            .sortedByDescending { it.width * it.height }

                        resolutions.addAll(allSizes)
                    }

                    // If no sizes were parsed, provide standard video fallbacks
                    if (resolutions.isEmpty()) {
                        resolutions.addAll(
                            listOf(
                                Size(3840, 2160),
                                Size(1920, 1080),
                                Size(1280, 720),
                                Size(854, 480)
                            )
                        )
                    }

                    val fpsRanges = characteristics.get(CameraCharacteristics.CONTROL_AE_AVAILABLE_TARGET_FPS_RANGES)
                        ?.toList()
                        ?.sortedByDescending { it.upper }
                        ?: listOf(Range(30, 30), Range(15, 30))

                    val maxZoom = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                        val zoomRange = characteristics.get(CameraCharacteristics.CONTROL_ZOOM_RATIO_RANGE)
                        zoomRange?.upper ?: (characteristics.get(CameraCharacteristics.SCALER_AVAILABLE_MAX_DIGITAL_ZOOM) ?: 10.0f)
                    } else {
                        characteristics.get(CameraCharacteristics.SCALER_AVAILABLE_MAX_DIGITAL_ZOOM) ?: 10.0f
                    }
                    val hasFlash = characteristics.get(CameraCharacteristics.FLASH_INFO_AVAILABLE) ?: false

                    result.add(
                        CameraInfo(
                            id = cameraId,
                            name = name,
                            isFacingBack = isBack,
                            sensorOrientation = orientation,
                            supportedResolutions = resolutions,
                            supportedFpsRanges = fpsRanges,
                            maxZoom = maxZoom,
                            hasFlash = hasFlash
                        )
                    )
                } catch (e: Exception) {
                    e.printStackTrace()
                }
            }
        } catch (t: Throwable) {
            t.printStackTrace()
        }

        if (result.isEmpty()) {
            result.addAll(fallbackCameras())
        }
        return result
    }

    private fun fallbackCameras(): List<CameraInfo> {
        return listOf(
            CameraInfo(
                id = "0",
                name = "Varsayılan Kamera",
                isFacingBack = true,
                sensorOrientation = 90,
                supportedResolutions = listOf(
                    Size(1920, 1080),
                    Size(1280, 720),
                    Size(640, 480)
                ),
                supportedFpsRanges = listOf(Range(30, 30), Range(15, 30)),
                maxZoom = 4.0f,
                hasFlash = false
            )
        )
    }

    fun findBestMatchingResolution(camera: CameraInfo, targetWidth: Int, targetHeight: Int): Size {
        val reqW = maxOf(targetWidth, targetHeight)
        val reqH = minOf(targetWidth, targetHeight)

        val exact = camera.supportedResolutions.find { it.width == reqW && it.height == reqH }
        if (exact != null) return exact

        // Prefer the smallest sensor resolution that covers at least reqW x reqH (no upscaling loss)
        val covering = camera.supportedResolutions
            .filter { it.width >= reqW && it.height >= reqH }
            .minByOrNull { it.width * it.height }
        if (covering != null) return covering

        // Otherwise find closest area
        val targetArea = reqW * reqH
        return camera.supportedResolutions.minByOrNull {
            val area = it.width * it.height
            Math.abs(area - targetArea)
        } ?: Size(reqW, reqH)
    }

    fun findBestFpsRange(camera: CameraInfo, targetFps: Int): Range<Int> {
        // Look for fixed fps range e.g. [60, 60] or [30, 30]
        val exact = camera.supportedFpsRanges.find { it.lower == targetFps && it.upper == targetFps }
        if (exact != null) return exact

        // Look for range with target upper fps
        val withUpper = camera.supportedFpsRanges.find { it.upper == targetFps }
        if (withUpper != null) return withUpper

        // Return highest available
        return camera.supportedFpsRanges.firstOrNull() ?: Range(targetFps, targetFps)
    }
}
