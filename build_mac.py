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

    # 5. 清理 PyInstaller 留下來的多餘散裝目錄 (只保留純淨的 .app)
    unneeded_dir = os.path.join(dist_dir, app_name)
    if os.path.isdir(unneeded_dir):
        try:
            shutil.rmtree(unneeded_dir)
            print(f"[Build Mac] 已自動清理多餘的散裝中間目錄: {unneeded_dir}")
        except Exception as e:
            print(f"[Build Mac] 清理散裝目錄提示: {e}")

    # 6. 自動清除隔離屬性並封裝為分享用 ZIP (透過 macOS 原生 ditto 指令保證權限與符號連結完整)
    zip_output = os.path.join(dist_dir, f"{app_name}_macOS.zip")
    if sys.platform == "darwin":
        import subprocess
        try:
            subprocess.run(["xattr", "-cr", app_bundle], check=False)
            subprocess.run(["ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", app_bundle, zip_output], check=False)
            if os.path.exists(zip_output):
                print(f"[Build Mac] 已自動生成可直接分享的 ZIP 壓縮檔: {zip_output}")
        except Exception as e:
            print(f"[Build Mac] 生成 ZIP 提示: {e}")

    print("=" * 60)
    print("[Build Mac] macOS 打包完成！")
    print(f"[Build Mac] 應用程式路徑: {app_bundle}")
    if os.path.exists(zip_output):
        print(f"[Build Mac] 分享用壓縮檔: {zip_output}")
    print("=" * 60)

if __name__ == "__main__":
    build_mac()
