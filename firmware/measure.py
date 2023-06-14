import asyncio

from async_button import Button
from laser_egismos import LaserError
from mag_cal import MagneticAnomalyError, DipAnomalyError, GravityAnomalyError, NotCalibrated

from data import readings, Leg
import adafruit_logging as logging

logger = logging.getLogger()


async def measure(devices, config, display):
    """
    This is the main measurement task
    :return:
    """
    from data import readings
    #need to switch display to measurement here...
    logger.debug("Showing start screen")
    display.show_start_screen()
    logger.debug("turning on laser")
    devices.laser_enable(True)
    await asyncio.sleep(0.1)
    logger.debug("turning on laser light")
    while True:
        await devices.laser.set_laser(True)
        btn, click = await devices.both_buttons.wait(a=Button.SINGLE, b=Button.SINGLE)
        if btn == "a":
            # take a reading
            logger.info("Taking a reading")
            mag = devices.magnetometer.magnetic
            logger.debug(f"Mag: {mag}")
            grav = devices.accelerometer.acceleration
            logger.debug(f"Grav: {grav}")
            try:
                azimuth, inclination, _ = config.calib.get_angles(mag, grav)
                distance = await asyncio.wait_for(devices.laser.measure(), 3.0) / 1000
                logger.debug(f"Distance: {distance}m")
                config.calib.raise_if_anomaly(mag, grav, config.anomaly_strictness)
            except LaserError as exc:
                logger.info("Laser read failed")
                logger.info(exc)
                display.show_big_info(f"Laser Fail:\n{exc.__class__.__name__}\n{exc}")
                devices.beep_sad()
                continue
            except (MagneticAnomalyError,DipAnomalyError) as exc:
                logger.info("Magnetic Anomaly")
                logger.info(exc)
                display.show_big_info("Magnetic\nAnomaly:\nIron nearby?")
                devices.beep_sad()
                continue
            except GravityAnomalyError as exc:
                logger.info("Gravity Anomaly")
                logger.info(exc)
                display.show_big_info("Device\nMovement\nDetected")
                devices.beep_sad()
                continue
            except NotCalibrated as exc:
                logger.info("Device not calibrated")
                logger.info(exc)
                display.show_big_info("Calibration\nneeded\nHold B 3s")
                devices.beep_sad()
            readings.store_reading(Leg(azimuth, inclination, distance))
            devices.bt.disto.send_data(azimuth, inclination, distance)
            devices.beep_bip()
        elif btn == "b":
            logger.debug("B pressed")
            readings.get_prev_reading()
        if readings.current_reading is not None:
            display.update_measurement(readings.current, readings.current_reading)