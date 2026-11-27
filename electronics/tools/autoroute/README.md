# Autorouting the cartridge PCB with Freerouting

Used on 2026-11-25 to produce `cartridge_pcb_autoroute.kicad_pcb`, which Kyle
finished by hand and which became `electronics/cartridge_pcb/cartridge_pcb.kicad_pcb`
on 2026-11-26 (see `docs/decisions.md`). Freerouting alone left every ground and power pin
unconnected (it found no room for the plane vias), so the stubs to the planes
are placed first, by script, and locked; Freerouting then routes the signals.

Tools: Freerouting 2.5.0 (`freerouting-2.5.0.jar` from the GitHub releases,
checked against its published SHA-256), run with Homebrew's `openjdk` (the jar
needs Java 25 or newer). The native `freerouting-cli` build crashed on start.

```bash
KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
JAR=~/.local/share/freerouting-2.5.0-jar/freerouting-2.5.0.jar
T=electronics/tools/autoroute
# 1. A trackless copy of the board whose .kicad_pro has the net classes
#    (GND 0.3, P5V 0.3, P3V3 0.25 mm) and the via size; inner layers set to "power".
# 2. Stubs and vias to the planes, then export to Specctra DSN:
$KPY $T/dogbones.py board.kicad_pcb stubs.kicad_pcb board.dsn 0.45 0.2
# 3. Keep Freerouting's copper 0.3 mm off the edge (it otherwise comes to ~0.26):
python3 $T/shrink_boundary.py board.dsn board_e.dsn 150
# 4. Route (deterministic; a different boundary margin gives a different result):
/opt/homebrew/opt/openjdk/bin/java -Djava.awt.headless=true -jar $JAR \
    -de board_e.dsn -do board.ses --router.autorouter.max_passes=200
# 5. Bring the routes back into the stubbed board, then run DRC:
$KPY $T/import_ses.py stubs.kicad_pcb board.ses routed.kicad_pcb
```

Results on the cartridge (unconnected items after import, KiCad DRC):

| Vias | Best of 8 boundary margins |
|---|---|
| 0.6 / 0.3 mm | 11 |
| 0.45 / 0.2 mm | 5 (margin 150, after removing 3 stray vias) |
