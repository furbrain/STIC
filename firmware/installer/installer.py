#!/bin/env python3

import argparse
# This script updates a SAP6
import glob
import json
import os
import shutil
import subprocess
import time
import sys

import serial

TTY_SYS_DIR = "/sys/class/tty/"

FIRMWARE_FILE = "firmware.uf2"

BOOTLOADER_NAME = "XIAO-SENSE"

DEFAULT_HW_VERSION = "6.2.0"

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
parser.add_argument("-c", "--skip-code",
                    help="Skip the code installation",
                    action="store_true")

parser.add_argument("-hw", "--hw-version",
                    help="Specify the hardware version, set to 0 to skip",
                    default=DEFAULT_HW_VERSION,
                    action="store")

parser.add_argument("-d", "--debug",
                    help="Place a DEBUG file in the root directory, putting device in debug mode",
                    action="store_true")

parser.add_argument("-l", "--calibration",
                    help="Place a calibration file in the root directory,"
                         "allowing to perform a (incorrect) calibration",
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
    print(f"Clearing folder {path_to_clear}")
    try:
        shutil.rmtree(path_to_clear)
    except PermissionError:
        pass
    if len(os.listdir(path_to_clear)) > 0:
        print("Clear failed: ", os.listdir(path_to_clear))
        sys.exit(1)

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
        shutil.copy("resetter.py", os.path.join(cp_dev, "code.py"))
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
        sys.exit(0)
    with serial.Serial(ser_port) as ser:
        shutil.copy("../pins.py", fw_path)
        shutil.copy("../version.py", fw_path)
        shutil.copy("../layouts.py", fw_path)
        shutil.copyfile("fw_test.py", os.path.join(path, "code.py"))
        # copy full firmware over
        while True:
            line: bytes = ser.readline()
            if line is not None:
                print(line.decode('UTF-8').strip())
            if b"HW TEST COMPLETE" in line:
                break
    print("Hardware test successful")


def set_hw_version(major, minor, patch):
    clear_folder(path)
    print(f"Setting hardware version to {major}.{minor}.{patch}")
    ser_port = find_serial_port()
    if ser_port is None:
        print("SERIAL PORT NOT FOUND - EXITING")
        sys.exit(0)
    with serial.Serial(ser_port) as ser:
        ser.write(b'\x03')  # send ctrl-C
        time.sleep(1.0)
        ser.write(b'\n')  # send return
        time.sleep(1.0)
        output = ser.read_all()
        if not output.endswith(b">>> "):
            print("Unable to get to command line - EXITING")
            print(output.decode())
            sys.exit(1)
        ser.write(b'import microcontroller\r\n')
        ser.write(b'import supervisor\r\n')
        ser.write(f'microcontroller.nvm[-3:] = bytearray(({major},{minor},{patch}))\r\n'.encode())
        ser.write(b'supervisor.runtime.autoreload = True\r\n')
        ser.write(b'print("HW VERSION: " + ".".join(str(x) for x in microcontroller.nvm[-3:]))\r\n')
        time.sleep(1.0)
        output = ser.read_all()
        for line in output.splitlines():
            if line.startswith(b"HW VERSION"):
                print(line.decode())
        ser.write(b'\x04')  # send Ctrl-D to start auto running code.py


def install_code(debug: bool, calibration: bool):
    clear_folder(path)
    os.mkdir(fw_path)
    os.mkdir(versions_path)
    print("Copying fonts")
    shutil.copytree("../fonts", os.path.join(path, "fonts"))
    print("Copying images")
    shutil.copytree("../images", os.path.join(path, "images"))
    print("Copying manual")
    shutil.copy("manual.pdf", path)
    print("Copying python files")
    for f in glob.glob("../*.py"):
        shutil.copy(f, fw_path)
    for f in glob.glob("../versions/*.py"):
        shutil.copy(f, versions_path)
    if debug:
        print("Setting debug mode")
        with open(os.path.join(path, "DEBUG"), "w"):
            pass
    if calibration:
        print("adding calibration file")
        shutil.copy("../tests/calibration_data.json", path)
    print("Installing init files")
    shutil.copy("safemode.py", path)
    shutil.copy("boot.py", path)
    shutil.copy("code.py", path)


# first parse HW version
if options.hw_version == "0":
    hw_version = None
else:
    hw_version = tuple(int(x) for x in options.hw_version.split("."))
    if len(hw_version) != 3:
        print(f"Hardware version ({options.hw_version}) must have 3 components")
        exit()

if options.skip_firmware:
    print("Skipping firmware installation")
else:
    upgrade_firmware()
print("Waiting for CircuitPython disc")

while True:
    path = get_circuitpython_dir(rename=True)
    if path is not None:
        break
    time.sleep(1)

fw_path = os.path.join(path, "firmware")
versions_path = os.path.join(fw_path, "versions")

if hw_version is None:
    print("Skipping setting hardware version")
else:
    set_hw_version(*hw_version)

if options.skip_tests:
    print("Skipping tests")
else:
    run_tests()

if options.skip_code:
    print("Skipping code installation")
else:
    install_code(debug=options.debug, calibration=options.calibration)
