from __future__ import annotations

import colorsys
import math

from PIL import Image, ImageDraw

from vec import hash01, rgba, save

W, H = 640, 360
BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))


def bayer(x: int, y: int) -> float:
    return (BAYER[y & 3][x & 3] + 0.5) / 16.0


def tone(color: str, value: float = 0.0, sat: float = 0.0, hue: float = 0.0) -> str:
    r, g, b, _ = rgba(color)
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    h = (h + hue) % 1.0
    s = min(1.0, max(0.0, s * (1.0 + sat)))
    v = min(1.0, max(0.0, v * (1.0 + value)))
    r2, g2, b2 = colorsys.hsv_to_rgb(h, s, v)
    return "#%02x%02x%02x" % (round(r2 * 255), round(g2 * 255), round(b2 * 255))


def blend(a: str, b: str, t: float) -> str:
    x, y = rgba(a), rgba(b)
    return "#%02x%02x%02x" % tuple(round(x[i] + (y[i] - x[i]) * t) for i in range(3))


def paint(color, alpha: int = 255) -> tuple:
    c = rgba(color) if isinstance(color, str) else color
    return (c[0], c[1], c[2], alpha)


class Art:

    def __init__(self, fill=None) -> None:
        self.img = Image.new("RGBA", (W, H), paint(fill) if fill else (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def poly(self, pts: list, color, alpha: int = 255) -> None:
        for off in (-W, 0, W):
            self.d.polygon([(x + off, y) for x, y in pts], fill=paint(color, alpha))

    def ellipse(self, cx: float, cy: float, rx: float, ry: float, color, alpha: int = 255) -> None:
        rx, ry = max(0.5, rx), max(0.5, ry)
        for off in (-W, 0, W):
            self.d.ellipse([cx + off - rx, cy - ry, cx + off + rx, cy + ry], fill=paint(color, alpha))

    def rect(self, x0: float, y0: float, x1: float, y1: float, color, alpha: int = 255) -> None:
        if x1 < x0 or y1 < y0:
            return
        for off in (-W, 0, W):
            self.d.rectangle([x0 + off, y0, x1 + off, y1], fill=paint(color, alpha))

    def line(self, pts: list, color, width: int = 1) -> None:
        for off in (-W, 0, W):
            self.d.line([(x + off, y) for x, y in pts], fill=paint(color), width=width)

    def px(self, x: int, y: int, color) -> None:
        if 0 <= y < H:
            self.img.putpixel((int(x) % W, int(y)), paint(color))

    def over(self, other: "Art") -> None:
        self.img.alpha_composite(other.img)

    def glow(self, cx: float, cy: float, r: float, color, strength: float = 0.5, power: float = 1.5, squash: float = 1.0,
             steps: int = 5) -> None:
        c = paint(color)
        px = self.img.load()
        for y in range(max(0, int(cy - r * squash)), min(H, int(cy + r * squash) + 1)):
            for x in range(int(cx - r), int(cx + r) + 1):
                d = math.hypot(x - cx, (y - cy) / squash) / r
                if d >= 1.0:
                    continue
                q = (1.0 - d) ** power * steps
                level = int(q)
                if bayer(x, y) < (q - level - 0.3) / 0.4:
                    level += 1
                if level <= 0:
                    continue
                a = min(1.0, strength * level / steps)
                p = px[x % W, y]
                pa = p[3] / 255.0
                oa = a + pa * (1.0 - a)
                px[x % W, y] = (round((c[0] * a + p[0] * pa * (1 - a)) / oa), round((c[1] * a + p[1] * pa * (1 - a)) / oa),
                                round((c[2] * a + p[2] * pa * (1 - a)) / oa), round(oa * 255))

    def save(self, name: str) -> str:
        save(self.img, "backgrounds", name + ".png")
        return name + ".png"


def ramp(stops: list[tuple[int, str]], steps: int) -> list[tuple[int, str]]:
    out = []
    for (y0, c0), (y1, c1) in zip(stops, stops[1:]):
        for k in range(steps + 1):
            t = k / (steps + 1)
            out.append((round(y0 + (y1 - y0) * t), blend(c0, c1, t)))
    out.append(stops[-1])
    return out


def sky(stops: list[tuple[int, str]], dither: int = 6, smooth: int = 0) -> Art:
    if smooth:
        stops = ramp(stops, smooth)
        dither = min(dither, 4)
    strip = Image.new("RGBA", (4, H))
    px = strip.load()
    for y in range(H):
        i = max(k for k, (top, _) in enumerate(stops) if y >= top)
        for x in range(4):
            c = stops[i][1]
            if i + 1 < len(stops) and stops[i + 1][0] - y <= dither:
                if bayer(x, y) < 0.5 * (1.0 - (stops[i + 1][0] - y) / dither):
                    c = stops[i + 1][1]
            elif i > 0 and y - stops[i][0] < dither:
                if bayer(x, y) < 0.5 * (1.0 - (y - stops[i][0]) / dither):
                    c = stops[i - 1][1]
            px[x, y] = paint(c)
    art = Art()
    for x in range(0, W, 4):
        art.img.paste(strip, (x, 0))
    return art


def stars(art: Art, seed: int, count: int, y_max: int, colors: tuple = ("#ffffff", "#bfc8ff", "#ffe9b0")) -> None:
    for i in range(count):
        x, y = int(hash01(i, 1, seed) * W), int(hash01(i, 2, seed) ** 1.6 * y_max)
        c = colors[int(hash01(i, 3, seed) * len(colors))]
        art.px(x, y, c)
        if hash01(i, 4, seed) < 0.08:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                art.px(x + dx, y + dy, tone(c, -0.35))


def disc(art: Art, cx: int, cy: int, r: int, color: str, glow_color: str | None = None, glow_r: float = 2.4,
         glow_strength: float = 0.45, crescent: tuple | None = None, craters: bool = False, rim: str | None = None) -> None:
    if glow_color:
        art.glow(cx, cy, r * glow_r, glow_color, glow_strength, 1.4)
    if rim:
        art.ellipse(cx, cy, r + 1, r + 1, rim)
    art.ellipse(cx, cy, r, r, color)
    if craters:
        for i in range(5):
            a, d = hash01(i, 1, r) * 6.28, hash01(i, 2, r) * r * 0.6
            art.ellipse(cx + d * math.cos(a), cy + d * math.sin(a), 2 + r * 0.12 * hash01(i, 3, r), 2 + r * 0.1 * hash01(i, 4, r), tone(color, -0.1))
    if crescent:
        art.ellipse(cx + crescent[0], cy + crescent[1], r, r, crescent[2])


def aurora(art: Art, seed: int, colors: tuple, y0: int = 40, height: int = 70, curtains: int = 3) -> None:
    px = art.img.load()
    edge, body = paint(colors[0]), paint(colors[1])
    top = paint(colors[2] if len(colors) > 2 else colors[1])
    for k in range(curtains):
        for x in range(W):
            t = 2 * math.pi * x / W
            fold = math.sin((1 + k % 2) * t + seed * 1.7 + k * 2.4)
            if fold <= 0.0:
                continue
            fold = fold ** 0.55
            yb = y0 + height + k * 13 + 20 * math.sin((1 + k) * t + seed + k * 2.1) + 7 * math.sin(4 * t + k)
            ray = 0.5 + 0.5 * math.sin(x * 0.61 + k * 1.3) * math.sin(x * 0.17 + seed)
            length = height * (0.45 + 0.55 * ray) * fold
            reach = hash01(x, k, seed + 3)
            for j in range(int(length)):
                y = int(yb) - j
                if not 0 <= y < H:
                    continue
                f = j / length
                strength = (1.0 - f) ** 1.1 * (0.45 + 0.55 * ray) * fold
                if j < 2 and fold > 0.5:
                    px[x, y] = edge
                elif reach < strength * 1.15:
                    px[x, y] = edge if j < 4 and ray > 0.6 else body if f < 0.5 else top


def lumps(art: Art, balls: list, tones: tuple, light: tuple = (-0.5, -0.7)) -> None:
    hi, lit, body, shade = tones
    lx, ly = light
    for x, y, r in balls:
        art.ellipse(x, y, r, r * 0.86, shade)
        art.ellipse(x + lx * r * 0.1, y + ly * r * 0.16, r * 0.94, r * 0.76, body)
        art.ellipse(x + lx * r * 0.3, y + ly * r * 0.62, r * 0.62, r * 0.27, lit)
        if r > 13:
            art.ellipse(x + lx * r * 0.36, y + ly * r * 0.84, r * 0.34, r * 0.1, hi)


def cloud_tones(colors: tuple) -> tuple:
    return tuple(colors) if len(colors) == 4 else (tone(colors[0], 0.06, -0.3), colors[0], colors[1], colors[2])


def cumulus(art: Art, seed: int, count: int, y0: int, y1: int, size: tuple, colors: tuple, light: tuple = (-0.5, -0.7),
            tall: float = 0.5, at: tuple = ()) -> None:
    tones = cloud_tones(colors)
    for i in range(count):
        cloud = Art()
        cx = at[i] if i < len(at) else hash01(i, 1, seed) * W
        base = int(y0 + hash01(i, 2, seed) * (y1 - y0))
        width = size[0] + hash01(i, 3, seed) * (size[1] - size[0])
        height = width * tall * (0.7 + 0.6 * hash01(i, 4, seed))
        lean = (hash01(i, 5, seed) - 0.5) * 0.5
        n = int(14 + width / 5)
        balls = []
        for k in range(n):
            u = (k + 0.5) / n * 2 - 1 + (hash01(i, k, seed + 1) - 0.5) * 0.3
            arch = max(0.0, 1.0 - abs(u - lean) ** 1.7)
            small = k % 3 == 0
            r = width * (0.035 + 0.05 * hash01(k, i, seed + 2) if small else 0.07 + 0.09 * hash01(k, i, seed + 2)) * (0.55 + 0.7 * arch)
            up = height * arch * (hash01(k, i, seed + 3) ** 0.6 if not small else 0.75 + 0.3 * hash01(k, i, seed + 3))
            balls.append((cx + u * width * 0.5, base - r * 0.5 - up, r))
        balls.sort(key=lambda b: b[1])
        lumps(cloud, balls, tones, light)
        cloud.d.rectangle([0, base + 1, W, H], fill=(0, 0, 0, 0))
        px = cloud.img.load()
        shade = paint(tones[3])
        for y in range(base - 4, base + 1):
            if 0 <= y < H:
                for x in range(W):
                    if px[x, y][3] and (y >= base - 1 or bayer(x, y) < (y - (base - 5)) / 5):
                        px[x, y] = shade
        art.over(cloud)


def stratus(art: Art, seed: int, count: int, y0: int, y1: int, colors: tuple, length: tuple = (60, 220)) -> None:
    for i in range(count):
        cx, cy = hash01(i, 1, seed) * W, int(y0 + hash01(i, 2, seed) * (y1 - y0))
        size = length[0] + hash01(i, 3, seed) * (length[1] - length[0])
        rows = 2 + int(hash01(i, 4, seed) * 4)
        for r in range(rows):
            w = size * (1.0 - abs(r - (rows - 1) / 2) / rows * 1.4) * (0.7 + 0.5 * hash01(i, r, seed + 1))
            off = (hash01(r, i, seed + 2) - 0.5) * size * 0.3
            art.rect(cx + off - w / 2, cy + r, cx + off + w / 2, cy + r, colors[0] if r < rows / 2 else colors[1])


def cloud_bank(art: Art, seed: int, base: int, amp: int, radii: tuple, colors: tuple, light: int = -1, fill: bool = True,
               rows: int = 2, deep: str | None = None) -> None:
    tones = cloud_tones(colors)
    if fill:
        art.d.rectangle([0, base, W, H], fill=paint(tones[2]))
    for row in range(rows):
        balls, x, k = [], -radii[1], 0
        lift = amp * (rows - 1 - row) / max(1, rows - 1) if rows > 1 else 0
        while x < W + radii[1]:
            r = (radii[0] + (radii[1] - radii[0]) * hash01(k, 1, seed + row * 7)) * (0.8 + 0.2 * row / max(1, rows - 1))
            balls.append((x, base - lift - amp * 0.6 * hash01(k, 2, seed + row * 7), r))
            x += r * (0.7 + 0.6 * hash01(k, 3, seed + row * 7))
            k += 1
        lumps(art, balls, tones, (light * 0.5, -0.7))
    if fill:
        px = art.img.load()
        dark = paint(tones[3])
        deeper = paint(deep) if deep else None
        for y in range(base + 8, H):
            p = min(0.9, (y - base) / max(1, H - base) * 1.4)
            for xx in range(W):
                if bayer(xx, y) < p:
                    px[xx, y] = dark
                if deeper and bayer(xx + 2, y + 1) < p - 0.45:
                    px[xx, y] = deeper


def storm_ceiling(art: Art, seed: int, base: int, amp: int, radii: tuple, colors: tuple, flashes: tuple = (), flash: tuple | None = None) -> None:
    light, body, dark = colors
    art.d.rectangle([0, 0, W, base], fill=paint(body))
    tones = (light, tone(body, 0.22), body, dark)
    for row in range(3):
        x, k, balls = -radii[1], 0, []
        while x < W + radii[1]:
            r = (radii[0] + (radii[1] - radii[0]) * hash01(k, 1, seed + row * 5)) * (1.0 - 0.18 * row)
            y = base - 14 + row * 11 + amp * hash01(k, 2, seed + row * 5)
            hot = [f for f in flashes if abs(((x - f[0] + W / 2) % W) - W / 2) < f[1]]
            lumps(art, [(x, y, r)], flash if hot and flash else tones, (0.25, 0.75))
            x += r * (0.75 + 0.6 * hash01(k, 3, seed + row * 5))
            k += 1
    px = art.img.load()
    shade = paint(dark)
    for y in range(0, base + amp):
        p = 0.95 * max(0.0, 1.0 - y / (base + amp * 0.5))
        for xx in range(W):
            if px[xx, y][3] == 255 and bayer(xx, y) < p:
                px[xx, y] = shade


def lightning(art: Art, x0: float, y0: float, x1: float, y1: float, seed: int, colors: tuple = ("#ffffff", "#c4d4ff", "#7f9cf0"),
              forks: int = 3, glow: float = 16.0, depth: int = 0) -> None:
    core, edge, halo = colors
    pts = [(x0, y0), (x1, y1)]
    spread = math.hypot(x1 - x0, y1 - y0) * 0.2
    for level in range(4 if depth == 0 else 3):
        out = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            nx, ny = -(b[1] - a[1]), b[0] - a[0]
            n = math.hypot(nx, ny) or 1.0
            off = (hash01(len(out), level, seed) - 0.5) * spread
            out += [((a[0] + b[0]) / 2 + nx / n * off, (a[1] + b[1]) / 2 + ny / n * off), b]
        pts = out
        spread *= 0.52
    if glow and depth == 0:
        for x, y in pts[::2]:
            art.glow(x, y, glow, halo, 0.3, 1.7)
    if depth < 2:
        total = math.hypot(x1 - x0, y1 - y0)
        base = math.atan2(y1 - y0, x1 - x0)
        for f in range(forks):
            k = int(len(pts) * (0.15 + 0.6 * hash01(f, 1, seed)))
            ang = base + (0.35 + 0.5 * hash01(f, 2, seed)) * (1 if f % 2 else -1)
            length = total * (0.22 + 0.25 * hash01(f, 3, seed)) / (depth + 1)
            lightning(art, pts[k][0], pts[k][1], pts[k][0] + math.cos(ang) * length, pts[k][1] + math.sin(ang) * length,
                      seed * 7 + f + 1, colors, forks - 1, 0.0, depth + 1)
    n = len(pts) - 1
    if depth == 0:
        for k, (a, b) in enumerate(zip(pts, pts[1:])):
            art.line([a, b], edge, 3 if k < n * 0.6 else 2)
    for k, (a, b) in enumerate(zip(pts, pts[1:])):
        art.line([a, b], core if depth == 0 else edge, 2 if depth == 0 and k < n * 0.3 else 1)


def bolt(art: Art, x: float, y0: float, y1: float, seed: int, color: str = "#ffffff", glow_color: str = "#8fb0ff") -> None:
    lightning(art, x, y0, x + (hash01(seed, 1) - 0.5) * 60, y1, seed, (color, blend(color, glow_color, 0.5), glow_color))


def profile(seed: int, base: int, amp: int, jag: float = 0.0, freqs: tuple = (1, 2, 3, 5, 8, 13, 21)) -> list[int]:
    values = []
    for x in range(W):
        t = 2 * math.pi * x / W
        v = 0.0
        for i, k in enumerate(freqs):
            a = 1.0 / (i + 1) ** 0.95
            ph = hash01(k, i, seed) * 2 * math.pi
            v += a * ((1 - jag) * math.sin(k * t + ph) + jag * (1 - 2 * abs(math.sin(0.5 * k * t + ph))))
        values.append(v)
    lo, hi = min(values), max(values)
    return [int(round(base - amp * (v - lo) / (hi - lo))) for v in values]


def land(art: Art, prof: list[int], body: str, lit: str | None = None, dark: str | None = None, light: int = 1,
         depth: float = 0.5, snow: tuple | None = None, rim: str | None = None, haze: tuple | None = None, seed: int = 0) -> None:
    px = art.img.load()
    amp = max(1, max(prof) - min(prof))
    cb, cl, cd = paint(body), paint(lit) if lit else None, paint(dark) if dark else None
    for x in range(W):
        top = prof[x]
        slope = (prof[(x + 3) % W] - prof[(x - 3) % W]) * light
        d = int(amp * depth * (0.5 + 0.5 * hash01(x // 5, 1, seed)))
        for y in range(max(0, top), H):
            k = y - top
            c = cb
            if cl and slope > 1 and (k < d - 4 or (k < d and bayer(x, y) < (d - k) / 4)):
                c = cl
            elif cd and slope < -1 and (k < d * 0.8 - 4 or (k < d * 0.8 and bayer(x, y) < (d * 0.8 - k) / 4)):
                c = cd
            if snow and k < snow[2] * (0.5 + hash01(x // 3, 2, seed)):
                c = paint(snow[1] if slope < -1 else snow[0])
            if haze and y > haze[1] and bayer(x, y) < haze[2] * (y - haze[1]) / max(1, H - haze[1]):
                c = paint(haze[0])
            px[x, y] = c
        if rim and 0 <= top < H:
            px[x, top] = paint(rim)


def pine(art: Art, cx: int, base: int, height: int, seed: int, body: str, dark: str, rim: str | None = None, snow: str | None = None) -> None:
    tiers = max(4, height // 11)
    trunk = max(1, height // 26)
    art.rect(cx - trunk, base - height // 6, cx + trunk, base, dark)
    step = (height * 0.86) / tiers
    edges: dict[int, int] = {}
    for t in range(tiers):
        f = (t + 1) / tiers
        top = base - height + int(t * step)
        deep = int(step * 1.35) + 2
        half_max = 2 + height * 0.2 * f ** 0.85
        for j in range(deep):
            k = j / (deep - 1)
            half = int(half_max * (0.22 + 0.78 * k ** 0.85))
            for dx in range(-half, half + 1):
                edge = abs(dx) / max(1, half)
                if j >= deep - 3 and edge > 0.2 and (dx + t * 2) % 4 < 2 and j - (deep - 3) >= (0 if (dx + t) % 4 == 0 else 1):
                    continue
                yy = top + j + int(2.2 * k * edge * edge)
                c = dark if (dx < -half * 0.15 or j >= deep - 2) else body
                if snow and j < 3 and edge < 0.8:
                    c = snow
                art.px(cx + dx, yy, c)
                edges[yy] = max(edges.get(yy, cx + dx), cx + dx)
    if rim:
        for yy, hi in edges.items():
            if hash01(yy, seed, 5) < 0.8:
                art.px(hi, yy, rim)


def round_tree(art: Art, cx: float, base: float, height: float, seed: int, trunk: str, leaf: tuple, light: int = 1) -> None:
    body, lit, dark = leaf
    w = max(2, height / 13)
    art.poly([(cx - w, base), (cx + w, base), (cx + w * 0.6, base - height * 0.55), (cx - w * 0.6, base - height * 0.55)], trunk)
    cy = base - height * 0.68
    blobs = [(cx + (hash01(i, 1, seed) - 0.5) * height * 0.5, cy + (hash01(i, 2, seed) - 0.5) * height * 0.34,
              height * (0.17 + 0.1 * hash01(i, 3, seed))) for i in range(7)]
    for x, y, r in blobs:
        art.ellipse(x - light * 2, y + 3, r, r * 0.9, dark)
    for x, y, r in blobs:
        art.ellipse(x, y, r, r * 0.9, body)
    for x, y, r in blobs:
        art.ellipse(x + light * r * 0.25, y - r * 0.3, r * 0.6, r * 0.48, lit)


def cypress(art: Art, cx: int, base: int, height: int, seed: int, colors: tuple, light: int = 1) -> None:
    body, lit, dark = colors
    width = max(3, height * 0.13)
    art.rect(cx - 1, base - 6, cx + 1, base, dark)
    for j in range(height - 4):
        t = j / (height - 4)
        half = int(1 + width * math.sin(math.pi * min(1.0, t * 0.92 + 0.04)) ** 0.75 * (0.45 + 0.55 * t) + (hash01(j, 1, seed) < 0.3))
        y = base - height + j
        for dx in range(-half, half + 1):
            side = dx * light
            c = lit if side > half * 0.45 else dark if side < -half * 0.35 else body
            art.px(cx + dx, y, c)


def dead_tree(art: Art, x: float, y: float, length: float, angle: float, seed: int, color: str, width: int = 3) -> None:
    x2, y2 = x + length * math.sin(angle), y - length * math.cos(angle)
    art.line([(x, y), (x2, y2)], color, max(1, width))
    if length > 7:
        spread = 0.35 + 0.5 * hash01(seed, 1)
        dead_tree(art, x2, y2, length * (0.62 + 0.1 * hash01(seed, 2)), angle - spread, seed * 2 + 1, color, width - 1)
        dead_tree(art, x2, y2, length * (0.58 + 0.12 * hash01(seed, 3)), angle + spread * 0.9, seed * 2 + 2, color, width - 1)


def scatter(seed: int, count: int, lo: float, hi: float) -> list[tuple[int, float]]:
    return [(int((i + 0.15 + 0.7 * hash01(i, 1, seed)) * W / count), lo + hash01(i, 2, seed) * (hi - lo)) for i in range(count)]


def foliage(art: Art, seed: int, y: int, colors: tuple, size: tuple = (16, 34), hang: bool = True, step: float = 1.0) -> None:
    body, lit, dark = colors
    x, k = 0.0, 0
    while x < W:
        r = size[0] + (size[1] - size[0]) * hash01(k, 1, seed)
        cy = y + (hash01(k, 2, seed) - 0.5) * r * 0.8
        art.ellipse(x, cy + 3, r, r * 0.8, dark)
        art.ellipse(x, cy, r, r * 0.8, body)
        art.ellipse(x + r * 0.2, cy - r * 0.25, r * 0.55, r * 0.4, lit)
        if hang and hash01(k, 3, seed) < 0.45:
            vx, length = x + (hash01(k, 4, seed) - 0.5) * r, 20 + 50 * hash01(k, 5, seed)
            art.line([(vx, cy), (vx + 3, cy + length * 0.5), (vx - 1, cy + length)], dark, 2)
        x += r * (1.0 + 0.9 * hash01(k, 6, seed)) * step
        k += 1


def reeds(art: Art, seed: int, base: int, count: int, colors: tuple, height: tuple = (14, 44), flowers: tuple = ()) -> None:
    for i in range(count):
        x = hash01(i, 1, seed) * W
        h = height[0] + (height[1] - height[0]) * hash01(i, 2, seed) ** 1.5
        lean = (hash01(i, 3, seed) - 0.5) * h * 0.5
        art.line([(x, base), (x + lean * 0.4, base - h * 0.6), (x + lean, base - h)], colors[i % 2], 1 + (i % 3 == 0))
        if flowers and hash01(i, 4, seed) < 0.3:
            c = flowers[int(hash01(i, 5, seed) * len(flowers))]
            art.rect(x + lean - 1, base - h - 2, x + lean + 1, base - h, c)


def column(art: Art, cx: float, base: float, height: float, width: float, colors: tuple, light: int = 1,
           broken: bool = False, seed: int = 0) -> None:
    body, lit, dark = colors
    half = width / 2
    top = base - height
    art.rect(cx - half - 2, base - 3, cx + half + 2, base, body)
    if light > 0:
        art.rect(cx - half - 2, base - 3, cx - half, base, dark)
    else:
        art.rect(cx + half, base - 3, cx + half + 2, base, dark)
    for i in range(int(width) + 1):
        f = i / max(1.0, width)
        side = f if light > 0 else 1 - f
        c = lit if side > 0.68 else dark if side < 0.24 else body
        if i % 3 == 2 and 0.24 <= side <= 0.68:
            c = tone(body, -0.1)
        cut = top + (6 + 9 * hash01(i // 2, 1, seed) if broken else 0)
        art.line([(cx - half + i, base - 3), (cx - half + i, cut)], c, 1)
    if not broken:
        art.rect(cx - half - 1, top - 2, cx + half + 1, top, body)
        art.rect(cx - half - 3, top - 5, cx + half + 3, top - 3, lit if light else body)
        art.rect(cx - half - 3, top - 3, cx + half + 3, top - 3, dark)


def temple(art: Art, cx: float, base: float, width: float, height: float, count: int, colors: tuple, light: int = 1,
           ruined: float = 0.0, seed: int = 0) -> None:
    body, lit, dark = colors
    for s in range(3):
        art.rect(cx - width / 2 - 6 + s * 2, base - 3 * (s + 1), cx + width / 2 + 6 - s * 2, base - 3 * s, lit if s == 2 else body)
        art.rect(cx - width / 2 - 6 + s * 2, base - 3 * s - 1, cx + width / 2 + 6 - s * 2, base - 3 * s, dark)
    col_w = max(3.0, width / (count * 2.4))
    col_h = height * 0.62
    whole = True
    for i in range(count):
        x = cx - width / 2 + col_w + i * (width - 2 * col_w) / max(1, count - 1)
        broke = hash01(i, 1, seed) < ruined
        whole = whole and not broke
        column(art, x, base - 9, col_h * (0.4 + 0.4 * hash01(i, 2, seed) if broke else 1.0), col_w, colors, light, broke, seed + i)
    top = base - 9 - col_h - 5
    if ruined < 0.5:
        art.rect(cx - width / 2 - 2, top - 6, cx + width / 2 + 2, top, body)
        art.rect(cx - width / 2 - 2, top - 6, cx + width / 2 + 2, top - 5, lit)
        art.rect(cx - width / 2 - 2, top - 1, cx + width / 2 + 2, top, dark)
        peak = height * 0.22
        art.poly([(cx - width / 2 - 4, top - 6), (cx + width / 2 + 4, top - 6), (cx, top - 6 - peak)], body)
        art.poly([(cx - width / 2 + 6, top - 8), (cx + width / 2 - 6, top - 8), (cx, top - 6 - peak + 5)], dark)
        art.line([(cx - width / 2 - 4, top - 6), (cx, top - 6 - peak), (cx + width / 2 + 4, top - 6)], lit, 1)


def statue_dog(art: Art, cx: float, base: float, size: float, colors: tuple) -> None:
    body, lit, dark = colors
    art.rect(cx - size * 0.7, base - size * 0.5, cx + size * 0.7, base, body)
    art.rect(cx - size * 0.8, base - size * 0.5 - 2, cx + size * 0.8, base - size * 0.5, lit)
    art.rect(cx - size * 0.7, base - 2, cx + size * 0.7, base, dark)
    top = base - size * 0.5 - 2
    art.ellipse(cx - size * 0.1, top - size * 0.45, size * 0.42, size * 0.5, body)
    art.ellipse(cx + size * 0.2, top - size * 1.0, size * 0.3, size * 0.27, body)
    art.poly([(cx + size * 0.38, top - size * 0.98), (cx + size * 0.72, top - size * 0.9), (cx + size * 0.4, top - size * 0.8)], body)
    art.poly([(cx + size * 0.02, top - size * 1.18), (cx + size * 0.16, top - size * 1.5), (cx + size * 0.28, top - size * 1.2)], body)
    art.line([(cx - size * 0.45, top - size * 0.2), (cx - size * 0.7, top - size * 0.5)], body, 2)
    art.ellipse(cx + size * 0.28, top - size * 1.08, size * 0.14, size * 0.1, lit)


def village(art: Art, prof: list[int], x0: int, count: int, wall: str, roof: str, window: str, mill: bool = True) -> None:
    for i in range(count):
        x = x0 + i * 13 + int(hash01(i, 1, x0) * 6)
        w, h = 6 + int(hash01(i, 2, x0) * 4), 5 + int(hash01(i, 3, x0) * 4)
        top = prof[(x + w // 2) % W] - h + 2
        art.rect(x, top, x + w - 1, top + h + 3, wall)
        for k in range(w // 2 + 2):
            art.rect(x - 1 + k, top - 1 - k, x + w - k, top - 1 - k, roof)
        art.rect(x + 2, top + 2, x + 3, top + 3, window)
    if mill:
        mx = x0 + count * 13 + 14
        my = prof[mx % W] - 18
        art.poly([(mx - 3, my + 22), (mx + 3, my + 22), (mx + 2, my), (mx - 2, my)], wall)
        for a in (0.5, 2.07, 3.64, 5.21):
            art.line([(mx, my), (mx + 13 * math.cos(a), my + 13 * math.sin(a))], roof, 1)
        art.rect(mx - 1, my + 8, mx, my + 9, window)


def boat(art: Art, cx: float, y: float, color: str, lantern: str) -> None:
    art.poly([(cx - 22, y - 4), (cx + 22, y - 4), (cx + 16, y + 2), (cx - 16, y + 2)], color)
    art.poly([(cx + 22, y - 4), (cx + 28, y - 12), (cx + 24, y - 4)], color)
    art.poly([(cx - 4, y - 4), (cx - 1, y - 22), (cx + 3, y - 4)], color)
    art.ellipse(cx - 1, y - 23, 3, 3, color)
    art.line([(cx + 5, y - 30), (cx + 9, y + 6)], color, 1)
    art.glow(cx - 14, y - 12, 14, lantern, 0.6, 1.2)
    art.rect(cx - 15, y - 13, cx - 13, y - 11, lantern)


def cave(art: Art, seed: int, colors: tuple, ceiling: tuple | None = (70, 40), floor: tuple | None = (300, 40),
         spikes: tuple = (9, 7), reach: int = 46) -> None:
    body, rim, dark = paint(colors[0]), paint(colors[1]), paint(colors[2])
    px = art.img.load()
    if ceiling:
        prof = profile(seed, ceiling[0], ceiling[1], 0.55)
        flat = [2 * ceiling[0] - p for p in prof]
        edge = list(flat)
        for i in range(spikes[0]):
            x0 = int((i + 0.2 + 0.6 * hash01(i, 1, seed)) * W / spikes[0])
            length, half = reach * (0.35 + 0.65 * hash01(i, 2, seed)), 4 + int(7 * hash01(i, 3, seed))
            for dx in range(-half, half + 1):
                x = (x0 + dx) % W
                edge[x] = max(edge[x], int(flat[x] + length * (1 - abs(dx) / half) ** 1.4))
        for x in range(W):
            for y in range(0, min(H, edge[x] + 1)):
                k = edge[x] - y
                px[x, y] = rim if k < 1 else body if (k < 6 or (k < 12 and bayer(x, y) < (12 - k) / 6)) else dark
    if floor:
        prof = profile(seed + 7, floor[0], floor[1], 0.55)
        edge = list(prof)
        for i in range(spikes[1]):
            x0 = int((i + 0.2 + 0.6 * hash01(i, 4, seed)) * W / spikes[1])
            length, half = reach * (0.3 + 0.6 * hash01(i, 5, seed)), 5 + int(8 * hash01(i, 6, seed))
            for dx in range(-half, half + 1):
                x = (x0 + dx) % W
                edge[x] = min(edge[x], int(prof[x] - length * (1 - abs(dx) / half) ** 1.4))
        for x in range(W):
            for y in range(max(0, edge[x]), H):
                k = y - edge[x]
                px[x, y] = rim if k < 1 else body if (k < 6 or (k < 12 and bayer(x, y) < (12 - k) / 6)) else dark


def crystal(art: Art, bx: float, by: float, length: float, angle: float, half: float, colors: tuple) -> None:
    light, mid, dark = colors
    ax, ay = math.sin(angle), -math.cos(angle)
    nx, ny = math.cos(angle), math.sin(angle)
    neck = max(1.0, length - half * 1.8)

    def pt(along: float, across: float) -> tuple:
        return (bx + ax * along + nx * across, by + ay * along + ny * across)
    tip = pt(length, half * 0.1)
    art.poly([pt(0, -half), pt(0, -half * 0.2), pt(neck, -half * 0.2), pt(neck, -half)], light)
    art.poly([pt(0, -half * 0.2), pt(0, half * 0.5), pt(neck, half * 0.5), pt(neck, -half * 0.2)], mid)
    art.poly([pt(0, half * 0.5), pt(0, half), pt(neck, half), pt(neck, half * 0.5)], dark)
    art.poly([pt(neck, -half), pt(neck, -half * 0.2), tip], tone(light, 0.2, -0.45))
    art.poly([pt(neck, -half * 0.2), pt(neck, half * 0.5), tip], light)
    art.poly([pt(neck, half * 0.5), pt(neck, half), tip], mid)
    if half >= 3:
        art.line([pt(neck * 0.35, -half + 1), pt(neck * 0.9, -half + 1)], "#ffffff", 1)


def crystals(art: Art, cx: float, base: float, size: float, seed: int, colors: tuple, glow_color: str | None = None,
             down: bool = False, count: int = 0) -> None:
    turn = math.pi if down else 0.0
    sign = 1 if down else -1
    if glow_color:
        art.glow(cx, base + sign * size * 0.45, size * 1.5, glow_color, 0.3, 1.35)
    n = count or 4 + int(hash01(seed, 9) * 3)
    shards = []
    for i in range(n):
        f = (i + 0.5) / n * 2 - 1
        ang = f * 0.85 + (hash01(i, 1, seed) - 0.5) * 0.25
        length = size * (1.0 - 0.55 * abs(f)) * (0.75 + 0.35 * hash01(i, 2, seed))
        shards.append((abs(f), cx + f * size * 0.32, length, ang))
    for _, bx, length, ang in sorted(shards, reverse=True):
        crystal(art, bx, base, length, turn + (ang if not down else -ang), max(2.0, length * 0.15), colors)


def roots(art: Art, seed: int, count: int, colors: tuple, y_range: tuple = (40, 300), width: tuple = (8, 22)) -> None:
    body, lit, dark = colors
    for i in range(count):
        y0 = y_range[0] + hash01(i, 1, seed) * (y_range[1] - y_range[0])
        y1 = y_range[0] + hash01(i, 2, seed) * (y_range[1] - y_range[0])
        sag = (hash01(i, 3, seed) - 0.3) * 120
        w0 = width[0] + hash01(i, 4, seed) * (width[1] - width[0])
        x0 = hash01(i, 5, seed) * W
        span = W * (0.5 + 0.4 * hash01(i, 6, seed))
        steps = 60
        spine = [(x0 + span * k / steps, y0 + (y1 - y0) * k / steps + sag * math.sin(math.pi * k / steps) + 3 * math.sin(k * 0.5 + i),
                  max(2.0, w0 * (1 - 0.7 * k / steps))) for k in range(steps + 1)]
        upper = [(x, y - w * 0.5) for x, y, w in spine]
        lower = [(x, y + w * 0.5) for x, y, w in spine]
        art.poly(upper + lower[::-1], body)
        art.poly([(x, y + w * 0.12) for x, y, w in spine] + lower[::-1], dark)
        art.poly(upper + [(x, y - w * 0.28) for x, y, w in spine][::-1], lit)
        for k in range(6, steps, 11):
            x, y, w = spine[k]
            art.line([(x, y + w * 0.4), (x + 6, y + w * 0.5 + 10 + 14 * hash01(k, i, seed)), (x + 3, y + w * 0.5 + 26 + 20 * hash01(k, i, seed + 1))], dark, 2)


def lake(art: Art, source: Image.Image, y0: int, top: str, deep: str, strength: float = 0.5, glitter: str | None = None, seed: int = 0) -> None:
    src = source.convert("RGBA").load()
    px = art.img.load()
    ct, cd = rgba(top), rgba(deep)
    for y in range(y0, H):
        t = (y - y0) / max(1, H - y0)
        base = [round(ct[i] + (cd[i] - ct[i]) * min(1.0, t * 1.2)) for i in range(3)]
        sy = max(0, y0 - 1 - int((y - y0) * 1.6))
        wobble = round(1.5 * math.sin(y * 0.8 + seed) * (1 + 3 * t))
        for x in range(W):
            r = src[(x + wobble) % W, sy]
            k = strength * (r[3] / 255.0) * (1.0 - 0.6 * t)
            px[x, y] = (round(base[0] + (r[0] - base[0]) * k), round(base[1] + (r[1] - base[1]) * k), round(base[2] + (r[2] - base[2]) * k), 255)
    if glitter:
        c = paint(glitter)
        for i in range(90):
            y = y0 + 2 + int(hash01(i, 1, seed + 3) ** 1.7 * (H - y0 - 4))
            x, length = int(hash01(i, 2, seed + 3) * W), 2 + int(hash01(i, 3, seed + 3) * (4 + 10 * (y - y0) / (H - y0)))
            for dx in range(length):
                px[(x + dx) % W, y] = c


def sea(art: Art, y0: int, colors: tuple, foam: str, seed: int = 0, sun_x: int | None = None, sun_color: str = "#fff6c8") -> None:
    px = art.img.load()
    stops = [(y0, colors[0]), (y0 + (H - y0) // 3, colors[1]), (y0 + 2 * (H - y0) // 3, colors[2])]
    for y in range(y0, H):
        i = max(k for k, (top, _) in enumerate(stops) if y >= top)
        for x in range(W):
            c = stops[i][1]
            if i + 1 < len(stops) and stops[i + 1][0] - y <= 8 and bayer(x, y) < 0.5 * (1 - (stops[i + 1][0] - y) / 8):
                c = stops[i + 1][1]
            px[x, y] = paint(c)
    for i in range(170):
        t = hash01(i, 1, seed) ** 1.5
        y = y0 + 1 + int(t * (H - y0 - 2))
        x, length = int(hash01(i, 2, seed) * W), 2 + int(t * 14 * hash01(i, 3, seed)) + 1
        for dx in range(length):
            px[(x + dx) % W, y] = paint(foam)
    if sun_x is not None:
        for y in range(y0, H):
            t = (y - y0) / (H - y0)
            spread = 5 + 34 * t
            for k in range(int(3 + 5 * t)):
                x = int(sun_x + (hash01(y, k, seed + 5) - 0.5) * 2 * spread)
                for dx in range(1 + int(4 * t)):
                    px[(x + dx) % W, y] = paint(sun_color)


def lava(art: Art, y0: int, colors: tuple, seed: int = 0) -> None:
    px = art.img.load()
    bright, body, crust = paint(colors[0]), paint(colors[1]), paint(colors[2])
    for y in range(max(0, y0 - 70), y0):
        p = 0.55 * ((y - (y0 - 70)) / 70) ** 1.6
        for x in range(W):
            if bayer(x, y) < p:
                px[x, y] = body
    for y in range(y0, H):
        for x in range(W):
            n = math.sin(x * 0.05 + y * 0.21 + seed) + math.sin(x * 0.013 - y * 0.09) + hash01(x // 6, y // 3, seed)
            px[x, y] = bright if n > 1.55 else crust if n < -0.2 else body


def rays(art: Art, seed: int, count: int, color: str, alpha: int = 32, slant: float = -150.0, width: tuple = (14, 50), bottom: int = H) -> None:
    for i in range(count):
        x0 = (i + hash01(i, 1, seed)) * W / count
        w = width[0] + (width[1] - width[0]) * hash01(i, 2, seed)
        layer = Art()
        layer.poly([(x0, -10), (x0 + w, -10), (x0 + w * 2.2 + slant, bottom), (x0 + slant, bottom)], color, int(alpha * (0.6 + 0.6 * hash01(i, 3, seed))))
        art.over(layer)


def fog(art: Art, seed: int, color: str, y0: int, y1: int, count: int = 18, alpha: int = 26, size: tuple = (70, 200)) -> None:
    for k in range(count):
        layer = Art()
        x, y = hash01(k, 1, seed) * W, y0 + hash01(k, 2, seed) * (y1 - y0)
        layer.ellipse(x, y, size[0] + (size[1] - size[0]) * hash01(k, 3, seed), 5 + 10 * hash01(k, 4, seed), color, alpha)
        art.over(layer)


def kelp(art: Art, seed: int, count: int, colors: tuple, height: tuple = (60, 200), base: int = H) -> None:
    for i in range(count):
        x0 = hash01(i, 1, seed) * W
        h = height[0] + (height[1] - height[0]) * hash01(i, 2, seed)
        pts = [(x0 + 7 * math.sin(k * 0.55 + i), base - h * k / 14) for k in range(15)]
        art.line(pts, colors[0], 3)
        for k in range(2, 14, 2):
            side = 1 if k % 4 == 0 else -1
            art.ellipse(pts[k][0] + side * 5, pts[k][1], 5, 2.5, colors[1] if i % 2 else colors[0])


def rock_pillars(art: Art, seed: int, count: int, colors: tuple, width: tuple = (18, 44), light: int = 1) -> None:
    body, rim, dark = paint(colors[0]), paint(colors[1]), paint(colors[2])
    px = art.img.load()
    for i in range(count):
        cx = int((i + 0.2 + 0.6 * hash01(i, 1, seed)) * W / count)
        w = width[0] + (width[1] - width[0]) * hash01(i, 2, seed)
        for y in range(H):
            pinch = 0.5 + 0.5 * abs(2 * y / H - 1) ** 1.6
            half = int(w * pinch + 3 * math.sin(y * 0.11 + i) + 2 * hash01(y // 5, i, seed))
            for dx in range(-half, half + 1):
                side = dx * light
                px[(cx + dx) % W, y] = rim if side >= half - 1 else dark if side < -half * 0.3 else body


def giant_tree(art: Art, cx: float, width: float, colors: tuple, seed: int = 0, light: int = 1) -> None:
    body, lit, dark = colors
    w = width
    art.poly([(cx - w * 1.5, H), (cx - w * 0.62, H - 70), (cx - w * 0.5, 80), (cx - w * 0.8, -10),
              (cx + w * 0.8, -10), (cx + w * 0.5, 80), (cx + w * 0.62, H - 70), (cx + w * 1.5, H)], body)
    art.poly([(cx - light * w * 1.5, H), (cx - light * w * 0.62, H - 70), (cx - light * w * 0.5, 80), (cx - light * w * 0.8, -10),
              (cx - light * w * 0.35, -10), (cx - light * w * 0.22, 90), (cx - light * w * 0.3, H - 60), (cx - light * w * 0.7, H)], dark)
    art.poly([(cx + light * w * 0.5, 80), (cx + light * w * 0.62, H - 70), (cx + light * w * 1.5, H), (cx + light * w * 1.3, H),
              (cx + light * w * 0.5, H - 66), (cx + light * w * 0.4, 84)], lit)
    for i in range(5):
        y = 60 + i * 52 + 20 * hash01(i, 1, seed)
        art.ellipse(cx + (hash01(i, 2, seed) - 0.5) * w * 0.5, y, 4 + 5 * hash01(i, 3, seed), 8 + 8 * hash01(i, 4, seed), dark)
    for side, reach in ((-1, 150), (1, 120)):
        art.line([(cx + side * w * 0.3, 90), (cx + side * (w * 0.6 + reach * 0.5), 46), (cx + side * (w * 0.6 + reach), 34)], body, int(w * 0.3))


def chains(art: Art, seed: int, count: int, color: str, length: tuple = (60, 200)) -> None:
    for i in range(count):
        x = int(hash01(i, 1, seed) * W)
        n = int(length[0] + (length[1] - length[0]) * hash01(i, 2, seed))
        for y in range(0, n, 6):
            art.rect(x, y, x + 1, y + 3, color)
            art.rect(x - 1, y + 4, x + 2, y + 5, color)


def peaks(art: Art, seed: int, specs: list, colors: tuple, light: int = 1, foot: int = 300, snow: tuple | None = None,
          trees: tuple | None = None, haze: tuple | None = None, rough: float = 1.0, fan: float = 5.0) -> list[int]:
    hi, lit, body, dark, deep = (paint(c) for c in colors)
    px = art.img.load()
    shapes = []
    for i, (cx, ty, hw) in enumerate(specs):
        slope = (foot - ty) / max(1.0, hw)
        lean = (hash01(i, 1, seed) - 0.5) * 0.5
        period = 26 + 30 * hash01(i, 2, seed)
        phase = hash01(i, 3, seed) * period
        zig, x, d = [], 0.0, 0.0
        step = (hash01(i, 4, seed) - 0.5) * 1.2 - light * 0.12
        for depth in range(H + 40):
            if depth % (7 + int(hash01(i, depth // 7, seed + 5) * 9)) == 0:
                step = (hash01(i, depth, seed + 6) - 0.5) * 1.5 - light * 0.12
            x += step
            zig.append(x)
        shapes.append((cx, ty, slope, lean, period, phase, zig))

    def height(i: int, dx: float) -> float:
        cx, ty, slope, lean, period, phase, _ = shapes[i]
        a = abs(dx)
        y = ty + a * slope * (1.0 + lean * (1 if dx > 0 else -1))
        bump = min(a * 0.4, 13.0 * rough)
        saw = abs(((a + phase) / period) % 1.0 - 0.5) * 2.0
        return y - bump * saw + (hash01(int(dx) // 2, i, seed + 7) - 0.5) * 2.0 * rough

    prof, owner = [], []
    for x in range(W):
        best, who, off = 1e9, 0, 0
        for i in range(len(specs)):
            for wrap in (-W, 0, W):
                y = height(i, x - specs[i][0] - wrap)
                if y < best:
                    best, who, off = y, i, wrap
        prof.append(int(round(best)))
        owner.append((who, off))
    for x in range(W):
        i, off = owner[x]
        cx, ty, slope, lean, period, phase, zig = shapes[i]
        tline = None
        if trees:
            tline = trees[2] - trees[3] * (0.5 + 0.5 * math.sin(x * 0.045 + seed)) - 5 * hash01(x // 9, 2, seed + 8) - (3 if x % 3 == 0 else 0) * hash01(x, 3, seed + 8)
        for y in range(max(0, prof[x]), H):
            d = y - ty
            s = (x - cx - off) - zig[max(0, min(len(zig) - 1, int(d)))]
            lit_side = s * light > 0
            u = abs(s) / max(6.0, d)
            b = int(u * fan)
            seg = int(d / (9 + 16 * hash01(b, i, seed + 1)))
            h = hash01(b * 7 + seg, i * 13 + lit_side, seed + 2)
            if lit_side:
                c = hi if h < 0.2 else lit if h < 0.72 else body
                if abs(s) < 1.5:
                    c = hi
            else:
                c = body if h < 0.18 else dark if h < 0.74 else deep
            if snow and d < snow[2] * (0.45 + 1.1 * hash01(b, i, seed + 3)) * (1.0 if lit_side else 0.6):
                c = paint(snow[0] if lit_side else snow[1])
            if tline is not None and y > tline:
                c = paint(trees[1] if hash01(x, y // 3, seed + 9) < 0.38 else trees[0])
            if haze and y > haze[1] and bayer(x, y) < haze[2] * (y - haze[1]) / max(1, H - haze[1]):
                c = paint(haze[0])
            px[x, y] = c
    return prof


def mist(art: Art, seed: int, y0: int, y1: int, count: int, color: str, length: tuple = (120, 320), thick: tuple = (5, 14)) -> None:
    px = art.img.load()
    col = paint(color)
    for i in range(count):
        cx, cy = hash01(i, 1, seed) * W, y0 + hash01(i, 2, seed) * (y1 - y0)
        size = length[0] + hash01(i, 3, seed) * (length[1] - length[0])
        t = thick[0] + hash01(i, 4, seed) * (thick[1] - thick[0])
        for r in range(int(-t), int(t) + 1):
            f = abs(r) / t
            half = size * 0.5 * (1.0 - f ** 1.6) ** 0.5 if f < 1 else 0
            y = int(cy + r)
            if not 0 <= y < H:
                continue
            for x in range(int(cx - half), int(cx + half)):
                edge = min(1.0, (half - abs(x - cx)) / 14.0)
                if bayer(x, y) < (1.0 - f) * 1.5 * edge + 0.05:
                    px[x % W, y] = col


def lavafall(art: Art, x: float, y0: float, y1: float, width: float, colors: tuple, seed: int = 0) -> None:
    hot, body, ember = colors
    art.glow(x, y1, width * 5, body, 0.4, 1.4, 0.5)
    for y in range(int(y0), int(y1)):
        sway = math.sin(y * 0.11 + seed) * 1.5
        w = width * (0.8 + 0.3 * math.sin(y * 0.3 + seed))
        art.rect(x + sway - w / 2 - 1, y, x + sway + w / 2 + 1, y, ember)
        art.rect(x + sway - w / 2, y, x + sway + w / 2, y, body)
        if hash01(y // 3, seed, 4) < 0.8:
            art.rect(x + sway - w / 6, y, x + sway + w / 6, y, hot)


def forge(art: Art, cx: float, base: float, width: float, height: float, colors: tuple, fire: tuple) -> None:
    body, rim = colors
    hot, lava_c, ember = fire
    art.glow(cx, base - height * 0.25, width * 0.9, lava_c, 0.35, 1.4)
    for k, (wf, hf) in enumerate(((1.0, 0.45), (0.74, 0.75), (0.46, 1.0))):
        art.rect(cx - width * wf / 2, base - height * hf, cx + width * wf / 2, base, body)
        art.rect(cx - width * wf / 2, base - height * hf, cx + width * wf / 2, base - height * hf, rim)
    for side in (-1, 1):
        art.rect(cx + side * width * 0.3 - 3, base - height * 1.35, cx + side * width * 0.3 + 3, base - height * 0.7, body)
        art.rect(cx + side * width * 0.3 - 4, base - height * 1.35, cx + side * width * 0.3 + 4, base - height * 1.35 + 2, rim)
    aw, ah = width * 0.2, height * 0.34
    art.rect(cx - aw - 1, base - ah, cx + aw + 1, base, ember)
    art.ellipse(cx, base - ah, aw + 1, aw * 0.9 + 1, ember)
    art.rect(cx - aw + 1, base - ah, cx + aw - 1, base, lava_c)
    art.ellipse(cx, base - ah, aw - 1, aw * 0.9 - 1, lava_c)
    art.ellipse(cx, base - ah * 0.5, aw * 0.5, ah * 0.5, hot)


def islands(art: Art, seed: int, y: int, count: int, colors: tuple, width: tuple = (30, 90)) -> None:
    for i in range(count):
        cx = hash01(i, 1, seed) * W
        w = width[0] + hash01(i, 2, seed) * (width[1] - width[0])
        h = w * (0.12 + 0.14 * hash01(i, 3, seed))
        art.poly([(cx - w / 2, y), (cx - w * 0.2, y - h), (cx + w * 0.1, y - h * 0.7), (cx + w * 0.28, y - h * 0.9), (cx + w / 2, y)], colors[0])
        art.poly([(cx - w * 0.2, y - h), (cx + w * 0.1, y - h * 0.7), (cx - w * 0.05, y - h * 0.3)], colors[1])


def birds(art: Art, seed: int, count: int, y0: int, y1: int, color: str) -> None:
    for i in range(count):
        x, y = int(hash01(i, 1, seed) * W), int(y0 + hash01(i, 2, seed) * (y1 - y0))
        for dx, dy in ((-2, -1), (-1, 0), (0, 1), (1, 0), (2, -1)) if hash01(i, 3, seed) < 0.6 else ((-1, -1), (0, 0), (1, -1)):
            art.px(x + dx, y + dy, color)


def sparkles(art: Art, seed: int, count: int, box: tuple, color: str = "#ffffff") -> None:
    for i in range(count):
        x = int(box[0] + hash01(i, 1, seed) * (box[2] - box[0]))
        y = int(box[1] + hash01(i, 2, seed) * (box[3] - box[1]))
        art.px(x, y, color)
        if hash01(i, 3, seed) < 0.45:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                art.px(x + dx, y + dy, color)


def strata_lines(art: Art, colors: tuple, seed: int = 0, spacing: int = 8, x0: int = 0, x1: int = W) -> None:
    body, lit, joint = paint(colors[0]), paint(colors[1]), paint(colors[2])
    px = art.img.load()
    for x in range(x0, x1):
        bend = 3 * math.sin(x * 0.045 + seed) + 2 * math.sin(x * 0.11)
        for y in range(H):
            if px[x % W, y] != body:
                continue
            v = int(y + bend)
            layer = v // spacing
            if v % spacing == 0 and hash01(x // 11, layer, seed) < 0.85:
                px[x % W, y] = joint
            elif hash01(layer, 1, seed) < 0.35:
                px[x % W, y] = lit


def light_spill(art: Art, lights: list, power: float = 0.7) -> None:
    px = art.img.load()
    for lx, ly, r, color in lights:
        lc = rgba(color)
        for y in range(max(0, int(ly - r)), min(H, int(ly + r) + 1)):
            for x in range(int(lx - r), int(lx + r) + 1):
                p = px[x % W, y]
                if not p[3]:
                    continue
                d = math.hypot(x - lx, y - ly) / r
                if d < 1.0 and bayer(x, y) < power * (1.0 - d) ** 1.2:
                    px[x % W, y] = (round(p[0] * 0.45 + lc[0] * 0.55), round(p[1] * 0.45 + lc[1] * 0.55), round(p[2] * 0.45 + lc[2] * 0.55), 255)


def plates(art: Art, y0: int, colors: tuple, seed: int = 0, count: int = 90) -> None:
    hot, body, crust, rim = colors
    px = art.img.load()
    for y in range(max(0, y0 - 80), y0):
        p = 0.6 * ((y - (y0 - 80)) / 80) ** 1.5
        for x in range(W):
            if bayer(x, y) < p:
                px[x, y] = paint(body)
    art.rect(0, y0, W, H, body)
    art.rect(0, y0, W, y0 + 1, hot)
    for i in sorted(range(count), key=lambda k: hash01(k, 1, seed)):
        t = hash01(i, 1, seed) ** 0.8
        y = y0 + 4 + t * (H - y0)
        x = hash01(i, 2, seed) * W
        w, h = (10 + 46 * t) * (0.6 + 0.8 * hash01(i, 3, seed)), 2 + 7 * t
        art.ellipse(x, y, w, h, rim)
        art.ellipse(x, y + 1, w - 1, h - 1, crust)
    for i in range(70):
        t = hash01(i, 4, seed)
        y = int(y0 + 2 + t * (H - y0 - 3))
        x = int(hash01(i, 5, seed) * W)
        for dx in range(3 + int(12 * t)):
            if px[(x + dx) % W, y] == paint(body):
                px[(x + dx) % W, y] = paint(hot)
