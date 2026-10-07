import os
import sys
import shutil
import subprocess
from typing import Optional, Union, List
from PyQt6.QtCore import Qt

from src.platform.base import PlatformAdapter

class MacOSPlatform(PlatformAdapter):
    """
    macOS 專屬實作層：
    封裝 ~/Library/LaunchAgents/ plist 開機啟動、open 指令喚起應用程式與腳本、
    ~/Library/Application Support/ 使用者設定檔存放目錄、afplay 原生音效後備、
    以及 macOS 鍵盤修飾鍵 (⌘/Ctrl) 判定。
    """
    PLIST_LABEL = "com.desktopassistant.pet"

    def __init__(self):
        super().__init__()
        self._launch_agents_dir = os.path.expanduser("~/Library/LaunchAgents")
        self._plist_path = os.path.join(self._launch_agents_dir, f"{self.PLIST_LABEL}.plist")

    def is_autostart_registered(self) -> bool:
        return os.path.exists(self._plist_path)

    def register_autostart(self, base_dir: str) -> bool:
        """在 ~/Library/LaunchAgents/ 寫入 launchd plist 設定檔"""
        try:
            os.makedirs(self._launch_agents_dir, exist_ok=True)
            args = self._get_launch_args(base_dir)

            args_xml = "\n".join([f"        <string>{arg}</string>" for arg in args])
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{self.PLIST_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
{args_xml}
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>ProcessType</key>
    <string>Interactive</string>
</dict>
</plist>
"""
            with open(self._plist_path, "w", encoding="utf-8") as f:
                f.write(plist_content)

            # 嘗試通知 launchctl 載入
            try:
                subprocess.run(["launchctl", "unload", self._plist_path], capture_output=True)
                subprocess.run(["launchctl", "load", self._plist_path], capture_output=True)
            except Exception:
                pass

            print(f"[MacOSPlatform] 已建立開機啟動設定: {self._plist_path}")
            return True
        except Exception as e:
            print(f"[MacOSPlatform] 註冊開機啟動失敗: {e}")
            return False

    def unregister_autostart(self) -> bool:
        try:
            if os.path.exists(self._plist_path):
                try:
                    subprocess.run(["launchctl", "unload", self._plist_path], capture_output=True)
                except Exception:
                    pass
                os.remove(self._plist_path)
            print("[MacOSPlatform] 已註銷開機啟動")
            return True
        except Exception as e:
            print(f"[MacOSPlatform] 註銷開機啟動失敗: {e}")
            return False

    def _get_launch_args(self, base_dir: str) -> List[str]:
        if getattr(sys, 'frozen', False):
            # 若打包為 .app，執行主執行檔
            return [sys.executable]
        main_py = os.path.join(os.path.abspath(base_dir), "main.py")
        return [sys.executable, main_py]

    def launch(self, target: Union[str, List, dict], cwd: Optional[str] = None) -> bool:
        if not target:
            return False

        if isinstance(target, (list, tuple)):
            all_ok = True
            for item in target:
                if isinstance(item, dict):
                    if not self.launch(item.get("target"), item.get("cwd")):
                        all_ok = False
                elif isinstance(item, str):
                    if not self.launch(item):
                        all_ok = False
            return all_ok

        path = os.path.expanduser(target)
        working_dir = cwd if cwd and os.path.isdir(cwd) else None

        print(f"[MacOSPlatform] 啟動目標: {path} (工作目錄: {working_dir})")
        try:
            # 若為 shell 腳本，確保具有可執行權限
            if path.endswith((".sh", ".command")) and os.path.isfile(path):
                try:
                    current_mode = os.stat(path).st_mode
                    os.chmod(path, current_mode | 0o111)
                except Exception as e:
                    print(f"[MacOSPlatform] chmod +x warning: {e}")

                # 使用 open 指令在 Terminal 中執行，或直接執行
                subprocess.Popen(["open", path], cwd=working_dir)
                return True

            # .app 應用程式包、檔案、資料夾或 URL：使用 macOS 原生 open 指令開啟
            cmd = ["open"]
            if os.path.isdir(path) and path.endswith(".app"):
                cmd.extend(["-a", path])
            else:
                cmd.append(path)

            subprocess.Popen(cmd, cwd=working_dir)
            return True
        except Exception as e:
            print(f"[MacOSPlatform] 呼叫 open 失敗 ({e})，嘗試使用 subprocess 直接呼叫...")
            try:
                subprocess.Popen([path], cwd=working_dir, shell=True)
                return True
            except Exception as e2:
                print(f"[MacOSPlatform] subprocess 啟動亦失敗: {e2}")
                return False

    def force_topmost(self, widget) -> None:
        if widget is None or not widget.isVisible():
            return
        widget.raise_()

    def setup_app_window(self, widget) -> None:
        """
        在 macOS 上配置視窗屬性。
        優先嘗試安全載入 PyObjC (若使用者有安裝)，否則退回使用純 Qt 機制，避免 ctypes 在不同 CPU 架構下發生 Segmentation Fault。
        """
        try:
            import objc
            from ctypes import c_void_p
            ns_view_ptr = int(widget.winId())
            if ns_view_ptr:
                ns_view = objc.objc_object(c_void_p=c_void_p(ns_view_ptr))
                ns_window = ns_view.window()
                if ns_window:
                    ns_window.setHasShadow_(False)
                    ns_window.invalidateShadow()
                    ns_window.setCollectionBehavior_((1 << 0) | (1 << 4))
                    ns_window.setLevel_(3)
                    print("[MacOSPlatform] 已透過 PyObjC 關閉 macOS 系統原生視窗陰影 (setHasShadow: NO)")
        except Exception:
            pass

    def get_config_dir(self, base_dir: str) -> str:
        """
        在 macOS 上將設定檔儲存於 ~/Library/Application Support/DesktopAssistant/config/。
        若是初次啟動，自動將專案內預設的 config/ 檔案複製過去。
        """
        user_config_dir = os.path.expanduser("~/Library/Application Support/DesktopAssistant/config")
        os.makedirs(user_config_dir, exist_ok=True)

        bundle_config_dir = os.path.join(base_dir, "config")
        if os.path.exists(bundle_config_dir):
            for filename in ["settings.json", "actions.json"]:
                dest_file = os.path.join(user_config_dir, filename)
                src_file = os.path.join(bundle_config_dir, filename)
                if not os.path.exists(dest_file) and os.path.exists(src_file):
                    try:
                        shutil.copy2(src_file, dest_file)
                        print(f"[MacOSPlatform] 已初始化設定檔至: {dest_file}")
                    except Exception as e:
                        print(f"[MacOSPlatform] 複製預設設定檔失敗: {e}")

        return user_config_dir

    def get_file_dialog_filter(self) -> str:
        return "所有支援格式 (*.app *.sh *.command);;應用程式 (*.app);;Shell 腳本 (*.sh *.command);;所有檔案 (*.*)"

    def get_zoom_modifier_name(self) -> str:
        return "⌘ (Command)"

    def is_zoom_modifier(self, modifiers: Qt.KeyboardModifier) -> bool:
        return bool(modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.MetaModifier))

    def _fallback_play_sound(self, sound_path: str) -> bool:
        try:
            subprocess.Popen(["afplay", sound_path])
            return True
        except Exception as e:
            print(f"[MacOSPlatform] afplay 播放失敗: {e}")
            return False

    def play_beep(self) -> None:
        try:
            ping_sound = "/System/Library/Sounds/Ping.aiff"
            if os.path.exists(ping_sound):
                subprocess.Popen(["afplay", ping_sound])
                return
        except Exception:
            pass
        super().play_beep()
