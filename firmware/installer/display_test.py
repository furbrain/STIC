"""
This file is designed to be run on my little display testing board
It connects to a display when the button is pressed and shows a test pattern. (A box around the edge
of the screen and some text).
"""
import time

import busio
import digitalio
import board
import adafruit_displayio_sh1106
from adafruit_display_shapes.rect import Rect

import displayio
import terminalio
from adafruit_display_text import label

displayio.release_displays()
v_supply = digitalio.DigitalInOut(board.D4)
v_supply.switch_to_output(True)

button = digitalio.DigitalInOut(board.D2)
button.pull = digitalio.Pull.DOWN


def show_pattern(disp):
    splash = displayio.Group()
    palette = displayio.Palette(2)
    palette[0] = 0x000000
    palette[1] = 0xFFFFFF
    bitmap_a = displayio.Bitmap(128,64,2)
    bitmap_a.fill(1)
    bitmap_b = displayio.Bitmap(108,44,2)
    bitmap_b.fill(0)
    tile_a = displayio.TileGrid(bitmap_a, pixel_shader=palette, x=0, y=0)
    tile_b = displayio.TileGrid(bitmap_b, pixel_shader=palette, x=10, y=10)
    splash.append(tile_a)
    splash.append(tile_b)
    splash.append(label.Label(terminalio.FONT, text="Press B", color=0xffffff, x=30, y=31))
    disp.root_group = splash


def test_display(button: digitalio.DigitalInOut):
    with busio.I2C(scl=board.D10, sda=board.D9, frequency=4000000) as i2c:
        bus = displayio.I2CDisplay(i2c, device_address=0x3c)
        oled = adafruit_displayio_sh1106.SH1106(bus, width=128, height=64, rotation=0, colstart=2)
        show_pattern(oled)
        while button.value:
            time.sleep(0.1)
        oled.root_group = None
        time.sleep(1)


while True:
    while not button.value:
        time.sleep(0.1)
    try:
        test_display(button)
    except Exception as e:
        print("Error: ", e)
    finally:
        displayio.release_displays()

