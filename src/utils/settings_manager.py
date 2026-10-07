import os
import json
import zipfile
import shutil
from typing import Optional, Tuple
from src.utils.config_loader import ConfigLoader

class SettingsBackupManager:
    @staticmethod
    def export_settings(base_dir: str, target_file: str) -> Tuple[bool, str]:
        """
        匯出應用程式設定與素材設定 (不含任何工作內容 actions)。
        支援匯出為 .json (純設定檔) 或 .zip (包含素材圖檔與音效之完整封包)。
        """
        try:
            config_loader = ConfigLoader(base_dir)
            settings = config_loader.load_settings()
            actions_data = config_loader.load_actions()

            export_dict = {
                "version": "1.0",
                "export_type": "desktop_assistant_settings",
                "language": settings.get("language", "zh"),
                "dialogue_prompt": actions_data.get("dialogue_prompt", "主人有何吩咐？"),
                "animation_groups": settings.get("animation_groups", {
                    "idle": ["train_dummy", "train_meditate"],
                    "asking": ["ask_fist", "ask_pray"],
                    "executing": ["act_punch"]
                }),
                "pomodoro": settings.get("pomodoro", {
                    "duration_minutes": 20,
                    "sound_file": ""
                }),
                "window": {
                    "idle_size": settings.get("window", {}).get("idle_size", [180, 180]),
                    "focus_size": settings.get("window", {}).get("focus_size", [320, 320]),
                    "fps": settings.get("window", {}).get("fps", 12),
                    "stay_on_top": settings.get("window", {}).get("stay_on_top", True)
                },
                "behavior": settings.get("behavior", {
                    "scale_in_place": True,
                    "idle_switch_interval_sec": 20,
                    "asking_switch_interval_sec": 15,
                    "approach_duration_ms": 450,
                    "return_duration_ms": 450
                })
            }

            if target_file.lower().endswith(".zip"):
                with zipfile.ZipFile(target_file, "w", zipfile.ZIP_DEFLATED) as zf:
                    # 1. 寫入 JSON 設定
                    zf.writestr("desktop_assistant_settings.json", json.dumps(export_dict, ensure_ascii=False, indent=2))

                    # 2. 封裝 assets 素材 (圖檔與音效)
                    assets_dir = os.path.join(base_dir, "assets")
                    if os.path.exists(assets_dir):
                        for root, _, files in os.walk(assets_dir):
                            for file in files:
                                full_p = os.path.join(root, file)
                                rel_p = os.path.relpath(full_p, base_dir)
                                zf.write(full_p, rel_p)
                return True, "已成功匯出完整設定與素材壓縮包 (.zip)！"
            else:
                with open(target_file, "w", encoding="utf-8") as f:
                    json.dump(export_dict, f, ensure_ascii=False, indent=2)
                return True, "已成功匯出應用程式設定檔 (.json)！"
        except Exception as e:
            return False, f"匯出失敗: {e}"

    @staticmethod
    def import_settings(base_dir: str, source_file: str) -> Tuple[bool, str, Optional[dict]]:
        """
        匯入應用程式設定與素材設定。
        注意：絕對不會覆蓋或變更使用者的自訂工作內容 (actions 清單完整保留)。
        """
        try:
            if not os.path.exists(source_file):
                return False, "所選檔案不存在！", None

            data = None
            if source_file.lower().endswith(".zip"):
                with zipfile.ZipFile(source_file, "r") as zf:
                    # 解壓縮 assets 目錄（若有素材）
                    for member in zf.namelist():
                        if member.startswith("assets/") or member.startswith("assets\\"):
                            target_path = os.path.join(base_dir, member)
                            os.makedirs(os.path.dirname(target_path), exist_ok=True)
                            with zf.open(member) as src, open(target_path, "wb") as dst:
                                shutil.copyfileobj(src, dst)

                    # 尋找 JSON 設定檔
                    json_name = None
                    for name in zf.namelist():
                        if name.endswith(".json"):
                            json_name = name
                            break
                    if json_name:
                        with zf.open(json_name) as f:
                            content = f.read().decode("utf-8")
                            data = json.loads(content)
                    else:
                        return False, "壓縮包內未包含任何有效的設定檔 (.json)！", None
            else:
                with open(source_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

            if not isinstance(data, dict):
                return False, "無效的設定檔格式！", None

            config_loader = ConfigLoader(base_dir)
            current_settings = config_loader.load_settings()
            current_actions = config_loader.load_actions()

            # 解析 settings (支援 export_dict 封裝格式或原始 settings.json 格式)
            imported_settings = data.get("settings", data)
            new_prompt = data.get("dialogue_prompt") or current_actions.get("dialogue_prompt", "主人有何吩咐？")

            new_lang = imported_settings.get("language", data.get("language"))
            if new_lang:
                current_settings["language"] = new_lang

            new_idle = imported_settings.get("animation_groups", {}).get("idle", current_settings.get("animation_groups", {}).get("idle", []))
            new_asking = imported_settings.get("animation_groups", {}).get("asking", current_settings.get("animation_groups", {}).get("asking", []))
            new_exec = imported_settings.get("animation_groups", {}).get("executing", current_settings.get("animation_groups", {}).get("executing", []))
            new_pomo = imported_settings.get("pomodoro", current_settings.get("pomodoro", {}))
            raw_window = imported_settings.get("window", {})
            new_window = dict(current_settings.get("window", {}))
            new_window.update(raw_window)
            if "idle_size" in imported_settings:
                new_window["idle_size"] = imported_settings["idle_size"]
            if "focus_size" in imported_settings:
                new_window["focus_size"] = imported_settings["focus_size"]
            if "fps" in imported_settings:
                new_window["fps"] = imported_settings["fps"]

            new_behavior = imported_settings.get("behavior", current_settings.get("behavior", {}))

            # 保留原有的 saved_position (若新匯入未指定)
            if "saved_position" in current_settings.get("window", {}) and "saved_position" not in raw_window:
                new_window["saved_position"] = current_settings["window"]["saved_position"]

            current_settings["window"] = new_window
            current_settings["behavior"] = new_behavior
            current_settings["pomodoro"] = new_pomo
            current_settings["animation_groups"] = {
                "idle": new_idle,
                "asking": new_asking,
                "executing": new_exec
            }
            config_loader.save_settings(current_settings)

            # 更新 actions.json 中的 dialogue_prompt 與 pomodoro 按鈕標籤，但絕對保留所有自訂工作
            current_actions["dialogue_prompt"] = new_prompt
            if new_pomo and "duration_minutes" in new_pomo:
                for act in current_actions.get("actions", []):
                    if act.get("action_type") == "pomodoro":
                        act["label"] = f"🍅 開始番茄鐘 ({new_pomo['duration_minutes']}分鐘)"
            config_loader.save_actions(current_actions)

            result_info = {
                "dialogue_prompt": new_prompt,
                "animation_groups": current_settings["animation_groups"],
                "pomodoro": new_pomo,
                "language": current_settings.get("language", "zh"),
                "fps": current_settings.get("window", {}).get("fps", 12),
                "settings": current_settings
            }
            return True, "設定與素材已成功匯入！\n（您的自訂工作清單完整保留不受影響）", result_info
        except Exception as e:
            return False, f"匯入失敗: {e}", None
