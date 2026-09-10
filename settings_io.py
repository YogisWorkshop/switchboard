import json
import os

import config
from config import SETTINGS_SPECS

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

def save_settings(overrides=None):
    data = {spec["key"]: getattr(config, spec["key"]) for spec in SETTINGS_SPECS}
    if overrides:
        data.update(overrides)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_settings():
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        return

    for key, value in data.items():
        setattr(config, key, value)