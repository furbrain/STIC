import math
try:
    # noinspection PyUnresolvedReferences
    from typing import Optional, Sequence
except ImportError:
    pass

import displayio
import terminalio
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text import label
from adafruit_progressbar.verticalprogressbar import VerticalProgressBar
from displayio import TileGrid, Bitmap
try:
    # try to load using 9.0 style, fall back to 8.x style
    from busdisplay import BusDisplay
except ImportError:
    from displayio import Display as BusDisplay

from ..bitmaps import bitmaps, palette
from ..config import Config
from ..data import Leg
from ..debug import logger
from ..display import DisplayBase
from ..utils import convert_voltage_to_progress, clean_block_text

WIDTH = 128
HEIGHT = 64


class Display(DisplayBase):
    MEASURE = 0
    MENU = 1

    def __init__(self, oled: BusDisplay, config: Config):
        self._config = config
        self.oled = oled
        self._icon_group = displayio.Group()
        self._bt_icon = TileGrid(bitmaps['bt'], pixel_shader=palette,
                                 width=1, height=1,
                                 tile_width=11, tile_height=16,
                                 x=115, y=1)
        self._bt_pending_bitmap = Bitmap(11, 2, 2)
        self._bt_pending_bitmap.fill(0)
        self._bt_pending_tile = TileGrid(self._bt_pending_bitmap, pixel_shader=palette, x=115, y=19)
        batt_icon = TileGrid(bitmaps['batt_icon'], pixel_shader=palette, x=115, y=48)
        self._bt_pending_count = 0
        self._batt_level = VerticalProgressBar((118, 53), (6, 8), max_value=100, border_thickness=0)
        self._icon_group.append(self._bt_icon)
        self._icon_group.append(batt_icon)
        self._icon_group.append(self._batt_level)
        self._icon_group.append(self._bt_pending_tile)

        # Initialize the measurement labels and group (these stay persistent)
        self._measurement_group = displayio.Group()

        # These labels are created once and updated later
        self._azimuth_label = label.Label(font_20, text="", color=0xffffff, x=1, y=9)
        self._inclination_label = label.Label(font_20, text="", color=0xffffff, x=1, y=31)
        self._distance_label = label.Label(font_20, text="", color=0xffffff, x=1, y=53)

        # Reading index label (used for showing index in the corner)
        self._reading_index_label = label.Label(terminalio.FONT, text="", color=0xffffff)
        self._reading_index_label.anchored_position = (127, 32)
        self._reading_index_label.anchor_point = (1.0, 0.5)

        # Add all the labels to the measurement group (so they can be updated together)
        self._measurement_group.append(self._azimuth_label)
        self._measurement_group.append(self._inclination_label)
        self._measurement_group.append(self._distance_label)
        self._measurement_group.append(self._reading_index_label)

        self._current_group = None
        self._inverted = False

    def _set_group_with_icons(self, group):
        if self._current_group:
            self._icon_group.remove(self._current_group)
        self._current_group = group
        self._icon_group.append(self._current_group)
        self.oled.root_group = self._icon_group

    def show_start_screen(self):
        self._set_group_with_icons(laser_group)
        self.refresh()

    def update_measurement(self, leg: Leg, reading_index: int, show_extents: bool):
        if show_extents:
            azimuth_text = "Extents"
            horizontal = math.cos(math.radians(leg.inclination)) * leg.distance
            vertical = math.sin(math.radians(leg.inclination)) * leg.distance
            inclination_text = "H:{:>6}".format(self._config.get_distance_text(horizontal))
            distance_text = "V:{:>6}".format(self._config.get_distance_text(vertical))
        else:
            azimuth_text = self._config.get_azimuth_text(leg.azimuth)
            inclination_text = self._config.get_inclination_text(leg.inclination)
            distance_text = self._config.get_distance_text(leg.distance)

        index = reading_index + 1
        index_text = "" if index <= 0 else "{:03d}".format(index)

        self._azimuth_label.text = azimuth_text
        self._inclination_label.text = inclination_text
        self._distance_label.text = distance_text
        self._reading_index_label.text = index_text

        self._set_group_with_icons(self._measurement_group)
        self.refresh()

    def set_bt_connected(self, connected: bool):
        currently_connected = self._bt_icon[0] == 1
        if currently_connected != connected:
            if connected:
                self._bt_icon[0] = 1
            else:
                self._bt_icon[0] = 0
            self.refresh()

    def set_bt_pending_count(self, count: int):
        count = min(count, 4)
        if count != self._bt_pending_count:
            self._bt_pending_count = count
            self._bt_pending_bitmap.fill(0)
            for i in range(count):
                self._bt_pending_bitmap[i * 3, 0] = 1
                self._bt_pending_bitmap[i * 3 + 1, 0] = 1
                self._bt_pending_bitmap[i * 3, 1] = 1
                self._bt_pending_bitmap[i * 3 + 1, 1] = 1
            self.refresh()

    def set_batt_level(self, voltage):
        self._batt_level.value = convert_voltage_to_progress(voltage, 100)
        self.refresh()

    def refresh(self):
        self.oled.refresh()

    def show_info(self, text, clean=False):
        if clean:
            text = clean_block_text(text)
        logger.debug(f"show_info: text: {repr(text)}")
        splash = displayio.Group()
        fontx, fonty = terminalio.FONT.get_bounding_box()
        term_palette = displayio.Palette(2)
        term_palette[0] = 0x000000
        term_palette[1] = 0xffffff
        logbox = displayio.TileGrid(terminalio.FONT.bitmap,
                                    x=0,
                                    y=0,
                                    width=self.oled.width // fontx,
                                    height=self.oled.height // fonty,
                                    tile_width=fontx,
                                    tile_height=fonty,
                                    pixel_shader=term_palette)
        splash.append(logbox)
        logterm = terminalio.Terminal(logbox, terminalio.FONT)

        self.oled.root_group = splash
        logterm.write(text)
        self.oled.refresh()

    def show_big_info(self, text):
        lines = text.splitlines()
        while len(lines) < 3:
            lines.append("")

        self._azimuth_label.text = lines[0]
        self._inclination_label.text = lines[1]
        self._distance_label.text = lines[2]
        self._reading_index_label.text = ""

        self._set_group_with_icons(self._measurement_group)
        self.refresh()

    def show_group(self, group: Optional[displayio.Group]):
        self.oled.root_group = group
        self.refresh()

    def clear_memory(self):
        if self._current_group:
            self._icon_group.remove(self._current_group)
            self._current_group = None
        font_20._glyphs.clear()

    @property
    def inverted(self):
        """
        Whether display is the right way up or rotated
        """
        return self._inverted

    @inverted.setter
    def inverted(self, inverted: bool):
        self._inverted = inverted
        if inverted:
            self.oled.rotation = 180
        else:
            self.oled.rotation = 0
        self.refresh()

    def sleep(self, wake=False):
        if wake:
            if hasattr(self.oled, "wake"):
                self.oled.wake()
        else:
            if hasattr(self.oled, "sleep"):
                self.oled.sleep()

    def deinit(self):
        if self._current_group:
            self._icon_group.remove(self._current_group)


def get_laser_bitmap_group():
    laser_bitmap = bitmaps['laser']
    x = (WIDTH - laser_bitmap.width) // 2
    y = (HEIGHT - laser_bitmap.height) // 2
    tile_grid = displayio.TileGrid(laser_bitmap, pixel_shader=palette, x=x, y=y)
    group = displayio.Group()
    group.append(tile_grid)
    return group
    # Add the Group to the Display


font_20 = bitmap_font.load_font("/fonts/terminus_28_ascii.pcf")
laser_group = get_laser_bitmap_group()
