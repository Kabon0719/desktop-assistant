import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

def get_base_dir() -> str:
    """取得應用程式根目錄 (跨平台相容開發環境、Windows 打包版及 macOS .app Bundle)"""
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        # 1. macOS .app (Contents/MacOS)：資源位於 Contents/Resources
        if sys.platform == "darwin" and "Contents/MacOS" in exe_dir:
            resources_dir = os.path.abspath(os.path.join(exe_dir, "..", "Resources"))
            if os.path.exists(os.path.join(resources_dir, "assets")):
                return resources_dir
            return exe_dir

        # 2. Windows / Linux onedir 打包：assets 與 config 位於 exe 旁邊
        if os.path.exists(os.path.join(exe_dir, "assets")):
            return exe_dir

        # 3. 若為 onefile 打包，PyInstaller 會解壓至 sys._MEIPASS
        if hasattr(sys, '_MEIPASS') and os.path.exists(os.path.join(sys._MEIPASS, "assets")):
            return sys._MEIPASS

        return exe_dir
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()
os.chdir(BASE_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.ui.pet_window import PetWindow

def main():
    # High-DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # 跨平台載入應用程式圖示 (macOS/Linux 優先 PNG，Windows 支援 ICO)
    for icon_name in ("app_icon.png", "app_icon.ico"):
        icon_path = os.path.join(BASE_DIR, "assets", icon_name)
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
            break

    window = PetWindow(base_dir=BASE_DIR)
    window.start()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
