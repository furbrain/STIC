import asyncio
import time
import traceback

import mag_cal
import microcontroller
from mag_cal import NotCalibrated
from watchdog import WatchDogMode

from display import Display
from measure import measure, take_reading
from menu import menu
from utils import simplify, check_mem

try:
    from typing import List, Coroutine
except ImportError:
    pass

from async_button import Button

import hardware
from config import Config
import adafruit_logging as logging

logger = logging.getLogger()


class App:
    """
    This class holds all the tasks for the main program
    """
    MEASURE = 0
    MENU = 1
    MENU_ITEM = 2

    def __init__(self, mode=MEASURE):
        check_mem("creating app")
        self.devices = hardware.Hardware()
        self.config = Config.load()
        self.display = Display(self.devices, self.config)
        self.mode = mode
        self.menu_action = None
        self.background_tasks: List[Coroutine] = [
            self.quitter_task(),
            self.timeout(),
            self.switch_mode_monitor(),
            self.watchdog(),
            self.devices.bt.disto_background_task(self.distox_callback),
            self.bt_connection_monitor(),
            self.batt_monitor(),
            self.flip_monitor(),
        ]
        if logger.getEffectiveLevel() <= logging.INFO:
            self.background_tasks.append(self.counter())
        self.current_task: asyncio.Task = None
        self.exception_context = {}
        self.shutdown_event = asyncio.Event()
        check_mem("Finished creating app")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deinit()


    def deinit(self):
        self.display.deinit()
        self.devices.deinit()


    async def switch_task(self, mode: int):
        # stop current task, async so can be scheduled by task due to finish...
        logger.info(f"Switching task to {mode}")
        if self.current_task:
            self.current_task.cancel()
        self.mode = mode
        if mode == self.MEASURE:
            self.current_task = asyncio.create_task(measure(self.devices, self.config,
                                                            self.display))
        elif mode == self.MENU:
            self.current_task = asyncio.create_task(menu(self.devices, self.config, self.display))

    async def switch_mode_monitor(self):
        while True:
            await self.devices.button_b.wait(Button.LONG)
            logger.info("switching mode")
            if self.mode in (self.MEASURE, self.MENU_ITEM):
                await self.switch_task(self.MENU)
            else:
                await self.switch_task(self.MEASURE)

    async def quitter_task(self):
        """
        Shuts down  if double click on button A
        """
        logger.debug("Quitter task started")
        lockout = time.monotonic()+0.5
        while True:
            await self.devices.button_a.wait(Button.DOUBLE)
            check_mem("double click")
            if time.monotonic() > lockout:
                logger.info("Double click detected, quitting")
                self.shutdown_event.set()

    async def timeout(self):
        """
        Shuts down if more than config.timeout seconds between button presses
        """
        logger.debug("Timeout task started")
        while True:
            try:
                await asyncio.wait_for(self.devices.both_buttons.wait(a=Button.ANY_CLICK,
                                                                      b=Button.ANY_CLICK),
                                       self.config.timeout)
            except asyncio.TimeoutError:
                logger.info("Timed out, quitting")
                self.shutdown_event.set()

    async def counter(self):
        logger.debug("Counter task started")
        i = 0
        while True:
            await asyncio.sleep(1)
            i += 1
            logger.info(f"Count: {i}")

    async def watchdog(self):
        logger.debug("Watchdog task started")
        microcontroller.watchdog.timeout = 5 # 5 second watchdog timeout
        microcontroller.watchdog.mode = WatchDogMode.RAISE
        exception_count = 0
        try:
            while True:
                await asyncio.sleep(1)
                try:
                    microcontroller.watchdog.feed()
                except ValueError:
                    # for some reason we get an extra run through after the watchdog fires
                    # can't feed it any more, but ignore this exception so we get the correct
                    # exception reported from the code at fault, but for safety only ignore this once
                    if exception_count == 0:
                        exception_count += 1
                    else:
                        raise
        finally:
            microcontroller.watchdog.deinit()

    async def bt_connection_monitor(self):
        while True:
            await asyncio.sleep(0.5)
            self.display.set_bt_connected(self.devices.bt.connected)
            self.display.set_bt_pending_count(self.devices.bt.pending_count())

    async def bt_quit_now(self):
        logger.debug("Shut down due to BT command")
        self.shutdown_event.set()

    async def distox_callback(self, value: int):
        CALLBACKS = {
            0x34: lambda: self.bt_quit_now(),
            0x36: lambda: self.devices.laser.set_laser(True),
            0x37: lambda: self.devices.laser.set_laser(False),
            0x38: lambda: take_reading(self.devices, self.config, self.display),

        }
        logger.debug(f"disto callback received with {value}")
        if value in CALLBACKS:
            res = CALLBACKS[value]()
            if hasattr(res,"__await__"):
                await res

    async def batt_monitor(self):
        logger.debug("Starting Battery monitor")
        while True:
            voltage = self.devices.batt_voltage
            logger.debug(f"Voltage is {voltage:.2f}v")
            if voltage < 3.4:
                self.devices.beep_sad()
                raise LowBattery(f"Battery low ({voltage:3.1f}v)")
            self.display.set_batt_level(voltage)
            self.devices.bt.set_battery_level(voltage)
            await asyncio.sleep(2.0)

    async def flip_monitor(self):
        logger.debug("Starting flip monitor")
        while True:
            await asyncio.sleep(0.3)
            grav = self.devices.accelerometer.acceleration
            if self.config.calib is not None:
                grav = self.config.calib.grav.apply(grav)
            else:
                axes = mag_cal.Axes(self.config.mag_axes)
                grav = axes.fix_axes(grav)
                grav /= 9.81
            if self.display.inverted and grav[0] < -0.3:
                logger.debug("Flipping to right way up")
                self.display.inverted = False
            elif not self.display.inverted and grav[0] > 0.3:
                logger.debug("Flipping to inverted")
                self.display.inverted = True

    async def main(self):
        # set up exception handling
        clean_shutdown = True
        logger.debug("Main app routine started")
        self.setup_exception_handler()
        all_background_tasks = [asyncio.create_task(t) for t in self.background_tasks]
        self.devices.beep_happy()
        await self.switch_task(self.mode)
        await self.shutdown_event.wait()
        check_mem("Starting shutdown")
        self.clear_exception_handler()
        for t in all_background_tasks:
            t.cancel()
        self.current_task.cancel()
        self.config.save_if_changed()
        await asyncio.sleep(0) # allow everything to stop
        check_mem("tasks cancelled")
        if self.exception_context:
            clean_shutdown = False
            output = traceback.format_exception(self.exception_context["exception"])
            # FIXME implement nicer exception handling
            try:
                with open("/error.log", "w") as f:
                    f.write(output[0])
                    f.flush()
            except OSError:
                #unable to save to disk, probably connected via USB, so print
                logger.error(output[0])
            try:
                brief_output = simplify(output[0])
                self.display.show_info(brief_output)
                for i in range(10):
                    await asyncio.sleep(1)
                    if microcontroller.watchdog.mode != None:
                        microcontroller.watchdog.feed()
            except Exception as exc:
                # error displaying: give up
                logger.error("Error displaying error")
                logger.error(traceback.format_exception(exc)[0])
                pass
        self.devices.beep_shutdown()
        await self.devices.beep_wait()
        logger.debug("Stopping watchdog")
        microcontroller.watchdog.deinit()
        logger.debug(f"Exiting App: {clean_shutdown}")
        await asyncio.sleep(0.1)
        check_mem("leaving app")
        return clean_shutdown

    def setup_exception_handler(self):
        logger.debug("Asyncio exception handler created")

        def exception_handler(loop, context):
            logger.info("Exception received")
            self.exception_context.update(context)
            logger.debug("Triggering shutdown")
            self.shutdown_event.set()

        asyncio.get_event_loop().set_exception_handler(exception_handler)

    def clear_exception_handler(self):
        logger.debug("Clearing exception handler")
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(None)

class LowBattery(Exception):
    """
    This represents a shutdown due to low battery
    """