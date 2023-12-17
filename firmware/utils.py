import gc
import os

import microcontroller
import memorymap
import sys

from .debug import logger


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


_NOT_FOUND = object()


def simplify(formatted_exception: str):
    lines = formatted_exception.splitlines()
    import re
    pattern = r'File "(.*)", line (\d+), in (.*)$'
    if len(lines) < 2:
        return lines[0]
    matches = re.search(pattern, lines[-2])
    if matches:
        return ':'.join(matches.groups()) + '\r\n' + lines[-1]
    else:
        return '\r\n'.join(lines[-2:])


def partial(func, *args, **kwargs):
    def f():
        return func(*args, **kwargs)

    return f


def convert_voltage_to_progress(voltage: float, maximum: int):
    if voltage < MIN_VOLTAGE:
        return 0
    if voltage > MAX_VOLTAGE:
        return maximum
    return int(maximum * (voltage - MIN_VOLTAGE) / (MAX_VOLTAGE - MIN_VOLTAGE))


def set_nvm(text: bytes):
    microcontroller.nvm[0:len(text)] = text


def check_nvm(text: bytes):
    return microcontroller.nvm[0:len(text)] == text


def clear_nvm():
    microcontroller.nvm[0:32] = b'\xff' * 32


def clean_block_text(text: str) -> str:
    """
    Takes some triple quoted text and removes empty lines and left and right spaces.
    :param str text: text to clean
    :return: cleaned text
    """
    return '\r\n'.join(x.strip() for x in text.splitlines() if x.strip())


def check_mem(text: str):
    gc.collect()
    logger.debug(f"{text} mem: {gc.mem_free()}")


MIN_VOLTAGE = 3.5
MAX_VOLTAGE = 4.2


def diskfree():
    """
    :return: Disk space available in kB
    """
    data = os.statvfs('/')
    block_size = data[0]
    free_blocks = data[3]
    return (block_size * free_blocks) / 1024
