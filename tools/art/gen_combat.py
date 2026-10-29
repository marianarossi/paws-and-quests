from __future__ import annotations

import math

from PIL import Image

from vec import Canvas, ellipse, rgba, save, save_json

PINK = {"core": "#ffffff", "hot": "#ffd0ee", "pink": "#ff5fb0", "magenta": "#c0297f", "deep": "#5a1c5e"}


def spark() -> None:
    frames = 4
    sheet = Image.new("RGBA", (12 * frames, 12), (0, 0, 0, 0))
    for f in range(frames):
        img = Image.new("RGBA", (12, 12), (0, 0, 0, 0))
        px = img.load()
        for y in range(12):
            for x in range(12):
                dx, dy = x - 5.5, y - 5.5
                d = math.hypot(dx, dy)
                if f % 2 == 0:
                    arm = min(abs(dx), abs(dy)) < 0.6
                else:
                    arm = abs(abs(dx) - abs(dy)) < 0.8
                reach = 5.2 if f in (0, 1) else 4.2
                col = None
                if d < 1.3:
                    col = PINK["core"]
                elif d < 2.3:
                    col = PINK["hot"]
                elif d < 3.3:
                    col = PINK["pink"]
                elif d < 4.0 and not arm:
                    col = PINK["magenta"] if (x + y + f) % 2 else None
                if arm and 2.3 <= d < reach:
                    col = PINK["hot"] if d < 3.6 else PINK["pink"]
                if col:
                    px[x, y] = rgba(col)
        sheet.paste(img, (f * 12, 0))
    save(sheet, "sprites", "combat", "spark.png")
    save_json({"image": "spark.png", "frame_w": 12, "frame_h": 12, "scale": 1.0,
               "animations": {"fly": {"row": 0, "frames": frames, "fps": 14, "loop": True}}},
              "sprites", "combat", "spark.json")


def wisp_frame(f: int, charge: float, flash: bool = False) -> Image.Image:
    c = Canvas(24, 24, origin=(12, 13))
    puff = 0.5 * math.sin(f * math.pi / 2)
    grow = 1.0 + 0.08 * charge

    def tone(calm: str, storm: str) -> tuple:
        a, b = rgba(calm), rgba(storm)
        return tuple(round(a[i] + (b[i] - a[i]) * charge) for i in range(4))

    top, base = rgba("#ffffff"), tone("#eef2f8", "#d9deea")
    shade, deep = tone("#c9d1e2", "#8f98b0"), tone("#9ea8c0", "#626b85")
    if flash:
        top, base, shade, deep = rgba("#ffffff"), rgba("#ffffff"), rgba("#e6ebf5"), rgba("#c9d1e2")
    lobes = [(-6.2, 1.6, 3.4), (-2.8, -1.8, 4.4), (2.4, -2.8, 4.8), (6.4, 0.8, 3.4), (-1.0, 2.4, 4.4), (3.6, 2.6, 4.0)]
    lobes = [(x * grow, y * grow - (puff if k in (1, 2) else 0), r * grow) for k, (x, y, r) in enumerate(lobes)]
    for x, y, r in lobes:
        c.poly(ellipse((x, y + 1.0), r, r * 0.82), deep)
    for x, y, r in lobes:
        c.poly(ellipse((x, y + 0.3), r * 0.96, r * 0.8), shade)
    for x, y, r in lobes:
        c.poly(ellipse((x - r * 0.06, y - r * 0.12), r * 0.86, r * 0.66), base)
    for x, y, r in lobes[:4]:
        c.poly(ellipse((x - r * 0.22, y - r * 0.38), r * 0.5, r * 0.32), top)
    out = "#1c1433"
    if charge < 0.6 and not flash:
        for ex in (-4, 2):
            c.dot((ex, 0), out, 2, 3)
            c.dot((ex, 0), "#ffffff")
        c.dot((-1, 3), out)
        c.dot((0, 4), out)
        c.dot((1, 3), out)
    else:
        c.dot((-4, 0), out)
        c.dot((-3, 1), out)
        c.dot((-4, 2), out)
        c.dot((3, 0), out)
        c.dot((2, 1), out)
        c.dot((3, 2), out)
        if flash or charge > 0.9:
            c.dot((-1, 3), out, 2, 2)
            c.dot((-1, 4), "#c0297f", 2, 1)
        else:
            c.dot((-1, 4), out, 2, 1)
    blush = "#ff9ac8" if charge < 0.5 else "#ff6fb4"
    c.dot((-6, 3), blush, 2, 1)
    c.dot((4, 3), blush, 2, 1)
    img = c.finish(outline=out)
    px = img.load()
    if charge > 0.3 and not flash:
        n = 2 + int(charge * 4)
        for k in range(n):
            a = k * 2.4 + f * 1.3
            x = int(12 + 10.5 * math.cos(a))
            y = int(13 + 7.5 * math.sin(a))
            for dx, dy, col in ((0, 0, "#ffffff"), (1, 0, "#ff5fb0"), (0, 1, "#ff5fb0"), (-1, 0, "#c0297f")):
                if 0 <= x + dx < 24 and 0 <= y + dy < 24 and (k + dx) % 2 == 0:
                    px[x + dx, y + dy] = rgba(col)
    return img


