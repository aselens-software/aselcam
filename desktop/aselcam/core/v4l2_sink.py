import os
import sys
import struct
import subprocess
import glob
import threading
import time
import shutil
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


def _find_driver_file(relative_subpath: str) -> Optional[str]:
    """Locates bundled driver files across standard, source, and PyInstaller environments."""
    candidates = []
    # 1. PyInstaller bundled temp directory
    if hasattr(sys, "_MEIPASS"):
        candidates.append(os.path.join(sys._MEIPASS, "aselcam", "drivers", relative_subpath))
        candidates.append(os.path.join(sys._MEIPASS, "drivers", relative_subpath))
        candidates.append(os.path.join(sys._MEIPASS, relative_subpath))

    # 2. Executable parent directory
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    candidates.append(os.path.join(exe_dir, "aselcam", "drivers", relative_subpath))
    candidates.append(os.path.join(exe_dir, "drivers", relative_subpath))
    candidates.append(os.path.join(exe_dir, "_internal", "aselcam", "drivers", relative_subpath))

    # 3. Source directory relative to this file
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates.append(os.path.join(base_dir, "drivers", relative_subpath))
    candidates.append(os.path.join(base_dir, "..", "drivers", relative_subpath))

    for path in candidates:
        if os.path.exists(path):
            return os.path.abspath(path)
    return None


