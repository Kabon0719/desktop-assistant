import os
from typing import Optional
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from src.platform import play_sound, play_beep

class PomodoroTimer(QObject):
    started = pyqtSignal(int)          # duration in minutes
    tick = pyqtSignal(int)             # remaining seconds
    finished = pyqtSignal()            # alarm triggered
    cancelled = pyqtSignal()

    def __init__(self, base_dir: str):
        super().__init__()
        self.base_dir = base_dir
        self.default_sound = os.path.join(base_dir, "assets", "audio", "bell.wav")

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._on_tick)

        self.remaining_seconds = 0
        self.total_seconds = 0
        self.current_sound_file = ""

    def start(self, duration_minutes: int = 20, sound_file: str = ""):
        """
        每次呼叫會清除舊的計時器並重新倒數
        """
        self.stop(silent=True)

        self.total_seconds = max(1, duration_minutes * 60)
        self.remaining_seconds = self.total_seconds
        self.current_sound_file = sound_file

        self.timer.start()
        self.started.emit(duration_minutes)
        self.tick.emit(self.remaining_seconds)
        print(f"[Pomodoro] 計時器已啟動: {duration_minutes} 分鐘")

    def stop(self, silent: bool = False):
        if self.timer.isActive():
            self.timer.stop()
            self.remaining_seconds = 0
            if not silent:
                self.cancelled.emit()
            print("[Pomodoro] 計時器已重設/停止")

    def is_running(self) -> bool:
        return self.timer.isActive()

    def get_remaining_seconds(self) -> int:
        return self.remaining_seconds

    def get_remaining_formatted(self) -> str:
        mins = self.remaining_seconds // 60
        secs = self.remaining_seconds % 60
        return f"{mins:02d}:{secs:02d}"

    def _on_tick(self):
        self.remaining_seconds -= 1
        if self.remaining_seconds <= 0:
            self.timer.stop()
            self.remaining_seconds = 0
            self.finished.emit()
            self.play_alarm()
        else:
            self.tick.emit(self.remaining_seconds)

    def play_alarm(self, sound_path: Optional[str] = None):
        target = sound_path if sound_path else self.current_sound_file
        if not target or not os.path.exists(target):
            target = self.default_sound

        if target and os.path.exists(target):
            success = play_sound(target, parent=self)
            if not success:
                print("[Pomodoro] 播放音效失敗，改用系統提示音")
                play_beep()
        else:
            play_beep()
