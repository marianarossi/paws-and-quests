from __future__ import annotations

import json
import math
import os

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ASSETS = os.path.join(ROOT, "assets")
DOCS_PREVIEW = os.path.join(ROOT, "docs", "preview")

C = {
    "outline": "#151229",
    "skin": "#f4cba8", "skin_d": "#dba182", "hair": "#5b3428", "hair_l": "#8c5538", "eye": "#1d1933",
    "jacket": "#f7ab3c", "jacket_d": "#dc7d2b", "jacket_l": "#ffd47a",
    "pants": "#35446f", "pants_d": "#28335a", "boot": "#70493a", "boot_d": "#523429",
    "pack": "#2f9486", "pack_d": "#216b69", "roll": "#f1dcae", "roll_d": "#cfae7c",
    "fur": "#cf8e4c", "fur_l": "#ecbd7c", "fur_d": "#a86c37",
    "soil": "#2e264b", "soil_l": "#4a3d74", "soil_d": "#1f1937", "stone": "#5d5488",
    "grass": "#3ccb9b", "grass_l": "#a6f7c6", "grass_d": "#1f8c85", "moss": "#2a6e79",
    "wood": "#8a5a41", "wood_l": "#b98458", "wood_d": "#5b3a30",
    "fire0": "#ee5a2c", "fire1": "#f9a33a", "fire2": "#ffe08c", "fire3": "#fff7dc",
    "red": "#d8443c", "white": "#ffffff", "mint": "#7ff2d4", "mint_l": "#d6fff2",
}


def rgba(color, alpha: int | None = None) -> tuple[int, int, int, int]:
    if isinstance(color, str):
        h = C.get(color, color).lstrip("#")
        out = (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)
    else:
        out = tuple(color) if len(color) == 4 else tuple(color) + (255,)
    return out if alpha is None else out[:3] + (alpha,)


def mix(a, b, t: float) -> tuple[int, int, int, int]:
    ca, cb = rgba(a), rgba(b)
    return tuple(int(round(ca[i] + (cb[i] - ca[i]) * t)) for i in range(4))


def hash01(x: int, y: int = 0, seed: int = 0) -> float:
    n = (int(x) * 374761393 + int(y) * 668265263 + int(seed) * 2246822519) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    n ^= n >> 16
    return (n & 0xFFFFFF) / 0x1000000


def ellipse(c, rx: float, ry: float | None = None, rot: float = 0.0, n: int = 28) -> list:
    ry = rx if ry is None else ry
    cr, sr = math.cos(rot), math.sin(rot)
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x, y = rx * math.cos(t), ry * math.sin(t)
        pts.append((c[0] + x * cr - y * sr, c[1] + x * sr + y * cr))
    return pts


def capsule(a, b, ra: float, rb: float | None = None, n: int = 10) -> list:
    rb = ra if rb is None else rb
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    pts = []
    for i in range(n + 1):
        t = ang + math.pi / 2 + math.pi * i / n
        pts.append((a[0] + ra * math.cos(t), a[1] + ra * math.sin(t)))
    for i in range(n + 1):
        t = ang - math.pi / 2 + math.pi * i / n
        pts.append((b[0] + rb * math.cos(t), b[1] + rb * math.sin(t)))
    return pts


def smooth(pts: list, iterations: int = 3) -> list:
    for _ in range(iterations):
        out = []
        for i, p in enumerate(pts):
            q = pts[(i + 1) % len(pts)]
            out.append((p[0] * 0.75 + q[0] * 0.25, p[1] * 0.75 + q[1] * 0.25))
            out.append((p[0] * 0.25 + q[0] * 0.75, p[1] * 0.25 + q[1] * 0.75))
        pts = out
    return pts


