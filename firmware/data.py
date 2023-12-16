import os
import re
import struct
from collections import namedtuple

import atexit

from .config import Config

try:
    # noinspection PyUnresolvedReferences
    from typing import Optional, Union, TextIO
except ImportError:
    pass

from .discarding_queue import DiscardingQueue

Leg = namedtuple("Leg", ("azimuth", "inclination", "distance"))

READINGS_DIR = "/readings/"

class FailedLeg:
    """
    This class simply represents a failed reading
    """


class Readings:
    """
    This class represents the set of most recent readings, whether a reading has been
    taken recently, and what is the current viewed reading
    """

    def __init__(self, from_bytes: Optional[bytes] = None, max_len=10):
        if from_bytes is not None:
            num_readings = from_bytes[0]
            length_required = min(num_readings, max_len) * struct.calcsize("3f")
            temp_bytes = bytes(from_bytes[0: 1 + length_required])
            temp_readings = [Leg(*struct.unpack_from("3f", temp_bytes, 1 + x * 3)) for x in range(num_readings)]
        else:
            temp_readings = []
        self._queue = DiscardingQueue(temp_readings, max_len)
        self.current_reading = None
        """None if no readings taken yet, otherwise last reading is -1, previous to that is -2 
        etc"""
        try:
            os.mkdir(READINGS_DIR)
        except OSError:
            pass
        self._trip_file: Optional[TextIO] = None

    def pack_into(self, store: bytearray):
        """
        Save latest readings into a byte array
        :param store: bytearray to store data in
        :return:
        """
        store[0] = len(self._queue)
        length_required = 1 + len(self._queue) * struct.calcsize("3f")
        b = bytearray(length_required)
        for i, leg in enumerate(self._queue):
            struct.pack_into("3f", b, 1 + i * 3, *leg)
        store[:length_required] = b

    def store_reading(self, leg: Leg, cfg: Config):
        self._queue.append(leg)
        self.current_reading = -1
        if cfg.save_readings and self.trip_file:
            texts = (
                cfg.get_distance_text(leg.distance, decimals=1)[:-1],
                cfg.get_azimuth_text(leg.azimuth, decimals=1)[:-1],
                cfg.get_inclination_text(leg.inclination, decimals=3)[:-1],
            )
            self.trip_file.write(f"{', '.join(texts)}\n")

    def get_prev_reading(self):
        if self.current_reading is None:
            if len(self._queue) > 0:
                self.current_reading = -1
        else:
            self.current_reading -= 1
            if self.current_reading < -len(self._queue):
                self.current_reading = -1

    @property
    def current(self) -> Union[Leg, FailedLeg]:
        return self._queue[self.current_reading]

    @property
    def reading_taken(self) -> bool:
        return self.current_reading is not None

    @property
    def trip_file(self):
        if self._trip_file:
            return self._trip_file
        try:
            max_trip = 0
            for fname in os.listdir(READINGS_DIR):
                match = re.match(r"Trip(\d\d\d\d\d).csv", fname)
                if match:
                    max_trip = max(max_trip, int(match.group(1)))
            f: TextIO = open(f"{READINGS_DIR}Trip{(max_trip + 1):05}.csv", "w")
            f.write("Distance, Compass, Clino\n")
            atexit.register(f.close)
            self._trip_file = f
            return f
        except OSError:
            return None

    def flush(self):
        #not using the property because we don't want to create a file if not already existing here...
        if self._trip_file:
            self._trip_file.flush()


readings = Readings()




