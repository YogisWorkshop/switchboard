import json
import os

LAYOUT_FILE = "layout.json"


def save_layout(scene):
    data = scene.save_to_dict()
    text = json.dumps(data, indent=2)       # if this fails, the real file is untouched
    temp_file = LAYOUT_FILE + ".tmp"
    with open(temp_file, "w") as f:
        f.write(text)
    os.replace(temp_file, LAYOUT_FILE)      # swap the finished file in, in one step

def load_layout(scene):
    try:
        with open(LAYOUT_FILE, "r") as f:
            data=json.load(f)
    except FileNotFoundError:
        return
    scene.load_from_dict(data)
