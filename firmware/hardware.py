import atexit
import time

import laser_egismos
import pwmio

import pins
from utils import cached_property


try:
    from typing import Optional
    import display
    import async_button
    import async_buzzer
    import displayio
    import rm3100
    import invertingpwmio
    import seeed_xiao_nrf52840
    from laser_egismos import Laser

    from busio import I2C

except ImportError:
    pass

import busio
import digitalio


# Pin definitions

HAPPY = (("C6", 50), ("E6", 50), ("G6", 50), ("C7", 50))
BIP = (("A7", 50),)
BOP = (("C7", 50),)
SAD = (("G6", 100), ("C6", 200))


# noinspection PyAttributeOutsideInit
class Hardware:
    def __init__(self):
        import displayio
        displayio.release_displays()
        self.las_en_pin = digitalio.DigitalInOut(pins.LASER_EN)
        self.las_en_pin.switch_to_output(False)
        self.periph_enable_io = digitalio.DigitalInOut(pins.PERIPH_EN)
        self.periph_enable_io.switch_to_output(True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deinit()

    @cached_property
    def button_a(self) -> async_button.Button:
        """ Async Button for Button A"""
        import async_button
        return async_button.Button(pins.BUTTON_A, value_when_pressed=False)

    @cached_property
    def button_b(self) -> async_button.Button:
        """ Async Button for Button B"""
        import async_button
        return async_button.Button(pins.BUTTON_B, value_when_pressed=False, long_click_enable=True)

    @cached_property
    def both_buttons(self) -> async_button.MultiButton:
        """ Multibutton for both buttons"""
        import async_button
        return async_button.MultiButton(a=self.button_a, b=self.button_b)

    @cached_property
    def magnetometer(self) -> rm3100._RM3100:
        """ RM3100 magnetometer """
        import rm3100
        self.drdy_io = digitalio.DigitalInOut(pins.DRDY)
        self.drdy_io.direction = digitalio.Direction.INPUT
        return rm3100.RM3100_I2C(self.i2c, drdy_pin=self.drdy_io)

    @cached_property
    def i2c(self) -> busio.I2C:
        from busio import I2C
        return I2C(scl=pins.SCL, sda=pins.SDA, frequency=4000000)

    @cached_property
    def laser(self) -> laser_egismos.AsyncLaser:
        from laser_egismos import AsyncLaser
        import busio
        self.uart = busio.UART(pins.TX, pins.RX, baudrate=9600)
        return AsyncLaser(self.uart)

    def laser_enable(self, value: bool) -> None:
        self.las_en_pin.value = value

    @cached_property
    def buzzer(self) -> async_buzzer.Buzzer:
        """Buzzer"""
        import async_buzzer
        import invertingpwmio
        self.pwm = invertingpwmio.InvertingPWMOut(pins.BUZZER_A, pins.BUZZER_B)
        return async_buzzer.Buzzer(self.pwm)

    @cached_property
    def battery(self) -> seeed_xiao_nrf52840.Battery:
        import seeed_xiao_nrf52840
        return seeed_xiao_nrf52840.Battery()

    @property
    def batt_voltage(self) -> float:
        return self.battery.voltage

    @cached_property
    def accelerometer(self):
        import seeed_xiao_nrf52840
        return seeed_xiao_nrf52840.IMU()

    def beep_happy(self):
        self.buzzer.play(HAPPY)

    def beep_shutdown(self):
        self.buzzer.play(reversed(HAPPY))

    def beep_bip(self):
        self.buzzer.play(BIP)

    def beep_bop(self):
        self.buzzer.play(BOP)

    def beep_sad(self):
        self.buzzer.play(SAD)

    async def beep_wait(self):
        await self.buzzer.wait()

    def deinit(self):
        # release display
        import displayio
        displayio.release_displays()
        for attr in self.__dict__.values():
            if attr is not None and hasattr(attr, "deinit"):
                attr.deinit()
