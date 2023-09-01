# noinspection PyPackageRequirements
import alarm
import pins
import _bleio
import board
import time
import hardware
import asyncio


async def runner():
    with hardware.Hardware():
        await asyncio.sleep(0.3)


LIGHT_SLEEP_TIMEOUT = 60
_bleio.adapter.stop_advertising()
time.sleep(0.1)
asyncio.run(runner())
pin_alarm = alarm.pin.PinAlarm(pins.BUTTON_A, value=False, pull=True)
periph_alarm = alarm.pin.PinAlarm(pins.PERIPH_EN, value=True, pull=True)
usb_alarm = alarm.pin.PinAlarm(board.CHARGE_STATUS, value=False, pull=False)
# wakeup = alarm.light_sleep_until_alarms(pin_alarm, usb_alarm)
# print(wakeup.pin)
time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + LIGHT_SLEEP_TIMEOUT)
print("sleeping")
wakeup = alarm.light_sleep_until_alarms(time_alarm, pin_alarm, usb_alarm)
