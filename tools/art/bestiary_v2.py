from __future__ import annotations

import math

from vec import ellipse, mix, smooth

from bestiary_kit import HOT, K, KD, KL, OUT, TAU, WHITE, creature, dark, light, pick, wave

GOLD, GOLD_L, GOLD_D = "#f2c14e", "#ffe9a0", "#b7802e"
BRONZE, BRONZE_L, BRONZE_D = "#d0913c", "#f4c36a", "#8a5527"
WOOD, WOOD_D = "#8a5a41", "#5e3b2c"


def _shade(p, shape, c, rx, ry, lite, deep, lx=-0.35, ly=-0.45, dx=0.25, dy=0.5):
    p.inside(shape, ellipse((c[0] + dx * rx, c[1] + dy * ry + ry * 0.35), rx * 1.05, ry * 0.7), deep)
    p.inside(shape, ellipse((c[0] + lx * rx, c[1] + ly * ry), rx * 0.55, ry * 0.42), lite)


def _ball(p, c, rx, ry, base, lite, deep, **kw):
    shape = ellipse(c, rx, ry)
    p.poly(shape, base)
    _shade(p, shape, c, rx, ry, lite, deep, **kw)
    return shape


def _eye(p, x, y, iris, w=2, h=2, shine=True):
    p.dot((x, y), iris, w, h)
    if shine:
        p.dot((x, y), WHITE)


@creature("Empusa Bat", "emboscada", 2, origin=(16, 16),
          hang=dict(frames=2, fps=2, loop=True), peek=dict(frames=2, fps=5, loop=False),
          move=dict(frames=4, fps=12, loop=True), attack=dict(frames=3, fps=14, loop=True))
def empusa_bat(p, anim, i, n):
    fur, fur_l, fur_d = "#5a3d82", "#8a6cba", "#3b2758"
    tuft = "#cdb8ee"
    mem, mem_l, mem_d, bone = "#71519b", "#8b6bb8", "#4a3270", "#c3aee6"
    ear_in = "#b993dc"

    def legs(y, dangle=0):
        p.limb((-1.6, y), (-1.8, y + 2.2 + dangle), 0.7, fur_d)
        p.limb((1.6, y), (2.0, y + 2.6 + dangle), 0.8, BRONZE)
        p.dot((2, y + 2 + dangle), BRONZE_L)

    if anim in ("hang", "peek"):
        sway = (0, 0.5)[i] if anim == "hang" else 0
        p.dot((-2, -16), fur_d, 2, 1)
        p.dot((1, -16), BRONZE, 2, 1)
        p.dot((1, -15), BRONZE_L)
        p.dot((-2, -15), fur_d)
        cocoon = [(-5.2, -13.6), (5.2, -13.6), (6.4, -6), (4.4, 1.8), (0, 3.2), (-4.4, 1.8), (-6.4, -6)]
        with p.pose(rot=sway * 3, pivot=(0, -15)):
            p.blob(cocoon, mem)
            p.inside(cocoon, [(-8, -15), (-1, -15), (-1.5, 4), (-8, 4)], mem_l)
            for x0, x1 in ((-3.6, -2.4), (0, 0), (3.6, 2.4)):
                p.line((x0, -13), (x1, 0.5), bone if x0 <= 0 else dark(mem, 0.25))
            p.tri((-3.4, 4.6), (-5.6, 11.2), (-0.6, 6.8), fur)
            p.tri((3.4, 4.6), (5.6, 11.2), (0.6, 6.8), fur)
            p.tri((-3.2, 6), (-4.6, 9.6), (-1.6, 7), ear_in)
            p.tri((3.2, 6), (4.6, 9.6), (1.6, 7), ear_in)
            face = ellipse((0, 3.6), 4.2, 3.8)
            p.poly(face, fur)
            p.inside(face, ellipse((-1.4, 5.4), 2.6, 1.8), fur_l)
            awake = anim == "peek" and i == 1
            if anim == "peek":
                p.dot((-3, 3), fur_d, 2, 1)
                if awake:
                    _eye(p, 1, 3, KL, 2, 2)
                else:
                    p.dot((1, 4), KL, 2, 1)
            else:
                p.dot((-3, 3), fur_d, 2, 1)
                p.dot((1, 3), fur_d, 2, 1)
            p.dot((-1, 1), WHITE)
            p.dot((0, 1), WHITE)
        if anim == "hang" and i == 1:
            p.glow((6, -9), "#e8e0ff")
            p.glow((7, -10), "#e8e0ff")
        if anim == "peek" and i == 1:
            p.glow((5, 1), KL)
            p.glow((6, 0), KL)
        return

    dive = anim == "attack"
    ang = (12, 16, 10)[i] if dive else (-38, -8, 30, -8)[i]
    bob = 0 if dive else (-1, 0, 1, 0)[i]
    tilt = 32 if dive else 0
    with p.pose(rot=tilt, dy=bob):
        for s in (-1, 1):
            sh = (s * 3.0, -1.0)
            fold = 0.72 if dive else 1.0
            pts = [(3, -1), (7.6, -4.6), (14.2, -3.4), (12.2, -0.2), (11.8, 3.0), (9.4, 1.8), (7.8, 4.6), (5.6, 2.8), (3.6, 3.2)]
            pts = [(s * (3 + (x - 3) * fold), y * (0.85 if dive else 1)) for x, y in pts]
            with p.pose(rot=s * (ang if not dive else -ang - 20), pivot=sh):
                p.blob(pts, mem, 1)
                p.inside(pts, [(s * 2, -2), (s * 16, -6), (s * 16, -2.6), (s * 2, 1.6)], mem_l)
                wrist = pts[1]
                p.line(sh, wrist, bone)
                for tip in (pts[4], pts[6]):
                    p.line(wrist, (tip[0] - s * 1.2, tip[1] - 1.2), mem_d)
                p.dot((wrist[0] - 0.5 * s, wrist[1] - 1), K)
        legs(3.4, 1 if dive else 0)
        for s in (-1, 1):
            p.tri((s * 4.2, -2.8), (s * 6.4, -11.4), (s * 0.8, -4.6), fur)
            p.tri((s * 3.8, -4.0), (s * 5.4, -9.4), (s * 2.0, -4.8), ear_in)
        body = _ball(p, (0, 0.2), 4.9, 4.7, fur, fur_l, fur_d)
        p.inside(body, [(-2.4, 1.6), (0, 0.6), (2.4, 1.6), (1.6, 5), (-1.6, 5)], tuft)
        p.dot((-1, 2), light(tuft, 0.4))
        if dive:
            p.dot((-3, -2), KL, 2, 1)
            p.dot((1, -2), KL, 2, 1)
            p.dot((-1, 0), OUT, 2, 1)
            p.dot((-1, 1), K, 2, 1)
            p.dot((-1, 0), WHITE)
            p.dot((0, 0), WHITE)
        else:
            _eye(p, -3, -2, KL)
            _eye(p, 1, -2, KL)
            p.dot((-1, 0), WHITE)
            p.dot((0, 0), WHITE)
    if dive:
        for d in range(3):
            p.glow((-10 - d * 2 + (i % 2), -10 - d * 2 + i), "#e8e0ff", 2, 1)


