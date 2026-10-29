from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw, ImageFont

import gen_dog as g
from vec import DOCS_PREVIEW

F = g.FRAME
BG, GROUND, EDGE = (70, 84, 110, 255), (52, 120, 84, 255), (36, 70, 52, 255)
NAMES = {
    "idle": "parado", "pant": "ofegar", "walk": "andar", "run": "correr", "jump": "pulo",
    "fall": "queda", "land": "aterragem", "sit": "sentado", "lie": "deitado",
    "sleep": "dormir", "bark": "latir", "sniff": "farejar", "happy": "alegria",
}
try:
    FONT = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 14)
except OSError:
    FONT = ImageFont.load_default()
OUT = os.path.join(DOCS_PREVIEW, "cachorro")
PREFIX = "cachorro"


def cell(sheet: Image.Image, row: int, col: int) -> Image.Image:
    return sheet.crop((col * F, row * F, col * F + F, row * F + F))


def ground(img: Image.Image, y: int) -> None:
    d = ImageDraw.Draw(img)
    d.rectangle((0, y, img.width, y), fill=EDGE)
    d.rectangle((0, y + 1, img.width, img.height), fill=GROUND)


def still(sheet: Image.Image, meta: dict, hero: Image.Image) -> None:
    scale, label_h = 5, 20
    cols = g.COLS + 1
    rows = len(meta["animations"])
    img = Image.new("RGBA", (cols * F * scale, rows * (F * scale + label_h)), BG)
    d = ImageDraw.Draw(img)
    for name, a in meta["animations"].items():
        y0 = a["row"] * (F * scale + label_h)
        strip = Image.new("RGBA", (cols * F, F - 4), BG)
        ground(strip, F - 5)
        strip.alpha_composite(hero.crop((0, 4, F, F)), (0, 0))
        for c in range(a["frames"]):
            strip.alpha_composite(cell(sheet, a["row"], c).crop((0, 4, F, F)), ((c + 1) * F, 0))
        img.alpha_composite(strip.resize((strip.width * scale, strip.height * scale), Image.NEAREST),
                            (0, y0 + label_h))
        d.text((6, y0 + 2), "%s (%s) - %d quadros, %d fps" % (NAMES.get(name, name), name, a["frames"], a["fps"]),
               fill=(240, 236, 228, 255), font=FONT)
    img.save(os.path.join(OUT, PREFIX + "_folha.png"))


def gif(sheet: Image.Image, meta: dict, hero: Image.Image) -> None:
    scale, per_row, label_h = 4, 5, 16
    anims = list(meta["animations"].items())
    nrows = (len(anims) + per_row - 1) // per_row
    cw, ch = F * scale, F * scale + label_h
    tick, total = 0.02, 4.0
    frames = []
    for k in range(int(total / tick)):
        t = k * tick
        img = Image.new("RGBA", (per_row * cw, nrows * ch), BG)
        d = ImageDraw.Draw(img)
        for i, (name, a) in enumerate(anims):
            n = a["frames"]
            idx = int(t * a["fps"])
            idx = idx % n if a["loop"] else min(idx % (n + 6), n - 1)
            box = Image.new("RGBA", (F, F), BG)
            ground(box, F - 1)
            box.alpha_composite(cell(sheet, a["row"], idx))
            x, y = (i % per_row) * cw, (i // per_row) * ch
            img.alpha_composite(box.resize((cw, cw), Image.NEAREST), (x, y + label_h))
            d.text((x + 4, y + 1), NAMES.get(name, name), fill=(240, 236, 228, 255), font=FONT)
        frames.append(img.convert("RGB").convert("P", palette=Image.ADAPTIVE, colors=64))
    out, durs = [frames[0]], [20]
    for f in frames[1:]:
        if f.tobytes() == out[-1].tobytes():
            durs[-1] += 20
        else:
            out.append(f)
            durs.append(20)
    out[0].save(os.path.join(OUT, PREFIX + ".gif"), save_all=True, append_images=out[1:],
                duration=durs, loop=0, disposal=1)


def main() -> None:
    global PREFIX
    os.makedirs(OUT, exist_ok=True)
    if "--zeus" in sys.argv:
        import gen_dog_zeus
        gen_dog_zeus.use()
        PREFIX = "zeus"
    sheet, meta = g.build()
    hero = Image.open(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "sprites", "hero",
                                   "hero.png")).convert("RGBA").crop((0, 0, F, F))
    still(sheet, meta, hero)
    gif(sheet, meta, hero)
    print("previa do cachorro: ok")


if __name__ == "__main__":
    main()
