from tile import Empty
from turnout import TurnoutRight, TurnoutLeft, Turnout3Way
from straight import Straight, Diagonal

TILE_CLASSES = {
    "TurnoutRight": TurnoutRight,
    "TurnoutLeft": TurnoutLeft,
    "Turnout3Way": Turnout3Way,
    "Empty": Empty,
    "Straight": Straight,
    "Diagonal": Diagonal,
}