import json
import os
from pathlib import Path

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "watch_folders": ["."],
    "provider": "openai",
    "model": "gpt-4o-mini",
    "buddy_size": "large",
    "personality": "You are Fuwa, a cute, slightly sarcastic, and extremely motivating axolotl terminal companion. You observe the user's coding folders and make comments. If they slack off, make them feel guilty. If they work hard, praise them. Your comments should be short (1-2 sentences).",
    "requests_per_min": 0
}

_cached_config = None

def load_config():
    global _cached_config
    if _cached_config is not None:
        return _cached_config

    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        _cached_config = DEFAULT_CONFIG.copy()
        return _cached_config

    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            # Ensure all default keys exist
            for k, v in DEFAULT_CONFIG.items():
                if k not in config:
                    config[k] = v
            _cached_config = config
            return config
    except Exception as e:
        print(f"Error loading config: {e}")
        return DEFAULT_CONFIG.copy()

def save_config(config):
    global _cached_config
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        mode = 0o600
        fd = os.open(CONFIG_FILE, flags, mode)
        with os.fdopen(fd, "w") as f:
            json.dump(config, f, indent=4)
        os.chmod(CONFIG_FILE, 0o600)  # Ensure permissions are set correctly even if file existed
        _cached_config = config
    except Exception as e:
        print(f"Error saving config: {e}")

def update_config(key, value):
    config = load_config()
    config[key] = value
    save_config(config)
