from __future__ import annotations

from PIL import Image

from vec import hash01, rgba, save

T = 16
BODY, LIT, SHADE, JOINT = (rgba(c) for c in ("#eadfd0", "#fffdf6", "#c6aab0", "#94788c"))
VEIN, VEIN_D = rgba("#dccbc6"), rgba("#cdb8bc")
GOLD, GOLD_L, GOLD_D = (rgba(c) for c in ("#eec45c", "#fff0a8", "#b98842"))
OUTLINE = rgba("#5e4058")
IVY_D, IVY, IVY_L = rgba("#2f5e4c"), rgba("#4c9c5e"), rgba("#a4e284")
CLEAR = (0, 0, 0, 0)


def sheet(w: int, h: int):
    img = Image.new("RGBA", (w, h), CLEAR)
    return img, img.load()


def outline(img: Image.Image, px, keep_top: bool = False) -> None:
    w, h = img.size
    edge = []
    for y in range(h):
        for x in range(w):
            if not px[x, y][3]:
                continue
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if not (0 <= nx < w and 0 <= ny < h) or not px[nx, ny][3]:
                    edge.append((x, y))
                    break
    for x, y in edge:
        px[x, y] = OUTLINE


def marble(x: int, y: int, seed: int, base: tuple = BODY) -> tuple:
    if hash01(x, y, seed) < 0.05:
        return VEIN_D
    if abs((x * 0.7 + y * 1.3 + seed * 3) % 11 - 5) < 0.45:
        return VEIN
    return base


def crack(px, w: int, h: int, x: int, y: int, length: int, seed: int) -> None:
    for k in range(length):
        if 0 <= x < w and 0 <= y < h and px[x, y][3]:
            px[x, y] = JOINT
        y += 1
        x += -1 if hash01(k, 1, seed) < 0.33 else 1 if hash01(k, 1, seed) > 0.66 else 0


def vine_down(px, w: int, h: int, x: int, y0: int, length: int, seed: int, over_air: bool = False) -> None:
    for k in range(length):
        y = y0 + k
        if not (0 <= x < w and 0 <= y < h) or (not over_air and not px[x, y][3]):
            return
        px[x, y] = IVY_D if k % 3 else IVY
        if hash01(y, 2, seed) < 0.55:
            side = 1 if (k + seed) % 2 else -1
            if 0 <= x + side < w and (over_air or px[x + side, y][3]):
                px[x + side, y] = IVY_L if hash01(y, 3, seed) < 0.45 else IVY
        x += 1 if hash01(k, 4, seed) < 0.12 else -1 if hash01(k, 4, seed) > 0.88 else 0


def vine_up(px, w: int, h: int, x: int, length: int, seed: int) -> None:
    for k in range(length):
        y = h - 2 - k
        if not (1 <= x < w - 1 and y >= 1) or not px[x, y][3]:
            return
        px[x, y] = IVY if k % 4 else IVY_D
        if hash01(y, 5, seed) < 0.5:
            side = -1 if (k + seed) % 2 else 1
            if px[x + side, y][3]:
                px[x + side, y] = IVY_L if hash01(y, 6, seed) < 0.4 else IVY
        x += 1 if hash01(k, 7, seed) < 0.2 else -1 if hash01(k, 7, seed) > 0.8 else 0


