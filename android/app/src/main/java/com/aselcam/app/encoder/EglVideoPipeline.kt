package com.aselcam.app.encoder

import android.graphics.SurfaceTexture
import android.opengl.EGL14
import android.opengl.EGLConfig
import android.opengl.EGLContext
import android.opengl.EGLDisplay
import android.opengl.EGLExt
import android.opengl.EGLSurface
import android.opengl.GLES11Ext
import android.opengl.GLES20
import android.opengl.Matrix
import android.os.Handler
import android.os.HandlerThread
import android.util.Log
import android.view.Surface
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.FloatBuffer
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean

/**
 * Hardware-accelerated OpenGL ES 2.0 video pipeline that decouples Camera2 from both
 * MediaCodec and the Activity's SurfaceView preview.
 *
 * - Camera2 writes ONLY to [cameraSurface] (backed by an OES SurfaceTexture).
 * - On each frame, renders the OES texture to the encoder EGLSurface (and optionally to the preview EGLSurface).
 * - Toggling preview, locking the phone screen, or backgrounding the app never touches Camera2's
 *   CameraCaptureSession or disconnects MediaCodec's input surface, eliminating green-screen artifacts.
 * - Handles sensor orientation, physical phone rotation (Portrait / Landscape), and aspect-ratio
 *   center-cropping (16:9, 9:16, 4:3, 3:4, 1:1) on the GPU with zero CPU copy.
 */
class EglVideoPipeline {
    private val TAG = "AselCam_EglPipeline"

    private var glThread: HandlerThread? = null
    private var glHandler: Handler? = null
    private val isRunning = AtomicBoolean(false)

    private var eglDisplay: EGLDisplay = EGL14.EGL_NO_DISPLAY
    private var eglContext: EGLContext = EGL14.EGL_NO_CONTEXT
    private var eglConfig: EGLConfig? = null
    private var pbufferSurface: EGLSurface = EGL14.EGL_NO_SURFACE
    private var encoderEglSurface: EGLSurface = EGL14.EGL_NO_SURFACE
    private var previewEglSurface: EGLSurface = EGL14.EGL_NO_SURFACE
    private var currentPreviewRawSurface: Surface? = null

    private var oesTextureId: Int = -1
    private var cameraSurfaceTexture: SurfaceTexture? = null
    var cameraSurface: Surface? = null
        private set

    private var programId: Int = 0
    private var aPositionLoc: Int = -1
    private var aTexCoordLoc: Int = -1
    private var uMVPMatrixLoc: Int = -1
    private var uSTMatrixLoc: Int = -1

    private val stMatrix = FloatArray(16)
    private val mvpMatrix = FloatArray(16)

    @Volatile
    var sensorWidth: Int = 1920
        private set
    @Volatile
    var sensorHeight: Int = 1080
        private set
    @Volatile
    var encoderWidth: Int = 1920
        private set
    @Volatile
    var encoderHeight: Int = 1080
        private set

    @Volatile
    var sensorOrientation: Int = 90
    @Volatile
    var isFacingBack: Boolean = true
    @Volatile
    var deviceOrientationDegrees: Int = 0
    @Volatile
    var isPreviewEnabled: Boolean = true

    var hasActiveClients: () -> Boolean = { true }

    @Volatile
    private var hasValidTextureFrame: Boolean = false
    private var lastFrameTimestampNs: Long = 0L

    private val vertexData = floatArrayOf(
        // X, Y, U, V
        -1.0f, -1.0f, 0.0f, 0.0f,
         1.0f, -1.0f, 1.0f, 0.0f,
        -1.0f,  1.0f, 0.0f, 1.0f,
         1.0f,  1.0f, 1.0f, 1.0f
    )
    private val vertexBuffer: FloatBuffer = ByteBuffer
        .allocateDirect(vertexData.size * 4)
        .order(ByteOrder.nativeOrder())
        .asFloatBuffer()
        .apply {
            put(vertexData)
            position(0)
        }

    private val heartbeatRunnable = object : Runnable {
        override fun run() {
            if (!isRunning.get()) return
            val nowNs = System.nanoTime()
            // If camera sensor hasn't delivered a new frame in >65ms (e.g. during camera switch or screen transition),
            // re-emit the last valid GPU texture so encoder and PC stream stay alive continuously.
            if (hasValidTextureFrame && (nowNs - lastFrameTimestampNs) > 65_000_000L && (hasActiveClients() || isPreviewEnabled)) {
                drawCurrentTexture(nowNs)
            }
            glHandler?.postDelayed(this, 33L)
        }
    }

