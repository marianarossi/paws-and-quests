from __future__ import annotations

import math
import json
import os
import random
import struct
import sys
import wave

SR = 44100
OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "audio", "sfx"))


def env(t: float, dur: float, attack: float = 0.004, curve: float = 2.0) -> float:
    if t < attack:
        return t / attack
    return max(0.0, 1.0 - (t - attack) / (dur - attack)) ** curve


def sweep(f0: float, f1: float, t: float, dur: float) -> float:
    return f0 * (f1 / f0) ** min(1.0, t / dur)


class Osc:
    def __init__(self, shape: str = "square", duty: float = 0.5):
        self.phase, self.shape, self.duty = 0.0, shape, duty

    def step(self, freq: float) -> float:
        self.phase = (self.phase + freq / SR) % 1.0
        if self.shape == "square":
            return 1.0 if self.phase < self.duty else -1.0
        if self.shape == "tri":
            return 4.0 * abs(self.phase - 0.5) - 1.0
        return math.sin(2 * math.pi * self.phase)


class LowPass:
    def __init__(self):
        self.y = 0.0

    def step(self, x: float, cutoff: float) -> float:
        self.y += (1.0 - math.exp(-2 * math.pi * cutoff / SR)) * (x - self.y)
        return self.y


def render(dur: float, fn) -> list[float]:
    return [fn(i / SR) for i in range(int(dur * SR))]


def jump() -> list[float]:
    osc, lp, dur = Osc("square", 0.25), LowPass(), 0.14
    return render(dur, lambda t: lp.step(osc.step(sweep(270, 560, t, 0.11)), 3800) * env(t, dur))


def double_jump() -> list[float]:
    osc, lp, nlp, dur = Osc("square", 0.25), LowPass(), LowPass(), 0.17
    rng = random.Random(2)

    def f(t: float) -> float:
        tone = lp.step(osc.step(sweep(430, 930, t, 0.13)), 4200) * env(t, dur)
        puff = nlp.step(rng.uniform(-1, 1), 2600) * env(t, 0.09, curve=1.5) * 0.5 if t < 0.09 else 0.0
        return tone * 0.8 + puff

    return render(dur, f)


def wall_jump() -> list[float]:
    osc, lp, nlp, dur = Osc("square", 0.5), LowPass(), LowPass(), 0.13
    rng = random.Random(3)

    def f(t: float) -> float:
        tone = lp.step(osc.step(sweep(230, 430, t, 0.1)), 3000) * env(t, dur)
        tick = nlp.step(rng.uniform(-1, 1), 5000) * env(t, 0.03) if t < 0.03 else 0.0
        return tone * 0.8 + tick * 0.6

    return render(dur, f)


def land() -> list[float]:
    osc, lp, dur = Osc("sine"), LowPass(), 0.12
    rng = random.Random(4)

    def f(t: float) -> float:
        thud = osc.step(sweep(120, 55, t, 0.1)) * env(t, dur, curve=1.5)
        dust = lp.step(rng.uniform(-1, 1), sweep(1100, 220, t, 0.09)) * env(t, 0.09)if t < 0.09 else 0.0
        return thud * 0.8 + dust * 0.9

    return render(dur, f)


def dash() -> list[float]:
    osc, hi, lo, dur = Osc("square", 0.5), LowPass(), LowPass(), 0.24
    rng = random.Random(5)

    def f(t: float) -> float:
        n = rng.uniform(-1, 1)
        fc = sweep(3200, 500, t, 0.2)
        whoosh = (hi.step(n, fc) - lo.step(n, fc * 0.35)) * env(t, dur, attack=0.012, curve=1.4)
        tone = osc.step(sweep(680, 150, t, 0.16)) * env(t, 0.18) * 0.16 if t < 0.18 else 0.0
        return whoosh * 1.4 + tone

    return render(dur, f)


