# This script updates a SAP6
import glob
import os
import shutil
import subprocess
import json
import time
import serial

TTY_SYS_DIR = "/sys/class/tty/"

FIRMWARE_FILE = "firmware.uf2"

BOOTLOADER_NAME = "XIAO-SENSE"

SAP6_NAMES = ['CIRCUITPY', 'SAP6']


def find_usb_devices():
    results = subprocess.check_output(("lsblk", "-J", "-o", "PATH,MOUNTPOINT,LABEL"))
    data = json.loads(results)['blockdevices']
    data = [x for x in data if x['label'] and x['mountpoint']]
    data = {x['label']: x for x in data}
    return data


def get_circuitpython_dir():
    devs = find_usb_devices()
    if "CIRCUITPY" in devs:
        dev = devs["CIRCUITPY"]
        # rename to SAP6
        subprocess.run(["sudo", "-S", "fatlabel", dev['path'], "SAP6"])
        return dev['mountpoint']
    if "SAP6" in devs:
        return devs["SAP6"]["mountpoint"]
    return None


def clear_folder(path_to_clear):
    print("Before clear folder:")
    print(os.listdir(path_to_clear))
    for dir_entry in os.listdir(path_to_clear):
        dir_entry = os.path.join(path_to_clear, dir_entry)
        try:
            if os.path.isdir(dir_entry):
                shutil.rmtree(dir_entry)
            else:
                os.remove(dir_entry)
        except OSError:
            pass
    print("After clear folder:")
    print(os.listdir(path_to_clear))


def find_serial_port():
    for tty_file in os.listdir(TTY_SYS_DIR):
        dev_data = os.path.join(TTY_SYS_DIR, tty_file, "device/interface")
        try:
            with open(dev_data) as iface:
                if "CircuitPython" in iface.readline():
                    return os.path.join("/dev/", tty_file)
        except OSError:
            pass
    return None


def upgrade_firmware():
    print("Finding SAP6 in bootloader mode")
    devs = find_usb_devices()
    if BOOTLOADER_NAME not in devs:
        print("Please connect the SAP6, and put it into bootloader mode")
        while True:
            time.sleep(1)
            devs = find_usb_devices()
            if BOOTLOADER_NAME in devs:
                break
    dev = devs[BOOTLOADER_NAME]
    print("SAP6 found")
    print("Updating CircuitPython firmware")
    shutil.copyfile(FIRMWARE_FILE, os.path.join(dev['mountpoint'], FIRMWARE_FILE))


# upgrade_firmware()

print("Waiting for CircuitPython disc")
while True:
    time.sleep(1)
    path = get_circuitpython_dir()
    if path is not None:
        break

print("Wiping CircuitPython dir")
clear_folder(path)

print("Testing hardware")
ser_port = find_serial_port()
if ser_port is None:
    print("SERIAL PORT NOT FOUND - EXITING")
    exit()
with serial.Serial(ser_port) as ser:
    shutil.copy("../pins.py", path)
    shutil.copyfile("fw_test.py", os.path.join(path, "code.py"))
    # copy full firmware over
    while True:
        line: bytes = ser.readline()
        if line is not None:
            print(line.decode('UTF-8').strip())
        if b"HW TEST COMPLETE" in line:
            break

print("Hardware test successful")
clear_folder(path)
print("Copying fonts")
shutil.copytree("../fonts", os.path.join(path, "fonts"))
print("Copying images")
shutil.copytree("../images", os.path.join(path, "images"))
print("Copying manual")
shutil.copy("manual.pdf", path)
print("Copying python files")
for f in glob.glob("../*.py"):
    if "code.py" not in f:
        shutil.copy(f, path)
shutil.copy("../code.py", path)
