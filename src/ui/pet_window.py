import os
import sys
from PyQt6.QtWidgets import QWidget, QMenu, QApplication, QToolTip
from PyQt6.QtCore import Qt, QPoint, QRect, QPropertyAnimation, QEasingCurve, pyqtSlot, QTimer
from PyQt6.QtGui import QPainter, QPixmap, QMouseEvent, QPaintEvent, QCursor, QAction, QWheelEvent

from src.core.state_machine import StateMachine, PetState
from src.core.launcher import Launcher
from src.core.pomodoro import PomodoroTimer
from src.ui.sprite_player import SpritePlayer
from src.ui.dialogue_widget import DialogueWidget
from src.utils.config_loader import ConfigLoader
from src.utils.i18n import I18n
from src.utils.topmost import force_topmost
from src.platform import is_zoom_modifier, setup_app_window

class PetWindow(QWidget):
    def __init__(self, base_dir: str):
        super().__init__()
        self.base_dir = base_dir
        self.config_loader = ConfigLoader(base_dir)
        self.settings = self.config_loader.load_settings()
        self.actions_data = self.config_loader.load_actions()

        # Window configs
        win_conf = self.settings.get("window", {})
        self.idle_size = tuple(win_conf.get("idle_size", [180, 180]))
        self.focus_size = tuple(win_conf.get("focus_size", [320, 320]))
        self.fps = win_conf.get("fps", 12)
        self.language = self.settings.get("language", "zh")
        I18n.set_language(self.language)
        stay_on_top = win_conf.get("stay_on_top", True)

        flags = Qt.WindowType.FramelessWindowHint
        if sys.platform != "darwin":
            flags |= Qt.WindowType.SubWindow
        else:
            flags |= Qt.WindowType.NoDropShadowWindowHint
            flags |= Qt.WindowType.WindowDoesNotAcceptFocus
            
        if stay_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        setup_app_window(self)
        self.setWindowTitle(I18n.t("app_name"))
        self.setToolTip(I18n.t("tooltip_idle"))

        # Rendering & animation
        self.assets_dir = os.path.join(base_dir, "assets", "animations")
        self.sprite_player = SpritePlayer(self.assets_dir, fps=self.fps)
        self.sprite_player.frame_changed.connect(self._on_frame_update)

        # State machine
        self.state_machine = StateMachine(self.settings)
        self.state_machine.state_changed.connect(self._on_state_changed)

        # 啟動時預先載入所有設定的動畫素材至記憶體快取
        self._preload_current_animations()

        # Dialogue widget
        self.dialogue = DialogueWidget()
        self.dialogue.action_clicked.connect(self._handle_action_selected)
        self.dialogue.action_deleted.connect(self._handle_action_deleted)
        self._prewarm_dialogue()

        # Pomodoro timer
        self.pomodoro = PomodoroTimer(base_dir)
        self.pomodoro.started.connect(self._on_pomodoro_started)
        self.pomodoro.tick.connect(self._on_pomodoro_tick)
        self.pomodoro.finished.connect(self._on_pomodoro_finished)
        self.pomodoro.cancelled.connect(self._on_pomodoro_cancelled)

        # Geometry animation
        self.geom_anim = QPropertyAnimation(self, b"geometry")
        self.idle_geometry = QRect()

        # Drag state
        self._is_dragging = False
        self._drag_start_pos = QPoint()
        self._click_start_pos = QPoint()

        # Current frame pixmap
        self.current_pixmap: QPixmap = QPixmap()

        # Initial placement on desktop
        self._init_position()

    def _get_current_screen_geometry(self) -> QRect:
        """獲取當前所在的螢幕範圍 (支援多螢幕)"""
        center_pt = self.geometry().center()
        screen = QApplication.screenAt(center_pt)
        if screen is None:
            screen = self.screen()
        if screen is None:
            screen = QApplication.primaryScreen()
        return screen.availableGeometry()

    def _clamp_rect_to_screen(self, rect: QRect) -> QRect:
        """確保矩形完整落在螢幕可視工作區範圍內，若超出邊界則自動修正座標"""
        screen = QApplication.screenAt(rect.center())
        if screen is None:
            screen = self._get_current_screen_geometry()
        else:
            screen = screen.availableGeometry()

        x = rect.x()
        y = rect.y()
        w = rect.width()
        h = rect.height()

        margin = 10
        # 水平邊界修正
        if x + w > screen.right() - margin:
            x = screen.right() - margin - w
        if x < screen.left() + margin:
            x = screen.left() + margin

        # 垂直邊界修正
        if y + h > screen.bottom() - margin:
            y = screen.bottom() - margin - h
        if y < screen.top() + margin:
            y = screen.top() + margin

        return QRect(x, y, w, h)

    def _init_position(self):
        w, h = self.idle_size
        saved_pos = self.settings.get("window", {}).get("saved_position")
        if isinstance(saved_pos, (list, tuple)) and len(saved_pos) == 2:
            try:
                x, y = int(saved_pos[0]), int(saved_pos[1])
                test_rect = QRect(x, y, w, h)
                for scr in QApplication.screens():
                    if scr.availableGeometry().intersects(test_rect):
                        clamped = self._clamp_rect_to_screen(test_rect)
                        self.setGeometry(clamped)
                        self.idle_geometry = clamped
                        return
            except Exception as e:
                print(f"[PetWindow] Error validating saved position: {e}")

        screen = self._get_current_screen_geometry()
        init_x = screen.right() - w - 60
        init_y = screen.bottom() - h - 60
        clamped = self._clamp_rect_to_screen(QRect(init_x, init_y, w, h))
        self.setGeometry(clamped)
        self.idle_geometry = clamped

    def _save_position(self):
        """保存當前待命休息位置至設定檔"""
        iw, ih = self.idle_size
        if (self.idle_geometry.isValid() and not self.idle_geometry.isEmpty()
                and self.idle_geometry.width() == iw and self.idle_geometry.height() == ih):
            save_x = self.idle_geometry.x()
            save_y = self.idle_geometry.y()
        else:
            cur = self.geometry()
            save_x = cur.center().x() - iw // 2
            save_y = cur.bottom() - ih + 1

        if "window" not in self.settings:
            self.settings["window"] = {}
        self.settings["window"]["saved_position"] = [save_x, save_y]
        self.config_loader.save_settings(self.settings)

    def start(self):
        self.show()
        setup_app_window(self)
        self.state_machine.start()

        # 置頂守護：定期把自己拉回最上層，防止被其他置頂視窗或系統 UI 擠到後面
        self._stay_on_top = self.settings.get("window", {}).get("stay_on_top", True)
        self._topmost_timer = QTimer(self)
        self._topmost_timer.timeout.connect(self._ensure_topmost)
        if self._stay_on_top:
            self._topmost_timer.start(1500)
            self._ensure_topmost()

    def _ensure_topmost(self):
        """重新宣告最上層 (不搶焦點)。有選單或對話視窗開啟時暫停，避免蓋住它們。"""
        if not getattr(self, "_stay_on_top", True):
            return
        if QApplication.activePopupWidget() is not None or QApplication.activeModalWidget() is not None:
            return
        force_topmost(self)
        # 對話氣泡最後處理，確保它疊在角色上方
        if self.dialogue.isVisible():
            force_topmost(self.dialogue)

    def _on_frame_update(self, pixmap: QPixmap):
        self.current_pixmap = pixmap
        self.update()

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.fillRect(event.rect(), Qt.GlobalColor.transparent)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

        if not self.current_pixmap.isNull():
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            scaled = self.current_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            # Center inside widget
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)

    def _on_state_changed(self, state: PetState, anim_name: str):
        behavior = self.settings.get("behavior", {})
        appr_dur = behavior.get("approach_duration_ms", 450)
        ret_dur = behavior.get("return_duration_ms", 450)

        if state == PetState.IDLE_TRAINING:
            self.dialogue.hide()
            iw, ih = self.idle_size
            # 自我修復：確保回到 IDLE_TRAINING 時視窗尺寸絕對為待命尺寸且位置精準還原
            if self.idle_geometry.isValid() and not self.idle_geometry.isEmpty():
                target_rect = self._clamp_rect_to_screen(QRect(self.idle_geometry.x(), self.idle_geometry.y(), iw, ih))
            else:
                cur = self.geometry()
                target_rect = self._clamp_rect_to_screen(QRect(cur.center().x() - iw // 2, cur.bottom() - ih + 1, iw, ih))
            
            if self.geometry() != target_rect:
                self.setGeometry(target_rect)
            self.idle_geometry = target_rect
            self.sprite_player.play_loop(anim_name)

        elif state == PetState.APPROACHING:
            self.dialogue.hide()
            iw, ih = self.idle_size
            cur = self.geometry()
            # 確保待命座標嚴格記錄待命尺寸並防止越界
            if cur.width() != iw or cur.height() != ih:
                self.idle_geometry = self._clamp_rect_to_screen(QRect(cur.center().x() - iw // 2, cur.bottom() - ih + 1, iw, ih))
            else:
                self.idle_geometry = self._clamp_rect_to_screen(cur)
            
            scale_in_place = behavior.get("scale_in_place", True)
            screen = self._get_current_screen_geometry()
            fw, fh = self.focus_size

            if scale_in_place:
                # 原地放大：以角色底部中心錨定，腳踩原處自然向上/外擴展
                target_cx = cur.center().x()
                target_bottom = cur.bottom()
                target_x = target_cx - fw // 2
                target_y = target_bottom - fh + 1
            else:
                # 移動靠近當前螢幕中心
                target_cx = max(screen.left() + fw // 2 + 50, min(self.geometry().center().x(), screen.right() - fw // 2 - 50))
                target_cy = max(screen.top() + fh // 2 + 50, min(self.geometry().center().y() - 80, screen.bottom() - fh // 2 - 50))
                target_x = target_cx - fw // 2
                target_y = target_cy - fh // 2

            # 防止超出當前所在螢幕可視邊界
            target_x = max(screen.left() + 10, min(target_x, screen.right() - fw - 10))
            target_y = max(screen.top() + 10, min(target_y, screen.bottom() - fh - 10))
            target_rect = QRect(target_x, target_y, fw, fh)

            self.geom_anim.stop()
            self.geom_anim.setDuration(appr_dur)
            self.geom_anim.setStartValue(self.geometry())
            self.geom_anim.setEndValue(target_rect)
            self.geom_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            try:
                self.geom_anim.finished.disconnect()
            except Exception:
                pass
            self.geom_anim.finished.connect(self.state_machine.on_approach_completed)
            self.geom_anim.start()

        elif state == PetState.ASKING:
            self.sprite_player.play_loop(anim_name)
            # 若對話框尚未顯示（剛抵達進入 ASKING），才建立內容並定位顯示；
            # 若已在 ASKING 狀態下切換動作，對話框保持原位不動，防止重複定位造成座標下移
            if not self.dialogue.isVisible():
                screen = self._get_current_screen_geometry()
                self.dialogue.set_content(
                    self.actions_data.get("dialogue_prompt", I18n.t("default_dialogue_prompt")),
                    self.actions_data.get("actions", [])
                )
                self.dialogue.position_next_to(self.geometry(), screen)
                self.dialogue.show()

        elif state == PetState.EXECUTING:
            self.dialogue.hide()
            self.sprite_player.play_once(anim_name, self.state_machine.on_action_completed)

        elif state == PetState.RETURNING:
            self.dialogue.hide()
            iw, ih = self.idle_size
            # 嚴格縮回進入大圖前記錄的小圖待命座標，並防止超出螢幕
            if self.idle_geometry.isValid() and not self.idle_geometry.isEmpty():
                return_rect = QRect(self.idle_geometry.x(), self.idle_geometry.y(), iw, ih)
            else:
                cur = self.geometry()
                return_rect = QRect(cur.center().x() - iw // 2, cur.bottom() - ih + 1, iw, ih)

            return_rect = self._clamp_rect_to_screen(return_rect)
            self.idle_geometry = return_rect
            self.geom_anim.stop()
            self.geom_anim.setDuration(ret_dur)
            self.geom_anim.setStartValue(self.geometry())
            self.geom_anim.setEndValue(return_rect)
            self.geom_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
            try:
                self.geom_anim.finished.disconnect()
            except Exception:
                pass
            self.geom_anim.finished.connect(self.state_machine.on_return_completed)
            self.geom_anim.start()

    def _handle_action_selected(self, action_dict: dict):
        action_type = action_dict.get("action_type")
        if action_type == "dismiss":
            self.state_machine.dismiss()
        elif action_type == "add_task":
            self._handle_add_task()
        elif action_type == "pomodoro":
            self._trigger_pomodoro()
        elif action_type == "executable":
            # 1. 出招姿勢：若設定為 random、未指定或不存在，則從 executing 動作群組中隨機抽選
            trigger_anim = action_dict.get("trigger_animation")
            if not trigger_anim or trigger_anim == "random" or trigger_anim not in self.state_machine.exec_anims:
                import random
                trigger_anim = random.choice(self.state_machine.exec_anims) if self.state_machine.exec_anims else "act_punch"
            self.state_machine.trigger_action(trigger_anim)

            # 2. 啟動應用程式：支援多目標同步並行啟動或單一目標啟動
            targets = action_dict.get("targets")
            if targets:
                Launcher.launch(targets)
            else:
                target = action_dict.get("target")
                Launcher.launch(target, action_dict.get("cwd"))

    def _trigger_pomodoro(self):
        pomo_cfg = self.settings.get("pomodoro", {})
        duration = pomo_cfg.get("duration_minutes", 20)
        sound_file = pomo_cfg.get("sound_file", "")
        # 每次呼叫自動清除舊計時器並重新啟動
        self.pomodoro.start(duration, sound_file)

        # 播放出招動作，完成後自動縮小回修煉狀態
        trigger_anim = self.state_machine.exec_anims[0] if self.state_machine.exec_anims else "act_punch"
        self.state_machine.trigger_action(trigger_anim)

    def _on_pomodoro_started(self, duration: int):
        self.setToolTip(I18n.t("tooltip_pomodoro", time=f"{duration:02d}:00"))

    def _on_pomodoro_tick(self, remaining_sec: int):
        self.setToolTip(I18n.t("tooltip_pomodoro", time=self.pomodoro.get_remaining_formatted()))

    def _on_pomodoro_finished(self):
        self.setToolTip(I18n.t("tooltip_idle"))
        # 時間到：若角色處於縮小狀態，自動原地放大
        if self.state_machine.current_state == PetState.IDLE_TRAINING:
            self.state_machine.on_pet_clicked()

        screen = self._get_current_screen_geometry()
        alarm_actions = [
            {
                "id": "dismiss",
                "label": I18n.t("pomo_alarm_dismiss"),
                "action_type": "dismiss"
            }
        ]
        custom_msg = (self.settings.get("pomodoro", {}).get("alarm_message") or "").strip()
        self.dialogue.set_content(
            custom_msg or I18n.t("pomo_alarm_prompt"),
            alarm_actions
        )
        self.dialogue.position_next_to(self.geometry(), screen)
        self.dialogue.show()

    def _on_pomodoro_cancelled(self):
        self.setToolTip(I18n.t("tooltip_idle"))

    def _handle_add_task(self):
        from src.ui.task_dialog import AddTaskDialog
        import time

        dialog = AddTaskDialog(parent=self)
        if dialog.exec():
            task_data = dialog.get_task_data()
            new_action = {
                "id": f"task_{int(time.time())}",
                "label": task_data["label"],
                "action_type": "executable",
                "targets": task_data.get("targets", []),
                "target": task_data.get("target", ""),
                "trigger_animation": "random"
            }

            actions_list = self.actions_data.get("actions", [])
            # 插入在 'add_task' 或 'dismiss' 之前
            insert_idx = len(actions_list)
            for idx, act in enumerate(actions_list):
                if act.get("action_type") in ("add_task", "dismiss"):
                    insert_idx = idx
                    break
            actions_list.insert(insert_idx, new_action)
            self.actions_data["actions"] = actions_list

            # 保存至 actions.json
            self.config_loader.save_actions(self.actions_data)

            # 重新整理對話框選單
            screen = self._get_current_screen_geometry()
            self.dialogue.invalidate_cache()
            self.dialogue.set_content(
                self.actions_data.get("dialogue_prompt", I18n.t("default_dialogue_prompt")),
                self.actions_data.get("actions", [])
            )
            self.dialogue.position_next_to(self.geometry(), screen)

    def _handle_action_deleted(self, action_dict: dict):
        act_id = action_dict.get("id")
        actions_list = self.actions_data.get("actions", [])
        self.actions_data["actions"] = [
            act for act in actions_list if act.get("id") != act_id
        ]
        self.config_loader.save_actions(self.actions_data)

        # 重新整理對話框選單
        screen = self._get_current_screen_geometry()
        self.dialogue.invalidate_cache()
        self.dialogue.set_content(
            self.actions_data.get("dialogue_prompt", I18n.t("default_dialogue_prompt")),
            self.actions_data.get("actions", [])
        )
        self.dialogue.position_next_to(self.geometry(), screen)

    # Mouse events for dragging and clicking
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            # 只有在待命修煉小圖狀態下才允許拖曳
            self._is_dragging = (self.state_machine.current_state == PetState.IDLE_TRAINING)
            self._drag_start_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._click_start_pos = event.globalPosition().toPoint()
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._is_dragging and (event.buttons() & Qt.MouseButton.LeftButton):
            # Only allow free dragging when in idle state
            if self.state_machine.current_state == PetState.IDLE_TRAINING:
                new_pos = event.globalPosition().toPoint() - self._drag_start_pos
                self.move(new_pos)
                self.idle_geometry = self.geometry()
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            was_dragging = self._is_dragging
            self._is_dragging = False
            distance = (event.globalPosition().toPoint() - self._click_start_pos).manhattanLength()

            if self.state_machine.current_state == PetState.IDLE_TRAINING:
                if distance < 10:
                    self.state_machine.on_pet_clicked()
                elif was_dragging:
                    iw, ih = self.idle_size
                    cur = self.geometry()
                    clamped_rect = self._clamp_rect_to_screen(QRect(cur.x(), cur.y(), iw, ih))
                    self.setGeometry(clamped_rect)
                    self.idle_geometry = clamped_rect
                    self._save_position()
            elif self.state_machine.current_state == PetState.ASKING:
                # 大圖模式下點擊角色切換姿勢，絕不污染待命尺寸
                self.state_machine.switch_asking_anim()

            event.accept()
    def wheelEvent(self, event: QWheelEvent):
        """縮放當前角色尺寸 (Ctrl/⌘ + 滾輪，小圖/大圖分別調整並持久化保存)"""
        if is_zoom_modifier(event.modifiers()):
            # 動畫運行中暫不響應縮放
            if self.geom_anim.state() == QPropertyAnimation.State.Running:
                event.accept()
                return

            delta = event.angleDelta().y()
            if delta == 0:
                delta = event.pixelDelta().y()
            if delta == 0:
                event.accept()
                return

            step = 10 if delta > 0 else -10
            screen = self._get_current_screen_geometry()
            cur = self.geometry()
            cx = cur.center().x()
            bottom = cur.bottom()

            if self.state_machine.current_state in (PetState.IDLE_TRAINING, PetState.RETURNING):
                cur_w, _ = self.idle_size
                new_w = max(60, min(cur_w + step, 500))
                new_h = new_w
                self.idle_size = (new_w, new_h)

                if "window" not in self.settings:
                    self.settings["window"] = {}
                self.settings["window"]["idle_size"] = [new_w, new_h]

                new_x = cx - new_w // 2
                new_y = bottom - new_h + 1
                # 確保不超出螢幕可見區域
                new_x = max(screen.left() + 5, min(new_x, screen.right() - new_w - 5))
                new_y = max(screen.top() + 5, min(new_y, screen.bottom() - new_h - 5))

                self.setGeometry(new_x, new_y, new_w, new_h)
                self.idle_geometry = self.geometry()
                self._save_position()
                self.config_loader.save_settings(self.settings)

                QToolTip.showText(
                    event.globalPosition().toPoint(),
                    I18n.t("hud_idle_size", w=new_w, h=new_h),
                    self
                )

            elif self.state_machine.current_state in (PetState.ASKING, PetState.APPROACHING, PetState.EXECUTING):
                cur_w, _ = self.focus_size
                new_w = max(100, min(cur_w + step, 800))
                new_h = new_w
                self.focus_size = (new_w, new_h)

                if "window" not in self.settings:
                    self.settings["window"] = {}
                self.settings["window"]["focus_size"] = [new_w, new_h]

                new_x = cx - new_w // 2
                new_y = bottom - new_h + 1
                new_x = max(screen.left() + 5, min(new_x, screen.right() - new_w - 5))
                new_y = max(screen.top() + 5, min(new_y, screen.bottom() - new_h - 5))

                self.setGeometry(new_x, new_y, new_w, new_h)
                self.config_loader.save_settings(self.settings)

                if self.dialogue.isVisible():
                    self.dialogue.position_next_to(self.geometry(), screen)

                QToolTip.showText(
                    event.globalPosition().toPoint(),
                    I18n.t("hud_focus_size", w=new_w, h=new_h),
                    self
                )

            event.accept()
        else:
            super().wheelEvent(event)

    def _show_context_menu(self, pos: QPoint):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #d4af37;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item:selected {
                background-color: #d4af37;
                color: #1a1a1a;
            }
        """)

        reset_act = QAction(I18n.t("menu_reset_pos"), self)
        reset_act.triggered.connect(self._reset_position)
        menu.addAction(reset_act)

        settings_act = QAction(I18n.t("menu_settings"), self)
        settings_act.triggered.connect(self._open_settings_dialog)
        menu.addAction(settings_act)

        # 根據目前開機啟動狀態，僅顯示註冊或註銷其中一種
        from src.utils.autostart import AutoStartManager
        if AutoStartManager.is_registered():
            autostart_act = QAction(I18n.t("menu_autostart_unreg"), self)
            autostart_act.triggered.connect(self._unregister_autostart)
            menu.addAction(autostart_act)
        else:
            autostart_act = QAction(I18n.t("menu_autostart_reg"), self)
            autostart_act.triggered.connect(self._register_autostart)
            menu.addAction(autostart_act)

        menu.addSeparator()

        exit_act = QAction(I18n.t("menu_exit"), self)
        exit_act.triggered.connect(self._quit_app)
        menu.addAction(exit_act)

        menu.exec(pos)

    def _register_autostart(self):
        from src.utils.autostart import AutoStartManager
        from PyQt6.QtWidgets import QMessageBox

        if AutoStartManager.register(self.base_dir):
            QMessageBox.information(
                self,
                I18n.t("autostart_title"),
                I18n.t("autostart_reg_success")
            )
        else:
            QMessageBox.warning(
                self,
                I18n.t("autostart_fail_title"),
                I18n.t("autostart_reg_fail")
            )

    def _unregister_autostart(self):
        from src.utils.autostart import AutoStartManager
        from PyQt6.QtWidgets import QMessageBox

        if AutoStartManager.unregister():
            QMessageBox.information(
                self,
                I18n.t("autostart_title"),
                I18n.t("autostart_unreg_success")
            )
        else:
            QMessageBox.warning(
                self,
                I18n.t("autostart_fail_title"),
                I18n.t("autostart_unreg_fail")
            )

    def _reload_from_settings(self):
        """重新自 settings.json 載入並即時套用最新設定（包含尺寸、動畫組、番茄鐘、語言與 FPS 等）"""
        self.settings = self.config_loader.load_settings()
        self.actions_data = self.config_loader.load_actions()

        self.language = self.settings.get("language", "zh")
        I18n.set_language(self.language)
        self.setWindowTitle(I18n.t("app_name"))
        if not self.pomodoro.is_running:
            self.setToolTip(I18n.t("tooltip_idle"))

        win_conf = self.settings.get("window", {})
        self.idle_size = tuple(win_conf.get("idle_size", [180, 180]))
        self.focus_size = tuple(win_conf.get("focus_size", [320, 320]))
        self.fps = win_conf.get("fps", 12)
        self.sprite_player.set_fps(self.fps)

        anim_groups = self.settings.get("animation_groups", {})
        self.state_machine.idle_anims = anim_groups.get("idle", ["train_meditate"])
        self.state_machine.asking_anims = anim_groups.get("asking", ["ask_fist"])
        self.state_machine.exec_anims = anim_groups.get("executing", ["act_punch"])

        # 預先載入最新設定中的所有動畫素材至記憶體快取
        self._preload_current_animations()

        screen = self._get_current_screen_geometry()
        cur = self.geometry()
        if self.state_machine.current_state == PetState.IDLE_TRAINING:
            iw, ih = self.idle_size
            clamped = self._clamp_rect_to_screen(QRect(cur.center().x() - iw // 2, cur.bottom() - ih + 1, iw, ih))
            self.setGeometry(clamped)
            self.idle_geometry = clamped
            self._save_position()
            if self.state_machine.current_anim not in self.state_machine.idle_anims:
                self.state_machine.current_anim = self.state_machine.idle_anims[0]
                self.sprite_player.play_loop(self.state_machine.current_anim)
        elif self.state_machine.current_state == PetState.ASKING:
            fw, fh = self.focus_size
            self.setGeometry(cur.center().x() - fw // 2, cur.bottom() - fh + 1, fw, fh)
            if self.dialogue.isVisible():
                self.dialogue.invalidate_cache()
                self.dialogue.set_content(
                    self.actions_data.get("dialogue_prompt", I18n.t("default_dialogue_prompt")),
                    self.actions_data.get("actions", [])
                )
                self.dialogue.position_next_to(self.geometry(), screen)
            if self.state_machine.current_anim not in self.state_machine.asking_anims:
                self.state_machine.current_anim = self.state_machine.asking_anims[0]
                self.sprite_player.play_loop(self.state_machine.current_anim)

    def _preload_current_animations(self):
        """依據目前 settings 中的動畫分組，將所有素材預載入快取並釋放已移除之素材"""
        anim_groups = self.settings.get("animation_groups", {})
        needed_anims = set()
        for group in ("idle", "asking", "executing"):
            for anim in anim_groups.get(group, []):
                if anim:
                    needed_anims.add(anim)
        
        # 清除不再使用的動畫快取（若有），釋放記憶體
        self.sprite_player.clear_cache(keep_anims=list(needed_anims))
        # 批量預載所有需要的動畫
        self.sprite_player.preload_animations(list(needed_anims))

    def _prewarm_dialogue(self):
        """預熱工作選單視窗，提前建立原生視窗句柄與繪製快取，徹底消除首次呼叫時的卡頓"""
        self.dialogue.set_content(
            self.actions_data.get("dialogue_prompt", I18n.t("default_dialogue_prompt")),
            self.actions_data.get("actions", [])
        )
        try:
            self.dialogue.winId()  # 強制生成系統原生視窗 handle
            if sys.platform != "darwin":
                self.dialogue.setWindowOpacity(0.0)
                self.dialogue.show()
                QApplication.processEvents()
                self.dialogue.hide()
                self.dialogue.setWindowOpacity(1.0)
        except Exception as e:
            print(f"[PetWindow] Dialogue prewarm note: {e}")

    def _open_settings_dialog(self):
        from src.ui.settings_dialog import SettingsDialog

        current_prompt = self.actions_data.get("dialogue_prompt", I18n.t("default_dialogue_prompt"))
        idle_anims = list(self.state_machine.idle_anims)
        asking_anims = list(self.state_machine.asking_anims)
        exec_anims = list(self.state_machine.exec_anims)

        pomo_cfg = self.settings.get("pomodoro", {})
        pomo_dur = pomo_cfg.get("duration_minutes", 20)
        pomo_sound = pomo_cfg.get("sound_file", "")

        dialog = SettingsDialog(
            base_dir=self.base_dir,
            current_prompt=current_prompt,
            idle_anims=idle_anims,
            asking_anims=asking_anims,
            exec_anims=exec_anims,
            pomodoro_duration=pomo_dur,
            pomodoro_sound=pomo_sound,
            pomodoro_alarm_message=pomo_cfg.get("alarm_message", ""),
            current_language=self.language,
            current_fps=self.fps,
            parent=self
        )

        if dialog.exec():
            new_prompt = dialog.get_prompt()
            new_idle = dialog.get_idle_anims()
            new_asking = dialog.get_asking_anims()
            new_exec = dialog.get_exec_anims()
            new_pomo = dialog.get_pomodoro_settings()
            new_lang = dialog.get_language()
            new_fps = dialog.get_fps()

            # 1. 保存台詞更新
            self.actions_data["dialogue_prompt"] = new_prompt

            # 更新 actions 中的 pomodoro 按鈕標籤
            for act in self.actions_data.get("actions", []):
                if act.get("action_type") == "pomodoro":
                    act["label"] = I18n.t("btn_pomodoro_dialogue", duration=new_pomo['duration_minutes'])

            self.config_loader.save_actions(self.actions_data)

            # 2. 保存動畫分組、番茄鐘、語言與 FPS 更新
            if "window" not in self.settings:
                self.settings["window"] = {}
            self.settings["window"]["fps"] = new_fps
            self.settings["language"] = new_lang

            if "animation_groups" not in self.settings:
                self.settings["animation_groups"] = {}
            self.settings["animation_groups"]["idle"] = new_idle
            self.settings["animation_groups"]["asking"] = new_asking
            self.settings["animation_groups"]["executing"] = new_exec
            self.settings["pomodoro"] = new_pomo
            self.config_loader.save_settings(self.settings)

            # 3. 即時套用至狀態機
            self.state_machine.idle_anims = new_idle
            self.state_machine.asking_anims = new_asking
            self.state_machine.exec_anims = new_exec

            # 若當前正在播放的動作已不在清單內，立即切換為清單中現存的動作
            if self.state_machine.current_state == PetState.IDLE_TRAINING:
                if self.state_machine.current_anim not in new_idle:
                    self.state_machine.current_anim = new_idle[0]
                    self.sprite_player.play_loop(self.state_machine.current_anim)
            elif self.state_machine.current_state == PetState.ASKING:
                if self.state_machine.current_anim not in new_asking:
                    self.state_machine.current_anim = new_asking[0]
                    self.sprite_player.play_loop(self.state_machine.current_anim)

            # 重新整理並即時套用尺寸與所有設定 (包含語言與 FPS)
            self._reload_from_settings()
        else:
            # 取消時恢復語言設定
            I18n.set_language(self.language)

    def _reset_position(self):
        self.geom_anim.stop()
        screen = self._get_current_screen_geometry()
        w, h = self.idle_size
        init_x = screen.right() - w - 60
        init_y = screen.bottom() - h - 60
        self.setGeometry(init_x, init_y, w, h)
        self.idle_geometry = self.geometry()
        self._save_position()
        if self.state_machine.current_state != PetState.IDLE_TRAINING:
            self.state_machine.current_state = PetState.IDLE_TRAINING
            self.dialogue.hide()
            self.sprite_player.play_loop(self.state_machine.current_anim)

    def _quit_app(self):
        self._save_position()
        self.dialogue.close()
        QApplication.instance().quit()

    def closeEvent(self, event):
        self._save_position()
        self.dialogue.close()
        super().closeEvent(event)