@creature("Bronte", "raio", 2,
          move=dict(frames=4, fps=8, loop=True), windup=dict(frames=3, fps=8, loop=False),
          attack=dict(frames=3, fps=12, loop=False))
def bronte(p, anim, i, n, arm="hammer"):
    skin, skin_l, skin_d = "#7f97da", "#b2c4f2", "#536aa8"
    apron, apron_l = "#6e4c3c", "#956a52"
    iron, iron_l, iron_d = BRONZE, BRONZE_L, BRONZE_D
    wind, atk = anim == "windup", anim == "attack"
    bob = (0, 1, 0, 1)[i] if anim == "move" else 0
    charge = (0.35, 0.75, 1.0)[i] if wind else ((1.0, 0.5, 0.1)[i] if atk else 0.0)
    squash = (1.0, 1.0, 1.0)[i] if wind else ((0.86, 0.92, 1.0)[i] if atk else 1.0)
    swing = (-120, -100, -92)[i] if wind else ((40, 40, -30)[i] if atk else (-158, -154, -150, -154)[i])
    shoulder = (-0.5, -7.5 + bob)

    def hammer():
        with p.pose(rot=swing, pivot=shoulder):
            p.limb((shoulder[0] + 1, shoulder[1]), (shoulder[0] + 10.5, shoulder[1]), 0.85, WOOD)
            head = [(shoulder[0] + 8.4, shoulder[1] - 3.8), (shoulder[0] + 13.2, shoulder[1] - 3.8),
                    (shoulder[0] + 13.2, shoulder[1] + 3.8), (shoulder[0] + 8.4, shoulder[1] + 3.8)]
            p.blob(head, iron, 1)
            p.inside(head, [(shoulder[0] + 8, shoulder[1] - 4), (shoulder[0] + 14, shoulder[1] - 4),
                            (shoulder[0] + 14, shoulder[1] - 1.8), (shoulder[0] + 8, shoulder[1] - 1.8)], iron_l)
            p.inside(head, [(shoulder[0] + 10.2, shoulder[1] - 4), (shoulder[0] + 11.4, shoulder[1] - 4),
                            (shoulder[0] + 11.4, shoulder[1] + 4), (shoulder[0] + 10.2, shoulder[1] + 4)], iron_d)
            if wind or atk:
                p.oval((shoulder[0] + 2.6, shoulder[1]), 1.6, 1.6, skin)

    with p.pose(sy=squash, sx=2 - squash, pivot=(0, 0)):
        for k, fx in enumerate((-3.2, 3.0)):
            lift = 1.2 if anim == "move" and ((i == 0 and k == 0) or (i == 2 and k == 1)) else 0
            p.oval((fx, -1.3 - lift), 2.6, 1.5, skin_d)
        if arm == "hammer" and not (wind or atk):
            hammer()
        body = _ball(p, (0, -8 + bob), 6.6, 6.6, skin, skin_l, skin_d)
        p.inside(body, [(-7, -6 + bob), (7, -6 + bob), (7, 0), (-7, 0)], apron)
        p.inside(body, [(-7, -6 + bob), (7, -6 + bob), (7, -5 + bob), (-7, -5 + bob)], apron_l)
        p.dot((-2, -3 + bob), apron_l)
        p.dot((1, -4 + bob), GOLD)
        eye = ellipse((2.4, -9.6 + bob), 3.5, 3.6)
        p.poly(eye, WHITE)
        p.inside(eye, ellipse((3.4, -9.4 + bob), 2.1, 2.2), K if charge < 0.7 else KL)
        p.dot((3, -10 + bob), OUT, 2, 2)
        p.dot((2, -11 + bob), WHITE)
        if charge > 0.6:
            p.dot((0, -13 + bob), skin_d, 3, 1)
            p.dot((3, -12 + bob), skin_d, 2, 1)
        p.dot((1, -5 + bob), OUT, 3, 1)
        p.dot((2, -5 + bob), WHITE)
        cloud = mix("#f4f7ff", "#79829c", charge)
        cloud_d = mix("#c4cce0", "#4f566c", charge)
        cloud_l = mix("#ffffff", "#a8b0c6", charge)
        puffs = ((-5.8, -13.8, 2.2), (-3.2, -16.0, 2.8), (0.6, -16.8, 3.0), (4.2, -15.8, 2.6), (6.2, -13.6, 1.8),
                 (-1.6, -14.4, 2.3), (2.4, -14.6, 2.2))
        for cx, cy, r in puffs:
            p.oval((cx, cy + bob + 0.7), r, r * 0.8, cloud_d)
        for cx, cy, r in puffs:
            p.oval((cx, cy + bob), r * 0.95, r * 0.74, cloud)
        for cx, cy, r in puffs[1:4]:
            p.oval((cx - r * 0.25, cy - r * 0.3 + bob), r * 0.5, r * 0.32, cloud_l)
        if arm == "hammer" and (wind or atk):
            hammer()
        elif arm == "bomb":
            from bestiary_v3 import bomber_arm
            bomber_arm(p, anim, i, shoulder, skin, skin_d)
    if charge > 0.6:
        for s in range(3 + i):
            a = s * 2.1 + i * 1.7
            p.glow((0.5 + 7.6 * math.cos(a), -15 + 4.2 * math.sin(a)), WHITE if s % 2 else "#d8e6ff")
    if atk and i < 2 and arm == "hammer":
        for dx in (-3, -2, 2, 3):
            p.glow((11 + dx, -1), WHITE)
        p.glow((11, -2), WHITE, 1, 2)
        if i == 0:
            for dx, dy in ((-4, -3), (4, -3), (-2, -5), (2, -5)):
                p.glow((11 + dx, dy), "#d8e6ff")


