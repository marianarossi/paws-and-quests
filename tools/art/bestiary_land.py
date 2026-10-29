from __future__ import annotations

import math

from vec import ellipse, mix, smooth

from bestiary_kit import HOT, K, KD, KL, OUT, TAU, WHITE, creature, dark, light, pick, wave

SNAKE = "#2f8f72"
GOLD = "#ffd86b"
WOOD = "#8a5a41"


def _step(i: int, k: int) -> float:
    return 1.5 if (i == 0 and k == 0) or (i == 2 and k == 1) else 0.0


@creature("Miasma Toad", "veneno", 2,
          move=dict(frames=6, fps=10, path=[(0, 0), (1, -1), (4, -7), (8, -9), (12, -4), (14, 0)]), attack=(5, 7))
def miasma_toad(p, anim, i, n):
    back, belly, shade = "#6c7d38", "#e6e3a6", "#475428"
    atk = anim == "attack"
    sq = pick((1.0, 0.94, 0.9, 1.1, 1.0), i) if atk else (0.8, 1.14, 1.08, 1.0, 1.04, 0.76)[i]
    air = (not atk) and i in (1, 2, 3, 4)
    sac = pick((3.4, 4.8, 6.4, 3.0, 3.4), i) if atk else 3.2
    burp = atk and i == 3
    with p.pose(sx=2 - sq, sy=sq):
        if air:
            p.limb((-6, -4), (-11.5, -0.8 if i != 2 else -2), 2.0, shade, 1.2)
            p.dot((-13, -1 if i != 2 else -2), shade, 3, 1)
        else:
            p.oval((-6.5, -3.2), 4.4, 3.2, shade)
            p.dot((-10, -1), shade, 5, 1)
        p.oval((0, -6.5), 9, 6, back)
        p.inside(ellipse((0, -6.5), 9, 6), ellipse((2, -2.2), 8, 2.8), belly)
        p.oval((2.6, -12), 2.5, 2.3, back)
        p.oval((7.0, -10.6), 2.3, 2.1, back)
        tone = mix(belly, KL, max(0.0, min(1.0, (sac - 3.2) / 2.4)))
        p.oval((5.6, -3.6 - (sac - 3.2) * 0.35), sac, sac * 0.82, tone)
        if sac > 4:
            p.dot((5 + sac * 0.3, -5 - sac * 0.3), WHITE)
        p.limb((3.5, -3), (5.5, -1), 1.4, shade)
        p.dot((5, -1), shade, 3, 1)
        if burp:
            p.oval((7.4, -6.6), 2.4, 1.5, K)
        else:
            p.line((3, -7), (8.6, -6.4), OUT)
        for ex, ey in ((2, -13), (6.6, -11.6)):
            p.dot((ex, ey), GOLD, 2, 2)
            p.dot((ex, ey + 1), OUT, 2, 1)
        for wx, wy in ((-4.5, -11.5), (-7.6, -8.6), (-1, -12.6)):
            p.dot((wx, wy), K, 2, 2)
            p.dot((wx, wy), KL)
    if atk and i in (3, 4):
        r = 3 if i == 3 else 5
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r and (dx + dy) % 2 == 0:
                    p.glow((11 + dx * 0.9, -10 - (i - 3) * 4 + dy * 0.7), KL if dx * dx + dy * dy < r else K)


