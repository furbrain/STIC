# Write your code here :-)
"""Example for Seeed Studio XIAO nRF52840. Blinks the built-in LED."""
import time

import board
import busio
import digitalio
import pwmio
import pins
import laser_at

leds = [digitalio.DigitalInOut(x) for x in [pins.LED_R, pins.LED_B]]
leds.append(leds[1])
board_leds = [
    digitalio.DigitalInOut(x) for x in [board.LED_RED, board.LED_GREEN, board.LED_BLUE]
]
for led in leds + board_leds:
    led.direction = digitalio.Direction.OUTPUT

button = digitalio.DigitalInOut(board.D3)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

buzzer_low = digitalio.DigitalInOut(pins.BUZZER_A)
buzzer_low.direction = digitalio.Direction.OUTPUT
buzzer_low.value = False

uart = busio.UART(pins.TX, pins.RX)
uart.baudrate = 19200
laser = laser_at.Laser(uart)
laser.on = True
i = 0
last_pressed = False
while True:
    pressed = not button.value
    if pressed != last_pressed:
        last_pressed = pressed
        if pressed:
            i = (i + 1) % 3
            for led in leds + board_leds:
                led.value = True
            leds[i].value = False
            board_leds[i].value = False
            print(laser.distance)
            with pwmio.PWMOut(pins.BUZZER_B, duty_cycle=2 ** 15, frequency=2000):
                time.sleep(0.1)
    time.sleep(0.01)
