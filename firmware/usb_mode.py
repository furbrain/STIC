import time

import terminalio
from adafruit_progressbar.horizontalprogressbar import HorizontalProgressBar, \
    HorizontalFillDirection
from adafruit_display_text import label
import config
import hardware
import display
import displayio
import adafruit_logging as logging

from bitmaps import bitmaps, palette
from utils import convert_voltage_to_progress

logger = logging.getLogger()


import utils

BAR_HEIGHT = 18

BAR_WIDTH = 40


def usb_charge_monitor():
    logger.debug("Releasing displays")
    displayio.release_displays()
    logger.debug("Showing Charging symbol")
    with hardware.Hardware() as devices:
        cfg = config.Config.load()
        disp = display.Display(devices, cfg)
        group = displayio.Group()
        battery_bmp = bitmaps['battery']
        battery_tile = displayio.TileGrid(battery_bmp, pixel_shader=palette, x=32, y=14)
        group.append(battery_tile)
        progress_bar = HorizontalProgressBar(
            (41,23), (BAR_WIDTH, BAR_HEIGHT), direction=HorizontalFillDirection.LEFT_TO_RIGHT,
            min_value=0, max_value=BAR_WIDTH, bar_color=0xffffff, margin_size=0, border_thickness=0
        )
        group.append(progress_bar)
        status_label = label.Label(terminalio.FONT, text=" "*13)
        status_label.anchored_position = (64, 52)
        status_label.anchor_point = (0.5, 0.0)
        percentage_label = label.Label(terminalio.FONT, text=" "*4)
        percentage_label.anchored_position = (127,0)
        percentage_label.anchor_point = (1.0, 0.0)
        voltage_label = label.Label(terminalio.FONT, text=" "*5)
        voltage_label.anchored_position = (0,0)
        voltage_label.anchor_point = (0.0, 0.0)
        group.append(percentage_label)
        group.append(voltage_label)

        group.append(status_label)

        disp.show_group(group)
        disconnnected_count = 0
        while True:
            voltage = devices.batt_voltage
            voltage_label.text = f"{voltage:4.2f}V"
            percent_progress = convert_voltage_to_progress(voltage, 100)
            percentage_label.text = f"{percent_progress}%"
            if not devices.battery.charge_status:
                progress = BAR_WIDTH
                status_label.text = "Fully Charged"
            else:
                progress = convert_voltage_to_progress(voltage, BAR_WIDTH)
                status_label.text = f"Charging"
            while progress <= BAR_WIDTH + 2:
                progress_bar.value = min(progress, BAR_WIDTH-1)
                disp.refresh()
                progress += 1
                time.sleep(0.1)
                if utils.usb_power_connected():
                    disconnnected_count = 0
                else:
                    disconnnected_count +=1
                if disconnnected_count > 5:
                    return