def dash_refill() -> list[float]:
    a, b, dur = Osc("tri"), Osc("tri"), 0.2

    def f(t: float) -> float:
        first = a.step(880) * env(t, 0.09) if t < 0.09 else 0.0
        second = b.step(1320) * env(t - 0.06, 0.14) if t >= 0.06 else 0.0
        return first * 0.7 + second * 0.7

    return render(dur, f)


def death() -> list[float]:
    osc, lp, nlp, dur = Osc("square", 0.5), LowPass(), LowPass(), 0.42
    rng = random.Random(6)

    def f(t: float) -> float:
        step = min(3, int(t / 0.07))
        tone = lp.step(osc.step(520 * 0.79 ** step), 2600) * env(t, dur, curve=1.3)
        burst = nlp.step(rng.uniform(-1, 1), 3000) * env(t, 0.12) if t < 0.12 else 0.0
        return tone * 0.7 + burst * 0.8

    return render(dur, f)


def respawn() -> list[float]:
    osc, dur = Osc("tri"), 0.22
    return render(dur, lambda t: osc.step(sweep(330, 660, t, 0.18)) * env(t, dur, attack=0.02))


def checkpoint() -> list[float]:
    oscs, dur = [Osc("tri"), Osc("tri"), Osc("tri")], 0.6
    notes = (523.25, 659.25, 783.99)

    def f(t: float) -> float:
        return sum(o.step(n) * env(t - i * 0.09, dur - i * 0.09, curve=2.5) for i, (o, n) in enumerate(zip(oscs, notes)) if t >= i * 0.09) * 0.45

    return render(dur, f)


def spring() -> list[float]:
    osc, dur = Osc("sine"), 0.3
    return render(dur, lambda t: osc.step(180 + 520 * math.sin(math.pi * min(1.0, t / 0.22)) ** 0.6) * env(t, dur, curve=1.4))


def crumble() -> list[float]:
    lp, dur = LowPass(), 0.4
    rng = random.Random(7)
    return render(dur, lambda t: lp.step(rng.uniform(-1, 1), sweep(700, 160, t, 0.35)) * env(t, dur, attack=0.02, curve=1.2) * (0.6 + 0.4 * math.sin(t * 90)))


def crystal() -> list[float]:
    osc, lp, dur = Osc("tri"), LowPass(), 0.22

    def f(t: float) -> float:
        freq = 880.0 if t < 0.07 else 1320.0
        return lp.step(osc.step(freq), 5200) * env(t if t < 0.07 else t - 0.07, 0.07 if t < 0.07 else dur - 0.07, curve=1.4)

    return render(dur, f)


def charge() -> list[float]:
    osc, lp, dur = Osc("tri"), LowPass(), 0.42

    def f(t: float) -> float:
        freq = sweep(260, 880, t, dur) * (1.0 + 0.03 * math.sin(t * 90))
        return lp.step(osc.step(freq), 4200) * min(1.0, t / 0.05) * (0.45 + 0.55 * t / dur)

    return render(dur, f)


def shot() -> list[float]:
    osc, lp, dur = Osc("square", 0.3), LowPass(), 0.13
    return render(dur, lambda t: lp.step(osc.step(sweep(1250, 420, t, 0.1)), 5200) * env(t, dur))


def spark_pop() -> list[float]:
    osc, lp, dur = Osc("tri"), LowPass(), 0.11
    rng = random.Random(11)
    return render(dur, lambda t: (lp.step(rng.uniform(-1, 1), 2600) * 0.7 + osc.step(sweep(700, 260, t, dur)) * 0.5) * env(t, dur, curve=2.5))


def mine_arm() -> list[float]:
    osc, dur = Osc("square", 0.5), 0.45

    def f(t: float) -> float:
        tone = osc.step(1480.0)
        for start in (0.0, 0.18, 0.31):
            if start <= t < start + 0.07:
                return tone * env(t - start, 0.07, curve=1.0) * 0.8
        return 0.0

    return render(dur, f)


