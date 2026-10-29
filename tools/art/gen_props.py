from __future__ import annotations

import math

from PIL import Image

import vec
from vec import Canvas, capsule, curve, ellipse, hash01, pack, ribbon, save, save_json, smooth

vec.C.update({"leaf": "#2fb592", "leaf_l": "#63dbaa"})
EMBER_GREENS = {"grass": "#4fb64c", "grass_l": "#b6ea6a", "grass_d": "#2a8648", "moss": "#2a6c44", "leaf": "#3d9a4e", "leaf_l": "#86d45e"}

PPU = 1
GRASS = ("grass", "grass_l", "grass_d")


def ground_canvas(w: float, h: float) -> Canvas:
    return Canvas(w, h, PPU, origin=(w / 2, h - 0.5))


def tuft(seed: int, width: float, height: float) -> Image.Image:
    c = ground_canvas(width + 4, height + 1.5)
    n = int(width)
    for i in range(n):
        bx = (i - (n - 1) / 2) * (width / n)
        hh = height * (0.4 + 0.6 * hash01(i, seed, 1))
        bend = (hash01(i, seed, 2) - 0.5) * height * 0.7 + bx * 0.25
        c.poly(ribbon(curve([(bx, 0.4), (bx + bend * 0.35, -hh * 0.55), (bx + bend, -hh)]), 0.6, 0.35), GRASS[i % 3])
    return c.finish()


def fern(seed: int, size: float) -> Image.Image:
    c = ground_canvas(size * 2.2, size + 1.5)
    for f in range(5):
        lean = (f - 2) / 2
        stem = curve([(0, 0.3), (lean * size * 0.42, -size * 0.72), (lean * size * 0.98, -size * (0.95 - 0.4 * abs(lean)))], 8)
        c.poly(ribbon(stem, 0.5, 0.4), "grass_d")
        for i in range(2, len(stem) - 1):
            t = i / len(stem)
            ang = math.atan2(stem[i + 1][1] - stem[i][1], stem[i + 1][0] - stem[i][0])
            reach = size * 0.2 * (1 - t) + 0.45
            for sgn in (-1, 1):
                at = (stem[i][0] + math.cos(ang + sgn * 1.25) * reach * 0.55, stem[i][1] + math.sin(ang + sgn * 1.25) * reach * 0.55)
                c.poly(ellipse(at, reach * 0.7, max(0.55, reach * 0.3), ang + sgn * 1.25, 10), "leaf" if (i + f + seed) % 2 else "leaf_l")
    return c.finish()


def flower(seed: int, petal: str, heart: str, height: float) -> Image.Image:
    c = ground_canvas(6, height + 3)
    lean = (hash01(seed, 1) - 0.5) * 2.0
    stem = curve([(0, 0.3), (lean * 0.4, -height * 0.5), (lean, -height)])
    c.poly(ribbon(stem, 0.5, 0.45), "grass_d")
    c.poly(ellipse((lean * 0.3 + 1.0, -height * 0.38), 1.1, 0.6, -0.5), "grass")
    c.poly(ellipse((lean * 0.3 - 1.0, -height * 0.5), 1.0, 0.6, 0.6), "grass")
    for i in range(5):
        a = i * 2 * math.pi / 5 - 1.57
        c.poly(ellipse((lean + math.cos(a) * 1.0, -height + math.sin(a) * 1.0), 0.9, 0.7, a), petal)
    c.poly(ellipse((lean, -height), 0.6), heart)
    return c.finish()


