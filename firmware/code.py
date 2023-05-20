import pins

try:
    from typing import List, Awaitable, Coroutine, Callable
except ImportError:
    pass

import digitalio
import time
import asyncio
import traceback
import pins
import alarm
import gc
import app
import microcontroller
import adafruit_logging as logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
LIGHT_SLEEP_TIMEOUT = 6*60*60 # light sleep for 6 hours

def double_click_start() -> bool:
    with digitalio.DigitalInOut(pins.BUTTON_A) as button_a:
        button_a.switch_to_input(digitalio.Pull.UP)
        # wait for release
        while not button_a.value:
            time.sleep(0.03)
        dbl_click_interval_expired = time.monotonic() + 1.0
        while time.monotonic() < dbl_click_interval_expired:
            if not button_a.value:
                # button been pressed in relevant time
                return True
            else:
                time.sleep(0.03)
        # timed out
        return False


#main

async def main(mode):
    with app.App(mode) as main_app:
        try:
            logger.info("Starting main app")
            await main_app.main()
        except Exception as err:
            #don't try and report this as system likely in an iffy state - just exit
            logger.error("Exception received in main outer layer:")
            traceback.print_exception(err)


while True:
    app_used = False
    if double_click_start():
        gc.collect()
        logger.info("Double click")
        logger.debug(f"Memory left: {gc.mem_free()}")
        with digitalio.DigitalInOut(pins.BUTTON_B) as button_b:
            app_used = True
            button_b.switch_to_input(digitalio.Pull.UP)
            if button_b.value == False:
                # button b is pressed
                mode = app.App.MENU
            else:
                mode = app.App.MEASURE
            logger.debug(f"App mode is {mode}")
        asyncio.run(main(mode))
    else:
        logger.info("no double click")
    pin_alarm = alarm.pin.PinAlarm(pins.BUTTON_A, value=False, pull=True)
    if app_used:
        logger.debug("App has been used, so starting a timed sleep")
        time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + LIGHT_SLEEP_TIMEOUT)
        wakeup = alarm.light_sleep_until_alarms(time_alarm, pin_alarm)
        if wakeup == time_alarm:
            logger.info("Resetting after period of disuse")
            # ensure device resets after a period if been used
            microcontroller.reset()
    else:
        logger.debug("App not used so indefinite sleep, waiting for pin press")
        alarm.light_sleep_until_alarms(pin_alarm)