    @Synchronized
    fun start(
        sensorW: Int,
        sensorH: Int,
        encW: Int,
        encH: Int,
        encoderSurface: Surface,
        previewSurface: Surface?
    ): Surface {
        stop()

        sensorWidth = sensorW
        sensorHeight = sensorH
        encoderWidth = encW
        encoderHeight = encH
        hasValidTextureFrame = false

        val thread = HandlerThread("AselCam-GLPipeline").apply { start() }
        val handler = Handler(thread.looper)
        glThread = thread
        glHandler = handler

        val latch = CountDownLatch(1)
        var initError: Exception? = null

        handler.post {
            try {
                initEgl()
                initShaders()
                initCameraSurfaceTexture(sensorW, sensorH, handler)
                setEncoderSurfaceInternal(encoderSurface, encW, encH)
                setPreviewSurfaceInternal(previewSurface)
                isRunning.set(true)
                handler.postDelayed(heartbeatRunnable, 33L)
            } catch (e: Exception) {
                Log.e(TAG, "EGL pipeline init failed: ${e.message}", e)
                initError = e
            } finally {
                latch.countDown()
            }
        }

        latch.await(3, TimeUnit.SECONDS)
        initError?.let { throw it }
        return cameraSurface ?: throw IllegalStateException("Camera surface was not created")
    }

    fun updateCameraBufferSize(sensorW: Int, sensorH: Int, orientation: Int, facingBack: Boolean) {
        sensorWidth = sensorW
        sensorHeight = sensorH
        sensorOrientation = orientation
        isFacingBack = facingBack
        glHandler?.post {
            try {
                cameraSurfaceTexture?.setDefaultBufferSize(sensorW, sensorH)
            } catch (e: Exception) {
                Log.w(TAG, "updateCameraBufferSize error: ${e.message}")
            }
        }
    }

    fun setEncoderSurface(encoderSurface: Surface, encW: Int, encH: Int) {
        val handler = glHandler ?: return
        val latch = CountDownLatch(1)
        handler.post {
            try {
                setEncoderSurfaceInternal(encoderSurface, encW, encH)
            } finally {
                latch.countDown()
            }
        }
        latch.await(2, TimeUnit.SECONDS)
    }

    fun setPreviewSurface(surface: Surface?) {
        glHandler?.post {
            setPreviewSurfaceInternal(surface)
        }
    }

    fun setPreviewEnabledState(enabled: Boolean) {
        isPreviewEnabled = enabled
    }

    private fun initEgl() {
        eglDisplay = EGL14.eglGetDisplay(EGL14.EGL_DEFAULT_DISPLAY)
        if (eglDisplay == EGL14.EGL_NO_DISPLAY) {
            throw RuntimeException("eglGetDisplay failed")
        }
        val version = IntArray(2)
        if (!EGL14.eglInitialize(eglDisplay, version, 0, version, 1)) {
            throw RuntimeException("eglInitialize failed")
        }

        val attribList = intArrayOf(
            EGL14.EGL_RED_SIZE, 8,
            EGL14.EGL_GREEN_SIZE, 8,
            EGL14.EGL_BLUE_SIZE, 8,
            EGL14.EGL_ALPHA_SIZE, 8,
            EGL14.EGL_RENDERABLE_TYPE, EGL14.EGL_OPENGL_ES2_BIT,
            EGLExt.EGL_RECORDABLE_ANDROID, 1,
            EGL14.EGL_NONE
        )
        val configs = arrayOfNulls<EGLConfig>(1)
        val numConfigs = IntArray(1)
        if (!EGL14.eglChooseConfig(eglDisplay, attribList, 0, configs, 0, 1, numConfigs, 0) || numConfigs[0] <= 0) {
            throw RuntimeException("eglChooseConfig failed")
        }
        eglConfig = configs[0]

        val contextAttribs = intArrayOf(
            EGL14.EGL_CONTEXT_CLIENT_VERSION, 2,
            EGL14.EGL_NONE
        )
        eglContext = EGL14.eglCreateContext(eglDisplay, eglConfig, EGL14.EGL_NO_CONTEXT, contextAttribs, 0)
        if (eglContext == EGL14.EGL_NO_CONTEXT) {
            throw RuntimeException("eglCreateContext failed")
        }

        val pbufferAttribs = intArrayOf(
            EGL14.EGL_WIDTH, 1,
            EGL14.EGL_HEIGHT, 1,
            EGL14.EGL_NONE
        )
        pbufferSurface = EGL14.eglCreatePbufferSurface(eglDisplay, eglConfig, pbufferAttribs, 0)
        EGL14.eglMakeCurrent(eglDisplay, pbufferSurface, pbufferSurface, eglContext)
    }

