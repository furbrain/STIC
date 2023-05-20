import json
import adafruit_logging as logging

logger = logging.getLogger()

_CONFIG_FILE = "/config.json"

class Config:
    DEGREES = 0
    GRADS = 1
    METRIC = 0
    IMPERIAL = 1

    def __init__(self,
                 timeout: int = 10,
                 angles: int = DEGREES,
                 units: int = METRIC):
        self.timeout = timeout
        self.angles = angles
        self.units = units

    def as_dict(self):
        dict = {k:v for k,v in self.__dict__.items() if not k.startswith("_")}
        return dict

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

