try:
    # noinspection PyUnresolvedReferences
    from typing import Optional, Tuple, Protocol

    class Magnetometer(Protocol):
        magnetic: Tuple[float, float, float]


    class Accelerometer(Protocol):
        acceleration: Tuple[float, float, float]


    from async_button import Button, MultiButton
    from async_buzzer import Buzzer
    from .hardware import HardwareBase
    from .config import Config

except ImportError:
    Magnetometer = None
    Accelerometer = None


# noinspection PyUnusedLocal
def not_implemented(*args, **kwargs):
    raise NotImplementedError


# noinspection PyUnusedLocal
def abstractmethod(f):
    return not_implemented
