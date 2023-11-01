#!/bin/env python3

# This script updates a SAP6
import glob
import os
import shutil
import subprocess
import json
import sys
import time
import serial
import argparse

TTY_SYS_DIR = "/sys/class/tty/"

FIRMWARE_FILE = "firmware.uf2"

BOOTLOADER_NAME = "XIAO-SENSE"

SAP6_NAMES = ['CIRCUITPY', 'SAP6']

RESET_DEVICE = False


parser = argparse.ArgumentParser(
    prog="installer.py",
    description="Installer for the SAP6"
)
parser.add_argument("-f", "--skip-firmware",
                    help="Do not try to update the CircuitPython Firmware",
                    action="store_true")
parser.add_argument("-t", "--skip-tests",
                    help="Skip the testing section - just install the code",
                    action="store_true")

options = parser.parse_args()
# noinspection SpellCheckingInspection
def find_usb_devices():
    results = subprocess.check_output(("lsblk", "-J", "-o", "PATH,MOUNTPOINT,LABEL"))
    data = json.loads(results)['blockdevices']
    data = [x for x in data if x['label'] and x['mountpoint']]
    data = {x['label']: x for x in data}
    return data


# noinspection SpellCheckingInspection
def get_circuitpython_dir(rename=False):
    devs = find_usb_devices()
    if "CIRCUITPY" in devs:
        dev = devs["CIRCUITPY"]
        # rename to SAP6
        if rename:
            subprocess.run(["sudo", "-S", "fatlabel", dev['path'], "SAP6"])
        return dev['mountpoint']
    if "SAP6" in devs:
        return devs["SAP6"]["mountpoint"]
    return None


def clear_folder(path_to_clear):
    print("Before clear folder:")
    print(os.listdir(path_to_clear))
    try:
        shutil.rmtree(path_to_clear)
    except PermissionError:
        pass
    # for dir_entry in os.listdir(path_to_clear):
    #     dir_entry = os.path.join(path_to_clear, dir_entry)
    #     try:
    #         if os.path.isdir(dir_entry):
    #             shutil.rmtree(dir_entry)
    #         else:
    #             os.remove(dir_entry)
    #     except OSError:
    #         pass
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


# noinspection SpellCheckingInspection
def upgrade_firmware():
    cp_dev = get_circuitpython_dir()
    if RESET_DEVICE and cp_dev is not None:
        print("Putting SAP6 in bootloader mode, this will take about 10s")
        shutil.copy("resetter.py", os.path.join(cp_dev,"code.py"))
        time.sleep(8)
    else:
        print("Finding SAP6 in bootloader mode")
        devs = find_usb_devices()
        if BOOTLOADER_NAME not in devs:
            print("Please connect the SAP6, and put it into bootloader mode")
    while True:
        devs = find_usb_devices()
        if BOOTLOADER_NAME in devs:
            break
        time.sleep(1)
    dev = devs[BOOTLOADER_NAME]
    print("SAP6 found")
    print("Updating CircuitPython firmware")
    shutil.copyfile(FIRMWARE_FILE, os.path.join(dev['mountpoint'], FIRMWARE_FILE))

def run_tests():
    clear_folder(path)
    os.mkdir(fw_path)
    print("Testing hardware")
    ser_port = find_serial_port()
    if ser_port is None:
        print("SERIAL PORT NOT FOUND - EXITING")
        exit()
    with serial.Serial(ser_port) as ser:
        shutil.copy("../pins.py", fw_path)
        shutil.copyfile("fw_test.py", os.path.join(path, "code.py"))
        # copy full firmware over
        while True:
            line: bytes = ser.readline()
            if line is not None:
                print(line.decode('UTF-8').strip())
            if b"HW TEST COMPLETE" in line:
                break
    print("Hardware test successful")


if not options.skip_firmware:
    upgrade_firmware()

print("Waiting for CircuitPython disc")
while True:
    time.sleep(1)
    path = get_circuitpython_dir(rename=True)
    if path is not None:
        break

print("Wiping CircuitPython dir")
fw_path = os.path.join(path, "firmware")


if not options.skip_tests:
    run_tests()

clear_folder(path)
os.mkdir(fw_path)
print("Copying fonts")
shutil.copytree("../fonts", os.path.join(path, "fonts"))
print("Copying images")
shutil.copytree("../images", os.path.join(path, "images"))
print("Copying manual")
shutil.copy("manual.pdf", path)
print("Copying python files")
for f in glob.glob("../*.py"):
    shutil.copy(f, fw_path)
shutil.copy("boot.py", path)
shutil.copy("code.py", path)
