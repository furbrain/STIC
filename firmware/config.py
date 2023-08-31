import json

try:
    from typing import Optional
except ImportError:
    pass

from mag_cal import Calibration

_GRADS_PER_DEGREE = 400 / 360.0
_CONFIG_FILE = "/config.json"
_DEFAULT_AXES_MAG = "+X+Y-Z"
_DEFAULT_AXES_GRAV = "-Y-X+Z"
_FEET_PER_METRE = 3.28084


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
                 anomaly_strictness: int = Calibration.SOFT,
                 laser_cal: int = 0,
                 calib: dict = None):
        self.timeout = timeout
        self.angles = angles
        self.units = units
        self.mag_axes = mag_axes
        self.grav_axes = grav_axes
        self.anomaly_strictness = anomaly_strictness
        self.laser_cal = laser_cal
        self._dirty = False
        if calib:
            self.calib: Optional[Calibration] = Calibration.from_dict(calib)
        else:
            self.calib: Optional[Calibration] = None

    def as_dict(self):
        dct = {}
        for k, v in self.__dict__.items():
            if not k.startswith("_"):
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
    def load(cls) -> "Config":
        try:
            with open(_CONFIG_FILE, "r") as f:
                dct = json.load(f)
        except (OSError, ValueError):
            dct = {}
        return cls(**dct)

    def set_var(self, varname, value):
        setattr(self, varname, value)
        self._dirty = True

    def get_azimuth_text(self, azimuth: float) -> str:
        azimuth = azimuth % 360  # move to proper range
        if self.angles == self.DEGREES:
            return f"{azimuth:05.1f}°"
        elif self.angles == self.GRADS:
            azimuth *= _GRADS_PER_DEGREE  # convert to grads
            return f"{azimuth:05.1f}g"

    def get_inclination_text(self, inclination: float) -> str:
        if self.angles == self.DEGREES:
            return f"{inclination:+05.1f}°"
        elif self.angles == self.GRADS:
            inclination *= _GRADS_PER_DEGREE  # convert to grads
            return f"{inclination:+05.1f}g"

    def get_distance_text(self, distance: float) -> str:
        if self.units == self.METRIC:
            return f"{distance:.3f}m"
        elif self.units == self.IMPERIAL:
            distance *= _FEET_PER_METRE
            return f"{distance:.3f}'"
