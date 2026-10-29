from __future__ import annotations

import math

from vec import ellipse, mix

from bestiary_kit import HOT, K, KD, KL, OUT, WHITE, creature
import bestiary_v2
from bestiary_v2 import WOOD_D

BOMB, BOMB_L, BOMB_D = "#2a3157", "#56649c", "#171b36"


def thunder_bomb(p, c, r=3.0, spark=0):
    x, y = c
    ball = ellipse(c, r, r)
    p.poly(ball, BOMB)
    p.inside(ball, ellipse((x + r * 0.3, y + r * 0.55), r * 0.95, r * 0.5), BOMB_D)
    p.inside(ball, ellipse((x - r * 0.35, y - r * 0.4), r * 0.5, r * 0.38), BOMB_L)
    p.dot((x - 1, y - 1), WHITE)
    p.dot((x, y), WHITE)
    p.dot((x - 1, y + 1), "#d8e6ff")
    tip = (x + r * 0.8, y - r * 1.25)
    p.line((x + r * 0.35, y - r * 0.8), tip, WOOD_D)
    p.glow((tip[0] + 0.6, tip[1] - 0.6), WHITE)
    for k, (dx, dy) in enumerate(((1, -1), (-1, -1), (1, 0), (0, -2))[: 2 + spark]):
        p.glow((tip[0] + 0.6 + dx, tip[1] - 0.6 + dy), K if k % 2 else KL)


def bomber_arm(p, anim, i, shoulder, skin, skin_d):
    sx, sy = shoulder[0] + 1.0, shoulder[1] + 0.5
    if anim == "windup":
        hand, bomb = (((1.0, -15.0), (1.5, -17.0)), ((-0.5, -19.5), (-0.5, -22.0)), ((-4.5, -18.5), (-5.5, -21.0)))[i]
    elif anim == "attack":
        hand, bomb = (((7.5, -12.0), (10.0, -13.5)), ((8.0, -8.5), None), ((5.0, -6.5), None))[i]
    else:
        hand, bomb = (2.0, sy + 4.0), None
    p.limb((sx, sy), hand, 1.0, skin)
    p.oval(hand, 1.5, 1.4, skin)
    p.dot((round(hand[0]), round(hand[1]) + 1), skin_d)
    if bomb:
        thunder_bomb(p, bomb, 2.8, i % 2)


def _orb(p, x, y, r, charge):
    for dx in range(-r, r + 1):
        for dy in range(-r, r + 1):
            if abs(dx) + abs(dy) <= r + (1 if r > 1 else 0):
                p.glow((x + dx, y + dy), K if abs(dx) + abs(dy) >= r else KL)
    p.glow((x, y), WHITE if charge > 0.6 else HOT)


@creature("Nephele", "nuvem", 2, size=(40, 32), origin=(20, 14),
          move=dict(frames=4, fps=6, loop=True), windup=dict(frames=3, fps=6, loop=False),
          attack=dict(frames=2, fps=8, loop=False))
