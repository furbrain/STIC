#!/usr/bin/bash
kicad-cli sch export python-bom Button/Button.kicad_sch
kicad-cli sch export python-bom PCB/STIC.kicad_sch
python3 xml2csv.py *bom.xml > bom.csv
