import asyncio
import traceback
import microcontroller
from watchdog import WatchDogMode

import config
from display import Display
from measure import measure
from menu import menu
from utils import simplify

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
            self.devices.bt.battery_background_task(),
            self.devices.bt.disto_background_task(),
            self.bt_connection_monitor(),
        ]
        if logger.getEffectiveLevel() <= logging.INFO:
            self.background_tasks.append(self.counter())
        self.current_task: asyncio.Task = None
        self.exception_context = {}

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
        Raises a shutdown exception if double click on button A
        """
        logger.debug("Quitter task started")
        await self.devices.button_a.wait(Button.DOUBLE)
        logger.info("Double click detected, quitting")
        raise Shutdown("quit!")

    async def timeout(self):
        """
        Raises a shutdown exception if more than config.timeout seconds between button presses
        """
        logger.debug("Timeout task started")
        while True:
            try:
                await asyncio.wait_for(self.devices.both_buttons.wait(a=Button.ANY_CLICK,
                                                                      b=Button.ANY_CLICK),
                                       self.config.timeout)
            except asyncio.TimeoutError:
                logger.info("Timed out, quitting")
                raise Shutdown(f"Timeout after {self.config.timeout} seconds inactivity")

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

    async def main(self):
        # set up exception handling
        clean_shutdown = True
        logger.debug("Main app routine started")
        self.setup_exception_handler()
        all_background_tasks = [asyncio.create_task(t) for t in self.background_tasks]
        self.devices.beep_happy()
        await self.switch_task(self.mode)
        try:
            await asyncio.gather(*all_background_tasks)
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            # this exception has come out through gather, rather than exception handler
            self.exception_context["exception"] = exc
        for t in all_background_tasks:
            t.cancel()
        self.current_task.cancel()
        self.config.save_if_changed()
        await asyncio.sleep(0) # allow everything to stop
        if self.exception_context:
            if isinstance(self.exception_context["exception"], Shutdown):
                # this is a planned shut down, no display or file write needed
                logger.info(f"Planned shutdown: {self.exception_context['exception'].args[0]}")
            else:
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
        microcontroller.watchdog.deinit()
        return clean_shutdown

    def setup_exception_handler(self):
        logger.debug("Asyncio exception handler created")
        this_task = asyncio.current_task()

        def exception_handler(loop, context):
            self.exception_context.update(context)
            this_task.cancel()

        # self.devices.beep_happy()
        asyncio.get_event_loop().set_exception_handler(exception_handler)


class Shutdown(Exception):
    """
    This represents a planned shutdown
    """
