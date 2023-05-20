import pwmio
import sys
from microcontroller import Pin

from utils import get_uint32_at, set_uint32_at, get_uint16_at, set_uint16_at, get_pin_no

PWM_BASE_ADDRS = [
    0x4001C000,
    0x40021000,
    0x40022000,
    0x4002D000
]

PSEL = 0x560
SEQ_PTR = 0x520
TASK_SEQSTART = 0x008

class InvertingPWMOut:

    def _find_pwm_module_and_channel(self, pin: Pin):
        pin_no = get_pin_no(pin)
        for i, addr in enumerate(PWM_BASE_ADDRS):
            for j in range(4):
                data = get_uint32_at(addr + PSEL + j * 4)
                if data == pin_no:
                    return i, j
        return None, None

    def _set_pwm_channel(self, module: int, channel: int, value: int):
        addr = PWM_BASE_ADDRS[module] + PSEL + channel * 4
        set_uint32_at(addr, value)

    def _set_pwm_module_and_channel(self, module: int, channel: int, pin: Pin):
        pin_no = get_pin_no(pin)
        self._set_pwm_channel(module, channel, pin_no)

    def _clear_pwm_channel(self, module: int, channel: int):
        self._set_pwm_channel(module, channel, 0xffffffff)


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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deinit()

    def _update_inverted_duty_cycle(self):
        addr = PWM_BASE_ADDRS[self.module]
        seq_addr = get_uint32_at(addr+SEQ_PTR)
        duty_cycle = get_uint16_at(seq_addr)
        if duty_cycle not in (0, 0x8000):
            duty_cycle ^= 0x8000 # invert polarity
        set_uint16_at(seq_addr+2, duty_cycle)
        set_uint32_at(addr+TASK_SEQSTART, 1)

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
        self._clear_pwm_channel(self.module, 1)
        self.pwm.deinit()
