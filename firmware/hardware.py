import atexit
import time


try:
    from typing import Optional
except ImportError:
    pass

import async_button
import board
import async_buzzer
import busio
import digitalio
import displayio
import rm3100
from laser_egismos import Laser
from busio import I2C

import invertingpwmio
import seeed_xiao_nrf52840

from display import SH1106_Display

#Pin definitions
LASER_EN = board.D0
RX = board.D1
TX = board.D2

BUTTON_A = board.D3
BUTTON_B = board.D4

BUZZER_A = board.D10
BUZZER_B = board.D6

PERIPH_EN = board.D5

SDA = board.D7
SCL = board.D8
DRDY = board.D9

HAPPY = (("C6", 50), ("E6", 50), ("G6", 50), ("C7", 50))


# noinspection PyAttributeOutsideInit
class Hardware:
    def __init__(self):
        displayio.release_displays()
        self.las_en_pin = digitalio.DigitalInOut(LASER_EN)
        self.las_en_pin.switch_to_output(False)
        self.periph_enable_io = digitalio.DigitalInOut(PERIPH_EN)
        self.periph_enable_io.switch_to_output(True)
        self.pwm = invertingpwmio.InvertingPWMOut(BUZZER_A, BUZZER_B)
        self.buzzer = async_buzzer.Buzzer(self.pwm)
        atexit.register(self.deinit)
        time.sleep(0.01)
        self.las_en_pin.switch_to_output(True)
        self.uart = busio.UART(TX, RX, baudrate=9600)
        self.laser = Laser(self.uart)
        time.sleep(0.1)
        self.i2c = I2C(scl=SCL, sda=SDA, frequency=4000000)
        self.drdy_io = digitalio.DigitalInOut(DRDY)
        self.drdy_io.direction = digitalio.Direction.INPUT
        self.magnetometer = rm3100.RM3100_I2C(self.i2c, drdy_pin=self.drdy_io)
        self.accelerometer = seeed_xiao_nrf52840.IMU()
        self.display = SH1106_Display(self.i2c)
        self.button_a = async_button.Button(BUTTON_A,value_when_pressed=False)
        self.button_b = async_button.Button(BUTTON_B,value_when_pressed=False,
                                            long_click_enable=True)
        self.both_buttons = async_button.MultiButton(a=self.button_a, b=self.button_b)
        self.batt_voltage = seeed_xiao_nrf52840.Battery.voltage
        self.initialised = True

    def laser_enable(self, value: bool):
        self.las_en_pin.value = value

    def update_voltage(self):
        self.batt_voltage = seeed_xiao_nrf52840.Battery.voltage

    def deinit(self):
        # release display
        if self.initialised:
            displayio.release_displays()
            # release i2c
            self.i2c.deinit()
            self.accelerometer.deinit()
            self.drdy_io.deinit()
            self.las_en_pin.deinit()
            self.pwm.deinit()
            self.uart.deinit()
            #remove power from board
            self.periph_enable_io.value=False
            self.periph_enable_io.deinit()
            self.button_a.deinit()
            self.button_b.deinit()
            self.initialised = False

    def beep_happy(self):
        self.buzzer.play(HAPPY)

    def beep_shutdown(self):
        self.buzzer.play(reversed(HAPPY))
