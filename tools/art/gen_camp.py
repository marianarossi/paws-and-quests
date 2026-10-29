from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw, ImageFont

from vec import Canvas, DOCS_PREVIEW, capsule, ellipse, ribbon, save

OUTLINE = "#151229"
TENT_W, TENT_H = 64, 40

TENT_COLORS = {
    "orange": dict(light="#f2a457", base="#d9773a", dark="#a54f2c", deep="#7a3826", seam="#ffcf8a"),
    "olive": dict(light="#a9b464", base="#7f8c47", dark="#5b6634", deep="#424b28", seam="#d4dc95",
                  patch="#c99a5a"),
    "navy": dict(light="#5873b4", base="#3d5592", dark="#2f4372", deep="#212f52", seam="#9fb5e6"),
}
INSIDE = dict(dark="#3a2230", warm="#8a4a34", glow="#e39a4f", floor="#5b3a30")
ROPE, STAKE, CLOTH = "#e4d3b0", "#8a5a41", "#3b3150"


def _ropes(img: Image.Image, ends: list[tuple[tuple[float, float], tuple[float, float]]]) -> Image.Image:
    d = ImageDraw.Draw(img)
    oy = TENT_H - 1
    for a, b in ends:
        d.line([(round(a[0]), round(a[1] + oy)), (round(b[0]), round(b[1] + oy))], fill=ROPE, width=1)
        x, y = round(b[0]), round(b[1] + oy)
        d.rectangle((x, y - 2, x, y), fill=STAKE)
        d.point((x, y - 3), fill=OUTLINE)
    return img


def a_frame(col: dict, patched: bool = False) -> Image.Image:
    c = Canvas(TENT_W, TENT_H, 1, origin=(0, TENT_H - 1))
    apex, back_apex = (44.0, -31.0), (19.0, -28.0)
    c.poly([(4, 0.5), (60, 0.5), (60, -1.5), (4, -1.5)], CLOTH)
    side = [back_apex, apex, (31.0, 0.0), (7.0, -1.0)]
    c.poly(side, col["dark"])
    c.clip(side, [(7, -1), (31, 0), (33, -4), (9, -5)], col["deep"])
    for t in (0.36, 0.68):
        top = (back_apex[0] + (apex[0] - back_apex[0]) * t, back_apex[1] + (apex[1] - back_apex[1]) * t)
        bot = (7 + 24 * t, -1 + t)
        c.poly(ribbon([top, bot], 0.45, 0.45), col["deep"])
    front = [apex, (58.0, 0.0), (31.0, 0.0)]
    c.poly(front, col["base"])
    c.clip(front, [apex, (58, 0), (52, 0), (44, -24)], col["light"])
    door = [(44.0, -22.0), (51.5, 0.0), (37.0, 0.0)]
    c.poly(door, INSIDE["dark"])
    c.clip(door, [(44, -12), (51, 0), (38, 0)], INSIDE["warm"])
    c.clip(door, ellipse((45.0, -2.5), 4.5, 3.5), INSIDE["glow"])
    c.poly([(36.5, 0.0), (44.0, -22.0), (40.0, -3.0)], col["dark"])
    c.poly(capsule((40.6, -4.0), (43.0, -16.0), 1.1), col["seam"])
    c.poly(capsule((52.0, 0.0), (45.0, -21.0), 0.55), col["deep"])
    if patched:
        c.poly([(13, -11), (18, -12), (18.5, -8), (13.5, -7)], col["patch"])
        c.poly([(51, -14), (54, -14.5), (54.5, -11), (51.5, -10.5)], col["patch"])
    c.poly(capsule((back_apex[0] - 1.5, back_apex[1] + 0.5), (apex[0] + 1.2, apex[1] - 0.6), 0.6), col["seam"])
    c.poly(capsule((apex[0], apex[1] - 2.5), (apex[0], apex[1] + 0.5), 0.6), STAKE)
    img = c.finish(outline=OUTLINE)
    return _ropes(img, [((back_apex[0] - 2, back_apex[1] + 1), (1.0, 0.0)), ((apex[0] + 2, apex[1] + 3), (63.0, 0.0))])


def dome(col: dict) -> Image.Image:
    c = Canvas(TENT_W, TENT_H, 1, origin=(0, TENT_H - 1))
    c.poly([(3, 0.5), (61, 0.5), (61, -1.5), (3, -1.5)], CLOTH)
    shell = [(x, -26.0 * (1 - ((x - 32.0) / 27.0) ** 2) ** 0.6) for x in [5 + 54 * i / 40 for i in range(41)]]
    c.poly(shell + [(59, 0), (5, 0)], col["base"])
    c.clip(shell + [(59, 0), (5, 0)], ellipse((22.0, -2.0), 20.0, 28.0), col["dark"])
    c.clip(shell + [(59, 0), (5, 0)], ellipse((48.0, -14.0), 13.0, 16.0), col["light"])
    c.clip(shell + [(59, 0), (5, 0)], [(5, 0), (59, 0), (59, -3), (5, -3)], col["deep"])
    for a, b in (((12.0, 0.0), (44.0, -24.5)), ((52.0, 0.0), (20.0, -24.5))):
        c.poly(ribbon([a, ((a[0] + b[0]) / 2, b[1] - 1.0), b], 0.5, 0.5), col["seam"])
    door = ellipse((43.0, 0.0), 7.5, 15.0)
    c.clip(shell + [(59, 0), (5, 0)], door, INSIDE["dark"])
    c.clip(door, ellipse((43.0, 0.0), 6.0, 9.0), INSIDE["warm"])
    c.clip(door, ellipse((44.0, -1.0), 4.0, 3.5), INSIDE["glow"])
    c.poly(capsule((35.8, -2.0), (37.5, -12.0), 1.2), col["seam"])
    return _ropes(c.finish(outline=OUTLINE), [((13.0, -19.0), (0.0, 0.0)), ((52.0, -18.0), (63.0, 0.0))])


