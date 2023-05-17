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

while True:
    if double_click_start():
        print("double click!")
        import gc
        gc.collect()
        print(f"Mem left: {gc.mem_free()}")
        with digitalio.DigitalInOut(pins.BUTTON_B) as button_b:
            button_b.switch_to_input(digitalio.Pull.UP)
            from app import App
            if button_b.value == False:
                # button b is pressed
                mode = App.MENU
            else:
                mode = App.MEASURE
        with App(mode) as main_app:
            try:
                asyncio.run(main_app.main())
            except Exception as err:
                print("exception!")
                traceback.print_exception(err)
    else:
        print("no double click")
    import alarm # delayed import to speed startup
    import displayio
    displayio.release_displays()
    time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + LIGHT_SLEEP_TIMEOUT)
    pin_alarm = alarm.pin.PinAlarm(pins.BUTTON_A, value=False, pull=True)
    wakeup = alarm.light_sleep_until_alarms(time_alarm, pin_alarm)
    if wakeup == time_alarm:
        # we've slept lightly for 6 hours, now go into true deep sleep
        import utils
        utils.true_deep_sleep(pin_alarm)

