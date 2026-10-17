import subprocess
import shutil
import os
from typing import List, Dict, Optional

class AdbHelper:
    def __init__(self):
        self.adb_bin = self._find_adb()

    def _find_adb(self) -> str:
        # Check standard SDK paths across Linux, macOS, and Windows
        home = os.path.expanduser("~")
        candidate_paths = [
            os.path.join(home, "Android", "Sdk", "platform-tools", "adb"),
            os.path.join(home, "Library", "Android", "sdk", "platform-tools", "adb"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Android", "Sdk", "platform-tools", "adb.exe"),
            os.path.join(os.environ.get("ProgramFiles", ""), "Android", "platform-tools", "adb.exe"),
        ]
        for p in candidate_paths:
            if p and os.path.exists(p) and (os.access(p, os.X_OK) or p.endswith(".exe")):
                return p

        # Check system PATH (shutil.which resolves adb.exe automatically on Windows)
        path_adb = shutil.which("adb")
        if path_adb:
            return path_adb

        return "adb"

    def is_available(self) -> bool:
        try:
            res = subprocess.run([self.adb_bin, "version"], capture_output=True, text=True, timeout=2)
            return res.returncode == 0
        except Exception:
            return False

    def list_devices(self) -> List[Dict[str, str]]:
        devices = []
        try:
            res = subprocess.run([self.adb_bin, "devices", "-l"], capture_output=True, text=True, timeout=3)
            for line in res.stdout.strip().splitlines()[1:]:
                parts = line.strip().split()
                if len(parts) >= 2 and parts[1] == "device":
                    serial = parts[0]
                    model = "Android Device"
                    for p in parts[2:]:
                        if p.startswith("model:"):
                            model = p.split(":", 1)[1].replace("_", " ")
                    devices.append({
                        "serial": serial,
                        "model": model,
                        "description": f"{model} ({serial})"
                    })
        except Exception as e:
            print(f"[ADB] Error listing devices: {e}")
        return devices

    def forward_ports(self, video_port: int = 4747, control_port: int = 4748, serial: Optional[str] = None) -> bool:
        try:
            cmd_prefix = [self.adb_bin]
            if serial:
                cmd_prefix.extend(["-s", serial])

            # Forward video port
            res1 = subprocess.run(cmd_prefix + ["forward", f"tcp:{video_port}", f"tcp:{video_port}"],
                                  capture_output=True, text=True, timeout=3)
            # Forward control port
            res2 = subprocess.run(cmd_prefix + ["forward", f"tcp:{control_port}", f"tcp:{control_port}"],
                                  capture_output=True, text=True, timeout=3)

            return res1.returncode == 0 and res2.returncode == 0
        except Exception as e:
            print(f"[ADB] Error forwarding ports: {e}")
            return False

    def remove_forward(self, video_port: int = 4747, control_port: int = 4748, serial: Optional[str] = None):
        try:
            cmd_prefix = [self.adb_bin]
            if serial:
                cmd_prefix.extend(["-s", serial])
            subprocess.run(cmd_prefix + ["forward", "--remove", f"tcp:{video_port}"], capture_output=True, timeout=2)
            subprocess.run(cmd_prefix + ["forward", "--remove", f"tcp:{control_port}"], capture_output=True, timeout=2)
        except Exception:
            pass
