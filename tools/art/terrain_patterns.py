from __future__ import annotations

import math

from PIL import Image, ImageDraw

from vec import hash01, rgba

PERIOD = 256


def _rows(img: Image.Image) -> list[list[tuple]]:
    data = list(img.convert("RGBA").getdata())
    return [data[y * PERIOD:(y + 1) * PERIOD] for y in range(PERIOD)]


def _canvas(color) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (PERIOD, PERIOD), rgba(color))
    return img, ImageDraw.Draw(img)


def _tiled(draw_one) -> None:
    for dy in (-PERIOD, 0, PERIOD):
        for dx in (-PERIOD, 0, PERIOD):
            draw_one(dx, dy)


def marble(pal: dict, seed: int = 71) -> list[list[tuple]]:
    img, d = _canvas(pal["gap"])
    px = img.load()
    heights = (14, 18, 12, 20)
    widths = (32, 40, 24, 32, 40, 24, 32, 32)
    y = 0
    row = 0
    while y < PERIOD:
        h = heights[row % 4]
        x = -int(hash01(row, 1, seed) * 24)
        col = 0
        while x < PERIOD:
            w = widths[(col + row * 3) % len(widths)]
            base, light, dark = pal["stones"][int(hash01(row, col, seed) * 3)]
            for yy in range(y, min(PERIOD, y + h - 1)):
                for xx in range(max(0, x), min(PERIOD, x + w - 1)):
                    c = base
                    if yy == y or xx == x:
                        c = light
                    elif yy == y + h - 2 or xx == x + w - 2:
                        c = dark
                    px[xx, yy] = rgba(c)
            for v in range(1 + int(hash01(row, col, seed + 1) * 2)):
                x0 = x + 2 + hash01(row, col, seed + 2 + v) * (w - 6)
                slope = (hash01(row, col, seed + 5 + v) - 0.5) * 1.6
                tone = light if hash01(row, col, seed + 8 + v) < 0.6 else dark
                for k in range(h - 4):
                    xx = int(x0 + slope * k + 1.5 * math.sin(k * 0.7 + col))
                    yy = y + 2 + k
                    if x + 1 < xx < x + w - 3 and 0 <= xx < PERIOD and yy < PERIOD and hash01(xx, yy, seed + 9) < 0.8:
                        px[xx, yy] = rgba(tone)
            x += w
            col += 1
        y += h
        row += 1
    return _rows(img)


def cloud(pal: dict, seed: int = 72) -> list[list[tuple]]:
    base, light, dark = pal["stones"][1]
    img, d = _canvas(base)
    lumps = []
    for i in range(120):
        lumps.append((hash01(i, 1, seed) * PERIOD, hash01(i, 2, seed) * PERIOD, 8 + hash01(i, 3, seed) * 13, int(hash01(i, 4, seed) * 3)))
    lumps.sort(key=lambda lump: lump[1])
    for cx, cy, r, k in lumps:
        body, lit, shade = pal["stones"][k]

        def one(dx: int, dy: int, cx=cx, cy=cy, r=r, body=body, lit=lit, shade=shade) -> None:
            x, y = cx + dx, cy + dy
            d.ellipse([x - r, y - r * 0.82, x + r, y + r * 0.82], fill=rgba(shade))
            d.ellipse([x - r * 0.96 - 1, y - r * 0.82 - 1, x + r * 0.9 - 1, y + r * 0.7 - 1], fill=rgba(body))
            d.ellipse([x - r * 0.72 - 1, y - r * 0.68 - 1, x + r * 0.34 - 1, y + r * 0.08 - 1], fill=rgba(lit))
        _tiled(one)
    return _rows(img)


