from __future__ import annotations

import math
import os
import sys
import unicodedata

from PIL import Image

import bestiary_land
import bestiary_sky
import bestiary_v2
import bestiary_v3
from bestiary_kit import CREATURES, HOT, K, KD, KL, OUT, WHITE, Pen, body_center, hurt_of, wave
from gen_enemies import poof_frame
from gen_font import GLYPHS, HEIGHT
from vec import DOCS_PREVIEW, rgba, save, save_json

PREVIEW = os.path.join(DOCS_PREVIEW, "inimigos")
TICK_MS = 60
WATER = (63, 127, 208, 120)


def render(cr: dict, anim: str, i: int) -> Image.Image:
    p = Pen(cr["size"][0], cr["size"][1], cr["origin"])
    cr["draw"](p, anim, i, cr["anims"][anim]["frames"])
    return p.done()


def frames_of(cr: dict) -> dict[str, list[Image.Image]]:
    out = {name: [render(cr, name, i) for i in range(spec["frames"])] for name, spec in cr["anims"].items()}
    w, h = cr["size"]
    hurt = hurt_of(out["move"][0])
    cx, cy = body_center(out["move"][0])
    die = [hurt]
    for step in range(3):
        frame = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        puff = poof_frame(24, 24, step)
        frame.paste(puff, (max(0, min(w - 24, cx - 12)), max(0, min(h - 24, cy - 13))), puff)
        die.append(frame)
    out["hurt"] = [hurt]
    out["die"] = die
    return out


def write_sheet(cr: dict, frames: dict[str, list[Image.Image]]) -> None:
    w, h = cr["size"]
    cols = max(len(f) for f in frames.values())
    sheet = Image.new("RGBA", (cols * w, len(frames) * h), (0, 0, 0, 0))
    table = {}
    for row, (name, imgs) in enumerate(frames.items()):
        for i, img in enumerate(imgs):
            sheet.paste(img, (i * w, row * h))
        spec = cr["anims"].get(name, {"fps": 1 if name == "hurt" else 14, "loop": False})
        table[name] = {"row": row, "frames": len(imgs), "fps": spec["fps"], "loop": bool(spec.get("loop", False))}
    save(sheet, "sprites", "enemies", cr["id"] + ".png")
    save_json({"image": cr["id"] + ".png", "frame_w": w, "frame_h": h, "scale": 1.0, "name": cr["name"],
               "theme": cr["theme"], "tier": cr["tier"], "feet": [cr["origin"][0], cr["origin"][1]],
               "animations": table}, "sprites", "enemies", cr["id"] + ".json")


def _shot(w: int, h: int, draw) -> Image.Image:
    p = Pen(w, h, (w / 2, h / 2))
    draw(p)
    return p.done()


