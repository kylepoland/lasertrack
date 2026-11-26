import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
print("import", pcbnew.ImportSpecctraSES(b, sys.argv[2]))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
v = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
print("tracks", len(b.GetTracks()) - len(v), "vias", len(v))
pcbnew.SaveBoard(sys.argv[3], b)
