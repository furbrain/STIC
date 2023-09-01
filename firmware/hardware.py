import atexit
import time

import laser_egismos
import pwmio

import bluetooth
import pins
import async_button
import async_buzzer
import displayio
import rm3100
import invertingpwmio
import seeed_xiao_nrf52840

try:
    from typing import Optional
except ImportError:
    pass

import busio
import digitalio
from debug import logger


# Pin definitions

HAPPY = (("C6", 50.0), ("E6", 50.0), ("G6", 50.0), ("C7", 50.0))
BIP = (("A7", 50),)
BOP = (("C7", 50),)
SAD = (("G6", 100), ("C6", 200))


# noinspection PyAttributeOutsideInit
class Hardware:
    def __init__(self):
        logger.debug("Initialising hardware")
        import displayio
        displayio.release_displays()
        self.las_en_pin = digitalio.DigitalInOut(pins.LASER_EN)
        self.las_en_pin.switch_to_output(False)
        self.peripheral_enable_io = digitalio.DigitalInOut(pins.PERIPH_EN)
        self.peripheral_enable_io.switch_to_output(True)
        time.sleep(0.1)
        self.button_a = async_button.Button(pins.BUTTON_A, value_when_pressed=False)
        self.button_b = async_button.Button(pins.BUTTON_B, value_when_pressed=False,
                                            long_click_enable=True)
        self.both_buttons = async_button.MultiButton(a=self.button_a, b=self.button_b)
        self.i2c = busio.I2C(scl=pins.SCL, sda=pins.SDA, frequency=4000000)
        self.drdy_io = digitalio.DigitalInOut(pins.DRDY)
        self.drdy_io.direction = digitalio.Direction.INPUT
        self.magnetometer = rm3100.RM3100_I2C(self.i2c, drdy_pin=self.drdy_io)
        self.uart = busio.UART(pins.TX, pins.RX, baudrate=9600)
        self.uart.reset_input_buffer()
        self.laser = laser_egismos.AsyncLaser(self.uart)
        if pins.BUZZER_B is None:
            self.pwm = pwmio.PWMOut(pins.BUZZER_A, variable_frequency=True)
        else:
            self.pwm = invertingpwmio.InvertingPWMOut(pins.BUZZER_A, pins.BUZZER_B)
        self.buzzer = async_buzzer.Buzzer(self.pwm)
        self.battery = seeed_xiao_nrf52840.Battery()
        self.accelerometer = seeed_xiao_nrf52840.IMU()
        self.bt = bluetooth.BluetoothServices()
        self.atexit_handler = self.deinit
        atexit.register(self.atexit_handler)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deinit()

    def laser_enable(self, value: bool) -> None:
        self.las_en_pin.value = value

    @property
    def batt_voltage(self) -> float:
        return self.battery.voltage

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

    def deinit(self):
        # release display
        displayio.release_displays()
        time.sleep(0.1)
        self.las_en_pin.value = False
        self.bt.deinit()
        self.accelerometer.deinit()
        self.battery.deinit()
        self.pwm.deinit()
        self.uart.deinit()
        self.i2c.deinit()
        self.drdy_io.deinit()
        self.button_b.deinit()
        self.button_a.deinit()
        self.peripheral_enable_io.value = False
        time.sleep(0.1)
        self.las_en_pin.deinit()
        self.peripheral_enable_io.deinit()
        atexit.unregister(self.atexit_handler)