def mushroom(seed: int, cap_w: float, cap_h: float, stalk_h: float, stalk_w: float, cap: tuple, gill: str, spots: int = 0) -> Image.Image:
    c = ground_canvas(cap_w + 2, cap_h + stalk_h + 2)
    stalk = smooth([(-stalk_w * 0.65, 0.3), (stalk_w * 0.65, 0.3), (stalk_w * 0.42, -stalk_h - 0.2), (-stalk_w * 0.42, -stalk_h - 0.2)], 1)
    c.poly(stalk, "#f4ecd6")
    c.clip(stalk, [(stalk_w * 0.1, 1), (stalk_w, 1), (stalk_w, -stalk_h - 1), (stalk_w * 0.1, -stalk_h - 1)], "#cdbfa6")
    cy, rx = -stalk_h + 0.3, cap_w / 2
    dome = [(rx * math.cos(math.pi + math.pi * i / 16), cy + cap_h * math.sin(math.pi + math.pi * i / 16)) for i in range(17)]
    dome += [(rx * math.cos(math.pi * i / 8), cy + 0.55 * math.sin(math.pi * i / 8)) for i in range(1, 8)]
    c.poly(dome, cap[0])
    c.clip(dome, ellipse((rx * 0.5, cy - cap_h * 0.2), rx * 0.75, cap_h * 0.9), cap[2])
    c.clip(dome, ellipse((-rx * 0.35, cy - cap_h * 0.62), rx * 0.42, cap_h * 0.3, -0.4), cap[1])
    c.poly(ellipse((0, cy + 0.1), rx * 0.9, 0.42), gill)
    for i in range(spots):
        sx = (hash01(i, seed, 3) - 0.5) * cap_w * 0.75
        sy = cy - cap_h * (0.25 + 0.55 * hash01(i, seed, 4))
        c.clip(dome, ellipse((sx, sy), 0.32 + 0.3 * hash01(i, seed, 5)), "#fff1d0")
    return c.finish()


AMANITA = {"cap": "#d43131", "light": "#f0604e", "dark": "#981f2a", "rim": "#5e1220", "shine": "#ff9a86",
           "spot": "#f6e7bc", "spot_d": "#cfb689", "stalk": "#a58d6b", "stalk_l": "#d2bd96", "stalk_d": "#6f5a43"}
AMANITA_SPOTS = [(0.05, 0.6, 1.3), (-0.52, 0.42, 1.0), (0.55, 0.4, 0.95), (-0.14, 0.2, 0.8), (0.76, 0.18, 0.7),
                 (-0.78, 0.2, 0.75), (0.32, 0.86, 0.7), (-0.36, 0.8, 0.7)]


def amanita(cap_w: float, cap_h: float, stalk_h: float, stalk_w: float, spots: int) -> Image.Image:
    a = AMANITA
    c = ground_canvas(cap_w + 2, cap_h + stalk_h + 2)
    stalk = smooth([(-stalk_w * 0.8, 0.3), (stalk_w * 0.8, 0.3), (stalk_w * 0.45, -stalk_h - 0.3), (-stalk_w * 0.45, -stalk_h - 0.3)], 1)
    c.poly(stalk, a["stalk"])
    c.clip(stalk, [(-stalk_w, 1), (-stalk_w * 0.2, 1), (-stalk_w * 0.2, -stalk_h - 1), (-stalk_w, -stalk_h - 1)], a["stalk_d"])
    c.clip(stalk, [(stalk_w * 0.05, 1), (stalk_w * 0.4, 1), (stalk_w * 0.4, -stalk_h - 1), (stalk_w * 0.05, -stalk_h - 1)], a["stalk_l"])
    cy, rx = -stalk_h + 0.4, cap_w / 2
    dome = [(rx * math.cos(math.pi + math.pi * i / 16), cy + cap_h * math.sin(math.pi + math.pi * i / 16)) for i in range(17)]
    dome += [(rx * math.cos(math.pi * i / 8), cy + 0.7 * math.sin(math.pi * i / 8)) for i in range(1, 8)]
    c.poly(dome, a["cap"])
    c.clip(dome, ellipse((rx * 0.32, cy - cap_h * 0.66), rx * 0.66, cap_h * 0.36), a["light"])
    c.clip(dome, [(-rx - 1, cy + 1), (rx + 1, cy + 1), (rx + 1, cy - cap_h * 0.2), (-rx - 1, cy - cap_h * 0.36)], a["dark"])
    c.clip(dome, ellipse((-rx * 0.94, cy - cap_h * 0.35), rx * 0.26, cap_h * 0.55), a["dark"])
    c.clip(dome, [(-rx - 1, cy + 1), (rx + 1, cy + 1), (rx + 1, cy - 0.8), (-rx - 1, cy - 0.8)], a["rim"])
    c.clip(dome, ellipse((rx * 0.5, cy - cap_h * 0.88), rx * 0.34, cap_h * 0.09), a["shine"])
    for fx, fy, k in AMANITA_SPOTS[:spots]:
        sx, sy = fx * rx * 0.9, cy - cap_h * fy
        r = max(0.55, cap_w * 0.075 * k)
        c.clip(dome, ellipse((sx - 0.25, sy + 0.25), r * 1.12, r * 0.92), a["spot_d"])
        c.clip(dome, ellipse((sx + 0.15, sy - 0.15), r * 0.92, r * 0.72), a["spot"])
    return c.finish()


