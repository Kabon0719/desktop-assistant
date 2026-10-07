from src.platform import (
    is_autostart_registered,
    register_autostart,
    unregister_autostart,
)

class AutoStartManager:
    """
    開機啟動管理器，委派至作業系統專屬之平台層實作。
    Windows: 寫入 HKCU Run 登錄檔。
    macOS: 寫入 ~/Library/LaunchAgents/ launchd plist。
    """
    @classmethod
    def is_registered(cls) -> bool:
        return is_autostart_registered()

    @classmethod
    def register(cls, base_dir: str) -> bool:
        return register_autostart(base_dir)

    @classmethod
    def unregister(cls) -> bool:
        return unregister_autostart()
