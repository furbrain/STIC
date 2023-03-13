#start with pseudocode...
import time

import busio
import digitalio

import pins
#import async_button
import rm3100
import mag_cal
import laser_at

# set up pins

# set up button....
#button = async_button.Button(pins.BUTTON,value_when_pressed=False, pull=True)
laser = laser_at.Laser(busio.UART(pins.TX, pins.RX, baudrate=19200))
i2c = busio.I2C(pins.SCL, pins.SDA)
mag = rm3100.RM3100_I2C(i2c)
periph_en = digitalio.DigitalInOut(pins.PERIPH_EN)
periph_en.switch_to_output(False)
time.sleep(0.5)
#laser.on = True
#shutdown routine

#?enter calibration

#main loop
async def main():
    # await button press
    # laser measure
    # measure magnetometer
    # measure inclinometer
    # apply calibration
    pass