def bush(seed: int, w: float, h: float) -> Image.Image:
    c = ground_canvas(w + 4, h + 3)
    n = max(4, int(w / 2.6))
    blobs = []
    for i in range(n):
        t = i / (n - 1)
        bx = (t - 0.5) * (w - 4) + (hash01(i, seed, 1) - 0.5) * 1.6
        by = -h * (0.3 + 0.5 * math.sin(math.pi * t) * (0.7 + 0.3 * hash01(i, seed, 2)))
        blobs.append((bx, by, h * (0.3 + 0.16 * hash01(i, seed, 3))))
    c.poly([(-w / 2 + 2, 0.4), (w / 2 - 2, 0.4), (w / 2 - 2.5, -h * 0.35), (-w / 2 + 2.5, -h * 0.35)], "grass_d")
    for bx, by, r in blobs:
        c.poly(ellipse((bx, by + r * 0.4), r * 1.15, r), "grass_d")
    for bx, by, r in blobs:
        c.poly(ellipse((bx - r * 0.12, by), r * 0.95, r * 0.82), "leaf")
    for bx, by, r in blobs:
        c.poly(ellipse((bx - r * 0.3, by - r * 0.32), r * 0.55, r * 0.42), "leaf_l")
    for i in range(int(w * 0.6)):
        bx, by, r = blobs[int(hash01(i, seed, 4) * n)]
        c.dot((bx + (hash01(i, seed, 5) - 0.6) * r * 1.6, by + (hash01(i, seed, 6) - 0.7) * r * 1.4), "grass_l")
    return c.finish()


def shrub(seed: int, w: float, h: float, bloom: str | None = None) -> Image.Image:
    c = ground_canvas(w + 6, h + 4)
    blobs = []
    for row in range(3):
        n = max(3, int(w / (5.5 - row * 0.6)))
        for i in range(n):
            t = (i + 0.5) / n
            arch = math.sin(math.pi * t) ** 0.7
            r = h * (0.3 - row * 0.05) * (0.75 + 0.5 * hash01(i, seed, 10 + row))
            bx = (t - 0.5) * (w - 2 * r) + (hash01(i, seed, 20 + row) - 0.5) * 2.5
            by = -r * 0.8 - (h - r * 2.0) * arch * (1.0 - row * 0.3) * (0.6 + 0.4 * hash01(i, seed, 30 + row))
            blobs.append((row, bx, by, r))
    c.poly([(-w / 2 + 3, 0.4), (w / 2 - 3, 0.4), (w / 2 - 4, -h * 0.4), (-w / 2 + 4, -h * 0.4)], "moss")
    for row in range(3):
        mine = [b for b in blobs if b[0] == row]
        for _, bx, by, r in mine:
            c.poly(ellipse((bx, by + r * 0.35), r * 1.12, r), "moss" if row == 0 else "grass_d")
        for _, bx, by, r in mine:
            c.poly(ellipse((bx - r * 0.1, by - r * 0.05), r * 0.92, r * 0.8), "grass_d" if row == 0 else "leaf")
        if row:
            for _, bx, by, r in mine:
                c.poly(ellipse((bx - r * 0.28, by - r * 0.34), r * 0.52, r * 0.36, -0.3), "leaf_l" if row == 2 else "grass")
    front = [b for b in blobs if b[0]]
    for i in range(int(w * h / 9)):
        _, bx, by, r = front[int(hash01(i, seed, 4) * len(front))]
        at = (bx + (hash01(i, seed, 5) - 0.55) * r * 1.7, by + (hash01(i, seed, 6) - 0.6) * r * 1.5)
        tone = ("leaf_l", "grass_l", "grass_d", "leaf_l", "grass")[int(hash01(i, seed, 7) * 5)]
        c.poly(ellipse(at, 1.3, 0.7, (hash01(i, seed, 8) - 0.5) * 2.4, 8), tone)
    if bloom:
        for i in range(int(w / 3.5)):
            _, bx, by, r = front[int(hash01(i, seed, 40) * len(front))]
            c.dot((bx + (hash01(i, seed, 41) - 0.5) * r * 1.5, by + (hash01(i, seed, 42) - 0.6) * r * 1.3), bloom)
    return c.finish()


