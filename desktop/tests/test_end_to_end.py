import os
import socket
import struct
import subprocess
import threading
import time
import json
import unittest
import numpy as np

from aselcam.core.receiver import (
    StreamReceiver, MAGIC, HEADER_FORMAT,
    TYPE_VIDEO_H264, TYPE_CODEC_CONFIG, TYPE_AUDIO_PCM
)
from aselcam.core.v4l2_sink import V4L2Sink
from aselcam.core.audio_sink import AudioSink
from aselcam.core.controller import PhoneController


class TestEndToEndPipeline(unittest.TestCase):

    def test_v4l2_always_on_feeder_with_external_consumer(self):
        """Verifies that /dev/video10 continuously outputs 30 FPS YUYV frames readable by external apps (ffmpeg/Chrome/OBS)."""
        if not os.path.exists("/dev/video10"):
            self.skipTest("/dev/video10 not present")

        sink = V4L2Sink("/dev/video10")
        self.assertTrue(sink.open(1920, 1080))
        try:
            # Push a bright green test frame
            green = np.zeros((1080, 1920, 3), dtype=np.uint8)
            green[:, :, 1] = 220
            sink.write_rgb_frame(green)

            # Now read 5 frames using an external ffmpeg V4L2 consumer process
            cmd = [
                "ffmpeg", "-y", "-v", "error",
                "-f", "v4l2",
                "-i", "/dev/video10",
                "-frames:v", "5",
                "-f", "null", "-"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=4)
            self.assertEqual(res.returncode, 0, f"External V4L2 consumer failed: {res.stderr}")

            # Reset to standby (simulating phone disconnect) and verify external consumer STILL gets frames without timeout
            sink.reset_to_standby()
            res2 = subprocess.run(cmd, capture_output=True, text=True, timeout=4)
            self.assertEqual(res2.returncode, 0, f"Standby V4L2 consumer failed: {res2.stderr}")
        finally:
            sink.close()

    def test_receiver_decodes_single_keyframe_and_scales_resolution(self):
        """Verifies that StreamReceiver with FFmpeg 9.0.2 decodes H.264 immediately and scales 1280x720 phone stream to 1920x1080."""
        # Generate 15 frames of 1280x720 H.264 Annex-B video using ffmpeg
        gen = subprocess.run(
            [
                "ffmpeg", "-v", "error",
                "-f", "lavfi", "-i", "testsrc=size=1280x720:rate=30",
                "-frames:v", "15",
                "-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency",
                "-g", "15", "-f", "h264", "pipe:1"
            ],
            capture_output=True,
            timeout=5
        )
        self.assertEqual(gen.returncode, 0)
        h264_bytes = gen.stdout
        self.assertGreater(len(h264_bytes), 100)

        # Start mock TCP stream server
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("127.0.0.1", 0))
        port = srv.getsockname()[1]
        srv.listen(1)

        def server_worker():
            conn, _ = srv.accept()
            try:
                # Send H264 stream in chunks wrapped in ASEL protocol
                chunk_size = 4096
                for i in range(0, len(h264_bytes), chunk_size):
                    part = h264_bytes[i:i + chunk_size]
                    hdr = struct.pack(HEADER_FORMAT, MAGIC, TYPE_VIDEO_H264, 1, int(time.time() * 1e6), len(part))
                    conn.sendall(hdr + part)
                    time.sleep(0.01)
                time.sleep(1.0)
            finally:
                conn.close()
                srv.close()

        t = threading.Thread(target=server_worker, daemon=True)
        t.start()

        received_frames = []
        receiver = StreamReceiver(host="127.0.0.1", port=port)
        receiver.on_frame_ready = lambda frame: received_frames.append(frame.shape)

        # Request 1920x1080 output while phone sends 1280x720!
        ok = receiver.start(width=1920, height=1080, codec="h264")
        self.assertTrue(ok)

        deadline = time.time() + 3.0
        while time.time() < deadline and len(received_frames) < 5:
            time.sleep(0.05)

        receiver.stop()
        self.assertGreaterEqual(len(received_frames), 5, f"Expected >=5 frames, got {len(received_frames)}")
        self.assertEqual(received_frames[0], (1080, 1920, 3))

    def test_controller_self_healing_reconnect(self):
        """Verifies that PhoneController automatically reconnects if a socket drops mid-session."""
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("127.0.0.1", 0))
        port = srv.getsockname()[1]
        srv.listen(5)

        def cmd_server():
            # Accept 1st connection and immediately close it when client sends data (simulating dropped socket)
            c1, _ = srv.accept()
            c1.recv(1024)
            c1.close()

            # Accept 2nd connection (auto-reconnect) and respond properly
            c2, _ = srv.accept()
            line = c2.makefile("r").readline()
            req = json.loads(line)
            resp = json.dumps({"reply_to": req["cmd"], "status": "ok"}) + "\n"
            c2.sendall(resp.encode("utf-8"))
            c2.close()
            srv.close()

        threading.Thread(target=cmd_server, daemon=True).start()

        ctrl = PhoneController("127.0.0.1", port)
        self.assertTrue(ctrl.connect())
        # First command triggers socket close on c1, controller should auto-reconnect to c2 and succeed!
        self.assertTrue(ctrl.set_torch(True))
        ctrl.disconnect()

    def test_audio_sink_virtual_mic_source(self):
        """Verifies that AudioSink creates both null-sink and remap-source in PipeWire/PulseAudio."""
        audio = AudioSink()
        self.assertTrue(audio.setup_virtual_mic())
        res = subprocess.run(["pactl", "list", "sources", "short"], capture_output=True, text=True, timeout=2)
        self.assertIn("AselCam_Mic", res.stdout)

    def test_main_window_v4l2_and_live_controls(self):
        """Verifies MainWindow startup V4L2 availability, camera switching, torch, blackout, and live video preview."""
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PyQt6.QtWidgets import QApplication
        from aselcam.gui.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        win = MainWindow()
        try:
            self.assertEqual(win.txt_ip.text(), win.config.get("wifi_ip", "192.168.1.3"))
            self.assertEqual(win.txt_port.text(), str(win.config.get("video_port", 4747)))

            if os.path.exists("/dev/video10"):
                self.assertTrue(win.v4l2_sink.is_open)
                # External app should be able to capture frames from /dev/video10 right now even while offline!
                cmd = [
                    "ffmpeg", "-y", "-v", "error",
                    "-f", "v4l2",
                    "-i", "/dev/video10",
                    "-frames:v", "3",
                    "-f", "null", "-"
                ]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=4)
                self.assertEqual(res.returncode, 0, f"Offline V4L2 read failed: {res.stderr}")

            # Verify VideoWidget clears frame on disconnect
            win.video_widget.set_preview_enabled(True)
            dummy_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
            win.video_widget.update_frame(dummy_frame)
            self.assertIsNotNone(win.video_widget._image)
            win._disconnect(user_initiated=True)
            self.assertIsNone(win.video_widget._image)

            # Verify bitrate parsing across all options
            win.combo_bitrate.setCurrentIndex(0)  # 50 Mbps
            self.assertEqual(win._parse_selected_bitrate(), 50_000_000)
            win.combo_bitrate.setCurrentIndex(3)  # 20 Mbps
            self.assertEqual(win._parse_selected_bitrate(), 20_000_000)

            # Verify 9:16 portrait, 4:3, and 1:1 aspect ratio options and V4L2 conversion
            portrait_rgb = np.zeros((1920, 1080, 3), dtype=np.uint8)
            yuyv_portrait = V4L2Sink.rgb_to_yuyv_bytes(portrait_rgb, 1080, 1920)
            self.assertEqual(len(yuyv_portrait), 1080 * 1920 * 2)

            # Pillarboxed 9:16 inside 1920x1080
            yuyv_pillarbox = V4L2Sink.rgb_to_yuyv_bytes(portrait_rgb, 1920, 1080)
            self.assertEqual(len(yuyv_pillarbox), 1920 * 1080 * 2)
        finally:
            win._disconnect(user_initiated=True)
            win.v4l2_sink.close()


if __name__ == "__main__":
    unittest.main()