def beam_charge() -> list[float]:
    a, b, lp, dur = Osc("tri"), Osc("sine"), LowPass(), 0.6

    def f(t: float) -> float:
        freq = sweep(90, 360, t, dur)
        return lp.step(a.step(freq) * 0.6 + b.step(freq * 2.01) * 0.4, 1800 + 2400 * t / dur) * min(1.0, t / 0.08)

    return render(dur, f)


def beam() -> list[float]:
    a, b, lp, dur = Osc("square", 0.4), Osc("square", 0.5), LowPass(), 0.5
    rng = random.Random(12)

    def f(t: float) -> float:
        buzz = a.step(196.0) * 0.5 + b.step(294.5 + 6 * math.sin(t * 40)) * 0.35 + rng.uniform(-1, 1) * 0.25
        return lp.step(buzz, 3000) * min(1.0, t / 0.01) * min(1.0, (dur - t) / 0.12)

    return render(dur, f)


def hit() -> list[float]:
    dur = 0.16
    osc = Osc("tri")
    lp = LowPass()
    rng = random.Random(22)

    def f(t: float) -> float:
        thump = osc.step(sweep(240.0, 70.0, t, 0.09)) * env(t, dur, 0.002, 2.2)
        crack = lp.step(rng.uniform(-1, 1), 5200.0) * env(t, 0.05, 0.001, 2.0) if t < 0.05 else 0.0
        return thump * 0.8 + crack * 0.6

    return render(dur, f)


def splash() -> list[float]:
    dur = 0.34
    lp = LowPass()
    osc = Osc("tri")
    rng = random.Random(31)

    def f(t: float) -> float:
        hiss = lp.step(rng.uniform(-1, 1), sweep(6000.0, 700.0, t, dur)) * env(t, dur, 0.004, 1.8)
        plop = osc.step(sweep(420.0, 130.0, t, 0.09)) * env(t, 0.12, 0.002, 2.0) if t < 0.12 else 0.0
        return hiss * 0.8 + plop * 0.5

    return render(dur, f)


def swim() -> list[float]:
    dur = 0.12
    osc = Osc("tri")
    lp = LowPass()
    return render(dur, lambda t: lp.step(osc.step(sweep(180.0, 420.0, t, dur)), 1400.0) * env(t, dur, 0.01, 1.5))


def gate_open() -> list[float]:
    dur = 3.1
    low, grit = LowPass(), LowPass()
    thud = Osc("sine")
    rng = random.Random(53)

    def f(t: float) -> float:
        slide = min(1.0, t / 0.3) * (1.0 if t < 2.6 else max(0.0, 1.0 - (t - 2.6) / 0.2))
        rumble = low.step(rng.uniform(-1, 1), 150.0 + 60.0 * math.sin(t * 9.0)) * (0.75 + 0.25 * math.sin(t * 31.0))
        scrape = grit.step(rng.uniform(-1, 1), 1400.0) * (0.12 if int(t * 14.0) % 3 == 0 else 0.03)
        v = (rumble * 1.6 + scrape) * slide
        if t >= 2.7:
            u = t - 2.7
            v += thud.step(sweep(95.0, 42.0, u, 0.3)) * env(u, 0.4, 0.003, 2.2) * 0.9
        return v

    return render(dur, f)


def lake_loop() -> list[float]:
    dur = 8.0
    n = int(dur * SR)
    rnd = random.Random(7)
    noise = [rnd.uniform(-1.0, 1.0) for _ in range(n)]
    low, soft = LowPass(), LowPass()
    out = [0.0] * n
    for k in range(2 * n):
        t = (k % n) / SR
        swell = 0.5 + 0.5 * math.sin(2 * math.pi * 3 * t / dur) * math.sin(2 * math.pi * 1 * t / dur + 0.8)
        lap = max(0.0, math.sin(2 * math.pi * 5 * t / dur + 1.9)) ** 3
        v = low.step(noise[k % n], 380.0 + 900.0 * lap) * (0.22 + 0.5 * swell + 0.6 * lap)
        v = soft.step(v, 2600.0)
        if k >= n:
            out[k - n] = v
    for start, f0 in ((0.9, 880.0), (2.7, 1180.0), (3.1, 760.0), (5.4, 990.0), (6.8, 1320.0)):
        for i in range(int(0.09 * SR)):
            t = i / SR
            out[(int(start * SR) + i) % n] += 0.16 * math.sin(2 * math.pi * sweep(f0, f0 * 1.7, t, 0.09) * t) * env(t, 0.09, 0.002, 2.5)
    return out


