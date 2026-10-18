import os
from typing import Optional
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QImage, QColor, QFont, QPen, QBrush, QPixmap
from PyQt6.QtCore import Qt, QRectF
import numpy as np
from ..core.i18n import _t


class VideoWidget(QWidget):
    """
    High-Performance Video Viewfinder & Telemetry HUD.
    Synchronized with Google Stitch 'Obsidian Stream Studio' Design System.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._image: Optional[QImage] = None
        self._fps_text = "0.0 FPS"
        self._res_text = "-x-"
        self._bitrate_text = "- kbps"
        self._preview_enabled = True
        self._screen_mirroring = False
        self._horz_logo: Optional[QPixmap] = None

        logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "aselcam_logo-horz-white.svg")
        if not os.path.exists(logo_path):
            logo_path = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "aselcam_logo-horz-white.svg")
        if not os.path.exists(logo_path):
            logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "aselcam_logo_horz_128.png")
        if os.path.exists(logo_path):
            self._horz_logo = QPixmap(logo_path)

        self.setMinimumSize(480, 270)
        self.setStyleSheet("background-color: #080c14; border-radius: 12px;")

    def set_screen_mirroring(self, enabled: bool):
        if self._screen_mirroring != enabled:
            self._screen_mirroring = enabled
            self.update()

    def set_preview_enabled(self, enabled: bool):
        self._preview_enabled = enabled
        self.update()

    def clear_frame(self):
        self._image = None
        self._fps_text = "0.0 FPS"
        self._bitrate_text = "- kbps"
        self.update()

    def update_frame(self, frame_rgb: np.ndarray):
        if not self._preview_enabled:
            return

        try:
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w

            # Zero-copy QImage wrap
            q_img = QImage(
                frame_rgb.data,
                w,
                h,
                bytes_per_line,
                QImage.Format.Format_RGB888
            )

            # Deep copy to detach from buffer
            self._image = q_img.copy()
            self._res_text = f"{w}x{h}"
            self.update()
        except Exception as e:
            print(f"[VideoWidget] update_frame error: {e}")

    def update_stats(self, fps: float, bitrate_kbps: float):
        self._fps_text = f"{fps:.1f} FPS"
        if bitrate_kbps >= 1000:
            self._bitrate_text = f"{bitrate_kbps / 1000.0:.1f} Mbps"
        else:
            self._bitrate_text = f"{bitrate_kbps:.0f} kbps"
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

            w = self.width()
            h = self.height()

            # Obsidian Viewfinder Canvas (#080C14)
            painter.fillRect(0, 0, w, h, QColor("#080c14"))

            # Outer subtle border (rgba(255, 255, 255, 0.08))
            painter.setPen(QPen(QColor(255, 255, 255, 20), 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(QRectF(1.0, 1.0, float(w - 2), float(h - 2)), 12.0, 12.0)

            if not self._preview_enabled:
                # Performance Mode Standby Card
                card_rect = QRectF(24.0, 24.0, float(w - 48), float(h - 48))
                painter.setPen(QPen(QColor(255, 255, 255, 20), 1))
                painter.setBrush(QBrush(QColor("#0f172a")))
                painter.drawRoundedRect(card_rect, 12.0, 12.0)

                # Draw Horizontal White Logo
                if self._horz_logo and not self._horz_logo.isNull():
                    scaled_logo = self._horz_logo.scaled(
                        220, 52,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    lw = scaled_logo.width()
                    lh = scaled_logo.height()
                    lx = (w - lw) / 2.0
                    ly = float(h // 2 - 92)
                    painter.drawPixmap(int(lx), int(ly), scaled_logo)

                painter.setPen(QColor("#38bdf8"))
                font = QFont("Space Grotesk", 15, QFont.Weight.Bold)
                painter.setFont(font)
                painter.drawText(QRectF(0, h // 2 - 28, w, 28), Qt.AlignmentFlag.AlignCenter, _t("perf_mode_title"))

                painter.setPen(QColor("#94a3b8"))
                font.setPointSize(10)
                font.setBold(False)
                painter.setFont(font)
                painter.drawText(
                    QRectF(0, h // 2 + 6, w, 45),
                    Qt.AlignmentFlag.AlignCenter,
                    _t("perf_mode_sub")
                )

                # Status pill badge
                pill_w, pill_h = 260.0, 28.0
                pill_rect = QRectF((w - pill_w) / 2.0, float(h // 2 + 58), pill_w, pill_h)
                painter.setPen(QPen(QColor(16, 185, 129, 90), 1))
                painter.setBrush(QColor(16, 185, 129, 30))
                painter.drawRoundedRect(pill_rect, 14.0, 14.0)

                painter.setPen(QColor("#34d399"))
                painter.setFont(QFont("Plus Jakarta Sans", 9, QFont.Weight.Bold))
                painter.drawText(pill_rect, Qt.AlignmentFlag.AlignCenter, _t("background_streaming"))
                return

            if self._image is not None and not self._image.isNull():
                img_w = self._image.width()
                img_h = self._image.height()

                # Maintain aspect ratio
                scale = min(w / img_w, h / img_h)
                target_w = img_w * scale
                target_h = img_h * scale
                target_x = (w - target_w) / 2.0
                target_y = (h - target_h) / 2.0

                target_rect = QRectF(target_x, target_y, target_w, target_h)
                painter.drawImage(target_rect, self._image)

                # Top-Left Telemetry HUD Pill (Stream Resolution, FPS & Bitrate)
                hud_text = f"{self._res_text} @ {self._fps_text} │ {self._bitrate_text}"
                hud_w = 260.0
                hud_left_rect = QRectF(target_x + 14.0, target_y + 14.0, hud_w, 32.0)
                painter.setPen(QPen(QColor(59, 130, 246, 70), 1))
                painter.setBrush(QColor(15, 23, 42, 220))
                painter.drawRoundedRect(hud_left_rect, 8.0, 8.0)

                # Neon Mint Recording Dot
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor("#10b981"))
                painter.drawEllipse(QRectF(target_x + 24.0, target_y + 25.0, 8.0, 8.0))

                # HUD Text
                painter.setPen(QColor("#f8fafc"))
                painter.setFont(QFont("JetBrains Mono", 10, QFont.Weight.DemiBold))
                painter.drawText(
                    QRectF(target_x + 38.0, target_y + 14.0, hud_w - 42.0, 32.0),
                    Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                    hud_text
                )

                # Live Badge (CANLI ÖNİZLEME)
                badge_w = 120.0
                hud_badge_rect = QRectF(target_x + hud_w + 22.0, target_y + 14.0, badge_w, 32.0)
                painter.setPen(QPen(QColor(56, 189, 248, 80), 1))
                painter.setBrush(QColor(15, 23, 42, 220))
                painter.drawRoundedRect(hud_badge_rect, 8.0, 8.0)

                painter.setPen(QColor("#38bdf8"))
                painter.setFont(QFont("Plus Jakarta Sans", 9, QFont.Weight.Bold))
                painter.drawText(
                    hud_badge_rect,
                    Qt.AlignmentFlag.AlignCenter,
                    _t("live_preview")
                )
            else:
                # Standby / Stream Waiting Card (#0F172A)
                card_rect = QRectF(24.0, 24.0, float(w - 48), float(h - 48))
                painter.setPen(QPen(QColor(255, 255, 255, 20), 1))
                painter.setBrush(QBrush(QColor("#0f172a")))
                painter.drawRoundedRect(card_rect, 12.0, 12.0)

                # Draw Horizontal Logo instead of generic character
                is_mirror = self._screen_mirroring
                if not is_mirror and self._horz_logo and not self._horz_logo.isNull():
                    scaled_logo = self._horz_logo.scaled(
                        220, 52,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    lw = scaled_logo.width()
                    lh = scaled_logo.height()
                    lx = (w - lw) / 2.0
                    ly = float(h // 2 - 92)
                    painter.drawPixmap(int(lx), int(ly), scaled_logo)
                else:
                    icon_box_w, icon_box_h = 56.0, 56.0
                    icon_box_rect = QRectF((w - icon_box_w) / 2.0, float(h // 2 - 96), icon_box_w, icon_box_h)
                    painter.setPen(QPen(QColor(255, 255, 255, 25), 1))
                    painter.setBrush(QBrush(QColor("#1e293b")))
                    painter.drawRoundedRect(icon_box_rect, 12.0, 12.0)

                    painter.setPen(QColor("#38bdf8" if is_mirror else "#4d8eff"))
                    painter.setFont(QFont("Space Grotesk", 22, QFont.Weight.Bold))
                    painter.drawText(
                        icon_box_rect,
                        Qt.AlignmentFlag.AlignCenter,
                        "📺" if is_mirror else "◈"
                    )

                painter.setPen(QColor("#dfe2f1"))
                title_font = QFont("Space Grotesk", 15, QFont.Weight.Bold)
                painter.setFont(title_font)
                painter.drawText(
                    QRectF(0, h // 2 - 28, w, 28),
                    Qt.AlignmentFlag.AlignCenter,
                    _t("waiting_screen") if is_mirror else _t("waiting_stream")
                )

                painter.setPen(QColor("#94a3b8"))
                sub_font = QFont("Plus Jakarta Sans", 11, QFont.Weight.Normal)
                painter.setFont(sub_font)
                painter.drawText(
                    QRectF(0, h // 2 + 6, w, 28),
                    Qt.AlignmentFlag.AlignCenter,
                    _t("screen_permission_hint") if is_mirror else _t("waiting_subtext")
                )

                # Savings Mode Pill Tag (Emerald)
                pill_w, pill_h = 290.0, 28.0
                pill_rect = QRectF((w - pill_w) / 2.0, float(h // 2 + 46), pill_w, pill_h)
                painter.setPen(QPen(QColor(16, 185, 129, 90), 1))
                painter.setBrush(QColor(16, 185, 129, 25))
                painter.drawRoundedRect(pill_rect, 14.0, 14.0)

                painter.setPen(QColor("#34d399"))
                painter.setFont(QFont("Plus Jakarta Sans", 9, QFont.Weight.Bold))
                painter.drawText(pill_rect, Qt.AlignmentFlag.AlignCenter, _t("power_saving_mode"))
        except Exception as e:
            print(f"[VideoWidget] paintEvent error: {e}")
        finally:
            painter.end()
