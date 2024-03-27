import asyncio
import gc

from async_button import Button
from fruity_menu.builder import build_menu, Action, Options

from . import measure
from . import calibrate
from . import config
from . import display
from . import hardware
from . import info
from . import debug
from .debug import logger
from .config import Config


try:
    # noinspection PyUnresolvedReferences
    from typing import Callable, Optional, Coroutine, Any

    AsyncActionItem = Optional[Callable[[hardware.HardwareBase, config.Config, display.DisplayBase], Coroutine]]
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


async def menu(devices: hardware.HardwareBase, cfg: config.Config, disp: display.DisplayBase):
    global action_item
    logger.debug("Menu task started")
    gc.collect()
    devices.laser_enable(True)
    await asyncio.sleep(0.1)
    await devices.laser_on(False)
    items = [
        ("Calibrate", [
            ("Sensors", AsyncAction(calibrate.calibrate_sensors)),
            ("Laser", AsyncAction(calibrate.calibrate_distance)),
            ("Cal From Saved", AsyncAction(calibrate.reset_to_calibrate)),
        ]),
        ("Info", [
            ("Raw Data", AsyncAction(info.raw_readings)),
            ("Calibrated Data", AsyncAction(info.calibrated_readings)),
            ("Orientation", AsyncAction(info.orientation)),
            ("Device", AsyncAction(info.device)),
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
            ("Shot Timer", ConfigOptions(
                name="timer", obj=cfg,
                options=[
                    ("0 seconds", 0),
                    ("3 seconds", 3),
                    ("5 seconds", 5),
                    ("10 seconds", 10),
                ]
            )),
            ("Distance Units", ConfigOptions(
                name="units", obj=cfg,
                options=[
                    ("Metric", Config.METRIC),
                    ("Imperial", Config.IMPERIAL)],
            )),
            ("Angle Units", ConfigOptions(
                name="angles", obj=cfg,
                options=[
                    ("Degrees", Config.DEGREES),
                    ("Grads", Config.GRADS)],
            )),
            ("Precision", ConfigOptions(
                name="low_precision", obj=cfg,
                options=[
                    ("Low", True),
                    ("Full", False),
                ]
            )),
            ("Show Extents", ConfigOptions(
                name="extended", obj=cfg,
                options=[
                    ("On", True),
                    ("Off", False),
                ]
            )),

            ("Anomaly Detection", ConfigOptions(
                name="anomaly_strictness", obj=cfg,
                options=[
                    ("Off", None),
                    ("Relaxed", config.SOFT_STRICTNESS),
                    ("Strict", config.HARD_STRICTNESS)],
            )),
            ("Save Readings", ConfigOptions(
                name="save_readings", obj=cfg,
                options=[
                    ("Off", False),
                    ("On", True),
                ]
            ))
        ]),
        ("Bluetooth", [
            ("Disconnect", devices.bt.disconnect),
            ("Forget pairings", devices.bt.forget),
        ])
    ]
    debug_items = [
        ("Debug", [
            ("Save shots", AsyncAction(measure.save_multiple_shots)),
            ("Battery test", AsyncAction(debug.battery_test)),
            ("Freeze", debug.freeze),
            ("ValueError", debug.breaker),
        ])
    ]
    if logger.getEffectiveLevel() <= debug.INFO:
        items.extend(debug_items)
    menu_root = disp.get_menu()
    # noinspection PyTypeChecker
    build_menu(menu_root, items)
    # clear display memory and dicts before show group to minimise memory usage
    disp.clear_memory()
    del items, debug_items
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
            # clear memory before show group to minimise memory usage
            disp.clear_memory()
            menu_root.show_menu()
            disp.refresh()
        elif button == "b":
            logger.debug("Menu: Scroll")
            gc.collect()
            devices.beep_bop()
            menu_root.scroll(1)
            # clear memory before show group to minimise memory usage
            disp.clear_memory()
            menu_root.show_menu()
            disp.refresh()

# noinspection PyUnusedLocal
