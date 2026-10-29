from __future__ import annotations

import math
import os

from PIL import Image, ImageDraw

from vec import ASSETS, DOCS_PREVIEW, hash01, rgba, save_json

H = 312
UNDER = 236
SPACING = 142
PILLARS = 8
FIRST = 48
WALL_X = FIRST + SPACING * (PILLARS - 1)
DOOR_CX = WALL_X + SPACING * 3 // 2
DOOR_W, DOOR_H = 80, 178
W = WALL_X + SPACING * 3 - 30
FLOOR_STYLE = "veios"

SUN = tuple(rgba(c) for c in ("#efe4d4", "#fffdf6", "#cfb8b6", "#a58d96"))
SHADE = tuple(rgba(c) for c in ("#dbcaca", "#eadeda", "#bca6b2", "#947e96"))
DEEP = tuple(rgba(c) for c in ("#c6b2ba", "#d4c2c6", "#aa94a8", "#86708c"))
OUTLINE = rgba("#75607a")
GOLD, GOLD_L, GOLD_D = (rgba(c) for c in ("#eec45c", "#fff0a8", "#b98842"))
BRONZE, BRONZE_L, BRONZE_D, BRONZE_DD = (rgba(c) for c in ("#c99a62", "#eccb8e", "#9a6c4c", "#6e4a44"))
MOSS, MOSS_L, MOSS_D = (rgba(c) for c in ("#7fae6a", "#aed084", "#5a8a5c"))
IVY, IVY_L, IVY_D, BLOOM = (rgba(c) for c in ("#5ea870", "#a4dc8c", "#3f7f5a", "#fff0f4"))
VEIN, VEIN_D = rgba("#dccbc6"), rgba("#cdb8bc")
BOLT = [(3, -16), (-8, 2), (-1, 2), (-6, 16), (9, -4), (2, -4), (9, -16)]
KEY = ["########", "#.......", "#.#####.", "#.#...#.", "#.###.#.", "#.....#.", "#######."]


def blank(w: int, h: int) -> Image.Image:
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def mix(a: tuple, b: tuple, t: float) -> tuple:
    t = min(1.0, max(0.0, t))
    return (round(a[0] + (b[0] - a[0]) * t), round(a[1] + (b[1] - a[1]) * t), round(a[2] + (b[2] - a[2]) * t), 255)


def outline(img: Image.Image, color: tuple = OUTLINE) -> None:
    px = img.load()
    w, h = img.size
    edge = []
    for y in range(h):
        for x in range(w):
            if px[x, y][3] and any(0 <= x + dx < w and y + dy < h and (y + dy < 0 or not px[x + dx, y + dy][3]) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                edge.append((x, y))
    for x, y in edge:
        px[x, y] = color


def bolt(img: Image.Image, cx: float, cy: float, scale: float) -> None:
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).polygon([(cx + x * scale, cy + y * scale) for x, y in BOLT], fill=255)
    m, px = mask.load(), img.load()
    for y in range(img.height):
        for x in range(img.width):
            if m[x, y]:
                px[x, y] = GOLD_D if x + 1 >= img.width or not m[x + 1, y] else GOLD_L if x and not m[x - 1, y] else GOLD