@creature("Miasma Toad", "veneno", 2, size=(40, 32), origin=(20, 31),
          idle=dict(frames=2, fps=3, loop=True),
          move=dict(frames=6, fps=10, loop=False, path=[(0, 0), (1, -3), (4, -9), (8, -11), (12, -5), (14, 0)]),
          windup=dict(frames=3, fps=7, loop=False), attack=dict(frames=2, fps=10, loop=False))
def miasma_toad(p, anim, i, n):
    g, g_l, d, belly = "#5fcf7c", "#9cf0a8", "#2f7f52", "#d8f7b0"
    eye_w, pupil = "#fffbe6", "#101428"
    p.outline = "#163c2c"
    SIT = ((0, -5.6), -12, 1.0, (-5, -4.6), (1.6, -2.4), (-6, -0.8), (1, -0.6), (5.4, -4.4), (6.6, -0.4))
    HOP = [
        ((0, -5.0), -8, 0.86, (-5, -4.0), (2.0, -2.2), (-6.4, -0.8), (1, -0.6), (5.2, -3.8), (6.6, -0.4)),
        ((1, -8.4), -34, 1.0, (-4, -5.4), (-7.4, -2.6), (-9.6, -0.6), (-13.6, -0.4), (5.6, -9.4), (9.4, -10.4)),
        ((2, -9.4), -24, 1.04, (-4, -7.4), (-10, -4.8), (-15, -2.8), (-19, -2.0), (6.4, -9.6), (11.2, -11.4)),
        ((2, -9.4), -2, 1.0, (-5, -8.4), (-11, -7.6), (-16, -7.2), (-19.4, -6.4), (7.4, -7.6), (12.4, -6.6)),
        ((2, -8.6), 18, 1.0, (-5, -9.6), (-1.4, -12.0), (-8, -11.6), (-11.6, -12.6), (7.6, -6.4), (10.4, -1.4)),
        ((0, -4.6), 0, 0.84, (-5, -4.0), (1.6, -2.0), (-6.6, -0.6), (0.6, -0.4), (6.2, -4.0), (8.2, -0.4)),
    ]
    wind, atk = anim == "windup", anim == "attack"
    if anim == "move":
        pose = HOP[i]
    elif anim == "idle":
        pose = SIT if i == 0 else (SIT[0], SIT[1], 0.96) + SIT[3:]
    elif wind:
        lean = (-16, -19, -22)[i]
        pose = ((SIT[0][0] - 0.6, SIT[0][1]), lean) + SIT[2:]
    else:
        pose = ((1.2, -5.8), -4) + SIT[2:]
    c, rot, sq, hip, knee, ankle, toe, shoulder, hand = pose

    def leg(color, dark, dx=0.0, dy=0.0):
        o = (dx, dy)
        hp, kn, an, tp = [(q[0] + o[0], q[1] + o[1]) for q in (hip, knee, ankle, toe)]
        p.limb(an, tp, 0.8, dark)
        p.limb(kn, an, 1.9, dark, 1.6)
        p.limb(hp, kn, 3.3, dark, 2.5)
        p.limb(kn, an, 1.2, color, 0.9)
        p.limb(hp, kn, 2.6, color, 1.8)
        p.dot((tp[0], tp[1] - 1), dark)
        p.dot((tp[0] + 1, tp[1]), dark)

    leg(d, d, 1.2, -0.6)
    p.limb((shoulder[0] - 1.6, shoulder[1]), (hand[0] - 1.6, hand[1]), 1.0, d)
    with p.pose(rot=rot, pivot=c, sy=sq):
        body = ellipse(c, 8.8, 5.4)
        p.poly(body, g)
        p.inside(body, ellipse((c[0] + 2.4, c[1] + 3.2), 6.4, 2.6), belly)
        p.inside(body, ellipse((c[0] - 2.4, c[1] - 3.6), 4.6, 1.4), g_l)
        p.inside(body, ellipse((c[0] - 6.0, c[1] + 2.6), 4.0, 2.4), d)
        if wind:
            r = (2.2, 3.0, 3.6)[i]
            p.oval((c[0] + 6.4, c[1] + 2.6), r, r * 0.7, mix(belly, KL, (0.4, 0.75, 1.0)[i]))
        for ex, ey, r in ((c[0] + 1.6, c[1] - 5.0, 2.2), (c[0] + 4.8, c[1] - 4.6, 2.8)):
            p.oval((ex, ey), r, r, g)
        big = 0.5 if wind or atk else 0.0
        p.oval((c[0] + 1.6, c[1] - 5.4), 1.3, 1.3, eye_w)
        p.dot((c[0] + 2, c[1] - 6), pupil)
        p.oval((c[0] + 4.9, c[1] - 5.2 - big), 1.9 + big, 1.9 + big, eye_w)
        p.dot((c[0] + 5.0, c[1] - 6.0 - big), pupil, 2, 2)
        p.dot((c[0] + 5.0, c[1] - 6.0 - big), eye_w)
        if atk:
            p.oval((c[0] + 7.2, c[1] + 0.8), 2.2, 1.6 if i == 0 else 1.2, K)
            p.dot((c[0] + 7, c[1] + 1), KD, 2, 1)
        else:
            p.line((c[0] + 3.0, c[1] + 0.4), (c[0] + 8.6, c[1] - 0.2), d)
        p.dot((c[0] + 5, c[1] - 1.6), "#ff9ac8", 2, 1)
        for wx, wy in ((-3.6, -2.6), (-6.4, 0.0), (-0.4, -4.0)):
            p.dot((c[0] + wx, c[1] + wy), K, 2, 2)
            p.dot((c[0] + wx, c[1] + wy), KL)
    leg(g, d)
    p.inside(ellipse(hip, 2.6, 2.6), ellipse((hip[0] - 0.6, hip[1] - 1.2), 1.6, 0.9), g_l)
    p.limb(shoulder, hand, 1.6, d, 1.4)
    p.limb(shoulder, hand, 1.0, g, 0.8)
    p.dot((hand[0] - 1, hand[1]), d, 3, 1)
    if anim == "move" and i == 0:
        for dx in (-9, -7, 7):
            p.glow((dx, -1), "#e6eeff")
    if anim == "move" and i == 5:
        for dx in (-12, -10, 10, 12):
            p.glow((dx, -1 - (abs(dx) == 12)), "#e6eeff")


