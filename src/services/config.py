import json
import os
from typing import Any, Dict

class Config:
    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        # Default config path is project root
        config_path = os.path.join(os.getcwd(), "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    self._config = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"[Config] Error loading config.json: {e}")
                self._config = {}
        else:
            print(f"[Config] config.json not found at {config_path}")
            self._config = {}

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

config = Config()
