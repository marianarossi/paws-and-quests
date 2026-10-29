from __future__ import annotations

import math
import os
import sys

from PIL import Image

from gen_bg_ember import H, W, gradient, lerp, streak
from gen_bg_grove import Sheet
from gen_bg_hollow import fan
from vec import ASSETS, DOCS_PREVIEW, hash01, rgba, save
from zonekit import Art, cypress, temple

ZONE = "olympus_dawn"
HORIZON = 266
SUN = (414, 240, 25)
SKY = [(0, "#3d58b4"), (44, "#5672cc"), (88, "#7f8ade"), (128, "#a898e2"), (164, "#d2a4dc"), (196, "#f2adc8"),
       (224, "#fdbcb0"), (248, "#ffd4a4"), (HORIZON, "#ffe8b4"), (H, "#fff6d8")]

PEACH = ("#fffbe8", "#ffe4c8", "#fcc4b4", "#eaa0b0")
GOLD = ("#fffde4", "#ffecb0", "#ffcf9c", "#f4a8a0")
ROSE = ("#fff2f0", "#ffd0d8", "#f4a8c4", "#d488b8")
LILAC = ("#f6ecff", "#dcc6f6", "#b49ee6", "#8c80d0")
PERI = ("#e8f0ff", "#bccaf6", "#93a4e6", "#7284d0")
MINT = ("#f2fff6", "#cdf2e4", "#9bdcd2", "#76b6cc")
MARBLE = {"body": "#dfc9c8", "lit": "#f8eade", "dark": "#b99aae", "joint": "#9c7f9c", "ivy": "#5ea870", "ivy_l": "#a4dc8c", "bloom": "#fff0f4"}


def blank() -> Image.Image:
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def dot(px, x: float, y: float, color: tuple) -> None:
    if 0 <= int(y) < H:
        px[int(x) % W, int(y)] = color


def tones(colors: tuple) -> tuple:
    return tuple(rgba(c) for c in colors)


def sky() -> Image.Image:
    img = Image.new("RGBA", (W, H))
    px = img.load()
    sx, sy, r = SUN
    glow, warm = rgba("#fff4c4"), rgba("#ffd0b8")
    for y in range(H):
        row = gradient(SKY, y)
        for x in range(W):
            d = math.hypot((x - sx) * 0.7, (y - sy) * 1.2) / 190.0
            c = lerp(row, glow, (1.0 - d) ** 2.0 * 0.6) if d < 1.0 else row
            far = math.hypot(x - sx, y - sy)
            if y < sy and far > 40:
                ang = math.atan2(sy - y, x - sx)
                if fan(ang * 9.0, 31) > 0.62:
                    c = lerp(c, warm, 0.1 * max(0.0, 1.0 - far / 330.0))
            px[x, y] = c
    for i in range(46):
        x, y = int(hash01(i, 1, 75) * W), int(hash01(i, 2, 75) ** 1.6 * 80)
        px[x, y] = lerp(rgba("#ffffff"), px[x, y], 0.25 + 0.75 * (y / 80.0))
    for i, (x, y, length, thick) in enumerate([(150, 196, 190, 5), (560, 214, 170, 5), (300, 230, 240, 4), (60, 242, 150, 3), (480, 246, 200, 3)]):
        streak(px, x, y, length, thick, 700 + i, tones(("#e89cc0", "#f8b4c0", "#ffd8b8", "#fff4d0")))
    for y in range(sy - r, sy + r + 1):
        for x in range(sx - r, sx + r + 1):
            d = math.hypot(x - sx, y - sy)
            if d <= r and 0 <= y < H:
                px[x, y] = rgba("#fffdf0" if d < r - 5 else "#fff6cc" if d < r - 2 else "#ffe9a0")
    return img


