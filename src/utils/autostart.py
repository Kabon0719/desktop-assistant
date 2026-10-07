import os
import sys
import winreg

class AutoStartManager:
    REG_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
    APP_NAME = "DesktopAssistant"
    LEGACY_APP_NAME = "MonkDesktopAssistant"

    @classmethod
    def is_registered(cls) -> bool:
        """檢查目前是否已註冊為開機啟動"""
        for name in (cls.APP_NAME, cls.LEGACY_APP_NAME):
            try:
                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    cls.REG_KEY_PATH,
                    0,
                    winreg.KEY_READ
                ) as key:
                    val, _ = winreg.QueryValueEx(key, name)
                    if bool(val):
                        return True
            except (FileNotFoundError, OSError):
                pass
        return False

    @classmethod
    def register(cls, base_dir: str) -> bool:
        """註冊開機自動啟動 (寫入 HKCU Run 登錄檔)"""
        try:
            cmd = cls.get_launch_command(base_dir)
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                cls.REG_KEY_PATH,
                0,
                winreg.KEY_SET_VALUE
            ) as key:
                winreg.SetValueEx(key, cls.APP_NAME, 0, winreg.REG_SZ, cmd)
                # 清理舊的鍵名（若存在）
                try:
                    winreg.DeleteValue(key, cls.LEGACY_APP_NAME)
                except FileNotFoundError:
                    pass
            print(f"[AutoStart] 已註冊開機啟動: {cmd}")
            return True
        except Exception as e:
            print(f"[AutoStart] 註冊失敗: {e}")
            return False

    @classmethod
    def unregister(cls) -> bool:
        """註銷開機自動啟動 (自 HKCU Run 登錄檔中移除)"""
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                cls.REG_KEY_PATH,
                0,
                winreg.KEY_SET_VALUE
            ) as key:
                for name in (cls.APP_NAME, cls.LEGACY_APP_NAME):
                    try:
                        winreg.DeleteValue(key, name)
                    except FileNotFoundError:
                        pass
            print("[AutoStart] 已註銷開機啟動")
            return True
        except Exception as e:
            print(f"[AutoStart] 註銷失敗: {e}")
            return False

    @classmethod
    def get_launch_command(cls, base_dir: str) -> str:
        """取得靜默啟動的命令 (打包成 exe 則直接指向 exe，否則優先使用 pythonw.exe main.py)"""
        if getattr(sys, 'frozen', False):
            return f'"{sys.executable}"'
        main_py = os.path.join(base_dir, "main.py")
        python_dir = os.path.dirname(sys.executable)
        pythonw_path = os.path.join(python_dir, "pythonw.exe")

        if not os.path.exists(pythonw_path):
            pythonw_path = sys.executable

        return f'"{pythonw_path}" "{main_py}"'
