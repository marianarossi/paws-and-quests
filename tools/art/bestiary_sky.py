from __future__ import annotations

import math

from vec import ellipse, mix, smooth

from bestiary_kit import HOT, K, KD, KL, OUT, TAU, WHITE, creature, dark, light, pick, wave, wing

GOLD = "#ffd86b"
BRONZE = "#e0a840"


def _arc(p, center, radius: float, a0: float, a1: float, color, step: float = 12.0) -> None:
    a = a0
    while a <= a1:
        r = math.radians(a)
        p.glow((center[0] + radius * math.cos(r), center[1] + radius * math.sin(r)), color)
        a += step


@creature("Styx Shade", "submundo", 2, origin=(16, 15), move=(4, 6), attack=(5, 9))
def styx_shade(p, anim, i, n):
    veil, veil_l, veil_d, void = "#7fd6d0", "#d6fff5", "#3f8f9a", "#16233f"
    atk = anim == "attack"
    bob = wave(i, n, 1.0) if not atk else 0.0
    stretch = pick((1.0, 0.9, 0.84, 1.22, 1.08), i) if atk else 1.0
    lean = pick((0, -8, -12, 22, 8), i) if atk else 0
    grab = atk and i in (3, 4)
    with p.pose(dy=bob, rot=lean, sx=stretch, sy=2 - stretch):
        w = [wave(i + k * 1.3, n if not atk else 5, 1.2) for k in range(4)]
        shape = smooth([(0, -11.5), (4.6, -9), (6.6, -3), (6.6, 5), (6, 10 + w[0]), (4, 6.5), (2, 12 + w[1]), (0, 7),
                        (-2, 11 + w[2]), (-4, 6.5), (-6, 10 + w[3]), (-6.6, 5), (-6.6, -3), (-4.6, -9)], 2)
        p.poly(shape, veil)
        p.inside(shape, ellipse((-2.6, -6.5), 3.4, 2.8), veil_l)
        p.inside(shape, [(-8, 6.5), (8, 6.5), (8, 15), (-8, 15)], veil_d)
        p.oval((1.4, -3.4), 4.0 if grab else 3.7, 4.8 if grab else 4.1, void)
        if grab:
            p.dot((0, -6), KL, 2, 2)
            p.dot((3, -6), KL, 2, 2)
            p.dot((0, -6), WHITE)
            p.dot((3, -6), WHITE)
            p.dot((1, -2), K, 2, 3)
            p.oval((8.6, -2), 1.7, 1.4, veil_l)
            p.oval((8.0, 3), 1.7, 1.4, veil_l)
        else:
            p.dot((0, -5), KL, 1, 2)
            p.dot((3, -5), KL, 1, 2)
            p.oval((5.6, 2), 1.7, 1.4, veil_l)
            p.oval((-3.6, 2.6), 1.6, 1.3, veil_l)
            p.dot((5, 1), GOLD, 2, 2)
    if atk and i == 3:
        for d in range(3):
            p.glow((-9 - d * 2, -4 + d * 4), veil_l, 2, 1)


