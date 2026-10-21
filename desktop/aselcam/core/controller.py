import socket
import json
import threading
import time
from typing import Optional, Dict, Any, Callable

class PhoneController:
    def __init__(self, host: str = "127.0.0.1", port: int = 4748):
        self.host = host
        self.port = port
        self._socket: Optional[socket.socket] = None
        self._lock = threading.Lock()
        self.is_connected = False
        self.last_ping_ms: float = 0.0
        self._recv_buf = b""

    def connect(self, timeout: float = 3.0) -> bool:
        with self._lock:
            return self._connect_unlocked(timeout=timeout)

    def _connect_unlocked(self, timeout: float = 3.0) -> bool:
        self._disconnect_unlocked()
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            s.settimeout(timeout)
            s.connect((self.host, self.port))
            self._socket = s
            self.is_connected = True
            self._recv_buf = b""
            return True
        except Exception as e:
            print(f"[Controller] Bağlantı hatası ({self.host}:{self.port}): {e}")
            self.is_connected = False
            return False

    def _disconnect_unlocked(self):
        self.is_connected = False
        self._recv_buf = b""
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None

    def _read_json_response(self, timeout: float = 3.0) -> Optional[Dict[str, Any]]:
        if not self._socket:
            return None
        self._socket.settimeout(timeout)
        while b"\n" not in self._recv_buf:
            chunk = self._socket.recv(4096)
            if not chunk:
                raise ConnectionError("Bağlantı kapandı")
            self._recv_buf += chunk

        raw_line, self._recv_buf = self._recv_buf.split(b"\n", 1)
        line = raw_line.decode("utf-8", errors="ignore").strip()
        if line:
            return json.loads(line)
        return None

    def send_command(self, cmd_dict: Dict[str, Any], timeout: float = 3.0) -> Optional[Dict[str, Any]]:
        with self._lock:
            for attempt in range(2):
                if not self.is_connected or not self._socket:
                    if not self._connect_unlocked(timeout=min(timeout, 2.0)):
                        return None

                try:
                    assert self._socket is not None
                    payload = json.dumps(cmd_dict) + "\n"
                    self._socket.sendall(payload.encode("utf-8"))
                    return self._read_json_response(timeout=timeout)
                except Exception as e:
                    cmd_name = cmd_dict.get("cmd", "unknown")
                    print(f"[Controller] Komut gönderim uyarısı ({cmd_name}, deneme {attempt + 1}): {e}")
                    self._disconnect_unlocked()
                    if attempt == 0:
                        time.sleep(0.1)
                        continue
            return None

    def get_device_info(self) -> Optional[Dict[str, Any]]:
        resp = self.send_command({"cmd": "get_info"})
        if resp and resp.get("status") == "ok":
            return resp.get("data")
        return None

    def start_stream(self) -> bool:
        resp = self.send_command({"cmd": "start_stream"})
        return bool(resp and resp.get("status") == "ok")

    def stop_stream(self) -> bool:
        resp = self.send_command({"cmd": "stop_stream"})
        return bool(resp and resp.get("status") == "ok")

    def switch_camera(self, camera_id: str) -> bool:
        resp = self.send_command({"cmd": "switch_camera", "camera_id": str(camera_id)})
        return bool(resp and resp.get("status") == "ok")

    def set_torch(self, enabled: bool) -> bool:
        resp = self.send_command({"cmd": "set_torch", "enabled": enabled})
        return bool(resp and resp.get("status") == "ok")

    def set_zoom(self, zoom: float) -> bool:
        resp = self.send_command({"cmd": "set_zoom", "zoom": float(zoom)})
        return bool(resp and resp.get("status") == "ok")

    def set_config(self, width: int, height: int, fps: int, bitrate: int, codec: str = "h264") -> bool:
        resp = self.send_command({
            "cmd": "set_config",
            "width": width,
            "height": height,
            "fps": fps,
            "bitrate": bitrate,
            "codec": codec
        })
        return bool(resp and resp.get("status") == "ok")

    def set_mute(self, muted: bool) -> bool:
        resp = self.send_command({"cmd": "set_mute", "muted": muted})
        return bool(resp and resp.get("status") == "ok")

    def set_audio_gain(self, gain: float) -> bool:
        resp = self.send_command({"cmd": "set_audio_gain", "gain": float(gain)})
        return bool(resp and resp.get("status") == "ok")

    def set_preview_enabled(self, enabled: bool) -> bool:
        resp = self.send_command({"cmd": "set_preview", "enabled": enabled})
        return bool(resp and resp.get("status") == "ok")

    def set_camera_enabled(self, enabled: bool) -> bool:
        resp = self.send_command({"cmd": "set_camera_enabled", "enabled": bool(enabled)})
        return bool(resp and resp.get("status") == "ok")

    def set_blackout(self, enabled: bool) -> bool:
        resp = self.send_command({"cmd": "blackout", "enabled": enabled})
        return bool(resp and resp.get("status") == "ok")

    def set_screen_mirror(self, enabled: bool) -> bool:
        resp = self.send_command({"cmd": "set_screen_mirror", "enabled": bool(enabled)})
        return bool(resp and resp.get("status") == "ok")

    def ping(self) -> float:
        t0 = time.time()
        resp = self.send_command({"cmd": "ping"}, timeout=1.5)
        if resp and resp.get("status") == "pong":
            self.last_ping_ms = (time.time() - t0) * 1000.0
            return self.last_ping_ms
        return -1.0

    def disconnect(self):
        self.is_connected = False
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None
