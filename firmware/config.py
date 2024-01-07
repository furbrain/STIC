import json
try:
    # noinspection PyUnresolvedReferences
    from typing import Optional
except ImportError:
    pass

from mag_cal import Calibration, Strictness

_GRADS_PER_DEGREE = 400 / 360.0
_CONFIG_FILE = "/config.json"
_DEFAULT_AXES_MAG = "+X+Y-Z"
_DEFAULT_AXES_GRAV = "-Y-X+Z"
_FEET_PER_METRE = 3.28084

HARD_STRICTNESS = Strictness(mag=2.0, grav=1.5, dip=3.0)

SOFT_STRICTNESS = Strictness(mag=5.0, grav=3.0, dip=5.0)

class Config:
    DEGREES = 0
    GRADS = 1
    METRIC = 0
    IMPERIAL = 1

    def __init__(self,
                 timeout: int = 60,
                 angles: int = DEGREES,
                 units: int = METRIC,
                 mag_axes: str = _DEFAULT_AXES_MAG,
                 grav_axes: str = _DEFAULT_AXES_GRAV,
                 anomaly_strictness: Strictness = SOFT_STRICTNESS,
                 laser_cal: int = 0.157,
                 save_readings: bool = False,
                 low_precision: bool = False,
                 calib: dict = None,
                 timer: int = 5):
        self.timeout = timeout
        self.angles = angles
        self.units = units
        self.mag_axes = mag_axes
        self.grav_axes = grav_axes
        if anomaly_strictness is None:
            self.anomaly_strictness = anomaly_strictness
        else:
            self.anomaly_strictness = Strictness(*anomaly_strictness)
        self.laser_cal = laser_cal
        self.save_readings = save_readings
        self.low_precision = low_precision
        self._dirty = False
        if calib:
            self.calib: Optional[Calibration] = Calibration.from_dict(calib)
        else:
            self.calib: Optional[Calibration] = None
        self.timer = timer

    def as_dict(self):
        dct = {}
        for k, v in self.__dict__.items():
            if isinstance(v, Strictness):
                dct[k] = list(v)
            elif k.startswith("_"):
                continue
            else:
                if hasattr(v, "as_dict"):
                    dct[k] = v.as_dict()
                else:
                    dct[k] = v
        return dct

    def save_if_changed(self):
        if self._dirty:
            self.save()

    def save(self):
        with open(_CONFIG_FILE, "w") as f:
            json.dump(self.as_dict(), f)
        self._dirty = False

    @classmethod
    def load(cls, fname=_CONFIG_FILE) -> "Config":
        try:
            with open(fname, "r") as f:
                dct = json.load(f)
        except (OSError, ValueError):
            dct = {}
        return cls(**dct)

    def set_var(self, varname, value):
        setattr(self, varname, value)
        self._dirty = True

    def get_angle_precision(self):
        if self.low_precision:
            return 0
        else:
            return 1

    def get_distance_precision(self):
        if self.low_precision:
            return 2
        else:
            return 3

    def get_azimuth_text(self, azimuth: float, decimals: Optional[int] = None, with_unit=True) -> str:
        if decimals is None:
            decimals = self.get_angle_precision()
        if decimals > 0:
            chars = decimals + 4
        else:
            chars = 3
        azimuth = azimuth % 360  # move to proper range
        if with_unit:
            unit = self.get_angle_unit()
        else:
            unit = ""
        azimuth = self.convert_angle(azimuth)
        return f"{azimuth:0{chars}.{decimals}f}{unit}"

    def get_inclination_text(self, inclination: float, decimals: Optional[int] = None, with_unit=True) -> str:
        if decimals is None:
            decimals = self.get_angle_precision()
        if decimals > 0:
            chars = decimals + 4
        else:
            chars = 3
        if with_unit:
            unit = self.get_angle_unit()
        else:
            unit = ""
        inclination = self.convert_angle(inclination)
        return f"{inclination:+0{chars}.{decimals}f}{unit}"


    def get_distance_text(self, distance: float, decimals: Optional[int] = None, with_unit=True) -> str:
        if decimals is None:
            decimals = self.get_distance_precision()
        if with_unit:
            unit = self.get_distance_unit()
        else:
            unit = ""
        distance = self.convert_distance(distance)
        return f"{distance:.{decimals}f}{unit}"

    def get_angle_unit(self):
        if self.angles == self.DEGREES:
            return "°"
        elif self.angles == self.GRADS:
            return "g"
        else:
            raise ValueError("Unknown angle setting")

    def get_distance_unit(self):
        if self.units == self.METRIC:
            return "m"
        elif self.units == self.IMPERIAL:
            return "'"
        else:
            raise ValueError("Unknown distance setting")

    def convert_angle(self, angle):
        if self.angles == self.GRADS:
            return angle * _GRADS_PER_DEGREE
        else:
            return angle

    def convert_distance(self, distance):
        if self.units == self.IMPERIAL:
            return distance * _FEET_PER_METRE
        else:
            return distance
