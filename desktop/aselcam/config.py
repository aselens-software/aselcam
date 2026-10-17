import json
import os
from pathlib import Path
from typing import Any, Dict

CONFIG_DIR = Path.home() / ".config" / "aselcam"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "connection_mode": "usb",  # "usb" or "wifi"
    "language": "auto",        # "auto", "en", "tr", "de", "fr", "es"
    "wifi_ip": "192.168.1.3",
    "video_port": 4747,
    "control_port": 4748,
    "selected_camera": "0",  # "0" for back, "1" for front
    "resolution": "1920x1080",
    "fps": 30,
    "bitrate": 8000000,
    "codec": "h264",
    "v4l2_device": "/dev/video10",
    "audio_sink": "AselCam_Mic",
    "enable_audio": True,
    "audio_volume": 1.0,
    "preview_enabled": True,
    "filters": {
        "exposure": 0.0,       # -2.0 to 2.0 EV
        "highlights": 0,       # -100 to 100
        "shadows": 0,          # -100 to 100
        "whites": 0,           # -100 to 100
        "blacks": 0,           # -100 to 100
        "contrast": 0,         # -100 to 100
        "brightness": 0,       # -100 to 100
        "temperature": 0,      # -100 to 100
        "tint": 0,             # -100 to 100
        "tone_curve": "linear",# "linear", "film", "portrait", "vivid", "vintage"
        "saturation": 100,     # 0 to 200%
        "vibrance": 0,         # -100 to 100
        "red_gain": 0,         # -50 to +50
        "green_gain": 0,       # -50 to +50
        "blue_gain": 0,        # -50 to +50
        "color_profile": "standard", # "standard", "vivid", "cinema", "portrait", "lowlight", "vintage", "bw", "custom"
        "focus_enabled": False, # Software background / subject focus toggle
        "focus_mode": "blur",  # "blur", "studio", "custom"
        "focus_radius": 45,    # 20 to 100%
        "focus_blur": 15,      # 5 to 40
        "focus_image_path": "",
        "sharpness": 0,        # 0 to 100
        "flip_h": False,       # Mirror
        "flip_v": False,
        "rotation": 0,         # 0, 90, 180, 270
        "grayscale": False,
        "invert": False
    }
}

COLOR_PROFILES: Dict[str, Dict[str, Any]] = {
    "standard": {
        "name": "Standart (Doğal)",
        "exposure": 0.0, "highlights": 0, "shadows": 0, "whites": 0, "blacks": 0,
        "contrast": 0, "brightness": 0, "temperature": 0, "tint": 0,
        "tone_curve": "linear", "saturation": 100, "vibrance": 0,
        "red_gain": 0, "green_gain": 0, "blue_gain": 0, "sharpness": 0,
        "grayscale": False, "invert": False
    },
    "vivid": {
        "name": "Canlı Yayın (Vivid)",
        "exposure": 0.2, "highlights": -10, "shadows": 15, "whites": 10, "blacks": 0,
        "contrast": 12, "brightness": 5, "temperature": 0, "tint": 0,
        "tone_curve": "vivid", "saturation": 115, "vibrance": 20,
        "red_gain": 2, "green_gain": 0, "blue_gain": 2, "sharpness": 25,
        "grayscale": False, "invert": False
    },
    "cinema": {
        "name": "Sinematik Sıcak (Cine)",
        "exposure": 0.1, "highlights": -15, "shadows": 20, "whites": 5, "blacks": 10,
        "contrast": 18, "brightness": 0, "temperature": 18, "tint": -4,
        "tone_curve": "film", "saturation": 105, "vibrance": 10,
        "red_gain": 8, "green_gain": 0, "blue_gain": -10, "sharpness": 20,
        "grayscale": False, "invert": False
    },
    "portrait": {
        "name": "Stüdyo Portre (Yumuşak)",
        "exposure": 0.2, "highlights": -8, "shadows": 12, "whites": 0, "blacks": 0,
        "contrast": 6, "brightness": 2, "temperature": 8, "tint": 2,
        "tone_curve": "portrait", "saturation": 100, "vibrance": 12,
        "red_gain": 4, "green_gain": 0, "blue_gain": -2, "sharpness": 15,
        "grayscale": False, "invert": False
    },
    "lowlight": {
        "name": "Düşük Işık / Gece",
        "exposure": 0.8, "highlights": -20, "shadows": 35, "whites": 15, "blacks": -10,
        "contrast": 10, "brightness": 15, "temperature": 0, "tint": 0,
        "tone_curve": "linear", "saturation": 110, "vibrance": 15,
        "red_gain": 0, "green_gain": 0, "blue_gain": 0, "sharpness": 30,
        "grayscale": False, "invert": False
    },
    "vintage": {
        "name": "Retro / Vintage",
        "exposure": 0.0, "highlights": -25, "shadows": 15, "whites": 0, "blacks": 25,
        "contrast": -10, "brightness": 0, "temperature": 22, "tint": 8,
        "tone_curve": "vintage", "saturation": 85, "vibrance": -10,
        "red_gain": 12, "green_gain": 0, "blue_gain": -15, "sharpness": 10,
        "grayscale": False, "invert": False
    },
    "bw": {
        "name": "Siyah & Beyaz (B&W Mono)",
        "exposure": 0.0, "highlights": 15, "shadows": -10, "whites": 20, "blacks": 15,
        "contrast": 30, "brightness": 0, "temperature": 0, "tint": 0,
        "tone_curve": "linear", "saturation": 100, "vibrance": 0,
        "red_gain": 0, "green_gain": 0, "blue_gain": 0, "sharpness": 35,
        "grayscale": True, "invert": False
    }
}

class ConfigManager:
    def __init__(self):
        self._config: Dict[str, Any] = DEFAULT_CONFIG.copy()
        self.load()

    def load(self) -> Dict[str, Any]:
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._merge(self._config, data)
        except Exception as e:
            print(f"[Config] Error loading config: {e}")
        return self._config

    def save(self):
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Config] Error saving config: {e}")

    def _merge(self, base: dict, override: dict):
        for k, v in override.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                self._merge(base[k], v)
            else:
                base[k] = v

    def get(self, key: str, default=None):
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        self._config[key] = value
        self.save()

    def get_filter(self, name: str, default=None):
        return self._config.get("filters", {}).get(name, default)

    def set_filter(self, name: str, value: Any, save: bool = True):
        if "filters" not in self._config:
            self._config["filters"] = {}
        self._config["filters"][name] = value
        if save:
            self.save()

    def set_filters(self, filters_dict: Dict[str, Any], save: bool = True):
        if "filters" not in self._config:
            self._config["filters"] = {}
        self._config["filters"].update(filters_dict)
        if save:
            self.save()

    def reset_filters(self):
        self._config["filters"] = DEFAULT_CONFIG["filters"].copy()
        self.save()
