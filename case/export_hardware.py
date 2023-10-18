import os
import TechDraw
import Mesh
FreeCAD.openDocument("bigboy.FCStd")
doc = App.getDocument("bigboy")
stl_parts = ("shim", "cap", "mount", "shell")
os.makedirs("build/abs/",exist_ok=True)
for part_name in stl_parts:
    print(f"Exporting {part_name}") 
    part = doc.findObjects(Label=f"^{part_name}$")[0]
    Mesh.export([part],f"build/abs/{part_name}.stl")
    
drawings = doc.findObjects("TechDraw::DrawPage")
for drawing in drawings:
    os.makedirs(f"build/{drawing.Label}/", exist_ok=True)
    for view in drawing.OutList:
        if view.TypeId == 'TechDraw::DrawViewPart':
            print(f"Exporting {view.Source[0].Label}") 
            TechDraw.writeDXFView(view,f"build/{drawing.Label}/{view.Source[0].Label}.dxf")
            
FreeCAD.openDocument("button_mould.FCStd")
doc = App.getDocument("button_mould")
os.makedirs("build/tpu/",exist_ok=True)
print(f"Exporting Boot") 
parts = doc.findObjects(Label="^Boot$")
Mesh.export(parts,f"build/tpu/Boot.stl")
exit(0)
