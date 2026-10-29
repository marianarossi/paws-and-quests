from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw

T = 6
SKY = (24, 30, 52)
TILE = {
    "#": (74, 92, 84), "=": (150, 110, 70), "~": (196, 160, 110), "W": (60, 110, 170),
    "^": (230, 60, 160), "v": (230, 60, 160), "<": (230, 60, 160), ">": (230, 60, 160),
}
MARK = {
    "P": ((120, 230, 120), "box"), "C": ((255, 140, 40), "fire"), "*": ((90, 170, 255), "dot"),
    "M": ((120, 230, 210), "dot"),
    "acorn": ((200, 140, 70), "dot"), "bat": ((170, 110, 230), "tri"), "bronte": ((255, 200, 60), "box"),
    "emitter": ((240, 240, 255), "cloud"), "mover": ((150, 110, 70), "bar"), "hint": ((255, 240, 120), "dot"),
    "mine": ((255, 70, 150), "dot"), "beam": ((255, 70, 150), "box"),
    "toad": ((110, 220, 90), "box"), "crab": ((90, 150, 240), "box"), "eye": ((255, 120, 200), "cloud"),
    "fall": ((234, 223, 208), "bar"), "beat": ((252, 211, 164), "bar"), "step": ((247, 175, 208), "bar"),
    "feather": ((240, 200, 96), "dot"), "archer": ((255, 225, 230), "tri"), "minotaur": ((170, 90, 60), "box"),
    "skeleton": ((220, 220, 200), "box"), "gust": ((180, 230, 255), "cloud"), "nimbus": ((255, 190, 230), "cloud"),
    "glow": ((255, 250, 220), "cloud"),
}
LEGEND = [("P", "inicio"), ("C", "fogueira"), ("*", "pata"), ("acorn", "Balanos"), ("bat", "morcego"),
          ("bronte", "Bronte"), ("emitter", "nuvenzinha"), ("toad", "sapo"), ("crab", "caranguejo"), ("eye", "olho"), ("mine", "mina"), ("^", "espinhos"), ("W", "agua"), ("~", "laje"), ("hint", "dica"),
          ("fall", "laje que cai"), ("beat", "nuvem ao ritmo"), ("step", "nuvem rosa"), ("feather", "marshmallow"),
          ("archer", "cupido"), ("minotaur", "minotauro"), ("skeleton", "Spartoi"), ("gust", "Boreas"), ("nimbus", "Nephele")]


def load(path: str) -> tuple[str, list[str], dict]:
    text = open(path, encoding="utf-8").read().replace("\r", "")
    parts = text.split("---")
    rows = [r for r in parts[1].strip("\n").split("\n")]
    width = max(len(r) for r in rows)
    kinds = {}
    for line in (parts[2] if len(parts) > 2 else "").split("\n"):
        if ":" in line and not line.startswith(";"):
            letter, rest = line.split(":", 1)
            kinds[letter.strip()] = rest.split()[0] if rest.split() else ""
    return os.path.basename(path)[:-5], [r.ljust(width, ".") for r in rows], kinds


def mark(d: ImageDraw.ImageDraw, x: int, y: int, color: tuple, shape: str) -> None:
    cx, cy = x * T + T // 2, y * T + T // 2
    if shape == "box":
        d.rectangle([cx - 4, cy - 6, cx + 4, cy + 2], fill=color, outline=(0, 0, 0))
    elif shape == "fire":
        d.polygon([(cx, cy - 8), (cx + 4, cy + 3), (cx - 4, cy + 3)], fill=color, outline=(0, 0, 0))
    elif shape == "tri":
        d.polygon([(cx - 5, cy - 3), (cx + 5, cy - 3), (cx, cy + 4)], fill=color, outline=(0, 0, 0))
    elif shape == "cloud":
        d.ellipse([cx - 7, cy - 4, cx + 7, cy + 4], fill=color, outline=(0, 0, 0))
    elif shape == "bar":
        d.rectangle([x * T, cy - 2, x * T + T, cy + 2], fill=color)
    else:
        d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=color, outline=(0, 0, 0))


def draw_room(name: str, rows: list[str], kinds: dict) -> Image.Image:
    h, w = len(rows), len(rows[0])
    body = Image.new("RGB", (w * T, h * T), SKY)
    d = ImageDraw.Draw(body)
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c in TILE:
                d.rectangle([x * T, y * T, x * T + T - 1, y * T + T - 1], fill=TILE[c])
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            key = c if c in MARK else kinds.get(c)
            if key in MARK:
                mark(d, x, y, *MARK[key])
    img = Image.new("RGB", (body.width, body.height + 14), (12, 14, 24))
    ImageDraw.Draw(img).text((4, 2), name, fill=(255, 255, 255))
    img.paste(body, (0, 14))
    return img


def legend(width: int) -> Image.Image:
    rows = 1 + sum(20 + 7 * len(label) for _, label in LEGEND) // max(1, width - 12)
    img = Image.new("RGB", (width, 22 * rows), (12, 14, 24))
    d = ImageDraw.Draw(img)
    x, y0 = 6, 0
    for key, label in LEGEND:
        if x + 20 + 7 * len(label) > width:
            x, y0 = 6, y0 + 22
        d = ImageDraw.Draw(img)
        if key in MARK:
            color, shape = MARK[key]
            mark(d, x // T, 2 + y0 // T, color, shape)
        else:
            d.rectangle([x, y0 + 10, x + T, y0 + 10 + T], fill=TILE[key])
        d.text((x + 10, y0 + 6), label, fill=(230, 230, 230))
        x += 20 + 7 * len(label)
    return img


def main() -> None:
    out, paths = sys.argv[1], sys.argv[2:]
    rooms = [draw_room(*load(p)) for p in paths]
    width = max(r.width for r in rooms)
    parts = rooms + [legend(width)]
    sheet = Image.new("RGB", (width, sum(p.height + 4 for p in parts)), (0, 0, 0))
    y = 0
    for p in parts:
        sheet.paste(p, (0, y))
        y += p.height + 4
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    sheet.save(out)
    print("mapa:", out, sheet.size)


if __name__ == "__main__":
    main()
