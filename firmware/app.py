import asyncio
import time

import calibrate
import config
from display import Display
from utils import usb_power_connected, partial, simplify

try:
    from typing import List, Coroutine
except ImportError:
    pass

import mag_cal
from async_button import Button
from fruity_menu.builder import Options, build_menu

import hardware
from config import Config
from data import Readings, Leg
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
        self.interfaces = {
            self.MEASURE: self.measure_task,
            self.MENU: self.menu_task,
            self.MENU_ITEM: self.menu_item_task
        }
        self.background_tasks: List[Coroutine] = [
            self.quitter_task(),
            self.timeout(),
            self.switch_mode_monitor(),
            self.watchdog()
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
        self.display.deinit()


    async def switch_task(self, mode: int):
        # stop current task, async so can be scheduled by task due to finish...
        logger.info(f"Switching task to {mode}")
        if self.current_task:
            self.current_task.cancel()
        self.mode = mode
        self.current_task = asyncio.create_task(self.interfaces[self.mode]())

    async def switch_mode_monitor(self):
        while True:
            await self.devices.button_b.wait(Button.LONG)
            print("switching mode")
            if self.mode in (self.MEASURE, self.MENU_ITEM):
                await self.switch_task(self.MENU)
            else:
                await self.switch_task(self.MEASURE)

    def start_menu_item(self, func):
        self.menu_action = func
        asyncio.create_task(self.switch_task(self.MENU_ITEM))

    async def menu_item_test(self, devices, config, display):
        for i in range(5):
            await asyncio.sleep(1)
            display.show_info(f"MENU TEST: {i}\r\nPhil was here\r\nHere is a very long line " +
                                f"indeed")

    async def raw_readings_item(self, devices: hardware.Hardware, config, display):
        while True:
            try:
                await asyncio.wait_for(devices.button_a.wait_for_click(),0.5)
                return
            except asyncio.TimeoutError:
                pass
            acc = devices.accelerometer.acceleration
            mag = devices.magnetometer.magnetic
            text = "Raw Accel Mag\r\n"
            for axis,a,m in zip("XYZ",acc,mag):
                text += f"{axis}   {a:05.3f} {m:05.2f}\r\n"
            display.show_info(text)
    async def breaker(self, devices, config, display):
        a = b

    async def measure_task(self):
        """
        This is the main measurement task
        :return:
        """
        from data import readings
        #need to switch display to measurement here...
        logger.debug("Showing start screen")
        self.display.show_start_screen()
        logger.debug("turning on laser")
        #self.devices.laser_enable(True)
        await asyncio.sleep(0.1)
        logger.debug("turning on laser light")
        #await self.devices.laser.set_laser(True)
        logger.debug("loading calibration")
        #self.devices.display.set_mode(self.devices.display.MEASURE)
        # FIXME we've just bodged the calibration for now...
        cal = get_null_calibration(self.config)
        while True:
            btn, click = await self.devices.both_buttons.wait(a=Button.SINGLE, b=Button.SINGLE)
            if btn == "a":
                # take a reading
                logger.info("Taking a reading")
                mag = self.devices.magnetometer.magnetic
                logger.debug(f"Mag: {mag}")
                grav = self.devices.accelerometer.acceleration
                logger.debug(f"Grav: {grav}")
                # FIXME maybe need to protect magnetometer from stray currents etc and maybe use
                # direct procedural calls...
                azimuth, inclination, _ =  cal.get_angles(mag, grav)
                try:
                    distance = await asyncio.wait_for(self.devices.laser.measure(),3.0) / 1000
                    logger.debug(f"Distance: {distance}m")
                    readings.store_reading(Leg(azimuth, inclination, distance))
                    self.devices.beep_bip()
                except TimeoutError:
                    logger.info("Laser read failed")
                    self.devices.beep_sad()
                    continue
            elif btn == "b":
                logger.debug("B pressed")
                readings.get_prev_reading()
            if readings.current_reading is not None:
                self.display.update_measurement(readings.current, readings.current_reading)

    async def quitter_task(self):
        """
        Raises a shutdown exception if double click on button A
        """
        logger.debug("Quitter task started")
        await self.devices.button_a.wait(Button.DOUBLE)
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
                raise Shutdown(f"Timeout after {self.config.timeout} seconds inactivity")

    async def counter(self):
        logger.debug("Counter task started")
        i = 0
        while True:
            await asyncio.sleep(1)
            i += 1
            logger.info(f"Count: {i}")

    async def watchdog(self):
        from microcontroller import watchdog as w
        from watchdog import WatchDogMode
        logger.debug("Watchdog task started")
        w.timeout = 5 # 5 second watchdog timeout
        w.mode = WatchDogMode.RAISE
        exception_count = 0
        try:
            while True:
                await asyncio.sleep(1)
                try:
                    w.feed()
                except ValueError:
                    # for some reason we get an extra run through after the watchdog fires
                    # can't feed it any more, but ignore this exception so we get the correct
                    # exception reported from the code at fault, but for safety only ignore this once
                    if exception_count == 0:
                        exception_count += 1
                    else:
                        raise
        finally:
            w.deinit()
    def dummy(self):
        pass

    def freeze(self):
        #stop everything for 10 seconds - should trigger watchdog
        time.sleep(10)
        time.sleep(10)

    async def menu_task(self):
        logger.debug("Menu task started")
        await asyncio.sleep(0.1)
        items = {
            "Calibrate": {
                "Sensors": partial(self.start_menu_item, calibrate.calibrate),
                "Laser": self.dummy,
                "Axes": self.freeze},
            "Test": {
                "Simple Test": partial(self.start_menu_item, self.menu_item_test),
                "Raw Data": partial(self.start_menu_item, self.raw_readings_item),
                "Value Error": partial(self.start_menu_item, self.breaker),
                "Freeze": self.freeze},
            "Settings": {
                "Units": Options(
                    value=self.config.units,
                    options = [Config.METRIC, Config.IMPERIAL],
                    option_labels = ["Metric", "Imperial"],
                    on_value_set = lambda x: self.config.set_var("units", x)
                ),
                "Angles": Options(
                    value=self.config.angles,
                    options = [Config.DEGREES, Config.GRADS],
                    option_labels = ["Degrees", "Grads"],
                    on_value_set = lambda x: self.config.set_var("angles", x)
                )
            }
        }
        menu = self.display.get_menu()
        build_menu(menu, items)
        await self.display.show_and_run_menu(menu)
        menu.show_menu()
        self.devices.display.refresh()
        while True:
            button, _ = await self.devices.both_buttons.wait(a=Button.SINGLE, b=Button.SINGLE)
            if button == "a":
                logger.debug("Menu: Click")
                menu.click()
                menu.show_menu()
                self.devices.display.refresh()
            elif button == "b":
                logger.debug("Menu: Scroll")
                menu.scroll(1)
                menu.show_menu()
                self.devices.display.refresh()

    async def menu_item_task(self):
        await self.menu_action(self.devices, self.config, self.display)
        asyncio.create_task(self.switch_task(self.MENU)) #schedule task switch

    async def main(self):
        # set up exception handling
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
                import traceback
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
                    from microcontroller import watchdog as w
                    for i in range(10):
                        await asyncio.sleep(1)
                        if w.mode != None:
                            w.feed()

                except Exception as exc:
                    # error displaying: give up
                    logger.error("Error displaying error¬")
                    logger.error(traceback.format_exception(exc)[0])
                    pass
        self.devices.beep_shutdown()
        await self.devices.beep_wait()
        from microcontroller import watchdog
        watchdog.deinit()

    def setup_exception_handler(self):
        logger.debug("Asyncio exception handler created")
        this_task = asyncio.current_task()

        def exception_handler(loop, context):
            self.exception_context.update(context)
            this_task.cancel()

        # self.devices.beep_happy()
        asyncio.get_event_loop().set_exception_handler(exception_handler)


def get_null_calibration(cfg: config.Config):
    from ulab import numpy as np
    cal = mag_cal.Calibration(mag_axes=cfg.mag_axes, grav_axes=cfg.grav_axes)
    cal.mag.transform = np.eye(3)
    cal.mag.centre = np.array([0.0,0,0])
    cal.grav.transform = cal.mag.transform
    cal.grav.centre = cal.mag.centre
    return cal


class Shutdown(Exception):
    """
    This represents a planned shutdown
    """
