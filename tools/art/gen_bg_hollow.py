from __future__ import annotations

import math
import os
import sys

from PIL import Image

from gen_bg_ember import H, P, W, gradient, lerp, put, scatter, stand, streak
from gen_bg_grove import Sheet, full_moon, mist, rays, rocks, under_crowns, vary
from vec import ASSETS, DOCS_PREVIEW, hash01, rgba, save

ZONE = "glow_lake"
SHORE = 232
SKY = [(0, "#110d34"), (56, "#1a154c"), (110, "#2a2064"), (158, "#42307e"), (196, "#624094"), (SHORE, "#8e5aa6"), (H, "#a868b0")]
MOON = (236, 140, 20)


def sky() -> Image.Image:
    img = Image.new("RGBA", (W, H))
    px = img.load()
    mx, my, r = MOON
    halo = rgba("#c4b0f4")
    for y in range(H):
        row = gradient(SKY, y)
        for x in range(W):
            d = math.hypot(x - mx, y - my) / 150.0
            px[x, y] = lerp(row, halo, (1.0 - d) ** 2.4 * 0.5) if d < 1.0 else row
    for i in range(150):
        x, y = int(hash01(i, 1, 73) * W), int(hash01(i, 2, 73) ** 1.3 * 170)
        star = rgba("#ffffff" if hash01(i, 3, 73) < 0.25 else "#c8c0ff" if hash01(i, 4, 73) < 0.6 else "#ffe9c8")
        px[x, y] = lerp(star, px[x, y], (y / 170.0) ** 2)
    for i, (x, y, length, thick) in enumerate([(470, 46, 200, 7), (40, 96, 170, 6), (560, 128, 150, 6), (330, 150, 190, 7),
                                               (120, 176, 230, 6), (460, 200, 200, 5), (250, 212, 170, 4)]):
        t = y / 210.0
        tones = tuple(lerp(rgba(a), rgba(b), t) for a, b in (("#221a58", "#5a3c8a"), ("#30266c", "#7a52a2"), ("#4c3c8c", "#a878c0"), ("#7a68b8", "#d8a8dc")))
        streak(px, x, y, length, thick, 600 + i, tones)
    full_moon(px, mx, my, r)
    return img


def fan(a: float, seed: int) -> float:
    i = math.floor(a)
    f = a - i
    f = f * f * (3 - 2 * f)
    return hash01(i, 0, seed) * (1 - f) + hash01(i + 1, 0, seed) * f


