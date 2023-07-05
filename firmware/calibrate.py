import asyncio
import mag_cal
from async_button import Button
try:
    import numpy as np
except ImportError:
    from ulab import numpy as np
import display
import hardware
import config
import json

async def calibrate_sensors(devices: hardware.Hardware, cfg: config.Config, disp: display.Display):
    devices.laser_enable(True)
    disp.show_info("Take a series of\r\nreadings, press\r\nA for a leg,\r\nB to finish")
    await devices.button_a.wait(Button.SINGLE)
    await devices.laser.set_laser(True)
    mags = []
    gravs = []
    count = 0
    while True:
        disp.show_info(f"Legs: {count}\r\nIdeally at least 24\r\nWith two groups\r\nin same " +
                       f"direction")
        button, click = await devices.both_buttons.wait(a=Button.SINGLE, b=Button.SINGLE)
        if button == "a":
            mags.append(devices.magnetometer.magnetic)
            gravs.append(devices.accelerometer.acceleration)
            devices.beep_bip()
        elif button == "b":
            devices.beep_bop()
            break
        count += 1
    cal = mag_cal.Calibration(mag_axes=cfg.mag_axes, grav_axes=cfg.grav_axes)
    try:
        #save data if we can
        with open("calibration_data.json","w") as f:
            json.dump({"mag": mags, "grav": gravs}, f)
    except OSError:
        pass
    accuracy = cal.calibrate(np.array(mags), np.array(gravs))
    if accuracy < 0.25:
        quality = "excellent"
    elif accuracy < 0.5:
        quality = "good"
    elif accuracy < 1.0:
        quality = "acceptable"
    else:
        quality = "poor"
    report = f"Accuracy is {accuracy:.3f}°\r\nThis is {quality}\r\nPress A to Save\r\nB to Discard"
    disp.show_info(report)
    button, click = await devices.both_buttons.wait(a=Button.SINGLE, b=Button.SINGLE)
    if button == "a":
        cfg.calib = cal
        cfg.save()
    elif button == "b":
        pass


async def calibrate_distance(devices: hardware.Hardware, cfg: config.Config, disp: display.Display):
    devices.laser_enable(True)
    disp.show_info("Place device\r\n1m from an object\r\nand press A")
    await devices.button_a.wait(Button.SINGLE)
    disp.show_info("Measuring...\r\nDo not touch\r\ndevice")
    await asyncio.sleep(1)
    dist = 0
    for i in range(10):
        dist += await devices.laser.measure()
        devices.beep_bip()
    dist /= 10.0
    dist = 1000 - dist
    if dist > 200:
        disp.show_info(f"Offset is {dist}mm\r\nThis seems very long\r\nAre you sure?\r\nA: Yes B: No")
        btn, _ = await devices.both_buttons.wait(a=Button.SINGLE, b=Button.SINGLE)
        if btn == "b":
            return
    elif dist < -50:
        text = f"Offset is {dist}mm\r\nThis seems very short\r\nAre you sure?\r\nA: Yes B: No"
        disp.show_info(text)
        btn, _ = await devices.both_buttons.wait(a=Button.SINGLE, b=Button.SINGLE)
        if btn == "b":
            return
    cfg.laser_cal = 0
    cfg.save()
    disp.show_info("Calibration complete")