def broadleaf(seed: int, size: float) -> Image.Image:
    c = ground_canvas(size * 2.4, size + 2.5)
    n = 7
    for i in sorted(range(n), key=lambda k: -abs(k - n // 2)):
        ang = (i - (n - 1) / 2) * 0.42 + (hash01(i, seed, 1) - 0.5) * 0.2
        length = size * (1.0 - 0.3 * abs(i - (n - 1) / 2) / n * 2) * (0.85 + 0.25 * hash01(i, seed, 2))
        tip = (math.sin(ang) * length, -math.cos(ang) * length)
        mid = (tip[0] * 0.55, tip[1] * 0.55)
        leaf = ellipse(mid, length * 0.5, max(1.2, length * 0.2), math.atan2(tip[1], tip[0]), 14)
        c.poly(leaf, ("leaf", "grass", "leaf_l")[i % 3])
        c.clip(leaf, ribbon([(0, 0), tip], 0.25, 0.2), "grass_d")
    return c.finish()


def sapling(seed: int, height: float) -> Image.Image:
    c = ground_canvas(height * 0.8 + 4, height + 2)
    c.poly([(-0.6, 0.4), (0.6, 0.4), (0.6, -height * 0.3), (-0.6, -height * 0.3)], "wood_d")
    tiers = 3 if height < 16 else 4
    for t in range(tiers - 1, -1, -1):
        f = (t + 1) / tiers
        top = -height + height * 0.78 * t / tiers
        half = height * 0.34 * f ** 0.8 + 0.6
        depth = height * 0.42
        skirt = [(0, top), (half * 0.55, top + depth * 0.55), (half, top + depth), (half * 0.45, top + depth * 0.82), (0, top + depth),
                 (-half * 0.45, top + depth * 0.82), (-half, top + depth), (-half * 0.55, top + depth * 0.55)]
        c.poly(skirt, "grass_d")
        c.clip(skirt, [(-0.2, top - 1), (half + 1, top - 1), (half + 1, top + depth * 0.7), (-0.2, top + depth * 0.7)], "leaf")
        c.clip(skirt, [(half * 0.3, top + depth * 0.5), (half + 1, top + depth * 0.5), (half + 1, top + depth * 0.86), (half * 0.3, top + depth * 0.86)], "leaf_l")
    return c.finish()


def reeds(seed: int, count: int, height: float) -> Image.Image:
    c = ground_canvas(count * 1.6 + 6, height + 3)
    for i in range(count):
        bx = (i - (count - 1) / 2) * 1.5
        hh = height * (0.55 + 0.45 * hash01(i, seed, 1))
        bend = (hash01(i, seed, 2) - 0.5) * height * 0.45 + bx * 0.2
        stem = curve([(bx, 0.4), (bx + bend * 0.3, -hh * 0.55), (bx + bend, -hh)], 8)
        c.poly(ribbon(stem, 0.55, 0.3), GRASS[i % 3])
        if i % 2 == 0:
            c.poly(ellipse((bx + bend, -hh - 0.9), 0.75, 1.7, bend * 0.05), "#ecd88c" if i % 4 else "#c9a860")
    return c.finish()


def vine(seed: int, length: float) -> Image.Image:
    c = Canvas(9, length + 2, PPU, origin=(4.5, 0.0))
    lean = (hash01(seed, 1) - 0.5) * 3.0
    stem = curve([(0, -0.5), (lean * 0.5, length * 0.45), (lean, length)], 8)
    c.poly(ribbon(stem, 0.55, 0.5), "moss")
    for i in range(2, len(stem) - 1, 2):
        side = 1 if (i // 2 + seed) % 2 else -1
        c.poly(ellipse((stem[i][0] + side * 1.3, stem[i][1] + 0.4), 1.3, 0.8, side * 0.5), "grass" if i % 4 else "leaf")
    c.poly(ellipse(stem[-1], 0.9, 1.1), "grass_l")
    return c.finish()


def stump(seed: int) -> Image.Image:
    c = ground_canvas(14, 9)
    body = smooth([(-5.2, 0.3), (-4.0, -2.0), (-4.0, -5.4), (4.0, -5.4), (4.0, -2.0), (5.4, 0.3)], 1)
    c.poly(body, "wood")
    c.clip(body, [(0.8, 1), (7, 1), (7, -7), (0.8, -7)], "wood_d")
    for x in (-2.4, -0.6, 2.6):
        c.clip(body, [(x, 0.5), (x + 0.6, 0.5), (x + 0.6, -4.2), (x, -4.2)], "wood_d")
    c.poly(ellipse((0, -5.5), 4.1, 1.4), "wood_l")
    c.poly(ellipse((0.3, -5.5), 2.2, 0.7), "wood")
    c.poly(ellipse((-2.6, -5.9), 1.9, 0.8), "grass")
    c.dot((-3.4, -6.6), "grass_l", 2, 1)
    return c.finish(outline="outline")


def rock(seed: int, w: float, h: float) -> Image.Image:
    c = ground_canvas(w + 2, h + 2)
    shape = smooth([(-w / 2, 0.3), (-w * 0.42, -h * 0.7), (-w * 0.1, -h), (w * 0.3, -h * 0.85), (w / 2, -h * 0.3), (w * 0.46, 0.3)], 2)
    c.poly(shape, "#565f86")
    c.clip(shape, ellipse((-w * 0.15, -h * 0.85), w * 0.4, h * 0.35), "#8e97b8")
    c.clip(shape, [(-w, 0.5), (w, 0.5), (w, -h * 0.22), (-w, -h * 0.3)], "#3f466b")
    c.clip(shape, ellipse((w * 0.1, -h), w * 0.3, h * 0.2), "grass")
    return c.finish()


TAN = ("#cc9360", "#eec390", "#94623f")
AQUA = ("#40d2c2", "#d6fff2", "#1f8f98")
LILAC = ("#9383ea", "#d3c8ff", "#6253b8")
MINT_GLOW = [0.5, 0.95, 0.83]
LILAC_GLOW = [0.72, 0.66, 1.0]
RED_GLOW = [1.0, 0.5, 0.42]

SWAY_MARGIN = 3


def item(name: str, image: Image.Image, weight: float, motion: str = "sway", anchor: str = "floor",
         glow: list | None = None, glow_radius: int = 0, front: float = 0.0, span: int = 1) -> dict:
    if motion != "none":
        wide = Image.new("RGBA", (image.width + 2 * SWAY_MARGIN, image.height), (0, 0, 0, 0))
        wide.paste(image, (SWAY_MARGIN, 0))
        image = wide
    out = {"name": name, "image": image, "weight": weight, "motion": motion, "anchor": anchor,
           "glow": glow, "glow_radius": glow_radius, "front": front}
    if span > 1:
        out["span"] = span
    return out


def forest_items() -> list[dict]:
    return [
        item("tuft_a", tuft(1, 7, 6), 6, front=0.35),
        item("tuft_b", tuft(2, 9, 8), 5, front=0.35),
        item("tuft_c", tuft(3, 5, 4.5), 5, front=0.35),
        item("tuft_tall", tuft(4, 8, 12), 2.5),
        item("tuft_wide", tuft(5, 12, 9.5), 2.5, front=0.2),
        item("fern_a", fern(1, 8), 2.2),
        item("fern_b", fern(2, 11), 1.6),
        item("bush_a", bush(1, 15, 9), 1.5, "rustle"),
        item("bush_b", bush(2, 21, 12), 1.0, "rustle"),
        item("flower_white", flower(1, "#f7f5ff", "fire2", 6.5), 1.6),
        item("flower_yellow", flower(2, "#ffe391", "fire1", 5.5), 1.4),
        item("flower_lilac", flower(3, "#bfb0ff", "#f7f5ff", 7.0), 1.4),
        item("shroom_red_s", amanita(5.4, 3.6, 3.0, 1.4, 3), 1.3, "bob", glow=RED_GLOW, glow_radius=22),
        item("shroom_red_m", amanita(7.6, 5.0, 4.2, 1.8, 5), 1.1, "bob", glow=RED_GLOW, glow_radius=28),
        item("shroom_red_l", amanita(10.6, 6.6, 5.4, 2.3, 7), 0.7, "bob", glow=RED_GLOW, glow_radius=34),
        item("shroom_tan", mushroom(3, 5.2, 2.6, 3.4, 1.4, TAN, "#f4ecd6"), 1.2, "bob"),
        item("glow_aqua_s", mushroom(4, 4.0, 2.8, 3.6, 1.0, AQUA, "mint_l", 3), 1.3, "bob", glow=MINT_GLOW, glow_radius=26),
        item("glow_aqua_m", mushroom(5, 5.6, 3.6, 5.4, 1.3, AQUA, "mint_l", 4), 0.9, "bob", glow=MINT_GLOW, glow_radius=34),
        item("glow_lilac_s", mushroom(6, 4.4, 3.0, 4.2, 1.1, LILAC, "#efeaff", 3), 1.1, "bob", glow=LILAC_GLOW, glow_radius=28),
        item("rock_a", rock(1, 9, 4.5), 1.0, "none"),
        item("rock_b", rock(2, 6, 3.2), 1.0, "none"),
        item("stump", stump(1), 0.5, "none"),
        item("vine_s", vine(1, 9), 3.0, anchor="ceiling"),
        item("vine_m", vine(2, 15), 2.5, anchor="ceiling"),
        item("vine_l", vine(3, 23), 1.5, anchor="ceiling"),
        item("vine_xl", vine(4, 31), 0.7, anchor="ceiling"),
    ]


def boulder(seed: int, w: float, h: float) -> Image.Image:
    c = ground_canvas(w + 2, h + 2)
    shape = [(-w / 2, 0.3), (-w * (0.4 + 0.06 * hash01(seed, 1)), -h * (0.5 + 0.3 * hash01(seed, 2))), (-w * 0.12, -h),
             (w * (0.14 + 0.1 * hash01(seed, 3)), -h * 0.92), (w * 0.4, -h * (0.45 + 0.25 * hash01(seed, 4))), (w / 2, 0.3)]
    c.poly(shape, "#565f86")
    c.clip(shape, [(-w * 0.14, -h - 1), (w, -h - 1), (w, -h * 0.62), (-w * 0.3, -h * 0.5)], "#8e97b8")
    c.clip(shape, [(-w, 0.5), (-w * 0.2, 0.5), (-w * 0.34, -h * 0.55), (-w, -h)], "#3f466b")
    c.clip(shape, [(-w, 0.5), (w, 0.5), (w, -h * 0.16), (-w, -h * 0.2)], "#3f466b")
    c.clip(shape, ribbon([(w * 0.1, -h), (w * 0.02, -h * 0.55), (w * 0.12, -h * 0.25)], 0.3, 0.2), "#3f466b")
    c.clip(shape, ellipse((-w * 0.02, -h * 1.02), w * 0.3, h * 0.16), "grass")
    c.clip(shape, ellipse((-w * 0.08, -h * 1.05), w * 0.16, h * 0.1), "grass_l")
    return c.finish()


def grove_items() -> list[dict]:
    weights = {"fern_a": 3.0, "fern_b": 2.6, "bush_a": 2.4, "bush_b": 2.0, "rock_a": 1.6, "rock_b": 1.6}
    items = forest_items()
    for d in items:
        d["weight"] = weights.get(d["name"], d["weight"])
    return items + [
        item("boulder_a", boulder(1, 15, 9), 1.5, "none"),
        item("boulder_b", boulder(2, 22, 13), 0.35, "none"),
        item("boulder_c", boulder(3, 30, 17), 0.2, "none"),
        item("boulder_d", boulder(4, 20, 16), 0.2, "none"),
        item("fern_big", fern(3, 14), 1.8),
    ]


def ember_items() -> list[dict]:
    keep = {k: vec.C[k] for k in EMBER_GREENS}
    vec.C.update(EMBER_GREENS)
    weights = {"tuft_tall": 3.0, "tuft_wide": 3.0, "fern_a": 3.0, "fern_b": 2.4, "bush_a": 1.6, "bush_b": 1.2,
               "shroom_red_s": 0.7, "shroom_red_m": 0.5, "shroom_red_l": 0.3, "shroom_tan": 1.0,
               "glow_aqua_s": 0.35, "glow_aqua_m": 0.2, "glow_lilac_s": 0.25, "rock_a": 0.5, "rock_b": 0.5}
    items = forest_items()
    for d in items:
        d["weight"] = weights.get(d["name"], d["weight"])
    items += [
        item("shrub_a", shrub(1, 26, 15), 1.2, "rustle", span=2),
        item("shrub_b", shrub(2, 34, 19), 0.9, "rustle", span=3),
        item("shrub_c", shrub(3, 44, 23), 0.5, "rustle", span=3),
        item("shrub_bloom", shrub(4, 30, 16, "#fff3c4"), 0.8, "rustle", span=2),
        item("shrub_berry", shrub(5, 24, 14, "#ffb05a"), 0.6, "rustle", span=2),
        item("broadleaf_a", broadleaf(1, 9), 3.0),
        item("broadleaf_b", broadleaf(2, 13), 2.4, span=2),
        item("fern_big", fern(3, 14), 2.4, span=2),
        item("reeds_a", reeds(1, 6, 15), 2.4, front=0.3),
        item("reeds_b", reeds(2, 9, 19), 1.8, front=0.2),
        item("sapling_a", sapling(1, 15), 1.3),
        item("sapling_b", sapling(2, 22), 1.0),
        item("flower_coral", flower(4, "#ff9c84", "#ffe391", 6.5), 1.4),
    ]
    vec.C.update(keep)
    return items


FIRE_FRAME = 24


def campfire_frame(f: int, frames: int, lit: bool = True) -> Image.Image:
    base = Canvas(FIRE_FRAME, FIRE_FRAME, PPU, origin=(12, 23.3))
    for x in (-7.2, -4.4, 4.4, 7.2):
        stone = ellipse((x, -1.0), 1.9, 1.35)
        base.poly(stone, "#5a6388")
        base.clip(stone, ellipse((x - 0.4, -1.7), 1.2, 0.6), "#8e97b8")
    for a, b, tone in (((5.6, -1.3), (-4.6, -3.8), "wood_d"), ((-5.6, -1.3), (4.6, -3.8), "wood")):
        base.poly(capsule(a, b, 1.25), tone)
        base.poly(ellipse(a, 1.0), "wood_l")
        base.poly(ellipse(a, 0.5), "wood")
    out = base.finish(outline="outline")
    if not lit:
        return out
    fire = Canvas(FIRE_FRAME, FIRE_FRAME, PPU, origin=(12, 23.3))
    phase = 2 * math.pi * f / frames
    fire.poly(ellipse((0, -2.8), 3.6, 1.2), "fire1")
    for k, (height, wmax, tone) in enumerate(((13.0, 4.3, "fire0"), (10.0, 3.2, "fire1"), (7.0, 2.2, "fire2"), (4.0, 1.2, "fire3"))):
        hh = height * (1.0 + 0.09 * math.sin(phase * 2 + k * 1.3))
        left, right = [], []
        for i in range(15):
            t = i / 14
            w = wmax * math.sin(math.pi * t ** 0.72) ** 0.9 * (1 - 0.3 * t)
            cx = 1.9 * t * t * math.sin(phase + t * 2.4 + k * 0.5)
            left.append((cx - w, -2.6 - hh * t))
            right.append((cx + w, -2.6 - hh * t))
        fire.poly(left + right[::-1], tone)
    for k in range(3):
        rise = (f * 1.6 + k * 3.1) % 9.0
        fire.poly(ellipse((math.sin(k * 2.1 + rise) * 3.0, -13.0 - rise), 0.32), "fire2")
    out.alpha_composite(fire.finish())
    return out


def dog() -> Image.Image:
    c = Canvas(32, 24, PPU, origin=(15, 23.3))
    for hip, paw in (((-5.4, -6.0), (-5.9, -1.0)), ((4.4, -6.0), (4.8, -1.0))):
        c.poly(capsule(hip, paw, 1.3, 1.0), "fur_d")
    c.poly(ribbon(curve([(-8.6, -9.8), (-11.4, -12.6), (-10.4, -16.4)]), 1.15, 0.5), "fur")
    c.poly(ellipse((-10.5, -15.9), 0.75), "fur_l")
    body = capsule((-6.0, -8.7), (4.6, -9.0), 4.0, 3.8)
    c.poly(body, "fur")
    c.clip(body, ellipse((-0.5, -5.6), 7.5, 1.9), "fur_l")
    c.poly(capsule((5.6, -10.2), (8.6, -13.4), 3.0, 2.7), "fur")
    c.poly(ellipse((6.4, -7.4), 1.9, 2.5), "fur_l")
    for hip, paw in (((-7.4, -6.0), (-7.8, -1.0)), ((6.2, -6.0), (6.6, -1.0))):
        c.poly(capsule(hip, paw, 1.45, 1.05), "fur")
        c.poly(ellipse((paw[0] + 0.5, paw[1] + 0.25), 1.4, 0.8), "fur_l")
    c.poly(ellipse((9.4, -14.8), 3.9, 3.6), "fur")
    c.poly(ellipse((12.7, -13.5), 2.5, 1.85), "fur_l")
    c.poly(ellipse((14.7, -14.2), 0.85, 0.68), "outline")
    c.poly(ribbon(curve([(12.4, -12.6), (13.4, -12.1), (14.4, -12.6)]), 0.14, 0.14), "fur_d")
    c.dot((10.4, -16.2), "eye", 1, 2)
    c.poly(smooth([(6.4, -17.8), (8.8, -18.2), (8.5, -13.6), (6.4, -12.2), (5.2, -14.8)], 2), "fur_d")
    c.poly(capsule((5.3, -12.3), (9.2, -10.9), 0.75), "red")
    c.poly(smooth([(5.6, -12.0), (9.3, -10.6), (7.7, -7.9)], 1), "red")
    return c.finish(outline="outline")


def main() -> None:
    for zone, decor, width in (("forest", forest_items(), 160), ("ember", ember_items(), 256), ("grove", grove_items(), 200)):
        atlas, rects = pack([(d["name"], d["image"]) for d in decor], width=width)
        save(atlas, "sprites", "decor", f"{zone}_decor.png")
        items = [{**{k: v for k, v in d.items() if k != "image"}, "rect": rects[d["name"]]} for d in decor]
        save_json({"image": f"{zone}_decor.png", "scale": 1.0 / PPU, "items": items}, "sprites", "decor", f"{zone}_decor.json")

    frames = 8
    fire = Image.new("RGBA", (FIRE_FRAME * frames, FIRE_FRAME * 2), (0, 0, 0, 0))
    for f in range(frames):
        fire.paste(campfire_frame(f, frames), (f * FIRE_FRAME, 0))
    fire.paste(campfire_frame(0, frames, lit=False), (0, FIRE_FRAME))
    save(fire, "sprites", "props", "campfire.png")
    save_json({"image": "campfire.png", "frame_w": FIRE_FRAME, "frame_h": FIRE_FRAME, "scale": 1.0,
               "animations": {"burn": {"row": 0, "frames": frames, "fps": 10, "loop": True},
                              "unlit": {"row": 1, "frames": 1, "fps": 1, "loop": False}}}, "sprites", "props", "campfire.json")
    save(dog(), "sprites", "dog", "dog_concept.png")
    print("decoracao, fogueira e cachorro: ok")


if __name__ == "__main__":
    main()
