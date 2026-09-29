from tile import Button #Empty
from turnout import TurnoutRight, TurnoutLeft, Turnout3Way, Signal
from straight import (Straight, StraightBumper, Diagonal, DiagonalDouble, 
                      TrackButton, CrossingRight, CrossingLeft)

TILE_CLASSES = {
    "TurnoutRight": TurnoutRight,
    "TurnoutLeft": TurnoutLeft,
    "Turnout3Way": Turnout3Way,
    #"Empty": Empty,
    "Straight": Straight,
    "StraightBumper": StraightBumper,
    "Diagonal": Diagonal,
    "DiagonalDouble": DiagonalDouble,
    "CrossingRight": CrossingRight,
    "CrossingLeft": CrossingLeft,
    "Signal": Signal,
    #"Emtpy": Empty,
    "TrackButton": TrackButton,
    "Button": Button,
}