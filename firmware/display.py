import adafruit_displayio_sh1106
import displayio
import terminalio
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text import label
from adafruit_progressbar.verticalprogressbar import VerticalProgressBar
from displayio import TileGrid
from fruity_menu.menu import Menu

from config import Config
from hardware import Hardware
from data import Leg
import adafruit_logging as logging

from bitmaps import bitmaps, palette
from utils import convert_voltage_to_progress

logger = logging.getLogger()

WIDTH = 128
HEIGHT = 64


class Display:
    MEASURE = 0
    MENU = 1

    def __init__(self, devices: Hardware, config: Config):
        self.devices = devices
        self.config = config
        bus = displayio.I2CDisplay(self.devices.i2c, device_address=0x3c)
        self.oled = adafruit_displayio_sh1106.SH1106(bus, width=WIDTH, height=HEIGHT,
                                                     rotation=0, auto_refresh=False, colstart=2)
        text = " " * 20

        self.measurement_group = displayio.Group()
        self.azimuth = label.Label(font_20, text=text, color=0xffffff, x=1, y=9)
        self.inclination = label.Label(font_20, text=text, color=0xffffff, x=1, y=31)
        self.distance = label.Label(font_20, text=text, color=0xffffff, x=1, y=53)
        self.reading_index = label.Label(terminalio.FONT, text="  ", color=0xffffff)
        self.reading_index.anchored_position = (127, 32)
        self.reading_index.anchor_point = (1.0, 0.5)
        self.measurement_group.append(self.azimuth)
        self.measurement_group.append(self.inclination)
        self.measurement_group.append(self.distance)
        self.measurement_group.append(self.reading_index)

        self.icon_group = displayio.Group()
        self.bt_icon = TileGrid(bitmaps['bt'], pixel_shader=palette,
                                width=1, height=1,
                                tile_width=11, tile_height=16,
                                x=115, y=1)
        batt_icon = TileGrid(bitmaps['batt_icon'], pixel_shader=palette, x=115, y=48)
        self.batt_level = VerticalProgressBar((118,53), (6,8), max_value=100, border_thickness=0)
        self.icon_group.append(self.bt_icon)
        self.icon_group.append(batt_icon)
        self.icon_group.append(self.batt_level)


        self.laser_group = displayio.Group()
        self.laser_group.append(laser_group)

    def set_group_with_icons(self, group):
        for grp in self.measurement_group, self.laser_group:
            if self.icon_group in grp:
                grp.remove(self.icon_group)
        group.append(self.icon_group)
        self.oled.show(group)

    def show_start_screen(self):
        self.set_group_with_icons(self.laser_group)
        self.refresh()

    def update_measurement(self, leg: Leg, reading_index: int):
        self.set_group_with_icons(self.measurement_group)
        self.azimuth.text = self.config.get_azimuth_text(leg.azimuth)
        self.inclination.text = self.config.get_inclination_text(leg.inclination)
        self.distance.text = self.config.get_distance_text(leg.distance)
        self.reading_index.text = str(reading_index)
        self.refresh()

    def set_bt_connected(self, connected:bool):
        if connected:
            self.bt_icon[0] = 1
        else:
            self.bt_icon[0] = 0
        self.refresh()

    def set_batt_level(self, voltage):
        self.batt_level.value = convert_voltage_to_progress(voltage, 100)
        self.refresh()

    def refresh(self):
        self.oled.refresh()

    def get_menu(self):
        return Menu(self.oled, HEIGHT, WIDTH, False, "Menu")

    def show_info(self, text):
        splash = displayio.Group()
        fontx, fonty = terminalio.FONT.get_bounding_box()
        term_palette = displayio.Palette(2)
        term_palette[0] = 0x000000
        term_palette[1] = 0xffffff
        logbox = displayio.TileGrid(terminalio.FONT.bitmap,
                                    x=0,
                                    y=0,
                                    width=WIDTH // fontx,
                                    height=HEIGHT // fonty,
                                    tile_width=fontx,
                                    tile_height=fonty,
                                    pixel_shader=term_palette)
        splash.append(logbox)
        logterm = terminalio.Terminal(logbox, terminalio.FONT)

        self.oled.show(splash)
        logterm.write(text)
        self.oled.refresh()

    def show_big_info(self, text):
        lines = text.splitlines()
        for lbl, line in zip((self.azimuth, self.inclination, self.distance), lines):
            lbl.text = line
        self.show_group(self.measurement_group)

    def show_group(self, group: displayio.Group):
        self.oled.show(group)
        self.refresh()

    def deinit(self):
        self.laser_group.remove(laser_group)

def get_laser_bitmap_group():
    laser_bitmap = bitmaps['laser']
    x = (WIDTH-laser_bitmap.width)//2
    y = (HEIGHT-laser_bitmap.height)//2
    tile_grid = displayio.TileGrid(laser_bitmap, pixel_shader=palette, x=x, y=y)
    group = displayio.Group()
    group.append(tile_grid)
    return group
    # Add the Group to the Display


font_20 = bitmap_font.load_font("/fonts/terminus_28_ascii.pcf")
laser_group = get_laser_bitmap_group()