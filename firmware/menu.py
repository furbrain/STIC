import asyncio
import gc
import time

from info import raw_readings, calibrated_readings, orientation, device

from async_button import Button
from fruity_menu.builder import build_menu, Action, Options
from mag_cal import Calibration

import calibrate
import config
import display
import hardware
from config import Config

try:
    from typing import Callable, Optional, Coroutine, Any

    AsyncActionItem = Optional[Callable[[hardware.Hardware, config.Config, display.Display], Coroutine]]
except ImportError:
    pass

import adafruit_logging as logging

logger = logging.getLogger()


action_item: AsyncActionItem = None


def start_menu_item(func):
    global action_item
    action_item = func

class AsyncAction(Action):
    def __init__(self, func: AsyncActionItem):
        super().__init__(start_menu_item, func)

class ConfigOptions(Options):
    def __init__(self, name: str, object: config.Config, options, *, option_labels=None):
        super().__init__(value=getattr(object,name),
                         options=options,
                         option_labels=option_labels,
                         on_value_set=lambda x: object.set_var(name, x))


async def menu(devices: hardware.Hardware, config: config.Config, display: display.Display):
    global action_item
    logger.debug("Menu task started")
    gc.collect()
    await asyncio.sleep(0.1)
    items = [
        ("Calibrate", [
            ("Sensors", AsyncAction(calibrate.calibrate)),
            ("Laser", dummy),
            ]),
        ("Info", [
            ("Raw Data", AsyncAction(raw_readings)),
            ("Tidy Data", AsyncAction(calibrated_readings)),
            ("Orientation", AsyncAction(orientation)),
            ("Device", AsyncAction(device)),
            ]),
        ("Settings", [
            ("Timeout", ConfigOptions(
                name="timeout", object=config,
                options=[
                    ("30 seconds", 30),
                    ("1 minute", 60),
                    ("2 minutes", 120),
                    ("3 minutes", 180),
                    ("5 minutes", 300),
                ]
            )),
            ("Units", ConfigOptions(
                name="units", object=config,
                options = [
                    ("Metric", Config.METRIC),
                    ("Imperial", Config.IMPERIAL)],
                )),
            ("Angles", ConfigOptions(
                name="angles", object=config,
                options=[
                    ("Degrees", Config.DEGREES),
                    ("Grads", Config.GRADS)],
                )),
            ("Anomaly Detection", ConfigOptions(
                name="anomaly_strictness", object=config,
                options=[
                    ("Off", Calibration.OFF),
                    ("Relaxed", Calibration.SOFT),
                    ("Strict", Calibration.HARD)],
                )),
            ]),
        ("Bluetooth", [
            ("Disconnect", devices.bt.disconnect),
            ("Forget pairings", devices.bt.forget),
        ])
        ]
    debug_items = [
        ("Debug", [
            ("Test item", AsyncAction(menu_item_test)),
            ("Freeze", freeze),
            ("ValueError", breaker),
        ])
    ]
    if logger.getEffectiveLevel() <= logging.INFO:
        items.extend(debug_items)
    menu = display.get_menu()
    build_menu(menu, items)
    menu.show_menu()
    display.refresh()
    while True:
        button, _ = await devices.both_buttons.wait(a=Button.SINGLE, b=Button.SINGLE)
        if button == "a":
            devices.beep_bip()
            logger.debug("Menu: Click")
            gc.collect()
            menu.click()
            if action_item is not None:
                logger.debug(f"Running {action_item}")
                await action_item(devices, config, display)
                action_item = None
            menu.show_menu()
            display.refresh()
        elif button == "b":
            logger.debug("Menu: Scroll")
            gc.collect()
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


def breaker():
    a = b


async def menu_item_test(devices, config, display):
    for i in range(5):
        await asyncio.sleep(1)
        display.show_info(f"MENU TEST: {i}\r\nPhil was here\r\nHere is a very long line " +
                            f"indeed")


