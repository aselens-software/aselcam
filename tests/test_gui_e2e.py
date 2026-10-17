#!/usr/bin/env python3
import os
import sys
import time
import unittest
import threading
from PyQt6.QtWidgets import QApplication

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../desktop")))

from aselcam.gui.main_window import MainWindow
from tests.test_stream_e2e import StreamServerMock

os.environ["QT_QPA_PLATFORM"] = "offscreen"

class TestGuiE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)
        cls.mock_server = StreamServerMock(host="127.0.0.1", video_port=4757, cmd_port=4758)
        cls.mock_server.start()
        time.sleep(0.3)

    @classmethod
    def tearDownClass(cls):
        cls.mock_server.stop()
        time.sleep(0.2)

    def test_gui_wifi_connect_and_stream(self):
        window = MainWindow()
        window.txt_ip.setText("127.0.0.1")
        window.txt_port.setText("4757")

        # Explicitly set 1920x1080 resolution and ensure preview enabled
        window.is_preview_enabled = True
        window.video_widget.set_preview_enabled(True)
        for i in range(window.combo_res.count()):
            if "1920x1080" in window.combo_res.itemText(i):
                window.combo_res.setCurrentIndex(i)
                break

        # 1. Connect
        window._toggle_connect_wifi()
        self.assertTrue(window.is_connected, "GUI should connect successfully via Wi-Fi")
        self.assertEqual(window.status_badge.text(), "🟢 YAYINDA")
        self.assertEqual(window.btn_connect_wifi.text(), "Bağlantıyı Kes")

        # 2. Wait for frames in video widget
        t0 = time.time()
        while time.time() - t0 < 5.0:
            self.app.processEvents()
            if window.video_widget._image is not None:
                break
            time.sleep(0.05)

        self.assertIsNotNone(window.video_widget._image, "VideoWidget should have received and rendered a frame")
        self.assertEqual(window.video_widget._res_text, "1920x1080")

        # 3. Test Camera Switching
        self.assertGreaterEqual(window.combo_remote_camera.count(), 2)
        window._remote_switch_camera()
        self.app.processEvents()

        # 4. Test Preview Toggle
        window._toggle_preview()
        self.assertFalse(window.is_preview_enabled)
        window._toggle_preview()
        self.assertTrue(window.is_preview_enabled)

        # 4. Test Settings Change
        for i in range(window.combo_res.count()):
            if "1280x720" in window.combo_res.itemText(i):
                window.combo_res.setCurrentIndex(i)
                break
        window._apply_stream_settings()
        self.app.processEvents()

        # 5. Remote controls test
        window._remote_switch_camera()
        window._remote_toggle_torch()
        window._remote_toggle_phone_preview()
        window._remote_toggle_blackout()

        # 6. Disconnect
        window._toggle_connect_wifi()
        self.assertFalse(window.is_connected)
        self.assertEqual(window.status_badge.text(), "🔴 ÇEVRİMDIŞI")
        self.assertIn(window.btn_connect_wifi.text(), ("Wi-Fi ile Bağlan", "Bağlan"))

        window.close()

if __name__ == "__main__":
    unittest.main()
