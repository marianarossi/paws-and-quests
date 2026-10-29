from __future__ import annotations

import math
import os
import sys

from PIL import Image

from vec import DOCS_PREVIEW, hash01, rgba, save

W, H = 640, 360
HORIZON = 236
SUN = (430, HORIZON - 30)


def put(px, x: int, y: int, color: tuple) -> None:
    if 0 <= y < H:
        px[x % W, y] = color


def lerp(a: tuple, b: tuple, t: float) -> tuple:
    t = min(1.0, max(0.0, t))
    return (round(a[0] + (b[0] - a[0]) * t), round(a[1] + (b[1] - a[1]) * t), round(a[2] + (b[2] - a[2]) * t), 255)


def gradient(stops: list[tuple[int, str]], y: float) -> tuple:
    if y <= stops[0][0]:
        return rgba(stops[0][1])
    for (y0, c0), (y1, c1) in zip(stops, stops[1:]):
        if y <= y1:
            t = (y - y0) / (y1 - y0)
            return lerp(rgba(c0), rgba(c1), t * t * (3 - 2 * t) * 0.5 + t * 0.5)
    return rgba(stops[-1][1])


SKY = [(0, "#17153a"), (36, "#241c52"), (72, "#3c2569"), (106, "#5e2f7a"), (136, "#8a3c82"), (162, "#b84c7e"),
       (184, "#de6470"), (204, "#f38560"), (220, "#fba85c"), (HORIZON, "#fdcb72"), (256, "#fee39c"), (H, "#fff0b8")]


def sky() -> Image.Image:
    img = Image.new("RGBA", (W, H))
    px = img.load()
    glow = rgba("#ffe7a0")
    for y in range(H):
        row = gradient(SKY, y)
        for x in range(W):
            d = math.hypot((x - SUN[0]) * 0.62, (y - SUN[1]) * 1.25) / 170.0
            px[x, y] = lerp(row, glow, (1.0 - d) ** 2.2 * 0.62) if d < 1.0 else row
    for i in range(110):
        x, y = int(hash01(i, 1, 71) * W), int(hash01(i, 2, 71) ** 1.5 * 120)
        star = rgba("#fff3d0" if hash01(i, 3, 71) < 0.3 else "#c2b2f0")
        px[x, y] = lerp(star, px[x, y], (y / 120.0) ** 1.5)
    r = 27
    for y in range(SUN[1] - r, SUN[1] + r + 1):
        for x in range(SUN[0] - r, SUN[0] + r + 1):
            d = math.hypot(x - SUN[0], y - SUN[1])
            if d <= r and 0 <= y < H:
                px[x, y] = rgba("#fffbe2" if d < r - 6 else "#fff0b4" if d < r - 2 else "#ffe08a")
    return img


