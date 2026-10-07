import os
from typing import List
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QMessageBox, QFrame, QListWidget, QListWidgetItem,
    QAbstractItemView
)
from PyQt6.QtCore import Qt
from src.utils.i18n import I18n
from src.platform import get_file_dialog_filter

class AddTaskDialog(QDialog):
    def __init__(self, available_exec_anims: List[str] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(I18n.t("task_dialog_title"))
        self.setFixedWidth(520)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        self._user_edited_name = False

        self.setStyleSheet("""
            QDialog {
                background-color: #202024;
                color: #f3f4f6;
                font-family: "Microsoft JhengHei", "PingFang SC", "Segoe UI", sans-serif;
            }
            QLabel {
                color: #e5e7eb;
                font-size: 13px;
                font-weight: 500;
            }
            QLineEdit {
                background-color: #2b2b30;
                color: #ffffff;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 7px 10px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #d4af37;
            }
            QListWidget {
                background-color: #26262b;
                color: #f3f4f6;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 4px;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 6px 8px;
                border-radius: 4px;
                margin-bottom: 2px;
            }
            QListWidget::item:hover {
                background-color: #383842;
            }
            QListWidget::item:selected {
                background-color: #d4af37;
                color: #1a1a1a;
                font-weight: bold;
            }
            QPushButton#browseBtn {
                background-color: #1e3a2b;
                color: #a7f3d0;
                border: 1px solid #059669;
                border-radius: 6px;
                padding: 7px 14px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton#browseBtn:hover {
                background-color: #10b981;
                color: #064e3b;
            }
            QPushButton#removeBtn {
                background-color: #3b2a2a;
                color: #fca5a5;
                border: 1px solid #dc2626;
                border-radius: 6px;
                padding: 7px 12px;
                font-size: 12px;
            }
            QPushButton#removeBtn:hover {
                background-color: #ef4444;
                color: #ffffff;
            }
            QPushButton#clearBtn {
                background-color: #2b2b30;
                color: #9ca3af;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 7px 12px;
                font-size: 12px;
            }
            QPushButton#clearBtn:hover {
                background-color: #374151;
                color: #ffffff;
            }
            QPushButton#confirmBtn {
                background-color: #92400e;
                color: #fef3c7;
                border: 1px solid #f59e0b;
                border-radius: 8px;
                padding: 8px 18px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton#confirmBtn:hover {
                background-color: #b45309;
                color: #ffffff;
            }
            QPushButton#cancelBtn {
                background-color: #18181b;
                color: #a1a1aa;
                border: 1px solid #3f3f46;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton#cancelBtn:hover {
                background-color: #2e2e33;
                color: #ffffff;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        # Title
        title_lbl = QLabel(I18n.t("task_header"), self)
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #f7e7b4; margin-bottom: 2px;")
        layout.addWidget(title_lbl)

        # 1. Task Name
        layout.addWidget(QLabel(I18n.t("task_name_label"), self))
        self.name_edit = QLineEdit(self)
        self.name_edit.setPlaceholderText(I18n.t("task_name_placeholder"))
        self.name_edit.textEdited.connect(self._on_name_edited)
        layout.addWidget(self.name_edit)

        # 2. Executables List
        target_header_row = QHBoxLayout()
        target_lbl = QLabel(I18n.t("task_targets_label"), self)
        target_header_row.addWidget(target_lbl)
        target_header_row.addStretch()
        self.count_lbl = QLabel(I18n.t("task_count_label", n=0), self)
        self.count_lbl.setStyleSheet("color: #9ca3af; font-size: 12px;")
        target_header_row.addWidget(self.count_lbl)
        layout.addLayout(target_header_row)

        self.target_list = QListWidget(self)
        self.target_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.target_list.setMinimumHeight(120)
        self.target_list.setMaximumHeight(160)
        layout.addWidget(self.target_list)

        # Management buttons for list
        action_btn_row = QHBoxLayout()
        self.browse_btn = QPushButton(I18n.t("btn_browse_exe"), self)
        self.browse_btn.setObjectName("browseBtn")
        self.browse_btn.clicked.connect(self._browse_files)
        action_btn_row.addWidget(self.browse_btn)

        self.remove_btn = QPushButton(I18n.t("btn_remove_target"), self)
        self.remove_btn.setObjectName("removeBtn")
        self.remove_btn.clicked.connect(self._remove_selected)
        action_btn_row.addWidget(self.remove_btn)

        self.clear_btn = QPushButton(I18n.t("btn_clear_targets"), self)
        self.clear_btn.setObjectName("clearBtn")
        self.clear_btn.clicked.connect(self._clear_targets)
        action_btn_row.addWidget(self.clear_btn)

        layout.addLayout(action_btn_row)
        layout.addSpacing(6)

        # Confirm & Cancel buttons row
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.cancel_btn = QPushButton(I18n.t("btn_cancel_task"), self)
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.cancel_btn)

        self.confirm_btn = QPushButton(I18n.t("btn_confirm_task"), self)
        self.confirm_btn.setObjectName("confirmBtn")
        self.confirm_btn.clicked.connect(self._on_confirm)
        btn_row.addWidget(self.confirm_btn)

        layout.addLayout(btn_row)

    def _on_name_edited(self, text: str):
        if text.strip():
            self._user_edited_name = True

    def _add_target_item(self, path: str):
        base = os.path.basename(path) or path
        item = QListWidgetItem(f"🖥️ {base}   [{path}]")
        item.setData(Qt.ItemDataRole.UserRole, path)
        item.setToolTip(path)
        self.target_list.addItem(item)
        self._update_count_label()

    def _update_count_label(self):
        count = self.target_list.count()
        self.count_lbl.setText(I18n.t("task_count_label", n=count))

    def _browse_files(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "選擇一個或多個應用程式/捷徑/腳本",
            "",
            get_file_dialog_filter()
        )
        if file_paths:
            existing = set(self.get_targets())
            for f in file_paths:
                f_norm = os.path.normpath(f)
                if f_norm not in existing:
                    self._add_target_item(f_norm)
                    existing.add(f_norm)
            self._auto_update_name()

    def _remove_selected(self):
        selected = self.target_list.selectedItems()
        if not selected:
            return
        for item in selected:
            row = self.target_list.row(item)
            self.target_list.takeItem(row)
        self._update_count_label()
        self._auto_update_name()

    def _clear_targets(self):
        self.target_list.clear()
        self._update_count_label()
        if not self._user_edited_name:
            self.name_edit.clear()

    def get_targets(self) -> List[str]:
        targets = []
        for i in range(self.target_list.count()):
            item = self.target_list.item(i)
            val = item.data(Qt.ItemDataRole.UserRole)
            if val:
                targets.append(val)
        return targets

    def _auto_update_name(self):
        if self._user_edited_name:
            return
        targets = self.get_targets()
        if not targets:
            self.name_edit.clear()
            return
        if len(targets) == 1:
            base_name = os.path.splitext(os.path.basename(targets[0]))[0]
            self.name_edit.setText(f"🚀 啟動 {base_name}")
        else:
            first_name = os.path.splitext(os.path.basename(targets[0]))[0]
            self.name_edit.setText(f"🚀 啟動 {first_name} 等 {len(targets)} 個程式")

    def _on_confirm(self):
        targets = self.get_targets()
        if not targets:
            QMessageBox.warning(self, I18n.t("task_warn_title"), I18n.t("task_warn_target"))
            return

        name = self.name_edit.text().strip()
        if not name:
            if len(targets) == 1:
                base_name = os.path.splitext(os.path.basename(targets[0]))[0]
                name = f"🚀 啟動 {base_name}"
            else:
                first_name = os.path.splitext(os.path.basename(targets[0]))[0]
                name = f"🚀 啟動 {first_name} 等 {len(targets)} 個程式"
            self.name_edit.setText(name)

        self.accept()

    def get_task_data(self) -> dict:
        targets = self.get_targets()
        return {
            "label": self.name_edit.text().strip(),
            "targets": targets,
            "target": targets[0] if targets else "",
            "trigger_animation": "random"
        }
