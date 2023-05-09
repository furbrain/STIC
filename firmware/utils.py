import microcontroller
import memorymap
import sys
import time
import alarm


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


def true_deep_sleep(*pins: alarm.pin.PinAlarm, pull: bool = True):
    # set up pins
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
    # turn off QSPI
    # qspi_base_addr = 0x40029000
    # ifconfig0 = get_uint32_at(qspi_base_addr + 0x544)
    # ifconfig0 |= 0x80
    # set_uint32_at(qspi_base_addr + 0x544, ifconfig0)
    # ifconfig1 = get_uint32_at(qspi_base_addr + 0x600)
    # ifconfig1 |= 0x01000000
    # set_uint32_at(qspi_base_addr + 0x600, ifconfig1)
    # set_uint32_at(qspi_base_addr + 0x614, 0x00010001)
    # time.sleep(0.1)
    # aaand shutdown
    set_uint32_at(0x40000500, 1)
