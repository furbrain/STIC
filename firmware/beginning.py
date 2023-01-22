# Write your code here :-)
"""Example for Seeed Studio XIAO nRF52840. Blinks the built-in LED."""
import time
import board
import digitalio
import pwmio

leds = [digitalio.DigitalInOut(x) for x in [board.D8, board.D9, board.D10]]
board_leds = [
    digitalio.DigitalInOut(x) for x in [board.RED_LED, board.GREEN_LED, board.BLUE_LED]
]
for led in leds + board_leds:
    led.direction = digitalio.Direction.OUTPUT

button = digitalio.DigitalInOut(board.D3)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

buzzer_low = digitalio.DigitalInOut(board.A1)
buzzer_low.direction = digitalio.Direction.OUTPUT
buzzer_low.value = False

buzzer_high = board.A0

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
            with pwmio.PWMOut(buzzer_high, duty_cycle=2 ** 15, frequency=2000):
                time.sleep(0.1)
    time.sleep(0.01)
