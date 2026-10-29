from __future__ import annotations

import json
import os
import random

from PIL import Image, ImageDraw

import gen_hero as g
import gen_hero_look as look
from vec import rgba

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOOK_DIR = os.path.join(ROOT, "assets", "sprites", "hero", "look")
OUT = os.path.join(ROOT, "docs", "preview", "personalizar")
NIGHT = (24, 30, 52, 255)
SUNSET = (232, 150, 120, 255)
SCALE = 4
ANIM_ROW = {name: row for row, (name, _, _, _) in enumerate(g.ANIMS)}


def compose(shape: dict[str, str]) -> Image.Image:
    sheet = Image.open(os.path.join(LOOK_DIR, f"base_{shape['hat']}_{shape['beard']}.png")).convert("RGBA")
    if shape["glasses"] != "none":
        sheet.alpha_composite(Image.open(os.path.join(LOOK_DIR, f"glasses_{shape['glasses']}.png")).convert("RGBA"))
    if shape["scarf"] != "none":
        sheet.alpha_composite(Image.open(os.path.join(LOOK_DIR, f"scarf_{shape['beard']}.png")).convert("RGBA"))
    return sheet


def paint(sheet: Image.Image, meta: dict, pal: dict[str, str]) -> Image.Image:
    by_index = {i: rgba(pal[ch]) for ch, i in meta["index"].items()}
    out = Image.new("RGBA", sheet.size, (0, 0, 0, 0))
    src, dst = sheet.load(), out.load()
    for y in range(sheet.height):
        for x in range(sheet.width):
            r, _, _, a = src[x, y]
            if a:
                dst[x, y] = by_index[round(r / meta["step"])]
    return out


def frame(sheet: Image.Image, anim: str, col: int) -> Image.Image:
    f = g.FRAME
    row = ANIM_ROW[anim]
    return sheet.crop((col * f, row * f, col * f + f, row * f + f)).resize((f * SCALE, f * SCALE), Image.NEAREST)


def shape_of(**kw) -> dict[str, str]:
    return {"hat": "none", "beard": "full", "glasses": "none", "scarf": "none"} | kw


POSES = [("idle", 0), ("run", 2), ("fall", 0), ("dash", 0)]


def card(meta: dict, shape: dict, pal: dict, bg, label: str, poses=POSES) -> Image.Image:
    sheet = paint(compose(shape), meta, pal)
    w = g.FRAME * SCALE
    img = Image.new("RGBA", (w * len(poses), w + 14), bg)
    for i, (anim, col) in enumerate(poses):
        img.alpha_composite(frame(sheet, anim, col), (i * w, 14))
    ImageDraw.Draw(img).text((4, 2), label, fill=(255, 255, 255, 255))
    return img


def grid(cards: list[Image.Image], cols: int, bg=(12, 14, 24, 255)) -> Image.Image:
    w, h = cards[0].size
    rows = (len(cards) + cols - 1) // cols
    img = Image.new("RGBA", (cols * (w + 6) + 6, rows * (h + 6) + 6), bg)
    for i, c in enumerate(cards):
        img.alpha_composite(c, (6 + (i % cols) * (w + 6), 6 + (i // cols) * (h + 6)))
    return img


def main() -> None:
    meta = json.load(open(os.path.join(LOOK_DIR, "look.json"), encoding="utf-8"))
    os.makedirs(OUT, exist_ok=True)
    george = look.look_pal()
    with_acc = look.look_pal()
    n = 0
    cards = []
    for kind, ids in (("hat", look.HATS), ("beard", look.BEARDS), ("glasses", look.GLASSES), ("scarf", look.SCARVES)):
        for sid in ids:
            n += 1
            cards.append(card(meta, shape_of(**{kind: sid}), with_acc, NIGHT, f"{n}. {kind}: {sid}"))
    grid(cards, 3).save(os.path.join(OUT, "pecas.png"))

    cards = []
    one = [("idle", 0)]
    for piece, (_, options) in look.PIECES.items():
        shape = shape_of(hat="bucket" if piece == "hat_color" else "none",
                         scarf="scarf" if piece == "scarf_color" else "none")
        for oid, _, _ in options:
            cards.append(card(meta, shape, look.look_pal({piece: oid}), NIGHT, f"{piece[:6]} {oid[:8]}", one))
        cards += [Image.new("RGBA", cards[-1].size, (0, 0, 0, 0))] * (10 - len(options))
    grid(cards, 10).save(os.path.join(OUT, "paletas.png"))

    rnd = random.Random(7)
    cards = []
    for i in range(12):
        choice = {piece: rnd.choice(options)[0] for piece, (_, options) in look.PIECES.items()}
        shape = {k: rnd.choice(v) for k, v in (("hat", look.HATS), ("beard", look.BEARDS),
                                                 ("glasses", look.GLASSES), ("scarf", look.SCARVES))}
        cards.append(card(meta, shape, look.look_pal(choice), NIGHT if i % 2 == 0 else SUNSET, str(i + 1),
                          [("idle", 0), ("run", 2)]))
    grid(cards, 4).save(os.path.join(OUT, "aleatorios.png"))

    hero = Image.open(os.path.join(ROOT, "assets", "sprites", "hero", "hero.png")).convert("RGBA")
    mine = paint(compose(shape_of()), meta, george)
    assert list(hero.getdata()) == list(mine.getdata()), "a folha indexada não bate com hero.png"
    print("prévia da personalização: ok")


if __name__ == "__main__":
    main()
