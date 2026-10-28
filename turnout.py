import config
from PySide6.QtGui import QBrush, QColor, QPen, QPainter
from PySide6.QtCore import Qt, QRectF, QPointF, QTimer
from tile import Tile

class Turnout(Tile):
    """A two-way turnout that a command station can drive.

    Several of these can share one address: the primary holds the address,
    and secondaries name it in "Linked To". The command that goes to the
    station is then the PARITY of the group: diverging when an odd number of
    the tiles are thrown, straight when an even number are.
    """
    property_specs = [
        {"key": "label", "label": "Label", "type": str, "max_length": 10, "default": ""},
        {"key": "name", "label": "Name", "type": str, "default": ""},
        {"key": "address", "label": "Address", "type": int, "default": 0},
        {"key": "protocol", "label": "Protocol", "type": "choice", "choices": ["DCC", "MM"], "default": "DCC"},
        {"key": "invert", "label": "Invert Display", "type": bool, "default": False},
        {"key": "linked_to", "label": "Linked To", "type": str, "max_length": 10, "default": ""},
    ]
    branch = "S"          # which corner the diverging track leaves toward

    def __init__(self):
        super().__init__()
        self.thrown = False
        self._pending_tile = None      # on a primary: the half whose tap we are waiting on
        self._pending_timer = None

    # ---- the group: a primary, plus the secondaries linked to its label ----

    def _turnouts(self):
        scene = self.scene()
        if scene is None:
            return []
        return [t for t in scene.tiles_by_cell.values() if isinstance(t, Turnout)]

    def primary(self):
        """The tile that holds the address, or None if the link points at nothing."""
        if not self.linked_to:
            return self
        for tile in self._turnouts():
            if tile.label == self.linked_to and not tile.linked_to:
                return tile
        return None

    def group(self):
        """Call on a primary. Returns the primary first, then its secondaries."""
        members = [self]
        if self.label:
            members += [t for t in self._turnouts() if t.linked_to == self.label]
        return members

    @staticmethod
    def _parity(members):
        return sum(1 for tile in members if tile.thrown) % 2 == 1

    # ---- tapping --------------------------------------------------------

    def on_tap(self):
        primary = self.primary()
        if primary is None:
            return                              # linked to a tile that isn't there
        scene = self.scene()
        bridge = scene.bridge
        if bridge is None:
            self.thrown = not self.thrown       # no station: just flip this half
            scene.update()
            return
        if primary._pending_tile is not None or primary.address <= 0:
            return                              # still waiting for the last command
        # flipping this half flips the parity, so that is what we ask the station for
        wanted = not self._parity(primary.group())
        if bridge.send_turnout(primary.address, primary.protocol, wanted):
            primary._wait_for_confirmation(self)
            # the picture changes when the station confirms, not now

    def _wait_for_confirmation(self, tile):
        self._pending_tile = tile
        self._pending_timer = QTimer()
        self._pending_timer.setSingleShot(True)
        self._pending_timer.timeout.connect(self._clear_pending)
        self._pending_timer.start(config.CONFIRM_TIMEOUT_MS)

    def _clear_pending(self):
        if self._pending_timer is not None:
            self._pending_timer.stop()
            self._pending_timer = None
        self._pending_tile = None

    # ---- the station speaking -------------------------------------------

    def on_station_turnout(self, address, protocol, diverging):
        if self.linked_to or address != self.address or protocol != self.protocol:
            return                              # not ours; secondaries never answer
        members = self.group()
        tile = self._pending_tile if self._pending_tile in members else None
        self._clear_pending()
        if self._parity(members) == diverging:
            return                              # the pictures already agree
        if tile is None:
            # not our own tap (CS3 screen, another throttle, or the first read after
            # connecting): either picture would be true, so the secondary gives way
            tile = members[1] if len(members) > 1 else self
        tile.thrown = not tile.thrown
        self.scene().update()

    # ---- drawing --------------------------------------------------------

    def draw(self, painter):
        self.draw_tile_background(painter)

        if self.primary() is None:              # linked to nothing: show both routes dead
            self.draw_line(painter, "W", self.branch, active=False)
            self.draw_line(painter, "W", "E", active=False)
            return

        # self.thrown is this half's own state. Invert Display only changes the
        # picture: the branch is shown active when thrown and invert differ.
        show_branch = self.thrown != self.invert

        # inactive route first, active route last, so the active one is on top
        if show_branch:
            self.draw_line(painter, "W", "E", active=False)
            self.draw_line(painter, "W", self.branch, active=True)
        else:
            self.draw_line(painter, "W", self.branch, active=False)
            self.draw_line(painter, "W", "E", active=True)

class TurnoutRight(Turnout):
    branch = "S"


class TurnoutLeft(Turnout):
    branch = "N"


