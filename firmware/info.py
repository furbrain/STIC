import asyncio
from os import uname

import config
import display
import hardware
from version import get_long_name, get_short_name, __version__, get_sw_version, get_hw_version


async def raw_readings(devices: hardware.Hardware, config: config.Config, display: display.Display):
    while True:
        try:
            await asyncio.wait_for(devices.button_a.wait_for_click(), 0.5)
            return
        except asyncio.TimeoutError:
            pass
        acc = devices.accelerometer.acceleration
        mag = devices.magnetometer.magnetic
        text = "Raw Accel Mag\r\n"
        for axis,a,m in zip("XYZ",acc,mag):
            text += f"{axis}   {a:05.3f} {m:05.2f}\r\n"
        display.show_info(text)


async def calibrated_readings(devices: hardware.Hardware, config: config.Config, display: display.Display):
    while True:
        try:
            await asyncio.wait_for(devices.button_a.wait_for_click(), 0.5)
            return
        except asyncio.TimeoutError:
            pass
        grav = devices.accelerometer.acceleration
        mag = devices.magnetometer.magnetic
        grav_strength, mag_strength = config.calib.get_field_strengths(mag, grav)
        grav = config.calib.grav.apply(grav)
        mag = config.calib.mag.apply(mag)
        text = "    Grav  Mag\r\n"
        for axis, g, m in zip("XYZ", grav, mag):
            text += f"{axis}   {g: 05.3f} {m: 05.3f}\r\n"
        text += f"|V| {grav_strength: 05.3f} {mag_strength: 05.3f}"
        display.show_info(text)


async def orientation(devices: hardware.Hardware, config: config.Config, display: display.Display):
    while True:
        try:
            await asyncio.wait_for(devices.button_a.wait_for_click(),0.5)
            return
        except asyncio.TimeoutError:
            pass
        grav = devices.accelerometer.acceleration
        mag = devices.magnetometer.magnetic
        heading, inclination, roll = config.calib.get_angles(mag, grav)
        dip = config.calib.get_dips(mag, grav)
        text = f"""
            Heading: {config.get_azimuth_text(heading)}
            Inclination: {config.get_inclination_text(inclination)}
            Roll: {config.get_inclination_text(roll)}
            Dip: {config.get_inclination_text(dip)}
        """
        display.show_info(text, clean=True)


async def device(devices: hardware.Hardware, config: config.Config, display: display.Display):
    text = f"""
        Name: {get_long_name()}
        BT Name: {get_short_name()}
        SW Version: {get_sw_version()}
        HW Version: {get_hw_version()}
        CP Version: {uname().release}
        """
    display.show_info(text, clean=True)
    await devices.button_a.wait_for_click()
