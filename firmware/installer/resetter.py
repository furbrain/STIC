import time
import microcontroller

print("Preparing to reset into bootloader")
time.sleep(5)
print("Resetting into bootloader")
microcontroller.on_next_reset(microcontroller.RunMode.BOOTLOADER)
microcontroller.reset()
