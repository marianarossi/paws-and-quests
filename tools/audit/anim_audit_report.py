import csv
import sys
from collections import Counter

rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))
for r in rows:
    for k in ("tick", "frame", "floor", "facing", "wall", "move_x"):
        r[k] = int(r[k])
    for k in ("t", "vx", "vy", "sx", "sy", "x", "y"):
        r[k] = float(r[k])
TICK = 1 / 120.0


def runs(key):
    out, start = [], 0
    for i in range(1, len(rows) + 1):
        if i == len(rows) or rows[i][key] != rows[start][key]:
            out.append((rows[start][key], start, i - start))
            start = i
    return out


print("passos:", len(rows), " tempo: %.1f s" % rows[-1]["t"])
state_runs = runs("state")
print("\nestados visitados:", dict(Counter(s for s, _, _ in state_runs)))

print("\n1) estados que duram 3 passos ou menos (piscadelas):")
blips = [(s, a, n) for (s, a, n) in state_runs if n <= 3]
for i, (s, a, n) in enumerate(state_runs):
    if n <= 3 and 0 < i < len(state_runs) - 1:
        print("   t=%.2f  %s -> %s (%d passos) -> %s   vy=%.0f floor=%d" % (
            rows[a]["t"], state_runs[i - 1][0], s, n, state_runs[i + 1][0], rows[a]["vy"], rows[a]["floor"]))
print("   total:", len(blips))

print("\n2) animacao 'run' com o personagem parado (|vx| < 5):")
count, longest, cur = 0, 0, 0
for r in rows:
    if r["anim"] == "run" and abs(r["vx"]) < 5:
        count += 1
        cur += 1
        longest = max(longest, cur)
    else:
        cur = 0
print("   %d passos (%.2f s), maior sequencia %.2f s" % (count, count * TICK, longest * TICK))

print("\n3) animacao 'fall' enquanto ainda sobe (vy < -20):")
count = sum(1 for r in rows if r["anim"] == "fall" and r["vy"] < -20)
print("   %d passos (%.2f s)" % (count, count * TICK))

print("\n4) animacao 'jump' ja a descer (vy > 20):")
count = sum(1 for r in rows if r["anim"] == "jump" and r["vy"] > 20)
print("   %d passos (%.2f s)" % (count, count * TICK))

print("\n5) dash: direcoes usadas com a mesma pose:")
dash_dirs = Counter()
for s, a, n in state_runs:
    if s == "Dash":
        mid = rows[min(a + n - 1, len(rows) - 1)]
        dash_dirs[("%+d" % (0 if abs(mid["vx"]) < 1 else (1 if mid["vx"] > 0 else -1)), "%+d" % (0 if abs(mid["vy"]) < 1 else (1 if mid["vy"] > 0 else -1)))] += 1
print("   ", dict(dash_dirs), " animacoes vistas no dash:", set(r["anim"] for r in rows if r["state"] == "Dash"))

print("\n6) esticar/achatar por escala (pixels de tamanhos diferentes no ecra):")
off = [r for r in rows if abs(r["sx"] - 1) > 0.02 or abs(r["sy"] - 1) > 0.02]
print("   %d passos (%.1f%% do tempo) com escala diferente de 1; extremos x %.2f..%.2f, y %.2f..%.2f" % (
    len(off), 100 * len(off) / len(rows), min(r["sx"] for r in rows), max(r["sx"] for r in rows),
    min(r["sy"] for r in rows), max(r["sy"] for r in rows)))

print("\n7) trocas de animacao muito proximas (menos de 0,1 s entre duas trocas):")
anim_runs = runs("anim")
quick = [(s, a, n) for (s, a, n) in anim_runs if n < 12]
for i, (s, a, n) in enumerate(anim_runs):
    if n < 12 and 0 < i < len(anim_runs) - 1:
        print("   t=%.2f  %s -> %s (%d passos) -> %s" % (rows[a]["t"], anim_runs[i - 1][0], s, n, anim_runs[i + 1][0]))
print("   total:", len(quick), "de", len(anim_runs), "trocas")

print("\n8) parede: lado para onde olha a deslizar e animacao encostado a parede no chao:")
ws = [r for r in rows if r["state"] == "WallSlide"]
print("   passos em WallSlide: %d; olha para a parede em %d" % (len(ws), sum(1 for r in ws if r["facing"] == r["wall"])))
