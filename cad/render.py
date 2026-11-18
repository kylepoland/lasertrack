"""Render STL files to PNGs so a model can be checked without opening FreeCAD.

Usage (from cad/):
  uv run python render.py NAME part.stl[:dz] [part.stl[:dz] ...]

Each part may be offset along Z by dz mm (for exploded views). Writes
out/renders/NAME_{iso,under,front,back,top,side}.png; the axis views are
orthographic so proportions can be read straight off them.

Optional close-up: --focus X,Y,Z,WIDTH renders NAME_closeup.png, an
orthographic view centred on X,Y,Z and WIDTH mm wide. --view picks the
direction from VIEWS (default "side", looking along -X).
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


def main(name, specs, focus=None, focus_view="side"):
    OUT.mkdir(parents=True, exist_ok=True)
    meshes = []
    for i, spec in enumerate(specs):
        path, _, dz = spec.partition(":")
        mesh = pv.read(path)
        if dz:
            mesh = mesh.translate((0, 0, float(dz)))
        meshes.append((mesh, COLORS[i % len(COLORS)]))

    views = dict(VIEWS)
    if focus:
        views = {"closeup": VIEWS[focus_view]}
    for view, (direction, up) in views.items():
        pl = pv.Plotter(off_screen=True, window_size=(1400, 1000))
        pl.set_background("#f4f2ee")
        for mesh, color in meshes:
            pl.add_mesh(mesh, color=color, smooth_shading=False,
                        show_edges=False, specular=0.2)
            pl.add_mesh(mesh.extract_feature_edges(30), color="#222222", line_width=1)
        pl.enable_lightkit()
        center = focus[:3] if focus else meshes[0][0].center
        pl.camera.focal_point = center
        pl.camera.position = [c + 300 * d for c, d in zip(center, direction)]
        pl.camera.up = up
        if view != "iso" and view != "under":
            pl.enable_parallel_projection()
        if focus:
            pl.camera.parallel_scale = focus[3] * 1000 / 1400 / 2
        else:
            pl.reset_camera()
            pl.camera.zoom(1.15)
        out = OUT / f"{name}_{view}.png"
        pl.screenshot(str(out))
        pl.close()
        print(out)


if __name__ == "__main__":
    args = sys.argv[1:]
    focus = None
    if "--focus" in args:
        i = args.index("--focus")
        focus = [float(v) for v in args[i + 1].split(",")]
        del args[i:i + 2]
    view = "side"
    if "--view" in args:
        i = args.index("--view")
        view = args[i + 1]
        del args[i:i + 2]
    main(args[0], args[1:], focus, view)
