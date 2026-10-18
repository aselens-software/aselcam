import sys
import os
import signal
import ctypes
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from aselcam.gui.main_window import MainWindow

def set_linux_process_name(name: str):
    """Sets the process name across operating systems (Linux kernel comm, Windows AppUserModelID)."""
    if sys.platform.startswith("linux"):
        try:
            # 15 = PR_SET_NAME
            libc = ctypes.CDLL(None)
            libc.prctl(15, name.encode("utf-8"), 0, 0, 0)
        except Exception:
            pass
    elif sys.platform.startswith("win32"):
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(f"AselCam.{name}")
        except Exception:
            pass

    try:
        sys.argv[0] = name
    except Exception:
        pass

def main():
    # Set process name immediately
    set_linux_process_name("AselCam")

    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Enable High DPI scaling
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("AselCam")
    app.setApplicationDisplayName("AselCam")
    app.setDesktopFileName("aselcam.desktop")
    app.setOrganizationName("Asel")
    app.setQuitOnLastWindowClosed(False)

    app_icon = QIcon()
    assets_dir = os.path.join(os.path.dirname(__file__), "assets")
    for sz in (16, 24, 32, 48, 64, 128, 256, 512):
        fn = os.path.join(assets_dir, f"aselcam_icon_{sz}.png")
        if os.path.exists(fn):
            app_icon.addFile(fn)
    ico_fn = os.path.join(assets_dir, "aselcam_icon.ico")
    if os.path.exists(ico_fn):
        app_icon.addFile(ico_fn)
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)

    # Ensure C-locale numeric conventions for neural network inference (ONNX) and OpenMP
    try:
        import locale
        locale.setlocale(locale.LC_NUMERIC, "C")
    except Exception:
        pass

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
