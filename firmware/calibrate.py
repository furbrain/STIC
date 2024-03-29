import asyncio
import mag_cal
from async_button import Button
import json
import microcontroller

try:
    import numpy as np
    WatchDogTimeout = None
except ImportError:
    # noinspection PyUnresolvedReferences
    from ulab import numpy as np
    # noinspection PyPackageRequirements
    from watchdog import WatchDogTimeout

from . import utils
from . import config
from .debug import logger

# import display and hardware only for type checking - does not import on device
try:
    # noinspection PyUnresolvedReferences
    from typing import Optional
    # noinspection PyUnresolvedReferences
    from . import display
    # noinspection PyUnresolvedReferences
    from . import hardware
except ImportError:
    pass

# patch mag_cal to use cholesky least squares
mag_cal.utils.lstsq.lstsq = utils.lstsq

CAL_DATA_FILE = "calibration_data.json"
CAL_DUE = b"CALIBRATE_ME"
CAL_DONE = b"CALIB DONE"

cal = None
accuracy: Optional[float] = None


async def calibrate_sensors(devices: hardware.HardwareBase, cfg: config.Config, disp: display.DisplayBase):
    from . import measure
    prelude = "Take a series of\r\nreadings, press\r\nA for a leg,\r\nB to finish"
    reminder = "Ideally at least 24\r\nWith two groups\r\nin same direction"
    fname = CAL_DATA_FILE
    mags, gravs = await measure.take_multiple_readings(devices, disp, fname, prelude, reminder)
    mags = np.array(mags)
    gravs = np.array(gravs)
    await live_calibration(mags, gravs, devices, cfg, disp)


async def cal_from_saved(devices: hardware.HardwareBase, cfg: config.Config, disp: display.DisplayBase):
    global cal, accuracy
    with open(CAL_DATA_FILE) as f:
        data = json.load(f)
    mag_data, grav_data = np.array(data['mag']), np.array(data['grav'])
    del data
    await live_calibration(mag_data, grav_data, devices, cfg, disp)


async def live_calibration(mag_data, grav_data, devices, cfg, disp):
    updater = utils.Updater(disp)
    global cal, accuracy
    try:
        await updater.update("Starting calibration")
        cal = mag_cal.Calibration(mag_axes=cfg.mag_axes, grav_axes=cfg.grav_axes)
        await updater.update("Fitting Ellipsoid")
        cal.fit_ellipsoid(mag_data, grav_data)
        await updater.update("Finding runs")
        runs = cal.find_similar_shots(mag_data, grav_data)
        if len(runs) == 0:
            raise ValueError("No runs of shots all in the same direction found")
        paired_data = [(mag_data[a:b], grav_data[a:b]) for a, b in runs]
        await updater.update("Fitting Axes")
        cal.fit_to_axis(paired_data)
        await updater.update("Non-linear adjust")
        cal.fit_non_linear_quick(paired_data)
        cal.set_field_characteristics(mag_data, grav_data)
        accuracy = cal.accuracy(paired_data)
    except (MemoryError, WatchDogTimeout):
        await reset_to_calibrate(devices, cfg, disp)
    else:
        await show_cal_results(devices, cfg, disp)


async def show_cal_results(devices: hardware.HardwareBase, cfg: config.Config, disp: display.DisplayBase):
    global cal, accuracy
    if isinstance(cal, Exception):
        raise cal
    if cal is None or accuracy is None:
        logger.debug(f"No calibration needed: cal {cal} accuracy {accuracy}")
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


# noinspection PyUnusedLocal
async def reset_to_calibrate(devices: hardware.HardwareBase, cfg: config.Config, disp: display.DisplayBase):
    disp.show_info("""
        Resetting to run
        calibration. The
        screen will blank
        for a few seconds
    """, clean=True)
    await asyncio.sleep(3)
    devices.beep_shutdown()
    utils.set_nvm(CAL_DUE)
    await devices.buzzer.wait()
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


async def calibrate_distance(devices: hardware.HardwareBase, cfg: config.Config, disp: display.DisplayBase):
    devices.laser_enable(True)
    disp.show_info("Place device\r\n1m from an object\r\nand press A")
    await devices.button_a.wait(Button.SINGLE)
    disp.show_info("Measuring...\r\nDo not touch\r\ndevice")
    await asyncio.sleep(1)
    dist = 0
    for i in range(10):
        dist += await devices.laser_measure()
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
    cfg.laser_cal = dist / 1000
    cfg.save()
    disp.show_info("Calibration complete")