def basalt(pal: dict, seed: int = 73) -> list[list[tuple]]:
    img, d = _canvas(pal["gap"])
    px = img.load()
    glow = pal.get("glow")
    x = 0
    col = 0
    joints = []
    while x < PERIOD:
        w = 9 + int(hash01(col, 1, seed) * 6)
        if PERIOD - (x + w) < 9:
            w = PERIOD - x
        base, light, dark = pal["stones"][int(hash01(col, 2, seed) * len(pal["stones"]))]
        cuts = []
        y = int(hash01(col, 3, seed) * 30)
        while y < PERIOD + 30:
            cuts.append(y % PERIOD)
            y += 14 + int(hash01(col, len(cuts), seed + 1) * 22)
        for yy in range(PERIOD):
            under = min((yy - c) % PERIOD for c in cuts)
            for xx in range(x, x + w - 1):
                c = base
                if under == 0:
                    c = pal["gap"]
                elif under <= 2 or xx == x:
                    c = light
                elif xx == x + w - 2 or (yy + 1 - cuts[0]) % PERIOD == 0:
                    c = dark
                elif hash01(xx, yy, seed + 2) < 0.04:
                    c = dark
                px[xx, yy] = rgba(c)
        joints.append(x + w - 1)
        x += w
        col += 1
    if glow:
        hot, lava, ember = (rgba(c) for c in glow)
        for k, jx in enumerate(joints):
            y = int(hash01(k, 5, seed) * PERIOD)
            runs = 1 + int(hash01(k, 6, seed) * 2)
            for r in range(runs):
                length = 18 + int(hash01(k, r, seed + 7) * 46)
                for i in range(length):
                    yy = (y + i) % PERIOD
                    edge = min(i, length - 1 - i)
                    px[jx % PERIOD, yy] = hot if edge > 6 and hash01(jx, yy, seed + 8) < 0.5 else lava
                    if edge > 2:
                        for side in (-1, 1):
                            px[(jx + side) % PERIOD, yy] = ember
                y += length + 40 + int(hash01(k, r, seed + 9) * 60)
    return _rows(img)