def curve(pts: list, steps: int = 6) -> list:
    if len(pts) < 3:
        return list(pts)
    ext = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for s in range(steps):
            t = s / steps
            out.append(tuple(
                0.5 * (2 * p1[k] + (p2[k] - p0[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t * t
                       + (3 * p1[k] - p0[k] - 3 * p2[k] + p3[k]) * t ** 3) for k in (0, 1)))
    out.append(pts[-1])
    return out


def ribbon(center: list, w0: float, w1: float) -> list:
    left, right = [], []
    n = len(center)
    for i, p in enumerate(center):
        a, b = center[max(0, i - 1)], center[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1.0
        w = w0 + (w1 - w0) * i / max(1, n - 1)
        left.append((p[0] - dy / d * w, p[1] + dx / d * w))
        right.append((p[0] + dy / d * w, p[1] - dx / d * w))
    return left + right[::-1]


def ik(a, b, l1: float, l2: float, bend: int) -> tuple[tuple, tuple]:
    dx, dy = b[0] - a[0], b[1] - a[1]
    full = math.hypot(dx, dy) or 0.01
    d = max(0.05, min(full, l1 + l2 - 0.02))
    base = math.atan2(dy, dx)
    ang = math.acos(max(-1.0, min(1.0, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))))
    k1 = (a[0] + l1 * math.cos(base + ang), a[1] + l1 * math.sin(base + ang))
    k2 = (a[0] + l1 * math.cos(base - ang), a[1] + l1 * math.sin(base - ang))
    joint = k1 if (k1[0] - k2[0]) * bend >= 0 else k2
    return joint, (a[0] + dx / full * d, a[1] + dy / full * d)


class Canvas:

    def __init__(self, w: float, h: float, ppu: int = 1, ss: int = 5, origin=(0.0, 0.0)):
        self.k = ppu * ss
        self.ppu = ppu
        self.ss = ss
        self.origin = origin
        self.img = Image.new("RGBA", (int(round(w * self.k)), int(round(h * self.k))), (0, 0, 0, 0))
        self.dots: list[tuple[int, int, tuple]] = []

    def _px(self, pts: list) -> list:
        ox, oy = self.origin
        return [((x + ox) * self.k, (y + oy) * self.k) for x, y in pts]

    def poly(self, pts: list, color, _alpha: int | None = None) -> None:
        ImageDraw.Draw(self.img).polygon(self._px(pts), fill=rgba(color))

    def clip(self, shape: list, region: list, color, _alpha: int | None = None) -> None:
        m1 = Image.new("L", self.img.size, 0)
        ImageDraw.Draw(m1).polygon(self._px(shape), fill=255)
        m2 = Image.new("L", self.img.size, 0)
        ImageDraw.Draw(m2).polygon(self._px(region), fill=255)
        self.img.paste(rgba(color), (0, 0), ImageChops.multiply(m1, m2))

    def dot(self, pos, color, w: int = 1, h: int = 1) -> None:
        x0 = int(math.floor((pos[0] + self.origin[0]) * self.ppu))
        y0 = int(math.floor((pos[1] + self.origin[1]) * self.ppu))
        for j in range(h):
            for i in range(w):
                self.dots.append((x0 + i, y0 + j, rgba(color)))

    def finish(self, outline=None, **_ignored) -> Image.Image:
        w, h = self.img.size
        palette: dict[tuple, int] = {}
        index = bytearray(w * h)
        for i, p in enumerate(self.img.getdata()):
            if p[3] >= 128:
                index[i] = palette.setdefault(p, len(palette) + 1)
        small = Image.frombytes("L", (w, h), bytes(index)).filter(ImageFilter.ModeFilter(self.ss))
        small = small.resize((w // self.ss, h // self.ss), Image.NEAREST)
        lut = {v: c for c, v in palette.items()}
        out = Image.new("RGBA", small.size, (0, 0, 0, 0))
        out.putdata([lut.get(v, (0, 0, 0, 0)) for v in small.getdata()])
        px = out.load()
        for x, y, col in self.dots:
            if 0 <= x < out.width and 0 <= y < out.height:
                px[x, y] = col
        if outline:
            col = rgba(outline)
            edge = []
            for y in range(out.height):
                for x in range(out.width):
                    if px[x, y][3] == 0 and any(
                            0 <= x + dx < out.width and 0 <= y + dy < out.height and px[x + dx, y + dy][3] != 0
                            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                        edge.append((x, y))
            for x, y in edge:
                px[x, y] = col
        return out


def save(img: Image.Image, *parts: str) -> str:
    path = os.path.join(ASSETS, *parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    return path


def save_json(data: dict, *parts: str) -> str:
    path = os.path.join(ASSETS, *parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    return path


def pack(sprites: list[tuple[str, Image.Image]], width: int = 128, pad: int = 1) -> tuple[Image.Image, dict[str, list[int]]]:
    x = y = shelf = 0
    rects: dict[str, list[int]] = {}
    for name, im in sprites:
        if x + im.width > width:
            x, y, shelf = 0, y + shelf + pad, 0
        rects[name] = [x, y, im.width, im.height]
        x += im.width + pad
        shelf = max(shelf, im.height)
    atlas = Image.new("RGBA", (width, y + shelf), (0, 0, 0, 0))
    for name, im in sprites:
        atlas.paste(im, tuple(rects[name][:2]))
    return atlas, rects
