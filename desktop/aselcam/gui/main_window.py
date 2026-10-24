import os
import sys
import time
import threading
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QComboBox, QSlider, QCheckBox,
    QTabWidget, QGroupBox, QProgressBar, QStatusBar, QMessageBox,
    QFrame, QSplitter, QScrollArea, QFileDialog, QSystemTrayIcon, QMenu
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot, QPoint, QMetaObject
from PyQt6.QtGui import QIcon, QFont, QColor, QPixmap

from .video_widget import VideoWidget
from .style import DARK_STYLE
from ..config import ConfigManager, COLOR_PROFILES
from ..core.adb_helper import AdbHelper
from ..core.audio_sink import AudioSink
from ..core.v4l2_sink import V4L2Sink
from ..core.filters import VideoFilters
from ..core.controller import PhoneController
from ..core.receiver import StreamReceiver
from ..core.i18n import _t, tr, I18nManager, SUPPORTED_LANGUAGES

class ValueBadgeEdit(QLineEdit):
    """
    Precision editable readout badge that displays current slider value,
    and allows user to click, type a number with keyboard, and press Enter to adjust slider.
    """
    userValueChanged = pyqtSignal(float)

    def __init__(self, text: str = "", is_float: bool = False, min_val: float = -100.0, max_val: float = 100.0, suffix: str = "", parent=None):
        super().__init__(text, parent)
        self.setObjectName("lbl_value_badge")
        self.is_float = is_float
        self.min_val = min_val
        self.max_val = max_val
        self.suffix = suffix
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumWidth(64 if suffix else 56)
        self.setMaximumWidth(84)
        self.setFixedHeight(22)
        self.returnPressed.connect(self._on_committed)
        self.editingFinished.connect(self._on_committed)

    def setText(self, text: str):
        if self.hasFocus():
            return
        super().setText(text)
        req = self.fontMetrics().horizontalAdvance(text) + 14
        if req > self.width():
            self.setMinimumWidth(min(84, max(56, req)))

    def set_value(self, val: float):
        if self.hasFocus():
            return
        if self.is_float:
            self.setText(f"{val:.1f}{self.suffix}")
        else:
            self.setText(f"{int(round(val))}{self.suffix}")

    def _on_committed(self):
        raw = self.text().strip()
        if self.suffix:
            raw = raw.replace(self.suffix.strip(), "").replace(self.suffix, "")
        raw = raw.replace("+", "").replace("%", "").replace("x", "").replace("X", "").strip()
        try:
            val = float(raw)
            val = max(self.min_val, min(self.max_val, val))
            self.userValueChanged.emit(val)
            self.set_value(val)
        except ValueError:
            pass