    private fun initShaders() {
        val vertexShaderCode = """
            uniform mat4 uMVPMatrix;
            uniform mat4 uSTMatrix;
            attribute vec4 aPosition;
            attribute vec4 aTexCoord;
            varying vec2 vTexCoord;
            void main() {
                gl_Position = uMVPMatrix * aPosition;
                vTexCoord = (uSTMatrix * aTexCoord).xy;
            }
        """.trimIndent()

        val fragmentShaderCode = """
            #extension GL_OES_EGL_image_external : require
            precision mediump float;
            varying vec2 vTexCoord;
            uniform samplerExternalOES sTexture;
            void main() {
                gl_FragColor = texture2D(sTexture, vTexCoord);
            }
        """.trimIndent()

        val vShader = compileShader(GLES20.GL_VERTEX_SHADER, vertexShaderCode)
        val fShader = compileShader(GLES20.GL_FRAGMENT_SHADER, fragmentShaderCode)
        programId = GLES20.glCreateProgram()
        GLES20.glAttachShader(programId, vShader)
        GLES20.glAttachShader(programId, fShader)
        GLES20.glLinkProgram(programId)

        aPositionLoc = GLES20.glGetAttribLocation(programId, "aPosition")
        aTexCoordLoc = GLES20.glGetAttribLocation(programId, "aTexCoord")
        uMVPMatrixLoc = GLES20.glGetUniformLocation(programId, "uMVPMatrix")
        uSTMatrixLoc = GLES20.glGetUniformLocation(programId, "uSTMatrix")
    }

    private fun compileShader(type: Int, source: String): Int {
        val shader = GLES20.glCreateShader(type)
        GLES20.glShaderSource(shader, source)
        GLES20.glCompileShader(shader)
        val compiled = IntArray(1)
        GLES20.glGetShaderiv(shader, GLES20.GL_COMPILE_STATUS, compiled, 0)
        if (compiled[0] == 0) {
            val info = GLES20.glGetShaderInfoLog(shader)
            GLES20.glDeleteShader(shader)
            throw RuntimeException("Shader compile error: $info")
        }
        return shader
    }

    private fun initCameraSurfaceTexture(sensorW: Int, sensorH: Int, handler: Handler) {
        val textures = IntArray(1)
        GLES20.glGenTextures(1, textures, 0)
        oesTextureId = textures[0]

        GLES20.glBindTexture(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, oesTextureId)
        GLES20.glTexParameterf(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_LINEAR.toFloat())
        GLES20.glTexParameterf(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, GLES20.GL_TEXTURE_MAG_FILTER, GLES20.GL_LINEAR.toFloat())
        GLES20.glTexParameteri(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, GLES20.GL_TEXTURE_WRAP_S, GLES20.GL_CLAMP_TO_EDGE)
        GLES20.glTexParameteri(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, GLES20.GL_TEXTURE_WRAP_T, GLES20.GL_CLAMP_TO_EDGE)

        val st = SurfaceTexture(oesTextureId)
        st.setDefaultBufferSize(sensorW, sensorH)
        st.setOnFrameAvailableListener({
            onCameraFrameAvailable()
        }, handler)

        cameraSurfaceTexture = st
        cameraSurface = Surface(st)
    }

    private fun setEncoderSurfaceInternal(surface: Surface, encW: Int, encH: Int) {
        EGL14.eglMakeCurrent(eglDisplay, pbufferSurface, pbufferSurface, eglContext)
        if (encoderEglSurface != EGL14.EGL_NO_SURFACE) {
            try {
                EGL14.eglDestroySurface(eglDisplay, encoderEglSurface)
            } catch (_: Exception) {}
            encoderEglSurface = EGL14.EGL_NO_SURFACE
        }
        encoderWidth = encW
        encoderHeight = encH
        if (surface.isValid) {
            val attribs = intArrayOf(EGL14.EGL_NONE)
            encoderEglSurface = EGL14.eglCreateWindowSurface(eglDisplay, eglConfig, surface, attribs, 0)
        }
    }