def shots() -> dict[str, tuple[list[Image.Image], int]]:
    out: dict[str, tuple[list[Image.Image], int]] = {}

    def glob(i):
        def d(p):
            p.oval((0, 0), 3.2 + (i % 2) * 0.5, 3.2 - (i % 2) * 0.5, K)
            p.oval((-2.6 - i, 1.4), 1.3, 1.0, KD)
            p.dot((-1, -2), KL, 2, 1)
            p.dot((1, -1), WHITE)
        return d
    out["poison_glob"] = ([_shot(12, 12, glob(i)) for i in range(2)], 8)

    def miasma(i):
        def d(p):
            r = (5, 8, 10.5)[i]
            for y in range(-12, 12):
                for x in range(-12, 12):
                    q = math.hypot(x + 0.5, (y + 0.5) * 1.15) + wave(x * 3 + y * 5, 7, 1.2)
                    if q < r and (x + y) % 2 == 0:
                        p.glow((x, y), KL if q < r * 0.45 else (K if q < r * 0.8 else KD))
                    elif q < r * 0.5 and i < 2:
                        p.glow((x, y), K)
        return d
    out["miasma"] = ([_shot(24, 24, miasma(i)) for i in range(3)], 5)

    def missile(i):
        def d(p):
            p.tri((-3, -3.4), (-6.4, -5), (-5, -1.4), "#2c3a66")
            p.tri((-3, 3.4), (-6.4, 5), (-5, 1.4), "#2c3a66")
            p.limb((-4, 0), (2.4, 0), 2.5, "#4a5f96")
            p.oval((3.4, 0), 2.6, 2.4, K)
            p.dot((-2, -2), "#93ace6", 4, 1)
            p.dot((0, -1), WHITE, 2, 2)
            p.dot((1, 0), OUT)
            p.dot((4, -1), KL)
            for k in range(3 + i):
                p.glow((-8 - k, (k * (1 if i else -1)) % 2 - 1), WHITE if k < 1 else (KL if k < 3 else K))
                p.glow((-8 - k * 0.6, k % 2), KL)
        return d
    out["missile"] = ([_shot(20, 12, missile(i)) for i in range(2)], 12)

    def arrow(i):
        def d(p):
            for k in range(5):
                p.glow((-10 - k * 2, (k + i) % 2 - 0.5), KL if k < 2 else K)
            p.line((-7, 0), (4, 0), "#f4ead0")
            p.tri((3, -2.6), (7.6, 0.5), (3, 3.4), K)
            p.dot((5, 0), KL)
            p.tri((-8, -3), (-4.4, 0), (-8, 0.4), "#a9c0f4")
            p.tri((-8, 3.6), (-4.4, 0.6), (-8, 0.6), "#a9c0f4")
        return d
    out["arrow"] = ([_shot(40, 8, arrow(i)) for i in range(2)], 12)

    def feather(i):
        def d(p):
            with p.pose(rot=(-12, 12)[i]):
                p.blob([(-5, 0), (-1, -2.6), (4, -1.4), (5.4, 0.4), (3, 1.8), (-2, 2)], "#2f8f8a", 1)
                p.line((-4, 0), (4, 0), "#86e6cc")
                p.dot((5, 0), K, 2, 1)
        return d
    out["feather"] = ([_shot(14, 8, feather(i)) for i in range(2)], 10)

    def blade(i):
        def d(p):
            p.blob([(0, -5), (2.2, -2), (1.4, 3), (0, 5.6), (-1.4, 3), (-2.2, -2)], "#5a6f9a", 1)
            p.line((0 if i == 0 else -1, -4), (0, 3), "#cfdaf0")
            p.dot((-0.5, 5), K, 1, 2)
        return d
    out["blade_feather"] = ([_shot(8, 14, blade(i)) for i in range(2)], 10)

    def note(i):
        def d(p):
            r = (4.0, 7.0, 10.0)[i]
            for a in range(-56, 57, (14, 9, 7)[i]):
                x, y = -6 + r * math.cos(math.radians(a)), r * math.sin(math.radians(a))
                p.glow((x, y), KL)
                p.glow((x - 1, y), K if i < 2 else KD)
        return d
    out["note_ring"] = ([_shot(12, 24, note(i)) for i in range(3)], 8)

    def spear(p):
        p.line((-9, 0), (5, 0), "#b98458")
        p.dot((-9, 0), "#f1ebdd", 2, 1)
        p.tri((5, -2.4), (9.6, 0.5), (5, 3.2), K)
        p.dot((7, 0), KL)
    out["bone_spear"] = ([_shot(22, 8, spear)], 1)

    def flame(i):
        def d(p):
            lick = (0.0, 1.0, -1.0)[i]
            p.blob([(-6, 0), (-2, -3.6 - lick), (2, -2), (6.6, lick), (2, 2.4), (-2, 3.6 + lick)], K, 2)
            p.blob([(-5, 0), (-1.6, -2.2), (2, -0.8), (4.4, lick * 0.6), (1.6, 1.2), (-1.6, 2.2)], KL, 2)
            p.oval((-2.4, 0), 2.0, 1.2, WHITE)
            p.glow((7 + i % 2, -2 + i), KL)
        return d
    out["flame"] = ([_shot(18, 12, flame(i)) for i in range(3)], 12)

    def icicle(turn):
        def d(p):
            for a in range(3):
                ang = a * math.pi / 3 + turn
                dx, dy = math.cos(ang) * 4.5, math.sin(ang) * 4.5
                p.line((-dx, -dy), (dx, dy), WHITE)
            p.dot((0, 0), K)
        return d
    out["icicle"] = ([_shot(12, 12, icicle(t)) for t in (0.0, math.pi / 6)], 8)

    def bolt(i):
        def d(p):
            pts = [(0, -16), (2.4, -11), (-1.6, -6), (2.0, -1), (-2.0, 4), (1.6, 9), (0, 16)]
            if i:
                pts = [(-x, y) for x, y in pts]
            for a, b in zip(pts, pts[1:]):
                p.line((a[0] - 1, a[1]), (b[0] - 1, b[1]), K, glow=True)
                p.line((a[0] + 1, a[1]), (b[0] + 1, b[1]), KL, glow=True)
                p.line(a, b, WHITE, glow=True)
        return d
    out["bolt"] = ([_shot(12, 32, bolt(i)) for i in range(2)], 14)

    def bomb(i):
        def d(p):
            bestiary_v3.thunder_bomb(p, (-0.5, 1.0), 3.2, i)
        return d
    out["thunder_bomb"] = ([_shot(14, 14, bomb(i)) for i in range(3)], 12)
    return out