def _crackle(rng: random.Random, chance: float, state: list) -> float:
    if rng.random() < chance:
        state[0] = 1.0
    state[0] *= 0.86
    return rng.uniform(-1, 1) * state[0]


def thunder() -> list[float]:
    dur = 5.4
    rng = random.Random(61)
    low, low2, crack = LowPass(), LowPass(), LowPass()
    spark = [0.0]

    def f(t: float) -> float:
        n = rng.uniform(-1, 1)
        v = 0.0
        if t < 0.6:
            v += (n - crack.step(n, 700.0)) * env(t, 0.6, 0.002, 3.2) * 1.5
            v += _crackle(rng, 0.006 * (1.0 - t / 0.6), spark) * 1.2
        swell = 0.6 + 0.4 * math.sin(t * 4.1) * math.sin(t * 1.3 + 0.5)
        rumble = low2.step(low.step(n, 260.0 - 30.0 * t), 150.0) * 4.0
        v += rumble * min(1.0, t / 0.08) * max(0.0, 1.0 - t / dur) ** 1.3 * swell
        return v

    return render(dur, f)


def thunder_far() -> list[float]:
    dur = 4.2
    rng = random.Random(62)
    low, low2 = LowPass(), LowPass()

    def f(t: float) -> float:
        swell = 0.55 + 0.45 * math.sin(t * 3.3 + 1.0) * math.sin(t * 1.1)
        rumble = low2.step(low.step(rng.uniform(-1, 1), 170.0), 110.0) * 4.0
        return rumble * min(1.0, t / 0.35) * max(0.0, 1.0 - t / dur) ** 1.6 * swell

    return render(dur, f)


def bolt_charge() -> list[float]:
    dur = 0.95
    rng = random.Random(67)
    hiss, buzz = LowPass(), Osc("square", 0.3)
    spark = [0.0]

    def f(t: float) -> float:
        p = t / dur
        n = rng.uniform(-1, 1)
        v = buzz.step(80.0 + 160.0 * p) * 0.08 * p
        v += (n - hiss.step(n, 2500.0)) * 0.1 * p
        v += _crackle(rng, 0.002 + 0.03 * p * p, spark) * 0.8
        return v * min(1.0, t / 0.04)

    return render(dur, f)


def bolt() -> list[float]:
    dur = 1.1
    rng = random.Random(68)
    crack, low = LowPass(), LowPass()
    thump = Osc("sine")
    spark = [0.0]

    def f(t: float) -> float:
        n = rng.uniform(-1, 1)
        v = (n - crack.step(n, 1100.0)) * env(t, 0.3, 0.001, 2.6) * 1.4
        v += _crackle(rng, 0.01 * max(0.0, 1.0 - t / 0.3), spark)
        v += thump.step(sweep(170.0, 38.0, t, 0.35)) * env(t, 0.5, 0.002, 2.0) * 0.9
        v += low.step(n, 220.0) * 3.0 * env(t, dur, 0.01, 1.6)
        return v

    return render(dur, f)


