"""Render STL files to PNGs so a model can be checked without opening FreeCAD.

Usage (from cad/):
  uv run python render.py NAME part.stl[:dz] [part.stl[:dz] ...]

Each part may be offset along Z by dz mm (for exploded views). Writes
out/renders/NAME_{iso,front,back,top,side}.png.
"""

import sys
from pathlib import Path

import pyvista as pv

OUT = Path(__file__).resolve().parent / "out" / "renders"
COLORS = ["#e8dcc4", "#5a5048", "#c9a26b", "#8aa0a8"]
VIEWS = {
    "iso": ((1, -1.6, 1.4), (0, 0, 1)),
    "front": ((0, 0, 1), (0, 1, 0)),
    "back": ((0, 0, -1), (0, 1, 0)),
    "top": ((0, 1, 0), (0, 0, 1)),
    "side": ((1, 0, 0), (0, 1, 0)),
    "under": ((0.8, -1.2, -1.4), (0, 0, 1)),
}


def main(name, specs):
    OUT.mkdir(parents=True, exist_ok=True)
    meshes = []
    for i, spec in enumerate(specs):
        path, _, dz = spec.partition(":")
        mesh = pv.read(path)
        if dz:
            mesh = mesh.translate((0, 0, float(dz)))
        meshes.append((mesh, COLORS[i % len(COLORS)]))

    for view, (direction, up) in VIEWS.items():
        pl = pv.Plotter(off_screen=True, window_size=(1400, 1000))
        pl.set_background("#f4f2ee")
        for mesh, color in meshes:
            pl.add_mesh(mesh, color=color, smooth_shading=False,
                        show_edges=False, specular=0.2)
            pl.add_mesh(mesh.extract_feature_edges(30), color="#222222", line_width=1)
        pl.enable_lightkit()
        center = meshes[0][0].center
        pl.camera.focal_point = center
        pl.camera.position = [c + 300 * d for c, d in zip(center, direction)]
        pl.camera.up = up
        pl.reset_camera()
        pl.camera.zoom(1.15)
        out = OUT / f"{name}_{view}.png"
        pl.screenshot(str(out))
        pl.close()
        print(out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