def massif(img: Image.Image, peaks: list, base: int, pal: dict, seed: int, light: int = -1, detail: float = 1.0) -> None:
    px = img.load()
    cones = [(x + off, y, s) for x, y, s in peaks for off in (-W, 0, W)]
    haze = rgba(pal["haze"])
    for x in range(W):
        best = min(cones, key=lambda c: c[1] + abs(x - c[0]) * c[2])
        cx, py, slope = best
        top = py + abs(x - cx) * slope
        top += (fan(x * 0.13, seed) - 0.5) * 9 + (fan(x * 0.41, seed + 1) - 0.5) * 4
        for y in range(max(0, int(top)), base + 1):
            sway = (fan(y * 0.06, seed + 10) - 0.5) * 70 + (fan(y * 0.21 + x * 0.02, seed + 11) - 0.5) * 22
            cx, py, slope = min(cones, key=lambda c: c[1] + abs(x + sway - c[0]) * c[2])
            dy = max(4.0, y - py + 16.0)
            a = (x - cx) / dy
            warp = (fan(y * 0.05 + x * 0.01, seed + 2) - 0.5) * 0.5
            n0 = fan(a * 6.0 * detail + warp * 3, seed + 3) + 0.5 * fan(a * 17.0 * detail + y * 0.03, seed + 4)
            n1 = fan((a + 0.03) * 6.0 * detail + warp * 3, seed + 3) + 0.5 * fan((a + 0.03) * 17.0 * detail + y * 0.03, seed + 4)
            turn = (n1 - n0) * light * -1.0 + (0.12 if (x - cx) * light < 0 else -0.12)
            t = (y - py) / max(1.0, base - py)
            snow_line = 0.3 + 0.16 * fan(a * 9 + 5, seed + 5)
            tree_line = 0.5 + 0.2 * fan(a * 5 + 2, seed + 6) + 0.1 * fan(x * 0.06, seed + 12)
            if y - top < 1.5 and turn > -0.05:
                c = pal["rim"]
            elif t < snow_line:
                c = pal["snow"] if turn > 0.05 else pal["rock_l"] if turn > -0.08 else pal["rock"]
                if turn > 0.05 and hash01(x // 2, y, seed + 7) < 0.18:
                    c = pal["rock_l"]
            elif t < tree_line:
                c = pal["rock_l"] if turn > 0.1 else pal["rock"] if turn > -0.06 else pal["rock_d"]
                if turn > 0.1 and hash01(x // 3, y // 2, seed + 8) < 0.1 and t < snow_line + 0.12:
                    c = pal["snow"]
            else:
                c = pal["wood_l"] if turn > 0.08 else pal["wood"] if turn > -0.08 else pal["wood_d"]
                if hash01(x, y // 4, seed + 9) < 0.3 and x % 2 == 0:
                    c = pal["wood_d"] if c != pal["wood_d"] else pal["wood"]
            px[x, y] = lerp(rgba(c), haze, max(0.0, t - 0.25) ** 1.6 * pal.get("mist", 0.8))


def hills() -> Image.Image:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    far = {"rim": "#a898d8", "snow": "#b4a8e0", "rock_l": "#7a68b4", "rock": "#6a58a6", "rock_d": "#5a4a98",
           "wood_l": "#5c4c9c", "wood": "#504290", "wood_d": "#463a84", "haze": "#9462aa", "mist": 0.9}
    massif(img, [(70, 150, 0.62), (190, 176, 0.7), (560, 140, 0.6), (640 - 150, 186, 0.8)], SHORE + 2, far, 51, -1, 0.7)
    near = {"rim": "#e6dcff", "snow": "#d4c8f8", "rock_l": "#8676c4", "rock": "#6756a8", "rock_d": "#4c3f8c",
            "wood_l": "#3f5488", "wood": "#303f74", "wood_d": "#26305e", "haze": "#a074b8", "mist": 0.85}
    massif(img, [(404, 62, 0.74), (322, 118, 0.9), (486, 106, 0.95), (252, 170, 1.0), (566, 164, 1.1)], SHORE + 2, near, 77, -1, 1.0)
    return img


def far_shore() -> Image.Image:
    img = stand(121, SHORE - 2, scatter(121, 46, (12, 36)), P("#33276a", "#291f5a", "#463a80", "#a894dc"), 1, (20, 8, 16), None)
    px = img.load()
    for y in range(SHORE + 1, H):
        for x in range(W):
            px[x, y] = (0, 0, 0, 0)
    return img


def water(scene: Image.Image) -> Image.Image:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = img.load()
    src = scene.load()
    top, deep = rgba("#5a48a4"), rgba("#15103e")
    for y in range(SHORE, H):
        d = y - SHORE
        f = d / (H - SHORE)
        sy = max(0, SHORE - 1 - d)
        wave = int(round(math.sin(d * 0.45) * max(0.0, f - 0.22) * 4.0))
        base = lerp(top, deep, f ** 0.7)
        for x in range(W):
            c = lerp(src[(x + wave) % W, sy], base, 0.26 + 0.42 * f)
            if d == 0:
                c = rgba("#c8b4f0")
            elif hash01(x // (5 + d // 12), y, 5) < 0.035 * (1 - f):
                c = lerp(c, rgba("#9fe8ff"), 0.45)
            px[x, y] = c
    return img


def moon_trail() -> Image.Image:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = img.load()
    mx = MOON[0]
    c = rgba("#fff8e4")
    for y in range(SHORE + 1, H):
        d = y - SHORE
        f = d / (H - SHORE)
        half = 6 + d * 0.36
        for x in range(int(mx - half), int(mx + half) + 1):
            if hash01(x // 3, y, 9) < 0.8 * (1 - f) ** 0.5 * (1.0 - abs(x - mx) / (half + 1)):
                px[x % W, y] = (c[0], c[1], c[2], 215)
    return img


def glitter(seed: int) -> Image.Image:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = img.load()
    for i in range(210):
        y = SHORE + 3 + int(hash01(i, 1, seed) ** 1.4 * (H - SHORE - 40))
        x = int(hash01(i, 2, seed) * W)
        length = 2 + int(hash01(i, 3, seed) * (3 + (y - SHORE) / 14))
        c = rgba("#c8f4ff" if hash01(i, 4, seed) < 0.5 else "#d8c8ff")
        for k in range(length):
            px[(x + k) % W, y] = (c[0], c[1], c[2], 150 if k not in (0, length - 1) else 80)
    return img


def lily(px, cx: int, cy: int, rx: int, seed: int, flower: bool) -> None:
    ry = max(2, int(rx * 0.3))
    leaf, light, dark, rim, under = rgba("#2f8f80"), rgba("#58c8a8"), rgba("#1f6a70"), rgba("#8fe8c4"), rgba("#143a52")
    notch = hash01(seed, 1) * 6.28
    for y in range(cy - ry - 1, cy + ry + 3):
        for x in range(cx - rx - 1, cx + rx + 2):
            u, v = (x - cx) / rx, (y - cy) / ry
            d = math.hypot(u, v)
            if d > 1.0:
                if math.hypot(u, (y - 2 - cy) / ry) <= 1.0 and v > 0:
                    put(px, x, y, under)
                continue
            ang = math.atan2(v, u)
            if abs((ang - notch + math.pi) % (2 * math.pi) - math.pi) < 0.22 and d > 0.25:
                continue
            if d > 0.86:
                c = rim if v < 0.1 else dark
            elif int((ang + math.pi) * 5 / math.pi + seed) % 2 == 0 and d > 0.3 and hash01(x, y, seed) < 0.5:
                c = light
            else:
                c = leaf
            put(px, x, y, c)
    if flower:
        fx, fy = cx + int(rx * 0.3), cy - ry
        for dx, dy, c in ((0, -3, "#fff4fa"), (-1, -2, "#ffd0e8"), (0, -2, "#fff4fa"), (1, -2, "#ffd0e8"), (-2, -1, "#f0a8d0"),
                          (-1, -1, "#fff4fa"), (0, -1, "#ffe08a"), (1, -1, "#fff4fa"), (2, -1, "#f0a8d0"), (-1, 0, "#f0a8d0"), (0, 0, "#ffd0e8"), (1, 0, "#f0a8d0")):
            put(px, fx + dx, fy + dy, rgba(c))


def lilies(seed: int, count: int, y0: int, y1: int, size: tuple) -> Image.Image:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = img.load()
    spots = []
    for i in range(count):
        t = hash01(i, 1, seed)
        spots.append((int((i + 0.2 + 0.6 * hash01(i, 2, seed)) * W / count), int(y0 + t * (y1 - y0)), int(size[0] + t * (size[1] - size[0])), i))
    for cx, cy, rx, i in sorted(spots, key=lambda s: s[1]):
        lily(px, cx, cy, rx, seed + i, hash01(i, 3, seed) < 0.4)
        if hash01(i, 4, seed) < 0.5:
            lily(px, cx + rx + 6, cy + 2, max(4, rx // 2), seed + i + 40, False)
    return img


def reeds(img: Image.Image, seed: int, base: int, count: int, colors: tuple) -> Image.Image:
    px = img.load()
    body, light, head = colors
    for i in range(count):
        cx = int((i + 0.2 + 0.6 * hash01(i, 1, seed)) * W / count)
        for k in range(5 + int(hash01(i, 2, seed) * 6)):
            x0 = cx + int((hash01(i, k, seed + 1) - 0.5) * 26)
            hgt = 14 + int(hash01(i, k, seed + 2) * 30)
            lean = (hash01(i, k, seed + 3) - 0.5) * 0.5
            for j in range(hgt):
                put(px, x0 + int(lean * j * j / hgt), base - j, light if (j + k) % 7 == 0 else body)
            if k % 3 == 0:
                tx = x0 + int(lean * hgt)
                for j in range(5):
                    put(px, tx, base - hgt - j, head)
                    put(px, tx + 1, base - hgt - j, head)
    return img


def platform() -> None:
    img = Image.new("RGBA", (48, 16), (0, 0, 0, 0))
    px = img.load()
    leaf, light, dark, rim, under = rgba("#2f8f80"), rgba("#58c8a8"), rgba("#1f6a70"), rgba("#8fe8c4"), rgba("#143a52")
    rows = {1: (6, rim), 2: (3, dark), 3: (1, leaf), 4: (0, leaf), 5: (0, leaf), 6: (1, leaf), 7: (3, dark), 8: (6, under), 9: (10, under)}
    for y, (inset, base) in rows.items():
        for x in range(inset, 48 - inset):
            c = base
            edge = min(x - inset, 47 - inset - x)
            if 3 <= y <= 6:
                if edge < 2:
                    c = rim if y <= 4 else dark
                elif (x + y * 2) % 8 == 0 or (x - y * 2) % 8 == 4:
                    c = light
                elif y == 6 and x % 3 == 0:
                    c = dark
            px[x, y] = c
    for x in range(20, 23):
        for y in range(5, 8):
            if x - 20 <= 7 - y:
                px[x, y] = (0, 0, 0, 0)
    for dx, dy, c in ((0, -3, "#fff4fa"), (-1, -2, "#ffd0e8"), (0, -2, "#fff4fa"), (1, -2, "#ffd0e8"), (-2, -1, "#f0a8d0"), (-1, -1, "#fff4fa"),
                      (0, -1, "#ffe08a"), (1, -1, "#fff4fa"), (2, -1, "#f0a8d0"), (-1, 0, "#f0a8d0"), (0, 0, "#ffd0e8"), (1, 0, "#f0a8d0")):
        px[9 + dx, 3 + dy] = rgba(c)
    img.save(os.path.join(ASSETS, "tiles", f"{ZONE}_platform.png"))


FROG = {"g": "#5fcf7c", "d": "#2f7f52", "b": "#d8f7b0", "e": "#fffbe6", "p": "#101428"}
FROG_FRAMES = [
    ["..........", "..........", "......ep..", "....ggggg.", "..ggggggbb", ".ggdgggbb.", ".gdd.gd.d.", ".dd..dd..."],
    ["..........", "..........", "..........", ".....gep..", "..gggggggb", ".ggdggggbb", "gddd.gdd.d", "dd...dd..."],
    ["......ep..", "....ggggg.", "..ggggggbb", ".gggggbb..", "gdgg......", "dd........", "..........", ".........."],
]


def frog_sheet() -> None:
    img = Image.new("RGBA", (10 * len(FROG_FRAMES), 8), (0, 0, 0, 0))
    px = img.load()
    for f, rows in enumerate(FROG_FRAMES):
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch != ".":
                    px[f * 10 + x, y] = rgba(FROG[ch])
    img.save(os.path.join(ASSETS, "sprites", "props", "frog.png"))


def build(preview: bool = False) -> dict:
    heaven = sky()
    range_, shore = hills(), far_shore()
    scene = heaven.copy()
    scene.alpha_composite(range_)
    scene.alpha_composite(shore)
    lake = {"scale_y": 0.12}
    mid_trees = vary([(64, 112), (330, 150), (470, 92), (590, 132)], 27, (0.74, 0.88), (0.85, 1.1))
    made = [
        ("hills", range_, 0.0, lake),
        ("haze", mist(12, SHORE - 34, SHORE - 6, 8, ("#b89ad8", "#9a8ad0", "#c8a8dc"), 120), 0.0, dict(lake, autoscroll=-2)),
        ("shore", shore, 0.0, lake),
        ("water", water(scene), 0.0, lake),
        ("trail", moon_trail(), 0.0, dict(lake, shimmer=True)),
        ("glitter", glitter(5), 0.0, dict(lake, autoscroll=-3)),
        ("lilies_far", lilies(11, 9, SHORE + 12, SHORE + 34, (7, 13)), 0.06, {"scale_y": 0.12}),
        ("mist", mist(4, SHORE - 6, SHORE + 30, 9, ("#b8a0e0", "#8fd8e8", "#d8b0e0"), 110), 0.1, {"autoscroll": -5, "scale_y": 0.13}),
        ("lilies", lilies(23, 6, SHORE + 44, SHORE + 70, (16, 28)), 0.16, {"scale_y": 0.16}),
        ("rays", rays(9, under_crowns(mid_trees, 306, 9), "#b8b0ff", 30), 0.27, {"scale_y": 0.2}),
        ("mid", reeds(rocks(stand(272, 306, mid_trees, P("#1e1a44", "#161236", "#234058", "#8a90e0"), 2, (6, 20, 40), None),
                            41, 306, 2, (22, 40), P("#2e2a5c", "#1e1a44", "#4c4c8c", "#23585e")),
                      6, 307, 8, P("#1a2a48", "#2f6a78", "#10102a")), 0.27, {"scale_y": 0.2}),
        ("near", reeds(rocks(stand(323, 322, [], P("#100f26", "#0b0a1c", "#21445a", "#6c7cd0"), 2, (7, 36, 64), None),
                             61, 322, 1, (48, 70), P("#1e1c40", "#100f26", "#34386a", "#1a3a44")),
                       15, 323, 6, P("#0e1630", "#1e4a5a", "#08081a")), 0.44, {"scale_y": 0.3}),
    ]
    layers = []
    for name, img, scale, extra in made:
        save(img, "backgrounds", f"{ZONE}_{name}.png")
        layers.append((f"{ZONE}_{name}.png", scale, extra))
    platform()
    frog_sheet()
    if preview:
        out = heaven.copy()
        for name, _, _ in layers:
            layer = Image.open(os.path.join(ASSETS, "backgrounds", name)).convert("RGBA")
            out.alpha_composite(layer.crop((0, layer.height - H, W, layer.height)))
        path = os.path.join(DOCS_PREVIEW, "glimmer_hollow", "fundo.png")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        out.resize((W * 2, H * 2), Image.NEAREST).save(path)
    return {"sky": Sheet(heaven), "layers": layers, "platform": f"{ZONE}_platform.png"}


if __name__ == "__main__":
    build("--preview" in sys.argv)
    print("fundo do lago de glimmer hollow: ok (para o tema e o chao: python tools/art/gen_zones.py glow_lake)")
