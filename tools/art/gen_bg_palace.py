from __future__ import annotations

import math
import os
import sys

from PIL import Image, ImageDraw

import gen_gate as gate
from gen_bg_ember import H, W, gradient, lerp
from gen_bg_grove import Sheet
from gen_bg_olympus import blank, mass
from gen_bg_hollow import fan
from vec import ASSETS, DOCS_PREVIEW, hash01, rgba, save
from zonekit import Art, bayer, fog


ZONE = "zeus_palace"
HORIZON = 292
SKY = [(0, "#0b0a1d"), (70, "#121029"), (150, "#1b1838"), (220, "#262049"), (270, "#2f2757"), (HORIZON, "#352b5d"), (H, "#3a2f63")]

FAR = ("#3a3363", "#58508c", "#2a2549", "#1b1730")
MID = ("#463d74", "#6c62a6", "#312a58", "#1d1934")
MOSS = ("#3f7462", "#64a07c", "#2c5a4c", "#8cc890")
MOSS_ROOM = ("#58a07e", "#8cd4a0", "#3c7c62", "#bcf4bc")
AMBER, AMBER_GLOW = "#ffd27a", "#ff9a4a"
BRONZE = ("#8a6a58", "#b8926a", "#5c4448")
GOLD = ("#c8a050", "#f0d080", "#8a6c40")
VIOLET = rgba("#4a3c7c")
WET = rgba("#8e80b4")

INDIGO = ("#a2a6de", "#787cc2", "#53569a", "#373770")
STORM_BLUE = ("#a6bce8", "#7a94d0", "#5468a8", "#384480")
PLUM = ("#c6b0e6", "#9e84cc", "#775ca8", "#503e82")
MAUVE = ("#d4aed2", "#b488be", "#8e629c", "#64447c")
TEAL = ("#acdcd8", "#78bcc2", "#4a8ea4", "#346284")
LIGHT = (-0.35, -0.9)


def tones(colors: tuple) -> tuple:
    return tuple(rgba(c) for c in colors)


def sky() -> Image.Image:
    img = Image.new("RGBA", (W, H))
    px = img.load()
    for y in range(H):
        row = gradient(SKY, y)
        for x in range(W):
            px[x, y] = row
    return img


def flare(img: Image.Image, cx: float, cy: float, rx: float, ry: float, color: str, strength: float) -> None:
    px = img.load()
    glow = rgba(color)
    for y in range(max(0, int(cy - ry)), min(H, int(cy + ry) + 1)):
        for x in range(int(cx - rx), int(cx + rx) + 1):
            q = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            c = px[x % W, y]
            if q < 1 and c[3]:
                m = lerp(c, glow, round((1 - q) * 4) / 4 * strength)
                px[x % W, y] = (m[0], m[1], m[2], c[3])


def drifting() -> Image.Image:
    img = blank()
    for seed, cx, base, width, height, pals in ((61, 250, 150, 150, 54, (TEAL, STORM_BLUE, INDIGO)), (73, 486, 118, 130, 46, (MAUVE, PLUM, INDIGO)),
                                                (85, 40, 112, 130, 50, (PLUM, MAUVE, INDIGO)), (97, 610, 196, 90, 34, (STORM_BLUE, PLUM, INDIGO))):
        mass(img, seed, cx, base, width, height, pals, LIGHT, scale=0.6, soft=True)
    flare(img, 486, 100, 40, 18, "#c8d8f4", 0.25)
    return img


def anvils() -> Image.Image:
    img = blank()
    haze = "#41346c"
    for seed, cx, width, height, pals in ((11, 120, 300, 222, (INDIGO, PLUM, MAUVE)), (27, 548, 250, 178, (STORM_BLUE, INDIGO, PLUM)),
                                          (43, 330, 170, 100, (PLUM, MAUVE, TEAL))):
        mass(img, seed, cx, HORIZON + 6, width, height, pals, LIGHT, haze, 110)
    flare(img, 130, 150, 64, 36, "#c8d4f4", 0.28)
    flare(img, 550, 196, 46, 26, "#bcdcec", 0.24)
    return img


def column_px(px, cx: int, top: int, base: int, half: int, pal: tuple, capital: bool = True) -> None:
    body, lit, dark, line = tones(pal)
    for y in range(max(0, top), min(H, base)):
        h = base - y
        width = half + (3 if capital and y < top + 5 else 2 if capital and y < top + 9 else 2 if h <= 4 else 0)
        for x in range(cx - width, cx + width + 1):
            f = (x - (cx - width)) / max(1, 2 * width)
            c = lit if f < 0.22 else dark if f > 0.7 else body
            if width == half and (x - cx) % 4 == 0 and 0.1 < f < 0.9:
                c = dark if c == body else line if c == dark else body
            if capital and y in (top + 4, top + 8):
                c = line
            if x in (cx - width, cx + width):
                c = line
            px[x % W, y] = c


