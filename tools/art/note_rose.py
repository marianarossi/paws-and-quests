from __future__ import annotations

import math
import os

from PIL import Image

from vec import DOCS_PREVIEW, Canvas, curve, ellipse, hash01, ribbon, rgba, smooth

W, H = 140, 160
P = ("#ffe4ec", "#ffb4c8", "#f2829e", "#dc5e80", "#b2405f", "#7e2846")
P_LINE = "#47162d"
G = ("#cdf2bf", "#93d79c", "#5ea67e", "#3e7c63", "#2b5a4b")
G_LINE = "#173a30"
THORN = "#8a4a4e"

HEAD = (40.0, 38.0)
TILT = math.radians(-30)
CUP = (1.0, 1.0)
FLARE = 1.0
TURNS = 2.4


def head_pts(pts: list) -> list:
    c, s = math.cos(TILT), math.sin(TILT)
    pts = [(x * CUP[0], y * CUP[1]) for x, y in pts]
    return [(HEAD[0] + x * c - y * s, HEAD[1] + x * s + y * c) for x, y in pts]


def stem_line() -> list:
    base = head_pts([(0, 18 if OPEN else 23)])[0]
    bx, by = base
    return curve([base, (bx + 9, by + 14), (bx + 21, by + 30), (bx + 23, by + 50), (bx + 30, by + 72),
                  (bx + 48, by + 88), (bx + 68, by + 96)], 8)


def leaf(cv: Canvas, at, angle: float, length: float, width: float, flip: int) -> None:
    ca, sa = math.cos(angle), math.sin(angle)

    def tr(u: float, v: float):
        return (at[0] + u * ca - v * sa, at[1] + u * sa + v * ca)

    top, bot = [], []
    n = 14
    for i in range(n + 1):
        t = i / n
        u = t * length
        half = width * math.sin(math.pi * t ** 0.8) * (1.0 - 0.15 * t)
        tooth = 1.3 if (i % 2 and 0.15 < t < 0.92) else 0.0
        top.append(tr(u, -(half + tooth)))
        bot.append(tr(u, half + tooth))
    shape = top + bot[::-1]
    cv.poly([tr(-3, -0.8), tr(-3, 0.8), tr(1, 0.8), tr(1, -0.8)], G[3])
    cv.poly(shape, G[1])
    shade = bot if flip > 0 else top
    cv.clip(shape, [tr(0, 0)] + shade + [tr(length, 0)], G[2])
    cv.clip(shape, [tr(u * length / 10, (0.2 + 0.25 * width * math.sin(math.pi * u / 10)) * flip) for u in range(11)]
            + [tr(length, 0)] + [tr(u * length / 10, (0.2 + 0.7 * width * math.sin(math.pi * u / 10)) * flip) for u in range(10, -1, -1)], G[3])
    cv.poly(ribbon([tr(u * length / 12, 0) for u in range(12)], 0.55, 0.2), G[3])
    for k in (0.3, 0.55):
        cv.dot(tr(k * length, -flip * width * 0.45), G[0])


def petal_lip(cv: Canvas, clip_shape: list, lip: list, light: str, shine: str, crease: str) -> None:
    cv.clip(clip_shape, ribbon([(x, y + 1.6) for x, y in lip], 1.3, 0.9), crease)
    cv.clip(clip_shape, ribbon(lip, 1.4, 1.0), light)
    cv.clip(clip_shape, ribbon([(x, y - 0.5) for x, y in lip[2:-2]], 0.55, 0.4), shine)


def spiral(cv: Canvas, cx: float, cy: float, rmax: float, squash: float) -> None:
    turns = TURNS
    n = 160
    spacing = (rmax - 1.5) / turns
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        th0, th1 = t0 * turns * 2 * math.pi + 0.6, t1 * turns * 2 * math.pi + 0.6
        r0, r1 = 1.5 + (rmax - 1.5) * t0, 1.5 + (rmax - 1.5) * t1
        mid = (th0 + th1) / 2
        gap = 1.25 / math.sqrt(math.cos(mid) ** 2 + (squash * math.sin(mid)) ** 2)
        petal = (mid - 0.6) % 3.6
        if petal < 0.35:
            gap *= 1.9
        band = max(0.8, spacing - gap)

        def at(r: float, th: float):
            return (cx + r * math.cos(th), cy + r * squash * math.sin(th))
        lit = -math.sin(mid) * 0.75 - math.cos(mid) * 0.45
        k = 0 if lit > 0.55 else 1 if lit > 0.05 else 2 if lit > -0.45 else 3
        if t0 < 0.12:
            k = max(k, 2)
        if petal > 3.1:
            k = max(0, k - 1)
        for f0, f1, dk in ((0.0, 0.3, -1), (0.3, 0.72, 0), (0.72, 1.0, 1)):
            quad = [at(r0 - band * f0, th0), at(r1 - band * f0, th1), at(r1 - band * f1, th1), at(r0 - band * f1, th0)]
            cv.poly(head_pts(quad), P[min(4, max(0, k + dk))])


