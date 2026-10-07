import os
import sys
import shutil

# 確保在 Windows 控制台輸出時不因編碼拋錯
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def build():
    print("=" * 60)
    print("[Build] 開始使用 PyInstaller 打包桌面助手 (Windows 免安裝/便攜版)...")
    print("=" * 60)

    # 1. 確保圖示檔案存在
    icon_path = os.path.join(BASE_DIR, "assets", "app_icon.ico")
    if not os.path.exists(icon_path):
        print("[Build] 正在生成 app_icon.ico...")
        from PIL import Image
        frame1 = os.path.join(BASE_DIR, "assets", "animations", "OZ_read", "frame_00001.png")
        if os.path.exists(frame1):
            img = Image.open(frame1)
            img.save(icon_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
            print("[Build] 已生成 app_icon.ico")

    # 2. 執行 PyInstaller
    dist_dir = os.path.join(BASE_DIR, "dist")
    build_dir = os.path.join(BASE_DIR, "build")
    output_app_dir = os.path.join(dist_dir, "桌面助手")

    import PyInstaller.__main__

    args = [
        os.path.join(BASE_DIR, "main.py"),
        "--name=桌面助手",
        "--onedir",
        "--windowed",
        "--noconsole",
        f"--icon={icon_path}",
        "--clean",
        "--noconfirm",
        f"--distpath={dist_dir}",
        f"--workpath={build_dir}",
    ]

    print(f"[Build] 正在執行 PyInstaller，打包核心程式庫至: {output_app_dir}")
    PyInstaller.__main__.run(args)

    # 3. 複製 assets 與 config 至輸出資料夾
    print("[Build] 正在同步素材資源 (assets) 與設定檔 (config)...")
    target_assets = os.path.join(output_app_dir, "assets")
    target_config = os.path.join(output_app_dir, "config")

    if os.path.exists(target_assets):
        shutil.rmtree(target_assets)
    shutil.copytree(os.path.join(BASE_DIR, "assets"), target_assets)

    if os.path.exists(target_config):
        shutil.rmtree(target_config)
    shutil.copytree(os.path.join(BASE_DIR, "config"), target_config)

    print("=" * 60)
    print("[Build] 打包完成！")
    print(f"[Build] 輸出資料夾路徑: {output_app_dir}")
    print(f"[Build] 執行檔位置: {os.path.join(output_app_dir, '桌面助手.exe')}")
    print("=" * 60)

if __name__ == "__main__":
    build()
