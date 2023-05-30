import adafruit_displayio_sh1106
import busio
import displayio
import terminalio
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text import label
from async_button import Button
from fruity_menu.menu import Menu

from config import Config
from hardware import Hardware
from data import Leg
import adafruit_logging as logging

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
        self.azimuth = label.Label(font_20, text=text, color=0xffffff, x=1, y=10)
        self.inclination = label.Label(font_20, text=text, color=0xffffff, x=1, y=31)
        self.distance = label.Label(font_20, text=text, color=0xffffff, x=1, y=52)
        self.reading_index = label.Label(terminalio.FONT, text="  ", color=0xffffff, x=80, y=52)
        self.measurement_group = displayio.Group()
        self.measurement_group.append(self.azimuth)
        self.measurement_group.append(self.inclination)
        self.measurement_group.append(self.distance)
        self.measurement_group.append(self.reading_index)

    def show_start_screen(self):
        self.oled.show(laser_group)
        self.refresh()

    def update_measurement(self, leg: Leg, reading_index: int):
        self.oled.show(self.measurement_group)
        self.azimuth.text = self.config.get_azimuth_text(leg.azimuth)
        self.inclination.text = self.config.get_inclination_text(leg.inclination)
        self.distance.text = self.config.get_distance_text(leg.distance)
        self.reading_index.text = str(reading_index)
        self.refresh()

    def refresh(self):
        self.oled.refresh()

    def get_menu(self):
        return Menu(self.oled, HEIGHT, WIDTH, False, "Menu")

    async def show_and_run_menu(self, menu):
        menu.show_menu()
        self.oled.refresh()
        while True:
            button, _ = await self.devices.both_buttons.wait(a=Button.SINGLE, b=Button.SINGLE)
            if button == "a":
                logger.debug("Menu: Click")
                self.devices.beep_bip()
                menu.click()
                menu.show_menu()
                self.oled.refresh()
            elif button == "b":
                logger.debug("Menu: Scroll")
                self.devices.beep_bop()
                menu.scroll(1)
                menu.show_menu()
                self.oled.refresh()

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

    def show_group(self, group: displayio.Group):
        self.oled.show(group)
        self.refresh()

    def deinit(self):
        #added for completeness, currently does nothing
        pass
def get_laser_bitmap_group():
    laser_bitmap = displayio.OnDiskBitmap("laser2.bmp")
    tile_grid = displayio.TileGrid(laser_bitmap, pixel_shader=laser_bitmap.pixel_shader)
    group = displayio.Group()
    group.append(tile_grid)
    return group
    # Add the Group to the Display

font_20 = bitmap_font.load_font("/fonts/terminus_20.pcf")
laser_group = get_laser_bitmap_group()