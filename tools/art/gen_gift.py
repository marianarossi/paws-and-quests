from __future__ import annotations

import math
import os
import sys

from PIL import Image

from note_rose import note_rose, shadow
from vec import ASSETS, DOCS_PREVIEW, rgba

W, H = 15, 20
PETAL = tuple(rgba(c) for c in ("#ffe6ee", "#ffb8cf", "#f48aae", "#d9668f", "#a8466e"))
LINE = rgba("#5c2a4c")
STEM = tuple(rgba(c) for c in ("#8cd4a0", "#58a07e", "#3c7c62"))
CX, CY, RX, RY = 7.0, 6.0, 6.2, 5.2


def bloom(px, w: int = W, h: int = H, cx: float = CX, cy: float = CY, rx: float = RX, ry: float = RY) -> None:
    W, H, CX, CY, RX, RY = w, h, cx, cy, rx, ry
    k_size = rx / 6.2
    for y in range(H):
        for x in range(W):
            u, v = (x + 0.5 - CX) / RX, (y + 0.5 - CY) / RY
            top = -1.0 + 0.16 * abs(math.sin((x + 0.5 - CX) / RX * math.pi * 1.5))
            if u * u + v * v > 1.0 or v < top:
                continue
            lum = -0.6 * u - 0.7 * v
            c = PETAL[1] if lum > 0.45 else PETAL[2] if lum > -0.15 else PETAL[3]
            if v > 0.35:
                c = PETAL[3] if abs(u) < 0.55 else PETAL[4]
                if abs(u) < 0.08 or abs(abs(u) - 0.6) < 0.08:
                    c = PETAL[4]
            px[x, y] = c
    for k in range(int(80 * k_size)):
        t = k / (80 * k_size - 1) * 2.6 * math.pi
        r = (0.5 + 0.62 * t) * k_size
        x, y = CX - 0.3 * k_size + math.cos(t) * r, CY - 0.8 * k_size + math.sin(t) * r * 0.75
        xi, yi = int(x), int(y)
        if 0 <= xi < W and 0 <= yi < H and px[xi, yi][3] and math.hypot(x - CX, (y - CY) * 1.2) < 4.6 * k_size:
            px[xi, yi] = PETAL[4]
            if yi - 1 >= 0 and px[xi, yi - 1][3] and px[xi, yi - 1] != PETAL[4]:
                px[xi, yi - 1] = PETAL[0]


def stem(px) -> None:
    light, body, dark = STEM
    for y in range(11, H - 1):
        x = 7 + (1 if y > 15 else 0)
        px[x, y] = body
        px[x + 1, y] = dark
    for x, y, c in ((5, 14, body), (4, 14, light), (3, 13, light), (4, 13, light), (5, 13, body), (6, 14, body),
                    (3, 12, body), (6, 15, dark), (5, 15, dark)):
        px[x, y] = c
    for x, y in ((10, 13), (11, 12)):
        px[x, y] = dark


def outline(img: Image.Image) -> None:
    px = img.load()
    solid = {(x, y) for y in range(H) for x in range(W) if px[x, y][3]}
    for y in range(H):
        for x in range(W):
            if (x, y) not in solid and any((x + dx, y + dy) in solid for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[x, y] = LINE


def rose() -> Image.Image:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = img.load()
    bloom(px)
    stem(px)
    outline(img)
    return img


NW, NH = 520, 200
PAPER_X, PAPER_Y = 22, 16
TEXT_X, TEXT_W = 158, 352
PAPER_SHADOW = rgba("#d3b588")
PAPER = tuple(rgba(c) for c in ("#fbefd6", "#f3e2bf", "#e8d1a6", "#d6b98a", "#b9966a"))
INK_LINE = rgba("#6b4a3a")


def note() -> Image.Image:
    img = Image.new("RGBA", (NW, NH), (0, 0, 0, 0))
    px = img.load()
    w, h = NW - PAPER_X - 3, NH - PAPER_Y - 3
    def inside(x: int, y: int) -> bool:
        u, v = x - PAPER_X, y - PAPER_Y
        wob = lambda t, k: int(1.4 * math.sin(t * 0.21 + k) + 0.9 * math.sin(t * 0.53 + 2 * k))
        if u < 1 + wob(v, 1.0) or u > w - 2 + wob(v, 4.0) or v < 1 + wob(u, 2.0) or v > h - 2 + wob(u, 3.0):
            return False
        return not (min(u, w - u) + min(v, h - v) < 5)
    solid = {(x, y) for y in range(NH) for x in range(NW) if inside(x, y)}
    fold = PAPER_Y + h // 2
    for x, y in solid:
        edge = min(d for d in range(1, 6) if any((x + dx * d, y + dy * d) not in solid
                                               for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))) if any(
            (x + dx * k, y + dy * k) not in solid for k in range(1, 6) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) else 9
        n = math.sin(x * 12.9898 + y * 78.233) * 43758.5453
        n -= math.floor(n)
        c = PAPER[1]
        if edge <= 1:
            c = PAPER[4]
        elif edge <= 2:
            c = PAPER[3]
        elif edge <= 4 and n < 0.6:
            c = PAPER[2]
        elif n < 0.035:
            c = PAPER[2]
        elif n > 0.985:
            c = PAPER[0]
        if y == fold and edge > 2:
            c = PAPER[2]
        elif y == fold + 1 and edge > 2:
            c = PAPER[0]
        px[x, y] = c
    for y in range(NH):
        for x in range(NW):
            if (x, y) not in solid and any((x + dx, y + dy) in solid for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[x, y] = INK_LINE
    rose_img = note_rose()
    shade = shadow(rose_img, PAPER_SHADOW, (3, 4))
    clipped = Image.new("RGBA", shade.size, (0, 0, 0, 0))
    cp, sp = clipped.load(), shade.load()
    for y in range(shade.height):
        for x in range(shade.width):
            if sp[x, y][3] and (x + 2, y + 2) in solid:
                cp[x, y] = sp[x, y]
    img.alpha_composite(clipped, (2, 2))
    img.alpha_composite(rose_img, (2, 2))
    return img


def main() -> None:
    img = rose()
    out = os.path.join(ASSETS, "sprites", "props", "gift_rose.png")
    img.save(out)
    note().save(os.path.join(ASSETS, "sprites", "props", "gift_note.png"))
    if "--preview" in sys.argv:
        bg = Image.new("RGBA", (W + 8, H + 8), rgba("#1c1a33"))
        bg.alpha_composite(img, (4, 4))
        path = os.path.join(DOCS_PREVIEW, "ember", "presente_rosa.png")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        bg.resize((bg.width * 10, bg.height * 10), Image.NEAREST).save(path)
        nb = Image.new("RGBA", (NW + 16, NH + 16), rgba("#1c1a33"))
        nb.alpha_composite(note(), (8, 8))
        nb.resize((nb.width * 3, nb.height * 3), Image.NEAREST).save(os.path.join(DOCS_PREVIEW, "ember", "bilhete.png"))
        print("previa:", path)
    print("presente: ok")


if __name__ == "__main__":
    main()