@creature("Arges Eye", "míssil teleguiado", 3, origin=(16, 15), move=(4, 12), attack=(6, 10))
def arges_eye(p, anim, i, n):
    metal, metal_l, metal_d, glass = "#4a5f96", "#93acE6", "#2c3a66", "#cfe0ff"
    atk = anim == "attack"
    flap = (0, 1, 2, 1)[i % 4]
    recoil = pick((0, 0, 1, -3, -1, 0), i) if atk else 0
    aim = pick((0.35, 0.7, 1.0, 1.0, 0.4, 0.0), i) if atk else 0.0
    bob = wave(i, n, 0.8) if not atk else 0.0
    shot = atk and i == 3
    with p.pose(dx=recoil, dy=bob):
        tip = (-9, -4, 2)[flap]
        for side in (-1, 1):
            p.blob([(side * 4, -4), (side * 11, tip - 3), (side * 14.4, tip), (side * 11, tip + 3), (side * 5, 0)], glass, 1)
            p.line((side * 5, -2), (side * 12, tip), metal_l)
        p.blob([(-2.5, 6), (3.5, 6), (5.5, 10.5), (1.5, 11.5), (-2, 10)], metal_d, 1)
        p.dot((3, 9), OUT, 2, 2)
        ball = ellipse((0, 0), 7.5, 7.5)
        p.poly(ball, metal)
        p.inside(ball, ellipse((-2.6, -4.4), 4, 2.4), metal_l)
        p.inside(ball, ellipse((0, 6.2), 7.5, 2.6), metal_d)
        eye = ellipse((2.0, 0), 4.7, 4.7)
        p.poly(eye, WHITE)
        p.inside(eye, ellipse((3.4, 0), 2.8, 2.8), KL if shot else K)
        p.inside(eye, ellipse((3.8, 0), 1.3, 1.3), WHITE if shot else OUT)
        lid = 3.4 * aim
        if lid > 0:
            p.inside(eye, [(-4, -6), (8, -6), (8, -4.7 + lid), (-4, -4.7 + lid)], metal_d)
            p.inside(eye, [(-4, 6), (8, 6), (8, 4.7 - lid), (-4, 4.7 - lid)], metal_d)
        p.dot((1, -2), WHITE)
        for rx, ry in ((-6, -1), (-5, 3), (-2, 6)):
            p.dot((rx, ry), metal_l)
        p.line((-1, -7), (-3, -11), metal_d)
        p.dot((-4, -12), KL if aim > 0.5 else K)
    if shot:
        for d in range(4):
            p.glow((7 + d * 2, 10 + d), WHITE if d < 2 else KL, 2, 1)
        p.glow((14, 13), K, 2, 2)


@creature("Erote Archer", "flechas", 3, origin=(15, 17), move=(4, 10), attack=(6, 9))
def erote_archer(p, anim, i, n):
    marble, marble_d, curl, wing_c, wing_l = "#e8e4f4", "#aaa6cc", "#f0c060", "#a9c0f4", "#dbe6ff"
    atk = anim == "attack"
    flap = (0, 1, 2, 1)[i % 4]
    bob = wave(i, n, 0.8) if not atk else 0.0
    pull = pick((0, 1, 2, 3, -1, 0), i) if atk else 0
    with p.pose(dy=bob):
        wy = (-5, -1, 4)[flap]
        p.blob([(-2, -3), (-8, -5 + wy), (-11.5, -1 + wy), (-9, 2 + wy * 0.6), (-5, 1.5 + wy * 0.3), (-2, 1)], wing_c, 1)
        p.blob([(-2.5, -2.4), (-7, -3.6 + wy * 0.8), (-8, -1 + wy * 0.8), (-3, -0.4)], wing_l, 1)
        p.limb((-1, 6), (-2.6, 10), 1.2, marble_d)
        p.limb((1, 6), (0.6, 10.6), 1.2, marble)
        p.oval((0, 3), 3.4, 3.8, marble)
        p.line((-3, 1), (2, 6), curl)
        head = ellipse((0.5, -4.5), 4.6, 4.4)
        p.poly(head, marble)
        p.inside(head, ellipse((3, -1.5), 3, 1.6), light(marble, 0.6))
        for cx, cy, r in ((-3.2, -7.4, 1.9), (-0.4, -9.0, 2.0), (2.6, -8.4, 1.8), (-4.4, -4.6, 1.7)):
            p.oval((cx, cy), r, r, curl)
        aimed = pull >= 2
        p.dot((2, -5), KL if aimed else marble_d, 1, 2)
        p.dot((4, -5), KL if aimed else marble_d, 1, 2)
        p.dot((3, -2), marble_d, 2, 1)
        if pull == 0:
            p.limb((1, 1.5), (6, 4), 1.0, marble)
            for a, b in (((6, -1), (8, 2)), ((8, 2), (8, 5)), ((8, 5), (6, 8))):
                p.line(a, b, BRONZE)
            p.line((6, -1), (6, 8), marble_d)
        else:
            hx = 7.0 - max(pull, 0) * 2.2 if pull > 0 else 5.0
            p.limb((0.5, 0), (9, -1), 1.0, marble)
            p.limb((-0.5, 0.5), (hx, -1), 1.0, marble_d)
            for a, b in (((8, -7), (10, -4)), ((10, -4), (11, -1)), ((11, -1), (10, 2)), ((10, 2), (8, 5))):
                p.line(a, b, BRONZE)
            if pull > 0:
                p.line((8, -7), (hx, -1), marble_d)
                p.line((hx, -1), (8, 5), marble_d)
                p.line((hx, -1), (13, -1), "#f4ead0")
                p.dot((13, -2), K, 2, 3)
                p.dot((15, -1), KL if pull < 3 else WHITE)
                if pull == 3:
                    p.glow((16, -3), WHITE)
                    p.glow((16, 1), WHITE)
            else:
                p.line((8, -7), (8, 5), marble_d)
                for d in range(3):
                    p.glow((12 + d * 2, -1), WHITE if d else KL)


