import mag_cal
import config
import json
import numpy as np
np.set_printoptions(suppress=True)
def analyse(cfg: config.Config, fname: str):
    print(f"Showing data from {fname}")
    with open(fname, "r") as f:
        data = json.load(f)
        mag = data['mag']
        grav = data['grav']
        angles = np.vstack(cfg.calib.get_angles(mag, grav)).T
        print("  Heading        Inclination")
        print(angles[:,:2])
        dips = cfg.calib.get_dips(mag, grav)
        fs = cfg.calib.get_field_strengths(mag, grav)
        fields = np.vstack((*fs, dips)).T
        print("  Mag          Grav       Dip")
        print(fields)
        return fields

def show_percentages(avg, data):
    print("  Mag          Grav       Dip")
    print(100 - data / avg * 100)

def show_absolute(avg, data):
    print("  Mag          Grav       Dip")
    print(data-avg)

cfg = config.Config.load("/media/phil/SAP6/config.json")
cal_fields = analyse(cfg, '/media/phil/SAP6/calibration_data.json')
test_fields = analyse(cfg, '/media/phil/SAP6/debug_shots.json')
avg_fields = np.mean(cal_fields,axis=0)
print("%age change: Cal")
show_percentages(avg_fields,cal_fields)
print("%age change: Test")
show_percentages(avg_fields, test_fields)
print("absolute change: Cal")
show_absolute(avg_fields,cal_fields)
print("absolute change: Test")
show_absolute(avg_fields, test_fields)
