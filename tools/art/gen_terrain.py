from __future__ import annotations

import math

from PIL import Image

from terrain_patterns import EXTRAS, PATTERNS
from vec import Canvas, capsule, ellipse, hash01, rgba, save, smooth

T = 16
HALF = T // 2
PERIOD_TILES = 16
PERIOD = T * PERIOD_TILES
PAD = 8
RADIUS = 6.0
WOBBLE = 0.24

PALETTES = {
    "forest": {
        "edge": "#151229", "gap": "#1b1634", "earth": "#292147", "earth_l": "#3a305c", "earth_d": "#211a3c",
        "stones": [("#3b3363", "#6a5e9e", "#2c2550"), ("#463c72", "#7a6eb0", "#342c5c"), ("#514683", "#8b80c2", "#3b3268"),
                   ("#2f4668", "#4f7f99", "#243653")],
        "rim": "#6d5f96", "shadow": "#1b1634",
        "grass": "#3ccb9b", "grass_l": "#a6f7c6", "grass_d": "#1f8c85", "moss": "#2a6e79", "moss_d": "#1d4f63",
        "root": "#6b4a62", "root_l": "#8d627c",
        "soil": "#4a3345", "soil_l": "#604556", "soil_d": "#37263a", "pebble": "#7a6ea8",
    },
    "ember": {
        "edge": "#1c1220", "gap": "#2c1b26", "earth": "#553430", "earth_l": "#6c4638", "earth_d": "#432829",
        "stones": [("#6a5460", "#9c8288", "#4c3c48"), ("#74606a", "#a88e90", "#544450"), ("#5e4c5c", "#8c7684", "#443644"),
                   ("#4f6a58", "#7fa07c", "#3a5046")],
        "rim": "#84584a", "shadow": "#2c1b26",
        "grass": "#4fb64c", "grass_l": "#b6ea6a", "grass_d": "#2a8648", "moss": "#3d9450", "moss_d": "#2a6c44",
        "root": "#7c4c36", "root_l": "#a26a46",
        "soil": "#6e4234", "soil_l": "#8a5a40", "soil_d": "#56322c", "pebble": "#b09484",
        "earth_chance": 0.74, "cover": "lush", "extras": ("rootlets",),
        "flowers": ["#ffe391", "#fff6e8", "#ff9c84", "#c9b6ff"], "flower_chance": 0.16,
    },
}


def wrap(v: int) -> int:
    return v % PERIOD


def noise_map(cells: int, seed: int) -> list[list[float]]:
    size = PERIOD / cells

    def value(i: int, j: int) -> float:
        return hash01(i % cells, j % cells, seed) * 2 - 1

    out = []
    for y in range(PERIOD):
        gy = (y + 0.5) / size
        y0 = int(gy)
        fy = gy - y0
        fy = fy * fy * (3 - 2 * fy)
        row = []
        for x in range(PERIOD):
            gx = (x + 0.5) / size
            x0 = int(gx)
            fx = gx - x0
            fx = fx * fx * (3 - 2 * fx)
            a = value(x0, y0) + (value(x0 + 1, y0) - value(x0, y0)) * fx
            b = value(x0, y0 + 1) + (value(x0 + 1, y0 + 1) - value(x0, y0 + 1)) * fx
            row.append(a + (b - a) * fy)
        out.append(row)
    return out


def scallops(seed: int, widths: tuple, depths: tuple, gap_chance: float = 0.0, gaps: tuple = (0,)) -> list[int]:
    out: list[int] = []
    i = 0
    while len(out) < PERIOD:
        i += 1
        if hash01(i, 1, seed) < gap_chance:
            out += [0] * gaps[int(hash01(i, 2, seed) * len(gaps))]
            continue
        w = widths[int(hash01(i, 3, seed) * len(widths))]
        d = depths[int(hash01(i, 4, seed) * len(depths))]
        out += [d if 0 < k < w - 1 or w < 3 else d - 1 for k in range(w)]
    return out[:PERIOD]


def punchy(v: float) -> float:
    return math.copysign(min(1.0, abs(v) * 1.6) ** 0.7, v)