@creature("Karkinos", "carapaça", 2, size=(40, 32), origin=(20, 31),
          move=dict(frames=4, fps=10, loop=True), windup=dict(frames=2, fps=6, loop=False),
          attack=dict(frames=3, fps=12, loop=False), guard=dict(frames=2, fps=3, loop=True))
def karkinos(p, anim, i, n):
    shell, shell_l, shell_d, shell_dd = "#5aa6ec", "#a6d6ff", "#3a78c8", "#285a9e"
    belly = "#d6ecff"
    guard, wind, atk = anim == "guard", anim == "windup", anim == "attack"
    drop = 2.0 if guard else 0.0
    bob = (0, -1, 0, -1)[i] if anim == "move" else 0
    lean = (-1, 0, 1, 0)[i] if anim == "move" else 0
    if wind:
        lean = -1
    elif atk:
        lean = (2, 2, 1)[i]
    y0 = bob + drop
    for s in (-1, 1):
        for k in range(3):
            up = 1 if anim == "move" and (i + k + (s > 0)) % 2 == 0 else 0
            x = s * (4.6 + k * 2.2) + lean
            p.limb((x, -3.4 + y0 * 0.5), (x + s * 1.4, -0.8 - up), 0.9, shell_dd)
    if guard:
        pose = {-1: (0.0, 0.0, 0.0), 1: (0.0, 0.0, 0.0)}
    elif wind:
        pose = {-1: ((1.0, 1.8)[i], (3.0, 5.0)[i], 0.0), 1: ((1.0, 1.8)[i], (3.0, 5.0)[i], 0.0)}
    elif atk:
        pose = {-1: (0.0, -1.0, -2.0), 1: ((1.8, 0.0, 0.4)[i], (-1.0, -1.4, 0.0)[i], (1.6, 2.2, 0.6)[i])}
    else:
        bounce = (0.0, 0.6, 0.0, 0.6)[i] if anim == "move" else 0.0
        pose = {-1: (0.5, bounce, 0.0), 1: (0.5, bounce, 0.0)}

    def claw(s):
        claw_open, claw_up, reach = pose[s]
        arm0 = (s * 7.4 + lean, -6.8 + y0)
        c = (s * (11.4 + reach) + lean, -10.6 - claw_up + y0)
        p.limb(arm0, (c[0] - s * 1.6, c[1] + 1.6), 1.1, shell_d)
        mitt = ellipse((c[0], c[1]), 3.2, 3.0)
        p.poly(mitt, K)
        p.inside(mitt, ellipse((c[0] - s * 0.8, c[1] - 1.4), 1.8, 1.1), KL)
        p.inside(mitt, ellipse((c[0] + s * 0.6, c[1] + 1.8), 2.6, 1.0), KD)
        p.oval((c[0] + s * 1.4, c[1] - 2.6 - claw_open), 1.6, 1.4, K)
        p.dot((c[0] + s * 1.2, c[1] - 1 - claw_open * 0.5), KD, 1, 1 + int(claw_open))

    if not guard:
        claw(-1)
        claw(1)
    eye_y = -16.4 + y0 + (0.5 if anim == "move" and i % 2 else 0)
    if not guard:
        for s in (-1, 1):
            p.limb((s * 2.6 + lean, -11.4 + y0), (s * 3.2 + lean, eye_y + 1.6), 0.8, shell_d)
    body = ellipse((lean, -7.2 + y0), 8.8, 6.0)
    p.poly(body, shell)
    p.inside(body, ellipse((lean, -2.6 + y0), 7.8, 2.4), belly)
    p.inside(body, ellipse((lean - 3.0, -10.6 + y0), 4.0, 1.6), shell_l)
    p.inside(body, ellipse((lean + 5.2, -5.6 + y0), 3.0, 1.6), shell_d)
    p.inside(body, ellipse((lean, -1.4 + y0), 8.8, 1.0), shell_d)
    sx, sy = int(lean), -12 + int(y0)
    for dx, dy, col in ((0, -1, "#ffe9a0"), (-1, 0, "#f2c14e"), (0, 0, "#fff6c8"), (1, 0, "#f2c14e"), (0, 1, "#b7802e")):
        p.dot((sx + dx, sy + dy), col)
    if guard:
        for s in (-1, 1):
            ex = s * 3 + lean
            p.dot((ex - (1 if s < 0 else 0), -9 + drop), OUT)
            p.dot((ex + (1 if s < 0 else -1), -8 + drop), OUT)
            p.dot((ex - (1 if s < 0 else 0), -7 + drop), OUT)
        for s in (-1, 1):
            c = (s * 3.6, -4.4 + drop + (i == 1) * 0.4)
            mitt = ellipse(c, 3.6, 2.6)
            p.poly(mitt, K)
            p.inside(mitt, ellipse((c[0] - s * 0.8, c[1] - 1), 2.0, 1.0), KL)
            p.inside(mitt, ellipse((c[0], c[1] + 1.6), 3.4, 1.0), KD)
    else:
        look = 1 if (wind or atk) else 0
        for s in (-1, 1):
            ex = s * 3.4 + lean
            p.oval((ex, eye_y), 2.5, 2.5, WHITE)
            px_ = int(ex) - (1 if s < 0 else 0) + look
            p.dot((px_, int(eye_y) - (1 if wind else 0)), OUT, 2, 2)
            p.dot((px_, int(eye_y) - (1 if wind else 0)), WHITE)
        p.dot((-5 + lean, -7 + y0), "#ff9ac8", 2, 1)
        p.dot((4 + lean, -7 + y0), "#ff9ac8", 2, 1)
        if atk:
            p.dot((-1 + lean, -7 + y0), OUT, 2, 2)
        else:
            p.dot((-1 + lean, -7 + y0), OUT)
            p.dot((0 + lean, -6 + y0), OUT)
            p.dot((1 + lean, -7 + y0), OUT)
    if atk and i == 1:
        for dx, dy in ((0, -2), (2, 0), (0, 2), (1, -1), (1, 1)):
            p.glow((15 + dx, -11 + dy), WHITE if dx == 0 else KL)
    if atk and i < 2:
        for k, y in enumerate((-12, -8, -4)):
            p.glow((-14 - (k + i) % 2 * 2, y), "#e6eeff", 2, 1)


