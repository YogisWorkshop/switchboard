from tile import Empty, Button
from turnout import TurnoutRight, TurnoutLeft, Turnout3Way, Signal
from straight import Straight, StraightBumper, Diagonal, DiagonalDouble, TrackButton

TILE_CLASSES = {
    "TurnoutRight": TurnoutRight,
    "TurnoutLeft": TurnoutLeft,
    "Turnout3Way": Turnout3Way,
    "Empty": Empty,
    "Straight": Straight,
    "StraightBumper": StraightBumper,
    "Diagonal": Diagonal,
    "DiagonalDouble": DiagonalDouble,
    "Signal": Signal,
    "Emtpy": Empty,
    "TrackButton": TrackButton,
    "Button": Button,
}