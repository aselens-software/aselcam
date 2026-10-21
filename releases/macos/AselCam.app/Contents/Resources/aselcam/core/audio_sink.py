import os
import sys
import shutil
import subprocess
import threading
import numpy as np
from typing import Optional, Callable, Tuple

try:
    import ctypes
    from ctypes import wintypes
    HAS_CTYPES = True
except ImportError:
    ctypes = None
    HAS_CTYPES = False


def _find_audio_driver_file(relative_subpath: str) -> Optional[str]:
    """Locates bundled audio driver files across standard, source, and PyInstaller environments."""
    candidates = []
    if hasattr(sys, "_MEIPASS"):
        candidates.append(os.path.join(sys._MEIPASS, "aselcam", "drivers", relative_subpath))
        candidates.append(os.path.join(sys._MEIPASS, "drivers", relative_subpath))
        candidates.append(os.path.join(sys._MEIPASS, relative_subpath))

    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    candidates.append(os.path.join(exe_dir, "aselcam", "drivers", relative_subpath))
    candidates.append(os.path.join(exe_dir, "drivers", relative_subpath))
    candidates.append(os.path.join(exe_dir, "_internal", "aselcam", "drivers", relative_subpath))

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates.append(os.path.join(base_dir, "drivers", relative_subpath))
    candidates.append(os.path.join(base_dir, "..", "drivers", relative_subpath))

    for path in candidates:
        if os.path.exists(path):
            return os.path.abspath(path)
    return None


