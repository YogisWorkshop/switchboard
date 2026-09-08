import json

LAYOUT_FILE = "layout.json"


def save_layout(scene):
    data = scene.save_to_dict()
    with open(LAYOUT_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_layout(scene):
    try:
        with open(LAYOUT_FILE, "r") as f:
            data=json.load(f)
    except FileNotFoundError:
        return
    scene.load_from_dict(data)
