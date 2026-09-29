import os
from enum import Enum, auto

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

GEAR_ICON_PATH = os.path.join(ASSETS_DIR, "gear.svg")
GEAR_SIZE = 40

GRID_SIZE = 80
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 800

TILE_ICON_SIZE = 80

PANEL_COLS = SCREEN_WIDTH // GRID_SIZE
PANEL_ROWS = SCREEN_HEIGHT // GRID_SIZE

BACKGROUND_COLOR = "#B8DBB7"

TILE_COLOR = "#99cc99"
TILE_BORDER_COLOR = "#808080"
TILE_BORDER_WIDTH = 0
TRACK_COLOR = "#000000"
INACTIVE_TRACK_COLOR = "#999999"
SELECTION_HIGHLIGHT_COLOR = "#00ffff"

BUTTON_COLOR_RED_ON = "#ff3333"
BUTTON_COLOR_RED_OFF = "#660000"
BUTTON_COLOR_GREEN_ON = "#33cc33"
BUTTON_COLOR_GREEN_OFF = "#004d00"
BUTTON_COLOR_BLUE_ON = "#3399ff"
BUTTON_COLOR_BLUE_OFF = "#003366"

SIGNAL_COLOR_RED = "#FF3333"
SIGNAL_COLOR_GREEN = "#33CC33"


TRACK_WIDTH = 12

APPEARANCE_SPECS = [
    {"key": "TILE_COLOR", "label": "Tile Color", "type": "color"},
    {"key": "BACKGROUND_COLOR", "label": "Background Color", "type": "color"},
    {"key": "TRACK_COLOR", "label": "Track Color", "type": "color"},
    {"key": "INACTIVE_TRACK_COLOR", "label": "Inactive Track Color", "type": "color"},
    {"key": "TRACK_WIDTH", "label": "Track Width", "type": int, "min": 1, "max": 30},
    {"key": "TILE_BORDER_WIDTH", "label": "Tile Border Width", "type": int, "min": 0, "max": 10},
    {"key": "TILE_BORDER_COLOR", "label": "Tile Border Color", "type": "color"},
    {"key": "SELECTION_HIGHLIGHT_COLOR", "label": "Selection Highlight Color", "type": "color"},
]

SYSTEM_SETTINGS = [
    {"key": "SCREEN_WIDTH", "label": "Screen Width", "type": int, "min": 320, "max": 7680},
    {"key": "SCREEN_HEIGHT", "label": "Screen Height", "type": int, "min": 240, "max": 4320},
    {"key": "GRID_SIZE", "label": "Grid Size", "type": int, "min": 20, "max": 300}
]

SETTINGS_SPECS = APPEARANCE_SPECS + SYSTEM_SETTINGS

DEFAULT_SETTINGS = {spec["key"]: globals()[spec["key"]] for spec in SETTINGS_SPECS}

class PanelMode(Enum):
    EDIT = auto()
    OPERATE = auto()

class Tool(Enum):
    SELECT = auto()
    PLACE = auto()
    MOVE = auto()

def recompute_derived_settings():
    global PANEL_COLS, PANEL_ROWS
    PANEL_COLS = SCREEN_WIDTH // GRID_SIZE
    PANEL_ROWS = SCREEN_HEIGHT // GRID_SIZE