def nephele(p, anim, i, n):
    wind, atk = anim == "windup", anim == "attack"
    charge = (0.35, 0.7, 1.0)[i] if wind else (0.6 if atk else 0.0)
    puff = (0.0, 0.5, 0.0, -0.5)[i] if anim == "move" else 0.0
    base = mix("#eef2f8", "#cdd3e2", charge)
    shade = mix("#c9d1e2", "#8f98b0", charge)
    deep = mix("#9ea8c0", "#5d6680", charge)
    lobes = [(-10.0, 1.5, 4.6), (-5.6, -3.2, 6.0), (1.0, -5.0, 6.8), (7.4, -2.6, 5.6), (11.0, 1.8, 4.0),
             (-3.0, 2.6, 5.6), (4.6, 2.6, 5.4)]
    lobes = [(x, y - (puff if k in (1, 2, 3) else 0.0), r) for k, (x, y, r) in enumerate(lobes)]
    drops = ((-6.0, 9.0), (0.5, 10.0), (7.0, 9.0))
    if not atk:
        grow = 1 if charge > 0.6 else 0
        for k, (x, y) in enumerate(drops):
            y += (0, -1, 0, 1)[(i + k) % 4] * 0.5 if anim == "move" else 0.0
            _orb(p, x, y, 1 + grow, charge)
    for x, y, r in lobes:
        p.oval((x, y + 1.0), r, r * 0.8, deep)
    for x, y, r in lobes:
        p.oval((x, y + 0.3), r * 0.96, r * 0.78, shade)
    for x, y, r in lobes:
        p.oval((x - r * 0.06, y - r * 0.12), r * 0.86, r * 0.64, base)
    for x, y, r in lobes[:5]:
        p.oval((x - r * 0.22, y - r * 0.4), r * 0.48, r * 0.3, WHITE)
    if charge < 0.6:
        for ex in (-4, 3):
            p.dot((ex, -1), OUT, 3, 2)
            p.dot((ex, -1), deep, 3, 1)
            p.dot((ex + 1, 0), WHITE)
        p.dot((-5, -3), OUT, 2, 1)
        p.dot((4, -3), OUT, 2, 1)
        p.dot((-1, 3), OUT, 3, 1)
    else:
        for ex, s in ((-4, 1), (4, -1)):
            p.dot((ex, -2), OUT)
            p.dot((ex + s, -1), OUT)
            p.dot((ex, 0), OUT)
        if atk:
            p.dot((-1, 2), OUT, 3, 2)
            p.dot((0, 3), KD)
        else:
            p.dot((-1, 3), OUT, 3, 1)
    blush = "#ff9ac8" if charge < 0.5 else "#ff6fb4"
    p.dot((-8, 2), blush, 2, 1)
    p.dot((6, 2), blush, 2, 1)
    if charge > 0.3:
        for s in range(2 + int(charge * 3)):
            a = s * 2.3 + i * 1.4
            p.glow((1 + 15 * math.cos(a), -1 + 8 * math.sin(a)), WHITE if s % 2 else KL)
    if atk and i == 0:
        for x, y in drops:
            p.glow((x, y + 1), WHITE)
            p.glow((x, y + 3), KL)


@creature("Bronte", "raio", 2, move=dict(frames=4, fps=8, loop=True),
          windup=dict(frames=3, fps=6, loop=False), attack=dict(frames=3, fps=10, loop=False))
def bronte(p, anim, i, n):
    bestiary_v2.bronte(p, anim, i, n, arm="bomb")


GHOST, GHOST_EYE = "#d9e4ff", "#1c1433"


@creature("Styx Shade", "submundo", 2, origin=(16, 15), move=dict(frames=4, fps=6, loop=True),
          attack=dict(frames=5, fps=9, loop=False))
def styx_shade(p, anim, i, n):
    atk = anim == "attack"
    lunge = atk and i >= 3
    bob = (0, -1, 0, 1)[i] if not atk else 0
    squash = (1.0, 0.92, 0.86, 1.0, 1.0)[i] if atk else 1.0
    with p.pose(dy=bob, rot=14 if lunge else 0, sx=(1.18 if lunge else 2 - squash), sy=(0.88 if lunge else squash),
                pivot=(0, 4)):
        pts = [(-6.4, 1.0), (-6.0, -4.4), (-3.4, -8.2), (0.4, -9.0), (4.0, -7.6), (6.2, -3.8), (6.6, 1.0)]
        wave_at = i if not atk else 0
        for k in range(7):
            x = 6.6 - k * 2.2
            y = 6.0 + (1.6 if (k + wave_at) % 2 == 0 else -0.2)
            pts.append((x, y))
        p.blob(pts, GHOST, 2)
        eye = "#ff5fb0" if atk else GHOST_EYE
        for ex in (-2.6, 1.8):
            p.dot((ex + 0.6, -4.6), eye, 2, 3)
        if atk:
            p.dot((-0.4, 0.2), GHOST_EYE, 2, 2 if not lunge else 3)