class WindowsWaveOutPlayer:
    """Pure-Python Windows waveOut audio player using built-in winmm.dll (no external dependencies)."""
    def __init__(self, sample_rate: int = 24000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.hWaveOut = None
        self._lock = threading.Lock()
        self._is_open = False

        if not sys.platform.startswith("win") or not HAS_CTYPES:
            return

        try:
            self._winmm = ctypes.windll.winmm
            self._open_device()
        except Exception as e:
            print(f"[WindowsWaveOut] Initialization notice: {e}")

    def _open_device(self):
        # WAVEFORMATEX structure: wFormatTag, nChannels, nSamplesPerSec, nAvgBytesPerSec, nBlockAlign, wBitsPerSample, cbSize
        class WAVEFORMATEX(ctypes.Structure):
            _fields_ = [
                ("wFormatTag", wintypes.WORD),
                ("nChannels", wintypes.WORD),
                ("nSamplesPerSec", wintypes.DWORD),
                ("nAvgBytesPerSec", wintypes.DWORD),
                ("nBlockAlign", wintypes.WORD),
                ("wBitsPerSample", wintypes.WORD),
                ("cbSize", wintypes.WORD),
            ]

        wfx = WAVEFORMATEX()
        wfx.wFormatTag = 1  # WAVE_FORMAT_PCM
        wfx.nChannels = self.channels
        wfx.nSamplesPerSec = self.sample_rate
        wfx.wBitsPerSample = 16
        wfx.nBlockAlign = (wfx.nChannels * wfx.wBitsPerSample) // 8
        wfx.nAvgBytesPerSec = wfx.nSamplesPerSec * wfx.nBlockAlign
        wfx.cbSize = 0

        # Scan for Virtual Audio device ID
        dev_id = -1  # WAVE_MAPPER default
        try:
            num_devs = self._winmm.waveOutGetNumDevs()
            class WAVEOUTCAPSW(ctypes.Structure):
                _fields_ = [
                    ("wMid", wintypes.WORD),
                    ("wPid", wintypes.WORD),
                    ("vDriverVersion", wintypes.UINT),
                    ("szPname", ctypes.c_wchar * 32),
                    ("dwFormats", wintypes.DWORD),
                    ("wChannels", wintypes.WORD),
                    ("wReserved1", wintypes.WORD),
                    ("dwSupport", wintypes.DWORD),
                ]
            caps = WAVEOUTCAPSW()
            for i in range(num_devs):
                if self._winmm.waveOutGetDevCapsW(i, ctypes.byref(caps), ctypes.sizeof(caps)) == 0:
                    name = caps.szPname.lower()
                    if any(k in name for k in ["virtual audio", "virtual mic", "cable", "aselcam"]):
                        dev_id = i
                        print(f"[WindowsWaveOut] Found virtual audio device [{i}]: {caps.szPname}")
                        break
        except Exception:
            pass

        self.hWaveOut = wintypes.HANDLE()
        res = self._winmm.waveOutOpen(
            ctypes.byref(self.hWaveOut),
            dev_id,
            ctypes.byref(wfx),
            0, 0, 0
        )
        if res == 0:
            self._is_open = True
            print(f"[WindowsWaveOut] waveOut opened (dev_id={dev_id}, rate={self.sample_rate}Hz)")

    def write(self, pcm_bytes: bytes):
        if not self._is_open or not self.hWaveOut:
            return

        class WAVEHDR(ctypes.Structure):
            pass
        WAVEHDR._fields_ = [
            ("lpData", ctypes.c_char_p),
            ("dwBufferLength", wintypes.DWORD),
            ("dwBytesRecorded", wintypes.DWORD),
            ("dwUser", ctypes.c_void_p),
            ("dwFlags", wintypes.DWORD),
            ("dwLoops", wintypes.DWORD),
            ("lpNext", ctypes.c_void_p),
            ("reserved", ctypes.c_void_p),
        ]

        try:
            header = WAVEHDR()
            header.lpData = pcm_bytes
            header.dwBufferLength = len(pcm_bytes)
            header.dwFlags = 0

            with self._lock:
                self._winmm.waveOutPrepareHeader(self.hWaveOut, ctypes.byref(header), ctypes.sizeof(header))
                self._winmm.waveOutWrite(self.hWaveOut, ctypes.byref(header), ctypes.sizeof(header))
        except Exception:
            pass

    def close(self):
        if self._is_open and self.hWaveOut:
            try:
                self._winmm.waveOutReset(self.hWaveOut)
                self._winmm.waveOutClose(self.hWaveOut)
            except Exception:
                pass
            self.hWaveOut = None
            self._is_open = False


class AudioSink:
    """
    Cross-platform direct virtual microphone sink.
    - Linux: Pipes real-time PCM audio directly to PulseAudio / PipeWire null-sink (AselCam_Mic).
    - Windows: Direct audio stream to Windows Virtual Audio Driver with automatic installation.
    - macOS: Direct audio output to BlackHole 2ch with automatic driver installation.
    All applications (Zoom, Discord, Teams, Meet) receive the phone microphone stream seamlessly.
    """
    def __init__(self, sink_name: str = "AselCam_Mic", sink_desc: str = "AselCam_Microphone"):
        self.sink_name = sink_name
        self.sink_desc = sink_desc
        self.source_name = f"{sink_name}_Source"
        self.module_id: Optional[str] = None
        self.remap_module_id: Optional[str] = None
        self._pacat_proc: Optional[subprocess.Popen] = None
        self._mac_audio_proc: Optional[subprocess.Popen] = None
        self._win_player: Optional[WindowsWaveOutPlayer] = None
        self._lock = threading.Lock()
        self._rate = 24000
        self._channels = 1
        self._is_running = False
        self._gain = 1.0
        self._muted = False
        self.on_level_callback: Optional[Callable[[float], None]] = None

    @staticmethod
    def auto_install_virtual_audio_driver() -> Tuple[bool, str]:
        """Automatically installs virtual audio driver if not present."""
        if sys.platform.startswith("win"):
            # Windows: Install Virtual Audio Driver via PnPUtil
            inf_path = _find_audio_driver_file("windows/VirtualAudioDriver.inf")
            if inf_path and os.path.exists(inf_path):
                try:
                    res = subprocess.run(
                        ["pnputil.exe", "/add-driver", inf_path, "/install"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if res.returncode == 0:
                        return True, "AselCam Sanal Ses Sürücüsü başarıyla yüklendi."
                except Exception:
                    pass
            return True, "Windows Sanal Mikrofon hazır."

        elif sys.platform == "darwin":
            # macOS: Install BlackHole driver or package
            system_hal = "/Library/Audio/Plug-Ins/HAL"
            driver_dir = _find_audio_driver_file("macos/BlackHole2ch.driver")
            pkg_path = _find_audio_driver_file("macos/BlackHole2ch-0.7.1.pkg")

            if driver_dir and os.path.exists(driver_dir) and not os.path.exists(os.path.join(system_hal, "BlackHole2ch.driver")):
                try:
                    if pkg_path and os.path.exists(pkg_path):
                        subprocess.run(
                            ["osascript", "-e", f"do shell script \"installer -pkg '{pkg_path}' -target /\" with administrator privileges"],
                            capture_output=True,
                            timeout=30
                        )
                    else:
                        subprocess.run(
                            ["osascript", "-e", f"do shell script \"cp -R '{driver_dir}' '{system_hal}/' && killall -9 coreaudiod\" with administrator privileges"],
                            capture_output=True,
                            timeout=30
                        )
                    return True, "macOS BlackHole Sanal Mikrofon sürücüsü kuruldu."
                except Exception as e:
                    return False, f"macOS sanal mikrofon kurulum hatası: {e}"
            return True, "macOS Sanal Mikrofon hazır."

        else:
            # Linux PulseAudio/PipeWire
            return True, "Linux ses altyapısı hazır."

    def setup_virtual_mic(self) -> bool:
        """Configures virtual microphone endpoint on the current operating system."""
        self.auto_install_virtual_audio_driver()

        if sys.platform.startswith("win"):
            return True

        if sys.platform == "darwin":
            return True

        # Linux PulseAudio / PipeWire configuration
        if not shutil.which("pactl") or not sys.platform.startswith("linux"):
            return True

        try:
            res = subprocess.run(["pactl", "list", "modules", "short"], capture_output=True, text=True, timeout=2)
            modules_out = res.stdout if res.returncode == 0 else ""

            for line in modules_out.splitlines():
                if f"sink_name={self.sink_name}" in line or (self.sink_name in line and "module-null-sink" in line):
                    self.module_id = line.split()[0]
                if f"source_name={self.source_name}" in line:
                    self.remap_module_id = line.split()[0]

            if not self.module_id:
                cmd = [
                    "pactl", "load-module", "module-null-sink",
                    f"sink_name={self.sink_name}",
                    f'sink_properties=device.description="{self.sink_desc}_Sink"'
                ]
                res_sink = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
                if res_sink.returncode == 0:
                    self.module_id = res_sink.stdout.strip()
                    print(f"[AudioSink] Loaded null-sink module id: {self.module_id}")
                else:
                    return False

            if not self.remap_module_id:
                cmd_remap = [
                    "pactl", "load-module", "module-remap-source",
                    f"master={self.sink_name}.monitor",
                    f"source_name={self.source_name}",
                    f'source_properties=device.description="{self.sink_desc}"'
                ]
                res_remap = subprocess.run(cmd_remap, capture_output=True, text=True, timeout=3)
                if res_remap.returncode == 0:
                    self.remap_module_id = res_remap.stdout.strip()
                    print(f"[AudioSink] Loaded remap-source module id: {self.remap_module_id}")

            return True
        except Exception as e:
            print(f"[AudioSink] Error setting up virtual mic: {e}")
            return False

    def start_playback(self, rate: int = 24000, channels: int = 1) -> bool:
        """Starts real-time playback into the virtual microphone device."""
        self.stop_playback()
        self.setup_virtual_mic()
        self._rate = rate
        self._channels = channels

        with self._lock:
            # 1. Windows: Native WaveOut Direct Player
            if sys.platform.startswith("win"):
                try:
                    self._win_player = WindowsWaveOutPlayer(sample_rate=rate, channels=channels)
                    self._is_running = True
                    return True
                except Exception as e:
                    print(f"[AudioSink] Windows waveOut notice: {e}")
                    self._is_running = True
                    return True

            # 2. macOS: CoreAudio / ffplay / sox pipe
            elif sys.platform == "darwin":
                for cmd_name, cmd in [
                    ("sox", ["sox", "-t", "raw", "-r", str(rate), "-c", str(channels), "-b", "16", "-e", "signed-integer", "-", "-d"]),
                    ("ffplay", ["ffplay", "-nodisp", "-autoexit", "-f", "s16le", "-ar", str(rate), "-ac", str(channels), "-i", "-"]),
                ]:
                    if shutil.which(cmd_name):
                        try:
                            self._mac_audio_proc = subprocess.Popen(
                                cmd,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                                bufsize=0
                            )
                            self._is_running = True
                            return True
                        except Exception:
                            pass
                self._is_running = True
                return True

            # 3. Linux: pacat pipe to PulseAudio / PipeWire null-sink
            else:
                if not shutil.which("pacat"):
                    self._is_running = True
                    return True

                try:
                    cmd = [
                        "pacat",
                        "--playback",
                        "-d", self.sink_name,
                        "--format=s16le",
                        f"--rate={rate}",
                        f"--channels={channels}",
                        "--latency-msec=20"
                    ]
                    self._pacat_proc = subprocess.Popen(
                        cmd,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        bufsize=0
                    )
                    self._is_running = True
                    return True
                except Exception as e:
                    print(f"[AudioSink] Error starting pacat: {e}")
                    self._is_running = True
                    return False

    def write_audio(self, pcm_data: bytes):
        """Writes PCM 16-bit audio chunk to the virtual microphone device and emits VU level."""
        with self._lock:
            if not self._is_running:
                return

            try:
                if self._muted:
                    if self.on_level_callback:
                        self.on_level_callback(0.0)
                    return

                samples = np.frombuffer(pcm_data, dtype=np.int16)
                if self._gain != 1.0:
                    amplified = (samples.astype(np.float32) * self._gain)
                    np.clip(amplified, -32768, 32767, out=amplified)
                    samples = amplified.astype(np.int16)
                    pcm_data = samples.tobytes()

                # Output to Linux pacat
                if self._pacat_proc and self._pacat_proc.stdin:
                    self._pacat_proc.stdin.write(pcm_data)

                # Output to Windows WaveOut
                if self._win_player:
                    self._win_player.write(pcm_data)

                # Output to macOS audio pipe
                if self._mac_audio_proc and self._mac_audio_proc.stdin:
                    self._mac_audio_proc.stdin.write(pcm_data)

                # Fast VU meter RMS level computation for HUD telemetry
                if self.on_level_callback and len(samples) > 0:
                    sub = samples[::4].astype(np.float32)
                    rms = np.sqrt(np.mean(sub ** 2))
                    level = min(1.0, float(rms / 16384.0))
                    self.on_level_callback(level)

            except (BrokenPipeError, OSError, ValueError, AttributeError):
                self._pacat_proc = None
                self._mac_audio_proc = None

    def set_gain(self, gain: float):
        self._gain = max(0.0, gain)

    def set_muted(self, muted: bool):
        self._muted = muted

    def stop_playback(self):
        with self._lock:
            self._is_running = False

            if self._win_player:
                self._win_player.close()
                self._win_player = None

            proc = self._pacat_proc
            self._pacat_proc = None
            if proc:
                try:
                    if proc.stdin:
                        proc.stdin.close()
                    proc.terminate()
                    proc.wait(timeout=0.5)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass

            mac_proc = self._mac_audio_proc
            self._mac_audio_proc = None
            if mac_proc:
                try:
                    if mac_proc.stdin:
                        mac_proc.stdin.close()
                    mac_proc.terminate()
                    mac_proc.wait(timeout=0.5)
                except Exception:
                    try:
                        mac_proc.kill()
                    except Exception:
                        pass

    def teardown_virtual_mic(self):
        self.stop_playback()
        if not shutil.which("pactl"):
            return
        if self.remap_module_id:
            try:
                subprocess.run(["pactl", "unload-module", self.remap_module_id], capture_output=True, timeout=2)
            except Exception:
                pass
            self.remap_module_id = None
        if self.module_id:
            try:
                subprocess.run(["pactl", "unload-module", self.module_id], capture_output=True, timeout=2)
                print(f"[AudioSink] Unloaded null-sink module: {self.module_id}")
            except Exception:
                pass
            self.module_id = None
