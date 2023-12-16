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
------------

Press **A** to take a reading. You will get an error if the device is not already :ref:`calibrated <Sensors>`. You can
choose either a short press (the reading will be taken just after the button is released), or a long press (the reading
will be taken once the button has been pressed for a second or so). Play with each mode and see what suits you.
Once the reading has been taken you will see three readings: compass, clino and distance.

Press **B** to see previous readings. You can tell which reading you are looking at by the small number at the right
hand side of the display.

.. |bt_on| image:: bt_on.png

.. |bt_off| image:: bt_off.png


There is also a battery level indicator on the bottom right of the screen. The top right is a bluetooth indicator:
|bt_on| if connected, |bt_off| if not. If you lose bluetooth connection, the device will store up to 20 readings and
will send them automatically when bluetooth connection is restored.

Menu
----

To navigate through the menu, press **A** to select an item and **B** to move on to the next item
Description of the various options here

Battery Life
------------

Testing in ideal circumstances (room temperature, about 4m range to a white wall, 10 seconds between successive
readings, display on):
  * ~4500 readings taken
  * 14 hours run time

Factors affecting battery consumption:
  * Temperature - poorer capacity with colder temperatures
  * Range  - increased battery usage with longer legs
  * Cave colouration:  increased battery usage with darker targets

Charging time - about 2-3 hours with a 500mA charger

Calibration
+++++++++++

Sensors
*******

You will need to calibrate the device the first time you use it, and any time that you move to an area where the
magnetic field has a substantially different strength or dip.

Once you enter the calibration routine you will ideally need to take 24 readings. Press **A** to take each reading,
and press **B** to finish. If you wish to cancel calibration, double-click **A**. I normally suggest 8 in random
directions, then a series of 8 readings between two points, rotating the device 45° along its axis between each shot.
You then need a further 8 readings between another 2 points, ideally about 90° from the first set. Don't
worry if you don't get these numbers exactly right, the algorithm will identify which readings are in the same direction
and adapt accordingly.

Laser
*****

You shouldn't need to calibrate the laser, unless you want to start measuring from the front of the device
or if you have replaced the end cap with something else.

To calibrate the laser, place on object exactly one meter from the point on the device you want to measure from. Start
the laser calibration routine and it will update the distance readings.

Info
++++

Raw Data
********

This shows the live raw output of the sensors, converted to ms\ :sup:`-2` and µT

Tidy Data
*********

This shows the live calibrated output of the sensors, again converted to ms\ :sup:`-2` and µT

Orientation
***********

This shows the live compass and clino readings along with the roll of the device and the current
magnetic dip

Device
******

This shows the name of the device as visible to bluetooth, and various version numbers

Settings
++++++++

Timeout
*******

This is how long the device will wait from the last button click before turning off

Units
*****

Choose between metric and imperial (decimal feet) units

Angles
******

Choose between degrees and grads for the angular measurements

Anomaly Detection
*****************

The device makes a note of the magnetic dip and field strength during calibration. If these are significantly
different when taking a reading, this would suggest that there are stray magnetic fields present. This option
lets you choose between **strict** detection which will pick up most bad readings, at the risk of getting a warning
when there is nothing wrong. There is also a **relaxed** mode, and it can also be turned **off**.

Bluetooth
+++++++++

Disconnect
**********

Disconnect from the current bluetooth device

Forget Pairings
***************

If you are having difficulties connecting, it may be worth selecting this option which will clear all the recorded
connections within the device.

Hacking
-------

This is an open source project - feel free to make your own devices, make adaptations and improvements.
All the hardware and software designs can be found on `GitHub <https://github.com/furbrain/STIC>`_.

Software
++++++++

This device uses `CircuitPython <https://circuitpython.org/>`_. All the code to run it is available on the device
itself - just plug it in to a laptop and you'll see a USB drive appear. You can go in and change the code as you see
fit. The version of CircuitPython that comes with the SAP6 has several additional libraries built in to it:

* `mag_cal <https://github.com/furbrain/CircuitPython_mag_cal>`_: This contains all the maths needed for calibration
* `rm3100 <https://github.com/furbrain/CircuitPython_RM3100>`_: This is a device driver for the RM3100 magnetometer
* `laser_egismos <https://github.com/furbrain/CircuitPython_laser_egismos>`_: This is a device driver for the
  laser module 2 by `Egismos <https://www.egismos.com/laser-distance-module-2M>`_.
* `caveble <https://github.com/furbrain/CircuitPython_CaveBLE>`_: This module is a cave survey specific module to talk
  to cave surveying apps such as SexyTopo.

File layout
***********

In the top level director of the USB Drive, you may see:

``firmware``
  This directory holds all the application code

``fonts``
  This directory holds the fonts used by the device

``images``
  This directory holds the images used

``boot.py``
  This code is run on startup, before all the other python code runs

``code.py``
  This code simply calls ``run`` in ``firmware/main.py``

``config.json``
  This holds all the calibration and settings data for the device

``manual.pdf``
  This documentation

``calibration_data.json``
  This is a record of all the shots you took last time you attempted to calibrate

``error.log``
  If the device crashes or encounters an error, you will get some debugging info in here

``DEBUG``
  If this file is present, then the device will be in debug mode. You won't see the normal battery charging
  screen, but you can double click and start the main device running. You also get a serial connection on
  ``/dev/ttyACM0`` or ``/dev/ttyUSB0`` on  linux or ``COM1`` on windows

Updating Circuitpython
**********************

FIXME show

Hardware
++++++++

You can build your own SAP6! This part is a work in progress

PCB
***

Get the gerbers from **FIXME**, and either make or get someone to make the PCB for you. The traces are pretty
chunky so you can mill or etch the board yourself

Components
**********

See the BOM for the list of components and where to get them

Solder them on to the board - they are all fairly chunky so you don't need to be a whizz at soldering

Plastic parts
*************

You will need to 3d print the following STLs:
  * ``shell.stl``:  print with largest opening downwards
  * ``cap.stl``: you may need to print this with the pointy end down, in which case use the ``cap_with_vanes.stl`` file.
  * ``shim.stl``: this inserts under the button pcb and holds it in place
  * ``bezel.stl``: glue this in place over the acrylic window -silicone sealant or adhesive is suitable here
  * ``mount.stl``: this holds the laser module and main pcb

``mount.stl`` and ``shell.stl`` will need 1 and 4 brass screwthreads respectively - these can be inserted by pressing on
them with a soldering iron. You can find suitable inserts on `RS <https://uk.rs-online.com/web/p/threaded-inserts/0278534>`_

Rubber parts
************

``boot.stl`` needs to be printed with as soft a TPU as you can get away with. Coat upper and lower surfaces with grease
before assembly.

Acrylic parts
*************

Ideally you should laser cut the following DXFs from 3mm clear acrylic. However the designs are fairly
simple so you may well be able to cut these by hand

Gaskets
*******

You can use 1mm silicone sheet or EVA foam for these pieces. Note that EVA foam works well but will need to be replaced
after each use as it permanently deforms once compressed. Ideally coat gaskets with silicone grease. You can probably
get away with no gaskets if you use plenty of grease