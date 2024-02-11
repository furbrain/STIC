import asyncio


try:
    # noinspection PyUnresolvedReferences
    from typing import Optional
except ImportError:
    pass

import mag_cal
from async_button import Button
import json
import microcontroller
try:
    import numpy as np
except ImportError:
    # noinspection PyUnresolvedReferences
    from ulab import numpy as np

from . import utils
from . import config
from .debug import logger

try:
    # noinspection PyUnresolvedReferences
    # import display and hardware only for type checking - does not import on device
    import typing
    from . import display
    from . import hardware
except ImportError:
    pass

CAL_DATA_FILE = "calibration_data.json"
CAL_DUE = b"CALIBRATE_ME"
CAL_DONE = b"CALIB DONE"

cal = None
accuracy: Optional[float] = None


async def calibrate_sensors(devices: hardware.Hardware, cfg: config.Config, disp: display.Display):
    from . import measure
    prelude = "Take a series of\r\nreadings, press\r\nA for a leg,\r\nB to finish"
    reminder = "Ideally at least 24\r\nWith two groups\r\nin same direction"
    fname = CAL_DATA_FILE
    await measure.take_multiple_readings(devices, disp, fname, prelude, reminder)
    await reset_to_calibrate(devices, cfg, disp)


# noinspection PyUnusedLocal
async def reset_to_calibrate(devices: hardware.Hardware, cfg: config.Config, disp: display.Display):
    disp.show_info("""
        Resetting to run
        calibration. The
        screen will blank
        for a few seconds
    """, clean=True)
    await asyncio.sleep(3)
    utils.set_nvm(CAL_DUE)
    microcontroller.reset()


def calibration_due():
    return utils.check_nvm(CAL_DUE)


def calibrate_if_due():
    global cal, accuracy
    if not calibration_due():
        logger.debug("No calibration due")
        logger.debug(microcontroller.nvm[0:10])
        return
    utils.clear_nvm()
    try:
        logger.debug("Loading calibration data")
        cfg = config.Config.load()
        with open(CAL_DATA_FILE) as f:
            data = json.load(f)
        logger.debug("Running calibration")
        cal = mag_cal.Calibration(mag_axes=cfg.mag_axes, grav_axes=cfg.grav_axes)
        logger.debug("Checking accuracy")
        accuracy = cal.calibrate(np.array(data['mag']), np.array(data['grav']))
    except Exception as e:
        cal = e
        return


async def show_cal_results(devices: hardware.Hardware, cfg: config.Config,
                           disp: display.Display):
    global cal, accuracy
    if isinstance(cal, Exception):
        raise cal
    if cal is None or accuracy is None:
        logger.debug(f"No calibration needed: cal {cal!r} accuracy {accuracy!r}")
        return
    if accuracy < 0.25:
        quality = "excellent"
    elif accuracy < 0.5:
        quality = "good"
    elif accuracy < 1.0:
        quality = "acceptable"
    else:
        quality = "poor"
    logger.debug("Showing accuracy")
    report = f"Accuracy is {accuracy:.3f}°\r\nThis is {quality}\r\nPress A to Save\r\nB to Discard"
    disp.show_info(report)
    button, click = await devices.both_buttons.wait(a=Button.SINGLE, b=Button.SINGLE)
    if button == "a":
        cfg.calib = cal
        cfg.save()
    elif button == "b":
        pass
    cal = None


async def calibrate_distance(devices: hardware.Hardware, cfg: config.Config, disp: display.Display):
    devices.laser_enable(True)
    disp.show_info("Place device\r\n1m from an object\r\nand press A")
    await devices.button_a.wait(Button.SINGLE)
    disp.show_info("Measuring...\r\nDo not touch\r\ndevice")
    await asyncio.sleep(1)
    dist = 0
    for i in range(10):
        dist += await devices.laser.measure()
        devices.beep_bip()
    dist /= 10.0
    dist = 1000 - dist
    if dist > 200:
        disp.show_info(f"Offset is {dist}mm\r\nThis seems very long\r\nAre you sure?\r\nA: Yes B: No")
        btn, _ = await devices.both_buttons.wait(a=Button.SINGLE, b=Button.SINGLE)
        if btn == "b":
            return
    elif dist < -50:
        text = f"Offset is {dist}mm\r\nThis seems very short\r\nAre you sure?\r\nA: Yes B: No"
        disp.show_info(text)
        btn, _ = await devices.both_buttons.wait(a=Button.SINGLE, b=Button.SINGLE)
        if btn == "b":
            return
    cfg.laser_cal = dist/1000
    cfg.save()
    disp.show_info("Calibration complete")
