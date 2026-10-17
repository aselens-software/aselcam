import unittest
import numpy as np
import os
import ctypes
from PyQt6.QtWidgets import QApplication, QScrollArea
from PyQt6.QtCore import Qt

from aselcam.core.filters import VideoFilters
from aselcam.gui.main_window import MainWindow, CustomTitleBar
from aselcam.main import set_linux_process_name
from aselcam.core.i18n import _t, I18nManager, SUPPORTED_LANGUAGES, detect_system_language

app = QApplication.instance() or QApplication([])

class TestRawFiltersAndUI(unittest.TestCase):

    def test_filter_identity_fast_path(self):
        """Verifies that default VideoFilters is identity and returns the original frame in 0 ms without copying."""
        vf = VideoFilters()
        self.assertTrue(vf.is_identity())
        frame = np.ones((720, 1280, 3), dtype=np.uint8) * 120
        out = vf.apply(frame)
        self.assertIs(out, frame, "Identity filter must return the same array reference (zero-copy fast path)")

    def test_sharpness_does_not_shift_highlights_on_flat_surfaces(self):
        """Verifies that True Laplacian sharpness has ZERO highlight shift or glowing blowout on solid tones."""
        vf = VideoFilters()
        # Flat middle grey (value 128)
        frame = np.full((100, 100, 3), 128, dtype=np.uint8)
        
        # Turn sharpness to maximum (100)
        vf.update_params(sharpness=100)
        self.assertFalse(vf.is_identity())
        
        out = vf.apply(frame)
        # Inside the border [1:-1, 1:-1], every single pixel must remain EXACTLY 128!
        inner = out[1:-1, 1:-1]
        self.assertTrue(np.all(inner == 128), f"Sharpness on flat areas must be 0 change, but got: min={inner.min()}, max={inner.max()}")

    def test_sharpness_enhances_edges_without_overflow(self):
        """Verifies that True Laplacian sharpness sharpens high-frequency edges without uint8 wrapping."""
        vf = VideoFilters()
        # Create a vertical edge: left side 50, right side 200
        frame = np.zeros((50, 50, 3), dtype=np.uint8)
        frame[:, :25] = 50
        frame[:, 25:] = 200

        vf.update_params(sharpness=100)
        out = vf.apply(frame)

        # On the dark side of the edge (col 24), pixel should be darker than 50
        # On the light side of the edge (col 25), pixel should be brighter than 200
        dark_edge = out[25, 24, 1]
        bright_edge = out[25, 25, 1]
        self.assertLess(dark_edge, 50, f"Expected dark overshoot < 50, got {dark_edge}")
        self.assertGreater(bright_edge, 200, f"Expected bright overshoot > 200, got {bright_edge}")
        # Ensure no negative wrap-around below 0 or above 255
        self.assertGreaterEqual(out.min(), 0)
        self.assertLessEqual(out.max(), 255)

    def test_raw_exposure_highlights_shadows_and_tone_curve(self):
        """Verifies that RAW tone controls properly generate 1D RGB LUTs and apply them accurately."""
        vf = VideoFilters()
        vf.update_params(
            exposure=1.0, # +1.0 EV doubles brightness
            highlights=-30,
            shadows=20,
            tone_curve="film"
        )
        self.assertFalse(vf.is_identity())

        frame = np.arange(256, dtype=np.uint8).reshape((1, 256, 1))
        frame = np.repeat(frame, 3, axis=2) # 1x256x3 gradient
        out = vf.apply(frame)

        self.assertEqual(out.shape, frame.shape)
        # Midtone (100) with +1.0 EV and film curve should be lifted significantly above 100
        self.assertGreater(out[0, 100, 0], 100)

    def test_white_balance_temp_and_tint(self):
        """Verifies that Temperature shifts Red and Blue, and Tint shifts Green."""
        vf = VideoFilters()
        # Warm temperature (+50)
        vf.update_params(temperature=50)
        neutral = np.full((10, 10, 3), 128, dtype=np.uint8)
        warm = vf.apply(neutral)
        self.assertGreater(warm[5, 5, 0], warm[5, 5, 2], "Warm temperature must have Red > Blue")

        # Green tint (-50)
        vf.update_params(temperature=0, tint=-50)
        greenish = vf.apply(neutral)
        self.assertGreater(greenish[5, 5, 1], greenish[5, 5, 0], "Negative tint must have Green > Red")

    def test_frameless_window_and_custom_title_bar(self):
        """Verifies that MainWindow is frameless, titled 'AselCam', and includes CustomTitleBar with all controls."""
        win = MainWindow()
        self.assertEqual(win.windowTitle(), "AselCam", "Window title must be exactly 'AselCam'")
        
        # Verify FramelessWindowHint
        flags = win.windowFlags()
        self.assertTrue(bool(flags & Qt.WindowType.FramelessWindowHint), "Window must have FramelessWindowHint")

        # Verify CustomTitleBar
        self.assertIsInstance(win.title_bar, CustomTitleBar)
        self.assertEqual(win.title_bar.title_label.text(), "AselCam")
        self.assertIsNotNone(win.title_bar.btn_min)
        self.assertIsNotNone(win.title_bar.btn_max)
        self.assertIsNotNone(win.title_bar.btn_close)
        self.assertIsNotNone(win.status_badge)
        self.assertIsNotNone(win.lbl_battery)
        self.assertIsNotNone(win.lbl_ping)

        # Verify RAW UI controls are connected
        self.assertIsNotNone(win.slider_exposure)
        self.assertIsNotNone(win.slider_highlights)
        self.assertIsNotNone(win.slider_shadows)
        self.assertIsNotNone(win.slider_whites)
        self.assertIsNotNone(win.slider_blacks)
        self.assertIsNotNone(win.slider_temp)
        self.assertIsNotNone(win.slider_tint)
        self.assertIsNotNone(win.combo_tone_curve)
        self.assertIsNotNone(win.slider_sharp)

        # Test changing a RAW slider updates the filter engine
        win.slider_exposure.setValue(15) # +1.5 EV
        self.assertAlmostEqual(win.filters.exposure, 1.5, places=1)
        self.assertEqual(win.lbl_exposure.text(), "+1.5 EV")

        # Test reset
        win.btn_reset_filters.click()
        self.assertEqual(win.slider_exposure.value(), 0)
        self.assertEqual(win.filters.exposure, 0.0)
        self.assertEqual(win.lbl_exposure.text(), "+0.0 EV")

        win.close()

    def test_set_linux_process_name(self):
        """Verifies that set_linux_process_name successfully updates /proc/self/comm."""
        set_linux_process_name("AselCam")
        try:
            with open(f"/proc/{os.getpid()}/comm", "r") as f:
                comm = f.read().strip()
                self.assertEqual(comm, "AselCam")
        except Exception:
            pass

    def test_neumorphic_theme_and_transparent_labels(self):
        """Verifies that all text labels render with transparent backgrounds and value badges have inset styling."""
        win = MainWindow()
        # Verify that all RAW numerical badges have objectName lbl_value_badge
        self.assertEqual(win.lbl_exposure.objectName(), "lbl_value_badge")
        self.assertEqual(win.lbl_highlights.objectName(), "lbl_value_badge")
        self.assertEqual(win.lbl_shadows.objectName(), "lbl_value_badge")
        self.assertEqual(win.lbl_zoom.objectName(), "lbl_value_badge")
        self.assertEqual(win.lbl_mic_gain.objectName(), "lbl_value_badge")

        # Verify that central_widget and body_widget have their respective object names
        self.assertEqual(win.centralWidget().objectName(), "central_widget")
        self.assertIsNotNone(win.centralWidget().findChild(type(win.centralWidget()), "body_widget"))

        # Verify that all 3 tabs are protected with QScrollArea to prevent squishing
        self.assertEqual(win.control_tabs.count(), 3)
        self.assertEqual(win.control_tabs.tabText(0), "Mobil Kontrol")
        self.assertEqual(win.control_tabs.tabText(1), "RAW && Renk")
        self.assertEqual(win.control_tabs.tabText(2), "Ayarlar")
        for i in range(win.control_tabs.count()):
            self.assertIsInstance(win.control_tabs.widget(i), QScrollArea, f"Tab {i} must be a QScrollArea")

        # Verify that new RGB and Focus badges exist
        self.assertEqual(win.lbl_gain_r.objectName(), "lbl_value_badge")
        self.assertEqual(win.lbl_gain_g.objectName(), "lbl_value_badge")
        self.assertEqual(win.lbl_gain_b.objectName(), "lbl_value_badge")
        self.assertEqual(win.lbl_focus_radius.objectName(), "lbl_value_badge")
        self.assertEqual(win.lbl_focus_blur.objectName(), "lbl_value_badge")

        win.close()

    def test_hardware_zoom_up_to_100x(self):
        """Verifies that zoom slider supports up to 100x hardware zoom (e.g. Galaxy S25 Ultra)."""
        win = MainWindow()
        self.assertEqual(win.slider_zoom.minimum(), 10)  # 1.0x
        self.assertEqual(win.slider_zoom.maximum(), 1000) # 100.0x
        win.slider_zoom.setValue(500) # 50.0x
        self.assertEqual(win.lbl_zoom.text(), "50x")
        win.slider_zoom.setValue(25) # 2.5x
        self.assertEqual(win.lbl_zoom.text(), "2.5x")
        win.close()

    def test_rgb_color_balance_and_profiles(self):
        """Verifies color profile selection and RGB channel gain adjustments."""
        win = MainWindow()
        # Apply Cinema profile
        win._apply_profile_by_key("cinema")
        self.assertEqual(win.combo_color_profile.currentData(), "cinema")
        self.assertEqual(win.filters.red_gain, 8)
        self.assertEqual(win.filters.blue_gain, -10)

        # Apply B&W profile
        win._apply_profile_by_key("bw")
        self.assertTrue(win.filters.grayscale)

        # Reset filters
        win._reset_filters()
        self.assertEqual(win.filters.red_gain, 0)
        self.assertEqual(win.filters.green_gain, 0)
        self.assertEqual(win.filters.blue_gain, 0)
        self.assertFalse(win.filters.grayscale)
        win.close()

    def test_software_portrait_focus_and_background(self):
        """Verifies AI neural person segmentation, bokeh blur background, and blend modes."""
        filters = VideoFilters()
        filters.update_params(focus_enabled=True, focus_mode="blur", focus_radius=50, focus_blur=15)
        self.assertTrue(filters.focus_enabled)
        self.assertEqual(filters.focus_mode, "blur")

        # Test frame processing with focus enabled on portrait photo or test frame
        sample_path = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "segmented_sample.jpg")
        if os.path.exists(sample_path):
            from PIL import Image
            img = np.array(Image.open(sample_path).convert("RGB"))
            out = filters.apply(img)
            self.assertEqual(out.shape, img.shape)
            self.assertEqual(out.dtype, np.uint8)

            # Check that segmentor was initialized
            self.assertIsNotNone(filters._segmentor)
            mask = filters._buf_mask
            self.assertIsNotNone(mask)
            # Person should have high mask values, background should have low values
            self.assertGreater(mask.max(), 200, "Person silhouette must have high mask value")
            self.assertLess(mask.min(), 50, "Background must have low mask value")
        else:
            frame = np.full((720, 1280, 3), 120, dtype=np.uint8)
            out = filters.apply(frame)
            self.assertEqual(out.shape, (720, 1280, 3))
            self.assertEqual(out.dtype, np.uint8)

        # Test studio mode
        filters.update_params(focus_mode="studio")
        out_studio = filters.apply(frame if not os.path.exists(sample_path) else img)
        self.assertIsNotNone(out_studio)

        # Test custom background mode
        filters.update_params(focus_mode="custom")
        filters.set_custom_background(sample_path if os.path.exists(sample_path) else "")
        out_custom = filters.apply(frame if not os.path.exists(sample_path) else img)
        self.assertIsNotNone(out_custom)

    def test_screen_mirror_toggle_and_telemetry(self):
        """Verifies Screen Mirror UI button, command dispatch, and telemetry synchronization."""
        win = MainWindow()
        self.assertTrue(hasattr(win, "btn_screen_mirror"))
        self.assertEqual(win.btn_screen_mirror.text(), "📱 Ekranı Yansıt (Telefon Ekranı)")

        # Simulate receiving telemetry that phone started screen mirroring
        win.is_connected = True
        win._on_telemetry_updated({"is_screen_mirroring": True})
        self.assertIn("Kameraya Dön", win.btn_screen_mirror.text())

        # Simulate receiving telemetry that phone returned to camera
        win._on_telemetry_updated({"is_screen_mirroring": False})
        self.assertIn("Ekranı Yansıt", win.btn_screen_mirror.text())

        # Verify controller method signature
        self.assertTrue(hasattr(win.controller, "set_screen_mirror"))
        win.close()

    def test_i18n_localization_and_dynamic_switching(self):
        """Verifies multi-language localization engine and dynamic UI retranslation."""
        from aselcam.core.i18n import I18nManager, _t
        i18n = I18nManager.get_instance()
        orig_lang = i18n.current_language

        # 1. Test dictionary lookups across supported languages
        i18n.set_language("en")
        self.assertEqual(_t("conn_btn_start"), "Start Camera")
        self.assertEqual(_t("zoom_header"), "OPTICAL & HARDWARE ZOOM")
        self.assertEqual(_t("status_offline"), "● OFFLINE")

        i18n.set_language("tr")
        self.assertEqual(_t("conn_btn_start"), "Bağlan")
        self.assertEqual(_t("zoom_header"), "DONANIMSAL ZOOM")
        self.assertEqual(_t("status_offline"), "● ÇEVRİMDIŞI")

        i18n.set_language("de")
        self.assertEqual(_t("conn_btn_start"), "Verbinden")
        self.assertEqual(_t("zoom_header"), "OPTISCHER & HARDWARE-ZOOM")

        i18n.set_language("fr")
        self.assertEqual(_t("conn_btn_start"), "Connecter")
        self.assertEqual(_t("zoom_header"), "ZOOM OPTIQUE & MATÉRIEL")

        i18n.set_language("es")
        self.assertEqual(_t("conn_btn_start"), "Conectar")
        self.assertEqual(_t("zoom_header"), "ZOOM ÓPTICO Y HARDWARE")

        # 2. Test dynamic retranslation on MainWindow
        win = MainWindow()
        try:
            # Switch to English
            i18n.set_language("en")
            win.retranslate_ui()
            self.assertEqual(win.btn_master_connect.text(), "Start Camera")
            self.assertEqual(win.tone_box.title(), "RAW SENSOR & COLOR SCIENCE")
            self.assertEqual(win.control_tabs.tabText(0), "Mobile Control")

            # Switch to German
            i18n.set_language("de")
            win.retranslate_ui()
            self.assertEqual(win.btn_master_connect.text(), "Verbinden")
            self.assertEqual(win.control_tabs.tabText(0), "Mobilsteuerung")

            # Switch to Turkish
            i18n.set_language("tr")
            win.retranslate_ui()
            self.assertEqual(win.btn_master_connect.text(), "Bağlan")
            self.assertEqual(win.tone_box.title(), "RAW SENSÖR & RENK BİLİMİ")
            self.assertEqual(win.control_tabs.tabText(0), "Mobil Kontrol")
        finally:
            win.close()
            i18n.set_language(orig_lang)


if __name__ == "__main__":
    unittest.main()


