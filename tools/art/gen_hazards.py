from __future__ import annotations

from PIL import Image

from gen_props import AQUA, LILAC, mushroom
from vec import Canvas, curve, hash01, rgba, ribbon, save, save_json, smooth


def outlined(img: Image.Image, color: str = "outline") -> Image.Image:
    out = img.copy()
    src = img.load()
    for y in range(img.height):
        for x in range(img.width):
            if src[x, y][3] == 0 and any(
                    0 <= x + dx < img.width and 0 <= y + dy < img.height and src[x + dx, y + dy][3] != 0
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out.putpixel((x, y), rgba(color))
    return out


THORNS = [
    [(1.8, 8.5, -0.6), (5.0, 12.2, 0.5), (8.4, 7.0, -0.3), (11.2, 11.2, 0.7), (14.3, 9.0, -0.5)],
    [(1.5, 10.6, 0.4), (4.6, 7.4, -0.5), (7.8, 11.8, 0.3), (11.0, 8.0, -0.6), (14.2, 12.0, 0.5)],
]


def spikes() -> None:
    sheet = Image.new("RGBA", (32, 16), (0, 0, 0, 0))
    for v, thorns in enumerate(THORNS):
        c = Canvas(16, 16)
        c.poly(smooth([(-1, 17), (-1, 12.6), (2.5, 11.8 + v), (5, 12.9), (8, 11.7), (11, 12.9 - v), (13.5, 11.9), (17, 12.6), (17, 17)], 1), "#2c1a3a")
        c.poly(ribbon(curve([(-1, 14.2 + v), (4, 13.2), (8, 14.7), (12, 13.3), (17, 14.2 + v)]), 0.55, 0.55), "#4a2a58")
        for x, h, lean in thorns:
            mid = (x + lean * 0.9, 16 - h * 0.55)
            tip = (x + lean * 1.7, 16 - h)
            c.poly([(x - 1.9, 15.6), (x + 1.9, 15.6), (mid[0] + 0.95, mid[1]), tip, (mid[0] - 0.95, mid[1])], "#5a1c5e")
            c.poly([(x - 0.9, 16 - h * 0.28), (x + 1.0, 16 - h * 0.28), (mid[0] + 0.55, mid[1]), tip, (mid[0] - 0.5, mid[1])], "#c0297f")
            c.poly([(x - 0.9, 16 - h * 0.28), (x - 0.2, 16 - h * 0.28), tip, (mid[0] - 0.5, mid[1])], "#ff5fb0")
            c.dot((tip[0] - 0.5, tip[1] + 0.4), "#ffb3e0", 1, 2)
        for i, x in enumerate((3.4, 9.8, 12.8)):
            c.dot((x, 11 + (i + v) % 2), "#c0297f", 1, 2)
            c.dot((x, 10 + (i + v) % 2), "#ff8ad0", 1, 1)
        sheet.paste(c.finish(outline="outline"), (v * 16, 0))
    save(sheet, "sprites", "props", "spikes.png")


SPRING_COLORS = {
    "lilac": (LILAC, "#efeaff", [0.72, 0.66, 1.0]),
    "pink": (("#ff9ac4", "#ffe3ef", "#c9608f"), "#fff0f6", [1.0, 0.66, 0.82]),
    "aqua": (AQUA, "mint_l", [0.5, 0.95, 0.83]),
    "green": (("#7fdc6a", "#e9ffc8", "#2f9a52"), "#f2ffe0", [0.62, 1.0, 0.55]),
}
SPRING_W, SPRING_H = 32, 22


def spring_frame(shape: tuple, palette: tuple, gill: str) -> Image.Image:
    cap_w, cap_h, stalk_h, stalk_w = shape
    img = Image.new("RGBA", (SPRING_W, SPRING_H), (0, 0, 0, 0))
    for dx, k, seed in ((-9, 0.5, 2), (9, 0.6, 3), (0, 1.0, 5)):
        m = mushroom(seed, cap_w * k, cap_h * k, stalk_h * k, stalk_w * 0.62 * max(k, 0.7), palette, gill, 6 if k == 1.0 else 2)
        img.alpha_composite(m, (SPRING_W // 2 + dx - m.width // 2, SPRING_H - m.height))
    return img


def spring() -> None:
    rest = [(18, 10, 6, 5), (19, 9.3, 5.5, 5.2), (18, 10, 6, 5), (17.4, 10.6, 6.5, 4.8)]
    squash = [(21, 7, 3.5, 6), (19.5, 8.6, 5, 5.5)]
    for name, (palette, gill, light) in SPRING_COLORS.items():
        sheet = Image.new("RGBA", (SPRING_W * 4, SPRING_H * 2), (0, 0, 0, 0))
        for row, shapes in enumerate((rest, squash)):
            for i, shape in enumerate(shapes):
                sheet.paste(spring_frame(shape, palette, gill), (i * SPRING_W, row * SPRING_H))
        save(sheet, "sprites", "props", "spring_%s.png" % name)
        save_json({"image": "spring_%s.png" % name, "frame_w": SPRING_W, "frame_h": SPRING_H, "scale": 1.0, "light": light,
                   "animations": {"idle": {"row": 0, "frames": 4, "fps": 4, "loop": True},
                                  "squash": {"row": 1, "frames": 2, "fps": 12, "loop": False}}},
                  "sprites", "props", "spring_%s.json" % name)


PAW = [
    "...xx.xx...",
    "...xx.xx...",
    "xx.......xx",
    "xx.xxxxx.xx",
    "..xxxxxxx..",
    "..xxxxxxx..",
    "..xxxxxxx..",
    "...xx.xx...",
]


def dash_crystal() -> None:
    sheet = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    for f in range(3):
        img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        px = img.load()
        for j, row in enumerate(PAW):
            for i, ch in enumerate(row):
                if ch == ".":
                    continue
                x, y = i + 2, j + 4
                lit = (row[i - 1] if i else ".") == "." and (PAW[j - 1][i] if j else ".") == "."
                low = j + 1 >= len(PAW) or PAW[j + 1][i] == "."
                col = "#d6e2ff" if lit else "#2f4372" if low else "#5b78c4"
                if f == 1 and (i + j) % 5 == 0:
                    col = "#f4f8ff"
                px[x, y] = rgba(col)
        if f < 2:
            img = outlined(img)
        else:
            ring = outlined(img, "#8f9dc0")
            src = img.load()
            out = ring.load()
            for y in range(16):
                for x in range(16):
                    if src[x, y][3]:
                        out[x, y] = (0, 0, 0, 0)
            img = ring
        sheet.paste(img, (f % 2 * 16, f // 2 * 16))
    save(sheet, "sprites", "props", "dash_crystal.png")
    save_json({"image": "dash_crystal.png", "frame_w": 16, "frame_h": 16, "scale": 1.0,
               "animations": {"idle": {"row": 0, "frames": 2, "fps": 3, "loop": True},
                              "empty": {"row": 1, "frames": 1, "fps": 1, "loop": False}}},
              "sprites", "props", "dash_crystal.json")


def crumble() -> None:
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = img.load()
    for x in range(16):
        depth = 6 + int(hash01(x // 2, 1, 8) * 3)
        for y in range(depth):
            col = "#6d5f96" if y == 0 else "#4a3d74" if y < depth - 1 else "#2e264b"
            if y > 0 and hash01(x, y, 9) < 0.1:
                col = "#3a305c"
            px[x, y] = rgba(col)
    for x, y in ((3, 1), (4, 2), (4, 3), (5, 4), (10, 1), (10, 2), (11, 3), (12, 3), (12, 4), (7, 5), (14, 2)):
        px[x, y] = rgba("#1f1937")
    for x in (1, 6, 9, 13):
        px[x, 0] = rgba("moss")
    save(img, "sprites", "props", "crumble.png")


def main() -> None:
    spikes()
    spring()
    crumble()
    dash_crystal()
    print("perigos: ok")


if __name__ == "__main__":
    main()
