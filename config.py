import json
import os
from pathlib import Path

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "watch_folders": ["."],
    "provider": "openai",
    "model": "gpt-4o-mini",
    "api_key": "",
    "personality": "You are Fuwa, a cute, slightly sarcastic, and extremely motivating axolotl terminal companion. You observe the user's coding folders and make comments. If they slack off, make them feel guilty. If they work hard, praise them. Your comments should be short (1-2 sentences)."
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            # Ensure all default keys exist
            for k, v in DEFAULT_CONFIG.items():
                if k not in config:
                    config[k] = v
            return config
    except Exception as e:
        print(f"Error loading config: {e}")
        return DEFAULT_CONFIG.copy()

def save_config(config):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error saving config: {e}")

def update_config(key, value):
    config = load_config()
    config[key] = value
    save_config(config)