@creature("Arges Eye", "míssil teleguiado", 3, origin=(16, 15),
          move=dict(frames=4, fps=12, loop=True), windup=dict(frames=3, fps=8, loop=False),
          attack=dict(frames=3, fps=12, loop=False))
def arges_eye(p, anim, i, n):
    metal, metal_l, metal_d = "#4c64a0", "#96b0ea", "#2c3a66"
    glass, vein = "#d8e8ff", "#93ace6"
    wind, atk = anim == "windup", anim == "attack"
    flap = (0, 1, 2, 1)[i % 4] if anim == "move" else (i % 2) * 2
    aim = (0.35, 0.7, 1.0)[i] if wind else ((0.2, 0.0, 0.0)[i] if atk else 0.0)
    recoil = (-3, -1, 0)[i] if atk else 0
    bob = wave(i, n, 0.8) if anim == "move" else 0.0
    shot = atk and i == 0
    with p.pose(dx=recoil, dy=bob):
        tip = (-9, -4, 1)[flap]
        for side in (-1, 1):
            for k, (dy, ln) in enumerate(((0, 14.4), (3.2, 11.6))):
                t = tip + k * 3
                wing = [(side * 4, -4 + dy), (side * (ln - 3), t - 2.8), (side * ln, t), (side * (ln - 3), t + 2.6), (side * 5, dy)]
                p.blob(wing, glass if k == 0 else mix(glass, vein, 0.35), 1)
                p.line((side * 5, -2 + dy), (side * (ln - 1), t), vein)
        p.blob([(-2.8, 5.6), (3.6, 5.6), (5.8, 10.4), (1.6, 11.6), (-2.2, 10)], metal_d, 1)
        p.dot((3, 9), OUT, 2, 2)
        if aim > 0.6:
            p.dot((3, 9), K, 2, 2)
        ball = _ball(p, (0, 0), 7.6, 7.6, metal, metal_l, metal_d)
        rimc = ellipse((2.0, 0), 5.6, 5.6)
        p.poly(rimc, BRONZE)
        p.inside(rimc, ellipse((0.6, -2.6), 4.4, 2.6), BRONZE_L)
        p.inside(rimc, ellipse((3.6, 3.6), 4.4, 2.4), BRONZE_D)
        eye = ellipse((2.0, 0), 4.4, 4.4)
        p.poly(eye, WHITE)
        p.inside(eye, ellipse((3.4, 0.4), 2.8, 2.8), KL if shot else K)
        p.inside(eye, ellipse((3.8, 0.4), 1.3, 1.4), WHITE if shot else OUT)
        lid = 3.6 * aim
        if lid > 0:
            p.inside(eye, [(-4, -6), (8, -6), (8, -4.4 + lid), (-4, -4.4 + lid)], metal)
            p.inside(eye, [(-4, 6), (8, 6), (8, 4.4 - lid), (-4, 4.4 - lid)], metal)
            p.inside(eye, [(-4, -4.6 + lid), (8, -4.6 + lid), (8, -3.8 + lid), (-4, -3.8 + lid)], metal_d)
        if not shot:
            p.dot((1, -2), WHITE)
        for rx, ry in ((-6, -1), (-5, 3), (-2, 6), (-4, -5)):
            p.dot((rx, ry), metal_l)
        p.line((-1, -7), (-3, -11), metal_d)
        p.dot((-4, -13), KL if aim > 0.5 else K, 2, 2)
        if aim > 0.5:
            p.dot((-4, -13), WHITE)
    if aim > 0.5:
        p.glow((-6, -14), KL)
        p.glow((-1, -14), KL)
    if shot:
        for d in range(4):
            p.glow((5 + d * 2, 11 + d), WHITE if d < 2 else KL, 2, 1)


