#!/usr/bin/bash
mkdir -p gerbers/Button gerbers/PCB

# make Button gerbers
kicad-cli pcb export drill -o gerbers/Button/ Button/Button.kicad_pcb
kicad-cli pcb export gerbers --no-x2 --subtract-soldermask -o gerbers/Button/ Button/Button.kicad_pcb

# make main PCB gerbers
kicad-cli pcb export drill -o gerbers/PCB/ PCB/STIC.kicad_pcb
kicad-cli pcb export gerbers --no-x2 --subtract-soldermask -o gerbers/PCB/ PCB/STIC.kicad_pcb