def write_shots() -> dict[str, tuple[list[Image.Image], int]]:
    table = shots()
    width = max(sum(f.width for f in fr) for fr, _ in table.values())
    height = sum(fr[0].height for fr, _ in table.values())
    atlas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    meta, y = {}, 0
    for name, (fr, fps) in table.items():
        for i, f in enumerate(fr):
            atlas.paste(f, (i * f.width, y))
        meta[name] = {"x": 0, "y": y, "frame_w": fr[0].width, "frame_h": fr[0].height, "frames": len(fr), "fps": fps}
        y += fr[0].height
    save(atlas, "sprites", "enemies", "shots.png")
    save_json({"image": "shots.png", "shots": meta}, "sprites", "enemies", "shots.json")
    return table


def plain(text: str) -> str:
    text = unicodedata.normalize("NFD", text.upper())
    return "".join(c for c in text if c in GLYPHS or c == " ")


def write(img: Image.Image, x: int, y: int, text: str, color) -> int:
    px = img.load()
    col = rgba(color)
    for ch in plain(text):
        if ch == " ":
            x += 4
            continue
        rows = GLYPHS[ch]
        for j, row in enumerate(rows):
            for i, bit in enumerate(row):
                if bit == "#" and 0 <= x + i < img.width and 0 <= y + j < img.height:
                    px[x + i, y + j] = col
        x += len(rows[0]) + 1
    return x


def pips(img: Image.Image, x: int, y: int, tier: int) -> None:
    for k in range(3):
        col = rgba(KL if k < tier else "#222a50")
        for dx, dy in ((1, 0), (0, 1), (1, 1), (2, 1), (1, 2)):
            img.putpixel((x + k * 5 + dx, y + dy), col)


def sheet_preview(group: list[tuple[int, dict, dict]], path: str, title: str) -> None:
    label, row_h, scale = 122, 46, 3
    width = label + max(sum(len(fr[a]) * cr["size"][0] + 10 for a in cr["anims"]) for _, cr, fr in group) + 6
    img = Image.new("RGBA", (width, 16 + row_h * len(group)), rgba("#191d38"))
    write(img, 6, 4, title, "#9fb0e0")
    x = label
    for name in ("MOVE", "ATTACK", "EXTRA"):
        write(img, x, 4, name, "#5d6aa0")
        x += 150 if name == "MOVE" else 200
    for r, (num, cr, fr) in enumerate(group):
        y0 = 16 + r * row_h
        band = Image.new("RGBA", (width, row_h), rgba("#3d4a78" if r % 2 == 0 else "#35416c"))
        img.paste(band, (0, y0))
        write(img, 6, y0 + 6, "%02d" % num, KL)
        write(img, 24, y0 + 6, cr["name"], WHITE)
        write(img, 24, y0 + 18, cr["theme"], "#aebbe8")
        pips(img, 24, y0 + 30, cr["tier"])
        x = label
        w, h = cr["size"]
        for a in cr["anims"]:
            for f in fr[a]:
                if cr["water"]:
                    img.paste(Image.new("RGBA", (w, h - cr["origin"][1]), rgba("#2a4f9a")), (x, y0 + 7 + cr["origin"][1]))
                img.paste(f, (x, y0 + 7), f)
                x += w
            x += 10
    img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    img.save(path)


def timeline(cr: dict, fr: dict, length: int) -> list[tuple[Image.Image | None, int, int]]:
    def clip(name: str, loops: int = 1) -> list:
        spec = cr["anims"].get(name, {"fps": 2 if name == "hurt" else 12})
        hold = max(1, round(1000 / TICK_MS / spec["fps"]))
        path = spec.get("path")
        seq = []
        for _ in range(loops):
            for i, f in enumerate(fr[name]):
                dx, dy = path[i] if path else (0, 0)
                seq += [(f, dx, dy)] * hold
        return seq
    extras = [a for a in cr["anims"] if a not in ("move", "attack")]
    tail = (clip("attack") if "attack" in fr else []) + clip("move")
    for a in extras:
        tail += clip(a, 2 if cr["anims"][a]["loop"] else 1) + clip("move")
    tail += clip("hurt") + clip("die") + [(None, 0, 0)] * 8
    walk = clip("move")
    head = []
    while len(head) + len(tail) < length:
        head += walk
    return (head + tail)[-length:] if len(head) + len(tail) > length else head + tail


