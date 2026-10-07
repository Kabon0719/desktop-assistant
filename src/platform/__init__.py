import sys
from typing import Optional, Union, List
from PyQt6.QtCore import Qt
from src.platform.base import PlatformAdapter

if sys.platform == "darwin":
    from src.platform.macos import MacOSPlatform
    platform_adapter: PlatformAdapter = MacOSPlatform()
elif sys.platform == "win32":
    from src.platform.windows import WindowsPlatform
    platform_adapter: PlatformAdapter = WindowsPlatform()
else:
    # Linux 或其他 Unix 系統，使用通用基礎轉接器
    from src.platform.windows import WindowsPlatform
    platform_adapter: PlatformAdapter = WindowsPlatform()

# 匯出模組級便利呼叫函式
def is_autostart_registered() -> bool:
    return platform_adapter.is_autostart_registered()

def register_autostart(base_dir: str) -> bool:
    return platform_adapter.register_autostart(base_dir)

def unregister_autostart() -> bool:
    return platform_adapter.unregister_autostart()

def launch(target: Union[str, List, dict], cwd: Optional[str] = None) -> bool:
    return platform_adapter.launch(target, cwd)

def force_topmost(widget) -> None:
    platform_adapter.force_topmost(widget)

def play_sound(sound_path: str, parent=None) -> bool:
    return platform_adapter.play_sound(sound_path, parent)

def play_beep() -> None:
    platform_adapter.play_beep()

def get_config_dir(base_dir: str) -> str:
    return platform_adapter.get_config_dir(base_dir)

def get_file_dialog_filter() -> str:
    return platform_adapter.get_file_dialog_filter()

def get_zoom_modifier_name() -> str:
    return platform_adapter.get_zoom_modifier_name()

def is_zoom_modifier(modifiers: Qt.KeyboardModifier) -> bool:
    return platform_adapter.is_zoom_modifier(modifiers)

def setup_app_window(widget) -> None:
    platform_adapter.setup_app_window(widget)

__all__ = [
    "platform_adapter",
    "is_autostart_registered",
    "register_autostart",
    "unregister_autostart",
    "launch",
    "force_topmost",
    "play_sound",
    "play_beep",
    "get_config_dir",
    "get_file_dialog_filter",
    "get_zoom_modifier_name",
    "is_zoom_modifier",
    "setup_app_window",
]
