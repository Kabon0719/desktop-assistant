import random
from enum import Enum, auto
from typing import List, Dict, Optional
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

class PetState(Enum):
    IDLE_TRAINING = auto()
    APPROACHING = auto()
    ASKING = auto()
    EXECUTING = auto()
    RETURNING = auto()

class StateMachine(QObject):
    state_changed = pyqtSignal(PetState, str) # new_state, anim_to_play

    def __init__(self, settings: dict):
        super().__init__()
        self.settings = settings
        behavior = settings.get("behavior", {})
        self.idle_switch_interval = behavior.get("idle_switch_interval_sec", 20) * 1000
        self.asking_switch_interval = behavior.get("asking_switch_interval_sec", 15) * 1000

        anim_groups = settings.get("animation_groups", {})
        self.idle_anims: List[str] = anim_groups.get("idle", ["train_meditate"])
        self.asking_anims: List[str] = anim_groups.get("asking", ["ask_fist"])
        self.exec_anims: List[str] = anim_groups.get("executing", ["act_punch"])

        self.current_state = PetState.IDLE_TRAINING
        self.current_anim = self.idle_anims[0] if self.idle_anims else ""

        # Timer for random alternation
        self.variation_timer = QTimer()
        self.variation_timer.timeout.connect(self._on_variation_timeout)

    def start(self):
        self.current_state = PetState.IDLE_TRAINING
        self.current_anim = random.choice(self.idle_anims) if self.idle_anims else ""
        self.state_changed.emit(self.current_state, self.current_anim)
        self.variation_timer.start(self.idle_switch_interval)

    def on_pet_clicked(self):
        """User clicks the monk while in idle training"""
        if self.current_state == PetState.IDLE_TRAINING:
            self.variation_timer.stop()
            self.current_state = PetState.APPROACHING
            self.state_changed.emit(self.current_state, self.current_anim)

    def on_approach_completed(self):
        """Monk finished moving & scaling closer"""
        if self.current_state == PetState.APPROACHING:
            self.current_state = PetState.ASKING
            self.current_anim = random.choice(self.asking_anims) if self.asking_anims else ""
            self.state_changed.emit(self.current_state, self.current_anim)
            self.variation_timer.start(self.asking_switch_interval)

    def trigger_action(self, trigger_anim: Optional[str] = None):
        """User clicked an action item"""
        if self.current_state == PetState.ASKING:
            self.variation_timer.stop()
            self.current_state = PetState.EXECUTING
            anim = trigger_anim if trigger_anim else (random.choice(self.exec_anims) if self.exec_anims else "")
            self.current_anim = anim
            self.state_changed.emit(self.current_state, self.current_anim)

    def on_action_completed(self):
        """一次性動作執行完畢後，平滑縮小並回到修煉模式 (縮小模式)"""
        if self.current_state == PetState.EXECUTING:
            self.current_state = PetState.RETURNING
            self.state_changed.emit(self.current_state, self.current_anim)

    def dismiss(self):
        """User selected 'nothing to do for now'"""
        if self.current_state in (PetState.ASKING, PetState.APPROACHING):
            self.variation_timer.stop()
            self.current_state = PetState.RETURNING
            self.state_changed.emit(self.current_state, self.current_anim)

    def on_return_completed(self):
        """Monk returned to original training spot"""
        if self.current_state == PetState.RETURNING:
            self.current_state = PetState.IDLE_TRAINING
            self.current_anim = random.choice(self.idle_anims) if self.idle_anims else ""
            self.state_changed.emit(self.current_state, self.current_anim)
            self.variation_timer.start(self.idle_switch_interval)

    def _on_variation_timeout(self):
        if self.current_state == PetState.IDLE_TRAINING and len(self.idle_anims) > 1:
            candidates = [a for a in self.idle_anims if a != self.current_anim]
            self.current_anim = random.choice(candidates)
            self.state_changed.emit(self.current_state, self.current_anim)
        elif self.current_state == PetState.ASKING and len(self.asking_anims) > 1:
            candidates = [a for a in self.asking_anims if a != self.current_anim]
            self.current_anim = random.choice(candidates)
            self.state_changed.emit(self.current_state, self.current_anim)

    def switch_asking_anim(self):
        """在大圖待命狀態下點擊角色切換姿勢"""
        if self.current_state == PetState.ASKING and self.asking_anims:
            if len(self.asking_anims) > 1:
                if self.current_anim in self.asking_anims:
                    cur_idx = self.asking_anims.index(self.current_anim)
                    next_idx = (cur_idx + 1) % len(self.asking_anims)
                    self.current_anim = self.asking_anims[next_idx]
                else:
                    self.current_anim = self.asking_anims[0]
            else:
                self.current_anim = self.asking_anims[0]
            self.state_changed.emit(self.current_state, self.current_anim)
            self.variation_timer.start(self.asking_switch_interval)