    private fun setPreviewSurfaceInternal(surface: Surface?) {
        if (currentPreviewRawSurface === surface && previewEglSurface != EGL14.EGL_NO_SURFACE) {
            return
        }
        EGL14.eglMakeCurrent(eglDisplay, pbufferSurface, pbufferSurface, eglContext)
        if (previewEglSurface != EGL14.EGL_NO_SURFACE) {
            try {
                EGL14.eglDestroySurface(eglDisplay, previewEglSurface)
            } catch (_: Exception) {}
            previewEglSurface = EGL14.EGL_NO_SURFACE
        }
        currentPreviewRawSurface = surface
        if (surface != null && surface.isValid) {
            try {
                val attribs = intArrayOf(EGL14.EGL_NONE)
                previewEglSurface = EGL14.eglCreateWindowSurface(eglDisplay, eglConfig, surface, attribs, 0)
            } catch (e: Exception) {
                Log.w(TAG, "Failed to create preview EGLSurface: ${e.message}")
                previewEglSurface = EGL14.EGL_NO_SURFACE
            }
        }
    }

    private fun onCameraFrameAvailable() {
        if (!isRunning.get()) return
        val st = cameraSurfaceTexture ?: return
        try {
            EGL14.eglMakeCurrent(eglDisplay, pbufferSurface, pbufferSurface, eglContext)
            st.updateTexImage()
            st.getTransformMatrix(stMatrix)
            hasValidTextureFrame = true
            val tsNs = if (st.timestamp > 0L) st.timestamp else System.nanoTime()
            lastFrameTimestampNs = System.nanoTime()
            drawCurrentTexture(tsNs)
        } catch (e: Exception) {
            Log.w(TAG, "onCameraFrameAvailable error: ${e.message}")
        }
    }

    private fun computeRotationAndScale(dstW: Int, dstH: Int) {
        // Check if SurfaceTexture's transform matrix already contains a 90/270 rotation
        val stAlreadyRotated = Math.abs(stMatrix[1]) > 0.5f

        val devDeg = deviceOrientationDegrees
        val cwRotation = if (!stAlreadyRotated) {
            if (isFacingBack) {
                (sensorOrientation + devDeg) % 360
            } else {
                (sensorOrientation - devDeg + 360) % 360
            }
        } else {
            devDeg % 360
        }

        val totalRotated90 = if (stAlreadyRotated) {
            (cwRotation == 0 || cwRotation == 180)
        } else {
            (cwRotation == 90 || cwRotation == 270)
        }

        val uprightW = if (totalRotated90) sensorHeight else sensorWidth
        val uprightH = if (totalRotated90) sensorWidth else sensorHeight

        val srcAspect = uprightW.toFloat() / Math.max(1, uprightH).toFloat()
        val dstAspect = dstW.toFloat() / Math.max(1, dstH).toFloat()

        val scaleX: Float
        val scaleY: Float
        if (srcAspect > dstAspect) {
            // Source is wider than target -> crop left/right cleanly
            scaleX = srcAspect / dstAspect
            scaleY = 1.0f
        } else {
            // Source is taller than target -> crop top/bottom cleanly
            scaleX = 1.0f
            scaleY = dstAspect / srcAspect
        }

        Matrix.setIdentityM(mvpMatrix, 0)
        Matrix.scaleM(mvpMatrix, 0, scaleX, scaleY, 1.0f)
        if (cwRotation != 0) {
            Matrix.rotateM(mvpMatrix, 0, -cwRotation.toFloat(), 0.0f, 0.0f, 1.0f)
        }
    }

    private fun drawCurrentTexture(timestampNs: Long) {
        if (!hasValidTextureFrame) return

        // 1. Render to VideoEncoder surface ONLY if active clients are connected
        val encSurf = encoderEglSurface
        if (hasActiveClients() && encSurf != EGL14.EGL_NO_SURFACE) {
            try {
                if (EGL14.eglMakeCurrent(eglDisplay, encSurf, encSurf, eglContext)) {
                    renderQuad(encoderWidth, encoderHeight)
                    EGLExt.eglPresentationTimeANDROID(eglDisplay, encSurf, timestampNs)
                    EGL14.eglSwapBuffers(eglDisplay, encSurf)
                }
            } catch (e: Exception) {
                Log.w(TAG, "Encoder render error: ${e.message}")
            }
        }

        // 2. Render to Phone Preview surface ONLY if enabled and valid
        val prevSurf = previewEglSurface
        val rawPrev = currentPreviewRawSurface
        if (isPreviewEnabled && prevSurf != EGL14.EGL_NO_SURFACE && rawPrev != null && rawPrev.isValid) {
            try {
                if (EGL14.eglMakeCurrent(eglDisplay, prevSurf, prevSurf, eglContext)) {
                    val wArr = IntArray(1)
                    val hArr = IntArray(1)
                    EGL14.eglQuerySurface(eglDisplay, prevSurf, EGL14.EGL_WIDTH, wArr, 0)
                    EGL14.eglQuerySurface(eglDisplay, prevSurf, EGL14.EGL_HEIGHT, hArr, 0)
                    val pw = if (wArr[0] > 0) wArr[0] else 1280
                    val ph = if (hArr[0] > 0) hArr[0] else 720
                    renderQuad(pw, ph)
                    if (!EGL14.eglSwapBuffers(eglDisplay, prevSurf)) {
                        setPreviewSurfaceInternal(null)
                    }
                }
            } catch (e: Exception) {
                setPreviewSurfaceInternal(null)
            }
        }
    }