WOB = [[punchy(0.7 * a + 0.3 * b) for a, b in zip(ra, rb)] for ra, rb in zip(noise_map(PERIOD // 10, 11), noise_map(PERIOD // 5, 12))]
GRASS_DEPTH = scallops(21, (2, 3, 3, 4, 5), (3, 4, 5, 5, 6, 7))


def blade_profile(seed: int) -> list[int]:
    out = [(0, 0, 1, 1, 1, 1, 2, 2)[int(hash01(x, 5, seed) * 8)] for x in range(PERIOD)]
    x = k = 0
    while x < PERIOD - 6:
        k += 1
        x += 7 + int(hash01(k, 1, seed) * 20)
        w = 2 + int(hash01(k, 2, seed) * 4)
        for i in range(w):
            if x + i < PERIOD:
                out[x + i] = max(out[x + i], 2 + int(hash01(k, i, seed + 1) * 3))
        x += w
    return out


BLADES = blade_profile(22)
MOSS_HANG = scallops(23, (2, 3, 4), (1, 2, 2, 3), 0.5, (3, 5, 8, 11))
ROOT_HANG = [(3 + int(hash01(x, 6, 24) * 5)) if hash01(x, 7, 24) < 0.06 else 0 for x in range(PERIOD)]
ROOTLETS = [(2 + int(hash01(x, 8, 25) * 3)) if hash01(x, 9, 25) < 0.14 else 0 for x in range(PERIOD)]
SIDE_MOSS = scallops(26, (3, 4, 5, 6), (2, 2, 3), 0.62, (6, 9, 13, 18))
SOIL_DEPTH = scallops(27, (3, 4, 5, 6, 7), (13, 14, 15, 15, 16, 17))
SOIL_FADE = 24
MASKS = 19


def bump_profile(seed: int, widths: tuple = (6, 8, 10, 13), heights: tuple = (2, 3, 3, 4, 5)) -> list[int]:
    out: list[int] = []
    i = 0
    while len(out) < PERIOD:
        i += 1
        w = widths[int(hash01(i, 1, seed) * len(widths))]
        h = heights[int(hash01(i, 2, seed) * len(heights))]
        out += [max(1, round(h * math.sqrt(max(0.0, 1 - ((k + 0.5 - w / 2) / (w / 2)) ** 2)))) for k in range(w)]
    return out[:PERIOD]


def spike_profile(seed: int, gap: tuple = (3, 12), height: tuple = (3, 7), chance: float = 1.0) -> list[int]:
    out = [0] * PERIOD
    x = k = 0
    while x < PERIOD - 6:
        k += 1
        x += gap[0] + int(hash01(k, 1, seed) * (gap[1] - gap[0]))
        h = height[0] + int(hash01(k, 2, seed) * (height[1] - height[0] + 1))
        if hash01(k, 3, seed) < chance:
            for i, v in enumerate((max(1, h // 2), h, max(1, h - 3))):
                if x + i < PERIOD:
                    out[x + i] = v
        x += 3
    return out


COVERS = {
    "grass": (GRASS_DEPTH, BLADES),
    "lush": (scallops(45, (2, 3, 3, 4, 5), (4, 5, 6, 6, 7, 7)), [b + 1 + (hash01(x, 6, 46) < 0.3) for x, b in enumerate(blade_profile(46))]),
    "snow": (scallops(31, (5, 6, 8, 10), (4, 5, 6, 7)), [0] * PERIOD),
    "thin": (scallops(32, (4, 6, 8, 10), (2, 2, 3, 3)), [1 if hash01(x, 3, 33) < 0.1 else 0 for x in range(PERIOD)]),
    "cloud": (scallops(34, (5, 7, 9, 12), (4, 5, 6, 7)), bump_profile(35)),
    "water": ([3] * PERIOD, [1 if hash01(x // 2, 4, 36) < 0.16 else 0 for x in range(PERIOD)]),
    "shards": (scallops(37, (3, 4, 6), (2, 2, 3)), spike_profile(38)),
}
HANGS = {
    "ice": spike_profile(39, (2, 9), (3, 9)),
    "shards": spike_profile(40, (5, 16), (3, 7), 0.7),
    "wisps": scallops(41, (4, 6, 8), (1, 2, 3), 0.3, (3, 5)),
    "drips": spike_profile(42, (9, 26), (2, 5), 0.6),
}


def soil_color(pal: dict, px: int, py: int) -> tuple:
    dash = hash01(px // 2, py, 51)
    if hash01(px, py, 52) < 0.012:
        return rgba(pal["pebble"])
    return rgba(pal["soil_l"] if dash < 0.09 else pal["soil_d"] if dash < 0.2 else pal["soil"])


def stone_pattern(pal: dict, seed: int = 31) -> list[list[tuple]]:
    nx, ny = PERIOD // 13, PERIOD // 10
    cw, ch = PERIOD / nx, PERIOD / ny
    seeds: list[tuple] = []
    cells: dict[tuple, int] = {}
    for j in range(ny):
        for i in range(nx):
            if hash01(i, j, seed) < 0.16:
                continue
            sx = (i + 0.5 + (0.5 if j % 2 else 0.0) + (hash01(i, j, seed + 1) - 0.5) * 0.7) * cw
            sy = (j + 0.5 + (hash01(i, j, seed + 2) - 0.5) * 0.7) * ch
            tone = int(hash01(i, j, seed + 4) * 3)
            if hash01(i, j, seed + 5) < 0.13:
                tone = 3
            if hash01(i, j, seed + 3) < pal.get("earth_chance", 0.3):
                tone = -1
            cells[(i, j)] = len(seeds)
            seeds.append((sx % PERIOD, sy % PERIOD, tone))

    ident = [[0] * PERIOD for _ in range(PERIOD)]
    gap = [[False] * PERIOD for _ in range(PERIOD)]
    for y in range(PERIOD):
        cj = int(y / ch)
        for x in range(PERIOD):
            ci = int(x / cw)
            d1 = d2 = 1e9
            best = 0
            for dj in range(-2, 3):
                for di in range(-3, 3):
                    k = cells.get(((ci + di) % nx, (cj + dj) % ny))
                    if k is None:
                        continue
                    dx = abs(x + 0.5 - seeds[k][0])
                    dy = abs(y + 0.5 - seeds[k][1])
                    dx = min(dx, PERIOD - dx)
                    dy = min(dy, PERIOD - dy) * 1.25
                    d = dx * dx + dy * dy
                    if d < d1:
                        d1, d2, best = d, d1, k
                    elif d < d2:
                        d2 = d
            ident[y][x] = best
            gap[y][x] = math.sqrt(d2) - math.sqrt(d1) < 1.5

    def other(x: int, y: int, k: int) -> bool:
        x, y = wrap(x), wrap(y)
        return gap[y][x] or ident[y][x] != k

    out = [[(0, 0, 0, 0)] * PERIOD for _ in range(PERIOD)]
    for y in range(PERIOD):
        for x in range(PERIOD):
            k = ident[y][x]
            tone = seeds[k][2]
            h = hash01(x, y, seed + 7)
            if tone < 0:
                dash = hash01(x // 2, y, seed + 8)
                col = pal["earth_l"] if dash < 0.07 else pal["earth_d"] if dash < 0.16 else pal["earth"]
            elif gap[y][x]:
                col = pal["gap"]
            else:
                base, light, dark = pal["stones"][tone]
                if other(x - 1, y - 1, k) or other(x, y - 1, k):
                    col = light
                elif other(x + 1, y + 1, k) or other(x, y + 1, k):
                    col = dark
                elif h < 0.05:
                    col = dark
                elif h < 0.08:
                    col = light
                else:
                    col = base
            out[y][x] = rgba(col)
    return out


def quad_bit(x: float, y: float) -> int:
    return (1 if x < HALF else 2) if y < HALF else (4 if x < HALF else 8)


_DISCS: dict[float, list] = {}


def _disc(radius: float) -> list:
    if radius not in _DISCS:
        _DISCS[radius] = [(dx * 0.5, dy * 0.5) for dx in range(-14, 15) for dy in range(-14, 15) if math.hypot(dx * 0.5, dy * 0.5) <= radius]
    return _DISCS[radius]


def coverage(mask: int, radius: float = RADIUS) -> tuple[list, list]:
    n = T + 2 * PAD
    disc = _disc(radius)
    f = [[0.0] * (n + 2) for _ in range(n + 2)]
    for j in range(n + 2):
        for i in range(n + 2):
            cx, cy = i - PAD - 1 + 0.5, j - PAD - 1 + 0.5
            hit = sum(1 for dx, dy in disc if mask & quad_bit(cx + dx, cy + dy))
            f[j][i] = hit / len(disc)
    cover = [[f[j + 1][i + 1] for i in range(n)] for j in range(n)]
    amp = [[0.0] * n for _ in range(n)]
    for j in range(n):
        for i in range(n):
            gx = f[j + 1][i + 2] - f[j + 1][i]
            gy = f[j + 2][i + 1] - f[j][i + 1]
            g = math.hypot(gx, gy)
            if g < 1e-6:
                continue
            ny_out = -gy / g
            amp[j][i] = WOBBLE * (1.0 - max(0.0, -ny_out)) ** 2 * (1.0 + 0.7 * max(0.0, ny_out))
    return cover, amp


def make_tile(mask: int, tx: int, ty: int, cover: list, amp: list, pattern: list, pal: dict) -> Image.Image:
    soil_above = mask - 15 if mask > 15 else 0
    mask = min(mask, 15)
    n = T + 2 * PAD
    ox, oy = tx * T - HALF - PAD, ty * T - HALF - PAD
    wob = pal.get("wobble", 1.0)
    solid = [[cover[j][i] + amp[j][i] * wob * WOB[wrap(oy + j)][wrap(ox + i)] > 0.5 for i in range(n)] for j in range(n)]
    cover_name = pal.get("cover", "grass")
    cover_depth, blades = COVERS[cover_name]
    band = pal.get("band", "soil")
    side_moss = pal.get("side_moss", True)

    def s(x: int, y: int) -> bool:
        return solid[y + PAD][x + PAD]

    def ground_column(x: int) -> bool:
        return bool(mask & quad_bit(x, T - 1)) and not mask & quad_bit(x, 0)

    tops: dict[int, int] = {}

    def top_of(x: int) -> int:
        if x not in tops:
            y = HALF
            while y > -PAD + 1 and s(x, y - 1):
                y -= 1
            while y < T + PAD - 1 and not s(x, y):
                y += 1
            tops[x] = y
        return tops[x]

    def grass_at(x: int, y: int) -> str | None:
        if not (-PAD < y < T + PAD and -PAD <= x < T + PAD) or not s(x, y) or not ground_column(x):
            return None
        px = wrap(ox + PAD + x)
        rel, depth, top = y - HALF, cover_depth[px], top_of(x)
        if rel >= depth:
            return None
        if y == top:
            return "grass_l"
        if rel == depth - 1:
            return "grass_d"
        h = hash01(px, rel, 41)
        if y == top + 1:
            return "grass_l" if h < 0.3 else "grass"
        return "moss" if h < 0.12 else "grass"

    def corner_tuft(x: int, y: int) -> str | None:
        if mask not in (4, 8) or not pal.get("corner_tuft", True):
            return None
        out_dir = 1 if mask == 4 else -1
        dx, dy = (x + 0.5 - HALF) * out_dir - 0.4, y + 0.5 - HALF - 2.6
        d = math.hypot(dx, dy * 0.9)
        if d > 3.3:
            return None
        if dy < -1.4 or (dy < 0 and dx < -1.0):
            return "grass_l"
        return "grass_d" if d > 2.3 and dy > 0.4 else "grass"

    img = Image.new("RGBA", (T, T), (0, 0, 0, 0))
    out = img.load()
    for y in range(T):
        for x in range(T):
            px, py = wrap(ox + PAD + x), wrap(oy + PAD + y)
            tuft = corner_tuft(x, y)
            if tuft:
                out[x, y] = rgba(pal[tuft])
                continue
            if s(x, y):
                grass = grass_at(x, y)
                if grass:
                    out[x, y] = rgba(pal[grass])
                    continue
                col = pattern[py][px]
                if band == "soil" and soil_above & (1 if x < HALF else 2):
                    depth = y + HALF
                    is_gap = col == rgba(pal["gap"])
                    if depth < SOIL_DEPTH[px]:
                        if is_gap or depth < SOIL_DEPTH[px] - 3 or hash01(px // 2, py // 2, 61) < 0.55:
                            col = soil_color(pal, px, py)
                    elif is_gap and hash01(px, py, 62) > (depth - SOIL_DEPTH[px]) / max(1.0, SOIL_FADE - SOIL_DEPTH[px]) - 0.15:
                        col = rgba(pal["soil_d"])
                if ground_column(x) and y >= HALF:
                    dt, depth = y - HALF, cover_depth[px]
                    if band == "soil":
                        col = soil_color(pal, px, py)
                        if dt == depth:
                            col = rgba(pal["shadow"])
                        elif 0 < dt - depth <= ROOTLETS[px]:
                            col = rgba(pal["root_l"] if (dt + px) % 3 == 0 else pal["root"])
                    elif band == "frieze":
                        k = dt - depth
                        if k == 0:
                            col = rgba(pal["rim"])
                        elif k in (1, 2):
                            col = rgba(pal["frieze"] if px % 5 < 3 else pal["shadow"])
                        elif k == 3:
                            col = rgba(pal["shadow"])
                    elif dt == depth and pal.get("cover_shadow", True):
                        col = rgba(pal["shadow"])
                moss = SIDE_MOSS[py] if side_moss else 0
                if not (s(x - 1, y) and s(x + 1, y) and s(x, y - 1) and s(x, y + 1)):
                    side = not (s(x - 1, y) and s(x + 1, y))
                    col = rgba(pal["moss_d"] if side and moss else pal["edge"])
                elif not (s(x - 2, y) and s(x, y - 2) and s(x - 1, y - 1)):
                    col = rgba(pal["moss"] if moss and not s(x - 2, y) else pal["rim"])
                elif not (s(x + 2, y) and s(x, y + 2) and s(x + 1, y + 1)):
                    col = rgba(pal["moss"] if moss and not s(x + 2, y) else pal["shadow"])
                out[x, y] = col
                continue

            if pal.get("blades", True) and ground_column(x):
                hgt = top_of(x) - y
                if 1 <= hgt <= blades[px]:
                    tip = hgt == blades[px] and (hgt > 1 or cover_name == "water")
                    key = "grass_l" if tip else ("blade" if "blade" in pal else "grass")
                    if tip and hgt > 1 and pal.get("flowers") and hash01(px, 0, 44) < pal.get("flower_chance", 0.3):
                        key = pal["flowers"][int(hash01(px, 1, 44) * len(pal["flowers"]))]
                    out[x, y] = rgba(pal.get(key, key))
                    continue
            lip = [g for g in (grass_at(x - 1, y), grass_at(x + 1, y)) if g]
            if lip and y - HALF <= 2:
                out[x, y] = rgba(pal["grass_d" if y - HALF == 2 else lip[0]])
                continue
            if pal.get("tufts", True) and side_moss and SIDE_MOSS[py] >= 3 and (s(x - 1, y) != s(x + 1, y)) and not grass_at(x - 1, y) and not grass_at(x + 1, y):
                if hash01(px, py, 43) < 0.7 and abs(x - HALF + 0.5) < 5:
                    out[x, y] = rgba(pal["moss"])
                    continue
            above = next((k for k in range(1, PAD) if s(x, y - k)), 0)
            hang = pal.get("hang", True)
            if hang is True and above and not ground_column(x):
                if above <= ROOT_HANG[px]:
                    out[x, y] = rgba(pal["root_l"] if above == ROOT_HANG[px] else pal["root"])
                elif above <= MOSS_HANG[px]:
                    out[x, y] = rgba(pal["moss_d"] if above == MOSS_HANG[px] else pal["moss"])
            elif hang and above and not ground_column(x) and above <= HANGS[hang][px]:
                out[x, y] = rgba(pal["hang_tip"] if above == HANGS[hang][px] else pal["hang_body"])
    return img


def interior(pal: dict) -> list[list[tuple]]:
    name = pal.get("pattern", "stones")
    rows = stone_pattern(pal) if name == "stones" else PATTERNS[name](pal, **pal.get("pattern_args", {}))
    for extra in pal.get("extras", ()):
        rows = EXTRAS[extra](rows, pal)
    return rows


def make_terrain(theme: str) -> None:
    pal = PALETTES[theme]
    pattern = interior(pal)
    atlas = Image.new("RGBA", (T * 4 * MASKS, T * 64), (0, 0, 0, 0))
    for mask in range(1, MASKS):
        cover, amp = coverage(min(mask, 15), pal.get("radius", RADIUS))
        for ty in range(PERIOD_TILES):
            for tx in range(PERIOD_TILES):
                tile = make_tile(mask, tx, ty, cover, amp, pattern, pal)
                atlas.paste(tile, (((tx % 4) * MASKS + mask) * T, ((tx // 4) * 16 + ty) * T))
    save(atlas, "tiles", f"{theme}_terrain.png")


PLATFORM_TOP = 3


def make_platform(theme: str) -> None:
    top = PLATFORM_TOP
    c = Canvas(48, 16)
    mid = top + 3.6
    body = capsule((4.2, mid), (43.8, mid), 3.5)
    c.poly(body, "wood")
    c.clip(body, [(0, top + 4.6), (48, top + 4.6), (48, 16), (0, 16)], "wood_d")
    c.clip(body, [(0, 0), (48, 0), (48, top + 1.7), (0, top + 1.7)], "wood_l")
    for x in (3.2, 44.8):
        c.poly(ellipse((x, mid), 2.3, 3.1), "#dcb787")
        c.poly(ellipse((x, mid), 1.2, 1.8), "wood_l")
        c.dot((x - 0.5, mid - 0.5), "wood", 1, 1)
    for i, (x, w) in enumerate(((7, 3), (11, 2), (19, 3), (24, 4), (28, 2), (35, 3), (39, 2))):
        c.dot((x, top + 2 + i % 2), "wood_d", w, 1)
        c.dot((x + 1, top + 5), "#3f2a26", w - 1, 1)
    for x in (13, 36):
        c.dot((x, top + 3), "#3f2a26", 2, 2)
        c.dot((x, top + 3), "wood_d", 1, 1)
    for i, (x, w) in enumerate(((8.5, 2.8), (21.0, 2.2), (26.5, 3.0), (40.5, 2.6))):
        c.poly(ellipse((x, top + 0.5), w, 1.4), "grass")
        c.poly(ellipse((x - 0.6, top + 0.1), w * 0.55, 0.7), "grass_l")
        c.dot((x + 1, top - 1), "grass", 1, 1)
        c.dot((x - 1, top - 2 + i % 2), "grass_l", 1, 2 - i % 2)
    for i, (x, length) in enumerate(((6, 2), (10, 3), (18, 2), (23, 4), (29, 2), (34, 3), (42, 5))):
        c.dot((x, top + 7), "grass_d", 2, 1)
        c.dot((x, top + 8), "moss" if i % 3 else "#6b4a62", 1, length)
    for x, h in ((30, 2), (38, 1)):
        c.dot((x, top - h), "mint_l", 1, h)
        c.dot((x - 1, top - h - 1), "mint", 3, 1)
        c.dot((x, top - h - 2), "mint_l", 1, 1)
    save(c.finish(outline="outline"), "tiles", f"{theme}_platform.png")


def main() -> None:
    make_terrain("forest")
    make_terrain("ember")
    make_platform("forest")
    print("terreno: ok")


if __name__ == "__main__":
    main()
