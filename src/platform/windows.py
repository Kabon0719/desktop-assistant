import os
import sys
import subprocess
from typing import Optional, Union, List
from PyQt6.QtCore import Qt

from src.platform.base import PlatformAdapter

class WindowsPlatform(PlatformAdapter):
    """
    Windows 專屬實作層：
    封裝 Windows 登錄檔 (HKCU Run)、Win32 SetWindowPos 置頂、os.startfile 與捷徑解析。
    """
    REG_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
    APP_NAME = "DesktopAssistant"
    LEGACY_APP_NAME = "MonkDesktopAssistant"

    def __init__(self):
        super().__init__()
        self._init_win32()

    def _init_win32(self):
        self._user32 = None
        self._HWND_TOPMOST = None
        self._FLAGS = None
        try:
            import ctypes
            from ctypes import wintypes
            self._user32 = ctypes.windll.user32
            self._user32.SetWindowPos.argtypes = [
                wintypes.HWND, wintypes.HWND,
                ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                ctypes.c_uint
            ]
            self._user32.SetWindowPos.restype = wintypes.BOOL
            self._HWND_TOPMOST = wintypes.HWND(-1)
            SWP_NOSIZE = 0x0001
            SWP_NOMOVE = 0x0002
            SWP_NOACTIVATE = 0x0010
            SWP_NOOWNERZORDER = 0x0200
            self._FLAGS = SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE | SWP_NOOWNERZORDER
        except Exception as e:
            print(f"[WindowsPlatform] Win32 API 初始化失敗: {e}")

    def is_autostart_registered(self) -> bool:
        try:
            import winreg
            for name in (self.APP_NAME, self.LEGACY_APP_NAME):
                try:
                    with winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER,
                        self.REG_KEY_PATH,
                        0,
                        winreg.KEY_READ
                    ) as key:
                        val, _ = winreg.QueryValueEx(key, name)
                        if bool(val):
                            return True
                except (FileNotFoundError, OSError):
                    pass
        except Exception as e:
            print(f"[WindowsPlatform] 檢查開機啟動失敗: {e}")
        return False

    def register_autostart(self, base_dir: str) -> bool:
        try:
            import winreg
            cmd = self._get_launch_command(base_dir)
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.REG_KEY_PATH,
                0,
                winreg.KEY_SET_VALUE
            ) as key:
                winreg.SetValueEx(key, self.APP_NAME, 0, winreg.REG_SZ, cmd)
                try:
                    winreg.DeleteValue(key, self.LEGACY_APP_NAME)
                except FileNotFoundError:
                    pass
            print(f"[WindowsPlatform] 已註冊開機啟動: {cmd}")
            return True
        except Exception as e:
            print(f"[WindowsPlatform] 註冊開機啟動失敗: {e}")
            return False

    def unregister_autostart(self) -> bool:
        try:
            import winreg
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                self.REG_KEY_PATH,
                0,
                winreg.KEY_SET_VALUE
            ) as key:
                for name in (self.APP_NAME, self.LEGACY_APP_NAME):
                    try:
                        winreg.DeleteValue(key, name)
                    except FileNotFoundError:
                        pass
            print("[WindowsPlatform] 已註銷開機啟動")
            return True
        except Exception as e:
            print(f"[WindowsPlatform] 註銷開機啟動失敗: {e}")
            return False

    def _get_launch_command(self, base_dir: str) -> str:
        if getattr(sys, 'frozen', False):
            return f'"{sys.executable}"'
        main_py = os.path.join(base_dir, "main.py")
        python_dir = os.path.dirname(sys.executable)
        pythonw_path = os.path.join(python_dir, "pythonw.exe")
        if not os.path.exists(pythonw_path):
            pythonw_path = sys.executable
        return f'"{pythonw_path}" "{main_py}"'

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

        working_dir = cwd
        if not working_dir:
            if os.path.exists(target):
                abs_path = os.path.abspath(target)
                if os.path.isfile(abs_path):
                    if abs_path.lower().endswith(".lnk"):
                        try:
                            import win32com.client
                            shell = win32com.client.Dispatch("WScript.Shell")
                            shortcut = shell.CreateShortCut(abs_path)
                            if shortcut.WorkingDirectory and os.path.isdir(shortcut.WorkingDirectory):
                                working_dir = shortcut.WorkingDirectory
                            elif shortcut.TargetPath and os.path.exists(shortcut.TargetPath):
                                working_dir = os.path.dirname(os.path.abspath(shortcut.TargetPath))
                        except Exception as e:
                            print(f"[WindowsPlatform] 解析 .lnk 捷徑失敗: {e}")
                            working_dir = os.path.dirname(abs_path)
                    else:
                        working_dir = os.path.dirname(abs_path)
                elif os.path.isdir(abs_path):
                    working_dir = abs_path

        if working_dir and not os.path.isdir(working_dir):
            working_dir = None

        print(f"[WindowsPlatform] 啟動目標: {target} (工作目錄: {working_dir})")
        try:
            if working_dir:
                os.startfile(target, cwd=working_dir)
            else:
                os.startfile(target)
            return True
        except Exception as e:
            print(f"[WindowsPlatform] os.startfile 啟動失敗 ({e})，嘗試使用 subprocess...")
            try:
                subprocess.Popen(target, cwd=working_dir, shell=True)
                return True
            except Exception as e2:
                print(f"[WindowsPlatform] subprocess 啟動亦失敗: {e2}")
                return False

    def force_topmost(self, widget) -> None:
        if widget is None or not widget.isVisible() or not self._user32:
            return
        try:
            hwnd = int(widget.winId())
            if hwnd:
                self._user32.SetWindowPos(hwnd, self._HWND_TOPMOST, 0, 0, 0, 0, self._FLAGS)
        except Exception as e:
            print(f"[WindowsPlatform] SetWindowPos 失敗: {e}")

    def get_config_dir(self, base_dir: str) -> str:
        config_dir = os.path.join(base_dir, "config")
        os.makedirs(config_dir, exist_ok=True)
        return config_dir

    def get_file_dialog_filter(self) -> str:
        return "所有支援格式 (*.exe *.bat *.cmd *.lnk *.url);;可執行檔 (*.exe);;批次檔 (*.bat *.cmd);;捷徑檔 (*.lnk);;所有檔案 (*.*)"

    def get_zoom_modifier_name(self) -> str:
        return "Ctrl"

    def is_zoom_modifier(self, modifiers: Qt.KeyboardModifier) -> bool:
        return bool(modifiers & Qt.KeyboardModifier.ControlModifier)

    def _fallback_play_sound(self, sound_path: str) -> bool:
        try:
            import winsound
            if sound_path.lower().endswith(".wav"):
                winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                return True
        except Exception as e:
            print(f"[WindowsPlatform] winsound 播放失敗: {e}")
        return False

    def play_beep(self) -> None:
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception:
            super().play_beep()