def tents() -> dict[str, Image.Image]:
    return {
        "A": a_frame(TENT_COLORS["orange"]),
        "B": a_frame(TENT_COLORS["olive"], patched=True),
        "C": dome(TENT_COLORS["navy"]),
    }


def options_sheet(out: str) -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.join(here, "..", "..")
    hero = Image.open(os.path.join(root, "assets", "sprites", "hero", "hero.png")).convert("RGBA").crop((0, 0, 32, 32))
    dog = Image.open(os.path.join(root, "assets", "sprites", "dog", "dog.png")).convert("RGBA")
    dog = dog.crop((0, 7 * 32, 32, 8 * 32))
    scale, cell_w, cell_h, label_h = 5, 110, 48, 24
    sky, grass = (64, 54, 92, 255), (46, 120, 92, 255)
    img = Image.new("RGBA", (3 * cell_w * scale, cell_h * scale + label_h), (30, 26, 44, 255))
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 20)
    names = {"A": "A: em A, laranja", "B": "B: em A, verde-oliva com remendos", "C": "C: iglu azul-marinho"}
    for i, (key, tent) in enumerate(tents().items()):
        cell = Image.new("RGBA", (cell_w, cell_h), sky)
        ImageDraw.Draw(cell).rectangle((0, cell_h - 6, cell_w, cell_h), fill=grass)
        cell.alpha_composite(tent, (4, cell_h - 6 - TENT_H + 1))
        cell.alpha_composite(dog, (60, cell_h - 6 - 31))
        cell.alpha_composite(hero, (78, cell_h - 6 - 31))
        img.alpha_composite(cell.resize((cell_w * scale, cell_h * scale), Image.NEAREST), (i * cell_w * scale, label_h))
        d.text((i * cell_w * scale + 8, 2), names[key], fill=(240, 236, 228, 255), font=font)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.save(out)


def bowl() -> Image.Image:
    c = Canvas(12, 6, 1, origin=(6, 5))
    body = [(-5, -3), (5, -3), (4, 0), (-4, 0)]
    c.poly(body, "#b9583e")
    c.clip(body, [(-5, -3), (5, -3), (5, -2), (-5, -2)], "#e07a55")
    c.poly(ellipse((0, -3.2), 4.2, 0.9), "#8a5a41")
    c.dot((-2, -4), "#b98458")
    c.dot((1, -4), "#b98458")
    return c.finish(outline=OUTLINE)


def ball() -> Image.Image:
    out = Image.new("RGBA", (14, 7), (0, 0, 0, 0))
    for f in range(2):
        img = Image.new("RGBA", (7, 7), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse((1, 1, 5, 5), fill="#c8e04a")
        d.point([(2, 2), (3, 2)], fill="#ecf79a")
        d.point([(4, 4), (5, 3), (3, 5)], fill="#8ea832")
        seam = [(2, 4), (3, 3), (4, 2)] if f == 0 else [(2, 2), (3, 3), (4, 4)]
        d.point(seam, fill="#f4f0eb")
        for y in range(7):
            for x in range(7):
                if img.getpixel((x, y))[3] == 0 and any(
                        0 <= x + dx < 7 and 0 <= y + dy < 7 and img.getpixel((x + dx, y + dy))[3] > 0
                        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    d.point((x, y), fill=OUTLINE)
        out.alpha_composite(img, (f * 7, 0))
    return out


def scorch() -> Image.Image:
    c = Canvas(24, 5, 1, origin=(12, 4))
    c.poly(ellipse((0, -1.2), 11.0, 2.2), "#2a2030")
    c.poly(ellipse((0, -1.4), 7.0, 1.4), "#120d18")
    img = c.finish()
    for x, y, col in ((-5, -2, "#ee5a2c"), (2, -1, "#f9a33a"), (6, -2, "#ee5a2c"), (-1, -2, "#ffe08c")):
        img.putpixel((12 + x, 4 + y), Image.new("RGBA", (1, 1), col).getpixel((0, 0)))
    return img


def main() -> None:
    if "--options" in sys.argv:
        options_sheet(os.path.join(DOCS_PREVIEW, "acampamento", "barraca_opcoes.png"))
        for key, tent in tents().items():
            save(tent, "sprites", "props", f"camp_tent_{key.lower()}.png")
        print("barracas (opcoes): ok")
        return
    save(tents()["C"], "sprites", "props", "camp_tent.png")
    save(bowl(), "sprites", "props", "camp_bowl.png")
    save(ball(), "sprites", "props", "camp_ball.png")
    save(scorch(), "sprites", "props", "camp_scorch.png")
    print("acampamento: ok")


if __name__ == "__main__":
    main()
