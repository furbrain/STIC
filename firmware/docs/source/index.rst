.. SAP6 documentation master file, created by
   sphinx-quickstart on Wed Jul 26 18:53:57 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

SAP6 Cave Surveying Device
==========================

.. toctree::
   :maxdepth: 2
   :caption: Contents:


Basic Usage
-----------

* To turn on or off: Press **A** twice in quick succession.
* To turn on in ``menu`` mode: Press **A** twice while holding down **B**
* To switch between ``menu`` and ``measure`` modes: Hold down **B**
* To select a menu item: Press **A**
* To move to the next menu item: Press **B**

Measure Mode
++++++++++++

Press **A** to take a reading. You will get an error if the device is not already :ref:`calibrated <Sensors>`. You can
choose either a short press (the reading will be taken just after the button is released), or a long press (the reading
will be taken once the button has been pressed for a second or so). Play with each mode and see what suits you.
Once the reading has been taken you will see three readings: compass, clino and distance.

Press **B** to see previous readings. You can tell which reading you are looking at by the small number at the right
hand side of the display.

.. |bt_on| image:: bt_on.png

.. |bt_off| image:: bt_off.png


There is also a battery level indicator on the bottom right of the screen. The top right is a bluetooth indicator:
|bt_on| if connected, |bt_off| if not.

Menu Mode
+++++++++

Description of the various options here

Bluetooth Connection
--------------------

Doing bluetooth stuff


Calibration
-----------

How to calibrate it

Sensors
+++++++


Calibration routine


Laser
+++++

You shouldn't need to calibrate the laser, unless you want to start measuring from the front of the device
or if you have replaced the end cap with


Anomaly Detection
-----------------

A bit here

Hacking
-------

This is an open source project - feel free to make your own devices, make adaptations and improvements.
All the hardware and software designs can be found on `GitHub <https://github.com/furbrain/STIC>`_.

Software
++++++++

This device uses `CircuitPython <https://circuitpython.org/>`_. All the code to run it is available on the device
itself - just plug it in to a laptop and you'll see a USB drive appear. You can go in and change the code as you see
fit. The version of CircuitPython that comes with the SAP6 has several additionaly libraries built in to it:

* `mag_cal <https://github.com/furbrain/CircuitPython_mag_cal>`_: This contains all the maths needed for calibration
* `rm3100 <https://github.com/furbrain/CircuitPython_RM3100>`_: This is a device driver for the RM3100 magnetometer
* `laser_egismos <https://github.com/furbrain/CircuitPython_laser_egismos>`_: This is a device driver for the
  laser module 2 by `Egismos <https://www.egismos.com/laser-distance-module-2M>`_.
* `caveble <https://github.com/furbrain/CircuitPython_CaveBLE>`_: This module is a cave survey specific module to talk
  to cave surveying apps such as SexyTopo.


Hardware
++++++++

and here