@creature("Erote Archer", "flechas", 3, origin=(16, 17),
          move=dict(frames=4, fps=10, loop=True), windup=dict(frames=4, fps=7, loop=False),
          attack=dict(frames=2, fps=10, loop=False))
def erote_archer(p, anim, i, n):
    marble, marble_l, marble_d = "#f1edf6", "#ffffff", "#b9b4cf"
    curl, curl_l, curl_d = "#f2c14e", "#ffe9a0", "#c08a32"
    wing_c, wing_d = "#ffffff", "#c6d4ef"
    wind, atk = anim == "windup", anim == "attack"
    flap = (0, 1, 2, 1)[i % 4] if anim == "move" else (1 if wind else 0)
    bob = wave(i, n, 0.8) if anim == "move" else 0.0
    pull = (1, 2, 3, 3)[i] if wind else ((-1, 0)[i] if atk else 0)
    awake = wind or atk
    with p.pose(dy=bob):
        wy = (-5, -1, 3)[flap]
        for k, (dx, c) in enumerate(((1.6, wing_d), (0, wing_c))):
            pts = [(-2 + dx, -3), (-7 + dx, -6 + wy), (-11.6 + dx, -3 + wy), (-11 + dx, 0 + wy * 0.6),
                   (-8.6 + dx, 1.2 + wy * 0.4), (-7.4 + dx, 3 + wy * 0.3), (-4 + dx, 2.4), (-2 + dx, 1)]
            p.blob(pts, c, 1)
            if k == 1:
                p.line((-4, -1 + wy * 0.3), (-10, -2 + wy * 0.8), wing_d)
                p.line((-4, 1 + wy * 0.2), (-8, 1 + wy * 0.5), wing_d)
        p.blob([(-4, -2), (-2, -3), (-1.4, 4), (-3.4, 4.4)], curl_d, 1)
        p.dot((-4, -3), KL)
        p.limb((-1, 6.4), (-2.4, 10), 1.3, marble_d)
        p.limb((1.2, 6.4), (1.0, 10.6), 1.3, marble)
        torso = _ball(p, (0, 3.4), 3.6, 3.8, marble, marble_l, marble_d)
        p.inside(torso, [(-4, 0.4), (4, 5.6), (4, 7), (-4, 1.8)], curl)
        head = _ball(p, (0.6, -4.6), 4.9, 4.6, marble, marble_l, marble_d, lx=0.3, ly=-0.1, dx=-0.6, dy=0.3)
        for cx, cy, r in ((-3.4, -7.8, 2.0), (-0.4, -9.4, 2.1), (2.8, -8.8, 1.9), (-4.6, -4.8, 1.8), (4.8, -7.0, 1.4)):
            p.oval((cx, cy), r, r, curl)
            p.oval((cx - r * 0.3, cy - r * 0.35), r * 0.45, r * 0.4, curl_l)
            p.dot((cx + r * 0.3, cy + r * 0.4), curl_d)
        if awake:
            p.dot((2, -5), KL, 1, 2)
            p.dot((4, -5), KL, 1, 2)
            if pull >= 3:
                p.dot((2, -5), WHITE)
                p.dot((4, -5), WHITE)
        else:
            p.dot((2, -4), marble_d, 1, 1)
            p.dot((4, -4), marble_d, 1, 1)
            p.dot((1, -5), marble_d)
            p.dot((5, -5), marble_d)
        p.dot((5, -3), "#f4c6d8")
        p.dot((3, -2), marble_d, 1, 1)
        if pull == 0:
            p.limb((1, 1.6), (6, 4.2), 1.1, marble)
            for a, b in (((6, -1), (8, 2)), ((8, 2), (8, 5)), ((8, 5), (6, 8))):
                p.line(a, b, GOLD)
            p.line((6, -1), (6, 8), marble_d)
        else:
            hx = 7.0 - max(pull, 0) * 2.2 if pull > 0 else 5.0
            p.limb((0.5, 0), (9.2, -1), 1.1, marble)
            p.limb((-0.5, 0.5), (hx, -1), 1.1, marble_d)
            for a, b in (((8, -7), (10, -4)), ((10, -4), (11, -1)), ((11, -1), (10, 2)), ((10, 2), (8, 5))):
                p.line(a, b, GOLD)
            p.dot((11, -1), GOLD_L)
            if pull > 0:
                p.line((8, -7), (hx, -1), marble_d)
                p.line((hx, -1), (8, 5), marble_d)
                p.line((hx, -1), (13, -1), "#f4ead0")
                p.dot((13, -2), K, 2, 3)
                p.dot((15, -1), KL if pull < 3 else WHITE)
            else:
                p.line((8, -7), (8, 5), marble_d)
    if pull >= 3:
        p.glow((16, -3), WHITE)
        p.glow((16, 1), WHITE)
        p.glow((17, -1), KL)
    if atk and i == 0:
        for d in range(3):
            p.glow((12 + d * 2, -1), WHITE if d else KL)


@creature("Minotaur Calf", "labirinto", 3, size=(40, 32), origin=(18, 31),
          move=dict(frames=4, fps=7, loop=True), windup=dict(frames=3, fps=6, loop=False),
          attack=dict(frames=2, fps=12, loop=True), stun=dict(frames=2, fps=4, loop=True))