class Turnout3Way(Tile):
    """A three-way turnout: two station turnouts behind one tile.

    Left = the upper branch, right = the lower branch, seen from the toe (west).
    Wire states: left thrown = (left r, right g), right thrown = (left g, right r),
    straight = (g, g). Both thrown at once cannot happen and is shown as unknown.
    """
    property_specs = [
        {"key": "label", "label": "Label", "type": str, "max_length": 10, "default": ""},
        {"key": "name", "label": "Name", "type": str, "default": ""},
        {"key": "address", "label": "Left Address", "type": int, "default": 0},
        {"key": "address2", "label": "Right Address", "type": int, "default": 0},
        {"key": "protocol", "label": "Protocol", "type": "choice", "choices": ["DCC", "MM"], "default": "DCC"}
        ]

    def __init__(self):
        super().__init__()
        self.thrown_state = 0           # 0 straight, 1 left, 2 right, -1 unknown
        self._next_side = 1             # straight > left > straight > right > straight
        self._wire = [False, False]     # last known wire state of the left and right address
        self._target = None
        self._pending_timer = None

    def on_tap(self):
        scene = self.scene()
        bridge = scene.bridge
        if self.thrown_state == 0:
            target = self._next_side
        else:
            target = 0                  # from left, right or unknown: back to straight

        if bridge is None:
            self._set_state(target)
            scene.update()
            return

        if self._target is not None or self.address <= 0 or self.address2 <= 0:
            return                      # waiting for the last move, or not addressed
        # the branch that is going back to straight is always released first, so
        # the two turnouts are never both thrown, not even for a moment
        want_left = target == 1
        want_right = target == 2
        commands = [(self.address2, want_right), (self.address, want_left)] if want_left \
            else [(self.address, want_left), (self.address2, want_right)]
        sent = False
        for address, diverging in commands:
            sent = bridge.send_turnout(address, self.protocol, diverging) or sent
        if sent:
            self._target = [want_left, want_right]
            self._pending_timer = QTimer()
            self._pending_timer.setSingleShot(True)
            self._pending_timer.timeout.connect(self._clear_pending)
            self._pending_timer.start(config.CONFIRM_TIMEOUT_MS)

    def _set_state(self, state):
        if state in (1, 2):
            self._next_side = 3 - state     # after this side, the other one comes next
        self.thrown_state = state

    def _clear_pending(self):
        if self._pending_timer is not None:
            self._pending_timer.stop()
            self._pending_timer = None
        self._target = None

    def on_station_turnout(self, address, protocol, diverging):
        if protocol != self.protocol or address not in (self.address, self.address2):
            return
        if address == self.address:
            self._wire[0] = diverging
        if address == self.address2:
            self._wire[1] = diverging
        left, right = self._wire
        if left and right:
            self._set_state(-1)
        elif left:
            self._set_state(1)
        elif right:
            self._set_state(2)
        else:
            self._set_state(0)
        if self._target is not None and self._wire == self._target:
            self._clear_pending()
        self.scene().update()

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
        elif self.thrown_state == -1:
            self.draw_line(painter, "W", "E", active=False)
            self.draw_line(painter, "W", "N", active=False)
            self.draw_line(painter, "W", "S", active=False)
        else:
            self.draw_line(painter, "W", "N", active=False)
            self.draw_line(painter, "W", "S", active=False)
            self.draw_line(painter, "W", "E", active=True)


class Signal(Tile):
    property_specs = [
        {"key": "label", "label": "Label", "type": str, "max_length": 10, "default": ""},
        {"key": "name", "label": "Name", "type": str, "default": ""}, 
        {"key": "address", "label": "Address", "type": int, "default": 0},
        {"key": "protocol", "label": "Protocol", "type": "choice", "choices": ["DCC", "MM"], "default": "DCC"}
        ]

    def __init__(self):
        super().__init__()
        self.show_red = False

    def on_tap(self):
         self.show_red = not self.show_red

    def draw(self, painter):
        self.draw_tile_background(painter)

        pen = QPen(QColor(config.TRACK_COLOR))
        pen.setWidth(config.TRACK_WIDTH)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        painter.setPen(pen)
        painter.drawLine(self.edge_point("W"), self.edge_point("E"))

        signal_pos_y = ((config.GRID_SIZE * 0.75) + (config.TRACK_WIDTH / 4)) / config.GRID_SIZE
        signal_head_bottom = self.point_at(0.75, signal_pos_y)
        signal_head_top = self.point_at(0.5, signal_pos_y)
        signal_base_bottom = self.point_at(0.15, signal_pos_y)
        signal_base_top = self.point_at(0.5, signal_pos_y)
        width = config.TRACK_WIDTH * 1.6
        signal_base_width = config.TRACK_WIDTH * 0.3
        self.draw_signal_element(painter, signal_head_bottom, signal_head_top, width)
        self.draw_signal_element(painter, signal_base_bottom, signal_base_top, signal_base_width)

        color = config.SIGNAL_COLOR_RED if self.show_red else config.SIGNAL_COLOR_GREEN
        painter.setBrush(QBrush(QColor(color)))
        painter.setPen(Qt.PenStyle.NoPen)
        center = self.point_at(0.5 if self.show_red else 0.75, signal_pos_y)
        radius = config.TRACK_WIDTH / 2
        painter.drawEllipse(center, radius, radius)


  
    


     
