from __future__ import annotations

import math
from contextlib import contextmanager

from PIL import Image

from vec import Canvas, capsule, curve, ellipse, mix, rgba, ribbon, smooth

OUT = "#1c1433"
K, KL, KD = "#c0297f", "#ff8ad0", "#7d1a5c"
HOT = "#ffd0ee"
WHITE = "#ffffff"
TAU = 2 * math.pi

OUTLINES = (OUT, "#163c2c")

CREATURES: list[dict] = []


def creature(name: str, theme: str, tier: int, size=(32, 32), origin=(16, 31), water: bool = False, **anims):
    def wrap(fn):
        table = {}
        for key, spec in anims.items():
            spec = dict(frames=spec[0], fps=spec[1]) if isinstance(spec, tuple) else dict(spec)
            spec.setdefault("loop", key not in ("attack", "rise", "dive", "shoot"))
            table[key] = spec
        entry = {"id": fn.__name__, "name": name, "theme": theme, "tier": tier,
                 "size": size, "origin": origin, "water": water, "anims": table, "draw": fn}
        for k, old in enumerate(CREATURES):
            if old["id"] == entry["id"]:
                CREATURES[k] = entry
                break
        else:
            CREATURES.append(entry)
        return fn
    return wrap


def wave(i: float, n: float, amp: float = 1.0, phase: float = 0.0) -> float:
    return amp * math.sin(TAU * i / n + phase)


def pick(seq, i: int):
    return seq[min(i, len(seq) - 1)]


def dark(color, t: float = 0.3):
    return mix(color, OUT, t)


def light(color, t: float = 0.3):
    return mix(color, WHITE, t)


class Pen(Canvas):

    def __init__(self, w: float, h: float, origin) -> None:
        super().__init__(w, h, origin=origin)
        self.m = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0)
        self.fx: list[tuple[int, int, tuple]] = []
        self.outline = OUT

    def _map(self, pt) -> tuple[float, float]:
        a, b, tx, c, d, ty = self.m
        return (a * pt[0] + b * pt[1] + tx, c * pt[0] + d * pt[1] + ty)

    def _px(self, pts: list) -> list:
        return super()._px([self._map(q) for q in pts])

    def _cell(self, pos) -> tuple[int, int]:
        x, y = self._map(pos)
        return int(math.floor(x + self.origin[0])), int(math.floor(y + self.origin[1]))

    def dot(self, pos, color, w: int = 1, h: int = 1) -> None:
        x0, y0 = self._cell(pos)
        for j in range(h):
            for i in range(w):
                self.dots.append((x0 + i, y0 + j, rgba(color)))

    def glow(self, pos, color, w: int = 1, h: int = 1) -> None:
        x0, y0 = self._cell(pos)
        for j in range(h):
            for i in range(w):
                self.fx.append((x0 + i, y0 + j, rgba(color)))

    def line(self, a, b, color, glow: bool = False) -> None:
        (x0, y0), (x1, y1) = self._cell(a), self._cell(b)
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        target = self.fx if glow else self.dots
        for k in range(n + 1):
            target.append((round(x0 + (x1 - x0) * k / n), round(y0 + (y1 - y0) * k / n), rgba(color)))

    @contextmanager
    def pose(self, dx: float = 0.0, dy: float = 0.0, rot: float = 0.0, pivot=(0.0, 0.0), sx: float = 1.0, sy: float = 1.0):
        old = self.m
        r = math.radians(rot)
        la, lb, lc, ld = math.cos(r) * sx, -math.sin(r) * sy, math.sin(r) * sx, math.cos(r) * sy
        ltx = pivot[0] - la * pivot[0] - lb * pivot[1] + dx
        lty = pivot[1] - lc * pivot[0] - ld * pivot[1] + dy
        a, b, tx, c, d, ty = old
        self.m = (a * la + b * lc, a * lb + b * ld, a * ltx + b * lty + tx,
                  c * la + d * lc, c * lb + d * ld, c * ltx + d * lty + ty)
        try:
            yield
        finally:
            self.m = old

    def oval(self, c, rx: float, ry: float, color, rot: float = 0.0) -> None:
        self.poly(ellipse(c, rx, ry, math.radians(rot)), color)

    def blob(self, pts, color, rounds: int = 2) -> None:
        self.poly(smooth(list(pts), rounds), color)

    def limb(self, a, b, r: float, color, r2: float | None = None) -> None:
        self.poly(capsule(a, b, r, r2), color)

    def band(self, pts, w0: float, w1: float, color) -> None:
        self.poly(ribbon(curve(list(pts)), w0, w1), color)

    def tri(self, a, b, c, color) -> None:
        self.poly([a, b, c], color)

    def inside(self, shape: list, region: list, color) -> None:
        self.clip(shape, region, color)

    def done(self) -> Image.Image:
        img = self.finish(outline=self.outline)
        px = img.load()
        for x, y, col in self.fx:
            if 0 <= x < img.width and 0 <= y < img.height:
                px[x, y] = col
        return img


def wing(p: Pen, root, span: float, lift: float, color, tip, feathers: int = 4, drop: float = 5.0) -> None:
    a = math.radians(lift)
    end = (root[0] - span * math.cos(a), root[1] - span * math.sin(a))
    for k in range(feathers):
        t = (k + 1) / feathers
        base = (root[0] + (end[0] - root[0]) * t, root[1] + (end[1] - root[1]) * t)
        fall = drop * (0.55 + 0.45 * t)
        p.blob([(base[0] + 2.2, base[1] - 0.6), (base[0] - 1.2, base[1] - 0.8),
                (base[0] - 2.0 - math.sin(a) * 1.5, base[1] + fall), (base[0] + 0.8, base[1] + fall * 0.7)],
               tip if k == feathers - 1 else color, 1)
    p.limb(root, end, 1.5, color, 1.0)


def hurt_of(img: Image.Image) -> Image.Image:
    out = img.copy()
    px = out.load()
    edges = {rgba(c) for c in OUTLINES}
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if a and (r, g, b, a) not in edges:
                px[x, y] = rgba(WHITE) if 0.3 * r + 0.59 * g + 0.11 * b > 150 else rgba(HOT)
    return out


def body_center(img: Image.Image) -> tuple[int, int]:
    box = img.getbbox() or (0, 0, img.width, img.height)
    return (box[0] + box[2]) // 2, (box[1] + box[3]) // 2
