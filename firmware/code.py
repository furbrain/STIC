import seeed_xiao_nrf52840

import pins
import usb_mode

try:
    from typing import List, Awaitable, Coroutine, Callable
except ImportError:
    pass

import adafruit_logging as logging
import storage
logger = logging.getLogger()
#if not storage.getmount("/").readonly:
#    logger.addHandler(logging.FileHandler("log.txt"))
logger.setLevel(logging.DEBUG)
logger.debug("Starting log")


from utils import usb_power_connected, check_mem
import digitalio
import time
import asyncio
import traceback
import pins
import alarm
import gc
import app
import microcontroller
import board
import _bleio

LIGHT_SLEEP_TIMEOUT = 6*60*60 # light sleep for 6 hours

def double_click_start() -> bool:
    #first check voltage and return false if too low...
    with seeed_xiao_nrf52840.Battery() as batt:
        voltage = batt.voltage
        if voltage < 3.2:
            logger.info(f"Low voltage {voltage:3.1f}v")
            return False
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
    check_mem("starting_app")
    with app.App(mode) as main_app:
        logger.info("Starting main app")
        shutdown_status = await main_app.main()
        check_mem("App closed")
        return shutdown_status

app_used = False
check_mem("First run")
while True:
    clean_shutdown = False
    if usb_power_connected() != storage.getmount("/").readonly:
        logger.info("Restarting microcontroller so can correctly mount flash")
        microcontroller.reset()
    try:
        if double_click_start():
            logger.info("Double click")
            check_mem("double_click")
            with digitalio.DigitalInOut(pins.BUTTON_B) as button_b:
                app_used = True
                button_b.switch_to_input(digitalio.Pull.UP)
                if button_b.value == False:
                    # button b is pressed
                    mode = app.App.MENU
                else:
                    mode = app.App.MEASURE
                logger.debug(f"App mode is {mode}")
            clean_shutdown = asyncio.run(main(mode))
        else:
            logger.info("no double click")
            time.sleep(0.1)
            if usb_power_connected() and logger.getEffectiveLevel() != logging.DEBUG:
                usb_mode.usb_charge_monitor()
            clean_shutdown = True
    except MemoryError:
        # limited debugging as can't do anything as no memory
        clean_shutdown = False
        logger.debug("Outer memory error")
    except Exception as exc:
        # do not go in to REPL on exception
        clean_shutdown = False
        logger.error(traceback.format_exception(exc))
    if not clean_shutdown:
        logger.debug("Unclean shutdown - resetting")
        time.sleep(0.1)
        microcontroller.reset()
    # shutdown watchdog before sleep
    if microcontroller.watchdog.mode != None:
        logger.debug("Disabling watchdog prior to sleep")
        microcontroller.watchdog.deinit()
    _bleio.adapter.stop_advertising()
    _bleio.adapter.stop_scan()
    pin_alarm = alarm.pin.PinAlarm(pins.BUTTON_A, value=False, pull=True)
    usb_alarm = alarm.pin.PinAlarm(board.CHARGE_STATUS, value=False, pull=False)
    if app_used:
        logger.debug("App has been used, so starting a timed sleep")
        check_mem("sleeping")
        time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + LIGHT_SLEEP_TIMEOUT)
        wakeup = alarm.light_sleep_until_alarms(time_alarm, pin_alarm, usb_alarm)
        if wakeup == time_alarm:
            logger.info("Resetting after period of disuse")
            # ensure device resets after a period if been used
            microcontroller.reset()
    else:
        logger.debug("App not used so indefinite sleep, waiting for pin press or usb connection")
        wakeup = alarm.light_sleep_until_alarms(pin_alarm, usb_alarm)
    if wakeup == usb_alarm:
        time.sleep(0.1)