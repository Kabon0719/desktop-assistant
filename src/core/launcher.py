import os
import subprocess
import sys
from typing import Optional

class Launcher:
    @staticmethod
    def launch(target, cwd: Optional[str] = None) -> bool:
        """
        啟動指定的執行檔/指令/捷徑，並確保工作目錄 (CWD) 設定在該應用程式的目錄下，
        徹底防止相對路徑找不到資源或設定檔的問題。
        支援傳入單一檔案路徑或多個檔案路徑清單 (同步並行啟動)。
        """
        if not target:
            return False

        if isinstance(target, (list, tuple)):
            all_ok = True
            for item in target:
                if isinstance(item, dict):
                    if not Launcher.launch(item.get("target"), item.get("cwd")):
                        all_ok = False
                elif isinstance(item, str):
                    if not Launcher.launch(item):
                        all_ok = False
            return all_ok

        working_dir = cwd
        if not working_dir:
            if os.path.exists(target):
                abs_path = os.path.abspath(target)
                if os.path.isfile(abs_path):
                    # 若為 Windows 捷徑 (.lnk)，優先解析捷徑設定的工作目錄或指向目標目錄
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
                            print(f"[Launcher] Failed to resolve .lnk target: {e}")
                            working_dir = os.path.dirname(abs_path)
                    else:
                        working_dir = os.path.dirname(abs_path)
                elif os.path.isdir(abs_path):
                    working_dir = abs_path

        # 確保 working_dir 為有效路徑
        if working_dir and not os.path.isdir(working_dir):
            working_dir = None

        print(f"[Launcher] 啟動目標: {target} (工作目錄 CWD: {working_dir})")

        try:
            if sys.platform == "win32":
                if working_dir:
                    os.startfile(target, cwd=working_dir)
                else:
                    os.startfile(target)
            else:
                subprocess.Popen([target], cwd=working_dir, shell=True)
            return True
        except Exception as e:
            print(f"[Launcher] os.startfile 啟動失敗 ({e})，嘗試使用 subprocess...")
            try:
                subprocess.Popen(target, cwd=working_dir, shell=True)
                return True
            except Exception as e2:
                print(f"[Launcher] subprocess 啟動亦失敗: {e2}")
                return False