def head(cv: Canvas) -> None:
    hp = head_pts
    for ang, ln in ((-78, 17), (-38, 15), (38, 15), (78, 17), (0, 12)):
        a = math.radians(ang)
        root = (math.sin(a) * 9, 16)
        mid = (math.sin(a) * (9 + ln * 0.55), 19 + math.cos(a) * ln * 0.35)
        tip = (math.sin(a) * (9 + ln), 17 + math.cos(a) * ln * 0.9)
        cv.poly(hp(ribbon(curve([root, mid, tip], 4), 2.4, 0.35)), G[2])
        cv.poly(hp(ribbon(curve([(root[0], root[1] - 0.6), (mid[0], mid[1] - 0.6), tip], 4), 0.9, 0.2)), G[1])
    def fl(pts: list) -> list:
        return [(math.copysign(20 + (abs(x) - 20) * FLARE, x) if abs(x) > 20 else x, y) for x, y in pts]
    left_flare = smooth(fl([(-21, -13), (-34, -17), (-33, -5), (-28, 9), (-16, 15)]), 2)
    right_flare = smooth(fl([(21, -14), (34, -19), (33, -5), (27, 9), (16, 15)]), 2)
    cv.poly(hp(left_flare), P[3])
    cv.poly(hp(right_flare), P[4])
    petal_lip(cv, hp(left_flare), hp(curve(fl([(-20, -12), (-28, -15), (-34, -17)]), 4)), P[1], P[0], P[5])
    petal_lip(cv, hp(right_flare), hp(curve(fl([(20, -13), (28, -16), (34, -19)]), 4)), P[2], P[1], P[5])
    cv.clip(hp(left_flare), hp([(-36, 0), (-20, 4), (-14, 20), (-36, 20)]), P[4])
    body = smooth([(-25, -12), (-25, 2), (-19, 15), (-9, 22), (0, 24), (9, 22), (19, 15), (25, 2), (25, -12)], 3)
    cv.poly(hp(body), P[3])
    rim = ellipse((0, -12), 24.5, 11.0, n=48)
    cv.poly(hp(rim), P[4])
    back_lip = [p for p in ellipse((0, -12), 23.6, 10.2, n=48) if p[1] < -14.5]
    back_lip.sort(key=lambda p: p[0])
    cv.clip(hp(rim), hp(ribbon(back_lip, 1.2, 1.2)), P[2])
    cv.clip(hp(rim), hp(ribbon([p for p in back_lip if p[0] < 4], 0.6, 0.6)), P[1])
    cv.poly(hp(ellipse((0.4, -12.6), 21.5, 9.2, n=48)), P[5])
    spiral(cv, 0.5, -13.0, 21.0, 0.44)
    f1 = smooth([(-26, -10), (-14, -3), (3, -5), (1, 10), (-4, 23), (-15, 18), (-24, 6)], 2)
    f2 = smooth([(-3, -5), (11, -1), (26, -11), (25, 4), (19, 15), (6, 23), (0, 10)], 2)
    f3 = smooth([(-18, 6), (-6, 12), (8, 11), (19, 5), (14, 16), (4, 23), (-6, 23), (-15, 16)], 2)
    cv.poly(hp(f1), P[2])
    cv.clip(hp(f1), hp([(-30, 4), (-12, 16), (-4, 30), (-30, 30)]), P[3])
    cv.poly(hp(f2), P[3])
    cv.clip(hp(f2), hp([(13, 2), (30, -14), (30, 30), (6, 30)]), P[4])
    cv.poly(hp(ribbon(curve([(2, -4), (3, 4), (1, 12), (-3, 22)], 4), 0.7, 0.5)), P[5])
    petal_lip(cv, hp(f1), hp(curve([(-26, -10), (-14, -3), (-2, -4), (3, -5)], 4)), P[1], P[0], P[5])
    petal_lip(cv, hp(f2), hp(curve([(-3, -5), (9, -1.5), (18, -3.5), (24.5, -8)], 4)), P[2], P[1], P[5])
    cv.poly(hp(f3), P[2])
    cv.clip(hp(f3), hp([(4, 15), (20, 5), (20, 30), (0, 30)]), P[3])
    cv.clip(hp(f3), hp([(-20, 19), (-4, 22), (-4, 30), (-20, 30)]), P[3])
    petal_lip(cv, hp(f3), hp(curve([(-18, 6), (-6, 12), (8, 11), (19, 5)], 4)), P[1], P[0], P[5])
    for pts in (((-19, 2), (-14, 9), (-11, 15)), ((14, 2), (13, 8), (11, 14)), ((-3, 16), (-2, 21)), ((7, 16), (6, 21))):
        cv.clip(hp(body), hp(ribbon(curve(list(pts), 3), 0.45, 0.3)), P[4])
    for x, y, c in ((-21, -5, P[0]), (-9, 14, P[1]), (-23, -2, P[1])):
        cv.dot(hp([(x, y)])[0], c)


