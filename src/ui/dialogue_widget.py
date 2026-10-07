import re
from typing import List, Dict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QPushButton,
    QGraphicsDropShadowEffect, QFrame, QMenu, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QColor, QFont, QAction
from src.utils.i18n import I18n

class DialogueWidget(QWidget):
    action_clicked = pyqtSignal(dict)
    action_deleted = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(310)

        # Main container with styling
        self.container = QFrame(self)
        self.container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.container.setObjectName("dialogueContainer")
        self.container.setStyleSheet("""
            QFrame#dialogueContainer {
                background-color: rgba(28, 28, 32, 235);
                border: 2px solid #d4af37;
                border-radius: 14px;
            }
            QLabel#promptLabel {
                color: #f7e7b4;
                font-size: 14px;
                font-weight: bold;
                padding: 4px 2px;
            }
            QPushButton.actionBtn {
                background-color: rgba(55, 48, 42, 210);
                color: #ffffff;
                border: 1px solid #8e6c32;
                border-radius: 8px;
                padding: 7px 12px;
                font-size: 13px;
                text-align: left;
            }
            QPushButton.actionBtn:hover {
                background-color: #d4af37;
                color: #1a1a1a;
                font-weight: bold;
            }
            QPushButton.addBtn {
                background-color: rgba(35, 60, 42, 220);
                color: #bbf7d0;
                border: 1px solid #4ade80;
                border-radius: 8px;
                padding: 7px 12px;
                font-size: 13px;
                text-align: left;
                font-weight: bold;
            }
            QPushButton.addBtn:hover {
                background-color: #22c55e;
                color: #052e16;
            }
            QPushButton.pomodoroBtn {
                background-color: rgba(85, 35, 30, 220);
                color: #fecaca;
                border: 1px solid #f87171;
                border-radius: 8px;
                padding: 7px 12px;
                font-size: 13px;
                text-align: left;
                font-weight: 500;
            }
            QPushButton.pomodoroBtn:hover {
                background-color: #dc2626;
                color: #ffffff;
                font-weight: bold;
            }
            QPushButton.dismissBtn {
                background-color: rgba(45, 45, 50, 180);
                color: #9ca3af;
                border: 1px dashed #6b7280;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 12px;
                text-align: center;
            }
            QPushButton.dismissBtn:hover {
                background-color: #4b5563;
                color: #ffffff;
            }
        """)

        # Shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setColor(QColor(0, 0, 0, 190))
        shadow.setOffset(0, 4)
        self.container.setGraphicsEffect(shadow)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.addWidget(self.container)

        self.box_layout = QVBoxLayout(self.container)
        self.box_layout.setContentsMargins(14, 14, 14, 14)
        self.box_layout.setSpacing(10)

        # Prompt
        self.prompt_label = QLabel(self.container)
        self.prompt_label.setObjectName("promptLabel")
        self.prompt_label.setWordWrap(True)
        self.box_layout.addWidget(self.prompt_label)

        # Grid Layout for action buttons (no scrollbar, dynamic sizing)
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(8)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.box_layout.addLayout(self.grid_layout)

    def _create_action_button(self, act: dict) -> QPushButton:
        label = act.get("label", "未命名")
        action_type = act.get("action_type")
        act_id = act.get("id")

        if act_id == "add_task" or action_type == "add_task":
            label = I18n.t("btn_add_task_dialogue")
        elif act_id == "dismiss" or action_type == "dismiss":
            label = I18n.t("btn_dismiss_dialogue")
        elif action_type == "pomodoro":
            m = re.search(r'(\d+)', label)
            dur = m.group(1) if m else "20"
            label = I18n.t("btn_pomodoro_dialogue", duration=dur)

        btn = QPushButton(label, self.container)
        if action_type == "dismiss":
            btn.setProperty("class", "dismissBtn")
        elif action_type == "add_task":
            btn.setProperty("class", "addBtn")
        elif action_type == "pomodoro":
            btn.setProperty("class", "pomodoroBtn")
        else:
            btn.setProperty("class", "actionBtn")
            # Right click on executable action allows deletion
            btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            btn.customContextMenuRequested.connect(
                lambda pos, b=btn, a=act: self._show_action_context_menu(pos, b, a)
            )

        btn.clicked.connect(lambda checked=False, a=act: self.action_clicked.emit(a))
        return btn

    def invalidate_cache(self):
        self._content_cache_key = None

    def set_content(self, prompt: str, actions: List[Dict]):
        if prompt in ("師主有何吩咐？", "主人有何吩咐？", "How may I help you?"):
            prompt = I18n.t("default_dialogue_prompt")

        cache_key = (prompt, tuple(str(a) for a in actions), I18n.get_language())
        if getattr(self, "_content_cache_key", None) == cache_key:
            return
        self._content_cache_key = cache_key

        self.prompt_label.setText(prompt)

        # Clear existing buttons in grid
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

        total_count = len(actions)
        is_dual_column = total_count > 10

        # Dynamic width: <=10 items is single column (310px), >10 items is dual column (520px)
        if is_dual_column:
            self.setFixedWidth(520)
        else:
            self.setFixedWidth(310)

        # Separate normal tasks and utility buttons (add_task, dismiss)
        normal_actions = []
        utility_actions = []
        for act in actions:
            if act.get("action_type") in ("add_task", "dismiss"):
                utility_actions.append(act)
            else:
                normal_actions.append(act)

        current_row = 0

        if not is_dual_column:
            # 1. 單欄模式 (<= 10 個項目)：由上至下依序排列，視窗高度完全自適應增長
            for act in actions:
                btn = self._create_action_button(act)
                self.grid_layout.addWidget(btn, current_row, 0)
                current_row += 1
        else:
            # 2. 雙欄/兩行模式 (> 10 個項目)：擴展為兩行並列
            for i, act in enumerate(normal_actions):
                btn = self._create_action_button(act)
                r = i // 2
                c = i % 2
                # 若常規項目為奇數且為最後一項，使其橫跨兩欄
                if i == len(normal_actions) - 1 and c == 0:
                    self.grid_layout.addWidget(btn, r, 0, 1, 2)
                    current_row = r + 1
                else:
                    self.grid_layout.addWidget(btn, r, c)
                    current_row = max(current_row, r + 1)

            # 底部功能按鈕處理
            if len(utility_actions) == 2:
                # 兩顆功能按鈕（新工作與沒事了）左右並排在同一列
                btn_left = self._create_action_button(utility_actions[0])
                btn_right = self._create_action_button(utility_actions[1])
                self.grid_layout.addWidget(btn_left, current_row, 0)
                self.grid_layout.addWidget(btn_right, current_row, 1)
            elif len(utility_actions) == 1:
                btn = self._create_action_button(utility_actions[0])
                self.grid_layout.addWidget(btn, current_row, 0, 1, 2)
            elif len(utility_actions) > 2:
                for i, act in enumerate(utility_actions):
                    btn = self._create_action_button(act)
                    r = current_row + (i // 2)
                    c = i % 2
                    if i == len(utility_actions) - 1 and c == 0:
                        self.grid_layout.addWidget(btn, r, 0, 1, 2)
                    else:
                        self.grid_layout.addWidget(btn, r, c)

        # 動態調整視窗至適合內容的高度
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()
        self.adjustSize()

    def _show_action_context_menu(self, pos: QPoint, button: QPushButton, action: dict):
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
                background-color: #dc2626;
                color: #ffffff;
            }
        """)
        del_act = QAction(I18n.t("task_context_delete"), self)
        del_act.triggered.connect(lambda: self.action_deleted.emit(action))
        menu.addAction(del_act)
        menu.exec(button.mapToGlobal(pos))

    def position_next_to(self, target_rect, screen_geometry):
        """Positions dialog smartly to the left or right of the pet within screen_geometry"""
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()
        self.adjustSize()
        w = self.width()
        h = max(self.height(), self.sizeHint().height())
        self.resize(w, h)

        # Try placing on the left first
        target_x = target_rect.x() - w - 10
        if target_x < screen_geometry.left() + 10:
            # Place on the right
            target_x = target_rect.right() + 10

        # Clamping in case right side also overflows
        if target_x + w > screen_geometry.right() - 10:
            target_x = max(screen_geometry.left() + 10, screen_geometry.right() - w - 10)

        target_y = target_rect.center().y() - h // 2
        # Boundary clamp
        target_y = max(screen_geometry.top() + 10, min(target_y, screen_geometry.bottom() - h - 10))

        self.move(target_x, target_y)