def gif_preview(items: list[tuple[int, dict, dict]], path: str) -> None:
    cols, cw, ch, scale = 4, 124, 60, 3
    rows = (len(items) + cols - 1) // cols
    length = max(len(timeline(cr, fr, 0)) for _, cr, fr in items) + 44
    lines = [timeline(cr, fr, length) for _, cr, fr in items]
    base = Image.new("RGBA", (cols * cw, rows * ch), rgba("#35416c"))
    for k, (num, cr, fr) in enumerate(items):
        x0, y0 = (k % cols) * cw, (k // cols) * ch
        if (k % cols + k // cols) % 2 == 0:
            base.paste(Image.new("RGBA", (cw, ch), rgba("#3d4a78")), (x0, y0))
        end = write(base, x0 + 4, y0 + ch - 10, "%02d" % num, KL)
        write(base, end + 3, y0 + ch - 10, cr["name"], "#c9d3f4")
        if cr["origin"][1] > cr["size"][1] - 3:
            base.paste(Image.new("RGBA", (cw - 16, 1), rgba("#242c54")), (x0 + 8, y0 + 7 + cr["size"][1]))
    out = []
    for t in range(length):
        frame = base.copy()
        for k, (num, cr, fr) in enumerate(items):
            f, dx, dy = lines[k][t]
            x0, y0 = (k % cols) * cw, (k // cols) * ch
            w, h = cr["size"]
            fx, fy = x0 + (cw - w) // 2 + dx - (7 if cr["anims"]["move"].get("path") else 0), y0 + 7 + dy
            if cr["water"]:
                frame.paste(Image.new("RGBA", (cw - 24, h - cr["origin"][1] + 4), rgba("#2a4f9a")), (x0 + 12, y0 + 7 + cr["origin"][1]))
            if f is not None:
                frame.paste(f, (fx, fy), f)
        out.append(frame.resize((frame.width * scale, frame.height * scale), Image.NEAREST).convert("P", palette=Image.ADAPTIVE, colors=255))
    out[0].save(path, save_all=True, append_images=out[1:], duration=TICK_MS, loop=0, optimize=False)


def shots_preview(table: dict, path: str) -> None:
    scale = 4
    img = Image.new("RGBA", (300, 12 + sum(max(14, fr[0].height + 4) for fr, _ in table.values())), rgba("#191d38"))
    write(img, 6, 3, "SHOTS", "#9fb0e0")
    y = 12
    for name, (fr, _) in table.items():
        row = max(14, fr[0].height + 4)
        write(img, 6, y + (row - HEIGHT) // 2, name.replace("_", " "), "#c9d3f4")
        for i, f in enumerate(fr):
            img.paste(f, (110 + i * (f.width + 6), y + (row - f.height) // 2), f)
        y += row
    img.resize((img.width * scale, img.height * scale), Image.NEAREST).save(path)


MOCK = [
    {"balanos": (150, 320), "spartoi": (224, 272), "styx_shade": (330, 120), "empusa_bat": (200, 96)},
    {"balanos": (100, 320), "karkinos": (224, 272), "miasma_toad": (300, 320), "nephele": (430, 130), "minotaur_calf": (344, 176)},
    {"bronte": (150, 320), "erote_archer": (440, 120), "harpy": (300, 70), "boreas_gust": (120, 150)},
    {"arges_eye": (300, 110)},
]


def mock_preview(captures: list[str], frames: dict[str, dict], path: str) -> None:
    by_id = {cr["id"]: cr for cr in CREATURES}
    tiles = []
    for capture, spots in zip(captures, MOCK):
        shot = Image.open(capture).convert("RGBA")
        scale = shot.width // 640
        for cid, (x, y) in spots.items():
            cr = by_id[cid]
            f = frames[cid]["hang" if cid == "empusa_bat" else "move"][0]
            f = f.resize((f.width * scale, f.height * scale), Image.NEAREST)
            ox, oy = cr["origin"]
            if oy < cr["size"][1] - 3 and not cr["water"]:
                oy = cr["size"][1] // 2
            shot.paste(f, ((x - ox) * scale, (y - 8 - oy) * scale), f)
        tiles.append(shot)
    w, h = tiles[0].size
    out = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 255))
    for k, tile in enumerate(tiles):
        out.paste(tile, ((k % 2) * w, (k // 2) * h))
    out.save(path)


def main() -> None:
    os.makedirs(PREVIEW, exist_ok=True)
    items = []
    frames = {}
    for num, cr in enumerate(CREATURES, 1):
        fr = frames_of(cr)
        write_sheet(cr, fr)
        frames[cr["id"]] = fr
        items.append((num, cr, fr))
    if "--mock" in sys.argv:
        k = sys.argv.index("--mock")
        mock_preview(sys.argv[k + 1:k + 5], frames, os.path.join(PREVIEW, "inimigos_nas_zonas.png"))
        print("bestiario: inimigos sobre as zonas")
        return
    table = write_shots()
    half = (len(items) + 1) // 2
    sheet_preview(items[:half], os.path.join(PREVIEW, "folha_1_chao.png"), "1 - GROUND")
    sheet_preview(items[half:], os.path.join(PREVIEW, "folha_2_ar_e_agua.png"), "2 - AIR")
    shots_preview(table, os.path.join(PREVIEW, "projeteis.png"))
    gif_preview(items, os.path.join(PREVIEW, "inimigos.gif"))
    print("bestiario: %d criaturas, %d projeteis" % (len(items), len(table)))


if __name__ == "__main__":
    main()
