import binascii

import microcontroller

__version__ = "1.0.0"
__hw_version__ = "1.0.0"

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
    crc = binascii.crc32(microcontroller.cpu.uid)
    a = crc % 100
    return a//10, a % 10


def get_short_name() -> str:
    a, b = get_id_indexes()
    return f"{BASENAME}_{chr(a+0x41)}{chr(b+0x41)}"


def get_long_name() -> str:
    a,b = get_id_indexes()
    return f"{ADJECTIVES[a]} {ANIMALS[b]}"

def get_sw_version() -> str:
    return __version__

def get_hw_version() -> str:
    return __hw_version__