def stem(cv: Canvas) -> list:
    line = stem_line()
    cv.poly(ribbon(line, 2.1, 1.6), G[2])
    cv.poly(ribbon([(x - 0.9, y - 0.5) for x, y in line[1:-1]], 0.7, 0.55), G[1])
    cv.poly(ribbon([(x + 1.2, y + 0.6) for x, y in line[2:]], 0.6, 0.5), G[3])
    return line


def thorns(cv: Canvas, line: list) -> None:
    for i, side in ((7, 1), (17, -1), (29, 1), (41, -1)):
        x, y = line[i]
        a, b = line[i - 1], line[i + 1]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d * side, dx / d * side
        cv.poly([(x - dx / d * 1.6 + nx * 1.4, y - dy / d * 1.6 + ny * 1.4),
                 (x + dx / d * 1.6 + nx * 1.4, y + dy / d * 1.6 + ny * 1.4),
                 (x + dx / d * 2.4 + nx * 5.0, y + dy / d * 2.4 + ny * 5.0)], THORN)


def outline(img: Image.Image) -> None:
    px = img.load()
    greens = {rgba(c)[:3] for c in G} | {rgba(THORN)[:3], rgba(G_LINE)[:3]}
    edge = []
    for y in range(img.height):
        for x in range(img.width):
            if px[x, y][3]:
                continue
            near = [px[x + dx, y + dy] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                    if 0 <= x + dx < img.width and 0 <= y + dy < img.height and px[x + dx, y + dy][3]]
            if near:
                petal = sum(1 for c in near if c[:3] not in greens)
                edge.append((x, y, (O_EDGE if OPEN else P_LINE) if petal * 2 >= len(near) and petal else G_LINE))
    for x, y, c in edge:
        px[x, y] = rgba(c)


O = ("#fff5f8", "#fcd0dc", "#f7a9bf", "#ef84a3", "#d95f84", "#ad3f63")
O_LINE = "#e2674f"
O_EDGE = "#a8403e"
OPEN = True
SQUASH = 0.86


def petal_shape(cx: float, cy: float, ang: float, r0: float, r1: float, half: float, seed: int, grow: float = 0.0) -> list:
    ca, sa = math.cos(ang), math.sin(ang)
    pts = []
    n = 26
    length = r1 - r0
    for i in range(n + 1):
        t = math.pi * i / n
        u = (1 - math.cos(t)) * 0.5
        w = half * (math.sin(math.pi * min(1.0, u * 0.9 + 0.1)) ** 0.5) * (0.55 + 0.45 * u)
        ruffle = 1.0 + 0.035 * math.sin(i * 0.9 + seed * 2.3) * u * u
        uu = (r0 + length * u * ruffle) + grow
        vv = (w + grow) * (1 if i <= n else -1)
        pts.append((uu, vv))
    pts += [(u, -v) for u, v in reversed(pts)]
    return [(cx + u * ca - v * sa, (cy + u * sa + v * ca)) for u, v in pts]