@creature("Harpy", "vento", 3, size=(40, 32), origin=(20, 15), move=(4, 10), attack=(5, 9))
def harpy(p, anim, i, n):
    feather, feather_l, feather_d, face, crest = "#2f8f8a", "#86e6cc", "#1d5a6a", "#f3e6d4", "#1a4658"
    atk = anim == "attack"
    lift = pick((55, 62, -28, -42, 12), i) if atk else (42, 6, -34, 6)[i]
    bob = pick((0, -1, 1, 1, 0), i) if atk else (-1, 0, 1, 0)[i]
    screech = atk and i in (0, 1)
    with p.pose(dy=bob):
        with p.pose(sx=-1):
            wing(p, (-2.5, -1), 12, lift, feather_d, crest, 4, 6)
        wing(p, (-2.5, -1), 12, lift, feather, feather_d, 4, 6)
        for k in (-1, 0, 1):
            p.blob([(k * 1.5 - 1, 5), (k * 4 - 1.5, 11.5), (k * 4 + 1.5, 11.5), (k * 1.5 + 1, 5)], feather_d, 1)
        for side in (-1.6, 1.6):
            p.line((side, 6), (side + 0.4, 9), BRONZE)
            p.dot((side - 1, 10), K, 3, 1)
        body = ellipse((0, 2), 4.3, 5)
        p.poly(body, feather)
        p.inside(body, ellipse((0.8, 3), 2.8, 3.4), feather_l)
        p.blob([(-4.4, -7), (-3, -12), (-0.6, -9.6), (1, -12.6), (2.4, -9.4), (4.6, -11), (4.4, -6)], crest, 1)
        p.oval((0.5, -6), 4.0, 3.9, face)
        p.inside(ellipse((0.5, -6), 4.0, 3.9), ellipse((-1, -9), 4.4, 1.9), crest)
        p.dot((0, -6), OUT, 1, 2)
        p.dot((3, -6), OUT, 1, 2)
        if screech:
            p.tri((1, -4.6), (5.4, -5.2), (2.4, -3.4), BRONZE)
            p.tri((1, -2.2), (4.6, -1.4), (2.6, -3.2), BRONZE)
            p.dot((2, -4), K, 2, 1)
        else:
            p.tri((1, -4.4), (5, -3.2), (1.8, -2.2), BRONZE)
    if screech:
        for r in (7, 10):
            _arc(p, (2, -4 + bob), r + i, -30, 30, WHITE, 15)
    if atk and i in (2, 3):
        for k in range(3):
            fx, fy = 9 + k * 3 + (i - 2) * 3, 2 + k * 3 + (i - 2) * 2
            p.glow((fx, fy), feather_l, 2, 1)
            p.glow((fx + 2, fy + 1), K)


