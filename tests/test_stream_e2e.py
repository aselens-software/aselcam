#!/usr/bin/env python3
import os
import sys
import time
import unittest
import threading
import socket
import struct
import subprocess
import json
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../desktop")))

from aselcam.core.controller import PhoneController
from aselcam.core.receiver import StreamReceiver
from aselcam.core.filters import VideoFilters

MAGIC = b"ASEL"
TYPE_VIDEO_H264 = 0x01
HEADER_FORMAT = ">4sB B Q I"

class StreamServerMock:
    def __init__(self, host="127.0.0.1", video_port=4747, cmd_port=4748):
        self.host = host
        self.video_port = video_port
        self.cmd_port = cmd_port
        self.running = False
        self.cmd_server = None
        self.video_server = None
        self.ffmpeg_proc = None
        self.cmd_thread = None
        self.video_thread = None

    def start(self):
        self.running = True
        self.cmd_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.cmd_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.cmd_server.bind((self.host, self.cmd_port))
        self.cmd_server.listen(5)

        self.video_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.video_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.video_server.bind((self.host, self.video_port))
        self.video_server.listen(5)

        self.cmd_thread = threading.Thread(target=self._run_cmd, daemon=True)
        self.video_thread = threading.Thread(target=self._run_video, daemon=True)
        self.cmd_thread.start()
        self.video_thread.start()

    def _run_cmd(self):
        while self.running:
            try:
                client, _ = self.cmd_server.accept()
                threading.Thread(target=self._handle_cmd_client, args=(client,), daemon=True).start()
            except Exception:
                break

    def _handle_cmd_client(self, client):
        with client:
            buf = ""
            while self.running:
                try:
                    data = client.recv(1024).decode("utf-8")
                    if not data:
                        break
                    buf += data
                    while "\n" in buf:
                        line, buf = buf.split("\n", 1)
                        if not line.strip():
                            continue
                        req = json.loads(line)
                        cmd = req.get("cmd")
                        res = {"reply_to": cmd, "status": "ok"}
                        if cmd == "get_info":
                            res["data"] = {
                                "device_model": "Test Phone",
                                "battery_level": 95,
                                "is_streaming": True,
                                "cameras": [
                                    {"id": "0", "name": "Arka Kamera (0)", "is_back": True},
                                    {"id": "1", "name": "Ön Kamera (1)", "is_back": False}
                                ],
                                "current_camera": "0"
                            }
                        elif cmd == "switch_camera":
                            res["status"] = "ok"
                            res["camera_id"] = req.get("camera_id")
                        elif cmd == "ping":
                            res["status"] = "pong"
                        client.sendall((json.dumps(res) + "\n").encode("utf-8"))
                except Exception:
                    break

    def _run_video(self):
        while self.running:
            try:
                client, _ = self.video_server.accept()
                threading.Thread(target=self._handle_video_client, args=(client,), daemon=True).start()
            except Exception:
                break

    def _handle_video_client(self, client):
        cmd = [
            "ffmpeg",
            "-re",
            "-f", "lavfi",
            "-i", "testsrc=size=1920x1080:rate=30",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "zerolatency",
            "-g", "15",
            "-f", "h264",
            "pipe:1"
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=64 * 1024)
        self.ffmpeg_proc = proc

        try:
            with client:
                while self.running and proc.poll() is None:
                    chunk = proc.stdout.read(4096)
                    if not chunk:
                        break
                    ts = int(time.time() * 1000000)
                    header = struct.pack(HEADER_FORMAT, MAGIC, TYPE_VIDEO_H264, 0, ts, len(chunk))
                    client.sendall(header + chunk)
        except Exception:
            pass
        finally:
            try:
                proc.kill()
            except Exception:
                pass

    def stop(self):
        self.running = False
        if self.cmd_server:
            try:
                self.cmd_server.close()
            except Exception:
                pass
        if self.video_server:
            try:
                self.video_server.close()
            except Exception:
                pass
        if self.ffmpeg_proc:
            try:
                self.ffmpeg_proc.kill()
            except Exception:
                pass

class TestStreamE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mock_server = StreamServerMock(host="127.0.0.1", video_port=4747, cmd_port=4748)
        cls.mock_server.start()
        time.sleep(0.3)

    @classmethod
    def tearDownClass(cls):
        cls.mock_server.stop()

    def test_01_controller_commands(self):
        ctrl = PhoneController(host="127.0.0.1", port=4748)
        ok = ctrl.connect(timeout=2.0)
        self.assertTrue(ok, "Controller should connect to mock server")

        info = ctrl.get_device_info()
        self.assertIsNotNone(info)
        self.assertEqual(info.get("device_model"), "Test Phone")
        self.assertEqual(info.get("battery_level"), 95)
        self.assertTrue(info.get("is_streaming"))

        self.assertTrue(ctrl.switch_camera("1"))
        self.assertTrue(ctrl.set_torch(True))
        self.assertTrue(ctrl.set_zoom(2.0))
        self.assertTrue(ctrl.set_config(1920, 1080, 30, 8000000, "h264"))
        self.assertTrue(ctrl.set_preview_enabled(False))
        self.assertTrue(ctrl.set_blackout(True))
        self.assertTrue(ctrl.start_stream())
        self.assertTrue(ctrl.stop_stream())

        ping_ms = ctrl.ping()
        self.assertGreaterEqual(ping_ms, 0.0)

        ctrl.disconnect()
        self.assertFalse(ctrl.is_connected)

    def test_02_receiver_video_stream(self):
        received_frames = []
        frame_event = threading.Event()

        def on_frame(frame: np.ndarray):
            received_frames.append(frame)
            if len(received_frames) >= 5:
                frame_event.set()

        filters = VideoFilters()
        receiver = StreamReceiver(
            host="127.0.0.1",
            port=4747,
            filters=filters
        )
        receiver.on_frame_ready = on_frame

        ok = receiver.start(width=1920, height=1080, codec="h264")
        self.assertTrue(ok, "Receiver should connect to mock stream server")

        # Wait up to 5 seconds for at least 5 frames
        got_frames = frame_event.wait(timeout=5.0)
        self.assertTrue(got_frames, f"Expected >= 5 frames, got {len(received_frames)}")

        first_frame = received_frames[0]
        self.assertEqual(first_frame.shape, (1080, 1920, 3))
        self.assertEqual(first_frame.dtype, np.uint8)

        # Test resolution switch on the fly
        receiver.current_width = 1280
        receiver.current_height = 720
        receiver._start_decoder(1280, 720, codec="h264")

        received_frames.clear()
        frame_event.clear()
        got_scaled_frames = frame_event.wait(timeout=5.0)
        self.assertTrue(got_scaled_frames, f"Expected frames after res switch, got {len(received_frames)}")
        scaled_frame = received_frames[0]
        self.assertEqual(scaled_frame.shape, (720, 1280, 3))

        receiver.stop()
        self.assertFalse(receiver._is_running)

    def test_camera_switch_command(self):
        controller = PhoneController(host="127.0.0.1", port=4748)
        ok = controller.connect()
        self.assertTrue(ok, "Controller should connect")

        info = controller.get_device_info()
        self.assertIsNotNone(info)
        self.assertIn("cameras", info)
        self.assertEqual(len(info["cameras"]), 2)

        switched = controller.switch_camera("1")
        self.assertTrue(switched, "Switch camera command should succeed")

        controller.disconnect()

if __name__ == "__main__":
    unittest.main()
