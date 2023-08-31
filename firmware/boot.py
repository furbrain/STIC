from utils import usb_power_connected
if not usb_power_connected():
    import storage
    storage.remount("/", False)
