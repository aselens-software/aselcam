package com.aselcam.app

import android.Manifest
import android.app.Activity
import android.content.ClipData
import android.content.ClipboardManager
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.ServiceConnection
import android.content.pm.PackageManager
import android.media.projection.MediaProjectionManager
import android.os.Build
import android.os.Bundle
import android.os.IBinder
import android.view.SurfaceHolder
import android.view.SurfaceView
import android.view.WindowManager
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.Image
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.ui.res.painterResource
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import com.aselcam.app.camera.CameraInfo
import com.aselcam.app.camera.CameraManagerHelper
import com.aselcam.app.service.CameraStreamService
import java.net.Inet4Address
import java.net.NetworkInterface

// Obsidian Stream Studio Design System Color Tokens (Synchronized with Stitch)
private val ObsidianCanvas = Color(0xFF0F131D)
private val ObsidianLowest = Color(0xFF0A0E18)
private val ObsidianLow = Color(0xFF171B26)
private val ObsidianCard = Color(0xFF1C1F2A)
private val ObsidianHigh = Color(0xFF262A35)
private val ObsidianHighest = Color(0xFF313540)
private val ObsidianBorder = Color(0x33424754)
private val ObsidianBorderSubtle = Color(0x1FFFFFFF)

private val MintNeon = Color(0xFF4EDEA3)
private val MintDark = Color(0xFF00A572)
private val MintText = Color(0xFF00311F)
private val SkyCyan = Color(0xFF4CD7F6)
private val PrimaryBlue = Color(0xFF4D8EFF)
private val PrimaryLight = Color(0xFFADC6FF)
private val TextPrimary = Color(0xFFDFE2F1)
private val TextSecondary = Color(0xFF8C909F)
private val TextMuted = Color(0xFF6B7280)
private val ErrorRed = Color(0xFFEF4444)
private val ErrorContainer = Color(0x33EF4444)

class MainActivity : ComponentActivity() {

    private var streamService by mutableStateOf<CameraStreamService?>(null)
    private var hasCameraPermission by mutableStateOf(false)
    private var isBound = false

    private val serviceConnection = object : ServiceConnection {
        override fun onServiceConnected(name: ComponentName?, service: IBinder?) {
            val binder = service as CameraStreamService.LocalBinder
            streamService = binder.getService()
            isBound = true
        }

        override fun onServiceDisconnected(name: ComponentName?) {
            streamService = null
            isBound = false
        }
    }

    private val permissionsLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { _ ->
        hasCameraPermission = ContextCompat.checkSelfPermission(
            this,
            Manifest.permission.CAMERA
        ) == PackageManager.PERMISSION_GRANTED
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        hasCameraPermission = ContextCompat.checkSelfPermission(
            this,
            Manifest.permission.CAMERA
        ) == PackageManager.PERMISSION_GRANTED

        requestPermissions()

        val serviceIntent = Intent(this, CameraStreamService::class.java)
        startService(serviceIntent)
        bindService(serviceIntent, serviceConnection, Context.BIND_AUTO_CREATE)
        handleIntentExtras(intent)

        setContent {
            AselCamApp(
                activity = this,
                service = streamService,
                hasCameraPermission = hasCameraPermission,
                onStartStream = { camId, w, h, fps, br, codec, surface ->
                    streamService?.startStreaming(camId, w, h, fps, br, codec, surface)
                },
                onStopStream = {
                    streamService?.userStoppedManually = true
                    streamService?.stopStreaming()
                },
                onBlackout = {
                    CameraStreamService.isBlackoutGlobal.value = true
                },
                onRequestScreenCapture = {
                    requestScreenCapture()
                }
            )
        }
    }

    private fun requestPermissions() {
        val permissions = mutableListOf(
            Manifest.permission.CAMERA,
            Manifest.permission.RECORD_AUDIO
        )
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            permissions.add(Manifest.permission.POST_NOTIFICATIONS)
        }

