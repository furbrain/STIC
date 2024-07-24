import os
import TechDraw
import Mesh
import time
import subprocess

FreeCAD.openDocument("bigboy.FCStd")
doc = App.getDocument("bigboy")
time.sleep(3)
stl_parts = ("shim", "cap", "cap with vanes", "mount", "shell", "bezel")
os.makedirs("build/abs/",exist_ok=True)
for part_name in stl_parts:
    print(f"Exporting {part_name}") 
    part = doc.findObjects(Label=f"^{part_name}$")[0]
    Mesh.export([part],f"build/abs/{part_name}.stl")
    
drawings = doc.findObjects("TechDraw::DrawPage")
drawing_stls = []
for drawing in drawings:
    os.makedirs(f"build/{drawing.Label}/", exist_ok=True)
    for view in drawing.OutList:
        if view.TypeId == 'TechDraw::DrawViewPart':
            print(f"Exporting {view.Source[0].Label}")
            # tech draw does not export DXFs properly from command line - so export as stl and we will post-process with openscad
            #TechDraw.writeDXFView(view,f"build/{drawing.Label}/{view.Source[0].Label}.dxf")
            fname = f"build/{drawing.Label}/{view.Source[0].Label}.stl"
            Mesh.export(view.Source,fname)
            drawing_stls.append(fname)
            
FreeCAD.openDocument("button_mould.FCStd")
doc = App.getDocument("button_mould")
os.makedirs("build/tpu/",exist_ok=True)
print(f"Exporting Boot") 
parts = doc.findObjects(Label="^Boot$")
Mesh.export(parts,f"build/tpu/Boot.stl")
exit(0)
