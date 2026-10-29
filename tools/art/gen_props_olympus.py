from __future__ import annotations

import math
import os

from PIL import Image

import gen_gate
import gen_props
import vec
from vec import ASSETS, hash01, pack, rgba, save, save_json
from zonekit import Art, cypress, statue_dog

ZONE = "olympus_dawn"
GREENS = {"grass": "#7cc86a", "grass_l": "#c8f294", "grass_d": "#4c9c5e", "moss": "#3f8058", "leaf": "#5cb86c", "leaf_l": "#a4e284"}
BODY, LIT, DARK, JOINT, GOLD = (rgba(c) for c in ("#eadfd0", "#fffdf6", "#c6aab0", "#94788c", "#f0c860"))
IVY, IVY_L = rgba("#4c9c5e"), rgba("#a4e284")


def sheet(w: int, h: int):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    return img, img.load()


def dot(img: Image.Image, px, x: float, y: float, color: tuple) -> None:
    if 0 <= int(x) < img.width and 0 <= int(y) < img.height:
        px[int(x), int(y)] = color


def crop(art: Art) -> Image.Image:
    return art.img.crop(art.img.getbbox())


def column(width: int, height: int, seed: int, broken: bool) -> Image.Image:
    img, px = sheet(width + 8, height)
    half = width // 2
    cx = img.width // 2
    top = 0 if broken else 6
    for y in range(top, height):
        for dx in range(-half, half + 1):
            if broken and y < int(hash01((dx + half) // 2, 1, seed) * 7):
                continue
            f = (dx + half) / width
            c = LIT if f < 0.26 else DARK if f > 0.7 else BODY
            if (dx + half) % 3 == 2 and 0.1 < f < 0.9:
                c = DARK if c == BODY else JOINT if c == DARK else BODY
            if (height - y) % 11 == 0:
                c = JOINT
            dot(img, px, cx + dx, y, c)
    for row, grow in ((1, 1), (2, 2), (3, 2)):
        for dx in range(-half - grow, half + grow + 1):
            dot(img, px, cx + dx, height - row, DARK if row == 1 else LIT if dx < 0 else BODY)
    if not broken:
        for row, grow in ((0, 3), (1, 3), (2, 3), (3, 2), (4, 1), (5, 1)):
            for dx in range(-half - grow, half + grow + 1):
                dot(img, px, cx + dx, row, LIT if row == 0 or dx < -half else DARK if dx > half else BODY)
        for sx in (-half - 3, half + 2):
            dot(img, px, cx + sx, 3, JOINT)
            dot(img, px, cx + sx + 1, 3, JOINT)
    x = cx - half + 1
    for y in range(height - 1, int(height * (0.35 + 0.3 * hash01(seed, 2))), -1):
        x = min(cx + half, max(cx - half, x + (1 if hash01(y, 3, seed) < 0.3 else -1 if hash01(y, 3, seed) > 0.8 else 0)))
        dot(img, px, x, y, IVY)
        if hash01(y, 4, seed) < 0.5:
            dot(img, px, x + (1 if y % 2 else -1), y, IVY_L if hash01(y, 5, seed) < 0.4 else IVY)
    return img


def fallen(length: int, seed: int) -> Image.Image:
    img, px = sheet(length, 11)
    for x in range(length):
        drum = x // 11
        if x % 11 == 10 and drum == 1:
            continue
        sink = 2 if drum == 2 else 0
        for y in range(1 + sink, 11):
            row = y - sink
            c = LIT if row < 3 else DARK if row > 7 else BODY
            if row in (4, 7):
                c = DARK if c == BODY else JOINT
            if x % 11 == 0 or x % 11 == 9:
                c = JOINT if x % 11 == 0 else c
            dot(img, px, x, y, c)
    for y in range(2, 10):
        dot(img, px, length - 1, y, LIT if 3 < y < 8 else JOINT)
    for k in range(6):
        dot(img, px, 3 + int(hash01(k, 1, seed) * (length - 6)), 1, IVY if k % 2 else IVY_L)
    return img


def bricks(w: int, h: int, seed: int, jagged: bool = True) -> Image.Image:
    img, px = sheet(w, h)
    for x in range(w):
        top = h - max(8, int(h * (0.4 + 0.6 * hash01(x // 8, 1, seed))) // 8 * 8) if jagged else 0
        for y in range(top, h):
            row = (h - 1 - y) // 8
            bx = (x + (7 if row % 2 else 0)) % 15
            by = (h - 1 - y) % 8
            c = JOINT if bx == 14 or by == 0 else LIT if by == 7 or bx == 0 else DARK if by == 1 or bx == 13 else BODY
            dot(img, px, x, y, c)
    for k in range(w // 5):
        x = int(hash01(k, 2, seed) * w)
        for y in range(h):
            if px[x, y][3]:
                dot(img, px, x, y, IVY_L if k % 3 else IVY)
                if k % 2:
                    dot(img, px, x, y + 1, IVY)
                break
    return img


def arch(seed: int) -> Image.Image:
    w, h = 46, 44
    img, px = sheet(w, h)
    cx, spring, outer, inner = w / 2 - 0.5, 22, 22.0, 14.0
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - cx, y - spring)
            ang = math.atan2(spring - y, x - cx)
            if y <= spring and inner <= d <= outer:
                if ang < 0.62:
                    continue
                band = int(ang * 6 / math.pi * 2.2)
                edge = abs(ang * 6 / math.pi * 2.2 - round(ang * 6 / math.pi * 2.2)) < 0.07
                c = JOINT if edge else LIT if d > outer - 2 else DARK if d < inner + 2 else BODY if band % 2 else rgba("#e0d2c6")
                dot(img, px, x, y, c)
            elif y > spring and (x < 8 or (x >= w - 8 and y > spring + 9 + int(hash01(x, 1, seed) * 4))):
                bx, by = (x if x < 8 else x - (w - 8)), (h - 1 - y) % 8
                c = JOINT if by == 0 else LIT if bx == 0 or by == 7 else DARK if bx == 7 else BODY
                dot(img, px, x, y, c)
    for y in range(spring - 4, h):
        x = 1 + int((math.sin(y * 0.5) + 1) * 2.5)
        if hash01(y, 2, seed) < 0.75:
            dot(img, px, x, y, IVY if y % 3 else IVY_L)
    return img


def urn(profile: list, seed: int, colors: tuple = ("#dc9478", "#f6c09c", "#ac6868", "#5e4058")) -> Image.Image:
    body, lit, dark, band = (rgba(c) for c in colors)
    h = len(profile)
    w = max(profile) * 2 + 5
    img, px = sheet(w, h)
    cx = w // 2
    for y, half in enumerate(profile):
        for dx in range(-half, half + 1):
            c = lit if dx < -half * 0.3 else dark if dx > half * 0.5 else body
            if y in (h * 2 // 5, h * 2 // 5 + 2):
                c = band
            elif y == h * 2 // 5 + 1:
                c = rgba("#f0c860") if (dx + seed) % 2 else band
            dot(img, px, cx + dx, y, c)
    for side in (-1, 1):
        for y in range(2, h * 2 // 5):
            dot(img, px, cx + side * (profile[y] + 2 if 2 < y < h * 2 // 5 - 1 else profile[y] + 1), y, dark if side > 0 else body)
    return img


def olive(seed: int, size: int) -> Image.Image:
    img, px = sheet(size + 6, size + 4)
    cx, h = img.width // 2, img.height
    trunk, trunk_l = rgba("#7c5a54"), rgba("#a88470")
    for y in range(h - 1, h - int(size * 0.55), -1):
        t = (h - 1 - y) / (size * 0.55)
        x = cx + int(math.sin(t * 3.0 + seed) * 2.0)
        for dx in range(-1 if t < 0.6 else 0, 2):
            dot(img, px, x + dx, y, trunk_l if dx < 0 else trunk)
    dark, mid, light = rgba("#4f8c6c"), rgba("#82bc8c"), rgba("#c0e2ac")
    blobs = []
    for i in range(7):
        a = i / 7 * 2 * math.pi + seed
        r = size * (0.16 + 0.08 * hash01(i, 1, seed))
        blobs.append((cx + math.cos(a) * size * 0.26, h - size * 0.72 + math.sin(a) * size * 0.14, r))
    blobs.append((cx, h - size * 0.74, size * 0.24))
    for tone, shift, shrink in ((dark, 0.0, 0.0), (mid, -1.0, 1.4)):
        for bx, by, r in blobs:
            rr = r - shrink
            for y in range(int(by - rr + shift), int(by + rr + shift) + 1):
                for x in range(int(bx - rr + shift), int(bx + rr + shift) + 1):
                    if math.hypot(x - bx - shift, y - by - shift) <= rr:
                        dot(img, px, x, y, tone)
    for i in range(size):
        bx, by, r = blobs[int(hash01(i, 2, seed) * len(blobs))]
        x, y = bx + (hash01(i, 3, seed) - 0.65) * r * 1.5, by + (hash01(i, 4, seed) - 0.75) * r * 1.4
        if 0 <= int(x) < img.width and 0 <= int(y) < h and px[int(x), int(y)][3]:
            dot(img, px, x, y, light if i % 5 else rgba("#5a4a78"))
    return img


def tree(height: int, seed: int) -> Image.Image:
    art = Art()
    cypress(art, 60, 200, height, seed, ("#4c9068", "#90cc84", "#346c5c"), -1)
    return crop(art)


def statue() -> Image.Image:
    art = Art()
    statue_dog(art, 60, 200, 11, ("#eadfd0", "#fffdf6", "#c6aab0"))
    return crop(art)


def chips(seed: int) -> Image.Image:
    img, px = sheet(9, 4)
    for x0, w, hh in ((0, 4, 3), (5, 3, 2)) if seed % 2 else ((1, 3, 2), (5, 4, 4)):
        for x in range(x0, x0 + w):
            for y in range(4 - hh, 4):
                dot(img, px, x, y, LIT if y == 4 - hh else DARK if x == x0 + w - 1 else BODY)
    return img


def items() -> list[dict]:
    it = gen_props.item
    keep = {k: vec.C[k] for k in GREENS}
    vec.C.update(GREENS)
    weights = {"fern_a": 1.0, "fern_b": 0.6, "bush_a": 1.2, "bush_b": 0.8, "shroom_tan": 0.2, "glow_lilac_s": 0.12, "vine_s": 3.0, "vine_m": 3.0, "vine_l": 2.2, "vine_xl": 1.2}
    out = []
    for d in gen_props.forest_items():
        if d["name"].startswith(("shroom", "glow", "rock", "stump")) and d["name"] not in weights:
            continue
        d["weight"] = weights.get(d["name"], d["weight"])
        out.append(d)
    out += [
        it("laurel_a", gen_props.shrub(11, 24, 14, "#ffd0dc"), 0.9, "rustle", span=2),
        it("laurel_b", gen_props.shrub(12, 32, 18, "#fff6e8"), 0.6, "rustle", span=3),
        it("pampas_a", gen_props.reeds(11, 6, 15), 1.3, front=0.3),
        it("pampas_b", gen_props.reeds(12, 9, 20), 0.9, front=0.2),
        it("flower_rose", gen_props.flower(11, "#ffb4cc", "#fff0c0", 6.5), 2.0),
        it("flower_peach", gen_props.flower(12, "#ffc8a0", "#fff6e8", 5.5), 1.6),
        it("flower_cream", gen_props.flower(13, "#fff6e8", "#ffd070", 7.0), 1.6),
    ]
    vec.C.update(keep)
    out += [
        it("column_stub_a", column(9, 13, 1, True), 0.7, "none"),
        it("column_stub_b", column(9, 26, 2, True), 0.5, "none"),
        it("column_whole", column(9, 46, 3, False), 0.3, "none"),
        it("column_big", column(13, 60, 4, False), 0.14, "none", span=2),
        it("column_fallen", fallen(34, 1), 0.3, "none", span=3),
        it("blocks_a", bricks(22, 8, 1, False), 0.4, "none", span=2),
        it("blocks_b", bricks(30, 16, 2), 0.35, "none", span=2),
        it("ruin_wall", bricks(46, 32, 3), 0.18, "none", span=3),
        it("arch", arch(1), 0.12, "none", span=3),
        it("urn_a", urn([2, 1, 1, 2, 3, 4, 4, 4, 4, 3, 3, 2, 1, 2], 1), 0.5, "none"),
        it("urn_b", urn([3, 2, 2, 3, 5, 6, 6, 6, 6, 5, 5, 4, 3, 2, 3], 2, ("#c8a0b8", "#ecc8d4", "#9878a0", "#5e4058")), 0.3, "none"),
        it("statue_dog", statue(), 0.12, "none", span=2),
        it("olive_a", olive(1, 24), 0.4, span=2),
        it("olive_b", olive(2, 32), 0.3, span=2),
        it("cypress_a", tree(26, 1), 0.5),
        it("cypress_b", tree(40, 2), 0.3),
        it("chips_a", chips(1), 1.0, "none"),
        it("chips_b", chips(2), 1.0, "none"),
    ]
    return out


def platform() -> None:
    img, px = sheet(48, 16)
    rim, light, body, shade, under = (rgba(c) for c in ("#ffffff", "#fff4f0", "#fbd8dc", "#e8b4cc", "#c896c2"))
    for x in range(48):
        end = min(x, 47 - x)
        top = 3 - int(round(1.0 + 1.0 * math.sin(x * math.pi / 4 + 0.6))) + (3 - end if end < 3 else 0)
        bot = 10 + int(round(1.2 * math.sin(x * math.pi / 4 + 2.4) + 0.6 * math.sin(x * math.pi / 8))) - (4 - end if end < 4 else 0)
        for y in range(top, bot + 1):
            c = rim if y == top else light if y < top + 3 else under if y == bot else shade if y > bot - 3 else body
            px[x, y] = c
    img.save(os.path.join(ASSETS, "tiles", f"{ZONE}_platform.png"))


def fore() -> str:
    import gen_bg_olympus

    img = gen_bg_olympus.bank(41, 332, 9, (14, 28), ("#ffffff", "#fff2ee", "#fbd6da", "#ecb4cc"), "#d49cc4", deep_h=30)
    img = img.crop((0, img.getbbox()[1], img.width, img.height))
    return save(img, "backgrounds", f"{ZONE}_fore.png") and f"{ZONE}_fore.png"


def build() -> dict:
    decor = items()
    atlas, rects = pack([(d["name"], d["image"]) for d in decor], width=256)
    save(atlas, "sprites", "decor", "olympus_decor.png")
    listed = [{**{k: v for k, v in d.items() if k != "image"}, "rect": rects[d["name"]]} for d in decor]
    save_json({"image": "olympus_decor.png", "scale": 1.0 / gen_props.PPU, "items": listed}, "sprites", "decor", "olympus_decor.json")
    platform()
    gen_gate.main()
    return {"decor": "olympus_decor.json", "platform": f"{ZONE}_platform.png", "fore": fore()}


if __name__ == "__main__":
    print(build())