@creature("Empusa Bat", "emboscada", 2, origin=(16, 16), move=(4, 12), hang=(2, 2), attack=dict(frames=3, fps=12, loop=True))
def empusa_bat(p, anim, i, n):
    fur, fur_l, mem, mem_d = "#4a2f5f", "#7a57a0", "#6f4a8f", "#3a2450"
    if anim == "hang":
        p.dot((-2, -16), GOLD, 2, 2)
        p.dot((1, -16), fur, 2, 2)
        cocoon = smooth([(-4.6, -13), (4.6, -13), (5.2, -4), (2.6, 3), (-2.6, 3), (-5.2, -4)], 2)
        p.poly(cocoon, mem)
        p.line((0, -13), (0, 0), mem_d)
        p.line((-3, -12), (-2, -1), mem_d)
        p.line((3, -12), (2, -1), mem_d)
        p.tri((-3.4, 5), (-4.6, 10.6), (-0.6, 7.4), fur)
        p.tri((3.4, 5), (4.6, 10.6), (0.6, 7.4), fur)
        p.dot((-4, 8), K)
        p.dot((3, 8), K)
        p.oval((0, 4.2), 3.7, 3.4, fur)
        if i == 0:
            p.dot((-2, 5), OUT, 2, 1)
            p.dot((1, 5), OUT, 2, 1)
        else:
            p.dot((-2, 5), OUT, 2, 1)
            p.dot((1, 4), KL, 2, 2)
        p.dot((-1, 2), WHITE)
        p.dot((1, 2), WHITE)
        return
    dive = anim == "attack"
    tip = -9 if dive else (-8, -2, 5, -2)[i]
    fold = 0.62 if dive else 1.0
    bob = 0 if dive else (-1, 0, 1, 0)[i]
    with p.pose(rot=38 if dive else 0, dy=bob):
        for side in (-1, 1):
            pts = [(side * 2, -2.5), (side * 8 * fold, tip - 1), (side * 13.4 * fold, tip + 1.5), (side * 11.5 * fold, tip + 5.5),
                   (side * 9 * fold, tip + 3.6), (side * 6.5 * fold, tip + 6.6), (side * 4.5, 2.4 + (tip > 0) * 2), (side * 2, 3)]
            p.poly(pts, mem)
            p.line((side * 2, -2), (side * 12.4 * fold, tip + 1.5), mem_d)
            p.line((side * 2.4, -1), (side * 8.4 * fold, tip + 3.2), mem_d)
        p.dot((-2, 5), GOLD, 1, 2)
        p.dot((1, 5), fur_l, 1, 2)
        p.oval((0, 1), 3.5, 4.0, fur)
        p.inside(ellipse((0, 1), 3.5, 4.0), ellipse((0, 2.4), 2.0, 2.4), fur_l)
        p.tri((-3.8, -4), (-5.2, -10.4), (-0.8, -6.6), fur)
        p.tri((3.8, -4), (5.2, -10.4), (0.8, -6.6), fur)
        p.dot((-4, -8), K, 1, 2)
        p.dot((3, -8), K, 1, 2)
        p.oval((0, -3.6), 3.6, 3.3, fur)
        p.dot((-2, -5), KL, 1, 2)
        p.dot((1, -5), KL, 1, 2)
        if dive:
            p.dot((-1, -2), K, 2, 2)
        p.dot((-2, -2), WHITE)
        p.dot((1, -2), WHITE)
    if dive:
        for d in range(3):
            p.glow((-9 - d * 2 + (i % 2), -11 - d * 2 + i), WHITE, 2, 1)


@creature("Boreas Gust", "gelo", 2, origin=(15, 15), move=(4, 6), attack=(6, 8))
def boreas_gust(p, anim, i, n):
    base, dark_c, lite = "#6b7ba6", "#46527a", "#95a6cf"
    atk = anim == "attack"
    blow = atk and i in (3, 4)
    bob = wave(i, n, 1.0) if not atk else 0.0
    puff = pick((1.04, 1.1, 1.14, 1.0, 1.0, 1.0), i) if atk else 1.0
    with p.pose(dy=bob, sx=puff, sy=puff):
        lumps = ((-4, -1, 5.0), (2, -3, 5.6), (6, 1.4, 4.0), (-1, 3.4, 5.0), (-7, 2.4, 3.4))
        for cx, cy, r in lumps:
            p.oval((cx, cy), r, r * 0.9, base)
        for cx, cy, r in lumps[:2]:
            p.oval((cx - 0.6, cy - 1.8), r * 0.6, r * 0.38, lite)
        p.oval((-1, 6.0), 5.0, 1.6, dark_c)
        p.dot((0, -3), WHITE, 2, 2)
        p.dot((4, -3), WHITE, 2, 2)
        p.dot((1, -2), OUT)
        p.dot((5, -2), OUT)
        p.line((-1, -5), (2, -4), OUT)
        p.line((6, -5), (3, -4), OUT)
        if blow:
            p.oval((8.6, 1.6), 1.6, 1.4, dark_c)
            p.dot((9, 1), OUT)
        elif atk and i < 3:
            p.dot((2, 2), OUT, 2, 1)
        else:
            p.dot((2, 2), OUT, 3, 1)
    for k in range(4):
        a = (k + i / n) / 4 * TAU
        x, y = round(math.cos(a) * 12), round(math.sin(a) * 9)
        p.glow((x, y), WHITE)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            p.glow((x + dx, y + dy), "#d6ecff")
    if blow:
        for d, y in enumerate((-3, 1, 5)):
            p.glow((11 + d % 2 * 2 + (i - 3) * 2, y), WHITE, 4, 1)
