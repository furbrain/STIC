import asyncio

import async_button
import async_buzzer

try:
    from typing import Optional
except ImportError:
    pass

from . import bluetooth
from .stubs import Magnetometer, Accelerometer, abstractmethod

HAPPY = (("C6", 50.0), ("E6", 50.0), ("G6", 50.0), ("C7", 50.0))
BIP = (("A7", 50),)
BOP = (("C7", 50),)
SAD = (("G6", 100), ("C6", 200))


# noinspection PyAttributeOutsideInit
class HardwareBase:
    button_a: async_button.Button
    button_b: async_button.Button
    both_buttons: async_button.MultiButton
    buzzer: async_buzzer.Buzzer
    magnetometer: Magnetometer
    accelerometer: Accelerometer
    bt: bluetooth.BluetoothServices
    batt_voltage: float

    def __init__(self):
        self.laser_task: Optional[asyncio.Task] = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deinit()

    @abstractmethod
    def create_display(self, cfg):
        pass

    @abstractmethod
    def laser_enable(self, value):
        pass

    @abstractmethod
    async def laser_on(self, value):
        pass

    def flash_laser(self, count: int, speed: float):
        if self.laser_task:
            if not self.laser_task.done():
                self.laser_task.cancel()
        self.laser_task = asyncio.create_task(self._flash_laser(count, speed))

    async def _flash_laser(self, count: int, speed: float):
        for _ in range(count):
            await self.laser_on(False)
            await asyncio.sleep(speed)
            await self.laser_on(True)
            await asyncio.sleep(speed)

    @abstractmethod
    async def laser_measure(self):
        pass

    @abstractmethod
    def peripherals_enable(self, value):
        pass

    def beep_happy(self):
        self.buzzer.play(HAPPY)

    def beep_shutdown(self):
        # noinspection PyTypeChecker
        self.buzzer.play(reversed(HAPPY))

    def beep_bip(self):
        self.buzzer.play(BIP)

    def beep_bop(self):
        self.buzzer.play(BOP)

    def beep_sad(self):
        self.buzzer.play(SAD)

    async def beep_wait(self):
        await self.buzzer.wait()

    @abstractmethod
    def charge_status(self):
        pass

    @abstractmethod
    def deinit(self):
        pass