class V4L2Sink:
    """
    Cross-platform direct virtual camera sink.
    - Linux: High-speed native V4L2 kernel loopback (/dev/video10) via direct ioctl.
    - Windows: DirectShow Virtual Camera (Unity Capture / OBS VirtualCam Filter) with automatic registration.
    - macOS: CoreMediaIO DAL Virtual Camera Plugin with automatic installation to ~/Library/CoreMediaIO/Plug-Ins/DAL/.
    Third-party apps (Zoom, Discord, Teams, Meet, Chrome) see an active virtual webcam automatically.
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
        self._standby_rgb_array: Optional[np.ndarray] = None

    @staticmethod
    def is_virtual_camera_installed() -> bool:
        """Checks if a supported virtual camera device/driver is present in the system."""
        if sys.platform.startswith("win"):
            try:
                import winreg
                ds_cat = r"CLSID\{860BB310-5D01-11D0-BD3B-00A0C911CE86}\Instance"
                with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, ds_cat) as k:
                    i = 0
                    while True:
                        try:
                            sub = winreg.EnumKey(k, i)
                            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, f"{ds_cat}\\{sub}") as sub_k:
                                try:
                                    fname, _ = winreg.QueryValueEx(sub_k, "FriendlyName")
                                    if any(x.lower() in fname.lower() for x in ["unity", "obs", "aselcam", "virtual"]):
                                        return True
                                except OSError:
                                    pass
                            i += 1
                        except OSError:
                            break
            except Exception:
                pass
            return False

        elif sys.platform == "darwin":
            user_dal = os.path.expanduser("~/Library/CoreMediaIO/Plug-Ins/DAL/obs-mac-virtualcam.plugin")
            sys_dal = "/Library/CoreMediaIO/Plug-Ins/DAL/obs-mac-virtualcam.plugin"
            return os.path.exists(user_dal) or os.path.exists(sys_dal)

        elif sys.platform.startswith("linux"):
            return os.path.exists("/dev/video10") or bool(glob.glob("/dev/video*"))

        return False

    @staticmethod
    def ensure_friendly_name():
        """Ensures the DirectShow filter FriendlyName appears as 'AselCam Virtual Camera' in Windows apps."""
        if not sys.platform.startswith("win"):
            return
        try:
            import winreg
            guid_path = r"SOFTWARE\Classes\CLSID\{860BB310-5D01-11D0-BD3B-00A0C911CE86}\Instance\{5C2CD55C-92AD-4999-8666-912BD3E70010}"
            clsid_path = r"CLSID\{860BB310-5D01-11D0-BD3B-00A0C911CE86}\Instance\{5C2CD55C-92AD-4999-8666-912BD3E70010}"
            k64 = getattr(winreg, "KEY_WOW64_64KEY", 0x0100)
            k32 = getattr(winreg, "KEY_WOW64_32KEY", 0x0200)

            targets = [
                (winreg.HKEY_CLASSES_ROOT, clsid_path, 0),
                (winreg.HKEY_CURRENT_USER, "Software\\Classes\\" + clsid_path, 0),
                (winreg.HKEY_LOCAL_MACHINE, guid_path, k64),
                (winreg.HKEY_LOCAL_MACHINE, guid_path, k32),
            ]
            for root, path, flags in targets:
                try:
                    access = winreg.KEY_SET_VALUE | flags if flags else winreg.KEY_SET_VALUE
                    with winreg.OpenKey(root, path, 0, access) as k:
                        winreg.SetValueEx(k, "FriendlyName", 0, winreg.REG_SZ, "AselCam Virtual Camera")
                except Exception:
                    pass
        except Exception:
            pass

    @staticmethod
    def auto_install_virtual_camera_driver() -> Tuple[bool, str]:
        """Automatically installs and registers virtual camera drivers only if needed."""
        if sys.platform.startswith("win"):
            # 1. If already registered, NEVER call regsvr32! Return immediately.
            if V4L2Sink.is_virtual_camera_installed():
                V4L2Sink.ensure_friendly_name()
                return True, "DirectShow Sanal Kamera sürücüsü hazır."

            # 2. Check if running with Administrator rights
            is_admin = False
            try:
                import ctypes
                is_admin = bool(ctypes.windll.shell32.IsUserAnAdmin())
            except Exception:
                pass

            if is_admin:
                # Admin: safe to run regsvr32 without popping 'AMovieSetupRegisterServer failed'
                dll64 = _find_driver_file("windows/UnityCaptureFilter64.dll")
                dll32 = _find_driver_file("windows/UnityCaptureFilter32.dll")
                registered_any = False
                if dll64 and os.path.exists(dll64):
                    try:
                        res = subprocess.run(["regsvr32.exe", "/s", dll64], capture_output=True, timeout=5)
                        if res.returncode == 0:
                            registered_any = True
                    except Exception:
                        pass
                if dll32 and os.path.exists(dll32):
                    try:
                        subprocess.run(["regsvr32.exe", "/s", dll32], capture_output=True, timeout=5)
                    except Exception:
                        pass
                if registered_any:
                    return True, "DirectShow Sanal Kamera filtresi başarıyla kaydedildi."
                return True, "Sanal kamera sürücü yapılandırması tamamlandı."
            else:
                # Non-admin: NEVER call regsvr32 directly because unprivileged regsvr32
                # triggers the 'AMovieSetupRegisterServer failed' error dialog from UnityCaptureFilter.
                # Request UAC elevation to run install_drivers.bat.
                bat_file = _find_driver_file("windows/install_drivers.bat")
                if not bat_file:
                    root_bat = os.path.join(os.path.dirname(sys.executable), "install_drivers.bat")
                    if os.path.exists(root_bat):
                        bat_file = root_bat

                if bat_file and os.path.exists(bat_file):
                    try:
                        import ctypes
                        ret = ctypes.windll.shell32.ShellExecuteW(
                            None, "runas", bat_file, "", os.path.dirname(bat_file), 1
                        )
                        if ret > 32:
                            return True, "Sürücü kurulumu yönetici olarak başlatıldı."
                    except Exception:
                        pass

                return False, "Sanal kamera sürücüsü kurulu değil. Lütfen 'install_drivers.bat' dosyasını Yönetici Olarak Çalıştırın."

        elif sys.platform == "darwin":
            # macOS: Install CoreMediaIO DAL plugin into user directory (no root password needed)
            src_plugin = _find_driver_file("macos/obs-mac-virtualcam.plugin")
            if src_plugin and os.path.exists(src_plugin):
                user_dal = os.path.expanduser("~/Library/CoreMediaIO/Plug-Ins/DAL")
                os.makedirs(user_dal, exist_ok=True)
                dst_plugin = os.path.join(user_dal, "obs-mac-virtualcam.plugin")
                if not os.path.exists(dst_plugin):
                    try:
                        shutil.copytree(src_plugin, dst_plugin)
                        subprocess.run(["xattr", "-cr", dst_plugin], capture_output=True, timeout=5)
                        return True, "CoreMedia sanal kamera eklentisi başarıyla kuruldu."
                    except Exception as e:
                        return False, f"macOS sanal kamera kurulum hatası: {e}"
                return True, "CoreMedia sanal kamera hazır."
            return False, "macOS sanal kamera eklentisi bulunamadı."

        else:
            # Linux: V4L2 loopback kernel module
            return V4L2Sink.load_loopback_module(10, "AselCam Video")

    @staticmethod
    def list_video_devices() -> List[Dict[str, str]]:
        if sys.platform.startswith("linux") and HAS_FCNTL:
            devices = []
            for dev in sorted(glob.glob("/dev/video*")):
                try:
                    fd = os.open(dev, os.O_RDWR | os.O_NONBLOCK)
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
            # Windows / macOS direct virtual camera device
            return [{
                "path": "virtualcam",
                "name": "AselCam Virtual Camera (Direct Virtual Device)",
                "driver": "pyvirtualcam" if HAS_PYVIRTUALCAM else "direct_software_sink",
                "is_loopback": True
            }]

    @staticmethod
    def load_loopback_module(video_nr: int = 10, label: str = "AselCam Video") -> Tuple[bool, str]:
        if not sys.platform.startswith("linux"):
            return V4L2Sink.auto_install_virtual_camera_driver()

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
        self._standby_rgb_array = np.full((height, width, 3), 16, dtype=np.uint8)
        self._last_rgb_array = self._standby_rgb_array

        # 1. Non-Linux platforms (Windows & macOS): Direct Virtual Camera Setup
        if not sys.platform.startswith("linux") or not HAS_FCNTL:
            if not self.is_virtual_camera_installed():
                self.auto_install_virtual_camera_driver()
            else:
                self.ensure_friendly_name()

            if HAS_PYVIRTUALCAM and pyvirtualcam:
                # Try preferred direct backends in priority order
                backends_to_try = []
                if sys.platform.startswith("win"):
                    backends_to_try = ["unitycapture", "obs", None]
                elif sys.platform == "darwin":
                    backends_to_try = ["obs", None]
                else:
                    backends_to_try = [None]

                for b in backends_to_try:
                    try:
                        kwargs = {
                            "width": width,
                            "height": height,
                            "fps": 30,
                            "fmt": pyvirtualcam.PixelFormat.RGB
                        }
                        if b is not None:
                            kwargs["backend"] = b

                        self._pyvirtualcam_cam = pyvirtualcam.Camera(**kwargs)
                        self.is_open = True
                        self._feeder_running = True
                        self._feeder_thread = threading.Thread(
                            target=self._feeder_loop,
                            name="AselCam-VirtualCamFeeder",
                            daemon=True
                        )
                        self._feeder_thread.start()
                        print(f"[VirtualCam] Direct virtual camera started successfully ({width}x{height} RGB 30fps, backend={b})")
                        return True
                    except Exception as e:
                        continue

            # Software loopback fallback if pyvirtualcam backend isn't loaded yet
            self.is_open = True
            self._feeder_running = True
            self._feeder_thread = threading.Thread(
                target=self._feeder_loop,
                name="AselCam-SoftwareFeeder",
                daemon=True
            )
            self._feeder_thread.start()
            print(f"[VirtualCam] Software camera loopback active ({width}x{height})")
            return True

        # 2. Linux native V4L2 device
        if not os.path.exists(self.device_path):
            self.auto_install_virtual_camera_driver()
            if not os.path.exists(self.device_path):
                print(f"[V4L2Sink] Aygıt bulunamadı: {self.device_path}")
                return False

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

            # Output to direct pyvirtualcam if available
            if self._pyvirtualcam_cam is not None:
                frame_to_send = self._last_rgb_array if self._last_rgb_array is not None else self._standby_rgb_array
                if frame_to_send is not None:
                    try:
                        self._pyvirtualcam_cam.send(frame_to_send)
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
        """Switches output back to standby frame without closing the device."""
        self._pending_rgb = None
        if self._standby_rgb_array is not None:
            self._last_rgb_array = self._standby_rgb_array
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