def head_open(cv: Canvas) -> None:
    hp = head_pts
    sq = lambda pts: [(x, y * SQUASH) for x, y in pts]
    for ang in (60, 90, 120, 25, 155):
        a = math.radians(ang)
        tip = (math.cos(a) * 34, math.sin(a) * 30)
        base_l = (math.cos(a - 0.25) * 18, math.sin(a - 0.25) * 18)
        base_r = (math.cos(a + 0.25) * 18, math.sin(a + 0.25) * 18)
        cv.poly(hp(sq([base_l, tip, base_r])), G[3])
        cv.poly(hp(sq([base_l, ((base_l[0] + tip[0]) / 2, (base_l[1] + tip[1]) / 2 - 0.5), tip, (base_l[0] * 0.7 + base_r[0] * 0.3, base_l[1] * 0.7 + base_r[1] * 0.3)])), G[2])
    rings = ((6, 33, 17.5, 6, 0.20, 0), (3, 25, 14.0, 5, 0.85, 0), (-3, 17, 11.0, 5, 0.30, 1), (-5, 10.5, 7.5, 4, 1.4, 2))
    seed = 0
    for k, (r0, base_r1, half, count, rot, tone) in enumerate(rings):
        angs = [rot + 2 * math.pi * i / count + 0.22 * (hash01(i, k, 7) - 0.5) for i in range(count)]
        angs.sort(key=lambda a: math.sin(a))
        for a in angs:
            seed += 1
            lit = -math.sin(a) * 0.6 - math.cos(a) * 0.5 + 0.1
            t = tone + (0 if lit > 0.3 else 1 if lit > -0.4 else 2)
            body = O[min(4, 1 + t)]
            light = O[max(0, t)]
            shade = O[min(5, 2 + t)]
            r1 = base_r1 * (0.9 + 0.18 * hash01(seed, 3))
            line_shape = sq(petal_shape(0, 0, a, r0, r1, half, seed, 1.1))
            shape = sq(petal_shape(0, 0, a, r0, r1, half, seed))
            cv.poly(hp(line_shape), O_LINE)
            cv.poly(hp(shape), body)
            cv.clip(hp(shape), hp(sq(petal_shape(0, 0, a, r0 - 2, r0 + (r1 - r0) * 0.5, half * 0.8, seed))), shade)
            cv.clip(hp(shape), hp(sq(petal_shape(0, 0, a, r0 - 2, r0 + (r1 - r0) * 0.22, half * 0.5, seed))), O[min(5, 3 + t)])
            outer = sq(petal_shape(0, 0, a, r0, r1, half, seed))
            inner = sq(petal_shape(0, 0, a, r0, r1 - 2.2, half - 1.6, seed))
            cv.clip(hp(outer), hp(_ring(outer, inner)), light)
            ca, sa = math.cos(a), math.sin(a)
            for dv in (-0.35, 0.3):
                p0 = (ca * (r0 + 1) - sa * dv * half * 0.4, sa * (r0 + 1) + ca * dv * half * 0.4)
                p1 = (ca * (r0 + (r1 - r0) * 0.55) - sa * dv * half, sa * (r0 + (r1 - r0) * 0.55) + ca * dv * half)
                cv.clip(hp(shape), hp(sq(ribbon([p0, p1], 0.4, 0.3))), shade)
            def across(rr: float, v0: float, v1: float) -> list:
                return [(ca * (rr - 1.2 * abs(v) / half) - sa * v, sa * (rr - 1.2 * abs(v) / half) + ca * v)
                        for v in (v0 + (v1 - v0) * j / 6 for j in range(7))]
            if k < 3:
                roll = r0 + (r1 - r0) * (0.62 + 0.1 * hash01(seed, 5))
                side = 1 if hash01(seed, 9) > 0.5 else -1
                cv.clip(hp(shape), hp(sq(ribbon(across(roll, -0.62 * half * side, 0.3 * half * side), 0.45, 0.4))), O_LINE)
                if lit > -0.1:
                    cv.clip(hp(shape), hp(sq(ribbon(across(r1 - 1.9, -0.55 * half, 0.15 * half), 0.45, 0.35))), O[0])
            if lit > -0.2 and k < 3:
                tip = (ca * (r1 - 3.5) - sa * half * 0.25, sa * (r1 - 3.5) + ca * half * 0.25)
                cv.dot(hp(sq([tip]))[0], O[0])
                if k < 2:
                    tip2 = (ca * (r1 - 5.5) + sa * half * 0.35, sa * (r1 - 5.5) - ca * half * 0.35)
                    cv.dot(hp(sq([tip2]))[0], O[0])
    cv.poly(hp(sq(ellipse((0, 0), 4.6, 4.2))), O_LINE)
    cv.poly(hp(sq(ellipse((0.3, -0.2), 3.6, 3.2))), O[4])
    cv.poly(hp(sq(ribbon(curve([(-2.5, 0.5), (-0.5, -1.8), (2.0, -0.6), (1.0, 1.5)], 3), 0.55, 0.45))), O[5])
    cv.dot(hp(sq([(-1.5, -1.5)]))[0], O[2])
    for r, a0, a1 in ((6.2, 3.6, 6.4), (8.0, 0.4, 2.9), (5.0, 1.2, 3.3)):
        arc = [(r * math.cos(a0 + (a1 - a0) * j / 8), r * math.sin(a0 + (a1 - a0) * j / 8)) for j in range(9)]
        cv.poly(hp(sq(ribbon(arc, 0.5, 0.4))), O_LINE)


