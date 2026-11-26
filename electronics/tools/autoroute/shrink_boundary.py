import re, sys
src, dst, d = sys.argv[1], sys.argv[2], float(sys.argv[3])
s = open(src).read()
i = s.index("(boundary"); j = s.index(")", s.index("(path", i))
head = s[i:j]; p = head.index("pcb 0") + len("pcb 0")
nums = list(map(float, re.match(r"[\s\d\.\-]+", head[p:]).group(0).split()))
pts = []
for k in range(0, len(nums), 2):
    x, y = nums[k], nums[k + 1]
    pts.append(f"{x + (-d if x > 150000 else d):g} {y + (d if y < -100000 else -d):g}")
open(dst, "w").write(s[:i] + head[:p] + "  " + "  ".join(pts) + "\n" + s[j:])