def column(tw: int, th: int, top: str, seed: int, hang: int = 0) -> Image.Image:
    w, h = tw * T, th * T
    img, px = sheet(w, h + hang)
    cap = top == "capital"
    joints, y = set(), h - 4
    while y > 8:
        y -= 22 + int(hash01(y, 11, seed) * 14)
        joints.add(y)
    for y in range(h):
        for x in range(w):
            if cap and y <= 3:
                c = LIT if y == 1 else BODY if y == 2 else SHADE
            elif cap and y <= 6:
                inset = y - 3
                if x < inset or x >= w - inset:
                    continue
                c = LIT if x < w * 0.3 else SHADE if x > w * 0.72 else BODY
            elif y >= h - 4:
                c = LIT if y == h - 4 else SHADE if y == h - 1 else BODY
            else:
                if x < 2 or x >= w - 2:
                    continue
                f = (x - 2) / (w - 4)
                c = LIT if f < 0.22 else SHADE if f > 0.7 else marble(x, y, seed)
                if (x - 2) % 5 == 4 and 0.08 < f < 0.94:
                    c = VEIN_D if c not in (SHADE, LIT) else JOINT if c == SHADE else BODY
                if y in joints:
                    c = JOINT
                elif y - 1 in joints:
                    c = LIT if f < 0.7 else c
            px[x, y] = c
    if not cap:
        for x in range(2, w - 2):
            edge = min(x - 2, w - 3 - x)
            depth = int(hash01(x // 2, 9, seed) * (5 - edge)) if edge < 5 else 0
            for y in range(depth):
                px[x, y] = CLEAR
        crack(px, w, h, 4 + int(hash01(seed, 1) * (w - 8)), 1, 6 + int(hash01(seed, 2) * 8), seed)
    for k in range(2):
        crack(px, w, h, 3 + int(hash01(k, seed, 3) * (w - 6)), int(hash01(k, seed, 4) * h * 0.8) + 8, 5, seed + k)
    outline(img, px)
    vine_up(px, w, h, 3 + int(hash01(seed, 5) * (w - 6)), int(h * (0.25 + 0.4 * hash01(seed, 6))), seed)
    if cap:
        for k in range(1 + tw // 2):
            vine_down(px, w, h, 2 + int(hash01(k, seed, 7) * (w - 4)), 4, 3 + int(hash01(k, seed, 8) * 9), seed + k)
    return img


def block(tw: int, th: int, seed: int, steps: bool = True) -> Image.Image:
    w, h = tw * T, th * T
    img, px = sheet(w, h)
    for y in range(h):
        for x in range(w):
            row = y // 8
            bx = (x + (9 if row % 2 else 0)) % 18
            by = y % 8
            c = marble(x, y, seed)
            if by == 0:
                c = JOINT
            elif by == 1:
                c = LIT
            elif by == 7:
                c = SHADE
            elif bx == 0:
                c = JOINT
            elif bx == 1:
                c = LIT
            px[x, y] = c
    if steps:
        for x in range(w):
            px[x, 1] = LIT
            px[x, 2] = LIT
            px[x, 3] = BODY
            px[x, 4] = SHADE
        if th >= 3:
            meander(px, w, 9)
    for x in range(w):
        if x in (0, w - 1):
            px[x, 0] = CLEAR
    for k in range(tw):
        crack(px, w, h, int(hash01(k, seed, 1) * w), 5 + int(hash01(k, seed, 2) * max(1, h - 12)), 4 + tw, seed + k)
    outline(img, px)
    for k in range(max(1, tw - 1)):
        vine_down(px, w, h, 2 + int(hash01(k, seed, 3) * (w - 4)), 1, 4 + int(hash01(k, seed, 4) * min(h - 4, 18)), seed + k)
    vine_up(px, w, h, 2 + int(hash01(seed, 9) * (w - 4)), min(h - 3, 6 + int(hash01(seed, 10) * 14)), seed)
    return img


def meander(px, w: int, y0: int) -> None:
    pattern = ("11111", "00001", "11101", "10001", "10111")
    for dy, line in enumerate(pattern):
        for x in range(1, w - 1):
            on = line[(x - 1) % 5] == "1"
            px[x, y0 + dy] = (GOLD_L if dy == 0 and x % 3 == 0 else GOLD) if on else GOLD_D


def drum(tw: int, seed: int) -> Image.Image:
    w, h = tw * T, T
    img, px = sheet(w, h)
    for y in range(h):
        for x in range(w):
            if y == 0 and (x < 2 or x > w - 3):
                continue
            c = LIT if y < 4 else SHADE if y > 11 else marble(x, y, seed)
            if y in (4, 8, 12) and x > 6:
                c = SHADE if c != SHADE else JOINT
            if x == 6 or (x > 6 and (x - 6) % 15 == 0):
                c = JOINT
            px[x, y] = c
    for y in range(1, h - 1):
        ring = abs(y - 7.5)
        for x in range(1, 6):
            px[x, y] = LIT if ring < 3 and x < 4 else BODY if ring < 6 else SHADE
    for y in range(4, h):
        for x in range(w - 1 - int(hash01(y, 3, seed) * 4 * (y / h)), w):
            px[x, y] = CLEAR
    outline(img, px)
    for k in range(2):
        vine_down(px, w, h, 8 + int(hash01(k, seed, 5) * (w - 14)), 1, 4 + int(hash01(k, seed, 6) * 8), seed + k)
    return img


def beam(tw: int, seed: int, hang: int = 10) -> Image.Image:
    w, h = tw * T, T
    img, px = sheet(w, h + hang)
    for y in range(h):
        for x in range(w):
            if y <= 2:
                c = LIT if y == 1 else BODY
            elif y == 3:
                c = SHADE
            elif y <= 9:
                tri = x % 16
                c = marble(x, y, seed)
                if tri in (2, 4, 6):
                    c = SHADE
                elif tri in (1, 7):
                    c = JOINT if y > 4 else SHADE
            elif y <= 14:
                c = SHADE
            else:
                c = SHADE
            px[x, y] = c
    meander(px, w, 10)
    for y in range(3, h):
        for x in range(w - 1 - int(hash01(y, 4, seed) * 7 * (y / h)), w):
            px[x, y] = CLEAR
    for k in range(tw // 2):
        crack(px, w, h, int(hash01(k, seed, 1) * w), 2, 5, seed + k)
    outline(img, px)
    for k in range(tw):
        x = 3 + int(hash01(k, seed, 2) * (w - 12))
        vine_down(px, w, h + hang, x, 3, 6 + int(hash01(k, seed, 3) * (hang + 6)), seed + k, over_air=True)
    return img


def capital_buried(seed: int) -> Image.Image:
    w, h = 40, 14
    img, px = sheet(w, h)
    for y in range(h):
        for x in range(w):
            if y <= 4:
                c = LIT if y == 1 else BODY if y < 4 else SHADE
            else:
                inset = 2 + (y - 5)
                if x < inset or x >= w - inset:
                    continue
                c = LIT if x < w * 0.3 else SHADE if x > w * 0.7 else marble(x, y, seed)
            px[x, y] = c
    crack(px, w, h, 14, 1, 9, seed)
    outline(img, px)
    vine_down(px, w, h, 30, 1, 7, seed)
    return img


def far(img: Image.Image) -> Image.Image:
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if a:
                px[x, y] = (int(r * 0.52), int(g * 0.55), int(b * 0.68), a)
    return img


PIECES = {
    "ruin_step_a": (block, (3, 1, 1)),
    "ruin_step_b": (block, (3, 3, 2)),
    "ruin_step_c": (block, (3, 5, 3)),
    "ruin_col_a": (column, (2, 6, "broken", 4)),
    "ruin_col_b": (column, (2, 9, "capital", 5)),
    "ruin_col_c": (column, (2, 8, "broken", 6)),
    "ruin_drum_a": (drum, (3, 7)),
    "ruin_col_d": (column, (2, 8, "broken", 8)),
    "ruin_wall_a": (block, (2, 11, 9, False)),
    "ruin_col_e": (column, (2, 6, "capital", 10)),
    "ruin_col_f": (column, (2, 6, "capital", 11)),
    "ruin_beam_a": (beam, (10, 12)),
    "ruin_drum_b": (drum, (3, 13)),
    "ruin_col_g": (column, (2, 3, "broken", 14)),
}
DECO = {
    "deco_capital": lambda: capital_buried(15),
    "deco_column_far": lambda: far(column(2, 13, "capital", 16)),
    "deco_column_far_b": lambda: far(column(2, 9, "broken", 17)),
}


def main() -> None:
    for name, (fn, args) in PIECES.items():
        save(fn(*args), "sprites", "props", name + ".png")
    for name, fn in DECO.items():
        save(fn(), "sprites", "props", name + ".png")
    print("ruinas: %d pecas e %d enfeites" % (len(PIECES), len(DECO)))


if __name__ == "__main__":
    main()