@creature("Bronte", "raio", 2, move=(4, 8), attack=(6, 9))
def bronte(p, anim, i, n):
    body, lite, shade = "#3f5fa8", "#86a6ea", "#2a3f78"
    atk = anim == "attack"
    bob = 0 if atk else (0, 1, 0, 1)[i]
    charge = pick((0.3, 0.7, 1.0, 1.0, 0.4, 0.0), i) if atk else 0.0
    swing = pick((-140, -105, -75, 35, 35, -150), i) if atk else (-165, -160, -155, -160)[i]
    for k, fx in enumerate((-3, 3)):
        p.oval((fx, -1.4 - (0 if atk else _step(i, k))), 2.5, 1.5, shade)
    shoulder = (-1.0, -7.0 + bob)

    def hammer() -> None:
        with p.pose(rot=swing, pivot=shoulder):
            p.limb((shoulder[0] + 2, shoulder[1]), (shoulder[0] + 10, shoulder[1]), 0.8, WOOD)
            p.blob([(shoulder[0] + 8.2, shoulder[1] - 3.4), (shoulder[0] + 12.2, shoulder[1] - 3.4),
                    (shoulder[0] + 12.2, shoulder[1] + 3.4), (shoulder[0] + 8.2, shoulder[1] + 3.4)], "#d9a441", 1)
            p.dot((shoulder[0] + 9.5, shoulder[1] - 2), GOLD, 2, 1)

    if not atk:
        hammer()
    p.oval((0, -8 + bob), 6.2, 6.3, body)
    p.inside(ellipse((0, -8 + bob), 6.2, 6.3), ellipse((-2.5, -11.5 + bob), 3.2, 2.2), lite)
    p.inside(ellipse((0, -8 + bob), 6.2, 6.3), ellipse((0, -2.5 + bob), 6, 1.8), shade)
    p.oval((2.2, -8.6 + bob), 3.5, 3.5, WHITE)
    p.oval((3.2, -8.4 + bob), 2.0, 2.0, KL if charge > 0.6 else K)
    p.dot((3, -9 + bob), OUT, 2, 2)
    p.dot((2, -10 + bob), WHITE)
    cloud = mix("#b9c4ea", "#5d6798", charge)
    top = mix("#e6ecff", "#8f9ad0", charge)
    for cx, cy, r in ((-3.6, -14.2, 3.0), (0.6, -15.8, 3.6), (4.2, -14.2, 2.8)):
        p.oval((cx, cy + bob), r, r * 0.9, cloud)
    p.oval((0.2, -16.8 + bob), 2.6, 1.6, top)
    p.oval((-3.8, -15.2 + bob), 1.6, 1.0, top)
    if charge > 0.5:
        for s in range(4):
            a = s * 1.7 + i * 2.3
            p.glow((0.5 + 7.5 * math.cos(a), -15 + bob + 4.5 * math.sin(a)), WHITE if s % 2 else KL)
    if atk:
        hammer()
    if atk and i in (3, 4):
        x = 9.0
        pts = [(x, -1), (x + 1.5, -6), (x - 1, -10), (x + 2, -15), (x, -20), (x + 2, -26), (x + 1, -31)]
        for a, b in zip(pts, pts[1:]):
            p.line((a[0] - 1, a[1]), (b[0] - 1, b[1]), KL, glow=True)
            p.line(a, b, WHITE if i == 3 else HOT, glow=True)
        for dx in (-3, -2, 2, 3):
            p.glow((x + dx, -1), WHITE)


