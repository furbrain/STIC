import os

import displayio


def get_bitmaps():
    result = {}
    for p in os.listdir("/images/"):
        fname = "/images/"+p
        stem, suffix = p.split(".")
        if suffix.lower()=="bmp":
            result[stem] = displayio.OnDiskBitmap(fname)
    return result


bitmaps = get_bitmaps()
palette = displayio.Palette(2)
palette[0] = 0xFFFFFF
palette[1] = 0x000000
