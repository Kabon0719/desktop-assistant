import os
import sys
from abc import ABC, abstractmethod
from typing import Optional, Union, List
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtMultimedia import QSoundEffect

class PlatformAdapter(ABC):
    """
    跨平台介面基底類別 (抽象介面)。
    定義各作業系統專屬之核心行為：開機啟動、程式喚起、音效播放、視窗置頂、設定檔存放路徑等。
    """
    def __init__(self):
        self._active_sound_effects: List[QSoundEffect] = []

    @abstractmethod
    def is_autostart_registered(self) -> bool:
        """檢查目前是否已註冊為開機自動啟動"""
        pass

    @abstractmethod
    def register_autostart(self, base_dir: str) -> bool:
        """註冊開機自動啟動"""
        pass

    @abstractmethod
    def unregister_autostart(self) -> bool:
        """註銷開機自動啟動"""
        pass

    @abstractmethod
    def launch(self, target: Union[str, List, dict], cwd: Optional[str] = None) -> bool:
        """啟動指定的執行檔、腳本或捷徑應用程式"""
        pass

    @abstractmethod
    def force_topmost(self, widget) -> None:
        """將指定視窗維持在桌面最頂層"""
        pass

    @abstractmethod
    def get_config_dir(self, base_dir: str) -> str:
        """取得使用者設定檔目錄 (支援讀寫權限)"""
        pass

    @abstractmethod
    def get_file_dialog_filter(self) -> str:
        """取得開啟檔案對話框的副檔名篩選字串"""
        pass

    @abstractmethod
    def get_zoom_modifier_name(self) -> str:
        """取得縮放快捷鍵名稱 (如 'Ctrl' 或 '⌘')"""
        pass

    @abstractmethod
    def is_zoom_modifier(self, modifiers: Qt.KeyboardModifier) -> bool:
        """判斷按鍵修飾鍵是否為縮放組合鍵"""
        pass

    def setup_app_window(self, widget) -> None:
        """為主要視窗進行作業系統特定的視窗特性配置 (如 macOS Spaces 行為)"""
        pass

    def play_sound(self, sound_path: str, parent=None) -> bool:
        """
        跨平台播放音效。
        預設使用 PyQt6 內建之 QSoundEffect 進行低延遲非同步播放。
        """
        if not sound_path or not os.path.exists(sound_path):
            return False

        try:
            abs_path = os.path.abspath(sound_path)
            effect = QSoundEffect(parent)
            effect.setSource(QUrl.fromLocalFile(abs_path))
            effect.setVolume(1.0)
            
            # 保存參照防止 Python 垃圾回收機制過早釋放
            self._active_sound_effects.append(effect)
            
            def _cleanup():
                if effect in self._active_sound_effects:
                    self._active_sound_effects.remove(effect)

            effect.playingChanged.connect(lambda: _cleanup() if not effect.isPlaying() else None)
            effect.play()
            return True
        except Exception as e:
            print(f"[Platform] QSoundEffect 播放失敗 ({e})，嘗試原生後備播放器...")
            return self._fallback_play_sound(sound_path)

    def _fallback_play_sound(self, sound_path: str) -> bool:
        """由各子類別實作的後備音效播放邏輯"""
        return False

    def play_beep(self) -> None:
        """播放系統提示音 (Beep)"""
        from PyQt6.QtWidgets import QApplication
        QApplication.beep()
