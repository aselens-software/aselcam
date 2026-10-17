import unittest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../desktop")))

from aselcam.core.filters import VideoFilters
from aselcam.core.audio_sink import AudioSink
from aselcam.core.v4l2_sink import V4L2Sink
from aselcam.core.adb_helper import AdbHelper
from aselcam.config import ConfigManager

class TestAselCam(unittest.TestCase):

    def test_video_filters_geometry(self):
        filters = VideoFilters()
        frame = np.zeros((100, 200, 3), dtype=np.uint8)
        frame[0, 0] = [255, 0, 0] # Top-left is blue

        # Test horizontal flip (mirror)
        filters.flip_h = True
        res = filters.apply(frame)
        self.assertEqual(res.shape, (100, 200, 3))
        np.testing.assert_array_equal(res[0, -1], [255, 0, 0])

        # Test rotation 90 degrees
        filters.flip_h = False
        filters.rotation = 90
        res = filters.apply(frame)
        self.assertEqual(res.shape, (200, 100, 3))

    def test_video_filters_color(self):
        filters = VideoFilters()
        frame = np.ones((10, 10, 3), dtype=np.uint8) * 100

        # Test invert
        filters.invert = True
        res = filters.apply(frame)
        self.assertEqual(res[0, 0, 0], 155)

        # Test grayscale
        filters.invert = False
        filters.grayscale = True
        res = filters.apply(frame)
        self.assertEqual(res[0, 0, 0], res[0, 0, 1])
        self.assertEqual(res[0, 0, 1], res[0, 0, 2])

    def test_config_manager(self):
        cfg = ConfigManager()
        cfg.set("test_key", 1234)
        self.assertEqual(cfg.get("test_key"), 1234)

    def test_v4l2_list_devices(self):
        devs = V4L2Sink.list_video_devices()
        self.assertIsInstance(devs, list)

    def test_adb_helper(self):
        adb = AdbHelper()
        self.assertTrue(adb.is_available())
        devs = adb.list_devices()
        self.assertIsInstance(devs, list)

if __name__ == "__main__":
    unittest.main()
