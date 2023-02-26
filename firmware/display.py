import time

import adafruit_displayio_ssd1306
import board
import busio
import digitalio
import displayio
import rm3100
import terminalio
from adafruit_display_text import label

WIDTH=64
HEIGHT=48
BORDER=2
scl = board.D6
sda = board.D5

def create_display(i2c_bus):
    bus = displayio.I2CDisplay(i2c_bus, device_address=0x3c)
    display = adafruit_displayio_ssd1306.SSD1306(bus, width=WIDTH, height=HEIGHT+40, rotation=270)

    splash = displayio.Group(y=40)
    display.show(splash)

    color_bitmap = displayio.Bitmap(WIDTH, HEIGHT, 1)
    color_palette = displayio.Palette(1)
    color_palette[0] = 0xFFFFFF  # White

    bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
    splash.append(bg_sprite)

    # Draw a smaller inner rectangle
    inner_bitmap = displayio.Bitmap(WIDTH - BORDER * 2, HEIGHT - BORDER * 2, 1)
    inner_palette = displayio.Palette(1)
    inner_palette[0] = 0x000000  # Black
    inner_sprite = displayio.TileGrid(
        inner_bitmap, pixel_shader=inner_palette, x=BORDER, y=BORDER
    )
    splash.append(inner_sprite)

    # Draw a label
    text = "Hello!   "
    text_area = label.Label(
        terminalio.FONT, text=text, color=0xFFFFFF, x=10, y=HEIGHT // 2 - 1
    )
    splash.append(text_area)
    return text_area


displayio.release_displays()
periph_en = digitalio.DigitalInOut(board.D1)
periph_en.switch_to_output()
periph_en.value = 0

time.sleep(0.01)

i2c = busio.I2C(scl,sda)
if i2c.try_lock():
    print(i2c.scan())
i2c.unlock()

text = create_display(i2c)
rm = rm3100.RM3100_I2C(i2c)
while True:
    text.text = f"{rm.magnetic[0]: 04.1f}"
    time.sleep(0.1)
