import asyncio
import time
try:
    from typing import List, Coroutine
except ImportError:
    pass

import mag_cal
from async_button import Button
from fruity_menu.menu import Menu

import hardware
import utils
from config import Config
from data import Readings, Leg


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
            self.counter(),
            self.watchdog()
        ]
        self.current_task: asyncio.Task = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deinit()


    def start_menu_action(self, action, *args):
        self.menu_action = lambda: action(*args)

    def deinit(self):
        import _bleio
        self.devices.deinit()


    def switch_task(self, mode: int):
        # stop current task
        if self.current_task:
            self.current_task.cancel()
        self.mode = mode
        self.current_task = asyncio.create_task(self.interfaces[self.mode]())

    async def switch_mode_monitor(self):
        while True:
            await self.devices.button_b.wait(Button.LONG)
            print("switching mode")
            if self.mode in (self.MEASURE, self.MENU_ITEM):
                self.switch_task(self.MENU)
            else:
                self.switch_task(self.MEASURE)

    async def measure_task(self):
        """
        This is the main measurement task
        :return:
        """
        from data import readings
        #need to switch display to measurement here...
        self.devices.laser_enable(True)
        await asyncio.sleep(0.1)
        await self.devices.laser.set_laser(True)
        self.devices.display.set_mode(self.devices.display.MEASURE)
        # FIXME we've just bodged the calibration for now...
        cal = get_null_calibration()
        while True:
            btn, click = await self.devices.both_buttons.wait(a=Button.SINGLE, b=Button.SINGLE)
            if btn == "a":
                # take a reading
                mag = self.devices.magnetometer.magnetic
                grav = self.devices.accelerometer.acceleration
                cal = get_null_calibration()
                # FIXME maybe need to protect magnetometer from stray currents etc and maybe use
                # direct procedural calls...
                azimuth, inclination, _ =  cal.get_angles(mag, grav)
                try:
                    distance = await asyncio.wait_for(self.devices.laser.measure(),3.0) / 1000
                    readings.store_reading(Leg(azimuth, inclination, distance))
                except TimeoutError:
                    print("laser read failed")
                    continue
            elif btn == "b":
                readings.get_prev_reading()
            if readings.current_reading is not None:
                self.devices.display.update_measurement(readings.current, readings.current_reading)

    async def quitter_task(self):
        """
        Raises a shutdown exception if double click on button A
        """
        await self.devices.button_a.wait(Button.DOUBLE)
        raise Shutdown("quit!")

    async def timeout(self):
        """
        Raises a shutdown exception if more than config.timeout seconds between button presses
        """
        while True:
            try:
                await asyncio.wait_for(self.devices.both_buttons.wait(a=Button.ANY_CLICK,
                                                                      b=Button.ANY_CLICK),
                                       self.config.timeout)
            except asyncio.TimeoutError:
                raise Shutdown(f"Timeout after {self.config.timeout} seconds inactivity")

    async def counter(self):
        i = 0
        while True:
            await asyncio.sleep(1)
            i += 1
            print(f"Count: {i}")

    async def watchdog(self):
        from microcontroller import watchdog as w
        from watchdog import WatchDogMode
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
        items = {"Calibrate": {
                    "Sensors": self.dummy,
                    "Laser": self.dummy,
                    "Axes": self.freeze},
                 "Settings": {
                     "Units": {
                         "Metric": self.dummy,
                         "Imperial": self.dummy
                     },
                     "Display": {
                         "Degrees": self.dummy,
                         "Grad": self.dummy
                     }
                 }
        }
        menu = Menu(self.devices.display.display, 64, 128, False, "Menu")
        #build_menu(menu, items)
        cal_menu = menu.create_menu("Calibrate")
        cal_menu.add_action_button("Sensors",self.dummy)
        cal_menu.add_action_button("Laser",self.dummy)
        cal_menu.add_action_button("Axes",self.freeze)
        settings_menu = menu.create_menu("Settings")
        settings_menu.add_option_button("Units",self.config.units,
                                       [Config.METRIC, Config.IMPERIAL],
                                       option_labels=["Metric", "Imperial"],
                                       on_value_set=lambda x: setattr(self.config, "units", x))
        if utils.usb_power_connected():
            menu.add_submenu_button("Calibrate", cal_menu)
        else:
            menu.add_submenu_button("Freedom",cal_menu)
        menu.add_submenu_button("Settings",settings_menu)
        self.devices.display.menu_group = menu.build_displayio_group()
        self.devices.display.set_mode(self.devices.display.MENU)
        menu.show_menu()
        self.devices.display.refresh()

        while True:
            button, _ = await self.devices.both_buttons.wait(a=Button.SINGLE, b=Button.SINGLE)
            if button == "a":
                menu.click()
                menu.show_menu()
                self.devices.display.refresh()
            elif button == "b":
                menu.scroll(1)
                menu.show_menu()
                self.devices.display.refresh()

    async def menu_item_task(self):
        pass

    async def main(self):
        # set up exception handling
        this_task = asyncio.current_task()
        exception_context = {}
        def exception_handler(loop, context):
            print(f"exception received: {context}")
            exception_context.update(context)
            this_task.cancel()
        #self.devices.beep_happy()
        asyncio.get_event_loop().set_exception_handler(exception_handler)
        all_background_tasks = [asyncio.create_task(t) for t in self.background_tasks]
        self.switch_task(self.mode)
        try:
            await asyncio.gather(*all_background_tasks)
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            exception_context["exception"] = exc
        for t in all_background_tasks:
            t.cancel()
        self.current_task.cancel()
        await asyncio.sleep(0) # allow everything to stop
        if exception_context:
            if isinstance(exception_context["exception"], Shutdown):
                print(f"Planned shutdown: {exception_context['exception'].args[0]}")
            else:
                import traceback
                output = traceback.format_exception(exception_context["exception"])
                # FIXME implement nicer exception handling
                try:
                    with open("/error.log", "w") as f:
                        f.write(output[0])
                        f.flush()
                except OSError:
                    #self.devices.beep_shutdown()
                    await self.devices.buzzer.wait()
        self.devices.beep_shutdown()
        await self.devices.beep_wait()
        from microcontroller import watchdog
        watchdog.deinit()


def get_null_calibration():
    from ulab import numpy as np
    cal = mag_cal.Calibration()
    cal.mag.transform = np.eye(3)
    cal.mag.centre = np.array([0.0,0,0])
    cal.grav.transform = cal.mag.transform
    cal.grav.centre = cal.mag.centre
    return cal


class Shutdown(Exception):
    """
    This represents a planned shutdown
    """
