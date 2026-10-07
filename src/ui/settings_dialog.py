import os
import shutil
from typing import List, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox, QFileDialog, QGroupBox,
    QFrame, QSpinBox, QComboBox, QPlainTextEdit
)
from PyQt6.QtCore import Qt
from src.utils.i18n import I18n
from src.platform import play_sound, play_beep

class SettingsDialog(QDialog):
    def __init__(
        self,
        base_dir: str,
        current_prompt: str,
        idle_anims: List[str],
        asking_anims: List[str],
        exec_anims: List[str] = None,
        pomodoro_duration: int = 20,
        pomodoro_sound: str = "",
        pomodoro_alarm_message: str = "",
        current_language: str = "zh",
        current_fps: int = 12,
        parent=None
    ):
        super().__init__(parent)
        self.base_dir = base_dir
        self.assets_dir = os.path.join(base_dir, "assets", "animations")
        self.default_sound = os.path.join(base_dir, "assets", "audio", "bell.wav")
        self.initial_language = current_language
        self.current_language = current_language
        I18n.set_language(current_language)

        if exec_anims is None:
            exec_anims = ["act_punch"]

        self.setFixedWidth(780)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

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
            QLineEdit, QSpinBox, QComboBox, QPlainTextEdit {
                background-color: #2b2b30;
                color: #ffffff;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QPlainTextEdit:focus {
                border: 1px solid #d4af37;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #2b2b30;
                color: #ffffff;
                selection-background-color: #d4af37;
                selection-color: #1a1a1a;
            }
            QGroupBox {
                border: 1px solid #856424;
                border-radius: 8px;
                margin-top: 10px;
                font-weight: bold;
                color: #f7e7b4;
                padding-top: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
            }
            QListWidget {
                background-color: #1a1a1d;
                border: 1px solid #3f3f46;
                border-radius: 6px;
                color: #f4f4f5;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 4px 6px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #d4af37;
                color: #18181b;
                font-weight: bold;
            }
            QPushButton.opBtn {
                background-color: #2d2d32;
                border: 1px solid #52525b;
                border-radius: 6px;
                color: #d4d4d8;
                padding: 5px 10px;
                font-size: 12px;
            }
            QPushButton.opBtn:hover {
                background-color: #3f3f46;
                color: #ffffff;
                border-color: #d4af37;
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
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        # 0. 基本與顯示設定 (語言選擇 & 動畫 FPS)
        general_row = QHBoxLayout()
        general_row.setSpacing(16)

        self.lang_label = QLabel(self)
        general_row.addWidget(self.lang_label)

        self.lang_combo = QComboBox(self)
        self.lang_combo.addItem("繁體中文 (Traditional Chinese)", "zh")
        self.lang_combo.addItem("English (英文)", "en")
        idx = self.lang_combo.findData(self.current_language)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)
        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)
        general_row.addWidget(self.lang_combo)

        general_row.addSpacing(20)

        self.fps_label = QLabel(self)
        general_row.addWidget(self.fps_label)

        self.fps_spin = QSpinBox(self)
        self.fps_spin.setRange(1, 60)
        self.fps_spin.setValue(max(1, min(60, current_fps)))
        self.fps_spin.setSuffix(" FPS")
        self.fps_spin.setFixedWidth(100)
        general_row.addWidget(self.fps_spin)

        general_row.addStretch()
        layout.addLayout(general_row)

        # 1. 對話台詞設定
        self.prompt_title_lbl = QLabel(self)
        self.prompt_title_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #f7e7b4;")
        layout.addWidget(self.prompt_title_lbl)

        self.prompt_edit = QLineEdit(self)
        self.prompt_edit.setText(current_prompt)
        layout.addWidget(self.prompt_edit)

        # 2. 動作素材管理 (三欄並排: 待命修煉 / 詢問對話 / 任務執行)
        anims_row = QHBoxLayout()
        anims_row.setSpacing(12)

        self.idle_box = self._create_anim_group_box(idle_anims, "idle")
        anims_row.addWidget(self.idle_box)

        self.asking_box = self._create_anim_group_box(asking_anims, "asking")
        anims_row.addWidget(self.asking_box)

        self.exec_box = self._create_anim_group_box(exec_anims, "executing")
        anims_row.addWidget(self.exec_box)

        layout.addLayout(anims_row)

        # 3. 番茄鐘設定分組
        self.pomo_box = QGroupBox(self)
        pomo_layout = QVBoxLayout(self.pomo_box)
        pomo_layout.setSpacing(10)

        pomo_row1 = QHBoxLayout()
        self.pomo_dur_lbl = QLabel(self.pomo_box)
        pomo_row1.addWidget(self.pomo_dur_lbl)
        self.pomo_spin = QSpinBox(self.pomo_box)
        self.pomo_spin.setRange(1, 180)
        self.pomo_spin.setValue(max(1, pomodoro_duration))
        self.pomo_spin.setFixedWidth(110)
        pomo_row1.addWidget(self.pomo_spin)
        pomo_row1.addStretch()
        pomo_layout.addLayout(pomo_row1)

        pomo_row2 = QHBoxLayout()
        self.pomo_sound_lbl = QLabel(self.pomo_box)
        pomo_row2.addWidget(self.pomo_sound_lbl)
        self.pomo_sound_edit = QLineEdit(self.pomo_box)
        self.pomo_sound_edit.setText(pomodoro_sound)
        pomo_row2.addWidget(self.pomo_sound_edit)

        self.browse_sound_btn = QPushButton(self.pomo_box)
        self.browse_sound_btn.setProperty("class", "opBtn")
        self.browse_sound_btn.clicked.connect(self._browse_sound)
        pomo_row2.addWidget(self.browse_sound_btn)

        self.preview_sound_btn = QPushButton(self.pomo_box)
        self.preview_sound_btn.setProperty("class", "opBtn")
        self.preview_sound_btn.clicked.connect(self._preview_sound)
        pomo_row2.addWidget(self.preview_sound_btn)

        pomo_layout.addLayout(pomo_row2)

        # 番茄鐘時間到的提醒語句 (留空 = 使用目前語言的預設文字)
        self.pomo_alarm_lbl = QLabel(self.pomo_box)
        pomo_layout.addWidget(self.pomo_alarm_lbl)
        self.pomo_alarm_edit = QPlainTextEdit(self.pomo_box)
        self.pomo_alarm_edit.setPlainText(pomodoro_alarm_message or "")
        self.pomo_alarm_edit.setFixedHeight(76)
        pomo_layout.addWidget(self.pomo_alarm_edit)

        layout.addWidget(self.pomo_box)

        # 提示文字
        self.hint_lbl = QLabel(self)
        self.hint_lbl.setStyleSheet("color: #9ca3af; font-size: 11px;")
        layout.addWidget(self.hint_lbl)

        # 4. 底部備份與確定/取消按鈕
        btn_row = QHBoxLayout()

        self.export_btn = QPushButton(self)
        self.export_btn.setProperty("class", "opBtn")
        self.export_btn.clicked.connect(self._on_export)
        btn_row.addWidget(self.export_btn)

        self.import_btn = QPushButton(self)
        self.import_btn.setProperty("class", "opBtn")
        self.import_btn.clicked.connect(self._on_import)
        btn_row.addWidget(self.import_btn)

        btn_row.addStretch()

        self.cancel_btn = QPushButton(self)
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.cancel_btn)

        self.confirm_btn = QPushButton(self)
        self.confirm_btn.setObjectName("confirmBtn")
        self.confirm_btn.clicked.connect(self._on_save)
        btn_row.addWidget(self.confirm_btn)

        layout.addLayout(btn_row)

        # 初始化動態多語言文字
        self._retranslate_ui()

    def _on_language_changed(self):
        new_lang = self.lang_combo.currentData()
        self.current_language = new_lang
        I18n.set_language(new_lang)
        self._retranslate_ui()

    def _retranslate_ui(self):
        """根據目前語言即時更新視窗所有文字與標籤"""
        self.setWindowTitle(I18n.t("settings_title"))
        self.lang_label.setText(I18n.t("settings_language_label"))
        self.fps_label.setText(I18n.t("settings_fps_label"))
        self.prompt_title_lbl.setText(I18n.t("settings_prompt_title"))
        self.prompt_edit.setPlaceholderText(I18n.t("settings_prompt_placeholder"))

        self.idle_box.setTitle(I18n.t("group_idle_anims"))
        self.asking_box.setTitle(I18n.t("group_asking_anims"))
        self.exec_box.setTitle(I18n.t("group_exec_anims"))

        self.add_idle_btn.setText(I18n.t("btn_add_asset"))
        self.del_idle_btn.setText(I18n.t("btn_delete_asset"))
        self.add_asking_btn.setText(I18n.t("btn_add_asset"))
        self.del_asking_btn.setText(I18n.t("btn_delete_asset"))
        self.add_exec_btn.setText(I18n.t("btn_add_asset"))
        self.del_exec_btn.setText(I18n.t("btn_delete_asset"))

        self.pomo_box.setTitle(I18n.t("group_pomo"))
        self.pomo_dur_lbl.setText(I18n.t("pomo_duration_label"))
        self.pomo_spin.setSuffix(I18n.t("pomo_unit_min"))
        self.pomo_sound_lbl.setText(I18n.t("pomo_sound_label"))
        self.pomo_sound_edit.setPlaceholderText(I18n.t("pomo_sound_placeholder"))
        self.browse_sound_btn.setText(I18n.t("btn_browse_sound"))
        self.preview_sound_btn.setText(I18n.t("btn_preview_sound"))
        self.pomo_alarm_lbl.setText(I18n.t("pomo_alarm_label"))
        self.pomo_alarm_edit.setPlaceholderText(I18n.t("pomo_alarm_prompt"))

        self.hint_lbl.setText(I18n.t("pomo_hint"))
        self.export_btn.setText(I18n.t("btn_export"))
        self.import_btn.setText(I18n.t("btn_import"))
        self.cancel_btn.setText(I18n.t("btn_cancel"))
        self.confirm_btn.setText(I18n.t("btn_save"))

    def _create_anim_group_box(self, initial_items: List[str], group_key: str) -> QGroupBox:
        box = QGroupBox(self)
        box_layout = QVBoxLayout(box)
        box_layout.setSpacing(6)

        list_widget = QListWidget(box)
        for item in initial_items:
            list_widget.addItem(item)
        box_layout.addWidget(list_widget)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        add_btn = QPushButton(box)
        add_btn.setProperty("class", "opBtn")
        btn_row.addWidget(add_btn)

        del_btn = QPushButton(box)
        del_btn.setProperty("class", "opBtn")
        btn_row.addWidget(del_btn)

        box_layout.addLayout(btn_row)

        if group_key == "idle":
            self.idle_list = list_widget
            self.add_idle_btn = add_btn
            self.del_idle_btn = del_btn
            group_name = "待命動作"
        elif group_key == "asking":
            self.asking_list = list_widget
            self.add_asking_btn = add_btn
            self.del_asking_btn = del_btn
            group_name = "詢問動作"
        else:
            self.exec_list = list_widget
            self.add_exec_btn = add_btn
            self.del_exec_btn = del_btn
            group_name = "執行動作"

        add_btn.clicked.connect(lambda: self._add_animation(list_widget, group_name))
        del_btn.clicked.connect(lambda: self._remove_animation(list_widget, group_name))

        return box

    def _add_animation(self, list_widget: QListWidget, group_name: str):
        folder = QFileDialog.getExistingDirectory(
            self,
            f"選擇【{group_name}】的動畫序列幀資料夾",
            self.assets_dir
        )
        if not folder:
            return

        has_images = any(
            f.lower().endswith(('.png', '.webp', '.jpg', '.jpeg'))
            for f in os.listdir(folder)
        )
        if not has_images:
            QMessageBox.warning(self, "無效資料夾", "選取的資料夾內找不到任何圖片檔案 (.png / .webp)！")
            return

        folder_name = os.path.basename(folder)
        dest_folder = os.path.join(self.assets_dir, folder_name)
        if os.path.abspath(folder) != os.path.abspath(dest_folder):
            if not os.path.exists(dest_folder):
                try:
                    shutil.copytree(folder, dest_folder)
                except Exception as e:
                    QMessageBox.critical(self, "複製失敗", f"無法將素材資料夾複製至 assets/animations: {e}")
                    return

        existing_items = [list_widget.item(i).text() for i in range(list_widget.count())]
        if folder_name in existing_items:
            QMessageBox.information(self, "重複素材", f"素材 '{folder_name}' 已經在清單中囉！")
            return

        list_widget.addItem(folder_name)

    def _remove_animation(self, list_widget: QListWidget, group_name: str):
        current_count = list_widget.count()
        if current_count <= 1:
            QMessageBox.warning(
                self,
                I18n.t("warn_cant_delete"),
                I18n.t("warn_min_one_asset")
            )
            return

        current_row = list_widget.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "請選取項目", "請先在清單中點選要移除的素材。")
            return

        item_text = list_widget.item(current_row).text()
        reply = QMessageBox.question(
            self,
            "確認移除",
            f"確定要從【{group_name}】清單中移除素材 '{item_text}' 嗎？\n（實體檔案仍會保留在資料夾中）",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            list_widget.takeItem(current_row)

    def _browse_sound(self):
        sound_path, _ = QFileDialog.getOpenFileName(
            self,
            "選擇番茄鐘鬧鐘音效檔案",
            os.path.dirname(self.default_sound),
            "音效檔案 (*.wav *.mp3 *.ogg);;所有檔案 (*.*)"
        )
        if sound_path:
            self.pomo_sound_edit.setText(sound_path)

    def _preview_sound(self):
        path = self.pomo_sound_edit.text().strip()
        if not path or not os.path.exists(path):
            path = self.default_sound

        if path and os.path.exists(path):
            success = play_sound(path, parent=self)
            if not success:
                QMessageBox.warning(self, "播放失敗", "無法播放音效檔案。")
        else:
            play_beep()

    def _on_save(self):
        prompt = self.prompt_edit.text().strip()
        if not prompt:
            prompt = I18n.t("default_dialogue_prompt")

        if self.idle_list.count() < 1 or self.asking_list.count() < 1 or self.exec_list.count() < 1:
            QMessageBox.warning(self, I18n.t("warn_cant_delete"), I18n.t("warn_min_one_asset"))
            return

        self.accept()

    def reject(self):
        I18n.set_language(self.initial_language)
        super().reject()

    def get_prompt(self) -> str:
        return self.prompt_edit.text().strip() or I18n.t("default_dialogue_prompt")

    def get_idle_anims(self) -> List[str]:
        return [self.idle_list.item(i).text() for i in range(self.idle_list.count())]

    def get_asking_anims(self) -> List[str]:
        return [self.asking_list.item(i).text() for i in range(self.asking_list.count())]

    def get_exec_anims(self) -> List[str]:
        return [self.exec_list.item(i).text() for i in range(self.exec_list.count())]

    def get_pomodoro_settings(self) -> dict:
        return {
            "duration_minutes": self.pomo_spin.value(),
            "sound_file": self.pomo_sound_edit.text().strip(),
            "alarm_message": self.pomo_alarm_edit.toPlainText().strip()
        }

    def get_language(self) -> str:
        return self.lang_combo.currentData() or "zh"

    def get_fps(self) -> int:
        return self.fps_spin.value()

    def _persist_current_to_settings(self):
        from src.utils.config_loader import ConfigLoader
        loader = ConfigLoader(self.base_dir)
        settings = loader.load_settings()
        actions = loader.load_actions()

        actions["dialogue_prompt"] = self.get_prompt()
        settings["language"] = self.get_language()
        if "window" not in settings:
            settings["window"] = {}
        settings["window"]["fps"] = self.get_fps()

        settings["animation_groups"] = {
            "idle": self.get_idle_anims(),
            "asking": self.get_asking_anims(),
            "executing": self.get_exec_anims()
        }
        settings["pomodoro"] = self.get_pomodoro_settings()

        loader.save_settings(settings)
        loader.save_actions(actions)

    def _on_export(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            I18n.t("export_dialog_title"),
            "desktop_assistant_settings.json",
            "JSON (*.json);;ZIP (*.zip)"
        )
        if file_path:
            from src.utils.settings_manager import SettingsBackupManager
            self._persist_current_to_settings()
            ok, msg = SettingsBackupManager.export_settings(self.base_dir, file_path)
            if ok:
                path_info = I18n.t("save_path_label", path=file_path)
                QMessageBox.information(self, I18n.t("export_success"), f"✅ {msg}\n\n{path_info}")
            else:
                QMessageBox.warning(self, I18n.t("export_fail"), f"❌ {msg}")

    def _on_import(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            I18n.t("import_dialog_title"),
            "",
            "Support (*.json *.zip);;JSON (*.json);;ZIP (*.zip);;All (*.*)"
        )
        if file_path:
            from src.utils.settings_manager import SettingsBackupManager
            ok, msg, result = SettingsBackupManager.import_settings(self.base_dir, file_path)
            if ok and result:
                self.prompt_edit.setText(result["dialogue_prompt"])

                anim_groups = result["animation_groups"]
                self._reload_list_widget(self.idle_list, anim_groups.get("idle", []))
                self._reload_list_widget(self.asking_list, anim_groups.get("asking", []))
                self._reload_list_widget(self.exec_list, anim_groups.get("executing", []))

                pomo = result.get("pomodoro", {})
                self.pomo_spin.setValue(pomo.get("duration_minutes", 20))
                self.pomo_sound_edit.setText(pomo.get("sound_file", ""))
                self.pomo_alarm_edit.setPlainText(pomo.get("alarm_message", ""))

                # 匯入語言更新
                imported_lang = result.get("language")
                if imported_lang:
                    idx = self.lang_combo.findData(imported_lang)
                    if idx >= 0:
                        self.lang_combo.setCurrentIndex(idx)

                # 匯入 FPS 更新
                imported_fps = result.get("fps")
                if imported_fps:
                    self.fps_spin.setValue(int(imported_fps))

                # 若父視窗存在，通知即時載入最新設定（包含尺寸、素材、語言與 FPS）
                if self.parent() and hasattr(self.parent(), "_reload_from_settings"):
                    self.parent()._reload_from_settings()

                QMessageBox.information(self, I18n.t("import_success"), f"✅ {msg}")
            else:
                QMessageBox.warning(self, I18n.t("import_fail"), f"❌ {msg}")

    def _reload_list_widget(self, list_widget: QListWidget, items: list):
        list_widget.clear()
        for item in items:
            list_widget.addItem(item)
