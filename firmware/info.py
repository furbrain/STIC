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
        acc = devices.accelerometer.acceleration
        acc = config.calib.grav.apply(acc)
        mag = devices.magnetometer.magnetic
        mag = config.calib.mag.apply(mag)
        text = "    Accel Mag\r\n"
        for axis, a, m in zip("XYZ", acc, mag):
            text += f"{axis}   {a:05.3f} {m:05.2f}\r\n"
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
