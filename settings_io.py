import json
import os

import config
from config import SETTINGS_SPECS

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

def save_settings(overrides=None):
    data = {spec["key"]: getattr(config, spec["key"]) for spec in SETTINGS_SPECS}
    if overrides:
            data.update(overrides)
    text = json.dumps(data, indent=2)       # if this fails, the real file is untouched
    temp_file = SETTINGS_FILE + ".tmp"
    with open(temp_file, "w") as f:
        f.write(text)
    os.replace(temp_file, SETTINGS_FILE)

def load_settings():
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        return

    for key, value in data.items():
        setattr(config, key, value)

def load_saved_settings():
    try:
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
            return {}