import asyncio
import gc
import time

from async_button import Button
from fruity_menu.builder import build_menu, Action, Options
from mag_cal import Calibration

from . import measure
from . import calibrate
from . import config
from . import display
from . import hardware
from .config import Config
from .info import raw_readings, calibrated_readings, orientation, device
from .debug import logger, INFO

try:
    # noinspection PyUnresolvedReferences
    from typing import Callable, Optional, Coroutine, Any

    AsyncActionItem = Optional[Callable[[hardware.Hardware, config.Config, display.Display], Coroutine]]
except ImportError:
    pass


# noinspection PyUnboundLocalVariable
action_item: AsyncActionItem = None


def start_menu_item(func):
    global action_item
    action_item = func


class AsyncAction(Action):
    def __init__(self, func: AsyncActionItem):
        super().__init__(start_menu_item, func)


class ConfigOptions(Options):
    def __init__(self, name: str, obj: config.Config, options, *, option_labels=None):
        super().__init__(value=getattr(obj, name),
                         options=options,
                         option_labels=option_labels,
                         on_value_set=lambda x: obj.set_var(name, x))


async def menu(devices: hardware.Hardware, cfg: config.Config, disp: display.Display):
    global action_item
    logger.debug("Menu task started")
    gc.collect()
    await asyncio.sleep(0.1)
    items = [
        ("Calibrate", [
            ("Sensors", AsyncAction(calibrate.calibrate_sensors)),
            ("Laser", AsyncAction(calibrate.calibrate_distance)),
        ]),
        ("Info", [
            ("Raw Data", AsyncAction(raw_readings)),
            ("Tidy Data", AsyncAction(calibrated_readings)),
            ("Orientation", AsyncAction(orientation)),
            ("Device", AsyncAction(device)),
        ]),
        ("Settings", [
            ("Timeout", ConfigOptions(
                name="timeout", obj=cfg,
                options=[
                    ("30 seconds", 30),
                    ("1 minute", 60),
                    ("2 minutes", 120),
                    ("3 minutes", 180),
                    ("5 minutes", 300),
                ]
            )),
            ("Units", ConfigOptions(
                name="units", obj=cfg,
                options=[
                    ("Metric", Config.METRIC),
                    ("Imperial", Config.IMPERIAL)],
            )),
            ("Angles", ConfigOptions(
                name="angles", obj=cfg,
                options=[
                    ("Degrees", Config.DEGREES),
                    ("Grads", Config.GRADS)],
            )),
            ("Anomaly Detection", ConfigOptions(
                name="anomaly_strictness", obj=cfg,
                options=[
                    ("Off", None),
                    ("Relaxed", config.SOFT_STRICTNESS),
                    ("Strict", config.HARD_STRICTNESS)],
            )),
        ]),
        ("Bluetooth", [
            ("Disconnect", devices.bt.disconnect),
            ("Forget pairings", devices.bt.forget),
        ])
    ]
    debug_items = [
        ("Debug", [
            ("Cal From Saved", AsyncAction(calibrate.reset_to_calibrate)),
            ("Test item", AsyncAction(menu_item_test)),
            ("Freeze", freeze),
            ("ValueError", breaker),
        ])
    ]
    if logger.getEffectiveLevel() <= INFO:
        items.extend(debug_items)
    menu_root = disp.get_menu()
    # noinspection PyTypeChecker
    build_menu(menu_root, items)
    menu_root.show_menu()
    disp.refresh()
    while True:
        button, _ = await devices.both_buttons.wait(a=Button.SINGLE, b=Button.SINGLE)
        if button == "a":
            devices.beep_bip()
            logger.debug("Menu: Click")
            gc.collect()
            menu_root.click()
            if action_item is not None:
                logger.debug(f"Running {action_item}")
                await action_item(devices, cfg, disp)
                action_item = None
            menu_root.show_menu()
            disp.refresh()
        elif button == "b":
            logger.debug("Menu: Scroll")
            gc.collect()
            devices.beep_bop()
            menu_root.scroll(1)
            menu_root.show_menu()
            disp.refresh()


def freeze():
    # stop everything for 10 seconds - should trigger watchdog
    time.sleep(10)
    time.sleep(10)


def dummy():
    pass


def breaker():
    # noinspection PyUnresolvedReferences,PyUnusedLocal
    a = b


# noinspection PyUnusedLocal
async def menu_item_test(devices: hardware.Hardware, cfg: config.Config, disp: display.Display):
    for i in range(5):
        await asyncio.sleep(1)
        disp.show_info(f"MENU TEST: {i}\r\nPhil was here\r\nHere is a very long line " +
                       f"indeed")