def streak(px, cx: float, cy: float, length: float, thick: float, seed: int, tones: tuple | None = None) -> None:
    n = max(5, int(length / 7))
    blobs = []
    for k in range(n):
        u = (k + 0.5) / n * 2 - 1 + (hash01(k, seed, 1) - 0.5) * 0.25
        fall = 1.0 - u * u
        blobs.append((cx + u * length / 2, cy + (hash01(k, seed, 2) - 0.5) * thick * 0.7 * fall,
                      (9 + 22 * hash01(k, seed, 3)) * (0.45 + 0.55 * fall), 1.2 + thick * (0.16 + 0.3 * hash01(k, seed, 4)) * (0.3 + 0.7 * fall)))
    x0, x1 = int(cx - length / 2 - 34), int(cx + length / 2 + 34)
    y0, y1 = int(cy - thick - 3), int(cy + thick + 3)
    t = min(1.0, max(0.0, (cy - 30) / 185.0))
    shade = lerp(rgba("#33265f"), rgba("#c2566e"), t)
    body = lerp(rgba("#55337a"), rgba("#ee7e5e"), t)
    lit = lerp(rgba("#a8508a"), rgba("#ffc878"), t)
    hot = lerp(rgba("#e07a92"), rgba("#fff0ae"), t)
    if tones:
        shade, body, lit, hot = tones
    for x in range(x0, x1):
        col = [y for y in range(y0, y1) if any(((x - bx) / rx) ** 2 + ((y - by) / ry) ** 2 <= 1.0 for bx, by, rx, ry in blobs)]
        if not col:
            continue
        top, bot = col[0], col[-1]
        span = max(1, bot - top)
        wob = (hash01(x // 3, seed, 5) - 0.5) * 0.22
        for y in col:
            v = (y - top) / span + wob
            c = hot if (y == bot and span > 3 and hash01(x // 2, seed, 6) < 0.7) else lit if v > 0.6 else shade if v < 0.24 else body
            put(px, x, y, c)


def clouds() -> Image.Image:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = img.load()
    spec = [(120, 62, 250, 24), (510, 112, 230, 20), (330, 34, 150, 8), (600, 52, 130, 10), (40, 140, 190, 12),
            (300, 150, 120, 7), (372, 172, 240, 13), (150, 186, 170, 8), (566, 178, 150, 7), (230, 204, 210, 8),
            (500, 208, 250, 7), (70, 216, 170, 5), (350, 222, 190, 4), (620, 224, 120, 4)]
    for i, (x, y, length, thick) in enumerate(spec):
        streak(px, x, y, length, thick, 300 + i)
    for i in range(12):
        streak(px, hash01(i, 1, 88) * W, 24 + hash01(i, 2, 88) * 190, 30 + hash01(i, 3, 88) * 50, 2 + hash01(i, 4, 88) * 2, 400 + i)
    return img


def ridge(seed: int, peaks: int, base: int, amp: int) -> tuple[list[float], list[int]]:
    pts = []
    for i in range(peaks):
        x = (i + 0.25 + 0.5 * hash01(i, 1, seed)) * W / peaks
        pts.append((x, base - amp * (0.45 + 0.55 * hash01(i, 2, seed))))
        pts.append((x + W / peaks * (0.35 + 0.3 * hash01(i, 3, seed)), base - amp * 0.2 * hash01(i, 4, seed)))
    pts = [(pts[-1][0] - W, pts[-1][1])] + pts + [(pts[0][0] + W, pts[0][1]), (pts[1][0] + W, pts[1][1])]
    top, owner = [0.0] * W, [0] * W
    for x in range(W):
        for k in range(len(pts) - 1):
            (xa, ya), (xb, yb) = pts[k], pts[k + 1]
            if xa <= x < xb:
                t = (x - xa) / (xb - xa)
                top[x] = ya + (yb - ya) * t + (hash01(x // 5, 7, seed) - 0.5) * 2.5
                owner[x] = round(xa if ya < yb else xb)
                break
    return top, owner


def hills() -> Image.Image:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = img.load()
    haze = rgba("#f39a6c")
    top, owner = ridge(41, 5, 222, 52)
    lit, shade, rim = rgba("#93548a"), rgba("#7a467f"), rgba("#f7a878")
    for x in range(W):
        y0 = int(top[x])
        for y in range(y0, H):
            x2 = int(x + ((y - y0) // 5 % 2) * 3 + (y - y0) * 0.45) % W
            dark = (owner[x2] - x2) % W < W // 2
            c = shade if dark else lit
            if y == y0 and not dark:
                c = rim
            px[x, y] = lerp(c, haze, (y - 150) / 160.0)
    body, low = rgba("#663e7c"), rgba("#59366f")
    for x in range(W):
        t = 2 * math.pi * x / W
        line = HORIZON - 4 - 13 * math.sin(t + 0.6) - 7 * math.sin(2 * t + 2.0) - 3 * math.sin(5 * t)
        teeth = abs((x + int(hash01(x // 7, 3, 43) * 3)) % 5 - 2) * 1.5 + 3 * hash01(x // 9, 4, 43)
        y0 = int(line - teeth)
        for y in range(y0, H):
            c = low if y - y0 > 5 + 3 * hash01(x // 6, 5, 43) else body
            px[x, y] = lerp(c, haze, (y - y0) / 130.0)
    return img


def pine(px, cx: int, base: int, h: int, seed: int, pal: tuple, detail: int = 2, crown_part: float = 0.9, spread: float = 1.0,
         dense: bool = False) -> None:
    body, dark, light, rim = pal
    tiers = max(4, round(h / 8.5))
    crown = h * crown_part
    top = base - h
    tw = max(1, int(h * spread) // 30)
    for y in range(base - int(h * (1.04 - crown_part)) - 2, base + 2):
        for x in range(cx - tw, cx + tw + 1):
            lit_side = x >= cx + tw - (tw // 4 if crown_part < 0.9 else 0) and tw > 1
            bark = tw > 3 and crown_part < 0.9 and hash01(x, (y + x * 3) // 11, seed) < 0.2
            put(px, x, y, body if (lit_side or bark) else dark)
            if rim and crown_part < 0.9 and x == cx + tw and hash01(y, seed, 6) < 0.7:
                put(px, x, y, rim)
    spans = []
    for t in range(tiers):
        f = (t + 1) / tiers
        y0 = top + int(crown * (t / tiers) ** 1.12)
        depth = int(crown / tiers * (1.5 + 0.5 * f)) + 3
        wmax = (1.5 + h * 0.2 * spread * f ** 0.85) * (0.86 + 0.28 * hash01(t, seed, 3))
        if crown_part < 0.9 and f > 0.7:
            wmax *= 1.0 - 0.6 * ((f - 0.7) / 0.3) ** 1.5
        off = int((hash01(t, seed, 4) - 0.5) * (2 + h / 40)) if t else 0
        spans.append((y0, depth, wmax, off))
    for y in range(top - 3, top + 1):
        put(px, cx, y, dark)
    edge: dict[int, int] = {}
    for t in range(tiers - 1, -1, -1):
        y0, depth, wmax, off = spans[t]
        shadow_to = spans[t - 1][0] + spans[t - 1][1] + 1 + (h > 70) if t else -999
        fans = boughs(int(wmax) + 1, seed * 31 + t, h)
        if dense:
            for j in range(depth):
                half = wmax * (0.14 + 0.86 * (j / (depth - 1)) ** 0.75) * 0.5
                for dx in range(-int(half), int(half) + 1):
                    put(px, cx + off + dx, y0 + j, dark)
            fans = {dx: (rel, min(drop, max(3, int(depth * 0.65)))) for dx, (rel, drop) in fans.items()}
        for j in range(depth):
            k = j / (depth - 1)
            half = wmax * (0.14 + 0.86 * k ** 0.75)
            hi = int(half)
            for dx in range(-hi, hi + 1):
                e = abs(dx) / max(1.0, half)
                rel, drop = fans[dx]
                below = depth - 1 - round(drop * abs(rel) ** 1.3) - j
                if below < 0:
                    continue
                y = y0 + j + int(2.6 * e * e * k)
                x = cx + off + dx
                sunny = dx > -half * 0.12
                stroke = detail > 1 and ((dx - j) if dx > 0 else (dx + j)) % 5 == 0 and hash01(dx // 2, j // 3, seed + t) < 0.62
                if y <= shadow_to and e < 0.82:
                    c = dark
                elif abs(rel) > 0.72 and below <= 2:
                    c = dark
                elif below <= 1 + drop // 2 and rel > -0.15:
                    c = light if sunny else body
                elif stroke:
                    c = dark if sunny else body
                else:
                    c = body if sunny else dark
                put(px, x, y, c)
                if dx > 0:
                    edge[y] = max(edge.get(y, x), x)
    if rim:
        for y, x in edge.items():
            if hash01(y, seed, 5) < 0.78:
                put(px, x, y, rim)


def boughs(hi: int, seed: int, h: int) -> dict[int, tuple[float, int]]:
    out: dict[int, tuple[float, int]] = {}
    x, i = -hi - 1 - int(hash01(0, seed, 9) * 3), 0
    while x <= hi + 1:
        w = 3 + int(hash01(i, seed, 1) * (3 + h / 28))
        drop = 2 + int(hash01(i, seed, 2) * (1.5 + w / 2))
        for q in range(w):
            out[x + q] = ((q + 0.5) / w * 2 - 1, drop)
        x += w
        i += 1
    return out


def bush(px, cx: int, base: int, w: int, h: int, seed: int, pal: tuple) -> None:
    body, dark, light, rim = pal
    n = max(4, w // 4)
    blobs = []
    for i in range(n):
        u = (i + 0.5) / n * 2 - 1 + (hash01(i, seed, 3) - 0.5) * 0.3
        r = max(3.0, h * (0.26 + 0.24 * hash01(i, seed, 1)) * (0.65 + 0.35 * (1 - u * u)))
        blobs.append((cx + u * (w / 2 - r * 0.6), base - r * 0.6 - h * 0.62 * max(0.0, 1 - u * u) * hash01(i, seed, 2) ** 0.6, r))
    blobs.sort(key=lambda b: b[1])
    for i, (bx, by, r) in enumerate(blobs):
        for y in range(int(by - r - 2), min(H, base + 2)):
            for x in range(int(bx - r - 2), int(bx + r + 3)):
                dx, dy = x - bx, y - by
                ang = math.atan2(dy, dx)
                rr = r * (1.0 + 0.13 * math.sin(ang * 7 + seed + i * 1.7))
                d = math.hypot(dx, dy)
                if d > rr:
                    continue
                n_light = (dx * 0.55 - dy * 0.83) / max(1.0, r)
                if d > rr - 1.2 and n_light > 0.3 and rim:
                    c = rim if hash01(x, y, seed) < 0.5 else light
                elif (n_light > 0.5 and d > r * 0.35) or (n_light > 0.0 and hash01(x // 2, y // 2, seed + 9) < 0.16):
                    c = light
                elif n_light < -0.3 or hash01(x // 2, y, seed + 7) < 0.1:
                    c = dark
                else:
                    c = body
                put(px, x, y, c)


def stand(seed: int, base: int, trees: list[tuple[int, int]], pal: tuple, detail: int, bushes: tuple = (0, 0, 0),
          haze: tuple | None = None, ground: str | None = None, crown: float = 0.9, dense: bool = False) -> Image.Image:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = img.load()
    body, dark, light, rim = pal
    floor = rgba(ground) if ground else dark
    for x in range(W):
        blade = int(hash01(x, 1, seed) * 4) if hash01(x // 4, 2, seed) < 0.6 else 0
        for y in range(base - blade, H):
            px[x, y] = floor if y >= base + 2 or hash01(x, y, seed) < 0.6 else body
    for i, tree in enumerate(sorted(trees, key=lambda s: s[1])):
        cx, h = tree[0], tree[1]
        pine(px, cx, base + 2, h, seed + i * 7, pal, detail, tree[2] if len(tree) > 2 else crown, tree[3] if len(tree) > 3 else 1.0, dense)
    count, w0, w1 = bushes
    for i in range(count):
        w = w0 + int(hash01(i, 3, seed) * (w1 - w0))
        bush(px, int((i + 0.1 + 0.8 * hash01(i, 4, seed)) * W / count), base + 3, w, int(w * (0.42 + 0.2 * hash01(i, 5, seed))), seed + i, pal)
    if haze:
        color, strength, height = rgba(haze[0]), haze[1], haze[2]
        for y in range(max(0, base - height), H):
            f = min(1.0, (y - (base - height)) / height) ** 1.3 * strength
            for x in range(W):
                if px[x, y][3]:
                    px[x, y] = lerp(px[x, y], color, f)
    return img


def scatter(seed: int, count: int, heights: tuple[int, int]) -> list[tuple[int, int]]:
    return [(int((i + 0.15 + 0.7 * hash01(i, 1, seed)) * W / count), heights[0] + int(hash01(i, 2, seed) ** 1.4 * (heights[1] - heights[0])))
            for i in range(count)]


def P(*colors: str | None) -> tuple:
    return tuple(rgba(c) if c else None for c in colors)


def layers() -> list[tuple[str, Image.Image]]:
    return [
        ("ember_sky", sky()),
        ("ember_clouds", clouds()),
        ("ember_hills", hills()),
        ("ember_pines_far", stand(101, 250, scatter(101, 30, (22, 50)), P("#5d3d7c", "#4d3270", "#7c4f88", "#f8a070"), 1,
                                  (16, 10, 20), ("#ea8468", 0.5, 44))),
        ("ember_pines_mid2", stand(151, 268, scatter(151, 17, (42, 82)), P("#473163", "#392755", "#5a4a70", "#f38a5c"), 2,
                                   (12, 16, 30), ("#c8627a", 0.4, 54))),
        ("ember_pines_mid", stand(202, 288, scatter(202, 10, (70, 124)), P("#30264f", "#241c40", "#35525a", "#ee7c52"), 2,
                                  (10, 22, 44), ("#8a4878", 0.3, 60))),
        ("ember_pines_near", stand(303, 312, [(30, 262), (598, 226), (346, 132), (212, 84)], P("#181430", "#110e24", "#1f3a3e", None), 2,
                                   (9, 34, 70))),
    ]


def main() -> None:
    made = layers()
    for name, img in made:
        save(img, "backgrounds", f"{name}.png")
    if "--preview" in sys.argv:
        out = Image.new("RGBA", (W, H))
        for _, img in made:
            out.alpha_composite(img)
        path = os.path.join(DOCS_PREVIEW, "ember", "fundo.png")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        out.resize((W * 2, H * 2), Image.NEAREST).save(path)
    print("fundo do ember camp: ok")


if __name__ == "__main__":
    main()
