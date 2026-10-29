import json
import os
import sys

from PIL import Image

meta = json.load(open(sys.argv[1], encoding="utf-8"))
folder = os.path.dirname(sys.argv[1])
sheet = Image.open(os.path.join(folder, meta["image"])).convert("RGBA")
for extra in sys.argv[2:]:
    sheet.alpha_composite(Image.open(extra).convert("RGBA"))
FW, FH = meta["frame_w"], meta["frame_h"]
GROUNDED = {"idle", "run", "push", "land", "sit", "crouch", "sit_roast", "sit_think", "sleep"}
FLOATING = {"sleep", "sit_think"}
problems = 0
total = 0


def components(mask: set) -> list[int]:
    left, sizes = set(mask), []
    while left:
        stack = [left.pop()]
        size = 0
        while stack:
            x, y = stack.pop()
            size += 1
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    n = (x + dx, y + dy)
                    if n in left:
                        left.discard(n)
                        stack.append(n)
        sizes.append(size)
    return sorted(sizes, reverse=True)


for name, anim in meta["animations"].items():
    previous = None
    for i in range(anim["frames"]):
        total += 1
        cell = sheet.crop((i * FW, anim["row"] * FH, (i + 1) * FW, (anim["row"] + 1) * FH))
        px = cell.load()
        mask = {(x, y) for y in range(FH) for x in range(FW) if px[x, y][3] > 0}
        notes = []
        if not mask:
            notes.append("frame vazio")
        else:
            if any(x in (0, FW - 1) or y == 0 for x, y in mask):
                notes.append("pixels na borda do frame (cortado)")
            sizes = components(mask)
            if len(sizes) > 1 and name not in FLOATING:
                notes.append("pedacos soltos: %s px" % sizes[1:])
            bottom = max(y for _, y in mask)
            if name in GROUNDED and bottom != FH - 1:
                notes.append("nao toca no chao (ultima linha %d)" % bottom)
            cx = sum(x for x, _ in mask) / len(mask)
            cy = sum(y for _, y in mask) / len(mask)
            if previous and (abs(cx - previous[0]) > 3.0 or abs(cy - previous[1]) > 3.0):
                notes.append("salto da silhueta: %.1f, %.1f px" % (cx - previous[0], cy - previous[1]))
            previous = (cx, cy)
        if notes:
            problems += 1
            print("  %-11s frame %2d: %s" % (name, i, "; ".join(notes)))
print("%d frames conferidos, %d com problemas" % (total, problems))
