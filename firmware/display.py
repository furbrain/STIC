import time
import atexit

import adafruit_displayio_sh1106
import busio
import displayio
import terminalio

import hardware
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font

from data import Readings, Leg

WIDTH = 132
HEIGHT = 64


class Display:
    MEASURE = 0
    MENU = 1

    def __init__(self, mode: int = MEASURE):
        self.mode: int = mode
        self.display = self.create_display()
        # self.display.refresh()
        self.azimuth: label.Label = None
        self.inclination: label.Label = None
        self.distance: label.Label = None
        self.reading_index: label.Label = None
        self.measurement_group = self.create_measurement_group()
        self.menu_group = None
        self.set_mode(mode)

    def set_mode(self, mode: int):
        self.mode = mode
        if self.mode == self.MEASURE:
            self.display.root_group = self.measurement_group
        elif self.mode == self.MENU:
            self.display.root_group = self.menu_group
        else:
            raise ValueError("Mode must be either MEASURE or MENU")

    def create_display(self) -> displayio.Display:
        ...

    def create_measurement_group(self) -> displayio.Group:
        ...


    def update_measurement(self, leg: Leg, reading_index: int):
        self.azimuth.text = str(leg.azimuth)
        self.inclination.text = str(leg.inclination)
        self.distance.text = str(leg.distance)
        self.reading_index = str(reading_index)
        self.refresh()

    def refresh(self):
        self.display.refresh()


class SH1106_Display(Display):
    def __init__(self, i2c: busio.I2C, mode: int = Display.MEASURE):
        self.i2c = i2c
        super().__init__(mode)


    def create_display(self) -> displayio.Display:
        i2c = self.i2c
        self.bus = displayio.I2CDisplay(i2c, device_address=0x3c)
        display = adafruit_displayio_sh1106.SH1106(self.bus, width=WIDTH, height=HEIGHT, rotation=0,
                                                   auto_refresh=True)
        return display

    def create_measurement_group(self) -> displayio.Group:
        #font_20 = bitmap_font.load_font("/fonts/OpenSans-20.bdf")
        font_20 = terminalio.FONT
        measurement_group = displayio.Group()
        text = " " * 20
        self.azimuth = label.Label(font_20, text=text, color=0xffffff, x=1, y=10)
        self.inclination = label.Label(font_20, text=text, color=0xffffff, x=1, y=31)
        self.distance = label.Label(font_20, text=text, color=0xffffff, x=1, y=52)
        self.reading_index = label.Label(font_20, text="  ", color=0xffffff, x=100, y=52)
        measurement_group.append(self.azimuth)
        measurement_group.append(self.inclination)
        measurement_group.append(self.distance)
        measurement_group.append(self.reading_index)
        return measurement_group