@creature("Minotaur Calf", "labirinto", 3, size=(40, 32), origin=(18, 31), move=(4, 7), attack=(6, 10), stun=(2, 4))
def minotaur_calf(p, anim, i, n):
    hide, hide_d, patch, muzzle, horn, cloth = "#eadfc8", "#b7a996", "#7a5a4a", "#d9aca2", "#fbf5e2", "#2f8f8a"
    atk, stun = anim == "attack", anim == "stun"
    lean = pick((6, 10, 14, 24, 24, -8), i) if atk else (-12 if stun else (0, 2, 0, 2)[i])
    bob = (0, 1, 0, 1)[i] if anim == "move" else 0
    for k, fx in enumerate((-5, 2)):
        lift = _step(i, k) * 1.3 if anim == "move" else 0
        shift = 0
        if atk:
            shift = (pick((0, -4, 0, -4, 5, 0), i), pick((0, 0, 0, 5, -4, 0), i))[k]
        p.limb((fx + 1, -6), (fx + shift, -2.4 - lift), 2.4, hide_d if k == 0 else hide, 2.0)
        p.dot((fx + shift - 2, -1 - lift), OUT, 5, 1)
    if atk and i in (1, 3):
        for d in range(3):
            p.glow((-12 - d * 2, -1 - d), "#d8cfee")
    with p.pose(rot=lean, pivot=(-2, -5), dy=bob):
        p.oval((-8.5, -7), 1.4, 1.2, patch)
        p.oval((-3, -9), 6.6, 6, hide)
        p.inside(ellipse((-3, -9), 6.6, 6), ellipse((-6.5, -11.5), 3.4, 2.8), patch)
        p.blob([(-9, -5.6), (3, -5.6), (2.4, -2.4), (-8.4, -2.4)], cloth, 1)
        p.limb((-1, -9.5), (1.5, -4.5), 2.0, hide_d, 1.8)
        p.band([(2.6, -18), (3.6, -22), (7, -23.6)], 1.3, 0.5, dark(horn, 0.28))
        p.tri((-0.6, -16), (-4.6, -18.4), (-1.4, -13.4), hide_d)
        p.oval((4.5, -14), 6, 5.3, hide)
        p.inside(ellipse((4.5, -14), 6, 5.3), ellipse((1.2, -18), 3.6, 2.6), patch)
        p.oval((8.6, -11.4), 3.7, 2.9, muzzle)
        p.dot((9, -12), OUT)
        p.dot((11, -12), OUT)
        p.dot((9, -10), GOLD, 2, 1)
        p.band([(5.6, -18.4), (7.6, -22.6), (11.6, -23.2)], 1.5, 0.5, horn)
        p.dot((12, -24), K)
        if stun:
            p.dot((5, -16), OUT, 1, 1)
            p.dot((7, -16), OUT, 1, 1)
            p.dot((6, -15), OUT, 1, 1)
            p.dot((5, -14), OUT, 1, 1)
            p.dot((7, -14), OUT, 1, 1)
        else:
            p.dot((6, -16), OUT, 2, 2)
            p.dot((5, -17), OUT, 4, 1)
            if atk:
                p.dot((6, -16), KL)
        if atk and i in (0, 1):
            for d in range(2 + i):
                p.glow((13 + d * 1.5, -10 + d), WHITE, 2, 1)
    if stun:
        for s in range(3):
            a = TAU * s / 3 + i * 1.0
            p.glow((1 + 8 * math.cos(a), -24 + 2.5 * math.sin(a)), GOLD, 2, 1)
            p.glow((1.5 + 8 * math.cos(a), -24.6 + 2.5 * math.sin(a)), GOLD, 1, 3)
    if atk and i in (3, 4):
        for d, y in enumerate((-19, -13, -7)):
            p.glow((-15 - d % 2 * 2, y), WHITE, 3, 1)


@creature("Karkinos", "carapaça", 2, move=(4, 10), attack=(5, 9), guard=(2, 3))
def karkinos(p, anim, i, n):
    shell, shell_l, shell_d, under = "#3458b0", "#77a2ee", "#22386f", "#cfdcff"
    atk, guard = anim == "attack", anim == "guard"
    walk = anim == "move"
    sway = (-1, 0, 1, 0)[i] if walk else 0
    low = (2 + i % 2) if guard else (pick((0, 1, -1, 1, 0), i) if atk else 0)
    lift_claw = pick((3, 8, 9, -1, 0), i) if atk else 0
    opened = atk and i in (1, 2)
    for side in (-1, 1):
        for k in range(3):
            up = 1 if walk and (k + i + (side > 0)) % 2 == 0 else 0
            a = (side * (5 + k * 1.4) + sway, -4.5 + low)
            m = (side * (7.5 + k * 2.0) + sway, -6 + low - (1 - k) * 0.5)
            b = (side * (8.5 + k * 2.3) + sway * 0.5, -1 - up)
            p.line(a, m, shell_d)
            p.line(m, b, shell_d)
    for side in (-1, 1):
        cx, cy = (side * 5.5, -5.0 + low) if guard else (side * 11.4 + sway, -7.0 - lift_claw + low)
        p.limb((side * 7 + sway, -7 + low), (cx, cy), 1.2, shell_d)
        if opened:
            p.blob([(cx - 2.8, cy), (cx - 2.0, cy - 5.4), (cx - 0.1, cy - 1.2)], K, 1)
            p.blob([(cx + 2.8, cy), (cx + 2.0, cy - 5.4), (cx + 0.1, cy - 1.2)], K, 1)
            p.oval((cx, cy + 0.6), 2.7, 2.0, K)
        else:
            p.oval((cx, cy - 1), 2.8, 3.1, K)
            p.line((cx, cy - 4), (cx, cy - 2), KD)
        p.dot((cx - 1.5, cy - 1), KL)
    dome = [(x + sway, y + low) for x, y in smooth([(-9, -3.6), (-9.4, -9), (-5, -14.4), (5, -14.4), (9.4, -9), (9, -3.6)], 2)]
    if not guard:
        for side in (-1, 1):
            p.line((side * 2.5 + sway, -13 + low), (side * 3 + sway, -17 + low), shell_d)
            p.dot((side * 3 + sway - 1, -19 + low), WHITE, 2, 2)
            p.dot((side * 3 + sway - (1 if side < 0 else 0), -18 + low), OUT)
    p.poly(dome, shell)
    p.inside(dome, ellipse((-3 + sway, -11.6 + low), 4.4, 2.0), shell_l)
    p.inside(dome, ellipse((sway, -3.4 + low), 11, 2.4), shell_d)
    for dx, dy in ((0, -13), (1, -12), (-1, -12), (0, -11)):
        p.dot((dx + sway, dy + low), under)
    if not guard:
        p.dot((-3 + sway, -7 + low), under, 7, 1)
        p.dot((-1 + sway, -6 + low), shell_d, 3, 1)


