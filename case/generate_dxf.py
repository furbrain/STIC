#!/bin/env python3
import subprocess
import glob
import os

print("Creating DXFs")
dirs = "[acrylic|Rubber]"
cwd = os.path.dirname(os.path.abspath(__file__))
drawing_stls = glob.glob(f"{cwd}/build/{dirs}*/*.stl")
print("fnames: ", drawing_stls)
for fname in drawing_stls:
    if "Window" in fname:
        rotation = ""
    else:
        rotation = "rotate(a=[90,0,0])"
    command = f'projection() {rotation} import("{fname}");'
    output = fname.replace("stl","dxf")
    subprocess.run(["openscad","/dev/null","-D",command,"-o",output])
       
