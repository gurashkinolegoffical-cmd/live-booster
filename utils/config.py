import json
import os

DEFAULT_SETTINGS = {
    "theme": "system",
    "notifications": True,
    "tracker_interval": 30,
    "game_time_threshold": 15,
    "language": "ru",
    "sound_enabled": True,
    "vibration": True,
    "payday_interval": 60,
    "vk_token": "",
    "username": "игрок"
}

class ConfigManager:
    def __init__(self, path="config.json"):
        self.path = path
        self.data = DEFAULT_SETTINGS.copy()
        self.load()

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self.data.update(loaded)
            except:
                pass

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except:
            pass

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()