    private fun renderQuad(viewportW: Int, viewportH: Int) {
        GLES20.glViewport(0, 0, viewportW, viewportH)
        GLES20.glClearColor(0.0f, 0.0f, 0.0f, 1.0f)
        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT)

        GLES20.glUseProgram(programId)
        GLES20.glActiveTexture(GLES20.GL_TEXTURE0)
        GLES20.glBindTexture(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, oesTextureId)

        computeRotationAndScale(viewportW, viewportH)

        vertexBuffer.position(0)
        GLES20.glVertexAttribPointer(aPositionLoc, 2, GLES20.GL_FLOAT, false, 16, vertexBuffer)
        GLES20.glEnableVertexAttribArray(aPositionLoc)

        vertexBuffer.position(2)
        GLES20.glVertexAttribPointer(aTexCoordLoc, 2, GLES20.GL_FLOAT, false, 16, vertexBuffer)
        GLES20.glEnableVertexAttribArray(aTexCoordLoc)

        GLES20.glUniformMatrix4fv(uMVPMatrixLoc, 1, false, mvpMatrix, 0)
        GLES20.glUniformMatrix4fv(uSTMatrixLoc, 1, false, stMatrix, 0)

        GLES20.glDrawArrays(GLES20.GL_TRIANGLE_STRIP, 0, 4)
        GLES20.glBindTexture(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, 0)
    }

    @Synchronized
    fun stop() {
        isRunning.set(false)
        val handler = glHandler
        val thread = glThread
        if (handler != null && thread != null) {
            val latch = CountDownLatch(1)
            handler.post {
                try {
                    handler.removeCallbacksAndMessages(null)
                    try {
                        cameraSurfaceTexture?.setOnFrameAvailableListener(null)
                    } catch (_: Exception) {}
                    try {
                        cameraSurface?.release()
                    } catch (_: Exception) {}
                    cameraSurface = null
                    try {
                        cameraSurfaceTexture?.release()
                    } catch (_: Exception) {}
                    cameraSurfaceTexture = null

                    if (eglDisplay != EGL14.EGL_NO_DISPLAY) {
                        EGL14.eglMakeCurrent(eglDisplay, EGL14.EGL_NO_SURFACE, EGL14.EGL_NO_SURFACE, EGL14.EGL_NO_CONTEXT)
                        if (encoderEglSurface != EGL14.EGL_NO_SURFACE) {
                            EGL14.eglDestroySurface(eglDisplay, encoderEglSurface)
                            encoderEglSurface = EGL14.EGL_NO_SURFACE
                        }
                        if (previewEglSurface != EGL14.EGL_NO_SURFACE) {
                            EGL14.eglDestroySurface(eglDisplay, previewEglSurface)
                            previewEglSurface = EGL14.EGL_NO_SURFACE
                        }
                        if (pbufferSurface != EGL14.EGL_NO_SURFACE) {
                            EGL14.eglDestroySurface(eglDisplay, pbufferSurface)
                            pbufferSurface = EGL14.EGL_NO_SURFACE
                        }
                        if (eglContext != EGL14.EGL_NO_CONTEXT) {
                            EGL14.eglDestroyContext(eglDisplay, eglContext)
                            eglContext = EGL14.EGL_NO_CONTEXT
                        }
                        EGL14.eglTerminate(eglDisplay)
                        eglDisplay = EGL14.EGL_NO_DISPLAY
                    }
                } catch (e: Exception) {
                    Log.w(TAG, "Error releasing EGL pipeline: ${e.message}")
                } finally {
                    latch.countDown()
                }
            }
            latch.await(1, TimeUnit.SECONDS)
            thread.quitSafely()
        }
        glHandler = null
        glThread = null
    }
}
