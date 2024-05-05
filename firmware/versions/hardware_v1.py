import asyncio
import time

import async_button
import async_buzzer
import atexit
import busio
import digitalio
import displayio
import laser_egismos
import pwmio
import rm3100
import seeed_xiao_nrf52840

from .. import bluetooth
from .. import config
from .. import invertingpwmio
from ..debug import logger
from ..hardware import HardwareBase


class Hardware(HardwareBase):
    def __init__(self, pins):
        logger.debug("Initialising hardware")
        super().__init__()
        import displayio
        displayio.release_displays()
        self._las_en_pin = digitalio.DigitalInOut(pins.LASER_EN)
        self._las_en_pin.switch_to_output(False)
        self._peripheral_enable_io = digitalio.DigitalInOut(pins.PERIPH_EN)
        self._peripheral_enable_io.switch_to_output(True)
        time.sleep(0.1)
        self.button_a = async_button.Button(pins.BUTTON_A, value_when_pressed=False, long_click_enable=True)
        self.button_b = async_button.Button(pins.BUTTON_B, value_when_pressed=False, long_click_enable=True)
        self.both_buttons = async_button.MultiButton(a=self.button_a, b=self.button_b)
        self._i2c = busio.I2C(scl=pins.SCL, sda=pins.SDA, frequency=4000000)
        self._drdy_io = digitalio.DigitalInOut(pins.DRDY)
        self._drdy_io.direction = digitalio.Direction.INPUT
        # noinspection PyTypeChecker
        self.magnetometer = rm3100.RM3100_I2C(self._i2c, drdy_pin=self._drdy_io, cycle_count=2000)
        self._uart = busio.UART(pins.TX, pins.RX, baudrate=9600, timeout=0.1)
        self._uart.reset_input_buffer()
        self._laser = laser_egismos.AsyncLaser(self._uart)
        if pins.BUZZER_B is None:
            self._pwm = pwmio.PWMOut(pins.BUZZER_A, variable_frequency=True)
        else:
            self._pwm = invertingpwmio.InvertingPWMOut(pins.BUZZER_A, pins.BUZZER_B)
        self.buzzer = async_buzzer.Buzzer(self._pwm)
        self._battery = seeed_xiao_nrf52840.Battery()
        self.accelerometer: seeed_xiao_nrf52840.IMU = seeed_xiao_nrf52840.IMU()
        self.bt = bluetooth.BluetoothServices()
        self._atexit_handler = self.deinit
        atexit.register(self._atexit_handler)

    def create_display(self, cfg: config.Config):
        try:
            # try to load using 9.0 style, fall back to 8.x style
            from i2cdisplaybus import I2CDisplayBus as I2CDisplay
        except ImportError:
            from displayio import I2CDisplay
        from . import display128x64
        import adafruit_displayio_sh1106
        bus = I2CDisplay(self._i2c, device_address=0x3c)
        # noinspection PyTypeChecker
        oled = adafruit_displayio_sh1106.SH1106(bus,
                                                width=display128x64.WIDTH,
                                                height=display128x64.HEIGHT,
                                                rotation=0,
                                                auto_refresh=False,
                                                colstart=2)

        return display128x64.Display(oled, cfg)

    def laser_enable(self, value: bool) -> None:
        self._las_en_pin.value = value

    async def laser_on(self, value: bool) -> None:
        await self._laser_mutex()
        await self._laser.set_laser(value)

    async def _laser_mutex(self):
        """This function waits for the laser task to complete before proceeding"""
        if self.laser_task and not self.laser_task.done():
            if asyncio.current_task() is not self.laser_task:
                #don't wait if we're actually *in* the laser task
                await self.laser_task

    async def laser_measure(self) -> float:
        await self._laser_mutex()
        self._laser.async_reader.s.read()  # clear the buffer
        return await self._laser.measure()

    def peripherals_enable(self, value: bool) -> None:
        self._peripheral_enable_io.value = value

    @property
    def batt_voltage(self):
        return self._battery.voltage

    def charge_status(self):
        return self._battery.charge_status

    def deinit(self):
        # release display
        displayio.release_displays()
        time.sleep(0.1)
        self._las_en_pin.value = False
        self.bt.deinit()
        self.accelerometer.deinit()
        self._battery.deinit()
        self._pwm.deinit()
        self._uart.deinit()
        self._i2c.deinit()
        self._drdy_io.deinit()
        try:
            self.button_b.deinit()
        except KeyError:
            pass
        try:
            self.button_a.deinit()
        except KeyError:
            pass
        self._peripheral_enable_io.value = False
        time.sleep(0.1)
        self._las_en_pin.deinit()
        self._peripheral_enable_io.deinit()
        atexit.unregister(self._atexit_handler)
