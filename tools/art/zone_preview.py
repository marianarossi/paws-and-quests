from __future__ import annotations

import json
import os
import sys

from PIL import Image

from vec import ASSETS, ROOT, rgba

sys.path.insert(0, os.path.join(ROOT, "tools", "levels"))
import make_zones

W, H, T, MASKS = 640, 360, 16, 19
DEPTH_ALPHA = (0.0, 0.0, 0.3, 0.52, 0.68)


def _solid(rows: list[str], x: int, y: int) -> bool:
    x = max(0, min(len(rows[0]) - 1, x))
    y = max(0, min(len(rows) - 1, y))
    return rows[y][x] == "#"


def terrain(rows: list[str], atlas: Image.Image) -> Image.Image:
    w, h = len(rows[0]), len(rows)
    out = Image.new("RGBA", (w * T + T, h * T + T), (0, 0, 0, 0))
    for j in range(h + 1):
        for i in range(w + 1):
            mask = sum(1 << c for c in range(4) if _solid(rows, i - 1 + (c & 1), j - 1 + (c >> 1)))
            if not mask:
                continue
            if mask == 15:
                mask += (0 if _solid(rows, i - 1, j - 2) else 1) + (0 if _solid(rows, i, j - 2) else 2)
            tx, ty = i % 16, j % 16
            cx, cy = (tx % 4) * MASKS + mask, (tx // 4) * 16 + ty
            tile = atlas.crop((cx * T, cy * T, cx * T + T, cy * T + T))
            out.alpha_composite(tile, (i * T, j * T))
    return out.crop((T // 2, T // 2, w * T + T // 2, h * T + T // 2))


def depth_shade(rows: list[str], color: str, strength: float) -> Image.Image:
    w, h = len(rows[0]), len(rows)
    depth = [[0 if rows[y][x] != "#" else 99 for x in range(w)] for y in range(h)]
    for _ in range(5):
        for y in range(h):
            for x in range(w):
                if depth[y][x]:
                    near = min(depth[max(0, y - 1)][x], depth[min(h - 1, y + 1)][x], depth[y][max(0, x - 1)], depth[y][min(w - 1, x + 1)])
                    depth[y][x] = min(depth[y][x], near + 1)
    alpha = Image.new("L", (w, h))
    alpha.putdata([int(255 * strength * DEPTH_ALPHA[min(d, 4)]) for row in depth for d in row])
    shade = Image.new("RGBA", (w * T, h * T), rgba(color))
    shade.putalpha(alpha.resize((w * T, h * T), Image.BILINEAR))
    return shade


def render(zone: str) -> Image.Image:
    data = json.load(open(os.path.join(ASSETS, "themes", zone + ".json"), encoding="utf-8"))
    base = os.path.join(ASSETS, "backgrounds")
    img = Image.open(os.path.join(base, data["sky"])).convert("RGBA").crop((0, 0, W, H))
    for layer in data["layers"]:
        art = Image.open(os.path.join(base, layer["texture"])).convert("RGBA")
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        canvas.alpha_composite(art.crop((0, 0, min(W, art.width), min(H, art.height))), (0, int(layer.get("y", 0))))
        img.alpha_composite(canvas)
    rows = make_zones.showcase()
    world = Image.new("RGBA", (len(rows[0]) * T, len(rows) * T), (0, 0, 0, 0))
    world.alpha_composite(terrain(rows, Image.open(os.path.join(ASSETS, "tiles", data["terrain"])).convert("RGBA")))
    world.alpha_composite(depth_shade(rows, data.get("depth_color", "#0d0a1c"), float(data.get("depth_strength", 1.0))))
    top, deep = data.get("water_top", "#5cd6d180"), data.get("water_deep", "#1a477abd")
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == "W":
                first = rows[y - 1][x] != "W"
                c = top if first else deep
                tile = Image.new("RGBA", (T, T), (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16), int(c[7:9] or "ff", 16)))
                world.alpha_composite(tile, (x * T, y * T))
                if first:
                    world.alpha_composite(Image.new("RGBA", (T, 1), rgba(data.get("water_foam", "#ffffffff")[:7])), (x * T, y * T))
            elif ch == "=":
                world.alpha_composite(Image.new("RGBA", (T, 5), rgba("#8a5a41")), (x * T, y * T))
    img.alpha_composite(world.crop((0, world.height - H, W, world.height)))
    return img


def main() -> None:
    out, zones = sys.argv[1], sys.argv[2:]
    cols = 2 if len(zones) > 1 else 1
    sheet = Image.new("RGB", (W * cols, H * ((len(zones) + cols - 1) // cols)))
    for k, zone in enumerate(zones):
        sheet.paste(render(zone).convert("RGB"), ((k % cols) * W, (k // cols) * H))
    sheet.save(out)
    print(out, sheet.size)


if __name__ == "__main__":
    main()
