import asyncio
import time

try:
    from typing import Callable, Optional
except ImportError:
    pass

from async_button import Button
from fruity_menu.builder import build_menu, Action, Options
from mag_cal import Calibration

import calibrate
import config
import display
import hardware
from config import Config
import adafruit_logging as logging

logger = logging.getLogger()


action_item: Optional[Callable[[hardware.Hardware, config.Config, display.Display],None]] = None


def start_menu_item(func):
    global action_item
    action_item = func


async def menu(devices: hardware.Hardware, config: config.Config, display: display.Display):
    global action_item
    logger.debug("Menu task started")
    await asyncio.sleep(0.1)
    items = [
        ("Calibrate", [
            ("Sensors", Action(start_menu_item, calibrate.calibrate)),
            ("Laser", dummy),
            ("Axes", freeze),
            ]),
        ("Test", [
            ("Simple Test", Action(start_menu_item, menu_item_test)),
            ("Raw Data", Action(start_menu_item, raw_readings_item)),
            ("Value Error", Action(start_menu_item, breaker)),
            ("Freeze", freeze),
            ]),
        ("Settings", [
            ("Units", Options(
                value=config.units,
                options = [
                    ("Metric", Config.METRIC),
                    ("Imperial", Config.IMPERIAL)],
                on_value_set = lambda x: config.set_var("units", x)
                )),
            ("Angles", Options(
                value=config.angles,
                options=[
                    ("Degrees", Config.DEGREES),
                    ("Grads", Config.GRADS)],
                on_value_set = lambda x: config.set_var("angles", x)
                )),
            ("Anomaly Detection", Options(
                value=config.anomaly_strictness,
                options=[
                    ("Off", Calibration.OFF),
                    ("Soft", Calibration.SOFT),
                    ("Hard", Calibration.HARD)],
                on_value_set=lambda x: config.set_var("anomaly_strictness", x)
                )),
            ]),
        ]
    menu = display.get_menu()
    build_menu(menu, items)
    menu.show_menu()
    display.refresh()
    while True:
        button, _ = await devices.both_buttons.wait(a=Button.SINGLE, b=Button.SINGLE)
        if button == "a":
            devices.beep_bip()
            logger.debug("Menu: Click")
            menu.click()
            if action_item is not None:
                logger.debug(f"Running {action_item}")
                await action_item(devices, config, display)
                action_item = None
            menu.show_menu()
            display.refresh()
        elif button == "b":
            logger.debug("Menu: Scroll")
            devices.beep_bop()
            menu.scroll(1)
            menu.show_menu()
            display.refresh()


def freeze():
    #stop everything for 10 seconds - should trigger watchdog
    time.sleep(10)
    time.sleep(10)


def dummy():
    pass


async def breaker(devices, config, display):
    a = b


async def menu_item_test(devices, config, display):
    for i in range(5):
        await asyncio.sleep(1)
        display.show_info(f"MENU TEST: {i}\r\nPhil was here\r\nHere is a very long line " +
                            f"indeed")


async def raw_readings_item(devices: hardware.Hardware, config, display):
    while True:
        try:
            await asyncio.wait_for(devices.button_a.wait_for_click(),0.5)
            return
        except asyncio.TimeoutError:
            pass
        acc = devices.accelerometer.acceleration
        mag = devices.magnetometer.magnetic
        text = "Raw Accel Mag\r\n"
        for axis,a,m in zip("XYZ",acc,mag):
            text += f"{axis}   {a:05.3f} {m:05.2f}\r\n"
        display.show_info(text)