import time

import adafruit_displayio_sh1106
import displayio
import terminalio
from adafruit_display_text import label
import digitalio
import rm3100
import busio
import laser_egismos
import seeed_xiao_nrf52840
import pwmio
import atexit

# noinspection PyUnresolvedReferences
import firmware.version as version

def show_pattern(disp):
    splash = displayio.Group()
    palette = displayio.Palette(2)
    palette[0] = 0x000000
    palette[1] = 0xFFFFFF
    bitmap_a = displayio.Bitmap(128,64,2)
    bitmap_a.fill(1)
    bitmap_b = displayio.Bitmap(108,44,2)
    bitmap_b.fill(0)
    tile_a = displayio.TileGrid(bitmap_a, pixel_shader=palette, x=0, y=0)
    tile_b = displayio.TileGrid(bitmap_b, pixel_shader=palette, x=10, y=10)
    splash.append(tile_a)
    splash.append(tile_b)
    splash.append(label.Label(terminalio.FONT, text="Press B", color=0xffffff, x=30, y=31))
    disp.root_group = splash


pins = version.get_pins()

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
    buzzer_b.switch_to_output(False)
pwm = pwmio.PWMOut(pins.BUZZER_A, frequency=512, duty_cycle=0x7FFF)
time.sleep(0.5)
pwm.deinit()
if pins.BUZZER_B is not None:
    # noinspection PyUnboundLocalVariable
    buzzer_b.deinit()
    print("Testing buzzer B")

    buzzer_a = digitalio.DigitalInOut(pins.BUZZER_A)
    buzzer_a.switch_to_output(False)
    pwm = pwmio.PWMOut(pins.BUZZER_B, frequency=1024, duty_cycle=0x7FFF)
    time.sleep(0.5)
    pwm.deinit()
    buzzer_a.deinit()
    print("\n")
else:
    print("No Buzzer B pin")

print("Turning on peripherals")
peripheral_enable_io = digitalio.DigitalInOut(pins.PERIPH_EN)
peripheral_enable_io.switch_to_output(True)
atexit.register(peripheral_enable_io.deinit)

print("Testing Laser")
las_en_pin = digitalio.DigitalInOut(pins.LASER_EN)
las_en_pin.switch_to_output(True)
time.sleep(0.1)
uart = busio.UART(pins.TX, pins.RX, baudrate=9600)
uart.reset_input_buffer()
laser = laser_egismos.Laser(uart)
print(f"{laser.distance}m")
print("\n")
laser.set_buzzer(False)
print(f"Laser buzzer turned off")
uart.deinit()

print("Testing i2c devices")
i2c = busio.I2C(scl=pins.SCL, sda=pins.SDA, frequency=4000000)
atexit.register(i2c.deinit)
drdy_io = digitalio.DigitalInOut(pins.DRDY)
drdy_io.direction = digitalio.Direction.INPUT

print("Testing magnetometer")
# noinspection PyTypeChecker
magnetometer = rm3100.RM3100_I2C(i2c, drdy_pin=drdy_io)
print(magnetometer.magnetic)
print("\n")

print("Testing display")
bus = displayio.I2CDisplay(i2c, device_address=0x3c)
# noinspection PyTypeChecker
oled = adafruit_displayio_sh1106.SH1106(bus, width=128, height=64,
                                        rotation=0, colstart=2)
atexit.register(displayio.release_displays)
show_pattern(oled)

button_b = digitalio.DigitalInOut(pins.BUTTON_B)
button_b.switch_to_input(digitalio.Pull.UP)
if button_b.value == 0:
    raise RuntimeError("Button B already pressed?")
while button_b.value == 1:
    pass
oled.root_group = None

button_b.deinit()
las_en_pin.deinit()
print("All tests complete, no errors found")
print("HW TEST COMPLETE")
time.sleep(1000)