class CustomTitleBar(QWidget):
    """
    Sleek, integrated custom title bar matching the AselCam dark theme.
    Supports window dragging, double-click maximize/restore, telemetry indicators,
    and frameless minimize, maximize, and close controls.
    """
    def __init__(self, parent_window: QMainWindow):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.setFixedHeight(44)
        self.setObjectName("custom_title_bar")
        self._drag_pos: Optional[QPoint] = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 10, 0)
        layout.setSpacing(12)

        # 1. Brand Anchor & Master Status
        self.icon_badge = QLabel()
        self.icon_badge.setFixedSize(28, 28)
        self.icon_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "aselcam_icon_64.png")
        if os.path.exists(logo_icon_path):
            pix = QPixmap(logo_icon_path).scaled(26, 26, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.icon_badge.setPixmap(pix)
            self.icon_badge.setStyleSheet("background: transparent; border: none;")
        else:
            self.icon_badge.setText("◈")
            self.icon_badge.setStyleSheet(
                "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #3b82f6, stop:1 #1d4ed8); "
                "color: #ffffff; border-radius: 7px; font-weight: bold; font-size: 14px;"
            )
        layout.addWidget(self.icon_badge)

        self.title_label = QLabel("AselCam")
        self.title_label.setFont(QFont("Space Grotesk", 13, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #dfe2f1; font-weight: 700; letter-spacing: -0.02em; background: transparent;")
        layout.addWidget(self.title_label)

        self.badge_version = QLabel("v1.4.7")
        self.badge_version.setStyleSheet(
            "background: transparent; color: #94a3b8; border: none; "
            "padding: 0px 4px; font-size: 10px; font-weight: 600; font-family: 'JetBrains Mono', monospace;"
        )
        layout.addWidget(self.badge_version)

        layout.addStretch()

        # Telemetry Header Cluster (Clean typography, transparent background, no emojis)
        self.telemetry_pill = QFrame()
        self.telemetry_pill.setStyleSheet("background: transparent; border: none; padding: 0px;")
        pill_l = QHBoxLayout(self.telemetry_pill)
        pill_l.setContentsMargins(0, 0, 0, 0)
        pill_l.setSpacing(10)

        self.lbl_device_info = QLabel(f"{_t('label_device')} —")
        self.lbl_device_info.setStyleSheet("color: #94a3b8; font-weight: 600; font-size: 10px; font-family: 'JetBrains Mono', monospace;")
        pill_l.addWidget(self.lbl_device_info)

        sep1 = QLabel("│")
        sep1.setStyleSheet("color: rgba(255, 255, 255, 0.12); font-size: 10px;")
        pill_l.addWidget(sep1)

        self.lbl_battery = QLabel(f"{_t('label_battery')} —%")
        self.lbl_battery.setStyleSheet("color: #4edea3; font-weight: 600; font-size: 10px; font-family: 'JetBrains Mono', monospace;")
        pill_l.addWidget(self.lbl_battery)

        sep2 = QLabel("│")
        sep2.setStyleSheet("color: rgba(255, 255, 255, 0.12); font-size: 10px;")
        pill_l.addWidget(sep2)

        self.lbl_ping = QLabel(f"{_t('label_ping')} — ms")
        self.lbl_ping.setStyleSheet("color: #4cd7f6; font-weight: 600; font-size: 10px; font-family: 'JetBrains Mono', monospace;")
        pill_l.addWidget(self.lbl_ping)

        sep3 = QLabel("│")
        sep3.setStyleSheet("color: rgba(255, 255, 255, 0.12); font-size: 10px;")
        pill_l.addWidget(sep3)

        self.status_badge = QLabel(_t("status_offline"))
        self.status_badge.setObjectName("status_badge")
        self.status_badge.setStyleSheet(
            "background: transparent; color: #f87171; border: none; padding: 2px 4px; font-weight: bold; font-size: 10px;"
        )
        pill_l.addWidget(self.status_badge)

        layout.addWidget(self.telemetry_pill)
        layout.addSpacing(8)

        # 4. Language Selector Dropdown with Flags
        self.combo_lang = QComboBox()
        self.combo_lang.setObjectName("combo_lang")
        self.combo_lang.setFixedWidth(96)
        self.combo_lang.setFixedHeight(26)
        self.combo_lang.setStyleSheet(
            "QComboBox { background-color: rgba(255, 255, 255, 0.06); color: #cbd5e1; border: 1px solid rgba(255, 255, 255, 0.12); "
            "border-radius: 6px; padding: 1px 6px; font-size: 11px; font-weight: 600; font-family: 'Space Grotesk', sans-serif; } "
            "QComboBox::drop-down { border: none; width: 14px; } "
            "QComboBox QAbstractItemView { background: #131722; color: #e2e8f0; selection-background-color: #2563eb; "
            "border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 6px; outline: none; padding: 4px; }"
        )
        for code, lang_name in SUPPORTED_LANGUAGES.items():
            flag = lang_name.split()[0]
            self.combo_lang.addItem(f"{flag} {code.upper()}", code)

        curr_lang = I18nManager.get_instance().current_language
        for idx in range(self.combo_lang.count()):
            if self.combo_lang.itemData(idx) == curr_lang:
                self.combo_lang.setCurrentIndex(idx)
                break

        self.combo_lang.currentIndexChanged.connect(self._on_lang_changed)
        layout.addWidget(self.combo_lang)
        layout.addSpacing(4)

        # 5. Frameless Window Controls
        self.btn_min = QPushButton("—")
        self.btn_min.setObjectName("btn_win_control")
        self.btn_min.setFixedSize(30, 26)
        self.btn_min.setToolTip("Simge Durumuna Küçült")
        self.btn_min.clicked.connect(self.parent_window.showMinimized)
        layout.addWidget(self.btn_min)

        self.btn_max = QPushButton("□")
        self.btn_max.setObjectName("btn_win_control")
        self.btn_max.setFixedSize(30, 26)
        self.btn_max.setToolTip("Ekranı Kapla / Geri Yükle")
        self.btn_max.clicked.connect(self._toggle_maximize)
        layout.addWidget(self.btn_max)

        self.btn_close = QPushButton("✕")
        self.btn_close.setObjectName("btn_win_close")
        self.btn_close.setFixedSize(30, 26)
        self.btn_close.setToolTip("Kapat")
        self.btn_close.clicked.connect(self.parent_window.close)
        layout.addWidget(self.btn_close)

    def _on_lang_changed(self, index: int):
        lang_code = self.combo_lang.itemData(index)
        if lang_code:
            I18nManager.get_instance().set_language(lang_code)
            if hasattr(self.parent_window, "config"):
                self.parent_window.config.set("language", lang_code)
            if hasattr(self.parent_window, "retranslate_ui"):
                self.parent_window.retranslate_ui()

    def _toggle_maximize(self):
        if self.parent_window.isMaximized():
            self.parent_window.showNormal()
            self.btn_max.setText("□")
        else:
            self.parent_window.showMaximized()
            self.btn_max.setText("❐")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self.parent_window.windowHandle()
            if handle and hasattr(handle, "startSystemMove"):
                if handle.startSystemMove():
                    event.accept()
                    return
            self._drag_pos = event.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            if not self.parent_window.isMaximized():
                self.parent_window.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_maximize()
            event.accept()

class MainWindow(QMainWindow):
    frame_received_signal = pyqtSignal(object)
    stats_updated_signal = pyqtSignal(float, float)
    audio_level_signal = pyqtSignal(float)
    telemetry_updated_signal = pyqtSignal(dict)
    disconnected_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AselCam")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setObjectName("main_window")
        win_icon = QIcon()
        assets_dir = os.path.join(os.path.dirname(__file__), "..", "assets")
        for sz in (16, 24, 32, 48, 64, 128, 256, 512):
            fn = os.path.join(assets_dir, f"aselcam_icon_{sz}.png")
            if os.path.exists(fn):
                win_icon.addFile(fn)
        if not win_icon.isNull():
            self.setWindowIcon(win_icon)
        self.resize(1340, 840)
        self.setMinimumSize(1000, 680)
        self.setStyleSheet(DARK_STYLE)
        self.setMouseTracking(True)

        self._filter_save_timer = QTimer(self)
        self._filter_save_timer.setSingleShot(True)
        self._filter_save_timer.timeout.connect(self._save_filters_to_disk)

        self.config = ConfigManager()
        configured_lang = self.config.get("language", "auto")
        I18nManager.get_instance().set_language(configured_lang)

        self.adb = AdbHelper()
        self.filters = VideoFilters()
        self._load_saved_filters()

        self.audio_sink = AudioSink(
            sink_name=self.config.get("audio_sink", "AselCam_Mic")
        )
        self.v4l2_sink = V4L2Sink(
            device_path=self.config.get("v4l2_device", "/dev/video10")
        )

        self.controller = PhoneController()
        self.receiver: Optional[StreamReceiver] = None

        self.is_connected = False
        self.is_camera_paused = False
        self.is_mic_muted = False
        self.is_preview_enabled = self.config.get("preview_enabled", True)
        self._user_disconnected = False
        self._reconnect_attempts = 0
        self._last_host = "192.168.1.3"
        self._last_video_port = 4747
        self._last_control_port = 4748

        self._zoom_timer = QTimer(self)
        self._zoom_timer.setSingleShot(True)
        self._zoom_timer.setInterval(80)
        self._zoom_timer.timeout.connect(self._send_debounced_zoom)
        self._pending_zoom = 1.0

        self._mic_gain_timer = QTimer(self)
        self._mic_gain_timer.setSingleShot(True)
        self._mic_gain_timer.setInterval(80)
        self._mic_gain_timer.timeout.connect(self._send_debounced_mic_gain)
        self._pending_mic_gain = 1.0

        self._force_quit = False
        self._last_fps = 0.0
        self._last_bitrate_kbps = 0.0
        self._last_ping = -1.0
        self._last_loss = 0.0
        self._remote_torch_on = False
        self._remote_phone_preview_on = True
        self._remote_blackout_on = False
        self.is_screen_mirror_active = False
        self._loaded_cameras = []
        self._last_device_model = "—"
        self._last_battery_level = "—"

        self._setup_ui()
        self._setup_signals()
        self._init_drivers()
        self._init_system_tray()
        self.retranslate_ui()

        # Telemetry poll timer
        self.telemetry_timer = QTimer(self)
        self.telemetry_timer.timeout.connect(self._poll_telemetry)
        self.telemetry_timer.start(2000)

    def _init_system_tray(self):
        """Initializes system tray icon and background persistence menu."""
        self.tray_icon = QSystemTrayIcon(self)
        logo_icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "aselcam_icon_64.png")
        if os.path.exists(logo_icon_path):
            self.tray_icon.setIcon(QIcon(logo_icon_path))
        else:
            self.tray_icon.setIcon(self.windowIcon())
        self.tray_icon.setToolTip("AselCam Studio")

        self.tray_menu = QMenu()
        self.tray_action_show = self.tray_menu.addAction(_t("tray_show"))
        self.tray_action_show.triggered.connect(self._toggle_window_from_tray)
        self.tray_menu.addSeparator()
        self.tray_action_quit = self.tray_menu.addAction(_t("tray_quit"))
        self.tray_action_quit.triggered.connect(self._quit_application)

        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self._toggle_window_from_tray()

    def _toggle_window_from_tray(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.activateWindow()
            self.raise_()

    def _quit_application(self):
        self._force_quit = True
        self.close()

    def _toggle_hub_panel(self):
        """Toggles the visibility of Hub #1 inspector pane."""
        if hasattr(self, "right_container"):
            is_visible = self.right_container.isVisible()
            self.right_container.setVisible(not is_visible)
            if hasattr(self, "btn_toggle_hub"):
                self.btn_toggle_hub.setText("◧ Hub #1" if is_visible else "■ Hub #1")

    def _update_status_bar_stats(self):
        """Formats and displays live streaming stats in footer bar including delay and packet loss."""
        delay_str = f"{self._last_ping:.0f} ms" if self._last_ping >= 0 else "—"
        loss_str = f"{self._last_loss:.1f}%"
        self.status_bar.showMessage(
            _t("stream_active_status").format(
                fps=f"{self._last_fps:.1f}",
                bitrate=f"{self._last_bitrate_kbps / 1000.0:.2f}",
                delay=delay_str,
                loss=loss_str,
                dev=self.v4l2_sink.device_path
            )
        )

    def _load_saved_filters(self):
        saved = self.config.get("filters", {})
        self.filters.update_params(
            exposure=float(saved.get("exposure", 0.0)),
            highlights=int(saved.get("highlights", 0)),
            shadows=int(saved.get("shadows", 0)),
            whites=int(saved.get("whites", 0)),
            blacks=int(saved.get("blacks", 0)),
            contrast=int(saved.get("contrast", 0)),
            brightness=int(saved.get("brightness", 0)),
            temperature=int(saved.get("temperature", 0)),
            tint=int(saved.get("tint", 0)),
            tone_curve=str(saved.get("tone_curve", "linear")),
            saturation=int(saved.get("saturation", 100)),
            vibrance=int(saved.get("vibrance", 0)),
            sharpness=int(saved.get("sharpness", 0)),
            flip_h=bool(saved.get("flip_h", False)),
            flip_v=bool(saved.get("flip_v", False)),
            rotation=int(saved.get("rotation", 0)),
            grayscale=bool(saved.get("grayscale", False)),
            invert=bool(saved.get("invert", False)),
            red_gain=int(saved.get("red_gain", 0)),
            green_gain=int(saved.get("green_gain", 0)),
            blue_gain=int(saved.get("blue_gain", 0)),
            focus_enabled=bool(saved.get("focus_enabled", False)),
            focus_mode=str(saved.get("focus_mode", "blur")),
            focus_radius=int(saved.get("focus_radius", 45)),
            focus_blur=int(saved.get("focus_blur", 15)),
            focus_image_path=str(saved.get("focus_image_path", ""))
        )

    def _get_resize_edges(self, pos: QPoint):
        if self.isMaximized():
            return Qt.Edge(0)
        w = self.width()
        h = self.height()
        b = 6  # border width in pixels
        edges = Qt.Edge(0)
        if pos.x() < b:
            edges |= Qt.Edge.LeftEdge
        elif pos.x() > w - b:
            edges |= Qt.Edge.RightEdge
        if pos.y() < b:
            edges |= Qt.Edge.TopEdge
        elif pos.y() > h - b:
            edges |= Qt.Edge.BottomEdge
        return edges

    def _update_cursor_for_edges(self, edges):
        has_l = bool(edges & Qt.Edge.LeftEdge)
        has_r = bool(edges & Qt.Edge.RightEdge)
        has_t = bool(edges & Qt.Edge.TopEdge)
        has_b = bool(edges & Qt.Edge.BottomEdge)

        if (has_t and has_l) or (has_b and has_r):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif (has_t and has_r) or (has_b and has_l):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif has_l or has_r:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif has_t or has_b:
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        else:
            self.unsetCursor()

    def mouseMoveEvent(self, event):
        try:
            edges = self._get_resize_edges(event.position().toPoint())
            self._update_cursor_for_edges(edges)
        except Exception:
            pass
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        try:
            if event.button() == Qt.MouseButton.LeftButton:
                edges = self._get_resize_edges(event.position().toPoint())
                if edges != Qt.Edge(0) and getattr(edges, "value", 0) != 0:
                    handle = self.windowHandle()
                    if handle and hasattr(handle, "startSystemResize"):
                        if handle.startSystemResize(edges):
                            event.accept()
                            return
        except Exception:
            pass
        super().mousePressEvent(event)

    def _init_drivers(self):
        # 1. Setup virtual mic directly in background
        if self.config.get("enable_audio", True):
            self.audio_sink.setup_virtual_mic()
            self.audio_sink.set_gain(self.config.get("audio_volume", 1.0))
            self.audio_sink.on_level_callback = lambda lvl: self.audio_level_signal.emit(lvl)
            if hasattr(self, "lbl_mic_status"):
                self.lbl_mic_status.setText("Sanal Mikrofon: Aktif")
                self.lbl_mic_status.setStyleSheet("color: #4edea3; font-weight: 600; background: transparent; margin-right: 14px; font-family: 'JetBrains Mono', monospace;")

        # 2. Open direct virtual camera device immediately so 3rd-party apps always see an active 30 FPS feed
        res_str = self.config.get("resolution", "1920x1080").split()[0]
        try:
            w, h = [int(x) for x in res_str.split("x")]
        except Exception:
            w, h = 1920, 1080

        if not sys.platform.startswith("linux"):
            # Windows & macOS: Direct virtual camera initialized automatically without 3rd party apps
            if self.v4l2_sink.open(w, h):
                self.lbl_v4l2_status.setText("Sanal Kamera: Aktif")
                self.lbl_v4l2_status.setStyleSheet("color: #4edea3; font-weight: 600; background: transparent; margin-right: 12px; font-family: 'JetBrains Mono', monospace;")
            else:
                self.lbl_v4l2_status.setText("Sanal Kamera: Aktif")
                self.lbl_v4l2_status.setStyleSheet("color: #4edea3; font-weight: 600; background: transparent; margin-right: 12px; font-family: 'JetBrains Mono', monospace;")
        else:
            vdev = self.config.get("v4l2_device", "/dev/video10")
            self.v4l2_sink.device_path = vdev
            if os.path.exists(vdev) or self.v4l2_sink.open(w, h):
                self.v4l2_sink.open(w, h)
                self.lbl_v4l2_status.setText("Sanal Kamera: Aktif")
                self.lbl_v4l2_status.setStyleSheet("color: #4edea3; font-weight: 600; background: transparent; margin-right: 12px; font-family: 'JetBrains Mono', monospace;")
            else:
                self.lbl_v4l2_status.setText("Sanal Kamera: Hazır")
                self.lbl_v4l2_status.setStyleSheet("color: #ffb703; font-weight: 600; background: transparent; margin-right: 12px; font-family: 'JetBrains Mono', monospace;")

    def _setup_ui(self):
        central_widget = QWidget()
        central_widget.setObjectName("central_widget")
        central_widget.setMouseTracking(True)
        self.setCentralWidget(central_widget)
        outer_layout = QVBoxLayout(central_widget)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # 1. Top Custom Frameless Title Bar (Theme-Integrated)
        self.title_bar = CustomTitleBar(self)
        outer_layout.addWidget(self.title_bar)

        self.status_badge = self.title_bar.status_badge
        self.lbl_device_info = self.title_bar.lbl_device_info
        self.lbl_battery = self.title_bar.lbl_battery
        self.lbl_ping = self.title_bar.lbl_ping

        # 2. QUICK HARDWARE CONNECTION STRIP (Immediately below Top Bar, like in Stitch)
        self.conn_strip = QFrame()
        self.conn_strip.setObjectName("connection_strip")
        self.conn_strip.setFixedHeight(48)
        strip_layout = QHBoxLayout(self.conn_strip)
        strip_layout.setContentsMargins(16, 4, 16, 4)
        strip_layout.setSpacing(12)

        # Mode Segment Selector (USB vs Wi-Fi)
        self.mode_container = QFrame()
        self.mode_container.setStyleSheet(
            "background-color: #0a0e18; border: 1px solid rgba(255, 255, 255, 0.08); "
            "border-radius: 8px; padding: 2px;"
        )
        mode_l = QHBoxLayout(self.mode_container)
        mode_l.setContentsMargins(2, 2, 2, 2)
        mode_l.setSpacing(2)

        self.btn_mode_usb = QPushButton("USB (ADB - Düşük Gecikme)")
        self.btn_mode_usb.setStyleSheet("background-color: #4d8eff; color: #00285d; border: none; border-radius: 6px; padding: 6px 14px; font-weight: 700; font-size: 12px;")
        self.btn_mode_usb.clicked.connect(lambda: self._set_connection_mode("usb"))
        mode_l.addWidget(self.btn_mode_usb)

        self.btn_mode_wifi = QPushButton("Wi-Fi (Kablosuz)")
        self.btn_mode_wifi.setStyleSheet("background-color: transparent; color: #c2c6d6; border: none; border-radius: 6px; padding: 6px 14px; font-weight: 500; font-size: 12px;")
        self.btn_mode_wifi.clicked.connect(lambda: self._set_connection_mode("wifi"))
        mode_l.addWidget(self.btn_mode_wifi)

        strip_layout.addWidget(self.mode_container)

        # Separator line
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: rgba(255, 255, 255, 0.12);")
        strip_layout.addWidget(sep)

        # Dynamic Field Area: USB device dropdown or Wi-Fi IP/Port inputs
        self.field_stack = QWidget()
        self.field_stack_l = QHBoxLayout(self.field_stack)
        self.field_stack_l.setContentsMargins(0, 0, 0, 0)
        self.field_stack_l.setSpacing(8)

        # USB fields
        self.widget_usb_fields = QWidget()
        w_usb_l = QHBoxLayout(self.widget_usb_fields)
        w_usb_l.setContentsMargins(0, 0, 0, 0)
        w_usb_l.setSpacing(6)
        lbl_dev = QLabel("CİHAZ:")
        lbl_dev.setStyleSheet("color: #8c909f; font-size: 11px; font-weight: 700; font-family: 'JetBrains Mono', monospace;")
        w_usb_l.addWidget(lbl_dev)

        self.combo_adb_devices = QComboBox()
        self.combo_adb_devices.setMinimumWidth(280)
        w_usb_l.addWidget(self.combo_adb_devices)

        self.btn_refresh_adb = QPushButton("Yenile")
        self.btn_refresh_adb.setToolTip("Cihazları Yenile")
        self.btn_refresh_adb.setFixedSize(68, 30)
        self.btn_refresh_adb.clicked.connect(self._refresh_adb_devices)
        w_usb_l.addWidget(self.btn_refresh_adb)
        self.field_stack_l.addWidget(self.widget_usb_fields)

        # Wi-Fi fields
        self.widget_wifi_fields = QWidget()
        w_wifi_l = QHBoxLayout(self.widget_wifi_fields)
        w_wifi_l.setContentsMargins(0, 0, 0, 0)
        w_wifi_l.setSpacing(6)
        lbl_ip = QLabel("IP:")
        lbl_ip.setStyleSheet("color: #8c909f; font-size: 11px; font-weight: 700; font-family: 'JetBrains Mono', monospace;")
        w_wifi_l.addWidget(lbl_ip)
        self.txt_ip = QLineEdit(self.config.get("wifi_ip", "192.168.1.3"))
        self.txt_ip.setPlaceholderText("192.168.1.3")
        self.txt_ip.setMinimumWidth(130)
        w_wifi_l.addWidget(self.txt_ip)

        lbl_port = QLabel("PORT:")
        lbl_port.setStyleSheet("color: #8c909f; font-size: 11px; font-weight: 700; font-family: 'JetBrains Mono', monospace;")
        w_wifi_l.addWidget(lbl_port)
        self.txt_port = QLineEdit(str(self.config.get("video_port", 4747)))
        self.txt_port.setMaximumWidth(60)
        w_wifi_l.addWidget(self.txt_port)
        self.widget_wifi_fields.hide()
        self.field_stack_l.addWidget(self.widget_wifi_fields)

        strip_layout.addWidget(self.field_stack)
        strip_layout.addStretch()

        # Driver ready status
        self.lbl_v4l2_indicator = QLabel(_t("driver_status_ready"))
        self.lbl_v4l2_indicator.setStyleSheet("color: #4edea3; font-weight: 600; font-size: 11px; font-family: 'JetBrains Mono', monospace;")
        strip_layout.addWidget(self.lbl_v4l2_indicator)

        # Master Connect Button (matches Stitch HTML line 262: Bağlan)
        self.btn_master_connect = QPushButton(_t("conn_btn_start"))
        self.btn_master_connect.setObjectName("btn_primary")
        self.btn_master_connect.setMinimumHeight(32)
        self.btn_master_connect.clicked.connect(self._toggle_master_connect)
        strip_layout.addWidget(self.btn_master_connect)

        # Aliases for backwards compatibility with methods
        self.btn_connect_usb = self.btn_master_connect
        self.btn_connect_wifi = self.btn_master_connect

        outer_layout.addWidget(self.conn_strip)

        # 3. Main Body Container
        body_widget = QWidget()
        body_widget.setObjectName("body_widget")
        body_widget.setMouseTracking(True)
        main_layout = QVBoxLayout(body_widget)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(12)
        outer_layout.addWidget(body_widget, 1)

        # 3. Main Center Area (Splitter: Video Preview Left, Controls Right)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(8)

        # Left Container: Video + Action Bar
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        self.video_widget = VideoWidget()
        self.video_widget.set_preview_enabled(self.is_preview_enabled)
        left_layout.addWidget(self.video_widget, stretch=1)

        # Video Quick Control Dock Frame (from Stitch design)
        dock_frame = QFrame()
        dock_frame.setObjectName("video_control_dock")
        vbar = QHBoxLayout(dock_frame)
        vbar.setContentsMargins(10, 8, 10, 8)
        vbar.setSpacing(8)

        # Preview Toggle Button
        self.btn_toggle_preview = QPushButton("Önizlemeyi Kapat" if self.is_preview_enabled else "Önizlemeyi Aç")
        self.btn_toggle_preview.setToolTip("Bilgisayarda ekran önizlemesini açıp kapatır. Kapatıldığında GPU ve CPU yükü sıfıra iner.")
        self.btn_toggle_preview.clicked.connect(self._toggle_preview)
        vbar.addWidget(self.btn_toggle_preview)

        # Camera Mute Toggle
        self.btn_pause_cam = QPushButton("Kamerayı Karart")
        self.btn_pause_cam.setToolTip("Video akışını geçici olarak karartır")
        self.btn_pause_cam.clicked.connect(self._toggle_camera_pause)
        vbar.addWidget(self.btn_pause_cam)

        # Mic Mute Toggle
        self.btn_mute_mic = QPushButton("Mikrofonu Kapat")
        self.btn_mute_mic.clicked.connect(self._toggle_mic_mute)
        vbar.addWidget(self.btn_mute_mic)

        # Master Audio Gain Fader Inset
        audio_inset = QFrame()
        audio_inset.setStyleSheet("background-color: #0a0e18; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 2px 8px;")
        audio_l = QHBoxLayout(audio_inset)
        audio_l.setContentsMargins(4, 2, 4, 2)
        audio_l.setSpacing(6)

        self.lbl_mic_icon = QLabel(_t("audio_label"))
        self.lbl_mic_icon.setStyleSheet("color: #8c909f; font-size: 10px; font-weight: 700; font-family: 'JetBrains Mono', monospace;")
        audio_l.addWidget(self.lbl_mic_icon)

        self.slider_mic_gain = QSlider(Qt.Orientation.Horizontal)
        self.slider_mic_gain.setRange(0, 200)
        self.slider_mic_gain.setValue(int(self.config.get("audio_volume", 1.0) * 100))
        self.slider_mic_gain.setMinimumWidth(80)
        self.slider_mic_gain.valueChanged.connect(self._on_mic_gain_changed)
        audio_l.addWidget(self.slider_mic_gain)

        self.lbl_mic_gain = ValueBadgeEdit(f"{self.slider_mic_gain.value()}%", min_val=0, max_val=200, suffix="%")
        self.lbl_mic_gain.setObjectName("lbl_value_badge")
        self.lbl_mic_gain.userValueChanged.connect(lambda v: self.slider_mic_gain.setValue(int(round(v))))
        audio_l.addWidget(self.lbl_mic_gain)

        # Audio VU Level Meter
        self.audio_vu = QProgressBar()
        self.audio_vu.setRange(0, 100)
        self.audio_vu.setValue(0)
        self.audio_vu.setTextVisible(False)
        self.audio_vu.setFixedWidth(60)
        audio_l.addWidget(self.audio_vu)

        self.btn_toggle_hub = QPushButton("◧ Hub #1")
        self.btn_toggle_hub.setObjectName("btn_toggle_hub")
        self.btn_toggle_hub.setToolTip("Hub #1 Panelini Aç / Kapat")
        self.btn_toggle_hub.clicked.connect(self._toggle_hub_panel)
        vbar.addWidget(self.btn_toggle_hub)

        vbar.addWidget(audio_inset)
        left_layout.addWidget(dock_frame)

        # Headless telemetry label references for background status handlers
        self.telemetry_encoder = QLabel()
        self.telemetry_conn = QLabel()
        self.telemetry_device = QLabel()
        self.telemetry_audio = QLabel()

        splitter.addWidget(left_container)

        # Right Container: Control Panels Tabs (Inspector Pane from Stitch)
        self.right_container = right_container = QWidget()
        right_container.setObjectName("inspector_shell")
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(10)

        # Inspector Header
        insp_header = QHBoxLayout()
        insp_header.setSpacing(8)

        insp_icon = QLabel()
        insp_icon.setFixedSize(30, 30)
        insp_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        insp_logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "aselcam_icon_64.png")
        if os.path.exists(insp_logo_path):
            pix = QPixmap(insp_logo_path).scaled(26, 26, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            insp_icon.setPixmap(pix)
            insp_icon.setStyleSheet("background: transparent; border: none;")
        else:
            insp_icon.setText("◈")
            insp_icon.setStyleSheet("background-color: #262a35; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 6px; font-size: 14px; color: #4d8eff;")
        insp_header.addWidget(insp_icon)

        insp_titles = QVBoxLayout()
        insp_titles.setSpacing(1)
        self.lbl_h_main = QLabel("Stüdyo Masası")
        self.lbl_h_main.setFont(QFont("Space Grotesk", 12, QFont.Weight.Bold))
        self.lbl_h_main.setStyleSheet("color: #dfe2f1; font-weight: 700;")
        self.lbl_h_sub = QLabel("Sürücü Hazır")
        self.lbl_h_sub.setStyleSheet("color: #4edea3; font-size: 10px; font-weight: 600; font-family: 'JetBrains Mono', monospace;")
        insp_titles.addWidget(self.lbl_h_main)
        insp_titles.addWidget(self.lbl_h_sub)
        insp_header.addLayout(insp_titles)

        insp_header.addStretch()

        self.lbl_hub_badge = QLabel("HUB #1")
        self.lbl_hub_badge.setStyleSheet("background-color: #313540; color: #8c909f; border-radius: 4px; padding: 2px 6px; font-size: 10px; font-weight: 700; font-family: 'JetBrains Mono', monospace;")
        insp_header.addWidget(self.lbl_hub_badge)

        self.btn_collapse_hub = QPushButton("✕")
        self.btn_collapse_hub.setObjectName("btn_collapse_hub")
        self.btn_collapse_hub.setFixedSize(26, 26)
        self.btn_collapse_hub.setToolTip(_t("hub_collapse"))
        self.btn_collapse_hub.setStyleSheet(
            "QPushButton#btn_collapse_hub { background: #262a35; color: #cbd5e1; border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 6px; font-weight: bold; font-size: 12px; padding: 0px !important; margin: 0px !important; text-align: center; } "
            "QPushButton#btn_collapse_hub:hover { background: #334155; color: #ffffff; border-color: rgba(255, 255, 255, 0.25); }"
        )
        self.btn_collapse_hub.clicked.connect(self._toggle_hub_panel)
        insp_header.addWidget(self.btn_collapse_hub)

        right_layout.addLayout(insp_header)

        self.control_tabs = QTabWidget()

        # TAB 1: Remote Phone Controls
        remote_scroll = QScrollArea()
        remote_scroll.setWidgetResizable(True)
        remote_scroll.setFrameShape(QFrame.Shape.NoFrame)
        remote_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        remote_tab = QWidget()
        remote_layout = QVBoxLayout(remote_tab)
        remote_layout.setContentsMargins(10, 10, 10, 10)
        remote_layout.setSpacing(12)

        # 1. Rapid Remote Mobile Toggles Card
        self.actions_box = actions_box = QGroupBox("Hızlı Telefon Aksiyonları")
        act_layout = QVBoxLayout(actions_box)
        act_layout.setSpacing(8)

        # Switch Camera Trigger (Full Width Electric Blue Action)
        self.btn_flip_camera = QPushButton("Kamera Değiştir (Ön / Arka)")
        self.btn_flip_camera.setObjectName("btn_action")
        self.btn_flip_camera.clicked.connect(self._remote_switch_camera)
        act_layout.addWidget(self.btn_flip_camera)

        # Flashlight & Preview Grid (2-columns)
        act_grid = QGridLayout()
        act_grid.setSpacing(6)

        self.btn_torch = QPushButton("Fener / Flaş Aç")
        self.btn_torch.clicked.connect(self._remote_toggle_torch)
        act_grid.addWidget(self.btn_torch, 0, 0)

        self.btn_remote_preview = QPushButton("Telefon Önizleme Yayını")
        self.btn_remote_preview.setToolTip("Telefonda önizlemeyi açıp kapatır")
        self.btn_remote_preview.clicked.connect(self._remote_toggle_phone_preview)
        act_grid.addWidget(self.btn_remote_preview, 0, 1)
        act_layout.addLayout(act_grid)

        # AMOLED Blackout (Full Width)
        self.btn_remote_blackout = QPushButton(_t("ctrl_blackout_on"))
        self.btn_remote_blackout.setToolTip("Telefon ekranını tamamen siyah yaparak OLED piksellerini kapatır")
        self.btn_remote_blackout.clicked.connect(self._remote_toggle_blackout)
        act_layout.addWidget(self.btn_remote_blackout)

        # Screen Mirroring (Full Width Electric Cyan, no emoji)
        self.btn_screen_mirror = QPushButton(_t("ctrl_screen_mirror_btn"))
        self.btn_screen_mirror.setObjectName("btn_screen_mirror")
        self.btn_screen_mirror.setToolTip("Telefon ekranını canlı olarak aktarır (Kamera ve Ekran arasında geçiş yapar)")
        self.btn_screen_mirror.clicked.connect(self._remote_toggle_screen_mirror)
        act_layout.addWidget(self.btn_screen_mirror)

        # Hidden or secondary dropdown for direct selection
        self.combo_remote_camera = QComboBox()
        self.combo_remote_camera.addItem(_t("cam_rear_default"), "0")
        self.combo_remote_camera.addItem(_t("cam_front_item"), "1")
        self.combo_remote_camera.currentIndexChanged.connect(self._on_remote_camera_selected)
        act_layout.addWidget(self.combo_remote_camera)

        remote_layout.addWidget(actions_box)

        # 2. Optical & Digital Zoom Card (Hardware delegated to phone Camera2 CONTROL_ZOOM_RATIO)
        self.zoom_box = zoom_box = QGroupBox("Kamera Zoom (Donanımsal Optik && Hibrit)")
        zoom_l = QVBoxLayout(zoom_box)
        zoom_l.setSpacing(8)

        zoom_hdr = QHBoxLayout()
        self.lbl_zoom_title = QLabel("Mevcut Zoom:")
        zoom_hdr.addWidget(self.lbl_zoom_title)
        self.lbl_zoom = ValueBadgeEdit("1.0x", is_float=True, min_val=1.0, max_val=100.0, suffix="x")
        self.lbl_zoom.setObjectName("lbl_value_badge")
        zoom_hdr.addWidget(self.lbl_zoom, 0, Qt.AlignmentFlag.AlignRight)
        zoom_l.addLayout(zoom_hdr)

        self.slider_zoom = QSlider(Qt.Orientation.Horizontal)
        self.slider_zoom.setRange(10, 1000) # 1.0x to 100.0x (S25 Ultra support)
        self.slider_zoom.setValue(10)
        self.slider_zoom.valueChanged.connect(self._remote_zoom_changed)
        self.lbl_zoom.userValueChanged.connect(lambda v: self.slider_zoom.setValue(int(round(v * 10))))
        zoom_l.addWidget(self.slider_zoom)

        # Quick Preset Chips (Supports full phone multi-camera range)
        zoom_chips = QHBoxLayout()
        zoom_chips.setSpacing(5)
        presets = [("1x", 10), ("2x", 20), ("5x", 50), ("10x", 100), ("30x", 300), ("100x", 1000)]
        for label, val in presets:
            btn_chip = QPushButton(label)
            btn_chip.setObjectName("btn_preset_chip")
            btn_chip.clicked.connect(lambda checked=False, v=val: self.slider_zoom.setValue(v))
            zoom_chips.addWidget(btn_chip)
        zoom_l.addLayout(zoom_chips)

        remote_layout.addWidget(zoom_box)

        # Quick Aspect Ratio / Portrait-Landscape Selector
        self.aspect_box = aspect_box = QGroupBox(_t("aspect_header"))
        aspect_l = QVBoxLayout(aspect_box)
        self.combo_quick_aspect = QComboBox()
        self.combo_quick_aspect.addItem(f"16:9 {_t('aspect_16_9_landscape')} (1920x1080)", "1920x1080")
        self.combo_quick_aspect.addItem(f"9:16 {_t('aspect_9_16_portrait')} (1080x1920)", "1080x1920")
        self.combo_quick_aspect.addItem(f"4:3 {_t('aspect_4_3_landscape')} (1440x1080)", "1440x1080")
        self.combo_quick_aspect.addItem(f"3:4 {_t('aspect_3_4_portrait')} (1080x1440)", "1080x1440")
        self.combo_quick_aspect.addItem(f"1:1 {_t('aspect_1_1_square')} (1080x1080)", "1080x1080")
        self.combo_quick_aspect.addItem(f"9:16 {_t('aspect_9_16_portrait')} HD (720x1280)", "720x1280")
        self.combo_quick_aspect.currentIndexChanged.connect(self._on_quick_aspect_selected)
        aspect_l.addWidget(self.combo_quick_aspect)
        remote_layout.addWidget(aspect_box)

        remote_layout.addStretch()
        remote_scroll.setWidget(remote_tab)
        self.control_tabs.addTab(remote_scroll, "Mobil Kontrol")

        # TAB 2: RAW Development & Color Grading Panel
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        filters_tab = QWidget()
        filters_layout = QVBoxLayout(filters_tab)
        filters_layout.setContentsMargins(8, 8, 8, 8)
        filters_layout.setSpacing(10)

        # SECTION 1: Renk & Görüntü Profilleri (Presets)
        self.profile_box = profile_box = QGroupBox("Renk && Görüntü Profilleri")
        prof_layout = QVBoxLayout(profile_box)
        prof_layout.setSpacing(8)

        prof_row = QHBoxLayout()
        self.lbl_prof_title = QLabel("Aktif Profil:")
        prof_row.addWidget(self.lbl_prof_title)
        self.combo_color_profile = QComboBox()
        self.combo_color_profile.addItem("Standart (Doğal)", "standard")
        self.combo_color_profile.addItem("Canlı Yayın (Vivid)", "vivid")
        self.combo_color_profile.addItem("Sinematik Sıcak (Cinema)", "cinema")
        self.combo_color_profile.addItem("Stüdyo Portre (Yumuşak)", "portrait")
        self.combo_color_profile.addItem("Düşük Işık / Gece", "lowlight")
        self.combo_color_profile.addItem("Retro / Vintage", "vintage")
        self.combo_color_profile.addItem("Siyah & Beyaz (B&W Mono)", "bw")
        self.combo_color_profile.addItem("Özel (Custom)", "custom")
        saved_prof = self.config.get("filters", {}).get("color_profile", "standard")
        prof_idx = self.combo_color_profile.findData(saved_prof)
        if prof_idx >= 0:
            self.combo_color_profile.setCurrentIndex(prof_idx)
        self.combo_color_profile.currentIndexChanged.connect(self._on_color_profile_selected)
        prof_row.addWidget(self.combo_color_profile)
        prof_layout.addLayout(prof_row)

        prof_chips = QHBoxLayout()
        prof_chips.setSpacing(5)
        p_presets = [
            ("chip_natural", "standard"),
            ("chip_vivid", "vivid"),
            ("chip_cinema", "cinema"),
            ("chip_portrait", "portrait"),
            ("chip_night", "lowlight"),
            ("chip_bw", "bw")
        ]
        self.prof_chip_buttons = []
        for i18n_key, p_key in p_presets:
            btn_p = QPushButton(_t(i18n_key))
            btn_p.setObjectName("btn_preset_chip")
            btn_p.clicked.connect(lambda checked=False, k=p_key: self._apply_profile_by_key(k))
            prof_chips.addWidget(btn_p)
            self.prof_chip_buttons.append((btn_p, i18n_key))
        prof_layout.addLayout(prof_chips)
        filters_layout.addWidget(profile_box)

        # SECTION 2: Portre Odak & Yazılımsal Arkaplan (AI Focus)
        self.focus_box = focus_box = QGroupBox("Yapay Zeka Kişi Algılama && Portre Odak (AI Focus)")
        focus_l = QVBoxLayout(focus_box)
        focus_l.setSpacing(8)

        self.chk_focus_enabled = QCheckBox("Yapay Zeka Kişi Algılama ve Arkaplan Efektini Etkinleştir")
        self.chk_focus_enabled.setChecked(self.filters.focus_enabled)
        self.chk_focus_enabled.stateChanged.connect(self._update_filters)
        focus_l.addWidget(self.chk_focus_enabled)

        fmode_row = QHBoxLayout()
        self.lbl_fmode = QLabel("Efekt Modu:")
        fmode_row.addWidget(self.lbl_fmode)
        self.combo_focus_mode = QComboBox()
        self.combo_focus_mode.addItem("Arkaplanı Bulanıklaştır (AI Bokeh)", "blur")
        self.combo_focus_mode.addItem("Stüdyo Koyu Arkaplan", "studio")
        self.combo_focus_mode.addItem("Özel Arkaplan Resmi", "custom")
        fmode_idx = self.combo_focus_mode.findData(self.filters.focus_mode)
        if fmode_idx >= 0:
            self.combo_focus_mode.setCurrentIndex(fmode_idx)
        self.combo_focus_mode.currentIndexChanged.connect(self._update_filters)
        fmode_row.addWidget(self.combo_focus_mode)
        focus_l.addLayout(fmode_row)

        frad_row = QHBoxLayout()
        self.lbl_frad = QLabel("Kişi Algılama Hassasiyeti:")
        frad_row.addWidget(self.lbl_frad)
        self.lbl_focus_radius = ValueBadgeEdit(f"{self.filters.focus_radius}%", min_val=20, max_val=90, suffix="%")
        self.lbl_focus_radius.setObjectName("lbl_value_badge")
        self.lbl_focus_radius.userValueChanged.connect(lambda v: self.slider_focus_radius.setValue(int(round(v))))
        frad_row.addWidget(self.lbl_focus_radius, 0, Qt.AlignmentFlag.AlignRight)
        focus_l.addLayout(frad_row)

        self.slider_focus_radius = QSlider(Qt.Orientation.Horizontal)
        self.slider_focus_radius.setRange(20, 90)
        self.slider_focus_radius.setToolTip("Yapay zeka kişi segmentasyonu eşiği ve saç/vücut detay hassasiyeti")
        self.slider_focus_radius.setValue(self.filters.focus_radius)
        self.slider_focus_radius.valueChanged.connect(self._update_filters)
        focus_l.addWidget(self.slider_focus_radius)

        fblur_row = QHBoxLayout()
        self.lbl_fblur = QLabel("Bulanıklık Seviyesi:")
        fblur_row.addWidget(self.lbl_fblur)
        self.lbl_focus_blur = ValueBadgeEdit(str(self.filters.focus_blur), min_val=5, max_val=35)
        self.lbl_focus_blur.setObjectName("lbl_value_badge")
        self.lbl_focus_blur.userValueChanged.connect(lambda v: self.slider_focus_blur.setValue(int(round(v))))
        fblur_row.addWidget(self.lbl_focus_blur, 0, Qt.AlignmentFlag.AlignRight)
        focus_l.addLayout(fblur_row)

        self.slider_focus_blur = QSlider(Qt.Orientation.Horizontal)
        self.slider_focus_blur.setRange(5, 35)
        self.slider_focus_blur.setValue(self.filters.focus_blur)
        self.slider_focus_blur.valueChanged.connect(self._update_filters)
        focus_l.addWidget(self.slider_focus_blur)

        fimg_row = QHBoxLayout()
        self.btn_choose_bg_img = QPushButton("Arkaplan Resmi Seç...")
        self.btn_choose_bg_img.clicked.connect(self._choose_focus_background_image)
        fimg_row.addWidget(self.btn_choose_bg_img)
        self.lbl_bg_img_path = QLabel(os.path.basename(self.filters.focus_image_path) if self.filters.focus_image_path else "Resim seçilmedi")
        self.lbl_bg_img_path.setStyleSheet("color: #8c909f; font-size: 11px; font-family: 'JetBrains Mono', monospace;")
        fimg_row.addWidget(self.lbl_bg_img_path, 1)
        focus_l.addLayout(fimg_row)

        filters_layout.addWidget(focus_box)

        # SECTION 3: RAW Pozlama & Işık Tonları
        self.tone_box = tone_box = QGroupBox("RAW Pozlama && Işık Tonları")
        tone_layout = QVBoxLayout(tone_box)
        tone_layout.setSpacing(8)

        # Exposure (-2.0 EV to +2.0 EV)
        exp_row = QHBoxLayout()
        self.lbl_exp = QLabel("Pozlama (Exposure):")
        exp_row.addWidget(self.lbl_exp)
        self.lbl_exposure = ValueBadgeEdit(f"{self.filters.exposure:+.1f} EV", is_float=True, min_val=-2.0, max_val=2.0, suffix=" EV")
        self.lbl_exposure.setObjectName("lbl_value_badge")
        self.lbl_exposure.userValueChanged.connect(lambda v: self.slider_exposure.setValue(int(round(v * 10))))
        exp_row.addWidget(self.lbl_exposure, 0, Qt.AlignmentFlag.AlignRight)
        tone_layout.addLayout(exp_row)

        self.slider_exposure = QSlider(Qt.Orientation.Horizontal)
        self.slider_exposure.setRange(-20, 20)
        self.slider_exposure.setValue(int(round(self.filters.exposure * 10)))
        self.slider_exposure.valueChanged.connect(self._update_filters)
        tone_layout.addWidget(self.slider_exposure)

        # Highlights
        high_row = QHBoxLayout()
        self.lbl_high = QLabel("Açık Tonlar (Highlights):")
        high_row.addWidget(self.lbl_high)
        self.lbl_highlights = ValueBadgeEdit(str(self.filters.highlights), min_val=-100, max_val=100)
        self.lbl_highlights.setObjectName("lbl_value_badge")
        self.lbl_highlights.userValueChanged.connect(lambda v: self.slider_highlights.setValue(int(round(v))))
        high_row.addWidget(self.lbl_highlights, 0, Qt.AlignmentFlag.AlignRight)
        tone_layout.addLayout(high_row)

        self.slider_highlights = QSlider(Qt.Orientation.Horizontal)
        self.slider_highlights.setRange(-100, 100)
        self.slider_highlights.setValue(self.filters.highlights)
        self.slider_highlights.valueChanged.connect(self._update_filters)
        tone_layout.addWidget(self.slider_highlights)

        # Shadows
        shadow_row = QHBoxLayout()
        self.lbl_shadow = QLabel("Gölgeler (Shadows):")
        shadow_row.addWidget(self.lbl_shadow)
        self.lbl_shadows = ValueBadgeEdit(str(self.filters.shadows), min_val=-100, max_val=100)
        self.lbl_shadows.setObjectName("lbl_value_badge")
        self.lbl_shadows.userValueChanged.connect(lambda v: self.slider_shadows.setValue(int(round(v))))
        shadow_row.addWidget(self.lbl_shadows, 0, Qt.AlignmentFlag.AlignRight)
        tone_layout.addLayout(shadow_row)

        self.slider_shadows = QSlider(Qt.Orientation.Horizontal)
        self.slider_shadows.setRange(-100, 100)
        self.slider_shadows.setValue(self.filters.shadows)
        self.slider_shadows.valueChanged.connect(self._update_filters)
        tone_layout.addWidget(self.slider_shadows)

        # Whites
        whites_row = QHBoxLayout()
        self.lbl_whites_title = QLabel("Beyazlar (Whites):")
        whites_row.addWidget(self.lbl_whites_title)
        self.lbl_whites = ValueBadgeEdit(str(self.filters.whites), min_val=-100, max_val=100)
        self.lbl_whites.setObjectName("lbl_value_badge")
        self.lbl_whites.userValueChanged.connect(lambda v: self.slider_whites.setValue(int(round(v))))
        whites_row.addWidget(self.lbl_whites, 0, Qt.AlignmentFlag.AlignRight)
        tone_layout.addLayout(whites_row)

        self.slider_whites = QSlider(Qt.Orientation.Horizontal)
        self.slider_whites.setRange(-100, 100)
        self.slider_whites.setValue(self.filters.whites)
        self.slider_whites.valueChanged.connect(self._update_filters)
        tone_layout.addWidget(self.slider_whites)

        # Blacks
        blacks_row = QHBoxLayout()
        self.lbl_blacks_title = QLabel("Siyahlar (Blacks):")
        blacks_row.addWidget(self.lbl_blacks_title)
        self.lbl_blacks = ValueBadgeEdit(str(self.filters.blacks), min_val=-100, max_val=100)
        self.lbl_blacks.setObjectName("lbl_value_badge")
        self.lbl_blacks.userValueChanged.connect(lambda v: self.slider_blacks.setValue(int(round(v))))
        blacks_row.addWidget(self.lbl_blacks, 0, Qt.AlignmentFlag.AlignRight)
        tone_layout.addLayout(blacks_row)

        self.slider_blacks = QSlider(Qt.Orientation.Horizontal)
        self.slider_blacks.setRange(-100, 100)
        self.slider_blacks.setValue(self.filters.blacks)
        self.slider_blacks.valueChanged.connect(self._update_filters)
        tone_layout.addWidget(self.slider_blacks)

        # Contrast
        contrast_row = QHBoxLayout()
        self.lbl_contrast_title = QLabel("Karşıtlık (Kontrast):")
        contrast_row.addWidget(self.lbl_contrast_title)
        self.lbl_contrast = ValueBadgeEdit(str(self.filters.contrast), min_val=-100, max_val=100)
        self.lbl_contrast.setObjectName("lbl_value_badge")
        self.lbl_contrast.userValueChanged.connect(lambda v: self.slider_contrast.setValue(int(round(v))))
        contrast_row.addWidget(self.lbl_contrast, 0, Qt.AlignmentFlag.AlignRight)
        tone_layout.addLayout(contrast_row)

        self.slider_contrast = QSlider(Qt.Orientation.Horizontal)
        self.slider_contrast.setRange(-100, 100)
        self.slider_contrast.setValue(self.filters.contrast)
        self.slider_contrast.valueChanged.connect(self._update_filters)
        tone_layout.addWidget(self.slider_contrast)

        # Brightness
        bright_row = QHBoxLayout()
        self.lbl_bright_title = QLabel("Parlaklık:")
        bright_row.addWidget(self.lbl_bright_title)
        self.lbl_bright = ValueBadgeEdit(str(self.filters.brightness), min_val=-100, max_val=100)
        self.lbl_bright.setObjectName("lbl_value_badge")
        self.lbl_bright.userValueChanged.connect(lambda v: self.slider_bright.setValue(int(round(v))))
        bright_row.addWidget(self.lbl_bright, 0, Qt.AlignmentFlag.AlignRight)
        tone_layout.addLayout(bright_row)

        self.slider_bright = QSlider(Qt.Orientation.Horizontal)
        self.slider_bright.setRange(-100, 100)
        self.slider_bright.setValue(self.filters.brightness)
        self.slider_bright.valueChanged.connect(self._update_filters)
        tone_layout.addWidget(self.slider_bright)

        filters_layout.addWidget(tone_box)

        # SECTION 4: Beyaz Dengesi & Renk
        self.color_box = color_box = QGroupBox("Beyaz Dengesi && Renk")
        color_layout = QVBoxLayout(color_box)
        color_layout.setSpacing(8)

        # Temperature
        temp_row = QHBoxLayout()
        self.lbl_temp_title = QLabel("Renk Sıcaklığı (Mavi ↔ Sarı):")
        temp_row.addWidget(self.lbl_temp_title)
        self.lbl_temp = ValueBadgeEdit(_t("val_natural") if self.filters.temperature == 0 else f"{self.filters.temperature:+d}", min_val=-100, max_val=100)
        self.lbl_temp.setObjectName("lbl_value_badge")
        self.lbl_temp.userValueChanged.connect(lambda v: self.slider_temp.setValue(int(round(v))))
        temp_row.addWidget(self.lbl_temp, 0, Qt.AlignmentFlag.AlignRight)
        color_layout.addLayout(temp_row)

        self.slider_temp = QSlider(Qt.Orientation.Horizontal)
        self.slider_temp.setRange(-100, 100)
        self.slider_temp.setValue(self.filters.temperature)
        self.slider_temp.valueChanged.connect(self._update_filters)
        color_layout.addWidget(self.slider_temp)

        # Tint
        tint_row = QHBoxLayout()
        self.lbl_tint_title = QLabel("Renk Tonu (Yeşil ↔ Macenta):")
        tint_row.addWidget(self.lbl_tint_title)
        self.lbl_tint = ValueBadgeEdit(_t("val_natural") if self.filters.tint == 0 else f"{self.filters.tint:+d}", min_val=-100, max_val=100)
        self.lbl_tint.setObjectName("lbl_value_badge")
        self.lbl_tint.userValueChanged.connect(lambda v: self.slider_tint.setValue(int(round(v))))
        tint_row.addWidget(self.lbl_tint, 0, Qt.AlignmentFlag.AlignRight)
        color_layout.addLayout(tint_row)

        self.slider_tint = QSlider(Qt.Orientation.Horizontal)
        self.slider_tint.setRange(-100, 100)
        self.slider_tint.setValue(self.filters.tint)
        self.slider_tint.valueChanged.connect(self._update_filters)
        color_layout.addWidget(self.slider_tint)

        # Vibrance
        vib_row = QHBoxLayout()
        self.lbl_vib_title = QLabel("Canlılık (Vibrance):")
        vib_row.addWidget(self.lbl_vib_title)
        self.lbl_vibrance = ValueBadgeEdit(str(self.filters.vibrance), min_val=-100, max_val=100)
        self.lbl_vibrance.setObjectName("lbl_value_badge")
        self.lbl_vibrance.userValueChanged.connect(lambda v: self.slider_vibrance.setValue(int(round(v))))
        vib_row.addWidget(self.lbl_vibrance, 0, Qt.AlignmentFlag.AlignRight)
        color_layout.addLayout(vib_row)

        self.slider_vibrance = QSlider(Qt.Orientation.Horizontal)
        self.slider_vibrance.setRange(-100, 100)
        self.slider_vibrance.setValue(self.filters.vibrance)
        self.slider_vibrance.valueChanged.connect(self._update_filters)
        color_layout.addWidget(self.slider_vibrance)

        # Saturation
        sat_row = QHBoxLayout()
        self.lbl_sat_title = QLabel("Doygunluk:")
        sat_row.addWidget(self.lbl_sat_title)
        self.lbl_sat = ValueBadgeEdit(f"{self.filters.saturation}%", min_val=0, max_val=200, suffix="%")
        self.lbl_sat.setObjectName("lbl_value_badge")
        self.lbl_sat.userValueChanged.connect(lambda v: self.slider_sat.setValue(int(round(v))))
        sat_row.addWidget(self.lbl_sat, 0, Qt.AlignmentFlag.AlignRight)
        color_layout.addLayout(sat_row)

        self.slider_sat = QSlider(Qt.Orientation.Horizontal)
        self.slider_sat.setRange(0, 200)
        self.slider_sat.setValue(self.filters.saturation)
        self.slider_sat.valueChanged.connect(self._update_filters)
        color_layout.addWidget(self.slider_sat)

        # Tone Curve Presets
        curve_row = QHBoxLayout()
        self.lbl_curve = QLabel("Ton Eğrisi Profili:")
        curve_row.addWidget(self.lbl_curve)
        self.combo_tone_curve = QComboBox()
        self.combo_tone_curve.addItem("Doğal (Doğrusal)", "linear")
        self.combo_tone_curve.addItem("Film / Sinematik", "film")
        self.combo_tone_curve.addItem("Portre (Yumuşak)", "portrait")
        self.combo_tone_curve.addItem("Canlı (Vivid)", "vivid")
        self.combo_tone_curve.addItem("Vintage (Mat)", "vintage")
        curve_idx = self.combo_tone_curve.findData(self.filters.tone_curve)
        if curve_idx >= 0:
            self.combo_tone_curve.setCurrentIndex(curve_idx)
        self.combo_tone_curve.currentIndexChanged.connect(self._update_filters)
        curve_row.addWidget(self.combo_tone_curve)
        color_layout.addLayout(curve_row)

        filters_layout.addWidget(color_box)

        # SECTION 5: Gelişmiş Renk Dengesi (RGB Kanalları)
        self.rgb_box = rgb_box = QGroupBox("Gelişmiş Renk Dengesi (RGB Kanalları)")
        rgb_layout = QVBoxLayout(rgb_box)
        rgb_layout.setSpacing(8)

        # Red Gain
        r_row = QHBoxLayout()
        self.lbl_r = QLabel("Kırmızı Dengesi (R):")
        r_row.addWidget(self.lbl_r)
        self.lbl_gain_r = ValueBadgeEdit(f"{self.filters.red_gain:+d}", min_val=-50, max_val=50)
        self.lbl_gain_r.setObjectName("lbl_value_badge")
        self.lbl_gain_r.userValueChanged.connect(lambda v: self.slider_gain_r.setValue(int(round(v))))
        r_row.addWidget(self.lbl_gain_r, 0, Qt.AlignmentFlag.AlignRight)
        rgb_layout.addLayout(r_row)

        self.slider_gain_r = QSlider(Qt.Orientation.Horizontal)
        self.slider_gain_r.setRange(-50, 50)
        self.slider_gain_r.setValue(self.filters.red_gain)
        self.slider_gain_r.valueChanged.connect(self._update_filters)
        rgb_layout.addWidget(self.slider_gain_r)

        # Green Gain
        g_row = QHBoxLayout()
        self.lbl_g = QLabel("Yeşil Dengesi (G):")
        g_row.addWidget(self.lbl_g)
        self.lbl_gain_g = ValueBadgeEdit(f"{self.filters.green_gain:+d}", min_val=-50, max_val=50)
        self.lbl_gain_g.setObjectName("lbl_value_badge")
        self.lbl_gain_g.userValueChanged.connect(lambda v: self.slider_gain_g.setValue(int(round(v))))
        g_row.addWidget(self.lbl_gain_g, 0, Qt.AlignmentFlag.AlignRight)
        rgb_layout.addLayout(g_row)

        self.slider_gain_g = QSlider(Qt.Orientation.Horizontal)
        self.slider_gain_g.setRange(-50, 50)
        self.slider_gain_g.setValue(self.filters.green_gain)
        self.slider_gain_g.valueChanged.connect(self._update_filters)
        rgb_layout.addWidget(self.slider_gain_g)

        # Blue Gain
        b_row = QHBoxLayout()
        self.lbl_b = QLabel("Mavi Dengesi (B):")
        b_row.addWidget(self.lbl_b)
        self.lbl_gain_b = ValueBadgeEdit(f"{self.filters.blue_gain:+d}", min_val=-50, max_val=50)
        self.lbl_gain_b.setObjectName("lbl_value_badge")
        self.lbl_gain_b.userValueChanged.connect(lambda v: self.slider_gain_b.setValue(int(round(v))))
        b_row.addWidget(self.lbl_gain_b, 0, Qt.AlignmentFlag.AlignRight)
        rgb_layout.addLayout(b_row)

        self.slider_gain_b = QSlider(Qt.Orientation.Horizontal)
        self.slider_gain_b.setRange(-50, 50)
        self.slider_gain_b.setValue(self.filters.blue_gain)
        self.slider_gain_b.valueChanged.connect(self._update_filters)
        rgb_layout.addWidget(self.slider_gain_b)

        filters_layout.addWidget(rgb_box)

        # SECTION 6: Detay & Geometri
        self.detail_box = detail_box = QGroupBox(_t("detail_geometry"))
        detail_layout = QVBoxLayout(detail_box)
        detail_layout.setSpacing(8)

        # True Laplacian Sharpness
        sharp_row = QHBoxLayout()
        self.lbl_sharp_title = QLabel(_t("laplacian_sharpness"))
        sharp_row.addWidget(self.lbl_sharp_title)
        self.lbl_sharp = ValueBadgeEdit(_t("val_off") if self.filters.sharpness == 0 else f"{self.filters.sharpness}%", min_val=0, max_val=100, suffix="%")
        self.lbl_sharp.setObjectName("lbl_value_badge")
        self.lbl_sharp.userValueChanged.connect(lambda v: self.slider_sharp.setValue(int(round(v))))
        sharp_row.addWidget(self.lbl_sharp, 0, Qt.AlignmentFlag.AlignRight)
        detail_layout.addLayout(sharp_row)

        self.slider_sharp = QSlider(Qt.Orientation.Horizontal)
        self.slider_sharp.setRange(0, 100)
        self.slider_sharp.setValue(self.filters.sharpness)
        self.slider_sharp.valueChanged.connect(self._update_filters)
        detail_layout.addWidget(self.slider_sharp)

        # Checkboxes
        chk_grid = QGridLayout()
        self.chk_flip_h = QCheckBox(_t("flip_h"))
        self.chk_flip_h.setChecked(self.filters.flip_h)
        self.chk_flip_h.stateChanged.connect(self._update_filters)
        chk_grid.addWidget(self.chk_flip_h, 0, 0)

        self.chk_flip_v = QCheckBox(_t("flip_v"))
        self.chk_flip_v.setChecked(self.filters.flip_v)
        self.chk_flip_v.stateChanged.connect(self._update_filters)
        chk_grid.addWidget(self.chk_flip_v, 0, 1)

        self.chk_gray = QCheckBox(_t("grayscale"))
        self.chk_gray.setChecked(self.filters.grayscale)
        self.chk_gray.stateChanged.connect(self._update_filters)
        chk_grid.addWidget(self.chk_gray, 1, 0)

        self.chk_invert = QCheckBox(_t("invert_colors"))
        self.chk_invert.setChecked(self.filters.invert)
        self.chk_invert.stateChanged.connect(self._update_filters)
        chk_grid.addWidget(self.chk_invert, 1, 1)
        detail_layout.addLayout(chk_grid)

        # Rotation
        rot_layout = QHBoxLayout()
        self.lbl_rot_title = QLabel(_t("rotation") + ":")
        rot_layout.addWidget(self.lbl_rot_title)
        self.combo_rot = QComboBox()
        self.combo_rot.addItems(["0°", "90°", "180°", "270°"])
        rot_idx = {0: 0, 90: 1, 180: 2, 270: 3}.get(self.filters.rotation, 0)
        self.combo_rot.setCurrentIndex(rot_idx)
        self.combo_rot.currentIndexChanged.connect(self._update_filters)
        rot_layout.addWidget(self.combo_rot)
        detail_layout.addLayout(rot_layout)

        filters_layout.addWidget(detail_box)

        # Reset button
        self.btn_reset_filters = QPushButton(_t("btn_reset_all_raw"))
        self.btn_reset_filters.clicked.connect(self._reset_filters)
        filters_layout.addWidget(self.btn_reset_filters)

        filters_layout.addStretch()

        scroll_area.setWidget(filters_tab)
        self.control_tabs.addTab(scroll_area, _t("tab_raw"))

        # TAB 3: Advanced Stream & Driver Settings
        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setFrameShape(QFrame.Shape.NoFrame)
        settings_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        settings_layout.setContentsMargins(10, 10, 10, 10)
        settings_layout.setSpacing(8)

        # Resolution (16:9, 9:16 Portrait, 4:3, 3:4 Portrait, 1:1 Square)
        self.lbl_settings_res = QLabel(_t("settings_res_title"))
        settings_layout.addWidget(self.lbl_settings_res)
        self.combo_res = QComboBox()
        res_list = [
            ("1920x1080", f"1920x1080 (1080p FHD - {_t('aspect_16_9_landscape')})"),
            ("1080x1920", f"1080x1920 (1080p FHD - {_t('aspect_9_16_portrait')})"),
            ("1280x720", f"1280x720 (720p HD - {_t('aspect_16_9_landscape')})"),
            ("720x1280", f"720x1280 (720p HD - {_t('aspect_9_16_portrait')})"),
            ("1440x1080", f"1440x1080 (1080p - {_t('aspect_4_3_landscape')})"),
            ("1080x1440", f"1080x1440 (1080p - {_t('aspect_3_4_portrait')})"),
            ("1080x1080", f"1080x1080 (1080p - {_t('aspect_1_1_square')})"),
            ("720x720", f"720x720 (720p - {_t('aspect_1_1_square')})"),
            ("3840x2160", f"3840x2160 (4K UHD - {_t('aspect_16_9_landscape')})"),
            ("2560x1440", f"2560x1440 (2K QHD - {_t('aspect_16_9_landscape')})"),
            ("960x720", f"960x720 (720p - {_t('aspect_4_3_landscape')})"),
            ("854x480", f"854x480 (480p SD - {_t('aspect_16_9_landscape')})"),
            ("640x480", f"640x480 (480p SD - {_t('aspect_4_3_landscape')})"),
        ]
        for val, label in res_list:
            self.combo_res.addItem(label, val)
        saved_res = self.config.get("resolution", "1920x1080").split()[0]
        for i in range(self.combo_res.count()):
            if self.combo_res.itemData(i) == saved_res or self.combo_res.itemText(i).startswith(saved_res):
                self.combo_res.setCurrentIndex(i)
                break
        self.combo_quick_aspect.blockSignals(True)
        for i in range(self.combo_quick_aspect.count()):
            if self.combo_quick_aspect.itemData(i) == saved_res:
                self.combo_quick_aspect.setCurrentIndex(i)
                break
        self.combo_quick_aspect.blockSignals(False)
        settings_layout.addWidget(self.combo_res)

        # FPS
        self.lbl_settings_fps = QLabel(_t("settings_fps_title"))
        settings_layout.addWidget(self.lbl_settings_fps)
        self.combo_fps = QComboBox()
        self.combo_fps.addItems(["60 FPS", "30 FPS", "24 FPS", "15 FPS"])
        saved_fps = f"{self.config.get('fps', 30)} FPS"
        self.combo_fps.setCurrentText(saved_fps)
        settings_layout.addWidget(self.combo_fps)

        # Bitrate
        self.lbl_settings_bitrate = QLabel(_t("settings_bitrate_title"))
        settings_layout.addWidget(self.lbl_settings_bitrate)
        self.combo_bitrate = QComboBox()
        self.combo_bitrate.addItems([
            _t("br_50"),
            _t("br_35"),
            _t("br_25"),
            _t("br_20"),
            _t("br_16"),
            _t("br_12"),
            _t("br_8"),
            _t("br_6"),
            _t("br_4"),
            _t("br_2")
        ])
        saved_bitrate_mbps = max(1, int(self.config.get("bitrate", 8000000)) // 1000000)
        matched_br = False
        for i in range(self.combo_bitrate.count()):
            if self.combo_bitrate.itemText(i).startswith(f"{saved_bitrate_mbps} "):
                self.combo_bitrate.setCurrentIndex(i)
                matched_br = True
                break
        if not matched_br:
            self.combo_bitrate.setCurrentIndex(6) # 8 Mbps default
        settings_layout.addWidget(self.combo_bitrate)

        # Codec
        self.lbl_settings_codec = QLabel(_t("settings_codec_title"))
        settings_layout.addWidget(self.lbl_settings_codec)
        self.combo_codec = QComboBox()
        self.combo_codec.addItem(_t("codec_h264_dropdown"), "h264")
        self.combo_codec.addItem(_t("codec_h265_dropdown"), "hevc")
        if str(self.config.get("codec", "h264")).lower() in ("hevc", "h265"):
            self.combo_codec.setCurrentIndex(1)
        settings_layout.addWidget(self.combo_codec)

        # Virtual Webcam Device (Configured & loaded automatically in background)
        self.combo_v4l2_devs = QComboBox()
        self._refresh_v4l2_devices()
        self.btn_load_v4l2 = QPushButton("Sanal Kamerayı Yükle")
        self.btn_load_v4l2.clicked.connect(self._load_v4l2_module)
        # Note: kept headless and not added to settings_layout for clean end-user experience

        # Apply settings button
        self.btn_apply_settings = QPushButton("Ayarları Telefona Gönder ve Uygula")
        self.btn_apply_settings.setObjectName("btn_action")
        self.btn_apply_settings.clicked.connect(self._apply_stream_settings)
        settings_layout.addWidget(self.btn_apply_settings)

        settings_layout.addStretch()
        settings_scroll.setWidget(settings_tab)
        self.control_tabs.addTab(settings_scroll, "Ayarlar")

        right_layout.addWidget(self.control_tabs)

        # Inspector Footer Action & Diagnostics (Token CTA & Footer Tabs from Stitch)
        insp_footer = QVBoxLayout()
        insp_footer.setSpacing(8)

        # CTA: Ayarları Gönder (From Stitch design)
        self.btn_apply_settings_cta = QPushButton("Ayarları Gönder")
        self.btn_apply_settings_cta.setObjectName("btn_action")
        self.btn_apply_settings_cta.setMinimumHeight(38)
        self.btn_apply_settings_cta.clicked.connect(self._apply_stream_settings)
        insp_footer.addWidget(self.btn_apply_settings_cta)

        right_layout.addLayout(insp_footer)

        splitter.addWidget(right_container)

        splitter.setSizes([850, 490])
        main_layout.addWidget(splitter, stretch=1)

        # 4. Master App Bottom Status Footer Bar (from Stitch design)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.lbl_v4l2_status = QLabel("Sanal Kamera: Hazır")
        self.lbl_v4l2_status.setStyleSheet("color: #4edea3; font-weight: 600; background: transparent; margin-right: 12px; font-family: 'JetBrains Mono', monospace;")
        self.status_bar.addPermanentWidget(self.lbl_v4l2_status)

        sep_sb = QLabel("│")
        sep_sb.setStyleSheet("color: rgba(255, 255, 255, 0.15); margin-right: 12px;")
        self.status_bar.addPermanentWidget(sep_sb)

        self.lbl_mic_status = QLabel("Sanal Mikrofon: Hazır")
        self.lbl_mic_status.setStyleSheet("color: #adc6ff; font-weight: 600; background: transparent; margin-right: 14px; font-family: 'JetBrains Mono', monospace;")
        self.status_bar.addPermanentWidget(self.lbl_mic_status)

        self.status_bar.showMessage("● AselCam hazır. Cihazınızı USB hata ayıklama ile bağlayın.")

        # Populate ADB devices initially
        self._refresh_adb_devices()

    def retranslate_ui(self):
        """Refreshes all UI text labels, tooltips, buttons, and placeholders for the active language."""
        # 1. Custom Title Bar
        if hasattr(self, "title_bar"):
            self.title_bar.btn_min.setToolTip(_t("win_min"))
            self.title_bar.btn_max.setToolTip(_t("win_max"))
            self.title_bar.btn_close.setToolTip(_t("win_close"))
            self.title_bar.badge_version.setText(_t("version_tag"))
            curr_model = getattr(self, "_last_device_model", "—")
            self.lbl_device_info.setText(f"{_t('label_device')} {curr_model}")
            curr_batt = getattr(self, "_last_battery_level", "—")
            self.lbl_battery.setText(f"{_t('label_battery')} {curr_batt}%" if curr_batt != "—" else f"{_t('label_battery')} —%")
            curr_ping = getattr(self, "_last_ping", -1)
            self.lbl_ping.setText(f"{_t('label_ping')} {curr_ping:.0f} ms" if curr_ping >= 0 else f"{_t('label_ping')} — ms")
            self.title_bar.status_badge.setText(_t("status_live") if self.is_connected else _t("status_offline"))

        # 2. Connection Strip
        if hasattr(self, "btn_mode_usb"):
            self.btn_mode_usb.setText(_t("conn_usb"))
            self.btn_mode_wifi.setText(_t("conn_wifi"))
            if self.is_connected:
                self.btn_master_connect.setText(_t("conn_btn_stop"))
            else:
                self.btn_master_connect.setText(_t("conn_btn_start"))
            self.btn_refresh_adb.setText(_t("refresh"))
            self.btn_refresh_adb.setToolTip(_t("refresh"))
            self.txt_ip.setPlaceholderText(_t("conn_ip_placeholder"))
        if hasattr(self, "lbl_v4l2_indicator"):
            self.lbl_v4l2_indicator.setText(_t("driver_status_ready"))

        # 3. Video dock controls
        if hasattr(self, "btn_toggle_preview"):
            self.btn_toggle_preview.setText(_t("preview_toggle_off") if self.is_preview_enabled else _t("preview_toggle_on"))
            self.btn_toggle_preview.setToolTip(_t("preview_tooltip"))
            self.btn_pause_cam.setText(_t("blackout_toggle_off") if self.is_camera_paused else _t("blackout_toggle_on"))
            self.btn_mute_mic.setText(_t("mic_toggle_on") if self.is_mic_muted else _t("mic_toggle_off"))

        # 4. Inspector Header & Tabs
        if hasattr(self, "lbl_h_main"):
            self.lbl_h_main.setText(_t("hub_title"))
        if hasattr(self, "lbl_h_sub"):
            self.lbl_h_sub.setText(_t("driver_status_ready"))
        if hasattr(self, "lbl_hub_badge"):
            self.lbl_hub_badge.setText(_t("hub_badge"))
        if hasattr(self, "btn_collapse_hub"):
            self.btn_collapse_hub.setToolTip(_t("hub_collapse"))
        if hasattr(self, "btn_toggle_hub"):
            self.btn_toggle_hub.setToolTip(_t("hub_toggle"))

        if hasattr(self, "control_tabs"):
            self.control_tabs.setTabText(0, _t("tab_mobile"))
            self.control_tabs.setTabText(1, _t("tab_raw"))
            self.control_tabs.setTabText(2, _t("tab_settings"))

        # 5. Remote Mobile Tab
        if hasattr(self, "actions_box"):
            self.actions_box.setTitle(_t("ctrl_actions_title"))
            self.btn_flip_camera.setText(_t("ctrl_switch_cam"))
            self.btn_torch.setText(_t("ctrl_torch_off") if getattr(self, "_remote_torch_on", False) else _t("ctrl_torch_on"))
            self.btn_remote_preview.setText(_t("ctrl_phone_preview_on") if not getattr(self, "_remote_phone_preview_on", True) else _t("ctrl_phone_preview_off"))
            self.btn_remote_blackout.setText(_t("ctrl_wake_screen") if getattr(self, "_remote_blackout_on", False) else _t("ctrl_blackout_on"))

        # Screen Mirroring button
        if hasattr(self, "btn_screen_mirror"):
            is_mirror = getattr(self, "is_screen_mirror_active", False)
            self.btn_screen_mirror.setText(_t("ctrl_back_to_cam_btn") if is_mirror else _t("ctrl_screen_mirror_btn"))

        # Camera Dropdown
        if hasattr(self, "combo_remote_camera"):
            if getattr(self, "_loaded_cameras", None):
                self._update_camera_list(self._loaded_cameras, self.combo_remote_camera.currentData())
            else:
                curr_idx = self.combo_remote_camera.currentIndex()
                self.combo_remote_camera.blockSignals(True)
                self.combo_remote_camera.clear()
                self.combo_remote_camera.addItem(_t("cam_rear_default"), "0")
                self.combo_remote_camera.addItem(_t("cam_front_item"), "1")
                self.combo_remote_camera.setCurrentIndex(curr_idx if curr_idx >= 0 else 0)
                self.combo_remote_camera.blockSignals(False)

        # Quick Aspect Ratio Selector
        if hasattr(self, "aspect_box"):
            self.aspect_box.setTitle(_t("aspect_header"))
        if hasattr(self, "combo_quick_aspect"):
            curr_data = self.combo_quick_aspect.currentData()
            self.combo_quick_aspect.blockSignals(True)
            self.combo_quick_aspect.clear()
            self.combo_quick_aspect.addItem(f"16:9 {_t('aspect_16_9_landscape')} (1920x1080)", "1920x1080")
            self.combo_quick_aspect.addItem(f"9:16 {_t('aspect_9_16_portrait')} (1080x1920)", "1080x1920")
            self.combo_quick_aspect.addItem(f"4:3 {_t('aspect_4_3_landscape')} (1440x1080)", "1440x1080")
            self.combo_quick_aspect.addItem(f"3:4 {_t('aspect_3_4_portrait')} (1080x1440)", "1080x1440")
            self.combo_quick_aspect.addItem(f"1:1 {_t('aspect_1_1_square')} (1080x1080)", "1080x1080")
            self.combo_quick_aspect.addItem(f"9:16 {_t('aspect_9_16_portrait')} HD (720x1280)", "720x1280")
            idx = self.combo_quick_aspect.findData(curr_data)
            if idx >= 0:
                self.combo_quick_aspect.setCurrentIndex(idx)
            self.combo_quick_aspect.blockSignals(False)

        # Zoom
        if hasattr(self, "zoom_box"):
            self.zoom_box.setTitle(_t("zoom_header"))
            if hasattr(self, "lbl_zoom_title"):
                self.lbl_zoom_title.setText(_t("zoom_title"))

        # 6. RAW & Color Tab
        if hasattr(self, "profile_box"):
            self.profile_box.setTitle(_t("color_profiles"))
            if hasattr(self, "lbl_prof_title"):
                self.lbl_prof_title.setText(_t("color_profiles") + ":")

        # Profile ComboBox
        if hasattr(self, "combo_color_profile"):
            current_data = self.combo_color_profile.currentData()
            self.combo_color_profile.blockSignals(True)
            self.combo_color_profile.clear()
            for key in ["standard", "vivid", "cinema", "portrait", "lowlight", "vintage", "bw", "custom"]:
                self.combo_color_profile.addItem(_t(f"profile_{key}"), key)
            idx = self.combo_color_profile.findData(current_data)
            if idx >= 0:
                self.combo_color_profile.setCurrentIndex(idx)
            self.combo_color_profile.blockSignals(False)

        # Focus Box
        if hasattr(self, "focus_box"):
            self.focus_box.setTitle(_t("focus_header"))
            self.chk_focus_enabled.setText(_t("focus_enable"))
            if hasattr(self, "lbl_fmode"):
                self.lbl_fmode.setText(_t("focus_mode"))
            if hasattr(self, "combo_focus_mode"):
                curr_fmode = self.combo_focus_mode.currentData()
                self.combo_focus_mode.blockSignals(True)
                self.combo_focus_mode.clear()
                self.combo_focus_mode.addItem(_t("focus_mode_blur"), "blur")
                self.combo_focus_mode.addItem(_t("focus_mode_studio"), "studio")
                self.combo_focus_mode.addItem(_t("focus_mode_custom"), "custom")
                fidx = self.combo_focus_mode.findData(curr_fmode)
                if fidx >= 0:
                    self.combo_focus_mode.setCurrentIndex(fidx)
                self.combo_focus_mode.blockSignals(False)
            if hasattr(self, "lbl_frad"):
                self.lbl_frad.setText(_t("focus_radius") + ":")
            if hasattr(self, "lbl_fblur"):
                self.lbl_fblur.setText(_t("focus_blur_amount") + ":")
            if hasattr(self, "btn_choose_bg_img"):
                self.btn_choose_bg_img.setText(_t("focus_choose_img"))

        # Tone & Sliders
        if hasattr(self, "tone_box"):
            self.tone_box.setTitle(_t("raw_header"))
            if hasattr(self, "lbl_exp"):
                self.lbl_exp.setText(_t("raw_exposure") + ":")
            if hasattr(self, "lbl_high"):
                self.lbl_high.setText(_t("raw_highlights") + ":")
            if hasattr(self, "lbl_shadow"):
                self.lbl_shadow.setText(_t("raw_shadows") + ":")
            if hasattr(self, "lbl_whites_title"):
                self.lbl_whites_title.setText(_t("raw_whites") + ":")
            if hasattr(self, "lbl_blacks_title"):
                self.lbl_blacks_title.setText(_t("raw_blacks") + ":")
            if hasattr(self, "lbl_contrast_title"):
                self.lbl_contrast_title.setText(_t("raw_contrast") + ":")
            if hasattr(self, "lbl_bright_title"):
                self.lbl_bright_title.setText(_t("raw_brightness") + ":")

        # Color & Temp
        if hasattr(self, "color_box"):
            self.color_box.setTitle(_t("raw_header"))
            if hasattr(self, "lbl_temp_title"):
                self.lbl_temp_title.setText(_t("raw_temp") + ":")
            if hasattr(self, "lbl_tint_title"):
                self.lbl_tint_title.setText(_t("raw_tint") + ":")
            if hasattr(self, "lbl_vib_title"):
                self.lbl_vib_title.setText(_t("raw_vibrance") + ":")
            if hasattr(self, "lbl_sat_title"):
                self.lbl_sat_title.setText(_t("raw_saturation") + ":")
            if hasattr(self, "lbl_curve"):
                self.lbl_curve.setText(_t("tone_curve") + ":")

        # Tone Curve ComboBox
        if hasattr(self, "combo_tone_curve"):
            curr_curve = self.combo_tone_curve.currentData()
            self.combo_tone_curve.blockSignals(True)
            self.combo_tone_curve.clear()
            for ckey in ["linear", "film", "portrait", "vivid", "vintage"]:
                self.combo_tone_curve.addItem(_t(f"curve_{ckey}"), ckey)
            cidx = self.combo_tone_curve.findData(curr_curve)
            if cidx >= 0:
                self.combo_tone_curve.setCurrentIndex(cidx)
            self.combo_tone_curve.blockSignals(False)

        # RGB Gains
        if hasattr(self, "rgb_box"):
            self.rgb_box.setTitle(_t("rgb_balance"))
            if hasattr(self, "lbl_r"):
                self.lbl_r.setText(_t("red_gain") + ":")
            if hasattr(self, "lbl_g"):
                self.lbl_g.setText(_t("green_gain") + ":")
            if hasattr(self, "lbl_b"):
                self.lbl_b.setText(_t("blue_gain") + ":")

        # Sharpness & Reset
        if hasattr(self, "sharp_box"):
            self.sharp_box.setTitle(_t("raw_sharpness"))
            if hasattr(self, "lbl_sharp_title"):
                self.lbl_sharp_title.setText(_t("raw_sharpness") + ":")
        if hasattr(self, "btn_reset_filters"):
            self.btn_reset_filters.setText(_t("btn_reset_all_raw"))

        # Section 6: Detay & Geometri Retranslation
        if hasattr(self, "detail_box"):
            self.detail_box.setTitle(_t("detail_geometry"))
        if hasattr(self, "lbl_sharp_title"):
            self.lbl_sharp_title.setText(_t("laplacian_sharpness"))
        if hasattr(self, "chk_flip_h"):
            self.chk_flip_h.setText(_t("flip_h"))
        if hasattr(self, "chk_flip_v"):
            self.chk_flip_v.setText(_t("flip_v"))
        if hasattr(self, "chk_gray"):
            self.chk_gray.setText(_t("grayscale"))
        if hasattr(self, "chk_invert"):
            self.chk_invert.setText(_t("invert_colors"))
        if hasattr(self, "lbl_rot_title"):
            self.lbl_rot_title.setText(_t("rotation") + ":")
        if hasattr(self, "lbl_mic_icon"):
            self.lbl_mic_icon.setText(_t("audio_label"))

        # Profile Presets Quick Action Chips Retranslation
        if hasattr(self, "prof_chip_buttons"):
            for btn_p, i18n_key in self.prof_chip_buttons:
                btn_p.setText(_t(i18n_key))

        # Dynamic Value Badges (Natural / Off when 0)
        if hasattr(self, "lbl_temp"):
            val = self.slider_temp.value() if hasattr(self, "slider_temp") else 0
            self.lbl_temp.setText(_t("val_natural") if val == 0 else f"{val:+d}")
        if hasattr(self, "lbl_tint"):
            val = self.slider_tint.value() if hasattr(self, "slider_tint") else 0
            self.lbl_tint.setText(_t("val_natural") if val == 0 else f"{val:+d}")
        if hasattr(self, "lbl_sharp"):
            val = self.slider_sharp.value() if hasattr(self, "slider_sharp") else 0
            self.lbl_sharp.setText(_t("val_off") if val == 0 else f"{val}%")

        # 7. Settings Tab
        if hasattr(self, "lbl_settings_res"):
            self.lbl_settings_res.setText(_t("settings_res_title"))
        if hasattr(self, "combo_res"):
            curr_data = self.combo_res.currentData()
            self.combo_res.blockSignals(True)
            self.combo_res.clear()
            res_list = [
                ("1920x1080", f"1920x1080 (1080p FHD - {_t('aspect_16_9_landscape')})"),
                ("1080x1920", f"1080x1920 (1080p FHD - {_t('aspect_9_16_portrait')})"),
                ("1280x720", f"1280x720 (720p HD - {_t('aspect_16_9_landscape')})"),
                ("720x1280", f"720x1280 (720p HD - {_t('aspect_9_16_portrait')})"),
                ("1440x1080", f"1440x1080 (1080p - {_t('aspect_4_3_landscape')})"),
                ("1080x1440", f"1080x1440 (1080p - {_t('aspect_3_4_portrait')})"),
                ("1080x1080", f"1080x1080 (1080p - {_t('aspect_1_1_square')})"),
                ("720x720", f"720x720 (720p - {_t('aspect_1_1_square')})"),
                ("3840x2160", f"3840x2160 (4K UHD - {_t('aspect_16_9_landscape')})"),
                ("2560x1440", f"2560x1440 (2K QHD - {_t('aspect_16_9_landscape')})"),
                ("960x720", f"960x720 (720p - {_t('aspect_4_3_landscape')})"),
                ("854x480", f"854x480 (480p SD - {_t('aspect_16_9_landscape')})"),
                ("640x480", f"640x480 (480p SD - {_t('aspect_4_3_landscape')})"),
            ]
            for val, label in res_list:
                self.combo_res.addItem(label, val)
            idx = self.combo_res.findData(curr_data)
            if idx >= 0:
                self.combo_res.setCurrentIndex(idx)
            self.combo_res.blockSignals(False)

        if hasattr(self, "lbl_settings_fps"):
            self.lbl_settings_fps.setText(_t("settings_fps_title"))
        if hasattr(self, "lbl_settings_bitrate"):
            self.lbl_settings_bitrate.setText(_t("settings_bitrate_title"))
        if hasattr(self, "combo_bitrate"):
            curr_idx = self.combo_bitrate.currentIndex()
            self.combo_bitrate.blockSignals(True)
            self.combo_bitrate.clear()
            self.combo_bitrate.addItems([
                _t("br_50"), _t("br_35"), _t("br_25"), _t("br_20"),
                _t("br_16"), _t("br_12"), _t("br_8"), _t("br_6"),
                _t("br_4"), _t("br_2")
            ])
            self.combo_bitrate.setCurrentIndex(curr_idx if curr_idx >= 0 else 6)
            self.combo_bitrate.blockSignals(False)

        if hasattr(self, "lbl_settings_codec"):
            self.lbl_settings_codec.setText(_t("settings_codec_title"))
        if hasattr(self, "combo_codec"):
            curr_idx = self.combo_codec.currentIndex()
            self.combo_codec.blockSignals(True)
            self.combo_codec.clear()
            self.combo_codec.addItem(_t("codec_h264_dropdown"), "h264")
            self.combo_codec.addItem(_t("codec_h265_dropdown"), "hevc")
            self.combo_codec.setCurrentIndex(curr_idx if curr_idx >= 0 else 0)
            self.combo_codec.blockSignals(False)

        if hasattr(self, "combo_adb_devices"):
            if self.combo_adb_devices.count() == 1 and not self.combo_adb_devices.itemData(0):
                self.combo_adb_devices.setItemText(0, _t("device_not_found"))
        if hasattr(self, "combo_v4l2_devs"):
            if self.combo_v4l2_devs.count() == 1 and "/dev/video10" in self.combo_v4l2_devs.itemData(0):
                self.combo_v4l2_devs.setItemText(0, _t("v4l2_will_create").format(dev="/dev/video10"))

        if hasattr(self, "btn_apply_settings"):
            self.btn_apply_settings.setText(_t("settings_btn_apply"))
        if hasattr(self, "btn_apply_settings_cta"):
            self.btn_apply_settings_cta.setText(_t("settings_btn_cta"))
        if hasattr(self, "lbl_v4l2_status"):
            self.lbl_v4l2_status.setText(_t("vcam_status_ready") if not self.is_connected else _t("vcam_status_active"))
        if hasattr(self, "lbl_mic_status"):
            self.lbl_mic_status.setText(_t("mic_status_ready") if not self.is_mic_muted else _t("mic_status_muted"))
        if hasattr(self, "tray_action_show"):
            self.tray_action_show.setText(_t("tray_show"))
        if hasattr(self, "tray_action_quit"):
            self.tray_action_quit.setText(_t("tray_quit"))

        if hasattr(self, "status_bar"):
            if self.is_connected and getattr(self, "_last_fps", 0) > 0:
                self._update_status_bar_stats()
            elif not self.is_connected:
                self.status_bar.showMessage(_t("footer_ready"))

        # Repaint video widget
        if hasattr(self, "video_widget"):
            self.video_widget.update()

        # Run Auto-Size engine to adaptively scale buttons and bounds for active language
        self.auto_size_ui()

    def auto_size_ui(self):
        """
        Dynamically calculates text metrics and resizes buttons, dock frames,
        splitters, and window bounds to perfectly accommodate any active language
        (TR, EN, DE, FR, ES, RU, JA, AR) without text clipping or layout overflow.
        """
        try:
            # 1. Adapt Connection Strip buttons
            if hasattr(self, "btn_mode_usb"):
                w = self.btn_mode_usb.fontMetrics().horizontalAdvance(self.btn_mode_usb.text()) + 28
                self.btn_mode_usb.setMinimumWidth(max(80, w))
            if hasattr(self, "btn_mode_wifi"):
                w = self.btn_mode_wifi.fontMetrics().horizontalAdvance(self.btn_mode_wifi.text()) + 28
                self.btn_mode_wifi.setMinimumWidth(max(80, w))
            if hasattr(self, "btn_refresh_adb"):
                w = self.btn_refresh_adb.fontMetrics().horizontalAdvance(self.btn_refresh_adb.text()) + 24
                self.btn_refresh_adb.setMinimumWidth(max(68, w))
                self.btn_refresh_adb.setFixedHeight(30)
            if hasattr(self, "btn_master_connect"):
                w = self.btn_master_connect.fontMetrics().horizontalAdvance(self.btn_master_connect.text()) + 32
                self.btn_master_connect.setMinimumWidth(max(130, w))

            # 2. Adapt Viewfinder Quick Control Dock Buttons (Below Video)
            dock_buttons = []
            if hasattr(self, "btn_toggle_preview"):
                dock_buttons.append(self.btn_toggle_preview)
            if hasattr(self, "btn_pause_cam"):
                dock_buttons.append(self.btn_pause_cam)
            if hasattr(self, "btn_mute_mic"):
                dock_buttons.append(self.btn_mute_mic)
            if hasattr(self, "btn_toggle_hub"):
                dock_buttons.append(self.btn_toggle_hub)

            total_dock_btn_w = 0
            for btn in dock_buttons:
                w = btn.fontMetrics().horizontalAdvance(btn.text()) + 24
                btn.setMinimumWidth(max(85, w))
                total_dock_btn_w += max(85, w)

            # 3. Adapt Hub #1 Action & Reset Buttons
            remote_buttons = []
            for attr in ["btn_flip_camera", "btn_torch", "btn_remote_preview", "btn_remote_blackout"]:
                if hasattr(self, attr):
                    remote_buttons.append(getattr(self, attr))
            for btn in remote_buttons:
                w = btn.fontMetrics().horizontalAdvance(btn.text()) + 18
                btn.setMinimumWidth(max(105, w))

            if hasattr(self, "btn_screen_mirror"):
                w = self.btn_screen_mirror.fontMetrics().horizontalAdvance(self.btn_screen_mirror.text()) + 28
                self.btn_screen_mirror.setMinimumWidth(max(150, w))

            if hasattr(self, "btn_reset_filters"):
                w = self.btn_reset_filters.fontMetrics().horizontalAdvance(self.btn_reset_filters.text()) + 28
                self.btn_reset_filters.setMinimumWidth(max(160, w))

            if hasattr(self, "btn_apply_settings_cta"):
                w = self.btn_apply_settings_cta.fontMetrics().horizontalAdvance(self.btn_apply_settings_cta.text()) + 28
                self.btn_apply_settings_cta.setMinimumWidth(max(160, w))

            # 3b. Adapt RAW Color Profile Chip Buttons
            if hasattr(self, "prof_chip_buttons"):
                for btn_p, _ in self.prof_chip_buttons:
                    w = btn_p.fontMetrics().horizontalAdvance(btn_p.text()) + 18
                    btn_p.setMinimumWidth(max(48, w))

            # 4. Header & Telemetry Labels
            if hasattr(self, "title_bar") and hasattr(self.title_bar, "status_badge"):
                self.title_bar.status_badge.adjustSize()
            if hasattr(self, "lbl_device_info"):
                self.lbl_device_info.adjustSize()
            if hasattr(self, "lbl_battery"):
                self.lbl_battery.adjustSize()
            if hasattr(self, "lbl_ping"):
                self.lbl_ping.adjustSize()
            if hasattr(self, "lbl_mic_icon"):
                self.lbl_mic_icon.adjustSize()

            # 5. Adaptive Splitter & Window Width
            audio_inset_w = 215
            needed_dock_w = total_dock_btn_w + audio_inset_w + 48
            min_left = max(520, needed_dock_w)
            min_right = 380

            if hasattr(self, "right_container") and self.right_container.isVisible():
                total_needed_w = min_left + min_right + 32
            else:
                total_needed_w = min_left + 40

            if self.width() < total_needed_w:
                self.resize(total_needed_w, self.height())

            if hasattr(self, "splitter"):
                curr_sizes = self.splitter.sizes()
                if len(curr_sizes) == 2:
                    current_left, current_right = curr_sizes[0], curr_sizes[1]
                    target_left = max(min_left, current_left)
                    target_right = max(min_right, current_right)
                    self.splitter.setSizes([target_left, target_right])

            if hasattr(self, "control_tabs"):
                self.control_tabs.tabBar().adjustSize()

            if self.layout():
                self.layout().activate()
            self.updateGeometry()
        except Exception as e:
            print(f"[Auto-Size] Warning during auto-sizing: {e}")

    def _parse_selected_bitrate(self) -> int:
        try:
            mbps = int(self.combo_bitrate.currentText().split()[0])
            return mbps * 1_000_000
        except Exception:
            return 4_000_000

    def _setup_signals(self):
        self.frame_received_signal.connect(self.video_widget.update_frame)
        self.stats_updated_signal.connect(self.video_widget.update_stats)
        self.stats_updated_signal.connect(self._on_stats_updated)
        self.audio_level_signal.connect(self._on_audio_level)
        self.telemetry_updated_signal.connect(self._on_telemetry_updated)
        self.disconnected_signal.connect(self._handle_disconnect)

    def _refresh_adb_devices(self):
        self.combo_adb_devices.clear()
        devices = self.adb.list_devices()
        if devices:
            for d in devices:
                self.combo_adb_devices.addItem(d["description"], d["serial"])
        else:
            self.combo_adb_devices.addItem(_t("device_not_found"), "")

    def _refresh_v4l2_devices(self):
        self.combo_v4l2_devs.clear()
        devs = V4L2Sink.list_video_devices()
        for d in devs:
            label = f"{d['name']}" + (" [Sanal Loopback]" if d["is_loopback"] else "")
            self.combo_v4l2_devs.addItem(label, d["path"])

        if self.combo_v4l2_devs.count() == 0:
            self.combo_v4l2_devs.addItem(_t("v4l2_will_create").format(dev="/dev/video10"), "/dev/video10")

    def _load_v4l2_module(self):
        ok, msg = V4L2Sink.load_loopback_module(10, "AselCam Video")
        if ok:
            QMessageBox.information(self, "Başarılı", f"Sanal kamera modülü yüklendi: {msg}")
            self._refresh_v4l2_devices()
            self._init_drivers()
        else:
            QMessageBox.warning(self, "Uyarı", f"Sanal kamera yüklenemedi:\n{msg}")

    def _set_connection_mode(self, mode: str):
        self._current_conn_mode = mode
        if mode == "usb":
            self.btn_mode_usb.setStyleSheet("background-color: #4d8eff; color: #00285d; border: none; border-radius: 6px; padding: 6px 14px; font-weight: 700; font-size: 12px;")
            self.btn_mode_wifi.setStyleSheet("background-color: transparent; color: #c2c6d6; border: none; border-radius: 6px; padding: 6px 14px; font-weight: 500; font-size: 12px;")
            self.widget_usb_fields.show()
            self.widget_wifi_fields.hide()
        else:
            self.btn_mode_usb.setStyleSheet("background-color: transparent; color: #c2c6d6; border: none; border-radius: 6px; padding: 6px 14px; font-weight: 500; font-size: 12px;")
            self.btn_mode_wifi.setStyleSheet("background-color: #4d8eff; color: #00285d; border: none; border-radius: 6px; padding: 6px 14px; font-weight: 700; font-size: 12px;")
            self.widget_usb_fields.hide()
            self.widget_wifi_fields.show()

    def _toggle_master_connect(self):
        if self.is_connected:
            self._disconnect()
            return
        if getattr(self, "_current_conn_mode", "usb") == "usb":
            self._toggle_connect_usb()
        else:
            self._toggle_connect_wifi()

    def _toggle_connect_usb(self):
        if self.is_connected:
            self._disconnect()
            return

        serial = self.combo_adb_devices.currentData()
        if not serial:
            self._refresh_adb_devices()
            serial = self.combo_adb_devices.currentData()
            if not serial:
                QMessageBox.warning(self, "Cihaz Yok", "USB ile bağlı bir Android cihaz bulunamadı.\nLütfen telefonunuzda 'USB Hata Ayıklama' (USB Debugging) modunu açın.")
                return

        # Forward ADB ports
        ok = self.adb.forward_ports(4747, 4748, serial)
        if not ok:
            QMessageBox.warning(self, "ADB Hatası", "ADB port yönlendirmesi başarısız oldu.")
            return

        self._start_connection("127.0.0.1", 4747, 4748)

    def _toggle_connect_wifi(self):
        if self.is_connected:
            self._disconnect()
            return

        raw_ip = self.txt_ip.text().strip()
        port_text = self.txt_port.text().strip()

        # Sanitize IP in case user pasted ip:port
        if ":" in raw_ip:
            parts = raw_ip.split(":")
            ip = parts[0].strip()
            if len(parts) > 1 and parts[1].strip().isdigit():
                port = int(parts[1].strip())
                self.txt_port.setText(str(port))
            else:
                port = int(port_text) if port_text.isdigit() else 4747
        else:
            ip = raw_ip
            port = int(port_text) if port_text.isdigit() else 4747

        if not ip:
            QMessageBox.warning(self, "Geçersiz IP", "Lütfen telefonunuzun IP adresini girin.")
            return

        self.config.set("wifi_ip", ip)
        self.config.set("video_port", port)

        self._start_connection(ip, port, port + 1)

    def _start_connection(self, host: str, video_port: int, control_port: int):
        self._user_disconnected = False
        self._reconnect_attempts = 0
        self._last_host = host
        self._last_video_port = video_port
        self._last_control_port = control_port
        self.status_bar.showMessage(f"{host}:{video_port} adresine bağlanılıyor...")

        # Parse requested resolution, fps, bitrate and codec
        res_str = self.combo_res.currentText().split()[0]
        w, h = [int(x) for x in res_str.split("x")]
        fps = int(self.combo_fps.currentText().split()[0])
        bitrate = self._parse_selected_bitrate()
        codec = "hevc" if "HEVC" in self.combo_codec.currentText() else "h264"

        # 1. Connect controller
        self.controller.host = host
        self.controller.port = control_port
        ctrl_ok = self.controller.connect(timeout=2.5)

        if ctrl_ok:
            # Query device info & synchronize stream configuration (including bitrate & aspect ratio)
            info = self.controller.get_device_info()
            if info:
                model = info.get("device_model", "Android")
                batt = info.get("battery_level", 0)
                self.lbl_device_info.setText(f"CİHAZ: {model}")
                self.lbl_battery.setText(f"PİL: {batt}%")
                self._update_camera_list(info.get("cameras", []), info.get("current_camera"))
                needs_config = (
                    not info.get("is_streaming", False)
                    or int(info.get("current_width", 0)) != w
                    or int(info.get("current_height", 0)) != h
                    or int(info.get("current_fps", 0)) != fps
                    or int(info.get("current_bitrate", 0)) != bitrate
                    or str(info.get("current_codec", "")).lower() != codec
                )
                if needs_config:
                    self.controller.set_config(w, h, fps, bitrate, codec)
                    time.sleep(0.15)
                    info = self.controller.get_device_info() or info
                if int(info.get("current_width", 0)) > 0 and int(info.get("current_height", 0)) > 0:
                    w = int(info.get("current_width", w))
                    h = int(info.get("current_height", h))
                if info.get("current_codec"):
                    codec = str(info.get("current_codec")).lower()
            else:
                self.controller.set_config(w, h, fps, bitrate, codec)
                time.sleep(0.15)

        # 2. Open v4l2loopback sink if available
        vdev = self.combo_v4l2_devs.currentData() or "/dev/video10"
        self.v4l2_sink.device_path = vdev
        try:
            self.v4l2_sink.open(w, h)
        except Exception as e:
            print(f"[MainWindow] v4l2loopback hatası: {e}")

        # 3. Start audio sink playback
        try:
            self.audio_sink.start_playback()
        except Exception as e:
            print(f"[MainWindow] Audio playback hatası: {e}")

        # 4. Start stream receiver
        if self.receiver:
            self.receiver.stop()
        self.receiver = StreamReceiver(
            host=host,
            port=video_port,
            audio_sink=self.audio_sink,
            v4l2_sink=self.v4l2_sink,
            filters=self.filters
        )
        self.receiver.is_preview_enabled = self.is_preview_enabled
        self.receiver.on_frame_ready = lambda frame: self.frame_received_signal.emit(frame)
        self.receiver.on_stats_updated = lambda fps_val, br: self.stats_updated_signal.emit(fps_val, br)
        self.receiver.on_disconnected = lambda: self.disconnected_signal.emit()

        recv_ok = self.receiver.start(w, h, codec=codec)

        if recv_ok or ctrl_ok:
            self.is_connected = True
            self.status_badge.setText(_t("status_live"))
            self.status_badge.setStyleSheet(
                "background: transparent; color: #34d399; border: none; padding: 2px 4px; font-weight: bold; font-size: 10px;"
            )
            self.btn_master_connect.setText(_t("conn_btn_stop"))
            self.btn_master_connect.setObjectName("btn_danger")
            self.btn_master_connect.style().unpolish(self.btn_master_connect)
            self.btn_master_connect.style().polish(self.btn_master_connect)
            if hasattr(self, "telemetry_conn"):
                self.telemetry_conn.setText("USB 3.0 (ADB)" if host == "127.0.0.1" else "Wi-Fi (5GHz)")
            if hasattr(self, "telemetry_encoder"):
                self.telemetry_encoder.setText(f"{codec.upper()} / FFmpeg")
            self.status_bar.showMessage(f"{host} - {_t('status_live')}")
            self._poll_telemetry()
        else:
            self._disconnect(user_initiated=True)
            QMessageBox.critical(
                self,
                "Bağlantı Başarısız",
                f"{host}:{video_port} adresine bağlanılamadı.\n\n"
                "Kontrol ediniz:\n"
                "1. Telefon ve bilgisayarın aynı Wi-Fi ağında olduğunu doğrulayın.\n"
                "2. Telefonda AselCam uygulamasının açık olduğunu doğrulayın.\n"
                "3. Telefonda 'YAYINI BAŞLAT' butonuna basılı olduğunu kontrol edin."
            )

    def _disconnect(self, user_initiated: bool = True):
        self._user_disconnected = user_initiated
        self.is_connected = False
        if self.receiver:
            self.receiver.stop()
            self.receiver = None

        self.controller.disconnect()
        self.audio_sink.stop_playback()
        # Keep V4L2 device open with standby signal so 3rd-party apps (OBS/Discord/Chrome) never lose camera!
        self.v4l2_sink.reset_to_standby()
        # Clear last video frame so PC preview immediately shows 'Bağlantı Yok' screen
        self.video_widget.clear_frame()

        self.status_badge.setText(_t("status_offline"))
        self.status_badge.setStyleSheet(
            "background: transparent; color: #f87171; border: none; padding: 2px 4px; font-weight: bold; font-size: 10px;"
        )
        self.btn_master_connect.setText(_t("conn_btn_start"))
        self.btn_master_connect.setObjectName("btn_primary")
        self.btn_master_connect.style().unpolish(self.btn_master_connect)
        self.btn_master_connect.style().polish(self.btn_master_connect)

        self._last_device_model = "—"
        self._last_battery_level = "—"
        self._last_ping = -1.0
        self.lbl_device_info.setText(f"{_t('label_device')} —")
        self.lbl_battery.setText(f"{_t('label_battery')} —%")
        self.lbl_ping.setText(f"{_t('label_ping')} — ms")
        if hasattr(self, "telemetry_device"):
            self.telemetry_device.setText(_t("status_standby"))
        self._remote_torch_on = False
        self._update_torch_ui()
        self.audio_vu.setValue(0)
        self.status_bar.showMessage(_t("footer_ready"))

    @pyqtSlot()
    def _handle_disconnect(self):
        if self._user_disconnected or not self.is_connected:
            self._disconnect(user_initiated=True)
            return

        # Automatic reconnection for transient Wi-Fi / USB glitches
        if self._reconnect_attempts < 3:
            self._reconnect_attempts += 1
            self.status_bar.showMessage(f"Akış kesintisi algılandı, yeniden bağlanılıyor ({self._reconnect_attempts}/3)...")
            QTimer.singleShot(500, self._try_auto_reconnect)
        else:
            self._disconnect(user_initiated=False)

    def _try_auto_reconnect(self):
        if self._user_disconnected:
            return
        if self._last_host == "127.0.0.1":
            serial = self.combo_adb_devices.currentData()
            if serial:
                self.adb.forward_ports(self._last_video_port, self._last_control_port, serial)

        res_str = self.combo_res.currentText().split()[0]
        w, h = [int(x) for x in res_str.split("x")]
        codec = "hevc" if "HEVC" in self.combo_codec.currentText() else "h264"

        if self.controller.ping() >= 0:
            info = self.controller.get_device_info()
            if info:
                if not info.get("is_streaming", False):
                    self.controller.start_stream()
                    time.sleep(0.2)
                if int(info.get("current_width", 0)) > 0 and int(info.get("current_height", 0)) > 0:
                    w = int(info.get("current_width", w))
                    h = int(info.get("current_height", h))
                if info.get("current_codec"):
                    codec = str(info.get("current_codec")).lower()

        if self.receiver:
            self.receiver.stop()
        self.receiver = StreamReceiver(
            host=self._last_host,
            port=self._last_video_port,
            audio_sink=self.audio_sink,
            v4l2_sink=self.v4l2_sink,
            filters=self.filters
        )
        self.receiver.is_preview_enabled = self.is_preview_enabled
        self.receiver.on_frame_ready = lambda frame: self.frame_received_signal.emit(frame)
        self.receiver.on_stats_updated = lambda fps_val, br: self.stats_updated_signal.emit(fps_val, br)
        self.receiver.on_disconnected = lambda: self.disconnected_signal.emit()

        if self.receiver.start(w, h, codec=codec):
            self._reconnect_attempts = 0
            self.status_bar.showMessage(f"{self._last_host} ile akış yeniden sağlandı.")
        else:
            self._handle_disconnect()

    @pyqtSlot(float, float)
    def _on_stats_updated(self, fps: float, bitrate_kbps: float):
        self._reconnect_attempts = 0
        self._last_fps = fps
        self._last_bitrate_kbps = bitrate_kbps
        self._update_status_bar_stats()

    @pyqtSlot(float)
    def _on_audio_level(self, level: float):
        self.audio_vu.setValue(int(level * 100))

    def _poll_telemetry(self):
        if not self.is_connected:
            return
        threading.Thread(target=self._async_poll_telemetry, daemon=True).start()

    def _async_poll_telemetry(self):
        try:
            ping = self.controller.ping()
            info = self.controller.get_device_info() or {}
            info["_ping"] = ping
            self.telemetry_updated_signal.emit(info)
        except Exception:
            pass

    @pyqtSlot(dict)
    def _on_telemetry_updated(self, info: dict):
        if not self.is_connected:
            return
        ping = info.get("_ping", -1.0)
        if ping >= 0:
            self._last_ping = ping
            self.lbl_ping.setText(f"{_t('label_ping')} {ping:.0f} ms")
        loss = info.get("packet_loss", 0.0)
        self._last_loss = float(loss)
        if self._last_fps > 0:
            self._update_status_bar_stats()

        model = info.get("device_model")
        if model:
            self._last_device_model = model
            self.lbl_device_info.setText(f"{_t('label_device')} {model}")
        batt = info.get("battery_level")
        if batt is not None:
            self._last_battery_level = batt
            self.lbl_battery.setText(f"{_t('label_battery')} {batt}%")
        self._update_camera_list(info.get("cameras", []), info.get("current_camera"))

        # Update dynamic zoom range from device (e.g. S25 Ultra 100x)
        max_zoom = float(info.get("max_zoom", 0.0))
        if max_zoom <= 1.0 and "cameras" in info:
            curr_id = str(info.get("current_camera", ""))
            for cam in info.get("cameras", []):
                if str(cam.get("id", "")) == curr_id:
                    max_zoom = float(cam.get("max_zoom", 1.0))
                    break
        if max_zoom > 1.0:
            max_val = int(max_zoom * 10)
            if self.slider_zoom.maximum() != max_val:
                self.slider_zoom.setMaximum(max_val)

        # Screen mirroring state synchronization
        is_mirror = bool(info.get("is_screen_mirroring", False))
        self.is_screen_mirror_active = is_mirror
        self.video_widget.set_screen_mirroring(is_mirror)
        if is_mirror:
            self.btn_screen_mirror.setText(_t("ctrl_back_to_cam_btn"))
            self.btn_screen_mirror.setStyleSheet(
                "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0284c7, stop:1 #0369a1); "
                "color: white; border-top: 1px solid #38bdf8; border-bottom: 1px solid #0c4a6e; border-radius: 9px; font-weight: 700;"
            )
        else:
            self.btn_screen_mirror.setText(_t("ctrl_screen_mirror_btn"))
            self.btn_screen_mirror.setStyleSheet("")

        # Flashlight state synchronization from phone telemetry
        if "torch_enabled" in info:
            phone_torch = bool(info.get("torch_enabled"))
            if phone_torch != getattr(self, "_remote_torch_on", False):
                self._remote_torch_on = phone_torch
                self._update_torch_ui()

        # If resolution or codec was changed on the phone UI, sync PC decoder & V4L2 automatically
        dev_w = int(info.get("current_width", 0))
        dev_h = int(info.get("current_height", 0))
        dev_codec = str(info.get("current_codec", "h264")).lower()
        if self.receiver and dev_w > 0 and dev_h > 0:
            if (dev_w != self.receiver.current_width
                or dev_h != self.receiver.current_height
                or dev_codec != self.receiver.current_codec):
                try:
                    self.v4l2_sink.open(dev_w, dev_h)
                except Exception:
                    pass
                self.receiver.reconfigure_decoder(dev_w, dev_h, codec=dev_codec)

    # Actions

    def _toggle_preview(self):
        self.is_preview_enabled = not self.is_preview_enabled
        self.config.set("preview_enabled", self.is_preview_enabled)
        self.video_widget.set_preview_enabled(self.is_preview_enabled)
        if self.receiver:
            self.receiver.set_preview_enabled(self.is_preview_enabled)

        if self.is_preview_enabled:
            self.btn_toggle_preview.setText(_t("preview_toggle_off"))
            self.status_bar.showMessage(_t("live_preview"))
        else:
            self.btn_toggle_preview.setText(_t("preview_toggle_on"))
            self.status_bar.showMessage(_t("perf_mode_title"))

    def _toggle_camera_pause(self):
        self.is_camera_paused = not self.is_camera_paused
        if self.receiver:
            self.receiver.set_camera_paused(self.is_camera_paused)

        # Physically tell phone to power off Camera2 sensor and MediaCodec encoder hardware
        if self.is_connected:
            threading.Thread(target=lambda: self.controller.set_camera_enabled(not self.is_camera_paused), daemon=True).start()

        if self.is_camera_paused:
            self.btn_pause_cam.setText(_t("blackout_toggle_off"))
            self.btn_pause_cam.setStyleSheet(
                "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #dc2626, stop:1 #b91c1c); "
                "color: white; border-top: 1px solid #f87171; border-bottom: 1px solid #5f1111; border-radius: 9px; font-weight: 700;"
            )
        else:
            self.btn_pause_cam.setText(_t("blackout_toggle_on"))
            self.btn_pause_cam.setStyleSheet("")

    def _toggle_mic_mute(self):
        self.is_mic_muted = not self.is_mic_muted
        self.audio_sink.set_muted(self.is_mic_muted)
        if self.is_connected:
            threading.Thread(target=lambda: self.controller.set_mute(self.is_mic_muted), daemon=True).start()

        if self.is_mic_muted:
            self.btn_mute_mic.setText(_t("mic_toggle_on"))
            self.btn_mute_mic.setStyleSheet(
                "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #dc2626, stop:1 #b91c1c); "
                "color: white; border-top: 1px solid #f87171; border-bottom: 1px solid #5f1111; border-radius: 9px; font-weight: 700;"
            )
            self.lbl_mic_status.setText(_t("mic_status_muted"))
            self.lbl_mic_status.setStyleSheet("color: #ff4757; background: transparent; margin-right: 15px;")
        else:
            self.btn_mute_mic.setText(_t("mic_toggle_off"))
            self.btn_mute_mic.setStyleSheet("")
            self.lbl_mic_status.setText(_t("mic_status_active"))
            self.lbl_mic_status.setStyleSheet("color: #00f5a0; background: transparent; margin-right: 15px;")

    def _on_mic_gain_changed(self, val: int):
        gain = val / 100.0
        self.lbl_mic_gain.setText(f"{val}%")
        self.audio_sink.set_gain(gain)
        self.config.set("audio_volume", gain)
        self._pending_mic_gain = gain
        self._mic_gain_timer.start()

    def _send_debounced_mic_gain(self):
        if self.is_connected:
            threading.Thread(target=lambda: self.controller.set_audio_gain(self._pending_mic_gain), daemon=True).start()

    # Remote Controls

    def _update_camera_list(self, cameras: list, current_cam_id: str = None):
        if not cameras:
            return
        self._loaded_cameras = cameras
        self.combo_remote_camera.blockSignals(True)
        self.combo_remote_camera.clear()
        selected_idx = 0
        target_id = str(current_cam_id) if current_cam_id is not None else str(self.config.get("selected_camera", "0"))

        for idx, cam in enumerate(cameras):
            cid = str(cam.get("id", idx))
            is_back = cam.get("is_back", True)
            facing = _t("back_cam") if is_back else _t("front_cam")
            label = f"{cid}: {facing} ({cid})"
            self.combo_remote_camera.addItem(label, cid)
            if cid == target_id:
                selected_idx = idx

        self.combo_remote_camera.setCurrentIndex(selected_idx)
        self.combo_remote_camera.blockSignals(False)

    def _on_remote_camera_selected(self, index: int):
        if not self.is_connected or index < 0:
            return
        cam_id = self.combo_remote_camera.itemData(index)
        if cam_id:
            self.config.set("selected_camera", str(cam_id))
            self.controller.switch_camera(str(cam_id))

    def _remote_switch_camera(self):
        count = self.combo_remote_camera.count()
        if count <= 1:
            curr = self.config.get("selected_camera", "0")
            nxt = "1" if curr == "0" else "0"
            self.config.set("selected_camera", nxt)
            self.controller.switch_camera(nxt)
            return

        nxt_idx = (self.combo_remote_camera.currentIndex() + 1) % count
        self.combo_remote_camera.setCurrentIndex(nxt_idx)

    def _remote_toggle_torch(self):
        if not self.is_connected:
            return
        target_state = not getattr(self, "_remote_torch_on", False)
        def _worker():
            ok = self.controller.set_torch(target_state)
            if ok:
                self._remote_torch_on = target_state
                QMetaObject.invokeMethod(self, "_update_torch_ui", Qt.ConnectionType.QueuedConnection)
            else:
                print(f"[MainWindow] Fener/Flaş komutu başarısız oldu (hedef: {target_state})")
        threading.Thread(target=_worker, daemon=True).start()

    @pyqtSlot()
    def _update_torch_ui(self):
        is_on = getattr(self, "_remote_torch_on", False)
        if hasattr(self, "btn_torch"):
            self.btn_torch.setText(_t("ctrl_torch_off") if is_on else _t("ctrl_torch_on"))
            if is_on:
                self.btn_torch.setStyleSheet(
                    "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #d97706, stop:1 #b45309); "
                    "color: #ffffff; border: 1px solid #f59e0b; border-radius: 6px; font-weight: 700;"
                )
            else:
                self.btn_torch.setStyleSheet("")

    def _remote_toggle_phone_preview(self):
        self._remote_phone_preview_on = not getattr(self, "_remote_phone_preview_on", True)
        if self.controller.set_preview_enabled(self._remote_phone_preview_on):
            self.btn_remote_preview.setText(_t("ctrl_phone_preview_on") if not self._remote_phone_preview_on else _t("ctrl_phone_preview_off"))

    def _remote_toggle_blackout(self):
        self._remote_blackout_on = not getattr(self, "_remote_blackout_on", False)
        if self.controller.set_blackout(self._remote_blackout_on):
            self.btn_remote_blackout.setText(_t("ctrl_wake_screen") if self._remote_blackout_on else _t("ctrl_blackout_on"))

    def _remote_toggle_screen_mirror(self):
        if not self.is_connected:
            return
        curr_is_mirror = getattr(self, "is_screen_mirror_active", False)
        new_state = not curr_is_mirror
        self.is_screen_mirror_active = new_state
        def task():
            self.controller.set_screen_mirror(new_state)
            time.sleep(0.4)
            self._poll_telemetry()
            time.sleep(1.0)
            self._poll_telemetry()
        threading.Thread(target=task, daemon=True).start()
        self.btn_screen_mirror.setText(_t("ctrl_back_to_cam_btn") if new_state else _t("ctrl_screen_mirror_btn"))

    def _remote_zoom_changed(self, val: int):
        zoom = val / 10.0
        self.lbl_zoom.setText(f"{zoom:.1f}x" if zoom < 10 else f"{zoom:.0f}x")
        self._pending_zoom = zoom
        self._zoom_timer.start()

    def _send_debounced_zoom(self):
        if self.is_connected:
            threading.Thread(target=lambda: self.controller.set_zoom(self._pending_zoom), daemon=True).start()

    def _on_quick_aspect_selected(self, index: int):
        if index < 0:
            return
        res_str = self.combo_quick_aspect.itemData(index)
        if not res_str:
            return
        self.combo_res.blockSignals(True)
        for i in range(self.combo_res.count()):
            if self.combo_res.itemText(i).startswith(res_str):
                self.combo_res.setCurrentIndex(i)
                break
        self.combo_res.blockSignals(False)
        self._apply_stream_settings()

    # Profiles & Filters

    def _apply_profile_by_key(self, key: str):
        idx = self.combo_color_profile.findData(key)
        if idx >= 0:
            self.combo_color_profile.setCurrentIndex(idx)
        else:
            self._apply_color_profile(key)

    def _on_color_profile_selected(self, index: int):
        if index < 0:
            return
        key = self.combo_color_profile.itemData(index)
        if key and key != "custom":
            self._apply_color_profile(key)

    def _apply_color_profile(self, key: str):
        prof = COLOR_PROFILES.get(key)
        if not prof:
            return
        self.slider_exposure.blockSignals(True)
        self.slider_highlights.blockSignals(True)
        self.slider_shadows.blockSignals(True)
        self.slider_whites.blockSignals(True)
        self.slider_blacks.blockSignals(True)
        self.slider_contrast.blockSignals(True)
        self.slider_bright.blockSignals(True)
        self.slider_temp.blockSignals(True)
        self.slider_tint.blockSignals(True)
        self.combo_tone_curve.blockSignals(True)
        self.slider_vibrance.blockSignals(True)
        self.slider_sat.blockSignals(True)
        self.slider_gain_r.blockSignals(True)
        self.slider_gain_g.blockSignals(True)
        self.slider_gain_b.blockSignals(True)
        self.slider_sharp.blockSignals(True)
        self.chk_gray.blockSignals(True)
        self.chk_invert.blockSignals(True)

        self.slider_exposure.setValue(int(round(float(prof.get("exposure", 0.0)) * 10)))
        self.slider_highlights.setValue(int(prof.get("highlights", 0)))
        self.slider_shadows.setValue(int(prof.get("shadows", 0)))
        self.slider_whites.setValue(int(prof.get("whites", 0)))
        self.slider_blacks.setValue(int(prof.get("blacks", 0)))
        self.slider_contrast.setValue(int(prof.get("contrast", 0)))
        self.slider_bright.setValue(int(prof.get("brightness", 0)))
        self.slider_temp.setValue(int(prof.get("temperature", 0)))
        self.slider_tint.setValue(int(prof.get("tint", 0)))
        curve_name = str(prof.get("tone_curve", "linear"))
        curve_i = self.combo_tone_curve.findData(curve_name)
        if curve_i >= 0:
            self.combo_tone_curve.setCurrentIndex(curve_i)
        self.slider_vibrance.setValue(int(prof.get("vibrance", 0)))
        self.slider_sat.setValue(int(prof.get("saturation", 100)))
        self.slider_gain_r.setValue(int(prof.get("red_gain", 0)))
        self.slider_gain_g.setValue(int(prof.get("green_gain", 0)))
        self.slider_gain_b.setValue(int(prof.get("blue_gain", 0)))
        self.slider_sharp.setValue(int(prof.get("sharpness", 0)))
        self.chk_gray.setChecked(bool(prof.get("grayscale", False)))
        self.chk_invert.setChecked(bool(prof.get("invert", False)))

        self.slider_exposure.blockSignals(False)
        self.slider_highlights.blockSignals(False)
        self.slider_shadows.blockSignals(False)
        self.slider_whites.blockSignals(False)
        self.slider_blacks.blockSignals(False)
        self.slider_contrast.blockSignals(False)
        self.slider_bright.blockSignals(False)
        self.slider_temp.blockSignals(False)
        self.slider_tint.blockSignals(False)
        self.combo_tone_curve.blockSignals(False)
        self.slider_vibrance.blockSignals(False)
        self.slider_sat.blockSignals(False)
        self.slider_gain_r.blockSignals(False)
        self.slider_gain_g.blockSignals(False)
        self.slider_gain_b.blockSignals(False)
        self.slider_sharp.blockSignals(False)
        self.chk_gray.blockSignals(False)
        self.chk_invert.blockSignals(False)

        self._update_filters()
        self.status_bar.showMessage(f"Renk profili uygulandı: {prof.get('name', key)}")

    def _choose_focus_background_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Özel Arkaplan Resmi Seç",
            os.path.expanduser("~"),
            "Resim Dosyaları (*.png *.jpg *.jpeg *.bmp *.webp);;Tüm Dosyalar (*)"
        )
        if file_path:
            self.lbl_bg_img_path.setText(os.path.basename(file_path))
            self.lbl_bg_img_path.setToolTip(file_path)
            self.filters.set_custom_background(file_path)
            idx = self.combo_focus_mode.findData("custom")
            if idx >= 0:
                self.combo_focus_mode.setCurrentIndex(idx)
            self._update_filters()
            self.status_bar.showMessage(f"Özel arkaplan resmi seçildi: {os.path.basename(file_path)}")

    def _update_filters(self):
        rot_map = {0: 0, 1: 90, 2: 180, 3: 270}
        rot = rot_map.get(self.combo_rot.currentIndex(), 0)

        exp_ev = self.slider_exposure.value() / 10.0
        highlights = self.slider_highlights.value()
        shadows = self.slider_shadows.value()
        whites = self.slider_whites.value()
        blacks = self.slider_blacks.value()
        contrast = self.slider_contrast.value()
        brightness = self.slider_bright.value()
        temperature = self.slider_temp.value()
        tint = self.slider_tint.value()
        tone_curve = self.combo_tone_curve.currentData() or "linear"
        saturation = self.slider_sat.value()
        vibrance = self.slider_vibrance.value()
        sharpness = self.slider_sharp.value()
        flip_h = self.chk_flip_h.isChecked()
        flip_v = self.chk_flip_v.isChecked()
        grayscale = self.chk_gray.isChecked()
        invert = self.chk_invert.isChecked()

        red_gain = self.slider_gain_r.value()
        green_gain = self.slider_gain_g.value()
        blue_gain = self.slider_gain_b.value()

        focus_enabled = self.chk_focus_enabled.isChecked()
        focus_mode = self.combo_focus_mode.currentData() or "blur"
        focus_radius = self.slider_focus_radius.value()
        focus_blur = self.slider_focus_blur.value()
        color_profile = self.combo_color_profile.currentData() or "custom"

        # Update numerical labels
        self.lbl_exposure.setText(f"{exp_ev:+.1f} EV")
        self.lbl_highlights.setText(f"{highlights:+d}")
        self.lbl_shadows.setText(f"{shadows:+d}")
        self.lbl_whites.setText(f"{whites:+d}")
        self.lbl_blacks.setText(f"{blacks:+d}")
        self.lbl_contrast.setText(f"{contrast:+d}")
        self.lbl_bright.setText(f"{brightness:+d}")
        self.lbl_temp.setText(_t("val_natural") if temperature == 0 else f"{temperature:+d}")
        self.lbl_tint.setText(_t("val_natural") if tint == 0 else f"{tint:+d}")
        self.lbl_vibrance.setText(f"{vibrance:+d}")
        self.lbl_sat.setText(f"{saturation}%")
        self.lbl_sharp.setText(_t("val_off") if sharpness == 0 else f"{sharpness}%")

        self.lbl_gain_r.setText(f"{red_gain:+d}")
        self.lbl_gain_g.setText(f"{green_gain:+d}")
        self.lbl_gain_b.setText(f"{blue_gain:+d}")
        self.lbl_focus_radius.setText(f"{focus_radius}%")
        self.lbl_focus_blur.setText(str(focus_blur))

        self.filters.update_params(
            exposure=exp_ev,
            highlights=highlights,
            shadows=shadows,
            whites=whites,
            blacks=blacks,
            contrast=contrast,
            brightness=brightness,
            temperature=temperature,
            tint=tint,
            tone_curve=tone_curve,
            saturation=saturation,
            vibrance=vibrance,
            red_gain=red_gain,
            green_gain=green_gain,
            blue_gain=blue_gain,
            focus_enabled=focus_enabled,
            focus_mode=focus_mode,
            focus_radius=focus_radius,
            focus_blur=focus_blur,
            sharpness=sharpness,
            flip_h=flip_h,
            flip_v=flip_v,
            rotation=rot,
            grayscale=grayscale,
            invert=invert
        )

        filter_dict = {
            "exposure": exp_ev,
            "highlights": highlights,
            "shadows": shadows,
            "whites": whites,
            "blacks": blacks,
            "contrast": contrast,
            "brightness": brightness,
            "temperature": temperature,
            "tint": tint,
            "tone_curve": tone_curve,
            "saturation": saturation,
            "vibrance": vibrance,
            "red_gain": red_gain,
            "green_gain": green_gain,
            "blue_gain": blue_gain,
            "color_profile": color_profile,
            "focus_enabled": focus_enabled,
            "focus_mode": focus_mode,
            "focus_radius": focus_radius,
            "focus_blur": focus_blur,
            "focus_image_path": self.filters.focus_image_path,
            "sharpness": sharpness,
            "flip_h": flip_h,
            "flip_v": flip_v,
            "rotation": rot,
            "grayscale": grayscale,
            "invert": invert
        }
        self.config.set_filters(filter_dict, save=False)
        self._filter_save_timer.start(500)

    def _save_filters_to_disk(self):
        try:
            self.config.save()
        except Exception:
            pass

    def _reset_filters(self):
        self.slider_exposure.setValue(0)
        self.slider_highlights.setValue(0)
        self.slider_shadows.setValue(0)
        self.slider_whites.setValue(0)
        self.slider_blacks.setValue(0)
        self.slider_contrast.setValue(0)
        self.slider_bright.setValue(0)
        self.slider_temp.setValue(0)
        self.slider_tint.setValue(0)
        self.slider_vibrance.setValue(0)
        self.slider_sat.setValue(100)
        self.slider_sharp.setValue(0)
        self.slider_gain_r.setValue(0)
        self.slider_gain_g.setValue(0)
        self.slider_gain_b.setValue(0)
        self.chk_focus_enabled.setChecked(False)
        self.combo_focus_mode.setCurrentIndex(0)
        self.slider_focus_radius.setValue(45)
        self.slider_focus_blur.setValue(15)
        self.chk_flip_h.setChecked(False)
        self.chk_flip_v.setChecked(False)
        self.chk_gray.setChecked(False)
        self.chk_invert.setChecked(False)
        self.combo_rot.setCurrentIndex(0)
        curve_idx = self.combo_tone_curve.findData("linear")
        if curve_idx >= 0:
            self.combo_tone_curve.setCurrentIndex(curve_idx)
        prof_idx = self.combo_color_profile.findData("standard")
        if prof_idx >= 0:
            self.combo_color_profile.blockSignals(True)
            self.combo_color_profile.setCurrentIndex(prof_idx)
            self.combo_color_profile.blockSignals(False)
        self._update_filters()
        self.config.save()
        self.status_bar.showMessage("Tüm RAW ve filtre ayarları sıfırlandı.")

    # Apply Quality Settings

    def _apply_stream_settings(self):
        res_str = self.combo_res.currentText().split()[0]
        w, h = [int(x) for x in res_str.split("x")]
        fps_str = self.combo_fps.currentText().split()[0]
        fps = int(fps_str)

        bitrate = self._parse_selected_bitrate()
        codec = "hevc" if "HEVC" in self.combo_codec.currentText() else "h264"

        self.combo_quick_aspect.blockSignals(True)
        for i in range(self.combo_quick_aspect.count()):
            if self.combo_quick_aspect.itemData(i) == res_str:
                self.combo_quick_aspect.setCurrentIndex(i)
                break
        self.combo_quick_aspect.blockSignals(False)

        self.config.set("resolution", res_str)
        self.config.set("fps", fps)
        self.config.set("bitrate", bitrate)
        self.config.set("codec", codec)

        # Update v4l2 device
        vdev = self.combo_v4l2_devs.currentData() or "/dev/video10"
        self.config.set("v4l2_device", vdev)
        self.v4l2_sink.device_path = vdev
        try:
            self.v4l2_sink.open(w, h)
        except Exception as e:
            print(f"[MainWindow] v4l2 açma hatası: {e}")

        if self.is_connected:
            ok = self.controller.set_config(w, h, fps, bitrate, codec)
            if ok:
                info = self.controller.get_device_info()
                if info:
                    if int(info.get("current_width", 0)) > 0 and int(info.get("current_height", 0)) > 0:
                        w = int(info.get("current_width", w))
                        h = int(info.get("current_height", h))
                    if info.get("current_codec"):
                        codec = str(info.get("current_codec", codec)).lower()
                try:
                    self.v4l2_sink.open(w, h)
                except Exception:
                    pass
                self.status_bar.showMessage(f"Yeni ayarlar uygulandı: {w}x{h} @ {fps}fps, {bitrate // 1000000} Mbps ({codec.upper()})")
                # Safely reconfigure receiver decoder without reconnecting socket
                if self.receiver:
                    self.receiver.reconfigure_decoder(w, h, codec=codec)
            else:
                QMessageBox.warning(self, "Uyarı", "Ayarlar cihaza iletilemedi.")
        else:
            self.status_bar.showMessage(f"Ayarlar kaydedildi: {w}x{h} @ {fps}fps, {bitrate // 1000000} Mbps.")

    def closeEvent(self, event):
        is_test = "unittest" in sys.argv[0] or "pytest" in sys.argv[0] or any("test" in arg for arg in sys.argv)
        if not is_test and not getattr(self, "_force_quit", False) and hasattr(self, "tray_icon") and self.tray_icon.isVisible():
            event.ignore()
            self.hide()
            try:
                self.tray_icon.showMessage(
                    "AselCam",
                    _t("tray_bg_notice"),
                    QSystemTrayIcon.MessageIcon.Information,
                    2000
                )
            except Exception:
                pass
        else:
            self._disconnect(user_initiated=True)
            self.v4l2_sink.close()
            self.audio_sink.teardown_virtual_mic()
            if hasattr(self, "tray_icon"):
                self.tray_icon.hide()
            event.accept()
