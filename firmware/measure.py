import asyncio
import json

from async_button import Button
from laser_egismos import LaserError
# noinspection PyProtectedMember
from mag_cal import MagneticAnomalyError, DipAnomalyError, GravityAnomalyError, NotCalibrated

LASER_TIMEOUT = 4.5

try:
    # noinspection PyUnresolvedReferences
    from typing import Dict
except ImportError:
    pass

from . import config
from . import display
from . import hardware
from .data import readings, Leg
from .debug import logger
from .utils import check_mem

ERROR_MESSAGES: Dict[type, str] = {
    LaserError: "Laser\nRead\nFailed",
    asyncio.TimeoutError: "Laser\nRead\nTimeout",
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
    # need to switch display to measurement here...
    logger.debug("Showing start screen")
    check_mem("start screen")
    disp.show_start_screen()
    check_mem("startup shown")
    logger.debug("turning on laser")
    devices.laser_enable(True)
    await asyncio.sleep(0.1)
    logger.debug("turning on laser light")
    await devices.laser.set_buzzer(False)
    while True:
        try:
            await devices.laser.set_laser(True)
        except LaserError:
            # possibly received a timeout last time around
            pass
        btn, click = await devices.both_buttons.wait(a=[Button.SINGLE, Button.LONG],
                                                     b=Button.SINGLE)
        check_mem("button pressed")
        if btn == "a":
            if click == Button.SINGLE:
                await asyncio.sleep(0.3)
            # long click should start timer.
            if click == Button.LONG:
                for i in range(cfg.timer):
                    devices.beep_bip()
                    await asyncio.sleep(1)
            success = await take_reading(devices, cfg, disp)
        elif btn == "b":
            logger.debug("B pressed")
            readings.get_prev_reading()
            success = True
        # noinspection PyUnboundLocalVariable
        if readings.current_reading is not None and success:
            disp.update_measurement(readings.current, readings.current_reading)


async def get_raw_measurement(devices: hardware.Hardware, disp: display.Display, with_laser: bool = True):
    logger.info("Taking a reading")
    try:
        disp.oled.sleep()
        if with_laser:
            devices.laser.async_reader.s.read() # clear the buffer
            distance = await asyncio.wait_for(devices.laser.measure(), LASER_TIMEOUT) / 1000
        else:
            distance = None
        logger.debug(f"Raw Distance: {distance}m")
        await devices.laser.set_laser(False)
        await asyncio.sleep(0.1)
        mag = devices.magnetometer.magnetic
        logger.debug(f"Mag: {mag}")
        grav = devices.accelerometer.acceleration
        logger.debug(f"Grav: {grav}")
        await asyncio.sleep(0.1)
        await devices.laser.set_laser(True)
    finally:
        disp.oled.wake()
    return mag, grav, distance

async def take_reading(devices: hardware.Hardware,
                       cfg: config.Config,
                       disp: display.Display) -> bool:
    # take a reading
    try:
        mag, grav, distance = await get_raw_measurement(devices, disp, True)
        if cfg.calib is None:
            raise NotCalibrated()
        azimuth, inclination, _ = cfg.calib.get_angles(mag, grav)
        distance += cfg.laser_cal
        logger.debug(f"Distance: {distance}m")
        if cfg.anomaly_strictness is not None:
            cfg.calib.raise_if_anomaly(mag, grav, cfg.anomaly_strictness)
    except tuple(ERROR_MESSAGES.keys()) as exc:
        for key in ERROR_MESSAGES.keys():
            if isinstance(exc, key):
                disp.show_big_info(ERROR_MESSAGES[key])
        logger.info(f"Measurement error: {repr(exc)}")
        if not isinstance(exc, asyncio.TimeoutError):
            # don't wibble the laser if it's timed out, it'll just get more confused
            for i in range(5):
                await devices.laser.set_laser(False)
                await asyncio.sleep(0.1)
                await devices.laser.set_laser(True)
                await asyncio.sleep(0.1)
        devices.beep_sad()
        return False
    else:
        leg = Leg(azimuth, inclination, distance)
        readings.store_reading(leg, cfg)
        devices.bt.disto.send_data(azimuth, inclination, distance)
        if readings.triple_shot():
            for _ in range(2):
                await devices.laser.set_laser(False)
                await asyncio.sleep(0.2)
                await devices.laser.set_laser(True)
                await asyncio.sleep(0.2)
            devices.beep_happy()
        else:
            devices.beep_bip()
        return True


async def take_multiple_readings(devices, disp, fname, prelude, reminder):
    devices.laser_enable(True)
    disp.show_info(prelude)
    await devices.button_a.wait(Button.SINGLE)
    await devices.laser.set_laser(True)
    mags = []
    gravs = []
    count = 0
    while True:
        disp.show_info(f"Legs: {count}\r\n{reminder}")
        button, click = await devices.both_buttons.wait(a=(Button.SINGLE, Button.LONG), b=Button.SINGLE)
        if button == "a":
            if click == Button.SINGLE:
                await asyncio.sleep(0.5)
            mag, grav, _ = await get_raw_measurement(devices, disp, False)
            mags.append(mag)
            gravs.append(grav)
            devices.beep_bip()
        elif button == "b":
            devices.beep_bop()
            break
        count += 1
    try:
        # save data if we can
        with open(fname, "w") as f:
            json.dump({"mag": mags, "grav": gravs}, f)
    except OSError:
        pass

async def save_multiple_shots(devices: hardware.Hardware, cfg: config.Config, disp: display.Display):
    prelude = "Press A\r\nto start recording\r\nPress B to stop"
    reminder = "Press B to stop"
    fname = "debug_shots.json"
    await take_multiple_readings(devices, disp, fname, prelude, reminder)
