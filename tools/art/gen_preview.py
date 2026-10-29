from __future__ import annotations

import os

from PIL import Image

from vec import ASSETS, DOCS_PREVIEW, ROOT, rgba


def asset(*parts: str) -> Image.Image:
    return Image.open(os.path.join(ASSETS, *parts)).convert("RGBA")


PAW = [
    "......xx....xx......",
    ".....xxxx..xxxx.....",
    ".....xxxx..xxxx.....",
    ".xx...xx....xx...xx.",
    "xxxx............xxxx",
    "xxxx....xxxx....xxxx",
    ".xx...xxxxxxxx...xx.",
    ".....xxxxxxxxxx.....",
    "....xxxxxxxxxxxx....",
    "....xxxxxxxxxxxx....",
    "....xxxxxxxxxxxx....",
    ".....xxxxxxxxxx.....",
    "......xxx..xxx......",
]


def game_icon() -> Image.Image:
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    px = img.load()
    for y in range(32):
        for x in range(32):
            if (x in (0, 31) and y in (0, 1, 30, 31)) or (y in (0, 31) and x in (0, 1, 30, 31)):
                continue
            t = y / 31
            px[x, y] = (round(20 + 22 * t), round(36 + 50 * t), round(72 + 46 * t), 255)
    for x, y in ((4, 4), (9, 7), (25, 3), (28, 9), (15, 3), (21, 6)):
        px[x, y] = rgba("#d6fff2")
    for y in range(12, 32):
        half = (y - 12) * 0.95
        for x in range(32):
            if abs(x - 20.5) <= half and px[x, y][3]:
                px[x, y] = rgba("#c9c2ee" if y < 16 else "#54447f" if x < 20.5 - half * 0.25 else "#3a2d5c")
    ox, oy = 6, 11
    for j, row in enumerate(PAW):
        for i, ch in enumerate(row):
            if ch == "x":
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    px[ox + i + dx, oy + j + dy] = rgba("#1c1433")
    for j, row in enumerate(PAW):
        for i, ch in enumerate(row):
            if ch == "x":
                lit = j == 0 or PAW[j - 1][i] != "x"
                low = j == len(PAW) - 1 or PAW[j + 1][i] != "x"
                px[ox + i, oy + j] = rgba("#fff3c4" if lit else "#e8853a" if low else "#ffc46a")
    return img


def main() -> None:
    os.makedirs(DOCS_PREVIEW, exist_ok=True)
    hero = asset("sprites", "hero", "hero.png")
    decor = asset("sprites", "decor", "forest_decor.png")
    fire = asset("sprites", "props", "campfire.png")
    dog = asset("sprites", "dog", "dog_concept.png")
    sheet = Image.new("RGBA", (max(hero.width, decor.width + 24 + fire.width), hero.height + 16 + max(decor.height + 56, fire.height + dog.height + 8)), rgba("#3a7a84"))
    sheet.alpha_composite(hero)
    sheet.alpha_composite(decor, (8, hero.height + 8))
    sheet.alpha_composite(fire, (decor.width + 24, hero.height + 8))
    sheet.alpha_composite(dog, (decor.width + 72, hero.height + 16 + fire.height))
    x = 8
    for name in ("spikes", "spring_lilac", "crumble", "dash_crystal"):
        prop = asset("sprites", "props", name + ".png")
        sheet.alpha_composite(prop, (x, hero.height + 16 + decor.height))
        x += prop.width + 8
    sheet.resize((sheet.width * 4, sheet.height * 4), Image.NEAREST).save(os.path.join(DOCS_PREVIEW, "sprites.png"))

    game_icon().resize((128, 128), Image.NEAREST).save(os.path.join(ROOT, "icon.png"))
    print("pre-visualizacoes: ok")


if __name__ == "__main__":
    main()
