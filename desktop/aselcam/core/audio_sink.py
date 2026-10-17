import subprocess
import shutil
import threading
import sys
import numpy as np
from typing import Optional, Callable

class AudioSink:
    """
    Cross-platform virtual audio sink.
    - On Linux: Configures PipeWire/PulseAudio null-sink and remap-source via pactl/pacat.
    - On Windows/macOS: Monitors real-time PCM audio streams and powers the VU level meter.
    """
    def __init__(self, sink_name: str = "AselCam_Mic", sink_desc: str = "AselCam_Microphone"):
        self.sink_name = sink_name
        self.sink_desc = sink_desc
        self.source_name = f"{sink_name}_Source"
        self.module_id: Optional[str] = None
        self.remap_module_id: Optional[str] = None
        self._pacat_proc: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        self._rate = 24000
        self._channels = 1
        self._is_running = False
        self._gain = 1.0
        self._muted = False
        self.on_level_callback: Optional[Callable[[float], None]] = None

    def setup_virtual_mic(self) -> bool:
        """Loads pulse/pipewire null-sink and remap-source modules on Linux."""
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
                    print(f"[AudioSink] Failed to load null sink: {res_sink.stderr}")
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
        """Starts pacat process that pipes raw audio to AselCam_Mic on Linux, or monitor mode."""
        self.stop_playback()
        self.setup_virtual_mic()
        self._rate = rate
        self._channels = channels

        with self._lock:
            if not shutil.which("pacat") or not sys.platform.startswith("linux"):
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
        """Writes PCM 16-bit audio chunk to pacat stdin or computes telemetry."""
        with self._lock:
            if not self._is_running:
                return

            try:
                if self._muted:
                    if self._pacat_proc and self._pacat_proc.stdin:
                        silence = bytes(len(pcm_data))
                        self._pacat_proc.stdin.write(silence)
                    if self.on_level_callback:
                        self.on_level_callback(0.0)
                    return

                samples = np.frombuffer(pcm_data, dtype=np.int16)
                if self._gain != 1.0:
                    amplified = (samples.astype(np.float32) * self._gain)
                    np.clip(amplified, -32768, 32767, out=amplified)
                    samples = amplified.astype(np.int16)
                    pcm_data = samples.tobytes()

                if self._pacat_proc and self._pacat_proc.stdin:
                    self._pacat_proc.stdin.write(pcm_data)

                # Fast VU meter RMS level computation
                if self.on_level_callback and len(samples) > 0:
                    sub = samples[::4].astype(np.float32)
                    rms = np.sqrt(np.mean(sub ** 2))
                    level = min(1.0, float(rms / 16384.0))
                    self.on_level_callback(level)

            except (BrokenPipeError, OSError, ValueError, AttributeError):
                self._pacat_proc = None

    def set_gain(self, gain: float):
        self._gain = max(0.0, gain)

    def set_muted(self, muted: bool):
        self._muted = muted

    def stop_playback(self):
        with self._lock:
            self._is_running = False
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
