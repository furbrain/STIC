import binascii

__version__ = "1.5.0"

from . import layouts

try:
    # noinspection PyUnresolvedReferences
    from typing import Tuple, Optional
except ImportError:
    pass

LAYOUTS = {(6, 1, 0): layouts.layout_6_1,
           (6, 2, 0): layouts.layout_6_2}

ADJECTIVES = [
    "Angry",
    "Bored",
    "Curious",
    "Devious",
    "Excited",
    "Fierce",
    "Grumpy",
    "Hungry",
    "Idle",
    "Jealous"
]
ANIMALS = [
    "Antelope",
    "Badger",
    "Cheetah",
    "Dolphin",
    "Eagle",
    "Fox",
    "Gorilla",
    "Hamster",
    "Iguana",
    "Jaguar"
]
BASENAME = "SAP6"


def get_id_indexes():
    import microcontroller  # hidden so can use version.py in documentation
    crc = binascii.crc32(microcontroller.cpu.uid)
    a = crc % 100
    return a // 10, a % 10


def get_short_name() -> str:
    a, b = get_id_indexes()
    return f"{BASENAME}_{chr(a + 0x41)}{chr(b + 0x41)}"


def get_long_name() -> str:
    a, b = get_id_indexes()
    return f"{ADJECTIVES[a]} {ANIMALS[b]}"


def get_sw_version() -> str:
    return __version__


def get_hw_version() -> Tuple[int, int, int]:
    import microcontroller
    version = tuple(microcontroller.nvm[-3:])
    if version == (255, 255, 255):
        version = (6, 1, 0)
    return version


def get_hw_version_as_str() -> str:
    v = get_hw_version()
    return ".".join(str(x) for x in v)


def get_layout(version: Optional[Tuple[int, int, int]] = None) -> layouts.Layout:
    if version is None:
        version = get_hw_version()
    return LAYOUTS[version]


def get_pins(layout: Optional[layouts.Layout] = None):
    if layout is None:
        layout = get_layout()
    from . import pins
    pin_group = getattr(pins, layout.pins)
    return pin_group


def get_device(version: Optional[Tuple[int, int, int]] = None):
    layout = get_layout(version)
    dev = layout.hardware
    pins = get_pins(layout)
    mod = __import__(f"firmware.versions.{dev}")
    module = getattr(mod.versions, dev)
    return module.Hardware(pins)
