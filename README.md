# LaserTrack

A 3D-printed TV set-top box that takes NFC cartridges. Personal project.

- `cad/` — parametric models in Python (build123d)
- `firmware/` — microcontroller code
- `electronics/` — wiring and pin maps
- `docs/` — decisions and notes
- `vendor/` — third-party part models and datasheets

## Building a model

```bash
cd cad
uv sync
uv run python models/tolerance_gauge.py
```

STEP files land in `cad/out/`. Open them in FreeCAD to inspect, or in Bambu
Studio to slice.
