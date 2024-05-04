from collections import namedtuple

Layout = namedtuple("Layout", ("mag_axes",
                               "grav_axes",
                               "laser_offset",
                               "pins",
                               "hardware"))

layout_6_1 = Layout(mag_axes="+X+Y-Z",
                    grav_axes="-Y-X+Z",
                    laser_offset=0.157,
                    pins="PinsA",
                    hardware="hardware_v1")

layout_6_2 = Layout(mag_axes="+X+Y-Z",
                    grav_axes="-Y-X+Z",
                    laser_offset=0.153,
                    pins="PinsA",
                    hardware="hardware_v1")