def strata(pal: dict, seed: int = 74, tilt: float = 0.0, wave: float = 2.5) -> list[list[tuple]]:
    thick = (5, 3, 7, 4, 9, 3, 6, 4, 8, 5, 4, 6)
    edges = []
    acc = 0
    for t in thick:
        edges.append((acc, t))
        acc += t
    out = [[(0, 0, 0, 0)] * PERIOD for _ in range(PERIOD)]
    n = len(pal["stones"])
    for y in range(PERIOD):
        for x in range(PERIOD):
            bend = wave * math.sin(2 * math.pi * x / 128 + 1.3) + wave * 0.6 * math.sin(2 * math.pi * x / 64 + 0.4)
            v = (y - tilt * x + bend) % 64
            k = max(i for i, (start, _) in enumerate(edges) if v >= start)
            start, t = edges[k]
            lane = int((y - tilt * x + bend) // 64) * len(thick) + k
            base, light, dark = pal["stones"][(k * 2 + k // 3) % n]
            into = v - start
            c = base
            if into < 1:
                c = light
            elif into >= t - 1:
                c = pal["gap"]
            elif hash01(x // (7 + k % 5), lane, seed) < 0.1 and hash01(x, 0, seed + lane) < 0.2:
                c = pal["gap"]
            elif hash01(x, y, seed + 3) < 0.05:
                c = dark
            elif hash01(x // 3, y, seed + 4) < 0.04:
                c = light
            out[y][x] = rgba(c)
    return out


def bricks(pal: dict, seed: int = 75) -> list[list[tuple]]:
    out = [[(0, 0, 0, 0)] * PERIOD for _ in range(PERIOD)]
    for y in range(PERIOD):
        row = y // 8
        for x in range(PERIOD):
            xs = (x + (8 if row % 2 else 0)) % PERIOD
            bx = xs // 16
            lx, ly = xs % 16, y % 8
            lost = hash01(bx, row, seed) < 0.08
            base, light, dark = pal["stones"][int(hash01(bx, row, seed + 1) * 3)]
            if lost:
                c = pal["earth_d"] if hash01(x // 2, y, seed + 2) < 0.2 else pal["earth"]
            elif ly == 7 or lx == 15:
                c = pal["gap"]
            elif ly == 0 or lx == 0:
                c = light
            elif ly == 6 or lx == 14:
                c = dark
            else:
                c = dark if hash01(x, y, seed + 3) < 0.05 else base
            if not lost and hash01(x // 5, y // 4, seed + 4) < 0.16 and hash01(x, y, seed + 5) < 0.65:
                c = pal["moss"] if hash01(x, y, seed + 6) < 0.7 else pal["moss_d"]
            out[y][x] = rgba(c)
    return out


def _apply(rows: list[list[tuple]], img: Image.Image) -> list[list[tuple]]:
    over = img.load()
    for y in range(PERIOD):
        row = rows[y]
        for x in range(PERIOD):
            p = over[x, y]
            if p[3]:
                row[x] = p
    return rows


def add_crystals(rows: list[list[tuple]], pal: dict, seed: int = 81, count: int = 40) -> list[list[tuple]]:
    gap = rgba(pal["gap"])
    vein, vein_d = rgba(pal["gems"][0][0]), rgba(pal["gems"][0][2])
    for y in range(PERIOD):
        for x in range(PERIOD):
            if rows[y][x] == gap:
                n = math.sin(x * 0.049 + 1.0) + math.sin(y * 0.061 + 2.0) + math.sin((x + y) * 0.037)
                if n > 1.25:
                    rows[y][x] = vein if hash01(x, y, seed) < 0.55 else vein_d
    img = Image.new("RGBA", (PERIOD, PERIOD), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i in range(int(pal.get("gem_count", count))):
        cx, cy = hash01(i, 1, seed) * PERIOD, hash01(i, 2, seed) * PERIOD
        light, mid, dark = pal["gems"][i % len(pal["gems"])]
        for s in range(2 + int(hash01(i, 3, seed) * 3)):
            ang = -math.pi / 2 + (hash01(i, s, seed + 1) - 0.5) * 2.2
            length = 7 + hash01(i, s, seed + 2) * 12
            half = 1.6 + hash01(i, s, seed + 3) * 1.6
            ax, ay = math.cos(ang), math.sin(ang)
            bx, by = cx + (s - 1.5) * 3, cy
            nx, ny = -ay * half, ax * half
            neck = length - half * 1.6

            def one(dx: int, dy: int, bx=bx, by=by, ax=ax, ay=ay, nx=nx, ny=ny, neck=neck, length=length, light=light, mid=mid, dark=dark) -> None:
                x0, y0 = bx + dx, by + dy
                tip = (x0 + ax * length, y0 + ay * length)
                sl, sr = (x0 + ax * neck - nx, y0 + ay * neck - ny), (x0 + ax * neck + nx, y0 + ay * neck + ny)
                sc = (x0 + ax * neck, y0 + ay * neck)
                d.polygon([(x0 - nx, y0 - ny), (x0, y0), sc, tip, sl], fill=rgba(light))
                d.polygon([(x0, y0), (x0 + nx, y0 + ny), sr, tip, sc], fill=rgba(dark))
                d.line([(x0, y0), sc], fill=rgba(mid), width=1)
                d.point([(sl[0] + ax, sl[1] + ay)], fill=(255, 255, 255, 255))
            _tiled(one)
    return _apply(rows, img)


def add_roots(rows: list[list[tuple]], pal: dict, seed: int = 82, count: int = 13) -> list[list[tuple]]:
    img = Image.new("RGBA", (PERIOD, PERIOD), (0, 0, 0, 0))
    px = img.load()
    for i in range(count):
        y0 = hash01(i, 1, seed) * PERIOD
        amp = 8 + hash01(i, 2, seed) * 20
        waves = 1 + int(hash01(i, 3, seed) * 2)
        thick = 3 + int(hash01(i, 4, seed) * 3)
        phase = hash01(i, 5, seed) * 6.28
        rise = (-1, 0, 1)[i % 3]
        for x in range(PERIOD):
            y = y0 + amp * math.sin(2 * math.pi * waves * x / PERIOD + phase) + rise * x
            for k in range(thick):
                yy = int(y + k) % PERIOD
                px[x, yy] = rgba(pal["root_l"] if k == 0 else pal["shadow"] if k == thick - 1 else pal["root"])
    return _apply(rows, img)


def add_rootlets(rows: list[list[tuple]], pal: dict, seed: int = 84, count: int = 46) -> list[list[tuple]]:
    earth = {rgba(pal[k]) for k in ("earth", "earth_l", "earth_d")}
    root, light, pebble, dark = rgba(pal["root"]), rgba(pal["root_l"]), rgba(pal["pebble"]), rgba(pal["earth_d"])

    def put(x: int, y: int, c: tuple) -> None:
        if rows[y % PERIOD][x % PERIOD] in earth:
            rows[y % PERIOD][x % PERIOD] = c
    for i in range(count):
        x, y = int(hash01(i, 1, seed) * PERIOD), int(hash01(i, 2, seed) * PERIOD)
        side = 1 if hash01(i, 3, seed) < 0.5 else -1
        for k in range(5 + int(hash01(i, 4, seed) * 12)):
            put(x, y, light if k % 4 == 0 else root)
            if hash01(i, k, seed + 1) < 0.45:
                x += side
                put(x, y, root)
            if hash01(i, k, seed + 2) < 0.12:
                side = -side
            y += 1
    for i in range(70):
        x, y = int(hash01(i, 5, seed) * PERIOD), int(hash01(i, 6, seed) * PERIOD)
        put(x, y, pebble)
        put(x + 1, y, pebble)
        put(x, y + 1, dark)
        put(x + 1, y + 1, dark)
    return rows


def add_bones(rows: list[list[tuple]], pal: dict, seed: int = 83, count: int = 34) -> list[list[tuple]]:
    bone, shade = rgba(pal["pebble"]), rgba(pal["gap"])

    def put(x: int, y: int, c: tuple) -> None:
        rows[y % PERIOD][x % PERIOD] = c
    for i in range(count):
        x, y = int(hash01(i, 1, seed) * PERIOD), int(hash01(i, 2, seed) * PERIOD)
        if hash01(i, 3, seed) < 0.3:
            for dy in range(4):
                for dx in range(5):
                    if (dx, dy) not in ((0, 0), (4, 0), (0, 3), (4, 3)):
                        put(x + dx, y + dy, bone)
            put(x + 1, y + 1, shade)
            put(x + 3, y + 1, shade)
            put(x + 2, y + 3, shade)
        else:
            length = 5 + int(hash01(i, 4, seed) * 5)
            slope = (-1, 0, 0, 1)[int(hash01(i, 5, seed) * 4)]
            for k in range(length):
                put(x + k, y + (k * slope) // 2, bone)
            for ex, ey in ((x - 1, y - 1), (x - 1, y + 1), (x + length, y + ((length - 1) * slope) // 2 - 1), (x + length, y + ((length - 1) * slope) // 2 + 1)):
                put(ex, ey, bone)
    return rows


def add_sheen(rows: list[list[tuple]], pal: dict, seed: int = 84) -> list[list[tuple]]:
    shine = rgba(pal["pebble"])
    gap = rgba(pal["gap"])
    for y in range(PERIOD):
        for x in range(PERIOD):
            band = ((x + y) // 4) % 64
            if rows[y][x] != gap and hash01(band, 0, seed) < 0.16 and hash01((x - y) // 22, band, seed + 1) < 0.5 and (x + y) % 4 < 2:
                rows[y][x] = shine
    return rows


PATTERNS = {"marble": marble, "cloud": cloud, "basalt": basalt, "strata": strata, "bricks": bricks}
EXTRAS = {"crystals": add_crystals, "roots": add_roots, "rootlets": add_rootlets, "bones": add_bones, "sheen": add_sheen}