def storm_loop() -> list[float]:
    dur = 8.0
    n = int(dur * SR)
    rnd = random.Random(9)
    noise = [rnd.uniform(-1.0, 1.0) for _ in range(n)]
    hp, soft, deep, deep2 = LowPass(), LowPass(), LowPass(), LowPass()
    out = [0.0] * n
    for k in range(2 * n):
        t = (k % n) / SR
        x = noise[k % n]
        swell = 0.75 + 0.25 * math.sin(2 * math.pi * 2 * t / dur) * math.sin(2 * math.pi * 3 * t / dur + 1.2)
        rain = soft.step(x - hp.step(x, 900.0), 5200.0) * 0.5 * swell
        far = max(0.0, math.sin(2 * math.pi * 1 * t / dur + 2.4)) ** 2
        rumble = deep2.step(deep.step(x, 120.0), 80.0) * 5.0 * (0.15 + 0.6 * far)
        if k >= n:
            out[k - n] = rain + rumble
    for i in range(70):
        start = int(rnd.uniform(0, dur) * SR)
        f0 = rnd.uniform(1400.0, 2600.0)
        for j in range(int(0.03 * SR)):
            t = j / SR
            out[(start + j) % n] += 0.06 * math.sin(2 * math.pi * f0 * t) * env(t, 0.03, 0.001, 3.0)
    return out


def door_slam() -> list[float]:
    dur = 1.6
    rng = random.Random(71)
    low, ring = LowPass(), Osc("tri")
    thud = Osc("sine")

    def f(t: float) -> float:
        n = rng.uniform(-1, 1)
        v = thud.step(sweep(110.0, 34.0, t, 0.4)) * env(t, 0.9, 0.002, 2.2) * 1.2
        v += low.step(n, 500.0) * env(t, 0.25, 0.001, 2.0) * 2.2
        v += ring.step(176.0 + 3.0 * math.sin(t * 40.0)) * env(t, dur, 0.004, 3.0) * 0.18
        if 0.18 < t < 0.5:
            u = t - 0.18
            v += low.step(n, 300.0) * env(u, 0.32, 0.002, 2.5) * 0.8
        return v

    return render(dur, f)


def gift() -> list[float]:
    dur = 1.6
    notes = (523.25, 659.25, 783.99, 1046.5, 1318.5)
    bells = [Osc("tri") for _ in notes]
    shine, lp = Osc("sine"), LowPass()

    def f(t: float) -> float:
        v = 0.0
        for k, (freq, osc) in enumerate(zip(notes, bells)):
            start = k * 0.09
            if t >= start:
                v += osc.step(freq) * env(t - start, dur - start, 0.004, 2.4) * 0.32
        v += shine.step(2093.0 * (1.0 + 0.004 * math.sin(t * 38.0))) * env(t, dur, 0.25, 1.6) * 0.08 * (0.6 + 0.4 * math.sin(t * 21.0))
        return lp.step(v, 6000)

    return render(dur, f)


def menu_move() -> list[float]:
    osc, lp, dur = Osc("tri"), LowPass(), 0.06
    return render(dur, lambda t: lp.step(osc.step(660), 3000) * env(t, dur, attack=0.003, curve=1.6))


def menu_select() -> list[float]:
    osc, lp, dur = Osc("tri"), LowPass(), 0.2

    def f(t: float) -> float:
        first = t < 0.06
        return lp.step(osc.step(523.25 if first else 783.99), 3600) * env(t if first else t - 0.06, 0.06 if first else dur - 0.06, curve=1.5)

    return render(dur, f)


def menu_back() -> list[float]:
    osc, lp, dur = Osc("tri"), LowPass(), 0.12
    return render(dur, lambda t: lp.step(osc.step(sweep(520, 330, t, 0.1)), 3000) * env(t, dur, curve=1.6))


def clank() -> list[float]:
    dur = 0.22
    partials = ((1180.0, 1.0), (1730.0, 0.6), (2650.0, 0.35))
    oscs = [Osc("sine") for _ in partials]
    rng = random.Random(41)

    def f(t: float) -> float:
        ring = sum(o.step(fr) * a for o, (fr, a) in zip(oscs, partials)) * env(t, dur, 0.001, 3.0)
        knock = rng.uniform(-1, 1) * env(t, 0.03, 0.001, 2.0) if t < 0.03 else 0.0
        return ring * 0.45 + knock * 0.5

    return render(dur, f)