def _ring(outer: list, inner: list) -> list:
    return outer + list(reversed(inner))


def note_rose() -> Image.Image:
    cv = Canvas(W, H)
    line = stem_line()
    leaf(cv, line[12], math.radians(-12), 27, 8.0, 1)
    leaf(cv, line[22], math.radians(158), 29, 8.5, -1)
    leaf(cv, line[36], math.radians(40), 22, 6.5, 1)
    stem(cv)
    thorns(cv, line)
    head_open(cv) if OPEN else head(cv)
    img = cv.finish()
    outline(img)
    return img


def shadow(img: Image.Image, color, offset=(3, 4)) -> Image.Image:
    sh = Image.new("RGBA", (img.width + offset[0], img.height + offset[1]), (0, 0, 0, 0))
    mask = img.split()[3]
    sh.paste(rgba(color), offset, mask)
    return sh


VARIANTS = (
    ("1 nova", {}),
    ("2 vermelha", {"O": ("#ffe9e6", "#ff9f96", "#f0645f", "#d8404a", "#b02a3c", "#7c1a2c"), "O_LINE": "#a3222f", "O_EDGE": "#5e1020"}),
    ("3 coral", {"O": ("#fff6ec", "#ffd3b8", "#ffae92", "#f5857a", "#dc6068", "#a8414f"), "O_LINE": "#d0574a", "O_EDGE": "#8a3348"}),
    ("4 cha clara", {"O": ("#ffffff", "#fff0f2", "#fcd6de", "#f3b4c4", "#e08fa6", "#b86a84"), "O_LINE": "#e88c7c", "O_EDGE": "#a35a6a"}),
    ("5 lavanda", {"O": ("#fbf6ff", "#e6d4fa", "#cbb0ee", "#ab8bd8", "#8869bb", "#5f4790"), "O_LINE": "#9a6cc6", "O_EDGE": "#4f3a78"}),
    ("6 rosa forte", {"O": ("#fff0f5", "#ffb3cb", "#f7819f", "#e85a82", "#c63c68", "#8e2550"), "O_LINE": "#d94a4a", "O_EDGE": "#7a2038"}),
    ("7 em pe", {"TILT": 0.0, "HEAD": (52.0, 38.0)}),
    ("8 anterior", {"OPEN": False}),
)


def variants_sheet(path: str) -> None:
    from PIL import ImageDraw
    g = globals()
    base = {k: g[k] for k in ("P", "P_LINE", "TILT", "HEAD", "CUP", "FLARE", "TURNS", "O", "O_LINE", "O_EDGE", "OPEN")}
    cell_w, cell_h, cols = W + 20, H + 30, 4
    sheet = Image.new("RGBA", (cell_w * cols, cell_h * 2), rgba("#1c1a33"))
    for i, (name, opts) in enumerate(VARIANTS):
        g.update(base)
        g.update(opts)
        cell = Image.new("RGBA", (cell_w - 4, cell_h - 4), rgba("#f3e2bf"))
        rose = note_rose()
        cell.alpha_composite(shadow(rose, "#d3b588"), (8, 20))
        cell.alpha_composite(rose, (8, 20))
        ImageDraw.Draw(cell).text((6, 4), name, fill=rgba("#4a2a3a"))
        sheet.alpha_composite(cell, ((i % cols) * cell_w + 2, (i // cols) * cell_h + 2))
    g.update(base)
    sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save(path)
    print("folha:", path)


if __name__ == "__main__":
    rose = note_rose()
    bg = Image.new("RGBA", (W + 16, H + 16), rgba("#f3e2bf"))
    bg.alpha_composite(shadow(rose, "#d6bb8e"), (8, 8))
    bg.alpha_composite(rose, (8, 8))
    path = os.path.join(DOCS_PREVIEW, "ember", "rosa_bilhete.png")
    bg.resize((bg.width * 5, bg.height * 5), Image.NEAREST).save(path)
    print("previa:", path)
    variants_sheet(os.path.join(DOCS_PREVIEW, "ember", "rosas_opcoes.png"))
