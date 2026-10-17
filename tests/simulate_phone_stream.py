#!/usr/bin/env python3
"""
AselCam Test Stream Simulator
Simulates an Android phone running AselCam for testing desktop receiver & GUI without phone hardware.
"""

import socket
import struct
import threading
import time
import subprocess
import json

MAGIC = b"ASEL"
TYPE_VIDEO_H264 = 0x01
TYPE_AUDIO_PCM = 0x03
TYPE_CODEC_CONFIG = 0x04

HEADER_FORMAT = ">4sB B Q I"

def run_command_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 4748))
    server.listen(5)
    print("[Sim-Control] Command server listening on 4748")

    while True:
        client, addr = server.accept()
        threading.Thread(target=handle_command_client, args=(client,), daemon=True).start()

def handle_command_client(client: socket.socket):
    with client:
        buf = ""
        while True:
            data = client.recv(1024).decode("utf-8")
            if not data:
                break
            buf += data
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                req = json.loads(line)
                cmd = req.get("cmd")
                res = {"reply_to": cmd, "status": "ok"}
                if cmd == "get_info":
                    res["data"] = {
                        "device_model": "AselCam Simulator Pro",
                        "android_version": "14",
                        "battery_level": 88,
                        "fps": 30,
                        "bitrate_bps": 8000000,
                        "clients": 1,
                        "is_streaming": True,
                        "cameras": [
                            {
                                "id": "0",
                                "name": "Arka Kamera (0)",
                                "is_back": True,
                                "max_zoom": 10.0,
                                "has_flash": True,
                                "resolutions": ["3840x2160", "2560x1440", "1920x1080", "1280x720"],
                                "fps_ranges": ["[30, 30]", "[60, 60]"]
                            },
                            {
                                "id": "1",
                                "name": "Ön Kamera (1)",
                                "is_back": False,
                                "max_zoom": 4.0,
                                "has_flash": False,
                                "resolutions": ["1920x1080", "1280x720"],
                                "fps_ranges": ["[30, 30]"]
                            }
                        ]
                    }
                elif cmd == "ping":
                    res["status"] = "pong"
                client.sendall((json.dumps(res) + "\n").encode("utf-8"))

def run_stream_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 4747))
    server.listen(5)
    print("[Sim-Media] Media stream server listening on 4747")

    while True:
        client, addr = server.accept()
        print(f"[Sim-Media] Desktop client connected from {addr}")
        threading.Thread(target=stream_synthetic_media, args=(client,), daemon=True).start()

def stream_synthetic_media(client: socket.socket):
    # Generates a synthetic test video stream using ffmpeg testsrc2
    cmd = [
        "ffmpeg",
        "-re",
        "-f", "lavfi",
        "-i", "testsrc2=size=1920x1080:rate=30",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-tune", "zerolatency",
        "-g", "30",
        "-f", "h264",
        "pipe:1"
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=64 * 1024)

    try:
        while True:
            chunk = proc.stdout.read(4096)
            if not chunk:
                break
            ts = int(time.time() * 1000000)
            header = struct.pack(HEADER_FORMAT, MAGIC, TYPE_VIDEO_H264, 0, ts, len(chunk))
            client.sendall(header + chunk)
    except Exception as e:
        print(f"[Sim-Media] Client disconnected: {e}")
    finally:
        proc.kill()
        client.close()

if __name__ == "__main__":
    t1 = threading.Thread(target=run_command_server, daemon=True)
    t2 = threading.Thread(target=run_stream_server, daemon=True)
    t1.start()
    t2.start()
    print("Phone simulator started. Press Ctrl+C to stop.")
    while True:
        time.sleep(1)