def swoop() -> list[float]:
    dur = 0.42
    lp = LowPass()
    rng = random.Random(7)

    def f(t: float) -> float:
        cut = 500.0 + 2400.0 * math.sin(math.pi * t / dur)
        return lp.step(rng.uniform(-1, 1), cut) * math.sin(math.pi * t / dur) ** 1.5

    return render(dur, f)


def croak() -> list[float]:
    dur = 0.5
    osc = Osc("square", 0.3)
    lp = LowPass()

    def f(t: float) -> float:
        pulse = 0.5 + 0.5 * math.sin(2 * math.pi * 26.0 * t)
        tone = osc.step(sweep(95.0, 150.0, t, dur))
        return lp.step(tone, 900.0) * pulse * env(t, dur, 0.02, 1.2)

    return render(dur, f)


def snap() -> list[float]:
    dur = 0.12
    lp = LowPass()
    rng = random.Random(5)

    def f(t: float) -> float:
        a = env(t, 0.025, 0.0005, 3.0) if t < 0.025 else 0.0
        b = env(t - 0.045, 0.03, 0.0005, 3.0) if 0.045 <= t < 0.075 else 0.0
        return lp.step(rng.uniform(-1, 1), 6500.0) * (a + b * 0.8)

    return render(dur, f)


def snort() -> list[float]:
    dur = 0.55
    lp = LowPass()
    rng = random.Random(17)

    def f(t: float) -> float:
        k = 0 if t < 0.24 else 1
        local = t - k * 0.28
        if local < 0.0:
            return 0.0
        shape = env(local, 0.22, 0.02, 1.6)
        return lp.step(rng.uniform(-1, 1), 1600.0 - 600.0 * local / 0.22) * shape

    return render(dur, f)


def bow_draw() -> list[float]:
    dur = 0.6
    osc = Osc("tri")
    lp = LowPass()

    def f(t: float) -> float:
        creak = 1.0 + 0.04 * math.sin(2 * math.pi * 47.0 * t)
        return lp.step(osc.step(sweep(380.0, 620.0, t, dur) * creak), 2200.0) * min(1.0, t / dur) * 0.6

    return render(dur, f)


def twang() -> list[float]:
    dur = 0.28
    osc = Osc("square", 0.18)
    lp = LowPass()

    def f(t: float) -> float:
        vib = 1.0 + 0.03 * math.sin(2 * math.pi * 38.0 * t)
        return lp.step(osc.step(sweep(520.0, 300.0, t, 0.2) * vib), 2600.0) * env(t, dur, 0.001, 2.4)

    return render(dur, f)


def tongue() -> list[float]:
    dur = 0.24
    osc = Osc("sine")
    lp = LowPass()
    rng = random.Random(29)

    def f(t: float) -> float:
        whip = osc.step(sweep(300.0, 1400.0, t, 0.08)) * env(t, 0.12, 0.002, 1.6) if t < 0.12 else 0.0
        smack = lp.step(rng.uniform(-1, 1), 2400.0) * env(t - 0.08, 0.06, 0.001, 2.5) if 0.08 <= t < 0.14 else 0.0
        return whip * 0.6 + smack * 0.7

    return render(dur, f)


def fuse() -> list[float]:
    dur = 1.2
    rng = random.Random(82)
    lp = LowPass()
    osc = Osc("square", 0.2)
    spark = [0.0]

    def f(t: float) -> float:
        hiss = lp.step(rng.uniform(-1, 1), 3500.0 + 2500.0 * t / dur) * 0.5
        crackle = _crackle(rng, 0.004 + 0.01 * t / dur, spark)
        buzz = osc.step(sweep(180.0, 420.0, t, dur)) * 0.15
        return (hiss + crackle + buzz) * min(1.0, t / 0.05) * (1.0 - max(0.0, t - dur + 0.08) / 0.08)

    return render(dur, f)