def moss(px, x0: int, x1: int, seed: int, hang: int = 6, thick: int = 3) -> None:
    body, lit, dark, tip = tones(MOSS)
    for x in range(x0, x1):
        xx = x % W
        for y in range(1, H - 1):
            if not px[xx, y][3] or px[xx, y - 1][3] or px[xx, y][:3] in (body[:3], lit[:3], dark[:3], tip[:3]):
                continue
            if hash01(x // 3, y // 3, seed) > 0.55:
                continue
            t = 1 + int(hash01(x, y, seed + 1) * thick)
            for k in range(t):
                if y + k < H and px[xx, y + k][3]:
                    px[xx, y + k] = tip if k == 0 and hash01(x, y, seed + 2) < 0.25 else lit if k == 0 else body if k < t - 1 else dark
            if hash01(x, y, seed + 3) < 0.12:
                px[xx, y - 1] = lit
    for x in range(x0, x1):
        xx = x % W
        for y in range(1, H - 1):
            c = px[xx, y]
            if c[3] and c[:3] in (body[:3], dark[:3]) and not px[xx, y + 1][3] and hash01(x, y, seed + 4) < 0.35:
                for k in range(1, 1 + int(hash01(x, y, seed + 5) * hang)):
                    if y + k < H and not px[xx, y + k][3]:
                        px[xx, y + k] = dark if k > 2 else body


def lamp(art: Art, x: int, y0: int, y1: int, size: float = 1.0) -> None:
    for y in range(y0, y1):
        if y % 3:
            art.px(x, y, BRONZE[2] if y % 3 == 1 else BRONZE[0])
    s = size
    art.glow(x, y1 + 4 * s, 22 * s, AMBER_GLOW, 0.4, 1.8)
    art.poly([(x - 7 * s, y1), (x + 7 * s, y1), (x + 4 * s, y1 + 5 * s), (x - 4 * s, y1 + 5 * s)], BRONZE[0])
    art.rect(x - 7 * s, y1, x + 7 * s, y1, BRONZE[1])
    art.rect(x - 2 * s, y1 + 5 * s, x + 2 * s, y1 + 6 * s, BRONZE[2])
    art.poly([(x - 2 * s, y1), (x, y1 - 5 * s), (x + 2 * s, y1)], AMBER)
    art.px(x, y1 - 2 * s, "#fff4d0")


def far_layer() -> Image.Image:
    art = Art()
    body, lit, dark, line = FAR
    art.rect(0, HORIZON - 4, W, H, dark)
    art.rect(0, HORIZON - 4, W, HORIZON - 4, lit)
    for y in range(HORIZON + 3, H, 7):
        art.rect(0, y, W, y, body)
    art.rect(0, 252, W, HORIZON - 5, body)
    art.rect(0, 252, W, 253, lit)
    art.rect(0, 260, W, 260, line)
    for i in range(32):
        art.rect(i * 20 + 4, 262, i * 20 + 12, HORIZON - 8, dark)
    px = art.img.load()
    for i in range(8):
        column_px(px, 40 + 80 * i, 92, HORIZON - 4, 10, FAR)
    for x in range(W):
        for y in range(62, 92):
            j = y - 62
            c = rgba(lit if j in (0, 13) else line if j in (12, 29) else dark if j > 24 else body)
            if 14 <= j < 24 and x % 18 < 6:
                c = rgba(dark if x % 18 in (0, 5) else lit if x % 18 == 1 else body)
            px[x, y] = c
    gate.outline(art.img, rgba(line))
    moss(px, 0, W, 51, hang=5, thick=2)
    for i in range(8):
        if i % 3 != 1:
            cx = 40 + 80 * i
            ivy(px, cx - 6 + int(hash01(i, 1, 52) * 12), HORIZON - 6, 150 + int(hash01(i, 2, 52) * 70), 60 + i)
    for i in range(8):
        cx = 40 + 80 * i
        crack(px, cx - 4 + int(hash01(i, 4, 52) * 8), 100 + int(hash01(i, 5, 52) * 120), 14 + int(hash01(i, 6, 52) * 26), 54 + i, rgba(line), rgba(lit))
        if i % 2:
            crack(px, cx + 20, 64, 10 + int(hash01(i, 7, 52) * 14), 64 + i, rgba(line), rgba(lit), 0.0)
    for x in (120, 440, 600):
        lamp(art, x, 92, 150 + (x % 7) * 3, 0.7)
    return art.img


def crack(px, x: float, y: int, length: int, seed: int, color: tuple, edge: tuple | None = None, drop: float = 1.0,
          w: int = W, h: int = H) -> None:
    xf = float(x)
    for k in range(length):
        if hash01(k, 1, seed) < drop * 0.75:
            y += 1
        else:
            xf += 1 if hash01(k, 2, seed) < 0.5 else -1
        if drop < 0.5:
            xf += 1
        xi = int(xf) % w
        if not (0 <= y < h) or not px[xi, y][3]:
            return
        px[xi, y] = color
        if edge and hash01(k, 3, seed) < 0.3 and 0 <= y - 1 and px[(xi + 1) % w, y][3]:
            px[(xi + 1) % w, y] = edge
        if k == length // 2:
            bx, by = xi, y
            for j in range(length // 4):
                bx += -1 if hash01(j, 4, seed) < 0.6 else 0
                by += 1
                if 0 <= by < h and px[bx % w, by][3]:
                    px[bx % w, by] = color


CLAW = (rgba("#5e4a66"), rgba("#86708c"), rgba("#fffdf6"))


def claw_marks(img: Image.Image, sets: tuple) -> None:
    px = img.load()
    stone = {c[:3] for pal in (gate.SUN, gate.SHADE, gate.DEEP) for c in pal}
    groove, end, rim = CLAW
    for x0, y0, length, lean in sets:
        for k in range(4):
            for j in range(length - abs(k - 1)):
                t = j / float(length)
                x = int(round(x0 + k * 2.4 + lean * j + 1.2 * math.sin(t * math.pi)))
                y = y0 + j
                if 0 <= x < img.width - 1 and 0 <= y < img.height and px[x, y][3] and px[x, y][:3] in stone:
                    px[x, y] = groove if 2 < j < length - 3 else end
                    if j % 2 and px[x + 1, y][3] and px[x + 1, y][:3] in stone:
                        px[x + 1, y] = rim


def ivy(px, x: float, y0: int, y1: int, seed: int, pal: tuple = MOSS, w: int = W) -> None:
    body, lit, dark, tip = tones(pal)
    for k, y in enumerate(range(y0, y1, -1)):
        r = hash01(k, 1, seed)
        x += 1 if r < 0.22 else -1 if r > 0.8 else 0
        xi = int(x) % w
        if not px[xi, y][3]:
            continue
        px[xi, y] = dark
        if hash01(k, 2, seed) < 0.55:
            side = -1 if hash01(k, 3, seed) < 0.5 else 1
            if px[(xi + side) % w, y][3]:
                px[(xi + side) % w, y] = lit if hash01(k, 4, seed) < 0.5 else body


def hang_vine(px, x: int, y0: int, length: int, seed: int) -> None:
    body, lit, dark, tip = tones(MOSS)
    xf = float(x)
    for k in range(length):
        y = y0 + k
        if not 0 <= y < H:
            break
        xf += 0.5 * math.sin(k * 0.25 + seed)
        xi = int(xf) % W
        px[xi, y] = dark
        if hash01(k, 1, seed) < 0.5:
            px[(xi + (1 if hash01(k, 2, seed) < 0.5 else -1)) % W, y] = lit if hash01(k, 3, seed) < 0.5 else body
        if k == length - 1:
            px[xi, y] = tip


def coffered_roof(art: Art) -> None:
    px = art.img.load()
    body, lit, dark, line = tones(MID)
    dull = rgba("#9a8462")
    for x in range(W):
        for y in range(0, 50):
            k, j = x % 32, y
            c = body
            if j >= 44:
                c = line if j == 49 else lit if j == 44 else dark
            elif 6 <= j < 38 and 4 <= k < 28:
                c = dark if j < 10 or k < 8 else rgba("#262048")
                d = math.hypot(k - 16, j - 22)
                tarnished = hash01(x // 32, 1, 18) < 0.35
                if d <= 4.5:
                    c = dull if tarnished else rgba(GOLD[0]) if d > 2.4 else rgba(GOLD[1])
                elif d < 6:
                    c = rgba("#1e1a3a")
            elif j in (5, 38) or k in (3, 28):
                c = line
            elif j < 5:
                c = dark
            px[x, y] = c
    for i in range(9):
        crack(px, hash01(i, 2, 18) * W, 39 + int(hash01(i, 3, 18) * 4), 18 + int(hash01(i, 4, 18) * 30), 19 + i, line, lit, 0.15)


def mid_layer() -> Image.Image:
    art = Art()
    px = art.img.load()
    body, lit, dark, line = tones(MID)
    for cx in (0, 320):
        column_px(px, cx, -10, 316, 26, MID, capital=False)
        for y in (58, 59, 60, 62):
            for x in range(cx - 26, cx + 27):
                px[x % W, y] = rgba(GOLD[1] if y == 58 else GOLD[0] if y < 62 else GOLD[2])
    coffered_roof(art)
    gate.outline(art.img, line)
    moss(px, 0, W, 61, hang=9, thick=3)
    for cx, seed in ((0, 71), (320, 72)):
        for k in range(3):
            ivy(px, cx - 20 + k * 18 + hash01(k, 1, seed) * 6, 315, 160 + int(hash01(k, 2, seed) * 120), seed + k)
    for k in range(16):
        x = int(hash01(k, 1, 17) * W)
        if px[x, 49][3] and not (-30 < x - 320 < 30 or x < 30 or x > W - 30):
            hang_vine(px, x, 50, 10 + int(hash01(k, 3, 17) * 44), 90 + k)
    for cx in (0, 320):
        for k in range(4):
            crack(px, cx - 18 + k * 11 + hash01(k, 1, cx + 5) * 5, 74 + int(hash01(k, 2, cx + 5) * 200), 18 + int(hash01(k, 3, cx + 5) * 34),
                  cx + 6 + k, line, lit)
    for x, y1 in ((58, 150), (170, 112), (250, 124), (430, 140), (548, 118)):
        lamp(art, x, 50, y1, 1.0)
    return art.img


def shafts() -> Image.Image:
    art = Art()
    for (a0, a1) in ((60, 120), (180, 236), (360, 420), (470, 530)):
        for alpha, inset in ((40, 0), (54, 9)):
            art.poly([(a0 + inset, 50), (a1 - inset, 50), (a1 + 70 - inset, 316), (a0 + 70 + inset, 316)], "#dcdcff", alpha)
    return art.img


def mist() -> Image.Image:
    art = Art()
    fog(art, 41, "#9a90d0", 236, 330, 16, 30, (90, 230))
    fog(art, 42, "#b0a6e0", 280, 340, 10, 22, (120, 260))
    fog(art, 43, "#8a80c0", 140, 210, 8, 14, (120, 260))
    return art.img


def shadow(img: Image.Image, top: float, bottom: float | None = None) -> Image.Image:
    px = img.load()
    for y in range(img.height):
        t = top if bottom is None else bottom + (top - bottom) * (1.0 - y / max(1, img.height - 1))
        for x in range(img.width):
            c = px[x, y]
            if c[3]:
                m = gate.mix(c, VIOLET, t)
                px[x, y] = (m[0], m[1], m[2], c[3])
    return img


def blank_size(w: int, h: int) -> Image.Image:
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def floor(width: int) -> Image.Image:
    img = gate.floor(width, "veios")
    px = img.load()
    for x in range(12):
        for y in range(img.height):
            px[x, y] = px[x + 160, y]
    for y in range(6, img.height):
        for x in range(width):
            if px[x, y] in (gate.IVY, gate.IVY_L, gate.IVY_D, gate.BLOOM):
                px[x, y] = gate.SUN[0] if y < 26 else px[x, y - 1] if y < 30 else gate.SHADE[0]
    for x in range(width):
        wet = fan(x * 0.011, 61) * 0.7 + fan(x * 0.05, 62) * 0.3
        if wet < 0.5:
            continue
        for y in range(1, 6):
            if wet - 0.5 > bayer(x, y) * 0.12:
                px[x, y] = gate.mix(px[x, y], WET, 0.42 if y > 1 else 0.2)
        if x % 4 == 0 and hash01(x, 1, 63) < (wet - 0.5) * 1.6:
            for y in range(7, 9 + int(hash01(x, 2, 63) * 12)):
                px[x, y] = gate.mix(px[x, y], WET, 0.3)
    for i in range(width // 14):
        x0 = int(hash01(i, 1, 64) * width)
        if fan(x0 * 0.011, 61) * 0.7 + fan(x0 * 0.05, 62) * 0.3 < 0.52:
            continue
        y = 2 + int(hash01(i, 2, 64) * 3)
        for x in range(x0, min(width, x0 + 3 + int(hash01(i, 3, 64) * 18))):
            px[x, y] = rgba("#fbf8ff") if hash01(x, 4, 64) < 0.8 else gate.SUN[1]
    return shadow(img, 0.34)


def column(height: int, clawed: bool = False) -> Image.Image:
    img = blank_size(104, height)
    gate.big_column(img, 52, height, height, 66, gate.SUN, 5)
    px = img.load()
    for k in range(7):
        x, y = 30 + int(hash01(k, 1, 3) * 44), int(height * (0.2 + 0.7 * hash01(k, 2, 3)))
        for j in range(14 + int(hash01(k, 3, 3) * 30)):
            x += 1 if hash01(k, j, 4) < 0.3 else -1 if hash01(k, j, 4) > 0.8 else 0
            if 0 <= x < img.width and px[x, y + j][3]:
                px[x, y + j] = gate.SUN[3]
    if clawed:
        g = height
        claw_marks(img, ((30, g - 34, 12, -0.3), (41, g - 27, 10, -0.2), (62, g - 33, 12, 0.25), (51, g - 24, 9, -0.25)))
    shadow(img, 0.6, 0.3)
    body, lit, dark, tip = tones(MOSS_ROOM)
    for k in range(3):
        x = 24.0 + k * 26 + hash01(k, 1, 37) * 8
        reach = int(height * (0.15 + 0.3 * hash01(k, 2, 37)))
        for j, y in enumerate(range(height - 8, height - 8 - reach, -1)):
            x += 1 if hash01(j, 1, 38 + k) < 0.22 else -1 if hash01(j, 1, 38 + k) > 0.8 else 0
            xi = int(x)
            if 0 <= xi < img.width and px[xi, y][3]:
                px[xi, y] = dark
                if hash01(j, 2, 38 + k) < 0.55:
                    side = 1 if hash01(j, 3, 38 + k) < 0.5 else -1
                    if 0 <= xi + side < img.width and px[xi + side, y][3]:
                        px[xi + side, y] = lit if hash01(j, 4, 38 + k) < 0.5 else body
    return img


def entrance(height: int) -> Image.Image:
    w = 224
    img = blank_size(w, height)
    px = img.load()
    body, lit, dark, joint = gate.SHADE
    cx, dw, dh = 112, gate.DOOR_W, gate.DOOR_H
    dx0, dx1, top = cx - dw // 2, cx + dw // 2, height - dh
    for y in range(height):
        h = height - 1 - y
        for x in range(w):
            if dx0 <= x < dx1 and y >= top:
                continue
            if h < 24:
                c = gate.SUN[2] if h == 0 else gate.GOLD_D if h == 21 else gate.GOLD if h == 22 else gate.SUN[1] if h == 23 else gate.SUN[0]
            else:
                row = (h - 24) // 42
                bx = (x + (48 if row % 2 else 0)) % 96
                c = dark if (h - 24) % 42 == 0 or bx == 95 else lit if (h - 24) % 42 == 41 or bx == 0 else body
                tone = hash01((x + (48 if row % 2 else 0)) // 96, row, 78)
                if c == body and tone < 0.3:
                    c = rgba("#d5c3c6")
                elif c == body and tone > 0.8:
                    c = rgba("#e2d2cf")
                v = math.sin(x * 0.045 + h * 0.11 + 2.0 * math.sin(h * 0.031 + row)) + 0.4 * math.sin(x * 0.13 - h * 0.05)
                if c not in (dark, lit) and abs(v) < 0.035:
                    c = dark
                if 118 <= h < 132:
                    j = h - 118
                    c = dark if j in (0, 13) else lit if j in (1, 12) else gate.SUN[0]
                    if 3 <= j < 10 and gate.KEY[j - 3][x % 8] == "#":
                        c = gate.SUN[2] if j > 3 else gate.SUN[1]
            near = max(dx0 - x, x - dx1 + 1, top - y)
            if near <= 12 and y >= top - 12 and dx0 - 12 <= x < dx1 + 12:
                c = gate.GOLD_D if near == 1 else gate.GOLD if near in (2, 3) else gate.SUN[2] if near == 4 else gate.SUN[0] if near < 9 else gate.SUN[3] if near == 9 else gate.SUN[1]
            if top - 20 <= y < top - 12 and dx0 - 16 <= x < dx1 + 16:
                j = top - 12 - y
                c = gate.SUN[2] if j == 1 else gate.GOLD if j == 6 else gate.SUN[1] if j >= 7 else gate.SUN[0]
            if x >= w - 3:
                c = gate.SUN[1] if x == w - 3 else gate.SUN[2] if x == w - 2 else gate.OUTLINE
            px[x, y] = c
    cy = top - 38
    for a in range(0, 360, 4):
        if 80 < a < 100:
            continue
        r = math.radians(a)
        for q, c in ((12.0, gate.GOLD_D), (13.6, gate.GOLD_L if a % 12 else gate.GOLD), (10.6, gate.GOLD)):
            px[int(cx + math.cos(r) * q), int(cy - math.sin(r) * q)] = c
    gate.bolt(img, cx, cy, 0.56)
    shadow(img, 0.52, 0.3)
    for k, x in enumerate((14, 40, 196)):
        ivy(px, x, height - 25, height - 120 - int(hash01(k, 1, 83) * 160), 84 + k, MOSS_ROOM, w)
    for k, (x, y, n, d) in enumerate(((dx0 - 12, top - 20, 40, 1.0), (dx1 + 12, top - 6, 30, 1.0), (30, height - 300, 46, 1.0),
                                      (180, height - 210, 36, 1.0), (60, height - 150, 28, 0.2), (150, height - 420, 40, 1.0))):
        crack(px, x, y, n, 86 + k, gate.mix(gate.SUN[3], VIOLET, 0.45), None, d, w, height)
    body_m, lit_m, dark_m, tip = tones(MOSS)
    return img


def outside() -> Image.Image:
    w, h = gate.DOOR_W, gate.DOOR_H
    img = blank_size(w, h)
    px = img.load()
    stops = [(0, "#fdbcb0"), (90, "#ffd4a4"), (150, "#ffe8b4"), (h, "#fff6d8")]
    for y in range(h):
        row = gradient(stops, y)
        for x in range(w):
            px[x, y] = row
    for cx in (14, 62):
        for y in range(0, h - 18):
            for x in range(cx - 9, cx + 10):
                px[x % w, y] = rgba("#e2b4b8") if x < cx - 5 else rgba("#cf9eaa")
    for y in range(h - 18, h):
        for x in range(w):
            px[x, y] = rgba("#fffdf6") if y == h - 18 else rgba("#efe4d4") if y < h - 4 else rgba("#cfb8b6")
    return img


def step(px, x0: int, x1: int, line: int, gold: bool) -> None:
    body, lit, dark, joint = gate.SUN
    for x in range(x0, x1):
        for y in range(line - 6, line + 16):
            if y < line:
                j = y - (line - 6)
                c = lit if j == 0 else gate.SHADE[1] if j == 1 else gate.SUN[1] if j == 5 else body
            else:
                j = y - line
                c = dark if j == 0 else lit if j == 1 else body
                if gold and j in (10, 11):
                    c = gate.GOLD if j == 10 else gate.GOLD_D
                if j == 15:
                    c = joint
            px[x, y] = c


def baluster(px, cx: int, top: int, bottom: int, half: int) -> None:
    body, lit, dark, joint = gate.SUN
    tall = bottom - top
    for y in range(top, bottom):
        t = (y - top) / max(1, tall - 1)
        if t > 0.86:
            w = half
        elif t > 0.8:
            w = half - 2
        elif t < 0.07:
            w = half - 1
        elif t < 0.13:
            w = half * 0.55
        else:
            w = half * (0.52 + 0.38 * math.sin(math.pi * (t - 0.13) / 0.67) ** 0.7)
        ring = 0.07 <= t < 0.1 or 0.77 <= t < 0.8 or 0.44 <= t < 0.46
        for x in range(int(cx - w), int(cx + w) + 1):
            f = (x - (cx - w)) / max(1.0, 2 * w)
            if ring:
                c = gate.GOLD_L if f < 0.3 else gate.GOLD_D if f > 0.75 else gate.GOLD
            else:
                c = lit if f < 0.2 else dark if f > 0.72 else body
            if y in (bottom - 1, top) or (t > 0.86 and y == int(top + tall * 0.86) + 1):
                c = joint
            px[x, y] = c


THRONE_W, THRONE_H = 336, 330
SEAT = 186
DAIS = 282


PAINTED_BALL = False


def throne() -> Image.Image:
    w, h = THRONE_W, THRONE_H
    img = blank_size(w, h)
    px = img.load()
    for k in range(3):
        step(px, 32 * k, w - 32 * k, h - 16 * (k + 1), k == 2)
    for k, (x, y) in enumerate(((20, h - 14), (300, h - 13), (52, h - 29), (270, h - 30), (90, h - 45))):
        crack(px, x, y, 10 + k * 2, 140 + k, gate.SUN[3], gate.SUN[1], 1.0, w, h)
    body, lit, dark, joint = gate.SUN
    velvet, velvet_l, velvet_d = rgba("#3c3478"), rgba("#544a9a"), rgba("#2a2458")
    for x in range(98, 238):
        u = (x - 168) / 70.0
        crest = int(26 - 26 * math.sqrt(max(0.0, 1.0 - u * u)))
        for y in range(crest, SEAT):
            edge = y - crest
            c = lit if x in (98, 99) or edge in (0, 1) else dark if x >= 235 else body
            if edge in (3, 4):
                c = gate.GOLD if edge == 3 else gate.GOLD_D
            if (100 <= x < 110 or 226 <= x < 236) and edge > 6 and x % 3 == 0:
                c = gate.SHADE[2]
            if 112 <= x < 224 and 36 <= y < 172:
                c = gate.GOLD_D if x in (112, 223) or y in (36, 171) else gate.GOLD
                if 114 <= x < 222 and 38 <= y < 170:
                    fold = (x - 114) % 12
                    c = velvet_l if fold in (2, 3) else velvet_d if fold in (8, 9) or x >= 219 or y >= 166 else velvet
                    if (x - 114) % 9 == 4 and y in (41, 166) or (y - 38) % 9 == 4 and x in (117, 218):
                        c = gate.GOLD_L
            px[x, y] = c
    for gx, gy in ((98, 26), (238, 26), (168, 4)):
        for y in range(gy - 7, gy + 2):
            for x in range(gx - 5, gx + 6):
                d = math.hypot(x - gx, y - (gy - 3))
                if d <= 5.2 and y >= 0:
                    px[x, y] = gate.GOLD_L if x - gx + y - gy < -4 else gate.GOLD_D if d > 4.2 else gate.GOLD
    cy = 96
    for a in range(0, 360, 3):
        if 78 < a < 102:
            continue
        r = math.radians(a)
        for q, c in ((25.0, gate.GOLD_D), (27.4, gate.GOLD_L if a % 9 else gate.GOLD), (22.8, gate.GOLD)):
            px[int(168 + math.cos(r) * q), int(cy - math.sin(r) * q)] = c
        if a % 18 == 0:
            for q in (24.0, 26.0):
                px[int(168 + math.cos(r + 0.06) * q), int(cy - math.sin(r + 0.06) * q)] = gate.GOLD_L
    gate.bolt(img, 168, cy, 1.15)
    for y in range(SEAT + 16, DAIS):
        for x in range(100, 236):
            px[x, y] = gate.mix(gate.DEEP[3], rgba("#2a2040"), 0.75 if y < SEAT + 40 else 0.6)
    for cx in (110, 226):
        baluster(px, cx, SEAT + 30, DAIS, 10)
    for x in range(114, 222):
        k = (x - 114) % 18
        tip = SEAT + 30 + 26 + int(10 * math.sin(math.pi * k / 18))
        for y in range(SEAT + 30, tip):
            fold = (x - 114) % 6
            c = velvet_l if fold == 1 else velvet_d if fold == 4 or y >= tip - 2 else velvet
            if y == tip - 4:
                c = gate.GOLD_D
            px[x, y] = c
        if k == 9:
            for y in range(tip, tip + 5):
                px[x, y] = gate.GOLD if y < tip + 3 else gate.GOLD_D
    for y in range(SEAT + 16, SEAT + 30):
        for x in range(98, 238):
            j = y - (SEAT + 16)
            c = lit if j == 0 else dark if j >= 12 else body
            if 3 <= j < 10 and gate.KEY[j - 3][x % 8] == "#":
                c = gate.GOLD if j > 3 else gate.GOLD_L
            px[x, y] = c
    for x in range(96, 240):
        for y in range(SEAT - 6, SEAT + 16):
            if y < SEAT:
                j = y - (SEAT - 6)
                c = lit if j == 0 else gate.SHADE[1] if j == 1 else gate.SUN[1] if j == 5 else body
            else:
                j = y - SEAT
                c = dark if j == 0 else gate.GOLD if j == 9 else gate.GOLD_D if j == 10 else lit if j == 1 else joint if j == 15 else body
            px[x, y] = c
    for x0 in (64, 236):
        baluster(px, x0 + 18, 146, DAIS, 13)
        for y in range(128, 146):
            for x in range(x0 - 4, x0 + 40):
                j = y - 128
                px[x, y] = lit if j < 3 else dark if j > 14 else gate.SUN[1] if j < 6 else body
        for x in range(x0 - 4, x0 + 40):
            px[x, 140] = gate.GOLD_D
        vx = x0 + 18
        for y in range(124, 150):
            for x in range(vx - 12, vx + 13):
                d = math.hypot(x - vx, y - 137)
                if d <= 11.5:
                    ring = int(d) % 4
                    px[x, y] = gate.GOLD_D if ring == 0 else gate.GOLD_L if ring == 1 and x < vx else gate.GOLD
    claw_marks(img, ((76, 250, 12, -0.25), (106, 258, 10, -0.2), (250, 248, 13, 0.25), (222, 262, 9, 0.2),
                     (186, SEAT + 2, 12, 0.2), (36, 316, 10, -0.3), (282, 315, 9, 0.2), (232, 299, 10, 0.2)))
    gate.outline(img)
    shadow(img, 0.4, 0.26)
    blue, blue_l, blue_d, tassel = rgba("#4a62b4"), rgba("#7f98e0"), rgba("#2e3d80"), rgba("#f0c860")
    for x in range(144, 192):
        end = min(x - 144, 191 - x)
        top = SEAT - 10 + (3 if end < 2 else 1 if end < 5 else 0) + (1 if 160 <= x < 176 else 0)
        for y in range(top, SEAT):
            c = blue_l if y == top else blue_d if y >= SEAT - 2 or end == 0 else blue
            if y == top + 1 and end > 3 and x % 7 == 0:
                c = blue_l
            px[x, y] = c
    for tx in (142, 192):
        for y in range(SEAT - 6, SEAT):
            px[tx, y] = tassel if y < SEAT - 2 else rgba("#b98842")
    for y in range(SEAT - 9, SEAT) if PAINTED_BALL else ():
        for x in range(196, 206):
            d = math.hypot(x - 200.5, y - (SEAT - 4.5))
            if d <= 4.6:
                seam = abs(math.hypot(x - 197, y - (SEAT - 9)) - 4.2) < 0.7
                px[x, y] = rgba("#f6f8e8") if seam else rgba("#eaf87a") if x < 200 and y < SEAT - 5 else rgba("#9cb43c") if d > 3.6 else rgba("#c8e04c")
    return img


def bowl() -> Image.Image:
    img = blank_size(22, 9)
    px = img.load()
    for y in range(9):
        inset = 2 if y >= 7 else 0 if y >= 1 else 1
        for x in range(inset, 22 - inset):
            c = gate.GOLD_L if y == 0 else gate.GOLD_D if y >= 7 or x >= 19 else gate.GOLD
            if y == 1:
                c = rgba("#5a3a3a")
            px[x, y] = c
    for x, y in ((11, 2), (10, 3), (11, 3), (12, 3), (11, 4), (10, 5), (11, 6)):
        px[x, y] = gate.GOLD_D
    gate.outline(img)
    return img


BOLT_SHAPES = 3
BOLT_BLUE = [(15, "#2f6ce0", 34, 7), (9, "#5aa8ff", 90, 4), (5, "#9ad8ff", 255, 2), (3, "#e4f8ff", 255, 1), (1, "#ffffff", 255, 0)]


def jag(seed: int, x0: float, y0: float, x1: float, y1: float, rough: float, step: tuple = (5, 13), sway: float = 0.0) -> list:
    pts = [(x0, y0)]
    x, y, k = x0, y0, 0
    phase = hash01(seed, 9) * 6.28
    while y < y1 and k < 400:
        n = step[0] + hash01(k, 1, seed) * (step[1] - step[0])
        kick = (hash01(k, 2, seed) - 0.5) * 2 * rough
        if hash01(k, 3, seed) < 0.16:
            kick *= 2.6
        y = min(y1, y + n * (0.45 + 0.55 * hash01(k, 4, seed)))
        t = (y - y0) / max(1.0, y1 - y0)
        guide = x0 + (x1 - x0) * t + sway * math.sin(t * 5.0 + phase) * math.sin(math.pi * t)
        x += kick * n + (guide - x) * 0.3
        pts.append((x, y))
        k += 1
    return pts


def bolt_tree(seed: int, w: int, h: int, rough: float, forks: int, top: float = 0.0) -> list:
    main = jag(seed, w / 2 + (hash01(seed, 1) - 0.5) * w * 0.3, top, w / 2 + (hash01(seed, 2) - 0.5) * w * 0.5, h - 1, rough, sway=w * 0.2)
    paths = [main]
    for f in range(forks):
        sx, sy = main[int(len(main) * (0.06 + 0.7 * hash01(f, 3, seed)))]
        side = 1 if hash01(f, 5, seed) < 0.5 else -1
        length = h * (0.14 + 0.26 * hash01(f, 4, seed))
        branch = jag(seed * 7 + f, sx, sy, sx + side * length * (0.45 + 0.45 * hash01(f, 6, seed)), min(h - 1, sy + length), rough * 1.1, (3, 9))
        paths.append(branch)
        if len(branch) > 5 and hash01(f, 7, seed) < 0.7:
            tx, ty = branch[len(branch) // 2]
            paths.append(jag(seed * 13 + f, tx, ty, tx + side * length * 0.4, min(h - 1, ty + length * 0.45), rough * 1.2, (2, 6)))
    return paths


def shaken(paths: list, seed: int, amount: float) -> list:
    return [[(x + (hash01(i, k, seed) - 0.5) * amount * min(1.0, i / 3), y) for i, (x, y) in enumerate(pts)] for k, pts in enumerate(paths)]


def strokes(size: tuple, paths: list, layers: list) -> Image.Image:
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    for width, color, alpha, branch_width in layers:
        one = Image.new("RGBA", size, (0, 0, 0, 0))
        d = ImageDraw.Draw(one)
        fill = rgba(color)[:3] + (alpha,)
        for k, pts in enumerate(paths):
            wd = width if k == 0 else branch_width
            if wd <= 0:
                continue
            pts = [(round(x), round(y)) for x, y in pts]
            chunk = 6 if k == 0 else len(pts)
            for i in range(0, len(pts) - 1, chunk):
                taper = max(1, round(wd * (1.0 - 0.45 * i / max(1, len(pts) - 1))))
                d.line(pts[i:i + chunk + 1], fill=fill, width=taper, joint="curve")
        out.alpha_composite(one)
    return out


def bolt_sheet(seed: int, w: int, h: int, rough: float, forks: int, layers: list) -> Image.Image:
    paths = bolt_tree(seed, w, h, rough, forks)
    thin = [(max(1, a - 2), c, al, max(0, b - 1)) for a, c, al, b in layers]
    sheet = blank_size(w, h * BOLT_SHAPES)
    for row, (shape, look) in enumerate(((paths, layers), (shaken(paths[:1 + forks // 2], seed + 1, 4.0), layers),
                                         (shaken(paths[:1], seed + 2, 3.0), thin))):
        sheet.alpha_composite(strokes((w, h), shape, look), (0, row * h))
    return sheet


def sky_bolts() -> Image.Image:
    fw, fh = 150, 300
    sheet = blank_size(fw * 4, fh * BOLT_SHAPES)
    for i in range(4):
        sheet.alpha_composite(bolt_sheet(40 + i, fw, fh, 1.1, 4, BOLT_BLUE), (i * fw, 0))
    return sheet


def big_bolt() -> Image.Image:
    return bolt_sheet(7, 300, 360, 1.2, 8, [(25, "#2f6ce0", 34, 11), (15, "#5aa8ff", 90, 6), (9, "#9ad8ff", 255, 3), (5, "#e4f8ff", 255, 2), (3, "#ffffff", 255, 1)])


def strikes() -> Image.Image:
    fw, fh = 96, 384
    mid = fw / 2
    main = [(min(mid + 9, max(mid - 9, x)), y) for x, y in jag(90, mid, 0, mid, fh - 1, 1.0, (4, 10))]
    main[-1] = (mid, fh - 1)
    paths = [main]
    for f in range(6):
        sx, sy = main[int(len(main) * (0.05 + 0.75 * hash01(f, 1, 91)))]
        side = 1 if f % 2 else -1
        length = 40 + hash01(f, 2, 91) * 60
        branch = jag(95 + f, sx, sy, sx + side * length * 0.55, min(fh - 1, sy + length), 1.1, (3, 8))
        paths.append([(min(fw - 2, max(1, x)), y) for x, y in branch])
    yellow = [(15, "#b0780c", 44, 7), (9, "#ffc22a", 110, 4), (5, "#ffdc5c", 255, 2), (3, "#fff2b4", 255, 1), (1, "#ffffff", 255, 0)]
    thin = [(max(1, a - 2), c, al, max(0, b - 1)) for a, c, al, b in yellow]
    sheet = blank_size(fw * 3, fh)
    shapes = ((paths, yellow), ([[(min(mid + 9, max(mid - 9, x)), y) for x, y in shaken([main], 92, 4.0)[0]]] + paths[1:4], yellow),
              ([main], thin))
    for i, (shape, look) in enumerate(shapes):
        sheet.alpha_composite(strokes((fw, fh), shape, look), (i * fw, 0))
    return sheet


def build(preview: bool = False) -> dict:
    heaven = sky()
    far = far_layer()
    mid = mid_layer()
    made = [
        ("anvils", anvils(), 0.02, {"autoscroll": -1.5, "scale_y": 0.01}),
        ("drifting", drifting(), 0.03, {"autoscroll": -5, "scale_y": 0.015}),
        ("hall_far", far, 0.08, {"scale_y": 0.04, "bolts": "far"}),
        ("hall_mid", mid, 0.2, {"scale_y": 0.1, "bolts": "big"}),
        ("shafts", shafts(), 0.2, {"scale_y": 0.1, "flash": True}),
        ("mist", mist(), 0.3, {"scale_y": 0.15, "autoscroll": -4}),
    ]
    layers = []
    for name, img, scale, extra in made:
        save(img, "backgrounds", f"{ZONE}_{name}.png")
        layers.append((f"{ZONE}_{name}.png", scale, extra))
    props = os.path.join("sprites", "props")
    save(floor(2400), props, "palace_floor.png")
    save(column(672), props, "palace_column.png")
    save(entrance(672), props, "palace_door.png")
    save(outside(), props, "palace_outside.png")
    save(throne(), props, "palace_throne.png")
    save(bowl(), props, "palace_bowl.png")
    save(column(672, clawed=True), props, "palace_column_clawed.png")
    combat = os.path.join("sprites", "combat")
    save(sky_bolts(), combat, "storm_bolt.png")
    save(big_bolt(), combat, "storm_bolt_big.png")
    save(strikes(), combat, "strike.png")
    if preview:
        out = heaven.copy()
        for name, _, extra in layers:
            if extra.get("flash"):
                continue
            art = Image.open(os.path.join(ASSETS, "backgrounds", name)).convert("RGBA")
            rows = art.height // extra.get("frames", 2 if "flap" in extra else 1)
            out.alpha_composite(art.crop((0, 0, W, rows)), (0, int(extra.get("y", 0))))
        path = os.path.join(DOCS_PREVIEW, "thunder_court", "fundo.png")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        gate.keep(out.resize((W * 2, H * 2), Image.NEAREST), path)
    return {"sky": Sheet(heaven), "layers": layers}


if __name__ == "__main__":
    build("--preview" in sys.argv)
    print("thunder court: ok (para o tema e o chao: python tools/art/gen_zones.py zeus_palace)")