def minotaur_calf(p, anim, i, n):
    hide, hide_l, hide_d = "#eee3cc", "#fffaf0", "#b9ab95"
    patch, patch_d = "#7a5a4a", "#5a4034"
    muzzle, muzzle_d = "#e0b3a8", "#b98478"
    horn, horn_d = "#fbf5e2", "#cbbf9f"
    cloth, cloth_d = "#2f8f8a", "#1f625f"
    wind, atk, stun = anim == "windup", anim == "attack", anim == "stun"
    lean = (4, 8, 12)[i] if wind else (22 if atk else (-10 if stun else (0, 2, 0, 2)[i]))
    bob = (0, 1, 0, 1)[i] if anim == "move" else (i if atk else 0)
    for k, fx in enumerate((-6, 2)):
        lift = (1.3 if (i == 0 and k == 0) or (i == 2 and k == 1) else 0) if anim == "move" else 0
        shift = 0
        if wind and k == 1:
            shift = (0, -3, 2)[i]
        if atk:
            shift = ((-4, 4), (4, -4))[i][k]
        p.limb((fx + 1, -6), (fx + shift, -2.4 - lift), 2.5, hide_d if k == 0 else hide, 2.1)
        p.dot((fx + shift - 2, -1 - lift), OUT, 5, 1)
        p.dot((fx + shift - 2, -2 - lift), patch_d, 4, 1)
    if wind and i >= 1:
        for d in range(2 + i):
            p.glow((-2 - d * 2, -1 - d % 2), "#e6dcf6")
    with p.pose(rot=lean, pivot=(-2, -5), dy=bob):
        p.limb((-9, -8), (-12, -10 + (i % 2)), 0.6, hide_d)
        p.oval((-12.5, -10.5 + (i % 2)), 1.3, 1.3, patch)
        body = _ball(p, (-3, -9), 7.0, 6.2, hide, hide_l, hide_d)
        p.inside(body, ellipse((-6.8, -11.6), 3.4, 2.8), patch)
        p.inside(body, ellipse((-0.4, -6.4), 1.8, 1.4), patch)
        loin = [(-10, -5.8), (3.4, -5.8), (2.6, -2.2), (-9.4, -2.2)]
        p.blob(loin, cloth, 1)
        p.inside(loin, [(-11, -3.6), (4, -3.6), (4, -1), (-11, -1)], cloth_d)
        p.dot((-3, -5), GOLD)
        p.limb((-0.6, -9.6), (1.8, -4.4), 2.1, hide_d, 1.8)
        for side, (a, b, c) in ((0, ((2.6, -18), (3.4, -22.4), (6.6, -24))),
                                (1, ((5.6, -18.6), (7.6, -22.8), (11.8, -23.4)))):
            p.band([a, b, c], 1.6 if side else 1.3, 0.5, horn if side else horn_d)
        p.dot((12, -24), K)
        p.dot((7, -25), K)
        p.tri((-0.6, -16), (-4.8, -18.6), (-1.4, -13.4), hide_d)
        head = _ball(p, (4.6, -14.2), 6.2, 5.4, hide, hide_l, hide_d)
        p.inside(head, ellipse((1.2, -18.2), 3.6, 2.6), patch)
        p.oval((3.6, -19.2), 2.0, 1.2, patch_d)
        mz = ellipse((8.8, -11.4), 3.8, 3.0)
        p.poly(mz, muzzle)
        p.inside(mz, ellipse((9.2, -9.6), 3.8, 1.2), muzzle_d)
        p.dot((9, -12), OUT)
        p.dot((11, -12), OUT)
        p.dot((9, -10), GOLD, 3, 1)
        p.dot((10, -9), GOLD_L)
        if stun:
            for dx, dy in ((0, 0), (2, 0), (1, 1), (0, 2), (2, 2)):
                p.dot((5 + dx, -17 + dy), OUT)
        else:
            p.dot((6, -16), OUT, 2, 2)
            p.dot((6, -16), WHITE)
            p.dot((5, -17), patch_d, 4, 1)
            if wind or atk:
                p.dot((7, -15), KL)
        if wind:
            for d in range(1 + i):
                p.glow((13 + d * 1.5, -10 + d), WHITE, 2, 1)
    if stun:
        for s in range(3):
            a = TAU * s / 3 + i * 1.0
            p.glow((1 + 8 * math.cos(a), -25 + 2.5 * math.sin(a)), GOLD, 2, 1)
            p.glow((1.5 + 8 * math.cos(a), -25.6 + 2.5 * math.sin(a)), GOLD, 1, 3)
    if atk:
        for d, y in enumerate((-19, -13, -7)):
            p.glow((-15 - (d + i) % 2 * 2, y), WHITE, 3, 1)
        for d in range(3):
            p.glow((-10 - d * 2, -1 - (d + i) % 2), "#e6dcf6")


@creature("Spartoi", "ossos", 2,
          rise=dict(frames=5, fps=8, loop=False), move=dict(frames=4, fps=8, loop=True),
          windup=dict(frames=3, fps=7, loop=False), attack=dict(frames=3, fps=12, loop=False))
