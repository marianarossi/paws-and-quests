from __future__ import annotations

import math

from PIL import Image

from vec import hash01, rgba, save

BODY, LIT, SHADE, JOINT = (rgba(c) for c in ("#eadfd0", "#fffdf6", "#c6aab0", "#94788c"))
VEIN, VEIN_D = rgba("#dccbc6"), rgba("#cdb8bc")
GOLD, GOLD_L, GOLD_D = (rgba(c) for c in ("#eec45c", "#fff0a8", "#b98842"))
OUTLINE = rgba("#5e4058")


def sheet(w: int, h: int):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    return img, img.load()


def fall_block() -> None:
    img, px = sheet(48, 16)
    for x in range(48):
        for y in range(16):
            end = min(x, 47 - x)
            if y > 12 and end < y - 12:
                continue
            if x == 0 or x == 47 or y == 15 or (y > 12 and end == y - 12):
                c = OUTLINE
            elif y == 0:
                c = LIT
            elif y == 1:
                c = BODY if end > 1 else LIT
            elif y in (4, 6):
                c = GOLD_D
            elif y == 5:
                c = GOLD_L if (x + 1) % 4 == 0 else GOLD
            elif y >= 12:
                c = SHADE
            elif x in (1, 46):
                c = LIT if x == 1 else SHADE
            else:
                c = BODY
                if hash01(x, y, 7) < 0.06:
                    c = VEIN_D
                elif abs((x * 0.7 + y * 1.3) % 9 - 4) < 0.5 and y > 6:
                    c = VEIN
            px[x, y] = c
    for x in (16, 32):
        for y in range(7, 15):
            px[x, y] = JOINT
    for x, y in ((9, 9), (10, 10), (10, 11), (37, 8), (38, 9), (24, 10), (25, 11)):
        px[x, y] = JOINT
    save(img, "sprites", "props", "fall_block.png")


def cloud_row(px, y0: int, colors: tuple, lit: bool) -> None:
    rim, light, body, shade, under = colors
    for x in range(48):
        end = min(x, 47 - x)
        top = 3 - int(round(1.0 + 1.0 * math.sin(x * math.pi / 4 + 0.6))) + (3 - end if end < 3 else 0)
        bot = 10 + int(round(1.2 * math.sin(x * math.pi / 4 + 2.4) + 0.6 * math.sin(x * math.pi / 8))) - (4 - end if end < 4 else 0)
        for y in range(top, bot + 1):
            if lit:
                c = rim if y == top else light if y < top + 3 else under if y == bot else shade if y > bot - 3 else body
            else:
                edge = y in (top, bot) or end == 0
                if not edge or (x + y) % 2:
                    continue
                c = (shade[0], shade[1], shade[2], 200)
            px[x, y0 + y] = c


def beat_cloud() -> None:
    img, px = sheet(48, 64)
    group_a = tuple(rgba(c) for c in ("#fffaf0", "#ffeccc", "#fcd3a4", "#eba97e", "#c98172"))
    group_b = tuple(rgba(c) for c in ("#f6f8ff", "#dde2ff", "#b9bdf2", "#9590d8", "#6f68b4"))
    cloud_row(px, 0, group_a, True)
    cloud_row(px, 16, group_a, False)
    cloud_row(px, 32, group_b, True)
    cloud_row(px, 48, group_b, False)
    save(img, "sprites", "props", "beat_cloud.png")


def cloud_step() -> None:
    img, px = sheet(48, 16)
    pink = tuple(rgba(c) for c in ("#fff6fa", "#ffd8ea", "#f7afd0", "#e286b6", "#b8669a"))
    cloud_row(px, 0, pink, True)
    save(img, "sprites", "props", "cloud_step.png")


MARSHMALLOW = [
    "..............",
    "..............",
    "..............",
    "....######....",
    "...#hhwwwwc#..",
    "..#hwwwwwwwc#.",
    "..#wwwwwwwwc#.",
    "..#cwwwwwwcc#.",
    "..#scccccccs#.",
    "..#wwewwewwc#.",
    "..#wpewwepcs#.",
    "..#cwwrrwwcs#.",
    "...#ccccccs#..",
    "....######....",
    "..............",
    "..............",
]
MARSH_COLORS = {"#": "#6a3a24", "h": "#ffffff", "w": "#fff4e6", "c": "#f0d8bc", "s": "#d6b394",
                "e": "#3a2030", "p": "#f4a0a8", "r": "#c0505e"}


def feather() -> None:
    w, h = len(MARSHMALLOW[0]), len(MARSHMALLOW)
    img, px = sheet(w * 7, h)
    colors = {k: rgba(v) for k, v in MARSH_COLORS.items()}
    for f in range(7):
        band = f * 6 - 3
        for y, row in enumerate(MARSHMALLOW):
            for x, ch in enumerate(row):
                if ch == ".":
                    continue
                if f == 6:
                    if ch == "#":
                        px[f * w + x, y] = (255, 236, 210, 150)
                    continue
                c = colors[ch]
                below = MARSHMALLOW[y + 1][x] if y + 1 < h else "."
                if f == 5 and ch == "e" and below == "e":
                    c = colors["w"]
                elif ch in "hwcs" and band - 1 <= x + y <= band:
                    c = tuple(round(v + (255 - v) * 0.6) for v in c[:3]) + (255,)
                px[f * w + x, y] = c
    save(img, "sprites", "props", "feather.png")


def storm_wall() -> None:
    w, h = 96, 360
    img, px = sheet(w * 2, h)
    tones = [rgba(c) for c in ("#1c1830", "#2a2444", "#3b3360", "#544a82", "#7a6eaa")]
    for f in range(2):
        for y in range(h):
            t = 2 * math.pi * y / h
            edge = 66 + 12 * math.sin(2 * t + f * 1.7) + 6 * math.sin(6 * t - f * 2.3) + 3 * math.sin(15 * t + f)
            for x in range(w):
                d = edge - x
                if d < 0:
                    continue
                k = 0 if d > 40 else 1 if d > 22 else 2 if d > 10 else 3 if d > 3 else 4
                if k <= 1 and math.sin(x / 7.0 + 28 * math.pi * y / h + f) > 0.82:
                    k += 1
                px[f * w + x, y] = tones[k]
        for i in range(26):
            x = int(hash01(i, f, 41) * 50) + 4
            y = int(hash01(i, f, 43) * (h - 8)) + 4
            px[f * w + x, y] = GOLD
            if hash01(i, f, 47) < 0.5:
                px[f * w + x + 1, y] = GOLD_D
    save(img, "sprites", "props", "storm_wall.png")


def sky_glow() -> None:
    s = 96
    img, px = sheet(s, s)
    c = (s - 1) / 2
    for y in range(s):
        for x in range(s):
            r = math.hypot(x - c, y - c)
            star = min(abs(x - c), abs(y - c)) < 1.2 and r < 26
            if r < 8 or star:
                px[x, y] = rgba("#fffdf6")
            elif r < 14:
                px[x, y] = rgba("#fff0d0", 220)
            elif r < 22:
                px[x, y] = rgba("#ffd8e8", 140)
            elif r < 32:
                px[x, y] = rgba("#ffc8de", 80)
            elif r < 46:
                px[x, y] = rgba("#ffc0d8", 36)
    save(img, "sprites", "props", "sky_glow.png")


def main() -> None:
    fall_block()
    beat_cloud()
    cloud_step()
    feather()
    storm_wall()
    sky_glow()
    print("pecas do olimpo: ok")


if __name__ == "__main__":
    main()
