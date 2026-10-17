import sys
import os
import signal
import ctypes
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

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