def boom() -> list[float]:
    dur = 0.9
    rng = random.Random(83)
    lp = LowPass()
    thump = Osc("sine")

    def f(t: float) -> float:
        crack = rng.uniform(-1, 1) * env(t, 0.12, 0.001, 1.2)
        rumble = lp.step(rng.uniform(-1, 1), 500.0 - 300.0 * min(1.0, t / dur)) * env(t, dur, 0.01, 1.6) * 1.6
        low = thump.step(sweep(90.0, 38.0, t, 0.4)) * env(t, 0.5, 0.002, 1.8)
        return crack * 0.6 + rumble + low * 0.8

    return render(dur, f)


def screech() -> list[float]:
    dur = 0.4
    osc = Osc("square", 0.3)
    lp = LowPass()
    rng = random.Random(86)

    def f(t: float) -> float:
        tone = osc.step(sweep(1500.0, 900.0, t, dur) * (1.0 + 0.04 * math.sin(2 * math.pi * 40.0 * t)))
        return lp.step(tone * 0.7 + rng.uniform(-1, 1) * 0.4, 4000.0) * env(t, dur, 0.01, 1.3)

    return render(dur, f)


def gust() -> list[float]:
    dur = 1.1
    rng = random.Random(87)
    lp = LowPass()

    def f(t: float) -> float:
        swell = math.sin(math.pi * min(1.0, t / dur)) ** 0.7
        return lp.step(rng.uniform(-1, 1), 700.0 + 1600.0 * swell) * swell * 1.3

    return render(dur, f)


def ball_bounce() -> list[float]:
    dur = 0.12
    osc = Osc("sine")
    rng = random.Random(92)

    def f(t: float) -> float:
        return (osc.step(sweep(360.0, 180.0, t, 0.05)) + rng.uniform(-1, 1) * 0.25 * env(t, 0.02)) * env(t, dur, 0.001, 2.4)

    return render(dur, f)


def _brass(freq: float, t: float, oscs: list, lp: LowPass, cutoff: float) -> float:
    v = oscs[0].step(freq) + oscs[1].step(freq * 1.006) * 0.8
    return lp.step(v, cutoff)


def boss_sting() -> list[float]:
    dur = 2.6
    hit = 0.55
    rng = random.Random(81)
    notes = (73.4, 110.0, 146.8, 207.7)
    oscs = [[Osc("square", 0.4), Osc("square", 0.33)] for _ in notes]
    lps = [LowPass() for _ in notes]
    hp, kick = LowPass(), Osc("sine")

    def f(t: float) -> float:
        n = rng.uniform(-1, 1)
        v = 0.0
        if t < hit:
            v += (n - hp.step(n, 3000.0)) * (t / hit) ** 3 * 0.9
        else:
            u = t - hit
            cutoff = 250.0 + 1700.0 * math.exp(-u * 2.2)
            chord = sum(_brass(fr, u, o, lp, cutoff) for fr, o, lp in zip(notes, oscs, lps))
            v += chord * 0.3 * min(1.0, u / 0.02) * max(0.0, 1.0 - u / (dur - hit)) ** 1.4
            for start in (0.0, 0.32):
                k = u - start
                if 0.0 <= k < 0.5:
                    v += kick.step(sweep(110.0, 36.0, k, 0.3)) * env(k, 0.5, 0.002, 2.2) * 1.3
            if u < 0.25:
                v += (n - hp.step(n, 1800.0)) * env(u, 0.25, 0.001, 2.5) * 0.5
        return v

    return render(dur, f)