@creature("Spartoi", "ossos", 2, move=(4, 8), attack=(6, 10), rise=(5, 8))
def spartoi(p, anim, i, n):
    bone, bone_d, helm, helm_l, shaft = "#f1ebdd", "#b9b1c6", "#3a3350", "#5d5788", "#b98458"
    atk, rise, walk = anim == "attack", anim == "rise", anim == "move"
    up = pick((23, 17, 11, 5, 0), i) if rise else 0
    bob = (0, 1, 0, 1)[i] if walk else 0
    wind = pick((0, 1, 2, 3, 4, 0), i) if atk else 0
    with p.pose(dy=up):
        for k, fx in enumerate((-2, 2)):
            fwd = ((2, 0, -2, 0), (-2, 0, 2, 0))[k][i] if walk else ((-3, 3)[k] if atk else 0)
            lift = 1 if walk and ((i == 1 and k == 0) or (i == 3 and k == 1)) else 0
            knee = (fx * 0.5 + fwd * 0.5 + 1, -4 - lift)
            col = bone_d if k == 0 else bone
            p.line((fx * 0.5, -7 + bob), knee, col)
            p.line(knee, (fx + fwd, -1 - lift), col)
            p.dot((fx + fwd, -1 - lift), col, 2, 1)
        p.dot((-2, -8 + bob), bone, 4, 1)
        p.line((0, -9 + bob), (0, -15 + bob), bone_d)
        for r in range(3):
            p.dot((-2, -14 + r * 2 + bob), bone, 5, 1)
        head = (1.0, -19.0 + bob)
        p.band([(-4, head[1] - 2.6), (-1, head[1] - 6.4), (4, head[1] - 5)], 1.3, 0.9, K)
        skull = ellipse(head, 4.2, 3.9)
        p.poly(skull, bone)
        p.inside(skull, ellipse((head[0] - 0.6, head[1] - 2.6), 5.4, 2.5), helm)
        p.inside(skull, ellipse((head[0] - 3.6, head[1]), 1.4, 3.8), helm)
        p.dot((head[0] - 2, head[1] - 4), helm_l, 3, 1)
        p.dot((0, head[1] + 4), bone, 4, 1)
        p.dot((1, head[1] + 4), OUT)
        p.dot((3, head[1] + 4), OUT)
        p.dot((1, head[1] - 1), OUT, 2, 2)
        p.dot((4, head[1] - 1), OUT, 1, 2)
        p.dot((2, head[1]), KL)
        shoulder = (1.0, -14.0 + bob)
        if wind in (1, 2):
            hand = (-3.0 - wind, -16.0 - wind * 0.5)
            p.line(shoulder, hand, bone)
            a, b = (hand[0] - 6, hand[1] + 3), (hand[0] + 10, hand[1] - 4)
            p.line(a, b, shaft)
            p.dot((b[0], b[1] - 1), K, 2, 2)
            p.dot((b[0] + 1, b[1] - 1), KL)
        elif wind in (3, 4):
            p.line(shoulder, (6, -15), bone)
            if wind == 3:
                p.line((8, -16), (14, -17), shaft, glow=True)
                p.glow((14, -18), K, 2, 2)
        else:
            hand = (5.0, -11.0 + bob)
            p.line(shoulder, hand, bone)
            p.line((5, -2), (5, -25 + bob), shaft)
            p.dot((4.5, -27 + bob), K, 2, 2)
            p.dot((5, -27 + bob), KL)
    if rise and i < 4:
        for s in range(5):
            p.glow((-6 + s * 3 + (i * s) % 2, -1 - (i + s) % 3), "#8a7fa8" if s % 2 else "#5d5788")