def puff(img: Image.Image, discs: list, base: int, colors: tuple, light: tuple, seed: int, bands: tuple = (5.0, 15.0),
         flood: bool = False, deep: str | None = None, deep_h: int = 60, haze: str | None = None, haze_h: int = 0) -> None:
    px = img.load()
    rows = [bytearray(W) for _ in range(H)]
    y_top = H
    for cx, cy, r in discs:
        for y in range(max(0, int(cy - r)), min(H - 1, base, int(cy + r)) + 1):
            half = math.sqrt(max(0.0, r * r - (y - cy) ** 2))
            row = rows[y]
            for x in range(int(cx - half), int(cx + half) + 1):
                row[x % W] = 1
        y_top = min(y_top, max(0, int(cy - r)))
    if flood:
        for y in range(base, H):
            rows[y] = bytearray(b"\x01" * W)
    rim, lit, body, shade = tones(colors)
    lx, ly = light
    norm = math.hypot(lx, ly)
    lx, ly = lx / norm, ly / norm
    reach = int(bands[1] + 4)
    last = H - 1 if flood else min(H - 1, base)
    for y in range(y_top, last + 1):
        row = rows[y]
        for x in range(W):
            if not row[x]:
                continue
            d = reach + 1
            for k in range(1, reach + 1):
                yy = int(round(y + ly * k))
                if yy < 0 or (yy <= last and not rows[yy][int(round(x + lx * k)) % W]):
                    d = k
                    break
                if yy > last:
                    break
            wob = (fan(x * 0.09 + y * 0.05, seed) - 0.5) * 5.0
            if d <= 1 and hash01(x // 2, y // 2, seed) < 0.9:
                c = rim
            elif d + wob < bands[0]:
                c = lit
            elif d + wob < bands[1]:
                c = body
            else:
                c = shade
            if deep and y > base:
                t = (y - base + (fan(x * 0.05, seed + 1) - 0.5) * 10.0) / deep_h
                c = lerp(c, rgba(deep), min(1.0, max(0.0, round(t * 5.0) / 5.0)))
            if haze and y > base - haze_h:
                t = (y - (base - haze_h) + (fan(x * 0.04, seed + 2) - 0.5) * 16.0) / haze_h
                c = lerp(c, rgba(haze), min(1.0, max(0.0, round(t * 9.0) / 9.0)) * 0.88)
            px[x, y] = c


def tower(seed: int, cx: float, base: float, width: float, height: float, lean: float = 0.0, soft: bool = False) -> list:
    discs = []
    n = int(9 + width / 10)
    for i in range(n):
        u = (i + 0.5) / n * 2 - 1 + (hash01(i, 1, seed) - 0.5) * 0.14
        prof = max(0.0, 1.0 - abs(u) ** 1.7) * (0.5 + 0.5 * fan(u * 2.6 + 3.0, seed))
        top = height * prof
        r = width * (0.05 + 0.065 * hash01(i, 2, seed)) * (0.55 + 0.65 * prof)
        x = cx + u * width / 2 + lean * top
        y = base - top
        while y < (base - r * 0.45 if soft else base + r) or y == base - top:
            k = len(discs)
            discs.append((x + (hash01(k, 3, seed) - 0.5) * r * 0.9, y, r * (0.85 + 0.35 * hash01(k, 4, seed))))
            y += r * 0.85
    return discs


def mass(img: Image.Image, seed: int, cx: float, base: int, width: float, height: float, palettes: tuple, light: tuple,
         haze: str | None = None, haze_h: int = 0, scale: float = 1.0, soft: bool = False) -> None:
    bands = (5.0 * scale, 15.0 * scale)
    cut = base + 40 if soft else base
    side = 1 if hash01(seed, 6) < 0.5 else -1
    tiers = [(cx, width, height, 1.0), (cx + side * width * 0.12, width * 0.8, height * 0.62, 0.7), (cx - side * width * 0.16, width * 0.62, height * 0.36, 0.45)]
    for k, (tx, tw, th, fade) in enumerate(tiers):
        body = tower(seed + k * 20, tx, base, tw, th, soft=soft)
        if k == 0:
            body += tower(seed + 1, tx + tw * (hash01(seed, 5) - 0.5) * 0.5, base - th * 0.42, tw * 0.42, th * 0.6)
            body += tower(seed + 2, tx - tw * 0.26, base - th * 0.2, tw * 0.3, th * 0.45)
        puff(img, body, cut, palettes[k], light, seed + k * 20, bands, haze=haze, haze_h=int(haze_h * fade))
        for j in range(6 if k == 0 else 4):
            s = seed + k * 20 + 5 + j
            u = (j + 0.5) / (6 if k == 0 else 4) * 2 - 1 + (hash01(s, 1) - 0.5) * 0.3
            lift = th * (1.0 - abs(u) ** 1.5) * (0.12 + 0.42 * hash01(s, 2))
            pal = palettes[min(2, k + 1)] if hash01(s, 3) < 0.4 else palettes[k]
            puff(img, tower(s, tx + u * tw * 0.36, base - lift, tw * (0.24 + 0.14 * hash01(s, 4)), th * (0.2 + 0.14 * hash01(s, 5)), soft=soft),
                 cut, pal, light, s, bands, haze=haze, haze_h=int(haze_h * fade))


def to_sun(cx: float, cy: float) -> tuple:
    dx, dy = SUN[0] - cx, SUN[1] - cy
    n = math.hypot(dx, dy) or 1.0
    return (dx / n * 0.75, dy / n * 0.3 - 0.75)


def towers() -> Image.Image:
    img = blank()
    haze = "#ffd8b8"
    for seed, cx, width, height, pals in ((11, 120, 300, 232, (PERI, LILAC, ROSE)), (27, 548, 250, 176, (LILAC, ROSE, PEACH)),
                                          (43, 318, 170, 96, (ROSE, PEACH, GOLD))):
        mass(img, seed, cx, HORIZON + 6, width, height, pals, to_sun(cx, HORIZON - height * 0.5), haze, 110)
    return img


def drifting() -> Image.Image:
    img = blank()
    for seed, cx, base, width, height, pals in ((61, 250, 272, 150, 62, (MINT, PERI, LILAC)), (73, 486, 268, 120, 50, (GOLD, PEACH, ROSE)),
                                                (85, 30, 262, 130, 54, (PEACH, ROSE, LILAC)), (97, 610, 176, 90, 34, (MINT, LILAC, PERI))):
        mass(img, seed, cx, base, width, height, pals, to_sun(cx, base - height * 0.5), scale=0.6, soft=True)
    return img


def birds() -> Image.Image:
    img = Image.new("RGBA", (W, H * 2), (0, 0, 0, 0))
    px = img.load()
    body, far = rgba("#6c5a94"), rgba("#9484b4")
    up = ((-3, -2), (-2, -1), (-1, 0), (0, 1), (1, 0), (2, -1), (3, -2))
    down = ((-3, 2), (-2, 1), (-1, 0), (0, 0), (1, 0), (2, 1), (3, 2))
    flock = [(0, 0), (-9, -6), (-10, 7), (-19, -11), (-21, 13), (-30, -17)]
    for fx, fy, small in ((180, 110, False), (470, 70, True), (600, 150, True)):
        for k, (dx, dy) in enumerate(flock[:6 if not small else 4]):
            cx, cy = fx + dx, fy + dy + (k % 2)
            for frame, wings in enumerate((up, down) if k % 2 == 0 else (down, up)):
                for wx, wy in wings:
                    if small and abs(wx) == 3:
                        continue
                    px[(cx + wx) % W, cy + wy + frame * H] = far if small else body
    return img


def bank(seed: int, base: int, amp: int, radii: tuple, colors: tuple, deep: str, rows: int = 3, deep_h: int = 60) -> Image.Image:
    img = blank()
    for row in range(rows):
        lift = amp * (rows - 1 - row) / max(1, rows - 1)
        step = (radii[0] + radii[1]) * 0.55
        n = int(W / step)
        discs = []
        for i in range(n):
            r = radii[0] + (radii[1] - radii[0]) * hash01(i, 1, seed + row * 7)
            discs.append((i * W / n + (hash01(i, 2, seed + row * 7) - 0.5) * step * 0.6,
                          base - lift + r * 0.35 - amp * 0.7 * hash01(i, 3, seed + row * 7), r))
        line = int(base - lift + radii[1] * 0.5)
        puff(img, discs, line, colors, (-0.45, -0.9), seed + row, (4.0, 12.0), flood=True, deep=deep if row == rows - 1 else None, deep_h=deep_h)
    return img


def isle(img: Image.Image, cx: int, top: int, width: int, depth: int, seed: int, pal: dict, falls: tuple = ()) -> None:
    px = img.load()
    half = width / 2
    for x in range(int(cx - half), int(cx + half) + 1):
        u = (x - cx) / half
        edge = 1.0 - abs(u)
        t0 = top + (2 if edge < 0.04 else 1 if edge < 0.1 else 0)
        bot = t0 + 3 + depth * edge ** 0.7 * (0.5 + 0.5 * fan(x * 0.07, seed)) + depth * 0.22 * fan(x * 0.45, seed + 1) * min(1.0, edge * 4)
        for y in range(t0, int(bot) + 1):
            v = (y - t0) / max(1.0, bot - t0)
            if y - t0 < 2:
                c = pal["grass_l"] if y == t0 else pal["grass"]
            elif y - t0 < 3 + int(hash01(x, 1, seed) * 2):
                c = pal["grass_d"] if hash01(x, y, seed) < 0.5 else pal["soil"]
            else:
                n = fan(x * 0.15 + y * 0.03, seed + 2) + (0.25 if u < -0.2 else -0.15 if u > 0.4 else 0.0)
                c = pal["rock_l"] if n > 0.7 and v < 0.55 else pal["rock_d"] if (n < 0.34 or v > 0.72) else pal["rock"]
                if int(y + fan(x * 0.06, seed + 3) * 5) % 8 == 0:
                    c = pal["rock_d"]
            dot(px, x, y, rgba(c))
        if hash01(x, 2, seed) < 0.12 and edge > 0.05:
            for j in range(3 + int(hash01(x, 3, seed) * 9)):
                dot(px, x, int(bot) + 1 + j, rgba(pal["grass"] if j % 3 else pal["grass_l"]))
    water, foam = rgba(pal.get("water", "#dff4ff")), rgba("#ffffff")
    for k, f in enumerate(falls):
        x0 = int(cx + f * half * 0.82)
        length = 46 + int(hash01(k, 4, seed) * 40)
        for j in range(length):
            t = j / length
            for dx in range(2 if width > 70 else 1):
                if t < 0.6 or hash01(x0 + dx, j, seed) > (t - 0.6) / 0.4:
                    dot(px, x0 + dx, top + 2 + j, foam if (j + dx * 2 + k) % 5 < 2 else water)
        for j in range(10):
            dot(px, x0 + int((hash01(j, 5, seed + k) - 0.5) * 10), top + length + int(hash01(j, 6, seed + k) * 8), foam)


def peaks(img: Image.Image, seed: int, base: int, count: int, pal: tuple) -> None:
    px = img.load()
    body, snow, dark = (rgba(c) for c in pal)
    for i in range(count):
        cx = int((i + 0.2 + 0.6 * hash01(i, 1, seed)) * W / count)
        h = 10 + int(hash01(i, 2, seed) * 20)
        for y in range(h):
            half = int(y * (0.7 + 0.5 * hash01(i, 3, seed))) + (1 if hash01(i, y, seed) < 0.4 else 0)
            for dx in range(-half, half + 1):
                c = snow if (y < h * 0.4 and dx <= 0) else dark if dx > half * 0.2 else body
                dot(px, cx + dx, base - h + y, c)


def far() -> Image.Image:
    img = blank()
    peaks(img, 5, HORIZON + 6, 7, ("#c4a8d4", "#f8ecf4", "#a88cc4"))
    pal = {"grass_l": "#d4f0b8", "grass": "#a8d8a0", "grass_d": "#84b894", "soil": "#d0a8a8", "rock_l": "#f0d4d0", "rock": "#d8b0c0", "rock_d": "#b890b8"}
    art = Art()
    temple(art, 216, 200, 92, 58, 6, ("#f4e4dc", "#fffaf2", "#d0b0c0"), -1)
    for x, h in ((150, 34), (162, 24), (276, 38), (290, 26)):
        cypress(art, x, 200, h, x, ("#8cbc98", "#b8dcac", "#6c9c8c"), -1)
    temple(art, 566, 168, 44, 30, 4, ("#f0dcdc", "#fff6f0", "#c8a8c0"), -1, 0.5, 3)
    cypress(art, 598, 168, 22, 7, ("#8cbc98", "#b8dcac", "#6c9c8c"), -1)
    isle(img, 220, 200, 190, 46, 21, pal, (-0.86, 0.7))
    isle(img, 572, 168, 92, 32, 22, pal, (0.5,))
    isle(img, 436, 150, 46, 18, 23, pal, (0.3,))
    img.alpha_composite(art.img)
    return img


def drum_column(px, cx: int, base: int, height: int, width: int, seed: int, broken: bool = False) -> None:
    body, lit, dark, joint = (rgba(MARBLE[k]) for k in ("body", "lit", "dark", "joint"))
    half = width // 2
    top = base - height
    for y in range(top, min(H, base)):
        drum = (y - top) // 15
        off = int(hash01(drum, 1, seed) * 3) - 1 if hash01(drum, 2, seed) < 0.3 else 0
        for dx in range(-half, half + 1):
            if broken and y < top + int(hash01((dx + half) // 3, 3, seed) * 12):
                continue
            f = (dx + half) / width
            c = lit if f < 0.24 else dark if f > 0.7 else body
            if (dx + half) % 4 == 3 and 0.06 < f < 0.94:
                c = dark if c == body else joint if c == dark else body
            if (y - top) % 15 == 14:
                c = joint
            dot(px, cx + dx + off, y, c)
    if not broken:
        for row, grow in ((1, 2), (2, 2), (3, 3), (4, 3), (5, 5), (6, 5), (7, 5)):
            for dx in range(-half - grow, half + grow + 1):
                dot(px, cx + dx, top - row, lit if dx < -half * 0.4 else dark if dx > half + grow - 2 else body)
        for sx in (-half - 3, half + 2):
            for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
                dot(px, cx + sx + dx, top - 3 + dy, joint)
    for k in range(3):
        x, y = cx - half + 2 + int(hash01(k, 4, seed) * (width - 4)), top + 10 + int(hash01(k, 5, seed) * max(1, height - 30))
        for j in range(5 + int(hash01(k, 6, seed) * 8)):
            dot(px, x + int(math.sin(j * 0.9 + k) * 1.5), y + j, joint)
    ivy(px, cx - half, top + (8 if broken else 0), base, width, seed + 9)


def ivy(px, x0: int, top: int, base: int, width: int, seed: int) -> None:
    leaf, light, bloom = rgba(MARBLE["ivy"]), rgba(MARBLE["ivy_l"]), rgba(MARBLE["bloom"])
    start = top + int((0.15 + 0.4 * hash01(seed, 1)) * (base - top))
    for y in range(start, min(H, base)):
        x = x0 + int(fan(y * 0.07, seed) * width * 0.9)
        dot(px, x, y, leaf)
        if hash01(y, 2, seed) < 0.6:
            side = -1 if hash01(y, 3, seed) < 0.5 else 1
            dot(px, x + side, y, light if hash01(y, 4, seed) < 0.4 else leaf)
            dot(px, x + side * 2, y - 1, leaf)
        if hash01(y, 5, seed) < 0.05:
            dot(px, x + 1, y - 1, bloom)


def wall(px, x0: int, base: int, w: int, h: int, seed: int) -> None:
    body, lit, dark, joint = (rgba(MARBLE[k]) for k in ("body", "lit", "dark", "joint"))
    for x in range(x0, x0 + w):
        f = (x - x0) / w
        top = base - int(h * (0.45 + 0.55 * fan(f * 3.0, seed)) // 9 * 9)
        for y in range(top, min(H, base)):
            row = (base - y - 1) // 9
            bx = (x - x0 + (8 if row % 2 else 0)) % 17
            by = (base - y - 1) % 9
            c = joint if bx == 16 or by == 0 else lit if by == 8 or bx == 0 else dark if by == 1 or bx == 15 else body
            if c == body and hash01(x // 17 + row * 5, row, seed) < 0.3:
                c = dark if hash01(x, y, seed) < 0.12 else body
            dot(px, x, y, c)


def lintel(px, x0: int, x1: int, y: int, seed: int) -> None:
    body, lit, dark, joint, gold = (rgba(c) for c in (MARBLE["body"], MARBLE["lit"], MARBLE["dark"], MARBLE["joint"], "#f0c878"))
    for x in range(x0, x1 + 1):
        if x > x1 - 6 and hash01(x, 1, seed) < (x - (x1 - 6)) / 6:
            continue
        for j in range(11):
            c = lit if j < 2 else joint if j == 10 or (x - x0) % 23 == 22 else gold if j == 5 and (x // 2) % 2 else dark if j > 7 else body
            dot(px, x, y - 11 + j, c)


def isles() -> Image.Image:
    img = blank()
    px = img.load()
    pal = {"grass_l": "#c8f098", "grass": "#86cc78", "grass_d": "#5c9c70", "soil": "#c49c8c", "rock_l": "#f0dccc", "rock": "#d0b0a8", "rock_d": "#a8849c",
           "water": "#cfeeff"}
    art = Art()
    for x, h in ((64, 50), (80, 32), (506, 44)):
        cypress(art, x, 238, h, x, ("#5c9c70", "#98d088", "#44786c"), -1)
    isle(img, 112, 238, 190, 70, 31, pal, (0.8,))
    isle(img, 500, 222, 150, 60, 32, pal, (-0.82,))
    isle(img, 318, 262, 84, 34, 33, pal, (0.6,))
    img.alpha_composite(art.img)
    px = img.load()
    for cx, base, height, broken in ((126, 238, 50, False), (160, 238, 50, False), (40, 238, 22, True), (462, 222, 30, True), (536, 222, 58, False),
                                     (322, 262, 18, True)):
        drum_column(px, cx, base, height, 11, cx, broken)
    lintel(px, 116, 174, 238 - 50 - 7, 3)
    return img


def ruins() -> Image.Image:
    img = blank()
    px = img.load()
    wall(px, 186, 360, 110, 120, 5)
    wall(px, 556, 360, 76, 92, 6)
    for cx, height, broken in ((40, 196, False), (110, 196, False), (250, 96, True), (418, 150, True), (500, 228, False)):
        drum_column(px, cx, 360, height, 21, cx, broken)
    return img


def build(preview: bool = False) -> dict:
    import gen_props_olympus

    heaven = sky()
    drift = {"scale_y": 0.02}
    made = [
        ("towers", towers(), 0.02, {"autoscroll": -1.2, "scale_y": 0.01}),
        ("far", far(), 0.04, drift),
        ("sea_far", bank(3, HORIZON + 2, 14, (16, 34), ("#fffcf2", "#ffecdc", "#fdd4cc", "#f2b8c6"), "#e4a4c4"), 0.07, {"autoscroll": -2, "scale_y": 0.04, "fill": "#e4a4c4"}),
        ("drifting", drifting(), 0.1, {"autoscroll": -3, "scale_y": 0.05}),
        ("birds", birds(), 0.12, {"autoscroll": -15, "scale_y": 0.05, "flap": 3}),
        ("isles", isles(), 0.15, {"scale_y": 0.09}),
        ("sea_mid", bank(9, 304, 18, (22, 46), ("#fff6ee", "#ffdcd8", "#f4b6c8", "#d894be"), "#b884ba"), 0.22, {"autoscroll": -4, "scale_y": 0.14, "fill": "#b884ba"}),
        ("ruins", ruins(), 0.32, {"scale_y": 0.2}),
        ("sea_near", bank(15, 338, 16, (30, 60), ("#fdeaec", "#f2c4d4", "#cfa0cc", "#a284c0"), "#7866ac", deep_h=40), 0.46, {"autoscroll": -7, "scale_y": 0.3, "fill": "#7866ac"}),
    ]
    layers = []
    for name, img, scale, extra in made:
        save(img, "backgrounds", f"{ZONE}_{name}.png")
        layers.append((f"{ZONE}_{name}.png", scale, extra))
    extras = gen_props_olympus.build()
    if preview:
        out = heaven.copy()
        for name, _, _ in layers:
            out.alpha_composite(Image.open(os.path.join(ASSETS, "backgrounds", name)).convert("RGBA").crop((0, 0, W, H)))
        path = os.path.join(DOCS_PREVIEW, "olympus", "fundo.png")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        out.resize((W * 2, H * 2), Image.NEAREST).save(path)
    return dict({"sky": Sheet(heaven), "layers": layers}, **extras)


if __name__ == "__main__":
    build("--preview" in sys.argv)
    print("fundo do amanhecer no olimpo: ok (para o tema e o chao: python tools/art/gen_zones.py olympus_dawn)")