def spartoi(p, anim, i, n):
    bone, bone_l, bone_d = "#efe6cf", "#fffaf0", "#b8ac92"
    crest, crest_l = "#3b5ba0", "#6f92d6"
    soil, soil_l = "#5a4334", "#7d604a"
    wind, atk, rise = anim == "windup", anim == "attack", anim == "rise"
    sink = (17, 13, 8, 4, 0)[i] if rise else 0
    bob = (0, 1, 0, 1)[i] if anim == "move" else 0
    spear_back = (2, 4, 6)[i] if wind else 0
    thrown = atk
    with p.pose(dy=sink + bob):
        for k, fx in enumerate((-1.8, 1.8)):
            lift = 1.2 if anim == "move" and ((i == 0 and k == 0) or (i == 2 and k == 1)) else 0
            p.line((fx * 0.6, -7), (fx, -3.6 - lift), bone)
            p.line((fx, -3.6 - lift), (fx, -1 - lift), bone)
            p.dot((fx - (0 if k else 1), -1 - lift), bone_d, 2, 1)
        p.oval((0, -7.4), 2.0, 1.0, bone_d)
        p.line((0, -8), (0, -11), bone_d)
        rib = ellipse((0, -11.6), 3.0, 2.6)
        p.poly(rib, bone)
        p.inside(rib, ellipse((1.2, -10), 2.6, 1.6), bone_d)
        for y in (-12, -10):
            p.dot((-2, y), OUT, 4, 1)
        shield = ellipse((-5.0, -10.2), 2.6, 3.8)
        p.poly(shield, BRONZE)
        p.inside(shield, ellipse((-5.6, -12.2), 1.8, 1.6), BRONZE_L)
        p.inside(shield, ellipse((-4.2, -7.8), 2.0, 1.4), BRONZE_D)
        p.dot((-6, -11), crest, 1, 2)
        hand = (3.6 - spear_back, -11.6 - (1 if wind else 0))
        p.line((1.6, -13.4), hand, bone)
        if not thrown or i == 2:
            back = spear_back if not thrown else 0
            p.line((hand[0] - 7, hand[1] + (1 if not wind else 0)), (hand[0] + 6, hand[1] - (0 if not wind else 0.5)), WOOD)
            tip = (hand[0] + 6, hand[1] - (0 if not wind else 0.5))
            p.dot((tip[0] + 1, tip[1] - 1), K, 2, 3)
            p.dot((tip[0] + 3, tip[1]), K)
            p.dot((tip[0] + 1, tip[1]), KL)
            if back:
                pass
        skull = _ball(p, (0.8, -17.6), 4.6, 4.2, bone, bone_l, bone_d)
        helm = [(-3.8, -18.6), (-3.6, -22.0), (0.8, -23.4), (5.2, -22.0), (5.6, -18.8), (4.8, -18.4),
                (4.4, -20.0), (-1.0, -20.0), (-1.2, -16.0), (-3.4, -15.4)]
        p.blob(helm, BRONZE, 1)
        p.inside(helm, ellipse((0, -22.6), 3.6, 1.2), BRONZE_L)
        p.inside(helm, [(-5, -17), (-1, -17), (-1, -15), (-5, -15)], BRONZE_D)
        crest_pts = [(-4.6, -21.0), (-3.0, -25.6), (1.6, -27.0), (5.6, -25.0), (4.0, -23.0), (0.6, -23.6), (-2.4, -21.8)]
        p.blob(crest_pts, crest, 1)
        p.inside(crest_pts, ellipse((0, -26.4), 3.2, 1.0), crest_l)
        p.dot((2, -18), OUT, 2, 2)
        p.dot((3, -18), KL if wind else K)
        p.dot((2, -15), OUT, 3, 1)
        p.dot((3, -15), bone)
    if rise:
        for dx in range(-6, 7):
            h = 1 + (abs(dx) < 4) + (abs(dx) < 2)
            if i < 4 or abs(dx) > 3:
                p.glow((dx, -h), soil if (dx + i) % 3 else soil_l, 1, h)
        if 1 <= i <= 3:
            for k in range(3):
                p.glow((-5 + k * 5 + (i % 2), -4 - i - k % 2), soil_l)
    if wind and i == 2:
        p.glow((-6, -14), KL)
    if atk and i == 0:
        for d in range(3):
            p.glow((10 + d * 2, -12 + (d % 2)), WHITE if d < 2 else KL)


@creature("Balanos", "carvalho", 1, move=dict(frames=4, fps=8, loop=True))
def balanos(p, anim, i, n):
    nut, nut_l, nut_d = "#c98a4b", "#ecbd7c", "#8f5a33"
    cap, cap_l, cap_d = "#6e4b30", "#9a7048", "#46301f"
    leaf, leaf_l, leaf_d = "#5fcf7c", "#9cf0a8", "#2f7f52"
    bob = (0, -1, 0, -1)[i]
    tilt = (-4, 0, 4, 0)[i]
    for k, fx in enumerate((-2.6, 2.2)):
        step = ((1.2, 0, -1.2, 0), (-1.2, 0, 1.2, 0))[k][i]
        lift = 1 if (i + k) % 2 == 1 else 0
        p.dot((fx + step - 1, -1 - lift), cap_d, 3, 1 + lift)
    with p.pose(rot=tilt, pivot=(0, -2 + bob)):
        c = (0, -7 + bob)
        body = _ball(p, c, 5.8, 5.6, nut, nut_l, nut_d)
        p.inside(body, ellipse((c[0] - 0.4, c[1] + 5.4), 2.2, 1.4), nut_d)
        hat = ellipse((0, -11.4 + bob), 6.9, 3.5)
        p.poly(hat, cap)
        p.inside(hat, ellipse((-2.4, -13.0 + bob), 3.6, 1.4), cap_l)
        p.inside(hat, ellipse((1.6, -9.4 + bob), 6.0, 1.2), cap_d)
        for dx, dy in ((-4, -12), (-1, -13), (2, -12), (4, -11), (-3, -10), (0, -11), (3, -10)):
            p.dot((dx, dy + bob), cap_d)
        p.limb((0.4, -14.4 + bob), (0.8, -16.6 + bob), 0.6, WOOD_D)
        flap = (0, 0.6, 0, -0.6)[i]
        lf = ellipse((3.0, -16.6 + bob + flap), 2.4, 1.2)
        p.poly(lf, leaf)
        p.inside(lf, ellipse((2.6, -17.2 + bob + flap), 1.4, 0.5), leaf_l)
        p.dot((4, -16 + bob + flap), leaf_d)
        fx = 1.2
        for ex in (-2.4, 1.8):
            p.dot((fx + ex, -8 + bob), WHITE, 2, 3)
            p.dot((fx + ex + 1, -7 + bob), OUT, 1, 2)
        p.line((fx - 4.0, -9.6 + bob), (fx - 1.2, -8.6 + bob), cap_d)
        p.line((fx + 4.2, -9.6 + bob), (fx + 1.6, -8.6 + bob), cap_d)
        p.dot((fx - 1.4, -4 + bob), nut_d, 4, 1)
        p.dot((fx - 1, -3 + bob), K)
        p.dot((fx + 1, -3 + bob), K)
        p.dot((fx - 3.6, -5 + bob), "#ff9ac8", 1, 1)
