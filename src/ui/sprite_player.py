import os
from typing import Callable, Optional, Dict, List
from PyQt6.QtCore import QTimer, pyqtSignal, QObject, Qt
from PyQt6.QtGui import QPixmap

class SpritePlayer(QObject):
    frame_changed = pyqtSignal(QPixmap)
    finished_once = pyqtSignal()

    def __init__(self, assets_dir: str, fps: int = 12):
        super().__init__()
        self.assets_dir = assets_dir
        self.fps = max(1, fps)
        self.timer = QTimer()
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.timeout.connect(self._next_frame)

        self.current_anim = ""
        self.frames: List[QPixmap] = []
        self.current_index = 0
        self.is_loop = True
        self.on_finish_callback: Optional[Callable] = None
        self._cache: Dict[str, List[QPixmap]] = {}

    def set_fps(self, fps: int):
        """動態更新動畫影格率並即時重設計時器週期"""
        self.fps = max(1, fps)
        if self.timer.isActive():
            self.timer.setInterval(int(1000 / self.fps))

    def preload_animation(self, anim_name: str) -> List[QPixmap]:
        if anim_name in self._cache:
            return self._cache[anim_name]

        anim_path = os.path.join(self.assets_dir, anim_name)
        frames = []
        if os.path.isdir(anim_path):
            file_names = sorted(os.listdir(anim_path))
            for f in file_names:
                if f.lower().endswith(('.png', '.webp', '.jpg', '.jpeg')):
                    full_p = os.path.join(anim_path, f)
                    pix = QPixmap(full_p)
                    if not pix.isNull():
                        frames.append(pix)
        elif os.path.isfile(anim_path):
            pix = QPixmap(anim_path)
            if not pix.isNull():
                frames.append(pix)

        self._cache[anim_name] = frames
        return frames

    def preload_animations(self, anim_names: List[str]):
        """批量預載指定的動作清單，將所有影格提前讀入記憶體"""
        for anim in anim_names:
            if anim:
                self.preload_animation(anim)

    def clear_cache(self, keep_anims: Optional[List[str]] = None):
        """清理已快取素材，釋放未在使用的動畫記憶體"""
        if keep_anims is None:
            self._cache.clear()
        else:
            keep_set = set(keep_anims)
            self._cache = {k: v for k, v in self._cache.items() if k in keep_set}

    def play_loop(self, anim_name: str):
        frames = self.preload_animation(anim_name)
        if not frames:
            print(f"[SpritePlayer] Warning: No frames found for {anim_name}")
            return
        
        # If already playing this loop, continue
        if self.current_anim == anim_name and self.is_loop and self.timer.isActive():
            return

        # 狀態轉換時先派發一幀全透明空白畫布，徹底清空殘留影像緩衝
        if self.current_anim != anim_name:
            blank = QPixmap(frames[0].size())
            blank.fill(Qt.GlobalColor.transparent)
            self.frame_changed.emit(blank)

        self.current_anim = anim_name
        self.frames = frames
        self.current_index = 0
        self.is_loop = True
        self.on_finish_callback = None

        self._emit_current()
        self.timer.start(int(1000 / self.fps))

    def play_once(self, anim_name: str, callback: Optional[Callable] = None):
        frames = self.preload_animation(anim_name)
        if not frames:
            print(f"[SpritePlayer] Warning: No frames found for {anim_name}")
            if callback:
                callback()
            return

        # 狀態轉換時先派發一幀全透明空白畫布，徹底清空殘留影像緩衝
        if self.current_anim != anim_name:
            blank = QPixmap(frames[0].size())
            blank.fill(Qt.GlobalColor.transparent)
            self.frame_changed.emit(blank)

        self.current_anim = anim_name
        self.frames = frames
        self.current_index = 0
        self.is_loop = False
        self.on_finish_callback = callback

        self._emit_current()
        self.timer.start(int(1000 / self.fps))

    def _next_frame(self):
        if not self.frames:
            return

        self.current_index += 1
        if self.current_index >= len(self.frames):
            if self.is_loop:
                self.current_index = 0
                self._emit_current()
            else:
                self.timer.stop()
                cb = self.on_finish_callback
                self.finished_once.emit()
                if cb:
                    cb()
                return
        else:
            self._emit_current()

    def _emit_current(self):
        if 0 <= self.current_index < len(self.frames):
            self.frame_changed.emit(self.frames[self.current_index])
