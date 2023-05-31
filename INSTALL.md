Installation
============

To install this firmware onto a SAP6 from scratch:
* install circup
* Press the reset button twice in quick succession while attached to a computer via USB
  You should see a hard drive called `XIAO_SENSE`
* copy `firmware.uf2` to this drive
* after a while the XIAO_SENSE drive should disappear and be replaced by one called `CIRCUITPY`
* from the firmware directory run `circup install -r circup_requirements.txt`
* copy the `fruity_menu` dir to `CIRCUITPY/lib/`
* copy the fonts and images directories to `CIRCUITPY`
* copy all the `.py` files from firmware to `CRICUITPY`
* unplug from the computer and press the reset button
