from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFont

import gen_hero as g
from vec import DOCS_PREVIEW

F = g.FRAME
MIST, GRASS, STONE, EDGE, DARK = (104, 168, 160, 255), (62, 214, 176, 255), (58, 48, 92, 255), (92, 80, 134, 255), (30, 42, 60, 255)
ROWS = {name: (row, len(poses)) for row, (name, _, _, poses) in enumerate(g.ANIMS)}
try:
    FONT = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 15)
except OSError:
    FONT = ImageFont.load_default()


def frame(sheet: Image.Image, anim: str, index: int) -> Image.Image:
    row, count = ROWS[anim]
    index %= count
    return sheet.crop((index * F, row * F, (index + 1) * F, (row + 1) * F))


def still(sheet: Image.Image) -> None:
    scale, pad = 6, 2
    lines = [
        ("parado | correr | correr | arranque do pulo | subida | cimo | queda | aterragem",
         [("idle", 0), ("run", 0), ("run", 2), ("jump", 0), ("jump", 1), ("apex", 0), ("fall", 0), ("land", 0)]),
        ("parede | dash de lado | dash para cima | dash para baixo | empurrar | sentado | agachado",
         [("wall_slide", 0), ("dash", 0), ("dash_up", 0), ("dash_down", 0), ("push", 0), ("sit", 0), ("crouch", 0)]),
    ]
    img = Image.new("RGBA", (8 * (F + pad), len(lines) * (F + 8)), MIST)
    d = ImageDraw.Draw(img)
    for j, (_, cells) in enumerate(lines):
        y0 = j * (F + 8)
        d.rectangle([0, y0 + F - 1, img.width, y0 + F + 8], fill=STONE)
        d.rectangle([0, y0 + F - 1, img.width, y0 + F], fill=GRASS)
        for i, (anim, index) in enumerate(cells):
            img.alpha_composite(frame(sheet, anim, index), (i * (F + pad), y0))
    big = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    d = ImageDraw.Draw(big)
    for j, (label, _) in enumerate(lines):
        d.text((8, (j * (F + 8) + F + 2) * scale), label, fill=(255, 255, 255, 255), font=FONT)
    big.save(os.path.join(DOCS_PREVIEW, "personagem_final.png"))


CELL_W, CELL_H, FLOOR, SCALE, TICK_MS, TICKS = 46, 100, 92, 4, 70, 72
JUMP_Y = [0, 0, 0, 4, 19, 32, 41, 46, 48, 48, 47, 41, 30, 16, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
LABELS = ["parado", "correr", "pular e aterrar", "deslizar na parede", "dash", "sentado e agachado", "empurrar parede"]


def cell(sheet: Image.Image, column: int, tick: int) -> tuple[Image.Image, int, str, bool]:
    if column == 0:
        return frame(sheet, "idle", tick // 2), 0, "", False
    if column == 1:
        return frame(sheet, "run", tick), 0, "", False
    if column == 2:
        t = tick % 24
        if t < 3 or t >= 16:
            return frame(sheet, "idle", 0), 0, "", False
        if t == 3:
            return frame(sheet, "jump", 0), JUMP_Y[t], "", False
        if t <= 7:
            return frame(sheet, "jump", 1), JUMP_Y[t], "", False
        if t <= 9:
            return frame(sheet, "apex", t - 8), JUMP_Y[t], "", False
        if t <= 13:
            return frame(sheet, "fall", t), JUMP_Y[t], "", False
        return frame(sheet, "land", t - 14), 0, "", False
    if column == 3:
        return frame(sheet, "wall_slide", tick // 2), 14, "", True
    if column == 4:
        t = tick % 18
        anim, name = (("dash", "lado"), ("dash_up", "cima"), ("dash_down", "baixo"))[t // 6]
        return frame(sheet, anim, t), 12, name, False
    if column == 5:
        t = tick % 24
        if t < 12:
            return frame(sheet, "sit", t // 6), 0, "sentado", False
        return frame(sheet, "crouch", t // 4), 0, "agachado", False
    return frame(sheet, "push", tick // 3), 0, "", True


def animated(sheet: Image.Image) -> None:
    frames = []
    w = CELL_W * len(LABELS)
    for tick in range(TICKS):
        img = Image.new("RGBA", (w, CELL_H), MIST)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, w, 10], fill=DARK)
        d.rectangle([0, FLOOR, w, CELL_H], fill=STONE)
        d.rectangle([0, FLOOR, w, FLOOR + 1], fill=GRASS)
        notes = []
        for col in range(len(LABELS)):
            x0 = col * CELL_W
            sprite, lift, note, wall = cell(sheet, col, tick)
            if col == 1:
                for k in range(-1, 4):
                    mx = x0 + k * 16 - (tick * 5) % 16
                    if x0 <= mx < x0 + CELL_W - 2:
                        d.rectangle([mx, FLOOR + 3, mx + 2, FLOOR + 4], fill=EDGE)
            if wall:
                wx = x0 + CELL_W // 2 + 4
                d.rectangle([wx, 11, x0 + CELL_W - 1, FLOOR + 1], fill=STONE)
                d.rectangle([wx, 11, wx, FLOOR - 1], fill=EDGE)
            img.alpha_composite(sprite, (x0 + CELL_W // 2 - F // 2, FLOOR - F - lift))
            if col:
                d.rectangle([x0, 0, x0, CELL_H - 1], fill=DARK)
            notes.append((x0, note))
        big = img.resize((w * SCALE, CELL_H * SCALE), Image.NEAREST)
        d = ImageDraw.Draw(big)
        for col, label in enumerate(LABELS):
            d.text((col * CELL_W * SCALE + 8, 6), label, fill=(255, 255, 255, 255), font=FONT)
        for x0, note in notes:
            if note:
                d.text((x0 * SCALE + 8, 46), note, fill=(40, 30, 70, 255), font=FONT)
        frames.append(big.convert("RGB"))
    palette = frames[5].quantize(colors=255, dither=Image.Dither.NONE)
    frames = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
    frames[0].save(os.path.join(DOCS_PREVIEW, "personagem_animacoes.gif"), save_all=True, append_images=frames[1:],
                   duration=TICK_MS, loop=0, optimize=True)


def main() -> None:
    os.makedirs(DOCS_PREVIEW, exist_ok=True)
    sheet = g.build()[0]
    still(sheet)
    animated(sheet)
    print("pre-visualizacao do personagem: ok")


if __name__ == "__main__":
    main()
