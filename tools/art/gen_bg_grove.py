from __future__ import annotations

import math
import os
import sys

from PIL import Image

import gen_bg_ember as kit
from gen_bg_ember import H, P, W, gradient, lerp, put, ridge, scatter, stand, streak
from vec import DOCS_PREVIEW, hash01, rgba, save

ZONE = "twilight_grove"
SKY = [(0, "#0c0f2c"), (50, "#141a44"), (100, "#20265c"), (146, "#343672"), (184, "#544482"), (214, "#84547f"),
       (238, "#b86c7c"), (258, "#dc9278"), (H, "#eeb488")]
MOON = (128, 58, 15)
NEAR_EXTRA = 250
NEAR_SCALE_Y = 0.3


class Sheet:

    def __init__(self, img: Image.Image) -> None:
        self.img = img

    def save(self, name: str) -> str:
        save(self.img, "backgrounds", name + ".png")
        return name + ".png"


def full_moon(px, mx: int, my: int, r: int) -> None:
    base, lit, limb, mare, mare_d, rim = (rgba(c) for c in ("#f6ecd2", "#fffbea", "#e2d4c6", "#d6c8d6", "#c2b4d0", "#ffffff"))
    seas = [(-0.34, -0.3, 0.33), (0.2, -0.42, 0.2), (0.32, 0.1, 0.3), (-0.16, 0.38, 0.24), (-0.58, 0.12, 0.15), (0.08, -0.08, 0.13)]
    craters = [(0.52, -0.5, 0.1), (-0.5, -0.6, 0.07), (0.06, 0.66, 0.09), (0.64, 0.44, 0.07), (-0.66, 0.42, 0.06)]
    for y in range(my - r, my + r + 1):
        for x in range(mx - r, mx + r + 1):
            d = math.hypot(x - mx, y - my)
            if d > r + 0.3:
                continue
            u, v = (x - mx) / r, (y - my) / r
            side = math.hypot(u + 0.2, v + 0.2)
            c = limb if side > 1.02 else lit if side < 0.6 else base
            for sx, sy, sr in seas:
                w = math.hypot(u - sx, v - sy) + (hash01(x // 2, y // 2, 5) - 0.5) * 0.14
                if w < sr:
                    c = mare_d if w < sr * 0.5 and sr > 0.22 else mare
            for cx, cy, cr in craters:
                w = math.hypot(u - cx, v - cy)
                if w < cr:
                    c = mare_d
                elif w < cr + 1.3 / r:
                    c = lit if (u - cx) + (v - cy) > 0 else mare
            if d > r - 1.2:
                c = rim if u + v < 0.1 else limb
            px[x % W, y] = c


def sky() -> Image.Image:
    img = Image.new("RGBA", (W, H))
    px = img.load()
    mx, my, r = MOON
    halo = rgba("#b8b4f0")
    for y in range(H):
        row = gradient(SKY, y)
        for x in range(W):
            d = math.hypot(x - mx, y - my) / 120.0
            px[x, y] = lerp(row, halo, (1.0 - d) ** 2.6 * 0.42) if d < 1.0 else row
    for i in range(150):
        x, y = int(hash01(i, 1, 72) * W), int(hash01(i, 2, 72) ** 1.3 * 170)
        star = rgba("#ffffff" if hash01(i, 3, 72) < 0.25 else "#b8c0ff" if hash01(i, 4, 72) < 0.6 else "#ffe9b0")
        px[x, y] = lerp(star, px[x, y], (y / 170.0) ** 2)
        if hash01(i, 5, 72) < 0.07 and y < 120:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                px[(x + dx) % W, max(0, y + dy)] = lerp(star, px[(x + dx) % W, max(0, y + dy)], 0.6)
    full_moon(px, mx, my, r)
    high = P("#232a60", "#343a78", "#5a5a9c", "#8a88c8")
    low = P("#7a4c7e", "#b0647e", "#e89878", "#ffd0a0")
    for i, (x, y, length, thick, tones) in enumerate([(420, 44, 180, 7, high), (250, 96, 220, 9, high), (560, 128, 150, 6, high),
                                                       (90, 160, 200, 8, high), (360, 196, 240, 8, low), (120, 222, 190, 6, low),
                                                       (520, 232, 230, 6, low), (300, 246, 180, 4, low), (40, 250, 120, 3, low)]):
        streak(px, x, y, length, thick, 500 + i, tones)
    return img


def hills() -> Image.Image:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = img.load()
    haze = rgba("#c07888")
    top, owner = ridge(41, 5, 226, 56)
    lit, shade, rim = rgba("#5a4a8a"), rgba("#4a3f7e"), rgba("#9a80b8")
    for x in range(W):
        y0 = int(top[x])
        for y in range(y0, H):
            x2 = int(x + ((y - y0) // 5 % 2) * 3 + (y - y0) * 0.45) % W
            dark = (owner[x2] - x2) % W < W // 2
            c = rim if (y == y0 and not dark) else shade if dark else lit
            px[x, y] = lerp(c, haze, (y - 160) / 170.0)
    return img


def rays(seed: int, sources: list, color: str, strength: int) -> Image.Image:
    height = kit.H
    img = Image.new("RGBA", (W, height), (0, 0, 0, 0))
    px = img.load()
    c = rgba(color)
    acc = [[0] * W for _ in range(height)]
    for i, (x0, y0, reach) in enumerate(sources):
        width = 12 + hash01(i, 2, seed) * 30
        for k in range(int(reach)):
            y = int(y0) + k
            if not 0 <= y < height:
                continue
            a = strength * min(1.0, k / 30.0) * (1.0 - k / reach) ** 0.8 * (0.6 + 0.4 * hash01(i, 4, seed))
            a = int(a / 6) * 6
            if a <= 0:
                continue
            left = x0 - k * 0.42
            for x in range(int(left), int(left + width * (1.0 + k / 500.0))):
                acc[y][x % W] = min(84, acc[y][x % W] + a)
    for y in range(height):
        for x in range(W):
            if acc[y][x]:
                px[x, y] = (c[0], c[1], c[2], acc[y][x])
    return img


def under_crowns(trees: list, base: int, seed: int, per_tree: int = 1) -> list:
    out = []
    for i, (x, h, crown, _spread) in enumerate(trees):
        bottom = base - h * (1.0 - crown)
        for k in range(per_tree):
            if hash01(i, k, seed) < 0.8:
                y0 = bottom - 30 - hash01(i, k + 5, seed) * 40
                out.append((x + (k - (per_tree - 1) / 2) * 44 + (hash01(i, k + 9, seed) - 0.3) * 30, y0, base - y0 + 16))
    return out


def mist(seed: int, y0: int, y1: int, count: int, colors: tuple, alpha: int) -> Image.Image:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = img.load()
    for i in range(count):
        cx, cy = hash01(i, 1, seed) * W, y0 + hash01(i, 2, seed) * (y1 - y0)
        length, thick = 130 + hash01(i, 3, seed) * 220, 4 + hash01(i, 4, seed) * 9
        c = rgba(colors[i % len(colors)])
        for x in range(int(cx - length / 2), int(cx + length / 2)):
            u = (x - cx) / (length / 2)
            half = thick * (1.0 - u * u) * (0.75 + 0.25 * math.sin(x * 0.07 + i))
            for y in range(int(cy - half), int(cy + half) + 1):
                if 0 <= y < H:
                    v = min(1.0, abs(y - cy) / max(1.0, half))
                    a = int(alpha * (1.0 - v) ** 0.7 * (1.0 - u * u) / 8) * 8
                    old = px[x % W, y]
                    if a > old[3]:
                        px[x % W, y] = (c[0], c[1], c[2], a)
    return img


def tall(extra: int, draw):
    kit.H = H + extra
    try:
        return draw()
    finally:
        kit.H = H


def vary(trees: list, seed: int, crown: tuple = (0.6, 0.88), spread: tuple = (0.8, 1.18)) -> list:
    return [(x, h, crown[0] + hash01(i, 1, seed) * (crown[1] - crown[0]), spread[0] + hash01(i, 2, seed) * (spread[1] - spread[0]))
            for i, (x, h) in enumerate(trees)]


def boulder(px, cx: int, base: int, w: int, h: int, seed: int, pal: tuple) -> None:
    body, dark, light, moss = pal
    pts = [(-0.5, 0.0), (-0.36 + 0.1 * hash01(seed, 1), 0.62 + 0.3 * hash01(seed, 2)), (-0.05 + 0.2 * hash01(seed, 3), 1.0),
           (0.3 + 0.1 * hash01(seed, 4), 0.7 + 0.25 * hash01(seed, 5)), (0.5, 0.0)]
    crack = int((hash01(seed, 6) - 0.5) * w * 0.4)
    for x in range(-w // 2, w // 2 + 1):
        u = x / w
        top = 0.0
        for (ua, va), (ub, vb) in zip(pts, pts[1:]):
            if ua <= u <= ub:
                top = va + (vb - va) * (u - ua) / (ub - ua)
        hh = int(h * top + hash01(x // 3, seed, 7) * 1.5)
        for d in range(hh):
            y = base - hh + d
            if d < 2 and moss and hash01(x // 2, seed, 8) < 0.55:
                c = moss
            elif d < 2 + h * 0.14 and u > -0.3:
                c = light
            elif u < -0.22 - d * 0.004 or d > hh - 3:
                c = dark
            elif abs(x - crack - d // 3) < 1 and d > 3 and d < hh * 0.7:
                c = dark
            else:
                c = body if hash01(x // 2, y // 2, seed + 9) > 0.12 else dark
            put(px, cx + x, y, c)


def rocks(img: Image.Image, seed: int, base: int, count: int, widths: tuple, pal: tuple) -> Image.Image:
    px = img.load()
    for i in range(count):
        w = widths[0] + int(hash01(i, 1, seed) * (widths[1] - widths[0]))
        cx = int((i + 0.15 + 0.7 * hash01(i, 2, seed)) * W / count)
        boulder(px, cx, base + 4, w, int(w * (0.5 + 0.3 * hash01(i, 3, seed))), seed + i, pal)
        if hash01(i, 4, seed) < 0.3:
            boulder(px, cx + int(w * 0.7), base + 4, int(w * 0.55), int(w * 0.3), seed + i + 50, pal)
    return img


def build(preview: bool = False) -> dict:
    moon = "#9aa4e8"
    mid_trees = vary(scatter(262, 9, (140, 262)), 262)
    giants = [(60, 540, 0.5, 1.0), (236, 522, 0.5, 1.0), (420, 556, 0.5, 1.0), (574, 532, 0.5, 1.0)]
    near_base = 314 + NEAR_EXTRA
    near_layer = {"scale_y": NEAR_SCALE_Y, "y": -NEAR_EXTRA}
    made = [
        ("hills", hills(), 0.04, {"scale_y": 0.015}),
        ("far", stand(111, 248, scatter(111, 44, (28, 66)), P("#4b4582", "#3e3974", "#5e5a94", "#c890a8"), 1,
                      (18, 10, 20), ("#b8708c", 0.5, 56)), 0.08, {"scale_y": 0.04}),
        ("mid3", stand(161, 264, scatter(161, 27, (60, 116)), P("#39356a", "#2d2a5c", "#474f80", moon), 2,
                       (14, 14, 28), ("#8a5c8c", 0.42, 70)), 0.14, {"scale_y": 0.07}),
        ("mist_back", mist(3, 220, 290, 12, ("#c88aa8", "#e0a890", "#9a88c8"), 168), 0.19, {"autoscroll": -4, "scale_y": 0.08}),
        ("mid2", rocks(stand(212, 282, vary(scatter(212, 19, (100, 190)), 212, (0.72, 0.9)), P("#29274f", "#1f1d42", "#2d4a60", "#8f9ae0"), 2,
                             (9, 20, 40), ("#5c4682", 0.3, 80)), 31, 282, 2, (18, 30), P("#3a3868", "#28264f", "#565a92", "#2d5a64")),
         0.22, {"scale_y": 0.12}),
        ("rays_back", rays(7, under_crowns(mid_trees, 300, 7), "#aab4ff", 44), 0.31, {"scale_y": 0.18}),
        ("mid", rocks(stand(262, 300, mid_trees, P("#1c1a3c", "#151330", "#223c50", "#7f8ad8"), 2,
                            (7, 26, 50), None), 47, 300, 2, (26, 46), P("#2c2a56", "#1c1a3c", "#484c84", "#23505a")),
         0.31, {"scale_y": 0.18}),
        ("mist_front", mist(8, 258, 318, 9, ("#b890b8", "#d8a0a0"), 128), 0.4, {"autoscroll": -8, "scale_y": 0.22}),
        ("rays_front", tall(NEAR_EXTRA, lambda: rays(19, under_crowns(giants, near_base, 19, 2), "#c4ccff", 38)), 0.44, near_layer),
        ("near", tall(NEAR_EXTRA, lambda: rocks(stand(313, near_base, giants, P("#100f26", "#0b0a1c", "#21445a", "#6c7cd0"), 2, (6, 36, 72), None, dense=True),
                                                59, near_base, 2, (44, 76), P("#1e1c40", "#100f26", "#34386a", "#1a3a44"))),
         0.44, near_layer),
    ]
    heaven = sky()
    layers = []
    for name, img, scale, extra in made:
        save(img, "backgrounds", f"{ZONE}_{name}.png")
        layers.append((f"{ZONE}_{name}.png", scale, extra))
    if preview:
        out = heaven.copy()
        for name, _, extra in layers:
            layer = Image.open(os.path.join(os.path.dirname(DOCS_PREVIEW), "..", "assets", "backgrounds", name)).convert("RGBA")
            out.alpha_composite(layer.crop((0, layer.height - H, W, layer.height)))
        path = os.path.join(DOCS_PREVIEW, "twilight_grove", "fundo.png")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        out.resize((W * 2, H * 2), Image.NEAREST).save(path)
    return {"sky": Sheet(heaven), "layers": layers}


if __name__ == "__main__":
    build("--preview" in sys.argv)
    print("fundo do twilight grove: ok (para o tema e o chão: python tools/art/gen_zones.py twilight_grove)")
