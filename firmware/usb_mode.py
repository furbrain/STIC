import time

from adafruit_progressbar.horizontalprogressbar import HorizontalProgressBar, \
    HorizontalFillDirection

import config
import hardware
import display
import displayio
import seeed_xiao_nrf52840

BAR_HEIGHT = 18

MIN_VOLTAGE=3.5
MAX_VOLTAGE=4.2

BAR_WIDTH = 40

def convert_voltage_to_progress(voltage:float, maximum:int):
    if voltage < MIN_VOLTAGE:
        return 0
    if voltage > MAX_VOLTAGE:
        return maximum
    return int(maximum*(voltage-MIN_VOLTAGE)/(MAX_VOLTAGE-MIN_VOLTAGE))


def usb_charge_monitor():
    displayio.release_displays()
    with hardware.Hardware() as devices:
        cfg = config.Config.load()
        disp = display.Display(devices, cfg)
        group = displayio.Group()
        battery_bmp = displayio.OnDiskBitmap("/images/battery.bmp")
        battery_tile = displayio.TileGrid(battery_bmp,pixel_shader=battery_bmp.pixel_shader, x=32, y=14)
        group.append(battery_tile)
        progress_bar = HorizontalProgressBar(
            (41,23), (BAR_WIDTH, BAR_HEIGHT), direction=HorizontalFillDirection.LEFT_TO_RIGHT,
            min_value=0, max_value=BAR_WIDTH, bar_color=0xffffff, margin_size=0, border_thickness=0
        )
        group.append(progress_bar)
        disp.show_group(group)
        while True:
            progress = 20
            #progress = convert_voltage_to_progress(devices.batt_voltage, BAR_WIDTH)
            while progress <= BAR_WIDTH + 2:
                progress_bar.value = min(progress, BAR_WIDTH-1)
                disp.refresh()
                progress += 1
                time.sleep(0.1)
