import asyncio
import time

import adafruit_logging
import os

import microcontroller
# noinspection PyPackageRequirements
import storage

try:
    # noinspection PyUnresolvedReferences
    # we try to import typing, this fails on circuitpython but gives us code completion in editors
    import typing
    from . import config
    from . import display
    from . import hardware
except ImportError:
    pass

logger = adafruit_logging.getLogger()
files = os.listdir("/")
files = [x.split('.')[0].upper() for x in files]
if "DEBUG" in files:
    logger.setLevel(adafruit_logging.DEBUG)
elif "INFO" in files:
    logger.setLevel(adafruit_logging.INFO)
else:
    logger.setLevel(adafruit_logging.WARNING)
#if not storage.getmount("/").readonly:
#    logger.addHandler(adafruit_logging.FileHandler("log.txt"))
logger.debug("Starting log")

INFO = adafruit_logging.INFO
WARNING = adafruit_logging.WARNING
DEBUG = adafruit_logging.DEBUG
ERROR = adafruit_logging.ERROR


def freeze():
    # stop everything for 10 seconds - should trigger watchdog
    time.sleep(10)
    time.sleep(10)


def dummy():
    pass


def breaker():
    # noinspection PyUnresolvedReferences,PyUnusedLocal
    a = b


async def menu_item_test(devices: hardware.Hardware, cfg: config.Config, disp: display.Display):
    for i in range(5):
        await asyncio.sleep(1)
        disp.show_info(f"MENU TEST: {i}\r\nPhil was here\r\nHere is a very long line " +
                       f"indeed")

async def battery_test(devices: hardware.Hardware, cfg: config.Config, disp: display.Display):
    from . import measure
    prev_timeout = cfg.timeout
    try:
        cfg.timeout = 1000000
        start_time = time.time()
        disp.show_info(f"""
                        Ensure device is
                        fully charged
                        (Voltage {devices.batt_voltage:4.2f}V)
                        Press A to start
                        battery test.
                        """,
                       clean=True)
        devices.laser_enable(True)
        await asyncio.sleep(0.1)
        devices.laser.set_laser(True)
        await devices.button_a.wait_for_click()
        count = 0
        while devices.batt_voltage > 3.5:
            await measure.take_reading(devices, cfg, disp)
            count += 1
            disp.show_big_info(f"Battery\r\n{devices.batt_voltage:4.2f}V\r\n{count}")
            await asyncio.sleep(10)
        with open("battery_test.txt", "w") as f:
            f.write(f"Took {count} shots over {time.time()-start_time} seconds")
    finally:
        cfg.timeout = prev_timeout
    await asyncio.sleep(10)
    microcontroller.reset()