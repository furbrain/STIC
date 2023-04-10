import digitalio
import microcontroller
import pwmio
import uctypes # note this class needs uctypes which is not compiled as standard
import sys
from microcontroller import Pin

PWM_BASE_ADDRS = [
    0x4001C000,
    0x40021000,
    0x40022000,
    0x4002D000
]

PSEL = 0x560
SEQ_PTR = 0x520

class InvertingPWMOut:
    def _get_pin_no(self, pin):
        for p in dir(microcontroller.pin):
            if pin is getattr(microcontroller.pin, p):
                port, pin_no = p[1:].split("_")
                port = int(port)
                pin_no = int(pin_no)
                return port*32 + pin_no
        return None

    def _find_pwm_module_and_channel(self, pin: Pin):
        pin_no = self._get_pin_no(pin)
        for i, addr in enumerate(PWM_BASE_ADDRS):
            for j in range(4):
                data = self._get_uint32_at(addr + PSEL + j * 4)
                if data == pin_no:
                    return i, j
        return None, None

    def _set_pwm_channel(self, module: int, channel: int, value: int):
        addr = PWM_BASE_ADDRS[module] + PSEL + channel * 4
        self._set_uint32_at(addr, value)

    def _set_pwm_module_and_channel(self, module: int, channel: int, pin: Pin):
        pin_no = self._get_pin_no(pin)
        self._set_pwm_channel(module, channel, pin_no)

    def _clear_pwm_channel(self, module: int, channel: int):
        self._set_pwm_channel(module, channel, 0xffffffff)
    def _get_uint32_at(self, addr: int):
        mem = uctypes.bytearray_at(addr, 4)
        data = int.from_bytes(mem, sys.byteorder)
        return data

    def _set_uint32_at(self, addr: int, value: int):
        data = value.to_bytes(4, sys.byteorder)
        mem = uctypes.bytearray_at(addr, 4)
        mem[:] = data

    def _get_uint16_at(self, addr: int):
        mem = uctypes.bytearray_at(addr, 2)
        data = int.from_bytes(mem, sys.byteorder)
        return data

    def _set_uint16_at(self, addr: int, value: int):
        data = value.to_bytes(2, sys.byteorder)
        mem = uctypes.bytearray_at(addr, 2)
        mem[:] = data


    def __init__(self, pin_a: Pin, pin_b: Pin):
        if sys.platform != 'nRF52840':
            raise NotImplementedError("This code only works on nrf52840")
        self.pin_a = pin_a
        self.pin_b = pin_b
        self.pwm = pwmio.PWMOut(pin_a, variable_frequency=True)
        self.module, channel = self._find_pwm_module_and_channel(pin_a)
        if channel != 0:
            raise ValueError("shouldn't be able to get here - pwm module should be unique to this"
                             " pin")
        self._set_pwm_module_and_channel(self.module, 1, pin_b)

    def _update_inverted_duty_cycle(self):
        addr = PWM_BASE_ADDRS[self.module]
        seq_addr = self._get_uint32_at(addr+SEQ_PTR)
        duty_cycle = self._get_uint16_at(seq_addr)
        duty_cycle ^= 0x8000 # invert polarity
        self._set_uint16_at(seq_addr+2, duty_cycle)

    @property
    def frequency(self):
        return self.pwm.frequency

    @frequency.setter
    def frequency(self, value):
        self.pwm.frequency = value
        self._update_inverted_duty_cycle()

    @property
    def duty_cycle(self):
        return self.pwm.duty_cycle

    @duty_cycle.setter
    def duty_cycle(self, value):
        self.pwm.duty_cycle = value
        self._update_inverted_duty_cycle()


    def deinit(self):
        self.pwm.deinit()
        self._clear_pwm_channel(self.module, 1)