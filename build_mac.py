import os
import sys
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def build_mac():
    """
    macOS 平台專屬打包腳本：
    使用 PyInstaller 將應用程式封裝為標準的 macOS .app Bundle (含獨立資源目錄及權限配置)。
    """
    print("=" * 60)
    print("[Build Mac] 開始使用 PyInstaller 打包 macOS 桌面助手 (.app Bundle)...")
    print("=" * 60)

    # 1. 圖示設定
    icon_icns = os.path.join(BASE_DIR, "assets", "app_icon.icns")
    icon_png = os.path.join(BASE_DIR, "assets", "app_icon.png")
    icon_arg = []
    if os.path.exists(icon_icns):
        icon_arg = [f"--icon={icon_icns}"]
    elif os.path.exists(icon_png):
        icon_arg = [f"--icon={icon_png}"]

    # 2. 目錄設定
    dist_dir = os.path.join(BASE_DIR, "dist")
    build_dir = os.path.join(BASE_DIR, "build")
    app_name = "DesktopAssistant"

    # 3. 執行 PyInstaller
    import PyInstaller.__main__
    sep = ":" if sys.platform != "win32" else ";"
    args = [
        os.path.join(BASE_DIR, "main.py"),
        f"--name={app_name}",
        "--windowed",
        "--noconsole",
        "--clean",
        "--noconfirm",
        f"--distpath={dist_dir}",
        f"--workpath={build_dir}",
        f"--add-data={os.path.join(BASE_DIR, 'assets')}{sep}assets",
        f"--add-data={os.path.join(BASE_DIR, 'config')}{sep}config",
    ] + icon_arg

    print(f"[Build Mac] 正在封裝 .app 至: {os.path.join(dist_dir, f'{app_name}.app')}")
    PyInstaller.__main__.run(args)

    # 4. 確保 Contents/Resources 內亦有一份 assets 與 config
    app_bundle = os.path.join(dist_dir, f"{app_name}.app")
    resources_dir = os.path.join(app_bundle, "Contents", "Resources")
    if os.path.exists(resources_dir):
        target_assets = os.path.join(resources_dir, "assets")
        target_config = os.path.join(resources_dir, "config")
        if not os.path.exists(target_assets):
            shutil.copytree(os.path.join(BASE_DIR, "assets"), target_assets)
        if not os.path.exists(target_config):
            shutil.copytree(os.path.join(BASE_DIR, "config"), target_config)

    print("=" * 60)
    print("[Build Mac] macOS 打包完成！")
    print(f"[Build Mac] 應用程式路徑: {app_bundle}")
    print("=" * 60)

if __name__ == "__main__":
    build_mac()
