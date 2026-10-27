from tile import Button
from turnout import TurnoutRight, TurnoutLeft, Turnout3Way, Signal
from straight import (Straight, StraightBumper, Diagonal, DiagonalDouble, 
                      TrackButton, CrossingRight, CrossingLeft)
from station_tiles import ConnectionTile, PowerTile

TILE_CLASSES = {
    "TurnoutRight": TurnoutRight,
    "TurnoutLeft": TurnoutLeft,
    "Turnout3Way": Turnout3Way,
    "Straight": Straight,
    "StraightBumper": StraightBumper,
    "Diagonal": Diagonal,
    "DiagonalDouble": DiagonalDouble,
    "CrossingRight": CrossingRight,
    "CrossingLeft": CrossingLeft,
    "Signal": Signal,
    "TrackButton": TrackButton,
    "Button": Button,
    "ConnectionTile": ConnectionTile,
    "PowerTile": PowerTile,
}