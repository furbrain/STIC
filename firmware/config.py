import json
import adafruit_logging as logging
from mag_cal import Calibration

logger = logging.getLogger()

_CONFIG_FILE = "/config.json"
_DEFAULT_AXES_MAG = "-Y+X+Z"
_DEFAULT_AXES_GRAV = "+Y-X-Z"
class Config:
    DEGREES = 0
    GRADS = 1
    METRIC = 0
    IMPERIAL = 1

    def __init__(self,
                 timeout: int = 10,
                 angles: int = DEGREES,
                 units: int = METRIC,
                 mag_axes: str = _DEFAULT_AXES_MAG,
                 grav_axes: str = _DEFAULT_AXES_GRAV,
                 calib: dict = None):
        self.timeout = timeout
        self.angles = angles
        self.units = units
        self.mag_axes = mag_axes
        self.grav_axes = grav_axes
        self._dirty = False
        if calib:
            self.calib = Calibration.from_dict(calib)
        else:
            self.calib = None

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
            json.dump(self.as_dict(),f)

    @classmethod
    def load(cls) -> "Config":
        try:
            with open(_CONFIG_FILE, "r") as f:
                dct = json.load(f)
        except OSError:
            dct = {}
        return cls(**dct)

    def set_var_and_save(self, varname, value):
        setattr(self, varname, value)
        self.save()

