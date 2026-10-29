from __future__ import annotations

import math

from PIL import Image

from vec import Canvas, ellipse, save, save_json

OUT = "#1c1433"


def poof_frame(w: int, h: int, step: int) -> Image.Image:
    c = Canvas(w, h, origin=(w / 2, h / 2 + 1))
    reach, r = (2.2, 4.6, 6.6)[step], (3.6, 2.7, 1.5)[step]
    for k in range(5):
        a = k * 2 * math.pi / 5 - 0.6
        c.poly(ellipse((reach * math.cos(a), reach * 0.8 * math.sin(a)), r, r * 0.9), "#b9a6d8" if k % 2 else "#e6dcf6")
    if step < 2:
        c.poly(ellipse((0, 0), (3.2, 1.8)[step]), "#ffffff")
    for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0), (0, 0)) if step > 0 else ():
        c.dot((dx * (3 - step), dy * (3 - step)), "#ff8ad0", 1, 1)
    return c.finish()


def death_row(first: Image.Image, w: int, h: int) -> list[Image.Image]:
    return [first] + [poof_frame(w, h, k) for k in range(3)]
