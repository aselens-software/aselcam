package com.aselens.aselcam.network

import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

class CommandServerTest {

    private lateinit var fakeListener: FakeCommandListener
    private lateinit var server: CommandServer

    class FakeCommandListener : CommandListener {
        var torchEnabled: Boolean? = null
        var switchedCameraId: String? = null
        var zoomLevel: Float? = null
        var streamStarted = false
        var streamStopped = false

        override fun onGetDeviceInfo(): JSONObject {
            return JSONObject().apply {
                put("model", "TestDevice")
                put("battery", 95)
            }
        }

        override fun onSwitchCamera(cameraId: String) {
            switchedCameraId = cameraId
        }

        override fun onSetTorch(enabled: Boolean) {
            torchEnabled = enabled
        }

        override fun onSetZoom(zoom: Float) {
            zoomLevel = zoom
        }

        override fun onSetConfig(width: Int, height: Int, fps: Int, bitrate: Int, codec: String) {}
        override fun onSetMute(muted: Boolean) {}
        override fun onSetAudioGain(gain: Float) {}
        override fun onSetPreviewEnabled(enabled: Boolean) {}
        override fun onSetCameraEnabled(enabled: Boolean) {}
        override fun onSetBlackout(enabled: Boolean) {}
        override fun onSetScreenMirror(enabled: Boolean) {}

        override fun onStartStream() {
            streamStarted = true
        }

        override fun onStopStream() {
            streamStopped = true
        }
    }

    @Before
    fun setUp() {
        fakeListener = FakeCommandListener()
        server = CommandServer(port = 4748, listener = fakeListener)
    }

    @Test
    fun testPingCommandReturnsPong() {
        val req = JSONObject().put("cmd", "ping").toString()
        val responseStr = server.processCommand(req)
        val res = JSONObject(responseStr)

        assertEquals("pong", res.getString("status"))
        assertTrue(res.has("timestamp"))
    }

    @Test
    fun testGetInfoReturnsDeviceInfo() {
        val req = JSONObject().put("cmd", "get_info").toString()
        val responseStr = server.processCommand(req)
        val res = JSONObject(responseStr)

        assertEquals("ok", res.getString("status"))
        val data = res.getJSONObject("data")
        assertEquals("TestDevice", data.getString("model"))
        assertEquals(95, data.getInt("battery"))
    }

    @Test
    fun testSetTorchInvokesListener() {
        val req = JSONObject().apply {
            put("cmd", "set_torch")
            put("enabled", true)
        }.toString()

        val responseStr = server.processCommand(req)
        val res = JSONObject(responseStr)

        assertEquals("ok", res.getString("status"))
        assertEquals(true, fakeListener.torchEnabled)
    }

    @Test
    fun testSetZoomInvokesListener() {
        val req = JSONObject().apply {
            put("cmd", "set_zoom")
            put("zoom", 2.5)
        }.toString()

        val responseStr = server.processCommand(req)
        val res = JSONObject(responseStr)

        assertEquals("ok", res.getString("status"))
        assertEquals(2.5f, fakeListener.zoomLevel ?: 0f, 0.001f)
    }

    @Test
    fun testDefaultRateLimitValue() {
        assertEquals(CommandServer.DEFAULT_MAX_COMMANDS_PER_SEC, server.maxCommandsPerSecond)

        val getReq = JSONObject().put("cmd", "get_rate_limit").toString()
        val res = JSONObject(server.processCommand(getReq))
        assertEquals("ok", res.getString("status"))
        assertEquals(30, res.getInt("limit"))
    }

    @Test
    fun testConfigureRateLimitWithinValidBounds() {
        val setReq = JSONObject().apply {
            put("cmd", "set_rate_limit")
            put("limit", 60)
        }.toString()

        val res = JSONObject(server.processCommand(setReq))
        assertEquals("ok", res.getString("status"))
        assertEquals(60, res.getInt("limit"))
        assertEquals(60, server.maxCommandsPerSecond)
    }

    @Test
    fun testConfigureRateLimitInvalidBoundsRejection() {
        val setReq = JSONObject().apply {
            put("cmd", "set_rate_limit")
            put("limit", 9999)
        }.toString()

        val res = JSONObject(server.processCommand(setReq))
        assertEquals("error", res.getString("status"))
        assertTrue(res.getString("message").contains("between 1 and 500"))
    }

    @Test
    fun testUnknownCommandReturnsError() {
        val req = JSONObject().put("cmd", "non_existent_command").toString()
        val res = JSONObject(server.processCommand(req))

        assertEquals("error", res.getString("status"))
        assertTrue(res.getString("message").contains("Unknown command"))
    }
}
