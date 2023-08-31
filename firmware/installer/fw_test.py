import time

import adafruit_displayio_sh1106
import displayio
import terminalio
from adafruit_display_text import label

import pins
import digitalio
import rm3100
import busio
import laser_egismos
import seeed_xiao_nrf52840
import pwmio
import atexit

print("Checking voltage")
bat = seeed_xiao_nrf52840.Battery()
print(f"{bat.voltage}v")
print("\n")
bat.deinit()

print("Testing accelerometer")
imu = seeed_xiao_nrf52840.IMU()
print(imu.acceleration)
print("\n")
imu.deinit()

print("Press Button A")
button_a = digitalio.DigitalInOut(pins.BUTTON_A)
button_a.switch_to_input(digitalio.Pull.UP)
if button_a.value == 0:
    raise RuntimeError("Button A already pressed?")
while button_a.value == 1:
    pass
button_a.deinit()

print("Testing buzzer A")
if pins.BUZZER_B is not None:
    buzzer_b = digitalio.DigitalInOut(pins.BUZZER_B)
    buzzer_b.switch_to_output(0)
pwm = pwmio.PWMOut(pins.BUZZER_A, frequency=512, duty_cycle=0x7FFF)
time.sleep(0.5)
pwm.deinit()
if pins.BUZZER_B is not None:
    # noinspection PyUnboundLocalVariable
    buzzer_b.deinit()
    print("Testing buzzer B")

    buzzer_a = digitalio.DigitalInOut(pins.BUZZER_A)
    buzzer_a.switch_to_output(0)
    pwm = pwmio.PWMOut(pins.BUZZER_B, frequency=1024, duty_cycle=0x7FFF)
    time.sleep(0.5)
    pwm.deinit()
    buzzer_a.deinit()
    print("\n")
else:
    print("No Buzzer B pin")

print("Turning on peripherals")
periph_enable_io = digitalio.DigitalInOut(pins.PERIPH_EN)
periph_enable_io.switch_to_output(True)
atexit.register(periph_enable_io.deinit)

print("Testing Laser")
las_en_pin = digitalio.DigitalInOut(pins.LASER_EN)
las_en_pin.switch_to_output(True)
time.sleep(0.1)
uart = busio.UART(pins.TX, pins.RX, baudrate=9600)
uart.reset_input_buffer()
laser = laser_egismos.Laser(uart)
print(f"{laser.distance}m")
print("\n")
uart.deinit()

print("Testing i2c devices")
i2c = busio.I2C(scl=pins.SCL, sda=pins.SDA, frequency=4000000)
atexit.register(i2c.deinit)
drdy_io = digitalio.DigitalInOut(pins.DRDY)
drdy_io.direction = digitalio.Direction.INPUT

print("Testing magnetometer")
magnetometer = rm3100.RM3100_I2C(i2c, drdy_pin=drdy_io)
print(magnetometer.magnetic)
print("\n")

print("Testing display")
bus = displayio.I2CDisplay(i2c, device_address=0x3c)
# noinspection PyTypeChecker
oled = adafruit_displayio_sh1106.SH1106(bus, width=128, height=64, auto_refresh=False,
                                        rotation=0, colstart=2)
atexit.register(displayio.release_displays)
group = displayio.Group()
text = label.Label(terminalio.FONT, text="Press B", color=0xffffff, x=30, y=31)
group.append(text)
oled.show(group)
oled.refresh()

button_b = digitalio.DigitalInOut(pins.BUTTON_B)
button_b.switch_to_input(digitalio.Pull.UP)
if button_b.value == 0:
    raise RuntimeError("Button B already pressed?")
while button_b.value == 1:
    pass
button_b.deinit()
las_en_pin.deinit()
print("All tests complete, no errors found")
print("HW TEST COMPLETE")
time.sleep(1000)
