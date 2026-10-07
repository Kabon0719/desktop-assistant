import json
import os
from src.platform import get_config_dir

class ConfigLoader:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.config_dir = get_config_dir(base_dir)
        self.actions_file = os.path.join(self.config_dir, "actions.json")
        self.settings_file = os.path.join(self.config_dir, "settings.json")
        
    def load_actions(self) -> dict:
        if os.path.exists(self.actions_file):
            try:
                with open(self.actions_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[ConfigLoader] Error loading actions.json: {e}")
        return {"dialogue_prompt": "師主有何吩咐？", "actions": []}

    def save_actions(self, actions_data: dict) -> bool:
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.actions_file, "w", encoding="utf-8") as f:
                json.dump(actions_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[ConfigLoader] Error saving actions.json: {e}")
            return False

    def load_settings(self) -> dict:
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[ConfigLoader] Error loading settings.json: {e}")
        return {}

    def save_settings(self, settings_data: dict) -> bool:
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(settings_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[ConfigLoader] Error saving settings.json: {e}")
            return False
