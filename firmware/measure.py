import asyncio

from utils import check_mem

try:
    from typing import Dict
except ImportError:
    pass

from async_button import Button
from laser_egismos import LaserError
# noinspection PyProtectedMember
from mag_cal import MagneticAnomalyError, DipAnomalyError, GravityAnomalyError, NotCalibrated

import config
import display
import hardware
from data import readings, Leg
from debug import logger

ERROR_MESSAGES: Dict[type, str] = {
    MagneticAnomalyError: "Magnetic\nAnomaly:\nIron nearby?",
    DipAnomalyError: "Magnetic\nAnomaly:\nIron nearby?",
    NotCalibrated: "Calibration\nneeded\nHold B 3s",
    GravityAnomalyError: "Device\nMovement\nDetected",
}

async def measure(devices: hardware.Hardware, cfg: config.Config, disp: display.Display):
    """
    This is the main measurement task
    :return:
    """
    from data import readings
    #need to switch display to measurement here...
    logger.debug("Showing start screen")
    check_mem("start screen")
    disp.show_start_screen()
    check_mem("startup shown")
    logger.debug("turning on laser")
    devices.laser_enable(True)
    await asyncio.sleep(0.1)
    logger.debug("turning on laser light")
    while True:
        await devices.laser.set_laser(True)
        btn, click = await devices.both_buttons.wait(a=[Button.SINGLE, Button.LONG],
                                                     b=Button.SINGLE)
        check_mem("button pressed")
        if btn == "a":
            success = await take_reading(devices, cfg, disp)
        elif btn == "b":
            logger.debug("B pressed")
            readings.get_prev_reading()
            success = True
        if readings.current_reading is not None and success:
            disp.update_measurement(readings.current, readings.current_reading)


async def take_reading(devices: hardware.Hardware,
                       cfg: config.Config,
                       disp: display.Display) -> bool:
    # take a reading
    logger.info("Taking a reading")
    mag = devices.magnetometer.magnetic
    logger.debug(f"Mag: {mag}")
    grav = devices.accelerometer.acceleration
    logger.debug(f"Grav: {grav}")
    exc = None
    try:
        if cfg.calib is None:
            raise NotCalibrated()
        azimuth, inclination, _ = cfg.calib.get_angles(mag, grav)
        distance = await asyncio.wait_for(devices.laser.measure(), 3.0) / 1000
        distance += cfg.laser_cal
        logger.debug(f"Distance: {distance}m")
        cfg.calib.raise_if_anomaly(mag, grav, cfg.anomaly_strictness)
    except LaserError as exc:
        disp.show_big_info(f"Laser Fail:\n{exc.__class__.__name__}\n{exc}")
        logger.info(exc)
        devices.beep_sad()
        return False
    except tuple(ERROR_MESSAGES.keys()) as exc:
        disp.show_big_info(ERROR_MESSAGES[exc.__class__])
        logger.info(exc)
        devices.beep_sad()
        return False
    else:
        readings.store_reading(Leg(azimuth, inclination, distance))
        devices.bt.disto.send_data(azimuth, inclination, distance)
        devices.beep_bip()
        return True