def big_column(img: Image.Image, cx: int, ground: int, height: int, width: int, pal: tuple, seed: int) -> None:
    body, lit, dark, joint = pal
    px = img.load()
    half0 = width / 2
    flutes = max(4, width // 4)
    for h in range(height):
        y = ground - 1 - h
        if h >= height - 9:
            half = half0 * 1.44
        elif h >= height - 21:
            half = half0 * (0.88 + 0.5 * (h - (height - 21)) / 12.0)
        elif h < 6:
            half = half0 * 1.36
        elif h < 10:
            half = half0 * (1.24 if h in (7, 8) else 1.18)
        elif h < 13:
            half = half0 * 1.07
        else:
            half = round(half0 * (1.0 - 0.14 * (h / height) ** 1.4) * 2) / 2
        for x in range(int(cx - half), int(cx + half) + 1):
            if not (0 <= x < img.width and 0 <= y < img.height):
                continue
            f = (x - (cx - half)) / max(1.0, 2 * half)
            c = lit if f < 0.2 else dark if f > 0.72 else body
            if h >= height - 9:
                c = lit if h >= height - 3 or f < 0.12 else dark if f > 0.82 or h < height - 7 else body
            elif h >= height - 21:
                c = lit if f < 0.18 else dark if f > 0.78 else body
            elif h >= height - 27:
                c = (GOLD_L if f < 0.3 else GOLD_D if f > 0.8 else GOLD) if pal is SUN else (GOLD if f < 0.3 else GOLD_D)
            elif h < 6:
                c = lit if h == 5 or f < 0.1 else dark if f > 0.86 or h == 0 else body
            elif h < 10:
                c = lit if h == 8 and f < 0.8 else dark if h == 6 or f > 0.84 else lit if f < 0.14 else body
            elif h < 13:
                c = (GOLD_L if f < 0.3 else GOLD_D if f > 0.8 else GOLD) if h == 12 else dark if h == 10 else body
            else:
                if int(f * flutes * 2) % 2 == 1 and 0.05 < f < 0.95:
                    c = dark if c == body else joint if c == dark else body
                if h % 31 == 30:
                    c = joint
            if x == int(cx - half) or x == int(cx + half):
                c = OUTLINE
            px[x, y] = c


def vine(img: Image.Image, x: float, y0: int, y1: int, seed: int, x_min: float, x_max: float, cling: bool = True) -> None:
    px = img.load()
    step = -1 if y1 < y0 else 1
    for k, y in enumerate(range(y0, y1, step)):
        r = hash01(k, 1, seed)
        x = min(x_max, max(x_min, x + (1 if r < 0.24 else -1 if r > 0.78 else 0)))
        xi = int(x)
        if not (0 <= xi < img.width and 0 <= y < img.height) or (cling and not px[xi, y][3]):
            continue
        px[xi, y] = IVY
        if hash01(k, 2, seed) < 0.6:
            side = -1 if hash01(k, 3, seed) < 0.5 else 1
            for dx, dy, c in ((side, 0, IVY_L if hash01(k, 4, seed) < 0.45 else IVY), (side * 2, -1, IVY_D if hash01(k, 6, seed) < 0.3 else IVY)):
                if 0 <= xi + dx < img.width and 0 <= y + dy < img.height and (not cling or px[xi + dx, y + dy][3]):
                    px[xi + dx, y + dy] = c
        if hash01(k, 5, seed) < 0.045 and 0 <= xi + 1 < img.width and y > 0:
            px[xi + 1, y - 1] = BLOOM


def roof(img: Image.Image) -> None:
    px = img.load()
    body, lit, dark, joint = SUN
    for h in range(UNDER, H):
        j = h - UNDER
        left = 0 if 46 <= j < 60 else 6
        for x in range(left, W):
            if j < 7:
                c = DEEP[3] if j in (0, 6) or x % 14 == 0 else DEEP[2] if (x % 14 in (1, 13) or j in (1, 5)) else DEEP[0]
            elif j < 23:
                c = joint if j == 7 else GOLD if j == 22 else GOLD_D if j == 21 else joint if x % 71 == 70 else lit if j == 20 else dark if j == 8 else body
            elif j < 46:
                k = x % 30
                c = body
                if k < 12:
                    c = dark if k in (0, 3, 4, 7, 8, 11) else lit if k in (1, 5, 9) else body
                    if j > 43:
                        c = lit
                elif (x // 30) % 2 == 0:
                    d = math.hypot(k - 21, j - 34)
                    if d <= 7.0:
                        c = GOLD_D if d > 5.5 else GOLD_L if (k - 21) + (j - 34) > 3 else GOLD
                if j == 23:
                    c = joint
            elif j < 60:
                c = dark if j < 49 else (joint if x % 8 < 4 else dark) if j == 49 else body if j < 56 else GOLD_D if j == 56 else lit
            else:
                c = dark if j == 60 else lit if j >= 74 else joint if x % 71 == 35 else body
            if x == left:
                c = OUTLINE
            px[x, H - 1 - h] = c
    for i in range(PILLARS + 3):
        bolt(img, FIRST + SPACING * i, H - 1 - (UNDER + 67), 0.36)
    for i in range(PILLARS + 2):
        x0 = FIRST + SPACING * i + 40
        for dy, row in enumerate(KEY):
            for k in range(62):
                if row[k % 8] == "#":
                    px[x0 + k, H - 1 - (UNDER + 71) + dy] = GOLD_D if dy else GOLD


def palace_wall(img: Image.Image) -> None:
    px = img.load()
    body, lit, dark, joint = SHADE
    x0 = WALL_X - 12
    dx0, dx1, top = DOOR_CX - DOOR_W // 2, DOOR_CX + DOOR_W // 2, H - DOOR_H
    for y in range(H - UNDER, H):
        h = H - 1 - y
        for x in range(x0, W):
            if dx0 <= x < dx1 and y >= top:
                continue
            if h < 24:
                c = SUN[2] if h == 0 else GOLD_D if h == 21 else GOLD if h == 22 else SUN[1] if h == 23 else SUN[3] if (x - x0) % 96 == 95 else SUN[0]
            else:
                row = (h - 24) // 42
                bx = (x - x0 + (48 if row % 2 else 0)) % 96
                c = dark if (h - 24) % 42 == 0 or bx == 95 else lit if (h - 24) % 42 == 41 or bx == 0 else body
                v = math.sin(x * 0.045 + h * 0.11 + 2.0 * math.sin(h * 0.031 + row)) + 0.4 * math.sin(x * 0.13 - h * 0.05)
                tone = hash01((x - x0 + (48 if row % 2 else 0)) // 96, row, 77)
                if c == body and tone < 0.3:
                    c = rgba("#d5c3c6")
                elif c == body and tone > 0.8:
                    c = rgba("#e2d2cf")
                if c not in (dark, lit) and abs(v) < 0.035:
                    c = dark
                if 118 <= h < 132:
                    j = h - 118
                    c = dark if j in (0, 13) else lit if j in (1, 12) else SUN[0]
                    if 3 <= j < 10 and KEY[j - 3][x % 8] == "#":
                        c = SUN[2] if j > 3 else SUN[1]
            if h > UNDER - 16:
                c = mix(c, DEEP[3], 0.5 * (h - (UNDER - 16)) / 16.0)
            near = max(dx0 - x, x - dx1 + 1, top - y)
            if near <= 12 and y >= top - 12 and dx0 - 12 <= x < dx1 + 12:
                c = GOLD_D if near == 1 else GOLD if near in (2, 3) else SUN[2] if near == 4 else SUN[0] if near < 9 else SUN[3] if near == 9 else SUN[1]
            if top - 20 <= y < top - 12 and dx0 - 16 <= x < dx1 + 16:
                j = top - 12 - y
                c = SUN[2] if j == 1 else GOLD if j == 6 else SUN[1] if j >= 7 else SUN[0]
            if x == x0:
                c = OUTLINE
            px[x, y] = c
    cy = top - 38
    for a in range(0, 360, 4):
        if 80 < a < 100:
            continue
        r = math.radians(a)
        for q, c in ((12.0, GOLD_D), (13.6, GOLD_L if a % 12 else GOLD), (10.6, GOLD)):
            px[int(DOOR_CX + math.cos(r) * q), int(cy - math.sin(r) * q)] = c
    bolt(img, DOOR_CX, cy, 0.56)


def building() -> Image.Image:
    img = blank(W, H)
    palace_wall(img)
    for i in range(PILLARS + 3):
        if FIRST + SPACING * i - 40 < W:
            big_column(img, FIRST + SPACING * i, H, UNDER, 54, SUN, FIRST + SPACING * (i % 4) + 7)
    for i in range(PILLARS + 3):
        cx = FIRST + SPACING * i
        for k in range((2, 1, 0, 2, 1, 1, 2, 0, 1, 2, 1)[i]):
            reach = int(UNDER * (0.3 + 0.45 * hash01(i, k, 81)))
            vine(img, cx - 20 + hash01(i, k, 82) * 40, H - 13, H - 13 - reach, 100 + i * 7 + k, cx - 23, cx + 23)
    for i, x in enumerate((WALL_X + 52, WALL_X + 92, DOOR_CX + 96, DOOR_CX + 118, W - 22)):
        vine(img, x, H - 24, H - 24 - int(60 + hash01(i, 1, 83) * 120), 200 + i, x - 14, x + 14)
    roof(img)
    for i in range(PILLARS + 2):
        for k in range(2):
            if hash01(i, k, 84) < 0.7:
                x = FIRST + SPACING * i + 44 + hash01(i, k, 85) * 54
                vine(img, x, H - UNDER, H - UNDER + int(8 + hash01(i, k, 86) * 38), 300 + i * 3 + k, x - 5, x + 5, cling=x > WALL_X)
    px = img.load()
    top = H - UNDER
    for y in range(top, top + 12):
        for x in range(W):
            c = px[x, y]
            if c[3] and c not in (GOLD, GOLD_L, GOLD_D, IVY, IVY_L, IVY_D, BLOOM):
                px[x, y] = mix(c, rgba("#8a7392"), 0.34 * (1.0 - (y - top) / 12.0))
    return img


def leaf() -> Image.Image:
    w, h = DOOR_W // 2, DOOR_H
    img = blank(w, h)
    px = img.load()
    for y in range(h):
        for x in range(w):
            c = BRONZE_DD if x == 0 or x == w - 1 or y == 0 else BRONZE_L if x == 1 or y == 1 else BRONZE
            ph = (y - 8) % 42
            if 5 <= x < w - 5 and 8 <= y < h - 8 and ph < 36:
                c = BRONZE_DD if x == 5 or ph == 0 else BRONZE_L if x == w - 6 or ph == 35 else BRONZE_D
                if x in (8, w - 9) and ph in (3, 32):
                    c = GOLD_L
            px[x, y] = c
    for dy in range(-4, 5):
        for dx in range(-4, 5):
            if 2.4 < math.hypot(dx, dy) <= 4.2:
                px[w - 9 + dx, 96 + dy] = GOLD_L if dx + dy < 0 else GOLD_D
    return img


def interior() -> Image.Image:
    img = blank(DOOR_W, DOOR_H)
    px = img.load()
    ramp = [rgba(c) for c in ("#0d0a1a", "#120e22", "#17122a", "#1d1733", "#241c3c", "#2c2346", "#352a50", "#40335c", "#4d3e6a", "#5c4b78")]
    for y in range(DOOR_H):
        for x in range(DOOR_W):
            up = 1.0 - y / (DOOR_H - 1)
            side = abs(x - (DOOR_W - 1) / 2) / (DOOR_W / 2)
            light = (1.0 - up) ** 1.8 * 0.85 + side ** 3 * 0.1 * (1.0 - up)
            v = min(1.0, max(0.0, light)) * (len(ramp) - 1)
            k = int(v)
            if v - k > 0.5 + (0.25 if (x + y) % 2 else -0.25):
                k += 1
            px[x, y] = ramp[min(len(ramp) - 1, k)]
    return img


def floor(width: int, style: str) -> Image.Image:
    height = 74
    img = blank(width, height)
    px = img.load()
    body, lit, dark, joint = SUN
    for x in range(width):
        for y in range(height):
            if x < 10 and y < 6 + (10 - x) // 2 * 3:
                continue
            if y < 6:
                c = lit if y == 0 else SUN[1] if y == 5 else SHADE[1] if y == 1 else body
                if (x + y * 6) % 160 == 0:
                    c = dark
            elif y < 26:
                j = y - 6
                c = dark if j == 0 else lit if j == 1 else body
                if style == "veios" and j in (5, 6):
                    c = GOLD if j == 5 else GOLD_D
                if style == "friso" and 6 <= j < 13:
                    if KEY[j - 6][x % 8] == "#":
                        c = SUN[2] if j > 6 else lit
                if style == "hera" and j < 4:
                    c = lit if j in (1, 2) else body
                if x % 160 == 80 and j > 1:
                    c = dark
            elif y < 30:
                c = dark if y < 29 else joint
            else:
                j = y - 30
                c = SHADE[2] if j < 3 else SHADE[1] if j == 3 else SHADE[0]
                if x % 240 == 120 and j > 3:
                    c = SHADE[2]
                if j >= height - 30 - 5:
                    c = SHADE[2] if j < height - 30 - 1 else OUTLINE
            if x < 12 and (x == 0 or px[x - 1, y][3] == 0):
                c = OUTLINE
            px[x, y] = c
    if style in ("veios", "hera"):
        for i in range(width // (30 if style == "veios" else 60)):
            x, y = int(hash01(i, 1, 5) * width), 9.0 + hash01(i, 2, 5) * 54.0
            if 24 < y < 36:
                continue
            slope = (hash01(i, 3, 5) - 0.5) * 0.9
            ground = body if y < 26 else SHADE[0]
            tone = (VEIN_D if hash01(i, 4, 5) < 0.5 else VEIN) if y < 26 else SHADE[2]
            for k in range(14 + int(hash01(i, 5, 5) * 40)):
                yy = int(y + slope * k + math.sin(k * 0.35 + i) * 1.3)
                if 0 <= x + k < width and 9 <= yy < height - 6 and px[x + k, yy] == ground:
                    px[x + k, yy] = tone
                if k == 12 and 0 <= x + k + 8 < width:
                    for q in range(8):
                        y2 = yy - q // 2 if slope > 0 else yy + q // 2
                        if 9 <= y2 < height - 6 and px[x + k + q, y2] == ground:
                            px[x + k + q, y2] = tone
    for i in range(width // 110):
        x = int((i + 0.2 + 0.6 * hash01(i, 1, 9)) * 110)
        if x > 14:
            vine(img, x, 6, 6 + int(8 + hash01(i, 2, 9) * 30), 400 + i, x - 4, x + 4)
    return img


def pillar(height: int, seed: int) -> Image.Image:
    body, lit, dark, joint = SUN
    w = 44
    img = blank(w, height)
    px = img.load()
    cx, ground = w // 2, img.height
    for y in range(ground):
        h = ground - y
        half = 17 if h < 6 else 15 if h < 10 else 12.5 * (1.0 - 0.13 * (h / height) ** 1.4)
        for x in range(w):
            d = x - cx
            if abs(d) > half or y < int(hash01(x // 3, 1, seed) * 12):
                continue
            f = (d + half) / (2 * half)
            c = lit if f < 0.2 else dark if f > 0.72 else body
            if h >= 10:
                if int(f * 14) % 2 == 1 and 0.06 < f < 0.94:
                    c = dark if c == body else joint if c == dark else body
                if (h - 10) % 26 == 0:
                    c = joint
            px[x, y] = c
    outline(img)
    vine(img, cx - 6, ground - 2, 6, seed + 40, cx - 11, cx + 11)
    vine(img, cx + 7, ground - 2, int(ground * 0.45), seed + 41, cx - 11, cx + 11)
    return img


def keep(img: Image.Image, path: str) -> None:
    try:
        img.save(path)
    except OSError:
        print("previa por guardar (ficheiro aberto?):", path)


def build() -> dict:
    out = os.path.join(ASSETS, "sprites", "props")
    main, lf, back = building(), leaf(), interior()
    door = [DOOR_CX - DOOR_W // 2, H - DOOR_H, DOOR_W, DOOR_H]
    for name, img in (("gate_main", main), ("gate_back", back), ("gate_door_l", lf), ("gate_door_r", lf.transpose(Image.FLIP_LEFT_RIGHT)),
                      ("gate_floor", floor(1600, FLOOR_STYLE)), ("gate_pillar_b", pillar(124, 2))):
        img.save(os.path.join(out, name + ".png"))
    for old in ("gate_far", "gate_front", "gate_veranda", "gate_pillar_a", "gate_pillar_c", "waterfall"):
        for ext in (".png", ".png.import"):
            if os.path.exists(os.path.join(out, old + ext)):
                os.remove(os.path.join(out, old + ext))
    data = {"size": [W, H], "feet_x": DOOR_CX, "door": door}
    save_json(data, "sprites", "props", "gate.json")
    folder = os.path.join(DOCS_PREVIEW, "olympus")
    os.makedirs(folder, exist_ok=True)
    crop = (W - 600, 0, W, H)
    sheet = Image.new("RGBA", (616, H * 2 + 24), rgba("#f4b8cc"))
    for i in range(2):
        gate = blank(W, H)
        gate.alpha_composite(back, (door[0], door[1]))
        if i == 0:
            gate.alpha_composite(lf, (door[0], door[1]))
            gate.alpha_composite(lf.transpose(Image.FLIP_LEFT_RIGHT), (DOOR_CX, door[1]))
        gate.alpha_composite(main)
        sheet.alpha_composite(gate.crop(crop), (8, 8 + i * (H + 8)))
    keep(sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST), os.path.join(folder, "portao.png"))
    options = Image.new("RGBA", (336, 3 * 44 + 8), rgba("#b9a0d8"))
    for i, style in enumerate(("veios", "friso", "hera")):
        options.alpha_composite(floor(320, style), (8, 8 + i * 44))
    keep(options.resize((options.width * 4, options.height * 4), Image.NEAREST), os.path.join(folder, "marmore_opcoes.png"))
    return data


def main() -> None:
    print("palacio: ok", build())


if __name__ == "__main__":
    main()
