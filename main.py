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

    # 初次啟動語言選擇
    from src.utils.config_loader import ConfigLoader
    config_loader = ConfigLoader(BASE_DIR)
    settings = config_loader.load_settings()
    
    if not settings.get("language"):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
        dialog = QDialog()
        dialog.setWindowTitle("Language Selection / 語言選擇")
        dialog.setFixedWidth(340)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        label = QLabel("Please select your preferred language:\n請選擇您偏好的介面語言：", dialog)
        label.setStyleSheet("font-size: 14px; font-weight: bold; line-height: 1.4;")
        layout.addWidget(label)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        btn_zh = QPushButton("繁體中文", dialog)
        btn_zh.setFixedHeight(36)
        btn_zh.setStyleSheet("font-size: 13px; font-weight: bold; padding: 6px 12px;")
        
        btn_en = QPushButton("English", dialog)
        btn_en.setFixedHeight(36)
        btn_en.setStyleSheet("font-size: 13px; font-weight: bold; padding: 6px 12px;")
        
        btn_layout.addWidget(btn_zh)
        btn_layout.addWidget(btn_en)
        layout.addLayout(btn_layout)
        
        selected_lang = ["zh"]
        def on_zh():
            selected_lang[0] = "zh"
            dialog.accept()
        def on_en():
            selected_lang[0] = "en"
            dialog.accept()
            
        btn_zh.clicked.connect(on_zh)
        btn_en.clicked.connect(on_en)
        
        # macOS 確保視窗跳到最前景
        if sys.platform == "darwin":
            try:
                import objc
                NSApp = objc.lookUpClass('NSApplication').sharedApplication()
                NSApp.activateIgnoringOtherApps_(True)
            except Exception:
                pass
            dialog.raise_()
            dialog.activateWindow()
            
        dialog.exec()
        settings["language"] = selected_lang[0]
        config_loader.save_settings(settings)

    # macOS 特有：進入主程式後將 App 設定為「附屬應用程式」(Accessory/LSUIElement)，確保後續懸浮絕不搶焦點
    if sys.platform == "darwin":
        try:
            import objc
            NSApp = objc.lookUpClass('NSApplication').sharedApplication()
            # 1 == NSApplicationActivationPolicyAccessory
            NSApp.setActivationPolicy_(1)
        except Exception as e:
            print(f"[Mac] Set activation policy failed: {e}")

    window = PetWindow(base_dir=BASE_DIR)
    window.start()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
