from utils import usb_power_connected
if not usb_power_connected():
    # noinspection PyPackageRequirements
    import storage
    storage.remount("/", False)