def wisp() -> None:
    sheet = Image.new("RGBA", (24 * 4, 24 * 3), (0, 0, 0, 0))
    for f in range(4):
        sheet.paste(wisp_frame(f, 0.0), (f * 24, 0))
        sheet.paste(wisp_frame(f, (f + 1) / 4), (f * 24, 24))
    sheet.paste(wisp_frame(0, 1.0, flash=True), (0, 48))
    sheet.paste(wisp_frame(1, 0.6), (24, 48))
    save(sheet, "sprites", "combat", "wisp.png")
    save_json({"image": "wisp.png", "frame_w": 24, "frame_h": 24, "scale": 1.0,
               "animations": {"idle": {"row": 0, "frames": 4, "fps": 5, "loop": True},
                              "charge": {"row": 1, "frames": 4, "fps": 8, "loop": False},
                              "fire": {"row": 2, "frames": 2, "fps": 12, "loop": False}}},
              "sprites", "combat", "wisp.json")


def mine_frame(armed: bool, blink: bool) -> Image.Image:
    c = Canvas(16, 16, origin=(8, 8))
    for k in range(8):
        a = k * math.pi / 4
        tip = (6.6 * math.cos(a), 6.6 * math.sin(a))
        side = (math.cos(a + math.pi / 2) * 1.3, math.sin(a + math.pi / 2) * 1.3)
        root = (3.4 * math.cos(a), 3.4 * math.sin(a))
        c.poly([(root[0] + side[0], root[1] + side[1]), tip, (root[0] - side[0], root[1] - side[1])], "#c0297f" if armed else "#5a1c5e")
    c.poly(ellipse((0, 0), 4.6), "#3a2d5c" if not armed else "#5a1c5e")
    c.poly(ellipse((-1.0, -1.2), 2.6, 2.0), "#54447f" if not armed else "#8a2a7a")
    core = ("#ffffff" if blink else "#ff5fb0") if armed else ("#c0297f" if blink else "#5a1c5e")
    c.poly(ellipse((0, 0), 1.9), core)
    if armed and blink:
        c.poly(ellipse((0, 0), 2.8), "#ffd0ee")
        c.poly(ellipse((0, 0), 1.6), "#ffffff")
    return c.finish(outline="#1c1433")


def mine() -> None:
    sheet = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    for row, armed in enumerate((False, True)):
        for i, blink in enumerate((False, True)):
            sheet.paste(mine_frame(armed, blink), (i * 16, row * 16))
    save(sheet, "sprites", "combat", "mine.png")
    save_json({"image": "mine.png", "frame_w": 16, "frame_h": 16, "scale": 1.0,
               "animations": {"sleep": {"row": 0, "frames": 2, "fps": 1.5, "loop": True},
                              "armed": {"row": 1, "frames": 2, "fps": 12, "loop": True}}},
              "sprites", "combat", "mine.json")


def main() -> None:
    spark()
    wisp()
    mine()
    print("projeteis: ok")


if __name__ == "__main__":
    main()