        val needed = permissions.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }
        if (needed.isNotEmpty()) {
            permissionsLauncher.launch(needed.toTypedArray())
        }
    }

    private val projectionManager: MediaProjectionManager by lazy {
        getSystemService(Context.MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
    }

    private val screenCaptureLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == Activity.RESULT_OK && result.data != null) {
            val srv = streamService ?: CameraStreamService.instance
            if (srv != null) {
                srv.startScreenMirroring(result.resultCode, result.data!!)
            } else {
                Toast.makeText(this, "Yayın servisi henüz hazır değil", Toast.LENGTH_SHORT).show()
            }
        } else {
            Toast.makeText(this, "Ekran yansıtma izni verilmedi veya iptal edildi", Toast.LENGTH_SHORT).show()
        }
    }

    fun requestScreenCapture() {
        try {
            screenCaptureLauncher.launch(projectionManager.createScreenCaptureIntent())
        } catch (e: Exception) {
            Toast.makeText(this, "Ekran izni isteği başlatılamadı: ${e.message}", Toast.LENGTH_SHORT).show()
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleIntentExtras(intent)
    }

    private fun handleIntentExtras(intent: Intent?) {
        if (intent?.getBooleanExtra(EXTRA_REQUEST_SCREEN_CAPTURE, false) == true) {
            requestScreenCapture()
        }
    }

    override fun onDestroy() {
        if (isBound) {
            unbindService(serviceConnection)
            isBound = false
        }
        super.onDestroy()
    }

    companion object {
        const val EXTRA_REQUEST_SCREEN_CAPTURE = "extra_request_screen_capture"
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AselCamApp(
    activity: Activity,
    service: CameraStreamService?,
    hasCameraPermission: Boolean,
    onStartStream: (String, Int, Int, Int, Int, String, android.view.Surface?) -> Unit,
    onStopStream: () -> Unit,
    onBlackout: () -> Unit,
    onRequestScreenCapture: () -> Unit
) {
    val context = LocalContext.current
    val cameras = remember(hasCameraPermission) { CameraManagerHelper.getAvailableCameras(context) }

    val isStreaming by CameraStreamService.isStreamingGlobal.collectAsState()
    val isScreenMirroring by CameraStreamService.isScreenMirroringGlobal.collectAsState()
    val selectedCameraId by CameraStreamService.currentCameraIdGlobal.collectAsState()
    val isPreviewEnabled by CameraStreamService.isPreviewGlobal.collectAsState()
    val isTorchEnabled by CameraStreamService.isTorchGlobal.collectAsState()
    val isCameraEnabled by CameraStreamService.isCameraEnabledGlobal.collectAsState()
    val isMuted by CameraStreamService.isMutedGlobal.collectAsState()
    val isBlackout by CameraStreamService.isBlackoutGlobal.collectAsState()
    val selectedResolution by CameraStreamService.currentResolutionGlobal.collectAsState()
    val selectedFps by CameraStreamService.currentFpsGlobal.collectAsState()
    val globalBitrateMbps by CameraStreamService.currentBitrateMbpsGlobal.collectAsState()
    val selectedCodec by CameraStreamService.currentCodecGlobal.collectAsState()

    var selectedBitrateMbps by remember(globalBitrateMbps) { mutableStateOf(globalBitrateMbps) }
    var audioGain by remember { mutableStateOf(1.0f) }

    var surfaceHolder by remember { mutableStateOf<SurfaceHolder?>(null) }

    val currentCamera = cameras.find { it.id == selectedCameraId } ?: cameras.firstOrNull()
    val localIp = remember { getLocalIpAddress(context) }

    val copyToClipboard: (String, String) -> Unit = { label, text ->
        val cm = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        cm.setPrimaryClip(ClipData.newPlainText(label, text))
        Toast.makeText(context, "$label kopyalandı", Toast.LENGTH_SHORT).show()
    }

    // Synchronize preview surface and auto-start streaming when ready
    LaunchedEffect(service, surfaceHolder, hasCameraPermission) {
        val srv = service ?: return@LaunchedEffect
        val holder = surfaceHolder
        if (holder != null && holder.surface.isValid) {
            srv.setPreviewSurface(holder.surface)
        }
        if (hasCameraPermission && !srv.isStreaming.value && !srv.userStoppedManually) {
            val parts = selectedResolution.split("x")
            val w = parts.getOrNull(0)?.toIntOrNull() ?: 1920
            val h = parts.getOrNull(1)?.toIntOrNull() ?: 1080
            val br = (selectedBitrateMbps * 1_000_000).toInt()
            srv.startStreaming(
                cameraId = selectedCameraId,
                width = w,
                height = h,
                fps = selectedFps,
                bitrate = br,
                codec = selectedCodec,
                previewSurface = if (isPreviewEnabled && holder?.surface?.isValid == true) holder.surface else null
            )
        }
    }

    // Handle AMOLED Blackout screen brightness in-place without pausing Activity or destroying SurfaceView
    LaunchedEffect(isBlackout) {
        val window = activity.window
        val lp = window.attributes
        lp.screenBrightness = if (isBlackout) 0.01f else WindowManager.LayoutParams.BRIGHTNESS_OVERRIDE_NONE
        window.attributes = lp
    }

    val applyLiveConfig: (String, Int, Float, String) -> Unit = { resStr, fpsVal, bitrateMbps, codecVal ->
        val parts = resStr.split("x")
        val w = parts.getOrNull(0)?.toIntOrNull() ?: 1920
        val h = parts.getOrNull(1)?.toIntOrNull() ?: 1080
        val br = (bitrateMbps * 1_000_000).toInt()
        CameraStreamService.currentResolutionGlobal.value = resStr
        CameraStreamService.currentFpsGlobal.value = fpsVal
        CameraStreamService.currentBitrateMbpsGlobal.value = bitrateMbps
        CameraStreamService.currentCodecGlobal.value = codecVal
        if (isStreaming) {
            service?.onSetConfig(w, h, fpsVal, br, codecVal)
        }
    }

    MaterialTheme(
        colorScheme = darkColorScheme(
            primary = PrimaryLight,
            secondary = MintNeon,
            background = ObsidianCanvas,
            surface = ObsidianLow,
            onPrimary = Color(0xFF00285D),
            onBackground = TextPrimary,
            onSurface = TextPrimary
        )
    ) {
        Box(modifier = Modifier.fillMaxSize().background(ObsidianCanvas)) {
            Scaffold(
                topBar = {
                    Surface(
                        color = ObsidianLowest,
                        border = BorderStroke(1.dp, ObsidianBorderSubtle)
                    ) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .statusBarsPadding()
                                .padding(horizontal = 16.dp, vertical = 10.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Box(
                                    modifier = Modifier
                                        .size(36.dp)
                                        .clip(RoundedCornerShape(8.dp))
                                        .background(ObsidianHigh)
                                        .border(1.dp, ObsidianBorder, RoundedCornerShape(8.dp)),
                                    contentAlignment = Alignment.Center
                                ) {
                                    Image(
                                        painter = painterResource(id = R.drawable.aselcam_logo_icon),
                                        contentDescription = "AselCam",
                                        modifier = Modifier.size(24.dp)
                                    )
                                }
                                Spacer(modifier = Modifier.width(10.dp))
                                Column {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        Text(
                                            "AselCam",
                                            fontWeight = FontWeight.Bold,
                                            fontSize = 18.sp,
                                            color = TextPrimary
                                        )
                                        Spacer(modifier = Modifier.width(6.dp))
                                        Surface(
                                            color = ObsidianHigh,
                                            shape = RoundedCornerShape(4.dp),
                                            border = BorderStroke(1.dp, ObsidianBorder)
                                        ) {
                                            Text(
                                                "v1.2",
                                                fontFamily = FontFamily.Monospace,
                                                fontSize = 9.sp,
                                                fontWeight = FontWeight.SemiBold,
                                                color = TextSecondary,
                                                modifier = Modifier.padding(horizontal = 4.dp, vertical = 1.dp)
                                            )
                                        }
                                    }
                                    Text(
                                        "Companion Streamer",
                                        fontFamily = FontFamily.Monospace,
                                        fontSize = 10.sp,
                                        color = TextSecondary
                                    )
                                }
                            }

                            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                // Status Pill Badge
                                Surface(
                                    color = if (isStreaming) Color(0x22EF4444) else Color(0x224EDEA3),
                                    shape = RoundedCornerShape(12.dp),
                                    border = BorderStroke(1.dp, if (isStreaming) Color(0x55EF4444) else Color(0x554EDEA3))
                                ) {
                                    Row(
                                        verticalAlignment = Alignment.CenterVertically,
                                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                                    ) {
                                        Box(
                                            modifier = Modifier
                                                .size(6.dp)
                                                .clip(CircleShape)
                                                .background(if (isStreaming) ErrorRed else MintNeon)
                                        )
                                        Spacer(modifier = Modifier.width(5.dp))
                                        Text(
                                            text = if (isStreaming) "YAYINDA" else "BEKLEMEDE",
                                            fontSize = 10.sp,
                                            fontWeight = FontWeight.Bold,
                                            fontFamily = FontFamily.Monospace,
                                            color = if (isStreaming) ErrorRed else MintNeon
                                        )
                                    }
                                }

                                // AMOLED Blackout Quick Icon
                                IconButton(
                                    onClick = onBlackout,
                                    modifier = Modifier
                                        .size(34.dp)
                                        .clip(RoundedCornerShape(8.dp))
                                        .background(ObsidianLow)
                                        .border(1.dp, ObsidianBorder, RoundedCornerShape(8.dp))
                                ) {
                                    Icon(
                                        Icons.Default.DarkMode,
                                        contentDescription = "Ekranı Karart",
                                        tint = TextSecondary,
                                        modifier = Modifier.size(18.dp)
                                    )
                                }
                            }
                        }
                    }
                },
                containerColor = ObsidianCanvas
            ) { padding ->
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(padding)
                        .verticalScroll(rememberScrollState())
                        .padding(14.dp),
                    verticalArrangement = Arrangement.spacedBy(14.dp)
                ) {
                    // Hero Viewfinder Card (Obsidian Frame)
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(230.dp)
                            .clip(RoundedCornerShape(14.dp))
                            .background(ObsidianLowest)
                            .border(1.dp, ObsidianBorder, RoundedCornerShape(14.dp)),
                        contentAlignment = Alignment.Center
                    ) {
                        AndroidView(
                            factory = { ctx ->
                                SurfaceView(ctx).apply {
                                    holder.addCallback(object : SurfaceHolder.Callback {
                                        override fun surfaceCreated(holder: SurfaceHolder) {
                                            surfaceHolder = holder
                                            service?.setPreviewSurface(holder.surface)
                                        }

                                        override fun surfaceChanged(holder: SurfaceHolder, format: Int, width: Int, height: Int) {
                                            surfaceHolder = holder
                                            service?.setPreviewSurface(holder.surface)
                                        }

                                        override fun surfaceDestroyed(holder: SurfaceHolder) {
                                            surfaceHolder = null
                                            service?.setPreviewSurface(null)
                                        }
                                    })
                                }
                            },
                            modifier = Modifier.fillMaxSize()
                        )

                        // Top Viewfinder HUD
                        Row(
                            modifier = Modifier
                                .align(Alignment.TopCenter)
                                .fillMaxWidth()
                                .padding(8.dp),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Surface(
                                color = Color(0xCC0A0E18),
                                shape = RoundedCornerShape(6.dp),
                                border = BorderStroke(1.dp, ObsidianBorder)
                            ) {
                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                                ) {
                                    Box(
                                        modifier = Modifier
                                            .size(6.dp)
                                            .clip(CircleShape)
                                            .background(if (isStreaming) ErrorRed else Color(0xFF64748B))
                                    )
                                    Spacer(modifier = Modifier.width(4.dp))
                                    Text(
                                        text = if (isStreaming) "CANLI" else "00:00:00",
                                        fontFamily = FontFamily.Monospace,
                                        fontSize = 10.sp,
                                        color = TextSecondary
                                    )
                                }
                            }

                            Surface(
                                color = Color(0xCC0A0E18),
                                shape = RoundedCornerShape(6.dp),
                                border = BorderStroke(1.dp, ObsidianBorder)
                            ) {
                                Text(
                                    text = "$selectedResolution · $selectedFps FPS",
                                    fontFamily = FontFamily.Monospace,
                                    fontWeight = FontWeight.SemiBold,
                                    fontSize = 10.sp,
                                    color = MintNeon,
                                    modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                                )
                            }
                        }

                        // Standby, Screen Mirroring or Hardware Mute Slates
                        if (isScreenMirroring) {
                            Column(
                                horizontalAlignment = Alignment.CenterHorizontally,
                                verticalArrangement = Arrangement.Center,
                                modifier = Modifier
                                    .fillMaxSize()
                                    .background(ObsidianLowest)
                                    .padding(16.dp)
                            ) {
                                Icon(
                                    Icons.Default.ScreenShare,
                                    contentDescription = null,
                                    tint = SkyCyan,
                                    modifier = Modifier.size(38.dp)
                                )
                                Spacer(modifier = Modifier.height(6.dp))
                                Text(
                                    text = "Telefon Ekranı Yayında",
                                    fontWeight = FontWeight.Bold,
                                    color = SkyCyan,
                                    fontSize = 14.sp
                                )
                                Text(
                                    text = "Cihaz ekranınız bilgisayara aktarılıyor",
                                    color = TextSecondary,
                                    fontSize = 11.sp
                                )
                                Spacer(modifier = Modifier.height(8.dp))
                                Surface(
                                    color = ObsidianHigh,
                                    shape = RoundedCornerShape(8.dp),
                                    border = BorderStroke(1.dp, SkyCyan),
                                    modifier = Modifier.clickable { service?.stopScreenMirroring() }
                                ) {
                                    Text(
                                        "Kameraya Dön",
                                        color = SkyCyan,
                                        fontSize = 12.sp,
                                        fontWeight = FontWeight.SemiBold,
                                        modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp)
                                    )
                                }
                            }
                        } else if (!isCameraEnabled) {
                            Column(
                                horizontalAlignment = Alignment.CenterHorizontally,
                                verticalArrangement = Arrangement.Center,
                                modifier = Modifier
                                    .fillMaxSize()
                                    .background(ObsidianLowest)
                                    .padding(16.dp)
                            ) {
                                Icon(
                                    Icons.Default.VideocamOff,
                                    contentDescription = null,
                                    tint = ErrorRed,
                                    modifier = Modifier.size(36.dp)
                                )
                                Spacer(modifier = Modifier.height(6.dp))
                                Text(
                                    text = "Kamera Donanımı Kapalı",
                                    fontWeight = FontWeight.Bold,
                                    color = Color(0xFFFCA5A5),
                                    fontSize = 14.sp
                                )
                                Text(
                                    text = "Sensör ve donanım kodlayıcı kapatıldı (Pil & Ağ Tasarrufu)",
                                    color = TextSecondary,
                                    fontSize = 11.sp
                                )
                            }
                        } else if (!isPreviewEnabled) {
                            Column(
                                horizontalAlignment = Alignment.CenterHorizontally,
                                verticalArrangement = Arrangement.Center,
                                modifier = Modifier
                                    .fillMaxSize()
                                    .background(ObsidianLowest)
                                    .padding(16.dp)
                            ) {
                                Icon(
                                    Icons.Default.VisibilityOff,
                                    contentDescription = null,
                                    tint = SkyCyan,
                                    modifier = Modifier.size(36.dp)
                                )
                                Spacer(modifier = Modifier.height(6.dp))
                                Text(
                                    text = "Önizleme Devre Dışı",
                                    fontWeight = FontWeight.Bold,
                                    color = TextPrimary,
                                    fontSize = 14.sp
                                )
                                Text(
                                    text = "GPU & Ekran tasarruf modu devrede. Yayın devam ediyor.",
                                    color = TextSecondary,
                                    fontSize = 11.sp
                                )
                            }
                        }

                        // Floating Quick Action Toolbelt at Bottom of Preview
                        Row(
                            modifier = Modifier
                                .align(Alignment.BottomCenter)
                                .fillMaxWidth()
                                .padding(6.dp)
                                .clip(RoundedCornerShape(10.dp))
                                .background(Color(0xEE0A0E18))
                                .border(1.dp, ObsidianBorder, RoundedCornerShape(10.dp))
                                .padding(vertical = 4.dp, horizontal = 2.dp),
                            horizontalArrangement = Arrangement.SpaceEvenly,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            // 1. Flip Camera
                            Column(
                                horizontalAlignment = Alignment.CenterHorizontally,
                                modifier = Modifier
                                    .clip(RoundedCornerShape(6.dp))
                                    .clickable {
                                        if (cameras.isNotEmpty()) {
                                            val idx = cameras.indexOfFirst { it.id == selectedCameraId }
                                            val nextCam = cameras[(idx + 1) % cameras.size]
                                            service?.onSwitchCamera(nextCam.id)
                                        }
                                    }
                                    .padding(horizontal = 6.dp, vertical = 2.dp)
                            ) {
                                Icon(Icons.Default.Cameraswitch, "Çevir", tint = TextPrimary, modifier = Modifier.size(18.dp))
                                Text("Çevir", fontSize = 9.sp, color = TextSecondary)
                            }

                            // 2. Camera Sensor Power Toggle
                            Column(
                                horizontalAlignment = Alignment.CenterHorizontally,
                                modifier = Modifier
                                    .clip(RoundedCornerShape(6.dp))
                                    .clickable {
                                        val newVal = !isCameraEnabled
                                        service?.onSetCameraEnabled(newVal)
                                    }
                                    .padding(horizontal = 6.dp, vertical = 2.dp)
                            ) {
                                Icon(
                                    if (isCameraEnabled) Icons.Default.Videocam else Icons.Default.VideocamOff,
                                    "Kamera",
                                    tint = if (isCameraEnabled) MintNeon else ErrorRed,
                                    modifier = Modifier.size(18.dp)
                                )
                                Text("Kamera", fontSize = 9.sp, color = if (isCameraEnabled) MintNeon else ErrorRed)
                            }

                            // 3. Preview Power Save Toggle
                            Column(
                                horizontalAlignment = Alignment.CenterHorizontally,
                                modifier = Modifier
                                    .clip(RoundedCornerShape(6.dp))
                                    .clickable {
                                        val newVal = !isPreviewEnabled
                                        service?.onSetPreviewEnabled(newVal)
                                    }
                                    .padding(horizontal = 6.dp, vertical = 2.dp)
                            ) {
                                Icon(
                                    if (isPreviewEnabled) Icons.Default.Visibility else Icons.Default.VisibilityOff,
                                    "Önizleme",
                                    tint = if (isPreviewEnabled) SkyCyan else ErrorRed,
                                    modifier = Modifier.size(18.dp)
                                )
                                Text("Önizleme", fontSize = 9.sp, color = if (isPreviewEnabled) SkyCyan else ErrorRed)
                            }

                            // 4. Torch / Flashlight Toggle
                            Column(
                                horizontalAlignment = Alignment.CenterHorizontally,
                                modifier = Modifier
                                    .clip(RoundedCornerShape(6.dp))
                                    .clickable {
                                        val newVal = !isTorchEnabled
                                        service?.onSetTorch(newVal)
                                    }
                                    .padding(horizontal = 6.dp, vertical = 2.dp)
                            ) {
                                Icon(
                                    if (isTorchEnabled) Icons.Default.FlashOn else Icons.Default.FlashOff,
                                    "Flaş",
                                    tint = if (isTorchEnabled) Color(0xFFFBBF24) else TextSecondary,
                                    modifier = Modifier.size(18.dp)
                                )
                                Text("Flaş", fontSize = 9.sp, color = if (isTorchEnabled) Color(0xFFFBBF24) else TextSecondary)
                            }

                            // 5. Mic Mute Toggle
                            Column(
                                horizontalAlignment = Alignment.CenterHorizontally,
                                modifier = Modifier
                                    .clip(RoundedCornerShape(6.dp))
                                    .clickable {
                                        val newVal = !isMuted
                                        service?.onSetMute(newVal)
                                    }
                                    .padding(horizontal = 6.dp, vertical = 2.dp)
                            ) {
                                Icon(
                                    if (isMuted) Icons.Default.MicOff else Icons.Default.Mic,
                                    "Mikrofon",
                                    tint = if (isMuted) ErrorRed else MintNeon,
                                    modifier = Modifier.size(18.dp)
                                )
                                Text("Mikrofon", fontSize = 9.sp, color = if (isMuted) ErrorRed else MintNeon)
                            }

                            // 6. AMOLED Blackout
                            Column(
                                horizontalAlignment = Alignment.CenterHorizontally,
                                modifier = Modifier
                                    .clip(RoundedCornerShape(6.dp))
                                    .clickable { onBlackout() }
                                    .padding(horizontal = 6.dp, vertical = 2.dp)
                            ) {
                                Icon(Icons.Default.PowerSettingsNew, "Karart", tint = Color(0xFFA78BFA), modifier = Modifier.size(18.dp))
                                Text("Karart", fontSize = 9.sp, color = Color(0xFFA78BFA))
                            }

                            // 7. Screen Mirroring
                            Column(
                                horizontalAlignment = Alignment.CenterHorizontally,
                                modifier = Modifier
                                    .clip(RoundedCornerShape(6.dp))
                                    .clickable {
                                        if (isScreenMirroring) {
                                            service?.stopScreenMirroring()
                                        } else {
                                            onRequestScreenCapture()
                                        }
                                    }
                                    .padding(horizontal = 6.dp, vertical = 2.dp)
                            ) {
                                Icon(
                                    if (isScreenMirroring) Icons.Default.ScreenShare else Icons.Default.StopScreenShare,
                                    "Ekran Yansıt",
                                    tint = if (isScreenMirroring) SkyCyan else TextSecondary,
                                    modifier = Modifier.size(18.dp)
                                )
                                Text(
                                    if (isScreenMirroring) "Yansıtılıyor" else "Ekran",
                                    fontSize = 9.sp,
                                    color = if (isScreenMirroring) SkyCyan else TextSecondary
                                )
                            }
                        }
                    }

                    // Primary Action Launch Button (Cyber Mint Glow Action)
                    Button(
                        onClick = {
                            if (isStreaming) {
                                onStopStream()
                            } else {
                                val parts = selectedResolution.split("x")
                                val w = parts.getOrNull(0)?.toIntOrNull() ?: 1920
                                val h = parts.getOrNull(1)?.toIntOrNull() ?: 1080
                                val br = (selectedBitrateMbps * 1_000_000).toInt()
                                onStartStream(
                                    selectedCameraId,
                                    w,
                                    h,
                                    selectedFps,
                                    br,
                                    selectedCodec,
                                    if (isPreviewEnabled) surfaceHolder?.surface else null
                                )
                            }
                        },
                        colors = ButtonDefaults.buttonColors(
                            containerColor = if (isStreaming) ErrorRed else MintNeon,
                            contentColor = if (isStreaming) Color.White else MintText
                        ),
                        shape = RoundedCornerShape(12.dp),
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(50.dp)
                    ) {
                        Icon(
                            if (isStreaming) Icons.Default.Stop else Icons.Default.PlayArrow,
                            contentDescription = null,
                            modifier = Modifier.size(22.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = if (isStreaming) "YAYINI DURDUR" else "YAYINI BAŞLAT",
                            fontWeight = FontWeight.Bold,
                            fontSize = 15.sp,
                            letterSpacing = 0.5.sp
                        )
                    }

                    // Connection Info Card ('Bağlantı Bilgileri')
                    Card(
                        colors = CardDefaults.cardColors(containerColor = ObsidianLow),
                        shape = RoundedCornerShape(14.dp),
                        border = BorderStroke(1.dp, ObsidianBorder),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Icon(Icons.Default.Sensors, null, tint = PrimaryLight, modifier = Modifier.size(18.dp))
                                    Spacer(modifier = Modifier.width(6.dp))
                                    Text("Bağlantı Bilgileri", fontWeight = FontWeight.Bold, color = TextPrimary, fontSize = 14.sp)
                                }
                                Surface(
                                    color = ObsidianHigh,
                                    shape = RoundedCornerShape(4.dp),
                                    border = BorderStroke(1.dp, ObsidianBorder)
                                ) {
                                    Text(
                                        "Yerel Ağ Hazır",
                                        fontFamily = FontFamily.Monospace,
                                        fontSize = 10.sp,
                                        color = MintNeon,
                                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                                    )
                                }
                            }

                            // Wi-Fi Module
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .clip(RoundedCornerShape(8.dp))
                                    .background(ObsidianLowest)
                                    .border(1.dp, ObsidianBorderSubtle, RoundedCornerShape(8.dp))
                                    .padding(10.dp),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Box(
                                        modifier = Modifier
                                            .size(32.dp)
                                            .clip(RoundedCornerShape(6.dp))
                                            .background(ObsidianHigh),
                                        contentAlignment = Alignment.Center
                                    ) {
                                        Icon(Icons.Default.Wifi, null, tint = PrimaryLight, modifier = Modifier.size(18.dp))
                                    }
                                    Spacer(modifier = Modifier.width(10.dp))
                                    Column {
                                        Text("Wi-Fi IP Adresi", fontSize = 11.sp, color = TextSecondary)
                                        Text(localIp, fontSize = 13.sp, fontWeight = FontWeight.SemiBold, fontFamily = FontFamily.Monospace, color = TextPrimary)
                                    }
                                }
                                Surface(
                                    color = ObsidianHigh,
                                    shape = RoundedCornerShape(6.dp),
                                    border = BorderStroke(1.dp, ObsidianBorder),
                                    modifier = Modifier.clickable { copyToClipboard("Wi-Fi IP", localIp) }
                                ) {
                                    Row(
                                        verticalAlignment = Alignment.CenterVertically,
                                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                                    ) {
                                        Icon(Icons.Default.ContentCopy, null, tint = PrimaryLight, modifier = Modifier.size(12.dp))
                                        Spacer(modifier = Modifier.width(4.dp))
                                        Text("Kopyala", fontSize = 11.sp, color = PrimaryLight)
                                    }
                                }
                            }

                            // USB (ADB) Terminal Tunnel
                            Column(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .clip(RoundedCornerShape(8.dp))
                                    .background(ObsidianLowest)
                                    .border(1.dp, ObsidianBorderSubtle, RoundedCornerShape(8.dp))
                                    .padding(10.dp),
                                verticalArrangement = Arrangement.spacedBy(6.dp)
                            ) {
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        Icon(Icons.Default.Usb, null, tint = SkyCyan, modifier = Modifier.size(16.dp))
                                        Spacer(modifier = Modifier.width(6.dp))
                                        Text("USB (ADB) Terminal Tüneli", fontSize = 11.sp, color = TextSecondary)
                                    }
                                    Surface(
                                        color = ObsidianHigh,
                                        shape = RoundedCornerShape(4.dp),
                                        modifier = Modifier.clickable { copyToClipboard("ADB Komutu", "adb forward tcp:4747 tcp:4747") }
                                    ) {
                                        Row(
                                            verticalAlignment = Alignment.CenterVertically,
                                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                                        ) {
                                            Icon(Icons.Default.Terminal, null, tint = SkyCyan, modifier = Modifier.size(12.dp))
                                            Spacer(modifier = Modifier.width(4.dp))
                                            Text("Komut", fontSize = 10.sp, color = SkyCyan)
                                        }
                                    }
                                }

                                Row(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .clip(RoundedCornerShape(4.dp))
                                        .background(ObsidianHigh)
                                        .border(1.dp, ObsidianBorder, RoundedCornerShape(4.dp))
                                        .padding(horizontal = 8.dp, vertical = 6.dp),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Text(
                                        "adb forward tcp:4747 tcp:4747",
                                        fontFamily = FontFamily.Monospace,
                                        fontSize = 11.sp,
                                        color = SkyCyan
                                    )
                                    Icon(
                                        Icons.Default.ContentCopy,
                                        contentDescription = "Kopyala",
                                        tint = TextSecondary,
                                        modifier = Modifier
                                            .size(14.dp)
                                            .clickable { copyToClipboard("ADB Komutu", "adb forward tcp:4747 tcp:4747") }
                                    )
                                }
                            }
                        }
                    }

                    // Detailed Stream & Quality Settings Card ('Ayrıntılı Kalite & Akış Ayarları')
                    Card(
                        colors = CardDefaults.cardColors(containerColor = ObsidianLow),
                        shape = RoundedCornerShape(14.dp),
                        border = BorderStroke(1.dp, ObsidianBorder),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(Icons.Default.Tune, null, tint = PrimaryLight, modifier = Modifier.size(18.dp))
                                Spacer(modifier = Modifier.width(6.dp))
                                Text("Ayrıntılı Kalite & Akış Ayarları", fontWeight = FontWeight.Bold, color = TextPrimary, fontSize = 14.sp)
                            }

                            // 1. Camera Selector
                            Text("Kamera Seçimi:", color = TextSecondary, fontSize = 12.sp)
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .horizontalScroll(rememberScrollState()),
                                horizontalArrangement = Arrangement.spacedBy(6.dp)
                            ) {
                                for (cam in cameras) {
                                    val isSelected = selectedCameraId == cam.id
                                    Surface(
                                        color = if (isSelected) ObsidianHigh else ObsidianLowest,
                                        shape = RoundedCornerShape(8.dp),
                                        border = BorderStroke(1.dp, if (isSelected) PrimaryLight else ObsidianBorder),
                                        modifier = Modifier.clickable { service?.onSwitchCamera(cam.id) }
                                    ) {
                                        Text(
                                            text = cam.name,
                                            fontSize = 12.sp,
                                            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
                                            color = if (isSelected) PrimaryLight else TextSecondary,
                                            modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp)
                                        )
                                    }
                                }
                            }

                            // 2. Aspect Ratio & Orientation Quick Selector (16:9, 9:16, 4:3, 3:4, 1:1)
                            Text("En-Boy Oranı & Yön:", color = TextSecondary, fontSize = 12.sp)
                            val aspectPresets = listOf(
                                "16:9 Yatay" to "1920x1080",
                                "9:16 Dikey" to "1080x1920",
                                "4:3 Yatay" to "1440x1080",
                                "3:4 Dikey" to "1080x1440",
                                "1:1 Kare" to "1080x1080"
                            )
                            val resParts = selectedResolution.split("x")
                            val curW = resParts.getOrNull(0)?.toIntOrNull() ?: 1920
                            val curH = resParts.getOrNull(1)?.toIntOrNull() ?: 1080
                            val curRatio = curW.toFloat() / maxOf(1, curH).toFloat()

                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .horizontalScroll(rememberScrollState()),
                                horizontalArrangement = Arrangement.spacedBy(6.dp)
                            ) {
                                for ((ratioLabel, defaultRes) in aspectPresets) {
                                    val isRatioSelected = when (ratioLabel) {
                                        "16:9 Yatay" -> curRatio > 1.6f
                                        "9:16 Dikey" -> curRatio < 0.65f
                                        "4:3 Yatay" -> curRatio in 1.2f..1.6f
                                        "3:4 Dikey" -> curRatio in 0.65f..0.85f
                                        "1:1 Kare" -> curRatio in 0.9f..1.1f
                                        else -> false
                                    }
                                    Surface(
                                        color = if (isRatioSelected) ObsidianHigh else ObsidianLowest,
                                        shape = RoundedCornerShape(8.dp),
                                        border = BorderStroke(1.dp, if (isRatioSelected) PrimaryLight else ObsidianBorder),
                                        modifier = Modifier.clickable {
                                            applyLiveConfig(defaultRes, selectedFps, selectedBitrateMbps, selectedCodec)
                                        }
                                    ) {
                                        Text(
                                            text = ratioLabel,
                                            fontSize = 11.sp,
                                            fontWeight = if (isRatioSelected) FontWeight.Bold else FontWeight.Normal,
                                            color = if (isRatioSelected) PrimaryLight else TextSecondary,
                                            modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp)
                                        )
                                    }
                                }
                            }

                            // 3. Resolution Selector
                            Text("Çözünürlük:", color = TextSecondary, fontSize = 12.sp)
                            val standardResList = listOf(
                                "1920x1080",
                                "1080x1920",
                                "1280x720",
                                "720x1280",
                                "1440x1080",
                                "1080x1440",
                                "1080x1080",
                                "720x720",
                                "3840x2160",
                                "2560x1440",
                                "960x720",
                                "640x480"
                            )
                            val hwResList = currentCamera?.supportedResolutions?.map { "${it.width}x${it.height}" } ?: emptyList()
                            val resList = (standardResList + hwResList).distinct()

                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .horizontalScroll(rememberScrollState()),
                                horizontalArrangement = Arrangement.spacedBy(6.dp)
                            ) {
                                for (res in resList) {
                                    val isResSelected = selectedResolution == res
                                    val label = when (res) {
                                        "3840x2160" -> "4K UHD"
                                        "2560x1440" -> "2K QHD"
                                        "1920x1080" -> "1080p FHD"
                                        "1080x1920" -> "1080p Dikey"
                                        "1280x720" -> "720p HD"
                                        "720x1280" -> "720p Dikey"
                                        "1440x1080" -> "1080p (4:3)"
                                        "1080x1440" -> "1080p (3:4)"
                                        "1080x1080" -> "1080p (1:1)"
                                        "720x720" -> "720p (1:1)"
                                        else -> res
                                    }
                                    Surface(
                                        color = if (isResSelected) ObsidianHigh else ObsidianLowest,
                                        shape = RoundedCornerShape(8.dp),
                                        border = BorderStroke(1.dp, if (isResSelected) PrimaryLight else ObsidianBorder),
                                        modifier = Modifier.clickable {
                                            applyLiveConfig(res, selectedFps, selectedBitrateMbps, selectedCodec)
                                        }
                                    ) {
                                        Text(
                                            text = label,
                                            fontSize = 11.sp,
                                            fontWeight = if (isResSelected) FontWeight.Bold else FontWeight.Normal,
                                            color = if (isResSelected) PrimaryLight else TextSecondary,
                                            modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp)
                                        )
                                    }
                                }
                            }

                            // 4. FPS Selector
                            Text("Kare Hızı (FPS):", color = TextSecondary, fontSize = 12.sp)
                            val fpsOptions = listOf(60, 30, 24, 15)
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                for (fps in fpsOptions) {
                                    val isFpsSelected = selectedFps == fps
                                    Surface(
                                        color = if (isFpsSelected) ObsidianHigh else ObsidianLowest,
                                        shape = RoundedCornerShape(8.dp),
                                        border = BorderStroke(1.dp, if (isFpsSelected) PrimaryLight else ObsidianBorder),
                                        modifier = Modifier
                                            .weight(1f)
                                            .clickable {
                                                applyLiveConfig(selectedResolution, fps, selectedBitrateMbps, selectedCodec)
                                            }
                                    ) {
                                        Text(
                                            text = "$fps FPS",
                                            fontSize = 11.sp,
                                            fontWeight = if (isFpsSelected) FontWeight.Bold else FontWeight.Normal,
                                            color = if (isFpsSelected) PrimaryLight else TextSecondary,
                                            modifier = Modifier.padding(vertical = 7.dp).wrapContentWidth(Alignment.CenterHorizontally)
                                        )
                                    }
                                }
                            }

                            // 5. Video Bitrate Slider
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text("Video Bitrate:", color = TextSecondary, fontSize = 12.sp)
                                Surface(
                                    color = ObsidianLowest,
                                    shape = RoundedCornerShape(4.dp),
                                    border = BorderStroke(1.dp, ObsidianBorder)
                                ) {
                                    Text(
                                        "${selectedBitrateMbps.toInt()} Mbps",
                                        fontFamily = FontFamily.Monospace,
                                        fontWeight = FontWeight.Bold,
                                        fontSize = 11.sp,
                                        color = PrimaryLight,
                                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                                    )
                                }
                            }
                            Slider(
                                value = selectedBitrateMbps,
                                onValueChange = { selectedBitrateMbps = it },
                                onValueChangeFinished = {
                                    applyLiveConfig(selectedResolution, selectedFps, selectedBitrateMbps, selectedCodec)
                                },
                                valueRange = 1f..50f,
                                steps = 49,
                                colors = SliderDefaults.colors(
                                    thumbColor = PrimaryLight,
                                    activeTrackColor = PrimaryBlue,
                                    inactiveTrackColor = ObsidianHigh
                                )
                            )

                            // 6. Video Codec
                            Text("Video Codec Donanım Hızlandırma:", color = TextSecondary, fontSize = 12.sp)
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                val isH264 = selectedCodec == "h264"
                                Surface(
                                    color = if (isH264) ObsidianHigh else ObsidianLowest,
                                    shape = RoundedCornerShape(8.dp),
                                    border = BorderStroke(1.dp, if (isH264) PrimaryLight else ObsidianBorder),
                                    modifier = Modifier
                                        .weight(1f)
                                        .clickable {
                                            applyLiveConfig(selectedResolution, selectedFps, selectedBitrateMbps, "h264")
                                        }
                                        .padding(8.dp)
                                ) {
                                    Column {
                                        Text("H.264 (AVC)", fontWeight = FontWeight.Bold, fontSize = 12.sp, color = if (isH264) PrimaryLight else TextPrimary)
                                        Text("Evrensel uyumluluk, minimum gecikme", fontSize = 10.sp, color = TextSecondary)
                                    }
                                }

                                val isHevc = selectedCodec == "hevc"
                                Surface(
                                    color = if (isHevc) ObsidianHigh else ObsidianLowest,
                                    shape = RoundedCornerShape(8.dp),
                                    border = BorderStroke(1.dp, if (isHevc) PrimaryLight else ObsidianBorder),
                                    modifier = Modifier
                                        .weight(1f)
                                        .clickable {
                                            applyLiveConfig(selectedResolution, selectedFps, selectedBitrateMbps, "hevc")
                                        }
                                        .padding(8.dp)
                                ) {
                                    Column {
                                        Text("H.265 (HEVC)", fontWeight = FontWeight.Bold, fontSize = 12.sp, color = if (isHevc) PrimaryLight else TextPrimary)
                                        Text("Bant tasarrufu, yüksek GPU sıkıştırma", fontSize = 10.sp, color = TextSecondary)
                                    }
                                }
                            }

                            // 7. Microphone Gain & VU Meter Representation
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Icon(Icons.Default.Mic, null, tint = MintNeon, modifier = Modifier.size(16.dp))
                                    Spacer(modifier = Modifier.width(6.dp))
                                    Text("Mikrofon Ses Seviyesi:", color = TextSecondary, fontSize = 12.sp)
                                }
                                Text(
                                    "${(audioGain * 100).toInt()}%",
                                    fontFamily = FontFamily.Monospace,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 11.sp,
                                    color = MintNeon
                                )
                            }
                            Slider(
                                value = audioGain,
                                onValueChange = {
                                    audioGain = it
                                    service?.audioEncoder?.gain = it
                                },
                                valueRange = 0f..2f,
                                colors = SliderDefaults.colors(
                                    thumbColor = MintNeon,
                                    activeTrackColor = MintDark,
                                    inactiveTrackColor = ObsidianHigh
                                )
                            )

                            // Dual-channel VU Meter Bar Representation
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .height(4.dp)
                                    .clip(RoundedCornerShape(2.dp))
                                    .background(ObsidianLowest),
                                horizontalArrangement = Arrangement.spacedBy(2.dp)
                            ) {
                                val bars = 16
                                for (i in 0 until bars) {
                                    val isLit = (i.toFloat() / bars.toFloat()) < (audioGain / 1.5f)
                                    Box(
                                        modifier = Modifier
                                            .weight(1f)
                                            .fillMaxHeight()
                                            .background(
                                                if (isLit) {
                                                    if (i > 13) ErrorRed else if (i > 10) Color(0xFFFBBF24) else MintNeon
                                                } else {
                                                    ObsidianHigh
                                                }
                                            )
                                    )
                                }
                            }
                        }
                    }
                }
            }

            // Fullscreen Pure-Black AMOLED Overlay
            if (isBlackout) {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(Color.Black)
                        .pointerInput(Unit) {
                            detectTapGestures(
                                onDoubleTap = {
                                    CameraStreamService.isBlackoutGlobal.value = false
                                }
                            )
                        },
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = "AselCam Yayında\n(Çıkmak için ekrana çift dokunun)",
                        color = Color(0x33FFFFFF),
                        fontFamily = FontFamily.Monospace,
                        fontSize = 13.sp
                    )
                }
            }
        }
    }
}

fun getLocalIpAddress(context: Context): String {
    try {
        val interfaces = NetworkInterface.getNetworkInterfaces()
        while (interfaces.hasMoreElements()) {
            val networkInterface = interfaces.nextElement()
            val addresses = networkInterface.inetAddresses
            while (addresses.hasMoreElements()) {
                val address = addresses.nextElement()
                if (!address.isLoopbackAddress && address is Inet4Address) {
                    val ip = address.hostAddress ?: ""
                    if (ip.startsWith("192.") || ip.startsWith("10.") || ip.startsWith("172.")) {
                        return ip
                    }
                }
            }
        }
    } catch (e: Exception) {}
    return "192.168.1.X"
}
