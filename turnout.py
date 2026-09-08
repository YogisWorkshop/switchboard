from tile import Tile

class TurnoutRight(Tile):
    property_specs = [
        {"key": "label", "label": "Label", "type": str, "max_length": 10, "default": ""},
        {"key": "name", "label": "Name", "type": str, "default": ""}, 
        {"key": "address", "label": "Address", "type": int, "default": 0},
        {"key": "protocol", "label": "Protocol", "type": "choice", "choices": ["DCC", "MM"], "default": "DCC"}
        ]

    def __init__(self):
        super().__init__()
        self.thrown = False

    def on_tap(self):
         self.thrown = not self.thrown

    def draw(self, painter):
        self.draw_tile_background(painter)

        if self.thrown:
            self.draw_line(painter, "W", "E", active=False)
            self.draw_line(painter, "W", "S", active=True)
        else:
            self.draw_line(painter, "W", "S", active=False)
            self.draw_line(painter, "W", "E", active=True)


class TurnoutLeft(Tile):
    property_specs = [
        {"key": "label", "label": "Label", "type": str, "max_length": 10, "default": ""},
        {"key": "name", "label": "Name", "type": str, "default": ""}, 
        {"key": "address", "label": "Address", "type": int, "default": 0},
        {"key": "protocol", "label": "Protocol", "type": "choice", "choices": ["DCC", "MM"], "default": "DCC"}
        ]

    def __init__(self):
        super().__init__()
        self.thrown = False

    def on_tap(self):
         self.thrown = not self.thrown

    def draw(self, painter):
        self.draw_tile_background(painter)

        if self.thrown:
            self.draw_line(painter, "W", "E", active=False)
            self.draw_line(painter, "W", "N", active=True)
        else:
            self.draw_line(painter, "W", "N", active=False)
            self.draw_line(painter, "W", "E", active=True)


class Turnout3Way(Tile):
    def __init__(self):
        super().__init__()
        self._pattern = [0, 1, 0, 2]
        self._index = 0
        self.thrown_state = 0

    def on_tap(self):
        self._index = (self._index +1) % 4
        self.thrown_state = self._pattern[self._index]
        
    def draw(self, painter):
        self.draw_tile_background(painter)

        if self.thrown_state == 1:
            self.draw_line(painter, "W", "E", active=False)
            self.draw_line(painter, "W", "S", active=False)
            self.draw_line(painter, "W", "N", active=True)
        elif self.thrown_state == 2:
            self.draw_line(painter, "W", "E", active=False)
            self.draw_line(painter, "W", "N", active=False)
            self.draw_line(painter, "W", "S", active=True)
        else:
            self.draw_line(painter, "W", "N", active=False)
            self.draw_line(painter, "W", "S", active=False)
            self.draw_line(painter, "W", "E", active=True)


     
