from collections import namedtuple

Layout = namedtuple("Layout", ("mag_axes",
                               "grav_axes",
                               "laser_offset",
                               "pins",
                               "hardware"))

layout_1 = Layout(mag_axes="+X+Y-Z",
                  grav_axes="-Y-X+Z",
                  laser_offset=0.157,
                  pins="PinsA",
                  hardware="hardware_v1")
