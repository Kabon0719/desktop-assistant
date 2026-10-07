from typing import Optional, Union, List
from src.platform import launch as platform_launch

class Launcher:
    @staticmethod
    def launch(target: Union[str, List, dict], cwd: Optional[str] = None) -> bool:
        """
        跨平台啟動應用程式/腳本/捷徑，並委派至作業系統專屬之平台轉接層執行。
        """
        return platform_launch(target, cwd)
