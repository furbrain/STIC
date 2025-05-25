try:
    import numpy as np
except ImportError:
    # noinspection PyUnresolvedReferences
    from ulab import numpy as np
from .debug import logger
from . import utils

def rot3Dsc(s, c, ax):
    """
    rotation matrix along axis "ax", by angle alpha such s=sin(alpha) and c=cos(alpha)
    """
    rot = np.zeros((3, 3))
    rot[ax, ax] = 1
    axp = ax - 1 if ax > 0 else 2
    axn = ax + 1 if ax < 2 else 0
    rot[axp, axp] = c
    rot[axn, axn] = c
    rot[axp, axn] = -s
    rot[axn, axp] = s
    return rot


def calib_fit_rotM_cstdip(mcorr, gcorr, axis=0, verbose=True):
    """
    correct magnetic readings roll (rotation along laser axis) such magnetic dip is constant
    mcorr: magn sensor readings corrected (except roll)
    gcorr: grav sensor readings corrected (except roll)
    return: rotation matrix correcting magnetic sensor roll

    The 2 first steps of the calibration are fitting sensor readings to an ellipsoid and then find misalignment
    between laser axis and sensor axis.
    Those 2 steps are done independently for the magnetic and the grav sensor respectively.
    However those steps can introduce an uncontrolled small roll rotation for each sensor.
    Even if we don't care about the final calculated roll angle of the device, the roll between the magnetic and grav
    sensor must be consistent for accurate azimuth calculation.
    The way to achieve this is to be make sure that the dip angle between magnetic and gravitational field vectors is
    constant as best as possible.


    The following rotation matrix allow straightforward least square formulation:
    (1  0  0
     0  c -s
     0  s  c )
    where s=sinus(roll) and c is (initially) approximated to 1 (as roll angle is small and cos(roll)=~1)

    Least square fitting will approximate the equation: rotated(mcorr).gcorr=dp, where dp is constant and . is the dot product
    which translates to: mcorr.gcorr + s*(mcorr.y*gcorr.z - mcorr.z*gcorr.y + d = 0

    The process is repeated for 3 iterations by incrementally correcting the magnetic roll at each iteration.
    At each iteration the roll angle correction to find becomes smaller and the approximation cos(roll)=1 quickly becomes very accurate.

    (c) F. Ballenegger, Anamosic Ballenegger Design, 2024
    Granted permission to use and modify for any civil application.

    """

    oa = tuple({0, 1, 2} - {axis})  # others axes
    sign = (1, -1, -1)

    rot = np.eye(3)
    prevrotsin = None
    for it in range(3):
        logger.debug(rot.shape)
        logger.debug(mcorr.shape)
        m = np.dot(rot, mcorr.transpose()).transpose()
        xb = np.sum(m * gcorr, axis=-1)
        xa = m[:, oa[0]] * gcorr[:, oa[1]] - m[:, oa[1]] * gcorr[:, oa[0]]
        D = np.concatenate(
            (
                xa.reshape((mcorr.shape[0], 1)),
                np.ones((mcorr.shape[0], 1)),
            ),
            axis=-1,
        )
        coeffs, _ = utils.lstsq(D, xb)
        s = coeffs[0]
        if prevrotsin is not None and abs(s) > prevrotsin:
            raise (
                ValueError(
                    "rotation must decrease at each iteration, maybe rotation direction issue ?"
                )
            )
        prevrotsin = abs(s)
        c = np.sqrt(1 - s * s)
        rot = np.dot(rot,rot3Dsc(sign[axis] * s, c, axis))
    # rot = rot @ np.array([[1,0,0],[0,c,s],[0,-s,c]])
    return rot

#this is a function that can be monkey patched into mag_cal
def align_sensor_roll(self, mag_data, grav_data):
    mag_data = self.mag.apply(mag_data)
    grav_data = self.grav.apply(grav_data)
    rot = calib_fit_rotM_cstdip(mag_data, grav_data, 1, False)
    self.mag.transform = np.dot(self.mag.transform, rot.transpose())
