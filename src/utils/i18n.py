from typing import Dict, Optional

class I18n:
    current_lang: str = "zh"

    TRANSLATIONS: Dict[str, Dict[str, str]] = {
        "zh": {
            # App / General
            "app_name": "桌面助手",

            # Context Menu
            "menu_reset_pos": "📍 重設位置至右下角",
            "menu_settings": "⚙️ 編輯設定與素材...",
            "menu_autostart_reg": "🚀 註冊成開機啟動",
            "menu_autostart_unreg": "🚫 註銷開機啟動",
            "menu_exit": "❌ 退出助手",

            # Tooltips & HUD
            "tooltip_idle": "桌面助手待命中",
            "tooltip_pomodoro": "桌面助手待命中\n🍅 番茄鐘專注倒數: {time}",
            "hud_idle_size": "📐 待命小圖尺寸: {w} × {h}",
            "hud_focus_size": "📐 互動大圖尺寸: {w} × {h}",

            # Autostart Messages
            "autostart_title": "開機啟動設定",
            "autostart_reg_success": "✅ 已成功註冊為開機啟動！\n下次電腦開機時桌面助手將自動現身陪伴您。",
            "autostart_unreg_success": "ℹ️ 已成功註銷開機啟動。\n電腦開機時桌面助手將不會自動執行。",
            "autostart_fail_title": "設定失敗",
            "autostart_reg_fail": "無法註冊開機啟動，請檢查安全軟體或系統權限設定。",
            "autostart_unreg_fail": "無法註銷開機啟動，請檢查系統權限設定。",

            # Pomodoro Alarm
            "pomo_alarm_prompt": "⏰ 【番茄鐘時間到】\n主人辛苦了！專注時長已滿，\n請起身活動筋骨、喝口茶休息一下吧！",
            "pomo_alarm_dismiss": "🍵 收到，去休息一下！(繼續待命)",

            # Dialogue default buttons
            "btn_add_task_dialogue": "📜 我有新工作要給你辦",
            "btn_dismiss_dialogue": "🍃 目前沒什麼事情要你做",
            "btn_pomodoro_dialogue": "🍅 開始番茄鐘 ({duration}分鐘)",
            "default_dialogue_prompt": "主人有何吩咐？",

            # Settings Dialog
            "settings_title": "⚙️ 應用程式設定、素材與番茄鐘管理",
            "settings_general_group": "⚙️ 基本與顯示設定",
            "settings_language_label": "🌐 介面語言 (Language)：",
            "settings_fps_label": "🎞️ 動畫影格率 (FPS)：",
            "settings_prompt_title": "💬 桌面助手詢問台詞設定：",
            "settings_prompt_placeholder": "請輸入點擊桌面助手時的台詞，例如：主人有何吩咐？",
            "group_idle_anims": "🧘 待命修煉素材 (Idle)",
            "group_asking_anims": "🙏 詢問對話素材 (Asking)",
            "group_exec_anims": "💥 任務執行動作 (Executing)",
            "btn_add_asset": "➕ 新增素材",
            "btn_delete_asset": "➖ 刪除",
            "group_pomo": "🍅 番茄鐘專注計時設定",
            "pomo_duration_label": "預設專注時長：",
            "pomo_unit_min": " 分鐘",
            "pomo_sound_label": "鬧鐘音效檔案：",
            "pomo_sound_placeholder": "留空時預設使用禪意罄鐘聲 (bell.wav)",
            "pomo_alarm_label": "時間到的提醒語句 (留空使用預設)：",
            "btn_browse_sound": "📂 瀏覽選擇音效檔案...",
            "btn_preview_sound": "▶️ 試聽",
            "btn_stop_sound": "⏹️ 停止",
            "pomo_hint": "💡 支援 WAV 音效。自訂音檔將自動複製至本機庫中保存。",
            "btn_export": "📤 匯出目前設定與素材...",
            "btn_import": "📥 匯入設定檔/素材包...",
            "btn_save": "💾 儲存並套用",
            "btn_cancel": "❌ 取消",
            "warn_min_one_asset": "每個狀態群組至少需保留 1 組動作素材！",
            "warn_cant_delete": "無法刪除",
            "export_dialog_title": "匯出應用程式與素材設定",
            "import_dialog_title": "選擇要匯入的設定檔或素材包",
            "export_success": "匯出成功",
            "export_fail": "匯出失敗",
            "import_success": "匯入成功",
            "import_fail": "匯入失敗",
            "save_path_label": "儲存路徑：{path}",

            # Task Dialog
            "task_dialog_title": "指派新工作",
            "task_header": "📜 交代桌面助手執行新任務",
            "task_name_label": "工作內容 / 按鈕文字：",
            "task_name_placeholder": "例如：開台準備 (OBS + MOZ-3) / 啟動常用環境",
            "task_targets_label": "要同步啟動的應用程式清單：",
            "task_count_label": "已加入 {n} 個項目",
            "btn_browse_exe": "➕ 瀏覽選擇檔案 (支援多選)...",
            "btn_remove_target": "➖ 移除所選",
            "btn_clear_targets": "🗑️ 清空",
            "btn_confirm_task": "確認交代此工作",
            "btn_cancel_task": "取消",
            "task_warn_title": "請填寫完整資訊",
            "task_warn_name": "請輸入工作內容/按鈕文字！",
            "task_warn_target": "請至少加入一個要啟動的應用程式！",
            "task_context_delete": "🗑️ 刪除此工作捷徑"
        },
        "en": {
            # App / General
            "app_name": "Desktop Assistant",

            # Context Menu
            "menu_reset_pos": "📍 Reset Position to Bottom-Right",
            "menu_settings": "⚙️ Settings & Assets...",
            "menu_autostart_reg": "🚀 Register Autostart",
            "menu_autostart_unreg": "🚫 Unregister Autostart",
            "menu_exit": "❌ Exit Assistant",

            # Tooltips & HUD
            "tooltip_idle": "Desktop Assistant (Idle)",
            "tooltip_pomodoro": "Desktop Assistant (Focus)\n🍅 Pomodoro: {time}",
            "hud_idle_size": "📐 Idle Size: {w} × {h}",
            "hud_focus_size": "📐 Focus Size: {w} × {h}",

            # Autostart Messages
            "autostart_title": "Autostart Settings",
            "autostart_reg_success": "✅ Successfully registered for autostart!\nThe desktop assistant will launch when Windows boots.",
            "autostart_unreg_success": "ℹ️ Successfully unregistered autostart.\nThe assistant will not launch at startup.",
            "autostart_fail_title": "Configuration Failed",
            "autostart_reg_fail": "Failed to register autostart. Please check permissions or security software.",
            "autostart_unreg_fail": "Failed to unregister autostart. Please check permissions.",

            # Pomodoro Alarm
            "pomo_alarm_prompt": "⏰ [Pomodoro Finished]\nGreat job! Focus session is complete.\nStretch your body and take a break!",
            "pomo_alarm_dismiss": "🍵 Got it, taking a break! (Resume Idle)",

            # Dialogue default buttons
            "btn_add_task_dialogue": "📜 I have a new task for you",
            "btn_dismiss_dialogue": "🍃 Nothing to do for now",
            "btn_pomodoro_dialogue": "🍅 Start Pomodoro ({duration} min)",
            "default_dialogue_prompt": "How may I help you?",

            # Settings Dialog
            "settings_title": "⚙️ App Settings, Assets & Pomodoro",
            "settings_general_group": "⚙️ General & Display Settings",
            "settings_language_label": "🌐 UI Language (介面語言):",
            "settings_fps_label": "🎞️ Animation Rate (FPS):",
            "settings_prompt_title": "💬 Assistant Dialogue Prompt:",
            "settings_prompt_placeholder": "Enter prompt when clicking the assistant, e.g., How may I help you?",
            "group_idle_anims": "🧘 Idle Animations (Idle)",
            "group_asking_anims": "🙏 Asking Animations (Asking)",
            "group_exec_anims": "💥 Action Animations (Executing)",
            "btn_add_asset": "➕ Add Asset",
            "btn_delete_asset": "➖ Delete",
            "group_pomo": "🍅 Pomodoro Timer Settings",
            "pomo_duration_label": "Default Duration:",
            "pomo_unit_min": " min",
            "pomo_sound_label": "Alarm Sound File:",
            "pomo_sound_placeholder": "Default: Zen Bell (bell.wav) if empty",
            "pomo_alarm_label": "Time's-up message (leave empty for default):",
            "btn_browse_sound": "📂 Browse Sound File...",
            "btn_preview_sound": "▶️ Preview",
            "btn_stop_sound": "⏹️ Stop",
            "pomo_hint": "💡 Supports WAV audio. Custom audio will be copied to local library.",
            "btn_export": "📤 Export Settings & Assets...",
            "btn_import": "📥 Import Settings/Assets...",
            "btn_save": "💾 Save & Apply",
            "btn_cancel": "❌ Cancel",
            "warn_min_one_asset": "Each state group must retain at least one animation asset!",
            "warn_cant_delete": "Cannot Delete",
            "export_dialog_title": "Export Settings and Assets",
            "import_dialog_title": "Select Settings or Asset Package to Import",
            "export_success": "Export Successful",
            "export_fail": "Export Failed",
            "import_success": "Import Successful",
            "import_fail": "Import Failed",
            "save_path_label": "Saved to: {path}",

            # Task Dialog
            "task_dialog_title": "Assign New Task",
            "task_header": "📜 Assign New Task to Assistant",
            "task_name_label": "Task Name / Button Label:",
            "task_name_placeholder": "e.g., Stream Setup (OBS + MOZ-3) / Dev Environment",
            "task_targets_label": "Applications to Launch in Sync:",
            "task_count_label": "{n} items added",
            "btn_browse_exe": "➕ Browse Files (Multi-select)...",
            "btn_remove_target": "➖ Remove Selected",
            "btn_clear_targets": "🗑️ Clear",
            "btn_confirm_task": "Confirm Task",
            "btn_cancel_task": "Cancel",
            "task_warn_title": "Incomplete Information",
            "task_warn_name": "Please enter task name/button label!",
            "task_warn_target": "Please add at least one application to launch!",
            "task_context_delete": "🗑️ Delete this Task"
        }
    }

    @classmethod
    def set_language(cls, lang: str):
        if lang in cls.TRANSLATIONS:
            cls.current_lang = lang

    @classmethod
    def get_language(cls) -> str:
        return cls.current_lang

    @classmethod
    def t(cls, key: str, lang: Optional[str] = None, **kwargs) -> str:
        target_lang = lang or cls.current_lang
        text = cls.TRANSLATIONS.get(target_lang, {}).get(key)
        if text is None:
            text = cls.TRANSLATIONS.get("zh", {}).get(key, key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text
