from firmware.utils import usb_power_connected

if usb_power_connected():
    import supervisor
    supervisor.runtime.autoreload = False
else:
    # noinspection PyPackageRequirements
    import storage
    storage.remount("/", False)
