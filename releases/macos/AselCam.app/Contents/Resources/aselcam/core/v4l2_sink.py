import os
import sys
import struct
import subprocess
import glob
import threading
import time
import numpy as np
from typing import List, Dict, Optional, Tuple

try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    fcntl = None
    HAS_FCNTL = False

try:
    import pyvirtualcam
    HAS_PYVIRTUALCAM = True
except ImportError:
    pyvirtualcam = None
    HAS_PYVIRTUALCAM = False

# V4L2 ioctl definitions (Linux)
VIDIOC_QUERYCAP = 0x80685600
VIDIOC_S_FMT = 0xC0D05605

V4L2_BUF_TYPE_VIDEO_OUTPUT = 2
V4L2_PIX_FMT_YUYV = 0x56595559  # 'YUYV'
V4L2_PIX_FMT_BGR24 = 0x33524742 # 'BGR3'
V4L2_FIELD_NONE = 1

class V4L2Sink:
    """
    Cross-platform virtual camera sink.
    - On Linux: Uses native high-speed V4L2 kernel loopback (/dev/video10) via direct ioctl.
    - On Windows/macOS: Integrates with DirectShow / OBS Virtual Camera / CoreMedia via pyvirtualcam
      or graceful software pass-through.
    """
    def __init__(self, device_path: str = "/dev/video10"):
        self.device_path = device_path
        self._fd: Optional[int] = None
        self._pyvirtualcam_cam = None
        self.width = 1920
        self.height = 1080
        self.format_fourcc = V4L2_PIX_FMT_YUYV
        self.is_open = False

        self._feeder_running = False
        self._feeder_thread: Optional[threading.Thread] = None
        self._frame_event = threading.Event()
        self._pending_rgb: Optional[np.ndarray] = None
        self._last_yuyv_bytes: Optional[bytes] = None
        self._last_rgb_array: Optional[np.ndarray] = None
        self._standby_yuyv_bytes: Optional[bytes] = None

    @staticmethod
    def list_video_devices() -> List[Dict[str, str]]:
        if sys.platform.startswith("linux") and HAS_FCNTL:
            devices = []
            for dev in sorted(glob.glob("/dev/video*")):
                try:
                    fd = os.open(dev, os.O_RDWR | os.O_NONBLOCK)
                    # struct v4l2_capability { driver[16], card[32], bus_info[32], version, capabilities, device_caps, reserved[3] }
                    cap = struct.pack("16s32s32sIIII", b"", b"", b"", 0, 0, 0, 0)
                    res = fcntl.ioctl(fd, VIDIOC_QUERYCAP, cap)
                    driver, card, bus, ver, caps, dev_caps, _ = struct.unpack("16s32s32sIIII", res)
                    os.close(fd)

                    driver_str = driver.split(b"\x00")[0].decode("utf-8", "ignore")
                    card_str = card.split(b"\x00")[0].decode("utf-8", "ignore")
                    is_loopback = "v4l2 loopback" in driver_str.lower() or "loopback" in card_str.lower()

                    devices.append({
                        "path": dev,
                        "name": f"{card_str} ({dev})",
                        "driver": driver_str,
                        "is_loopback": is_loopback
                    })
                except Exception:
                    devices.append({
                        "path": dev,
                        "name": f"Video Device ({dev})",
                        "driver": "unknown",
                        "is_loopback": False
                    })
            return devices
        else:
            # Windows / macOS virtual camera discovery
            return [{
                "path": "virtualcam",
                "name": "Virtual Camera (DirectShow / OBS / CoreMedia)",
                "driver": "pyvirtualcam" if HAS_PYVIRTUALCAM else "software_loopback",
                "is_loopback": True
            }]

    @staticmethod
    def load_loopback_module(video_nr: int = 10, label: str = "AselCam Video") -> Tuple[bool, str]:
        if not sys.platform.startswith("linux"):
            return True, "Virtual camera module handled by OS virtual driver."

        cmd = [
            "pkexec", "sh", "-c",
            f"modprobe -r v4l2loopback 2>/dev/null || true; "
            f"modprobe v4l2loopback devices=1 video_nr={video_nr} card_label='{label}' exclusive_caps=0; "
            f"v4l2-ctl -d /dev/video{video_nr} -c keep_format=1,sustain_framerate=1 2>/dev/null || true; "
            f"echo 'options v4l2loopback devices=1 video_nr={video_nr} card_label=\"{label}\" exclusive_caps=0' > /etc/modprobe.d/aselcam-v4l2loopback.conf 2>/dev/null || true"
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if res.returncode == 0:
                return True, f"/dev/video{video_nr} başarıyla yüklendi"
            return False, res.stderr or "İşlem iptal edildi veya yetki verilmedi"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def _create_standby_yuyv(width: int, height: int) -> bytes:
        # Dark frame in YUYV (Y=20, U=128, V=128)
        yuyv = np.empty((height, width // 2, 4), dtype=np.uint8)
        yuyv[:, :, 0] = 20
        yuyv[:, :, 1] = 128
        yuyv[:, :, 2] = 20
        yuyv[:, :, 3] = 128
        return yuyv.tobytes()

    @staticmethod
    def rgb_to_yuyv_bytes(rgb_array: np.ndarray, target_w: int, target_h: int) -> bytes:
        h, w = rgb_array.shape[:2]
        if (w, h) != (target_w, target_h):
            scale = min(target_w / max(1, w), target_h / max(1, h))
            new_w = max(2, (int(round(w * scale)) // 2) * 2)
            new_h = max(2, int(round(h * scale)))

            y_idx = np.linspace(0, h - 1, new_h).astype(np.int32)
            x_idx = np.linspace(0, w - 1, new_w).astype(np.int32)
            scaled = rgb_array[np.ix_(y_idx, x_idx)]

            if (new_w, new_h) == (target_w, target_h):
                rgb_array = scaled
            else:
                canvas = np.full((target_h, target_w, 3), 16, dtype=np.uint8)
                off_y = (target_h - new_h) // 2
                off_x = (target_w - new_w) // 2
                canvas[off_y:off_y + new_h, off_x:off_x + new_w] = scaled
                rgb_array = canvas
            h, w = target_h, target_w

        r = rgb_array[:, :, 0].astype(np.int16)
        g = rgb_array[:, :, 1].astype(np.int16)
        b = rgb_array[:, :, 2].astype(np.int16)

        # Standard ITU-R BT.601 RGB to YUV
        y = (((66 * r + 129 * g + 25 * b + 128) >> 8) + 16).astype(np.uint8)

        # Chroma subsampling: horizontal 2:1
        r_sub = r[:, 0::2]
        g_sub = g[:, 0::2]
        b_sub = b[:, 0::2]
        u0 = (((-38 * r_sub - 74 * g_sub + 112 * b_sub + 128) >> 8) + 128).astype(np.uint8)
        v0 = (((112 * r_sub - 94 * g_sub - 18 * b_sub + 128) >> 8) + 128).astype(np.uint8)

        yuyv = np.empty((h, w // 2, 4), dtype=np.uint8)
        yuyv[:, :, 0] = y[:, 0::2]
        yuyv[:, :, 1] = u0
        yuyv[:, :, 2] = y[:, 1::2]
        yuyv[:, :, 3] = v0
        return yuyv.tobytes()

    def open(self, width: int = 1920, height: int = 1080) -> bool:
        if self.is_open and (self._fd is not None or self._pyvirtualcam_cam is not None) and self.width == width and self.height == height:
            return True

        self.close()
        self.width = width
        self.height = height

        # 1. Non-Linux platforms or pyvirtualcam fallback
        if not sys.platform.startswith("linux") or not HAS_FCNTL:
            if HAS_PYVIRTUALCAM and pyvirtualcam:
                try:
                    self._pyvirtualcam_cam = pyvirtualcam.Camera(
                        width=width,
                        height=height,
                        fps=30,
                        fmt=pyvirtualcam.PixelFormat.RGB
                    )
                    self.is_open = True
                    self._feeder_running = True
                    self._feeder_thread = threading.Thread(
                        target=self._feeder_loop,
                        name="AselCam-VirtualCamFeeder",
                        daemon=True
                    )
                    self._feeder_thread.start()
                    print(f"[VirtualCam] pyvirtualcam started ({width}x{height} RGB, 30 FPS)")
                    return True
                except Exception as e:
                    print(f"[VirtualCam] pyvirtualcam init notice: {e}. Running in software standby mode.")
            # Software standby mode (safe pass-through)
            self.is_open = True
            return True

        # 2. Linux native V4L2 device
        if not os.path.exists(self.device_path):
            print(f"[V4L2Sink] Aygıt bulunamadı: {self.device_path}")
            return False

        # Unlock keep_format temporarily so VIDIOC_S_FMT can change dimensions
        try:
            subprocess.run(
                ["v4l2-ctl", "-d", self.device_path, "-c", "keep_format=0"],
                capture_output=True,
                timeout=2
            )
        except Exception:
            pass

        try:
            self._fd = os.open(self.device_path, os.O_RDWR | os.O_NONBLOCK)

            sizeimage = width * height * 2 # For YUYV 16bpp
            bytesperline = width * 2

            fmt = struct.pack(
                "I 4x 9I 164s",
                V4L2_BUF_TYPE_VIDEO_OUTPUT, # type
                width,                      # width
                height,                     # height
                self.format_fourcc,         # pixelformat (YUYV)
                V4L2_FIELD_NONE,            # field
                bytesperline,               # bytesperline
                sizeimage,                  # sizeimage
                1,                          # colorspace (SRGB)
                0,                          # priv
                0,                          # flags
                b"\x00" * 164               # padding to 208 bytes
            )

            res_fmt = fcntl.ioctl(self._fd, VIDIOC_S_FMT, fmt)
            try:
                unpacked = struct.unpack("I 4x 9I 164s", res_fmt)
                actual_w, actual_h = int(unpacked[1]), int(unpacked[2])
                if actual_w > 0 and actual_h > 0:
                    self.width = actual_w
                    self.height = actual_h
            except Exception:
                pass

            try:
                subprocess.run(
                    ["v4l2-ctl", "-d", self.device_path, "-c", "keep_format=1,sustain_framerate=1"],
                    capture_output=True,
                    timeout=2
                )
            except Exception:
                pass

            self._standby_yuyv_bytes = self._create_standby_yuyv(self.width, self.height)
            self._last_yuyv_bytes = self._standby_yuyv_bytes
            self.is_open = True

            # Write initial frame immediately so V4L2 consumers see ready signal
            try:
                os.write(self._fd, self._standby_yuyv_bytes)
            except Exception:
                pass

            self._feeder_running = True
            self._feeder_thread = threading.Thread(
                target=self._feeder_loop,
                name="AselCam-V4L2Feeder",
                daemon=True
            )
            self._feeder_thread.start()

            print(f"[V4L2Sink] {self.device_path} açıldı ({self.width}x{self.height} YUYV, sürekli besleme aktif)")
            return True
        except Exception as e:
            print(f"[V4L2Sink] Hata {self.device_path} açılamadı: {e}")
            self.close()
            return False

    def _feeder_loop(self):
        while self._feeder_running and self.is_open:
            self._frame_event.wait(timeout=0.033)
            self._frame_event.clear()

            if not self._feeder_running or not self.is_open:
                break

            rgb = self._pending_rgb
            if rgb is not None:
                self._pending_rgb = None
                self._last_rgb_array = rgb
                if self._fd is not None:
                    try:
                        self._last_yuyv_bytes = self.rgb_to_yuyv_bytes(rgb, self.width, self.height)
                    except Exception:
                        pass

            # Output to pyvirtualcam if available
            if self._pyvirtualcam_cam is not None and self._last_rgb_array is not None:
                try:
                    self._pyvirtualcam_cam.send(self._last_rgb_array)
                except Exception:
                    pass

            # Output to native Linux V4L2 device
            frame_bytes = self._last_yuyv_bytes
            if frame_bytes and self._fd is not None:
                try:
                    os.write(self._fd, frame_bytes)
                except (BlockingIOError, OSError):
                    pass
                except Exception:
                    pass

    def reset_to_standby(self):
        """Switches output back to standby frame without closing the V4L2 device."""
        self._pending_rgb = None
        if self._standby_yuyv_bytes is not None:
            self._last_yuyv_bytes = self._standby_yuyv_bytes
            self._frame_event.set()

    def write_yuyv_frame(self, yuyv_bytes: bytes):
        if not self.is_open:
            return
        self._last_yuyv_bytes = yuyv_bytes
        self._frame_event.set()

    def write_rgb_frame(self, rgb_array: np.ndarray):
        """Queues RGB image for asynchronous conversion and output on the background feeder thread."""
        if not self.is_open:
            return
        self._pending_rgb = rgb_array
        self._frame_event.set()

    def write_bgr_frame(self, bgr_array: np.ndarray):
        """Queues BGR image from OpenCV / NumPy for virtual cam output."""
        if not self.is_open:
            return
        self.write_rgb_frame(bgr_array[:, :, ::-1])

    def close(self):
        self._feeder_running = False
        self.is_open = False
        self._pending_rgb = None
        self._last_rgb_array = None
        self._frame_event.set()

        if self._feeder_thread and self._feeder_thread.is_alive() and threading.current_thread() != self._feeder_thread:
            self._feeder_thread.join(timeout=0.5)
        self._feeder_thread = None

        if self._pyvirtualcam_cam is not None:
            try:
                self._pyvirtualcam_cam.close()
            except Exception:
                pass
            self._pyvirtualcam_cam = None

        if self._fd is not None:
            try:
                os.close(self._fd)
            except Exception:
                pass
            self._fd = None

# Backward compatibility alias
VirtualCamSink = V4L2Sink
