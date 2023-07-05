import microcontroller
import memorymap
import alarm
import sys
import time


def get_int_at(addr: int, num_bytes: int) -> int:
    mem = memorymap.AddressRange(start=addr, length=num_bytes)
    data = int.from_bytes(mem[:], sys.byteorder)
    return data


def set_int_at(addr: int, num_bytes: int, value: int):
    data = value.to_bytes(num_bytes, sys.byteorder)
    mem = memorymap.AddressRange(start=addr, length=num_bytes)
    mem[:] = data


def get_uint32_at(addr: int):
    return get_int_at(addr, 4)


def set_uint32_at(addr: int, value: int):
    set_int_at(addr, 4, value)


def get_uint16_at(addr: int):
    return get_int_at(addr, 2)


def set_uint16_at(addr: int, value: int):
    set_int_at(addr, 2, value)


def get_pin_no(pin):
    for p in dir(microcontroller.pin):
        if pin is getattr(microcontroller.pin, p):
            port, pin_no = p[1:].split("_")
            port = int(port)
            pin_no = int(pin_no)
            return port * 32 + pin_no
    return None


def usb_power_connected() -> bool:
    """Return True if USB power applied"""
    addr = 0x40000438
    data = get_uint32_at(addr)
    return bool(data & 0x01)


def true_deep_sleep(*pins: "alarm.pin.PinAlarm", pull: bool = True):
    # set up pins
    global deep_sleep_wrapped
    for pin in pins:
        pin_no = get_pin_no(pin.pin)
        if pin_no >= 32:
            gpio_base_addr = 0x50000300
            pin_no %= 32
        else:
            gpio_base_addr = 0x50000000
        pin_cnf_addr = gpio_base_addr + 0x700 + pin_no * 4
        data = 0
        if pin.value == False:
            # active low
            data |= 0x00030000
            if pull:
                data |= 0x0000000C
        else:
            data |= 0x00020000
            if pull:
                data |= 0x00000008
        set_uint32_at(pin_cnf_addr, data)
    set_uint32_at(0x40000500, 1)


def clear_deep_sleep():
    data = get_uint32_at(0x40000400)
    print(f"reset field {data:x}")
    #set_uint32_at(0x40000400, data & 0xffff0000)


_NOT_FOUND = object()

class cached_property:
    """
    Copy of functools cached_property
    """
    def __init__(self, func):
        self.func = func
        self.cached_name = f"_{func.__name__}"
        if hasattr(func, "__doc__"):
            self.__doc__ = func.__doc__

    def __get__(self, instance, owner=None):
        if hasattr(instance, self.cached_name):
            return getattr(instance, self.cached_name)
        else:
            result = self.func(instance)
            setattr(instance, self.cached_name, result)
            return result

def simplify(formatted_exception:str):
    lines = formatted_exception.splitlines()
    import re
    pattern = r'File "(.*)", line (\d+), in (.*)$'
    matches = re.search(pattern, lines[-2])
    if matches:
        return ':'.join(matches.groups())+'\r\n'+lines[-1]
    else:
        return '\r\n'.join(lines[-2:])

def partial(func, *args, **kwargs):
    def f():
        return func(*args, **kwargs)
    return f


def convert_voltage_to_progress(voltage:float, maximum:int):
    if voltage < MIN_VOLTAGE:
        return 0
    if voltage > MAX_VOLTAGE:
        return maximum
    return int(maximum*(voltage-MIN_VOLTAGE)/(MAX_VOLTAGE-MIN_VOLTAGE))


def clean_block_text(text: str) ->str:
    return '\r\n'.join(x.strip() for x in text.splitlines() if x.strip())


MIN_VOLTAGE=3.5
MAX_VOLTAGE=4.2
