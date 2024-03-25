import asyncio
from os import uname

from . import config
from . import display
from . import hardware
from .version import get_long_name, get_short_name, get_sw_version, get_hw_version_as_str


# noinspection PyUnusedLocal
async def raw_readings(devices: hardware.HardwareBase, cfg: config.Config, disp: display.DisplayBase):
    while True:
        try:
            await asyncio.wait_for(devices.button_a.wait_for_click(), 0.5)
            return
        except asyncio.TimeoutError:
            pass
        acc = devices.accelerometer.acceleration
        mag = devices.magnetometer.magnetic
        text = "Raw Accel Mag\r\n"
        for axis, a, m in zip("XYZ", acc, mag):
            text += f"{axis}   {a:05.3f} {m:05.2f}\r\n"
        text += f"Voltage: {devices.batt_voltage:4.2f}V"
        disp.show_info(text)


async def calibrated_readings(devices: hardware.HardwareBase, cfg: config.Config, disp: display.DisplayBase):
    if cfg.calib is None:
        disp.show_info("Device not\r\ncalibrated")
        await devices.button_a.wait_for_click()
        return
    while True:
        try:
            await asyncio.wait_for(devices.button_a.wait_for_click(), 0.5)
            return
        except asyncio.TimeoutError:
            pass
        grav = devices.accelerometer.acceleration
        mag = devices.magnetometer.magnetic
        # noinspection PyTypeChecker
        mag_strength, grav_strength = cfg.calib.get_field_strengths(mag, grav)
        grav = cfg.calib.grav.apply(grav)
        mag = cfg.calib.mag.apply(mag)
        text = "    Grav  Mag\r\n"
        for axis, g, m in zip("XYZ", grav, mag):
            text += f"{axis}   {g: 05.3f} {m: 05.3f}\r\n"
        text += f"|V| {grav_strength: 05.3f} {mag_strength: 05.3f}\r\n"
        disp.show_info(text)


# noinspection PyTypeChecker
async def orientation(devices: hardware.HardwareBase, cfg: config.Config, disp: display.DisplayBase):
    if cfg.calib is None:
        disp.show_info("Device not\r\ncalibrated")
        await devices.button_a.wait_for_click()
        return
    while True:
        try:
            await asyncio.wait_for(devices.button_a.wait_for_click(), 0.5)
            return
        except asyncio.TimeoutError:
            pass
        grav = devices.accelerometer.acceleration
        mag = devices.magnetometer.magnetic
        heading, inclination, roll = cfg.calib.get_angles(mag, grav)
        dip = cfg.calib.get_dips(mag, grav)
        text = f"""
            Compass: {cfg.get_azimuth_text(heading)}
            Inclination: {cfg.get_inclination_text(inclination)}
            Roll: {cfg.get_inclination_text(roll)}
            Dip: {cfg.get_inclination_text(dip)}
        """
        disp.show_info(text, clean=True)


# noinspection PyUnusedLocal
async def device(devices: hardware.HardwareBase, cfg: config.Config, disp: display.DisplayBase):
    import gc
    gc.collect()
    mem_free = gc.mem_free()
    text = f"""
        {get_long_name()} ({get_short_name()})
        SW Version: {get_sw_version()}
        HW: {get_hw_version_as_str()} CP: {uname().release}
        Mem Free: {mem_free}
        """
    disp.show_info(text, clean=True)
    await devices.button_a.wait_for_click()
