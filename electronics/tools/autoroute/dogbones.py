"""Place power/ground dogbones (pad -> short track -> via) on a trackless board.

KiCad Python: dogbones.py IN.kicad_pcb OUT.kicad_pcb OUT.dsn [VIA_D VIA_DRILL]
Each GND/+5V/+3V3 pad gets a locked stub and via down to its inner plane
(+5V only left of the In2 split, +3V3 only right of it), then the board is
exported to Specctra DSN for Freerouting. See README.md."""
import sys, math, pcbnew
src, dst = sys.argv[1:3]
b = pcbnew.LoadBoard(src)
MM = pcbnew.FromMM; ToMM = pcbnew.ToMM
CX, CY = 150.0, 100.0
VIA_D = float(sys.argv[4]) if len(sys.argv) > 4 else 0.45
VIA_DR = float(sys.argv[5]) if len(sys.argv) > 5 else 0.2
CLR = 0.15
SPLIT = -6.5
WIDTH = {"/GND": 0.3, "/+5V": 0.3, "/+3V3": 0.25}
HALF_L, HALF_W, EDGE = 40.5, 3.95, 0.3

def region_ok(net, x):
    if net == "/+5V": return x <= SPLIT - 0.25 - VIA_D / 2 - 0.25
    if net == "/+3V3": return x >= SPLIT + 0.25 + VIA_D / 2 + 0.25
    return True

pads = [p for f in b.GetFootprints() for p in f.Pads()]
placed = []   # (net, shape_kind, data): vias as (x, y), tracks as (x0, y0, x1, y1, w)

def circle(x, y, r):
    return pcbnew.SHAPE_CIRCLE(pcbnew.VECTOR2I(MM(CX + x), MM(CY + y)), MM(r))

def seg(x0, y0, x1, y1, w):
    return pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(MM(CX + x0), MM(CY + y0)), pcbnew.VECTOR2I(MM(CX + x1), MM(CY + y1)), MM(w))

def pad_hits(shape, net, layers, allow=None):
    for p in pads:
        if p is allow: continue
        for L in layers:
            if not p.IsOnLayer(L): continue
            same = p.GetNetname() == net
            c = 0 if same else CLR
            if p.GetEffectiveShape(L).Collide(shape, MM(c)):
                if same and allow is not None and p is allow: continue
                return True
    return False

def dist_seg_pt(ax, ay, bx, by, px, py):
    dx, dy = bx - ax, by - ay
    t = 0 if dx == dy == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(ax + t * dx - px, ay + t * dy - py)

def seg_seg(a, b_):
    (x0, y0, x1, y1), (x2, y2, x3, y3) = a, b_
    return min(dist_seg_pt(x0, y0, x1, y1, x2, y2), dist_seg_pt(x0, y0, x1, y1, x3, y3),
               dist_seg_pt(x2, y2, x3, y3, x0, y0), dist_seg_pt(x2, y2, x3, y3, x1, y1))

def clear_of_placed(net, vx, vy, tr, w, layer):
    for pn, kind, d in placed:
        if kind == "via":
            dd = math.hypot(d[0] - vx, d[1] - vy)
            if dd < VIA_DR + 0.25: return False          # hole to hole
            if pn != net and dd < VIA_D + CLR: return False
            if pn != net and dist_seg_pt(*tr, d[0], d[1]) < VIA_D / 2 + w / 2 + CLR: return False
        else:
            (x0, y0, x1, y1, tw, tl) = d
            if pn == net: continue
            if dist_seg_pt(x0, y0, x1, y1, vx, vy) < VIA_D / 2 + tw / 2 + CLR: return False
            if tl == layer and seg_seg(tr, (x0, y0, x1, y1)) < w / 2 + tw / 2 + CLR: return False
    return True

cu = [pcbnew.F_Cu, pcbnew.B_Cu]
done, skipped = 0, []
for p in sorted(pads, key=lambda p: (p.GetNetname(), p.GetPosition().x)):
    net = p.GetNetname()
    if net not in WIDTH: continue
    layer = pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
    px, py = ToMM(p.GetPosition().x) - CX, ToMM(p.GetPosition().y) - CY
    w = WIDTH[net]
    best = None
    for r10 in range(4, 26):
        r = r10 / 10.0
        for k in range(32):
            a = 2 * math.pi * k / 32
            vx, vy = px + r * math.cos(a), py + r * math.sin(a)
            if abs(vx) > HALF_L - EDGE - VIA_D / 2 - 1.0 or abs(vy) > HALF_W - EDGE - VIA_D / 2: continue
            if not region_ok(net, vx): continue
            if pad_hits(circle(vx, vy, VIA_D / 2), net, cu): continue        # via off every pad
            if pad_hits(seg(px, py, vx, vy, w), net, [layer], allow=p): continue
            # the stub must not touch other pads of the same net either (keeps it a clean dogbone)
            if not clear_of_placed(net, vx, vy, (px, py, vx, vy), w, layer): continue
            best = (vx, vy); break
        if best: break
    if not best:
        skipped.append(f"{p.GetParentFootprint().GetReference()}-{p.GetNumber()} {net}")
        continue
    vx, vy = best
    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(MM(CX + vx), MM(CY + vy)))
    v.SetWidth(MM(VIA_D)); v.SetDrill(MM(VIA_DR)); v.SetNet(p.GetNet()); v.SetLocked(True); b.Add(v)
    t = pcbnew.PCB_TRACK(b); t.SetStart(p.GetPosition()); t.SetEnd(v.GetPosition()); t.SetWidth(MM(w))
    t.SetLayer(layer); t.SetNet(p.GetNet()); t.SetLocked(True); b.Add(t)
    placed.append((net, "via", (vx, vy)))
    placed.append((net, "trk", (px, py, vx, vy, w, layer)))
    done += 1
print("dogbones", done, "skipped", len(skipped)); print("\n".join(skipped))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(dst, b)
print("dsn", pcbnew.ExportSpecctraDSN(b, sys.argv[3]))