def boss_loop() -> list[float]:
    beat = 60.0 / 132.0
    dur = beat * 8
    n = int(dur * SR)
    out = [0.0] * n
    rng = random.Random(82)

    def add(start: float, length: float, fn) -> None:
        first = int(start * SR)
        for j in range(int(length * SR)):
            out[(first + j) % n] += fn(j / SR)

    def tom(pitch: float, gain: float):
        osc = Osc("sine")
        return lambda t: osc.step(sweep(pitch * 1.8, pitch, t, 0.12)) * env(t, 0.45, 0.002, 2.6) * gain

    def tick(gain: float):
        lp = LowPass()
        return lambda t: (lambda x: (x - lp.step(x, 5000.0)) * env(t, 0.05, 0.001, 3.0) * gain)(rng.uniform(-1, 1))

    for bar in range(2):
        b0 = bar * 4
        for b, pitch, gain in ((0, 52.0, 1.0), (1.5, 52.0, 0.7), (2, 52.0, 0.9), (3, 70.0, 0.6), (3.5, 82.0, 0.6),
                               (3.75, 98.0, 0.55 if bar == 1 else 0.0)):
            if gain > 0.0:
                add((b0 + b) * beat, 0.45, tom(pitch, gain))
        for k in range(8):
            add((b0 + k * 0.5) * beat, 0.05, tick(0.18 if k % 2 else 0.1))
    drone = Osc("sine")
    for i in range(n):
        t = i / SR
        pulse = 0.55 + 0.45 * math.cos(2 * math.pi * t / beat)
        out[i] += drone.step(round(36.7 * dur) / dur) * 0.22 * pulse
    return out


SOUNDS = {
    "boss_sting": (boss_sting, 0.8), "boss_loop": (boss_loop, 0.6),
    "ball_bounce": (ball_bounce, 0.35),
    "fuse": (fuse, 0.35), "boom": (boom, 0.75),
    "screech": (screech, 0.35), "gust": (gust, 0.4),
    "tongue": (tongue, 0.45),
    "clank": (clank, 0.5), "swoop": (swoop, 0.4), "croak": (croak, 0.45),
    "snap": (snap, 0.5), "snort": (snort, 0.4), "bow_draw": (bow_draw, 0.3), "twang": (twang, 0.4),
    "menu_move": (menu_move, 0.22), "menu_select": (menu_select, 0.3), "menu_back": (menu_back, 0.26),
    "door_slam": (door_slam, 0.7),
    "thunder": (thunder, 0.8), "thunder_far": (thunder_far, 0.55), "bolt_charge": (bolt_charge, 0.38), "bolt": (bolt, 0.6),
    "storm_loop": (storm_loop, 0.5),
    "splash": (splash, 0.42), "swim": (swim, 0.3), "lake_loop": (lake_loop, 0.5), "gate_open": (gate_open, 0.55),
    "hit": (hit, 0.5),
    "charge": (charge, 0.35), "shot": (shot, 0.4), "spark_pop": (spark_pop, 0.4),
    "mine_arm": (mine_arm, 0.32), "beam_charge": (beam_charge, 0.4), "beam": (beam, 0.36),
    "crystal": (crystal, 0.4),
    "gift": (gift, 0.6),
    "jump": (jump, 0.42), "double_jump": (double_jump, 0.42), "wall_jump": (wall_jump, 0.42),
    "land": (land, 0.5), "dash": (dash, 0.55), "dash_refill": (dash_refill, 0.3),
    "death": (death, 0.5), "respawn": (respawn, 0.3), "checkpoint": (checkpoint, 0.4),
    "spring": (spring, 0.45), "crumble": (crumble, 0.5),
}


def write_wav(name: str, samples: list[float], peak: float) -> None:
    top = max(1e-6, max(abs(s) for s in samples))
    fade = int(0.004 * SR)
    for i in range(1, min(fade, len(samples)) + 1):
        samples[-i] *= (i - 1) / fade
    with wave.open(os.path.join(OUT, name + ".wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1.0, min(1.0, s / top * peak)) * 32767)) for s in samples))


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    only = sys.argv[1:]
    sources = os.path.join(OUT, "sources.json")
    external = set(json.load(open(sources, encoding="utf-8"))) if os.path.exists(sources) else set()
    for name, (fn, peak) in SOUNDS.items():
        if (only and name not in only) or name in external:
            continue
        write_wav(name, fn(), peak)
    print("sfx: ok (%d sons)" % len(SOUNDS))


if __name__ == "__main__":
    main()
