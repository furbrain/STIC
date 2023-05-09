import utils
from utils import get_pin_no

try:
    from typing import List, Awaitable, Coroutine, Callable
except ImportError:
    pass

import time
import_start = time.monotonic()
import asyncio
import traceback
from fruity_menu.menu import Menu

from config import Config
import hardware
from async_button import Button
from data import Readings, Leg
import alarm
import mag_cal
import microcontroller
import board
print(f"imported all in {time.monotonic() - import_start}")


class Shutdown(Exception):
    """
    This represents a planned shutdown
    """

def get_null_calibration():
    from ulab import numpy as np
    cal = mag_cal.Calibration()
    cal.mag.transform = np.eye(3)
    cal.mag.centre = np.array([0.0,0,0])
    cal.grav.transform = cal.mag.transform
    cal.grav.centre = cal.mag.centre
    return cal



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

    def start_menu_action(self, action, *args):
        self.menu_action = lambda: action(*args)

    def shutdown(self):
        import _bleio
        from utils import set_uint32_at
        self.devices.deinit()
        #USB_alarm = alarm.pin.PinAlarm(board.CHARGE_STATUS, value=False, pull=True)
        button_alarm = alarm.pin.PinAlarm(hardware.BUTTON_A, value=False, pull=True)
        periph_keep_low = alarm.pin.PinAlarm(hardware.PERIPH_EN, value=True, pull=True)
        print("shutting down")
        time.sleep(0.1)
        _bleio.adapter.enabled=False
        time.sleep(1)
        #ok, dirty fix to just plonk device in deep sleep - may lose wake up on pins for now...
        pin_no = get_pin_no(hardware.BUTTON_A)
        if pin_no >= 32:
            gpio_base_addr = 0x50000300
            pin_no %= 32
        else:
            gpio_base_addr = 0x50000000
        pin_cnf_addr = gpio_base_addr + 0x700 + pin_no * 4
        set_uint32_at(pin_cnf_addr,0x0003000C) # sense low, input buffer, pullup
        set_uint32_at(0x40000500, 1) # SYSTEM OFF
        #shouldn't reach here...
        #alarm.exit_and_deep_sleep_until_alarms(button_alarm, periph_keep_low)


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
        #need to switch display to measurement here...
        readings = Readings(alarm.sleep_memory)
        self.devices.display.set_mode(self.devices.display.MEASURE)
        self.devices.laser_enable(True)
        await asyncio.sleep(0.5)
        self.devices.laser.set_laser(True)
        # FIXME we've just bodged the calibration for now...
        cal = get_null_calibration()
        a = 301.4
        b = -57
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
                #distance = self.devices.laser.distance / 100
                distance = a / 100
                #azimuth, inclination, distance = self.devices.magnetometer.magnetic
                #azimuth, inclination, distance = self.devices.accelerometer.acceleration
                a -= 5.5
                b += 3.4
                readings.store_reading(Leg(azimuth, inclination, distance))
                readings.pack_into(alarm.sleep_memory)
            elif btn == "b":
                readings.get_prev_reading()
            if readings.current_reading is not None:
                self.devices.display.update_measurement(readings.current, readings.current_reading)

    async def quitter_task(self):
        await self.devices.button_a.wait(Button.DOUBLE)
        raise Shutdown("quit!")
    
    async def timeout(self):
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
        w.timeout=5 # 5 second watchdog timeout
        w.mode = WatchDogMode.RAISE
        exception_count = 0
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
        print(f"Menu up in {time.monotonic()-import_start}")

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
            exception_context.update(context)
            this_task.cancel()
        self.devices.beep_happy()
        asyncio.get_event_loop().set_exception_handler(exception_handler)
        all_background_tasks = [asyncio.create_task(t) for t in self.background_tasks]
        self.switch_task(self.mode)
        try:
            await asyncio.gather(*all_background_tasks)
        #except asyncio.CancelledError:
        #    pass
        except Exception as exc:
            exception_context["exception"] = exc
        if exception_context:
            import storage
            import traceback
            output = traceback.format_exception(exception_context["exception"])
            # FIXME implement nicer exception handling
            try:
                with open("/error.log", "w") as f:
                    f.write(output[0])
                    f.flush()
            except OSError:
                self.devices.beep_shutdown()
                await self.devices.buzzer.wait()
        self.devices.beep_shutdown()
        await self.devices.buzzer.wait()

app = App(App.MENU)
try:
    asyncio.run(app.main())
except Exception as err:
    print("exception!")
    traceback.print_exception(err)
finally:
    app.shutdown()
