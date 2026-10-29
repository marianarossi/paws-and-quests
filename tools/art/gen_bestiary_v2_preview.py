from __future__ import annotations

import io
import json
import os
import subprocess

from PIL import Image

import bestiary_land
import bestiary_sky
from bestiary_kit import CREATURES, KL, WHITE, Pen
from vec import ROOT, rgba

V1 = {c["id"]: dict(c) for c in CREATURES}
import bestiary_v2
from gen_bestiary import write
V2 = {c["id"]: c for c in CREATURES}

PICKS = [("empusa_bat", "TWILIGHT GROVE"), ("bronte", "TWILIGHT GROVE"), ("miasma_toad", "GLIMMER HOLLOW"),
         ("karkinos", "GLIMMER HOLLOW"), ("arges_eye", "GLIMMER HOLLOW"), ("erote_archer", "OLIMPO"),
         ("minotaur_calf", "OLIMPO"), ("spartoi", "QUALQUER MAPA")]
OUT = os.path.join(ROOT, "docs", "preview", "inimigos")
BG, BAND1, BAND2 = "#191d38", "#3d4a78", "#35416c"


def frames(cr: dict) -> list[tuple[str, list[Image.Image], int, bool]]:
    out = []
    for name, spec in cr["anims"].items():
        imgs = []
        for i in range(spec["frames"]):
            p = Pen(cr["size"][0], cr["size"][1], cr["origin"])
            cr["draw"](p, name, i, spec["frames"])
            imgs.append(p.done())
        out.append((name, imgs, spec["fps"], spec.get("loop", True)))
    return out


def wisp_rows(img: Image.Image) -> list[tuple[str, list[Image.Image], int, bool]]:
    meta = {"idle": (0, 4, 5, True), "charge": (1, 4, 8, False), "fire": (2, 2, 12, False)}
    return [(name, [img.crop((i * 24, row * 24, i * 24 + 24, row * 24 + 24)) for i in range(n)], fps, loop)
            for name, (row, n, fps, loop) in meta.items()]


def old_wisp() -> Image.Image:
    data = subprocess.run(["git", "show", "inimigos-v1:assets/sprites/combat/wisp.png"], cwd=ROOT,
                          capture_output=True, check=True).stdout
    return Image.open(io.BytesIO(data)).convert("RGBA")


def entries() -> list[tuple[str, str, list, list, tuple[int, int]]]:
    out = []
    for cid, zone in PICKS:
        out.append((V2[cid]["name"], zone, frames(V1[cid]), frames(V2[cid]), tuple(V2[cid]["size"])))
    new_wisp = Image.open(os.path.join(ROOT, "assets", "sprites", "combat", "wisp.png")).convert("RGBA")
    out.append(("Nuvenzinha", "FAISCAS", wisp_rows(old_wisp()), wisp_rows(new_wisp), (24, 24)))
    return out


def comparison(items) -> None:
    label, scale = 118, 3
    row_h = 40
    width = label + max(sum(len(f) * (sz[0] + 1) + 8 for _, f, _, _ in rows) for _, _, a, b, sz in items for rows in (a, b)) + 6
    height = 14 + len(items) * (row_h * 2 + 4)
    img = Image.new("RGBA", (width, height), rgba(BG))
    write(img, 6, 3, "INIMIGOS V2  -  EM CIMA A V1, EM BAIXO A V2", "#9fb0e0")
    y = 14
    for k, (name, zone, a, b, size) in enumerate(items):
        for r, rows in enumerate((a, b)):
            band = Image.new("RGBA", (width, row_h), rgba(BAND1 if r else BAND2))
            img.paste(band, (0, y))
            if r == 0:
                write(img, 6, y + 6, name, WHITE)
                write(img, 6, y + 18, zone, "#aebbe8")
            write(img, label - 18, y + 14, "V2" if r else "V1", KL if r else "#7d88b8")
            x = label
            for anim, imgs, _, _ in rows:
                write(img, x, y + 1, anim, "#7d88b8")
                for f in imgs:
                    img.paste(f, (x, y + 7 + (32 - f.height)), f)
                    x += size[0] + 1
                x += 8
            y += row_h
        y += 4
    img.resize((img.width * scale, img.height * scale), Image.NEAREST).save(os.path.join(OUT, "v2_comparacao.png"))


def gif(items) -> None:
    cols, cw, ch, scale, tick = 3, 110, 56, 3, 60
    rows = (len(items) + cols - 1) // cols
    lines = []
    for name, zone, _, b, size in items:
        seq = []
        for anim, imgs, fps, loop in b:
            hold = max(1, round(1000 / tick / fps))
            for _ in range(2 if loop else 1):
                for f in imgs:
                    seq += [f] * hold
            if not loop:
                seq += [imgs[-1]] * 6
        lines.append(seq)
    length = max(len(s) for s in lines)
    base = Image.new("RGBA", (cols * cw, rows * ch), rgba(BAND2))
    for k, (name, zone, _, _, size) in enumerate(items):
        x0, y0 = (k % cols) * cw, (k // cols) * ch
        if (k % cols + k // cols) % 2 == 0:
            base.paste(Image.new("RGBA", (cw, ch), rgba(BAND1)), (x0, y0))
        write(base, x0 + 4, y0 + ch - 10, name, "#c9d3f4")
    out = []
    for t in range(length):
        frame = base.copy()
        for k, (name, zone, _, _, size) in enumerate(items):
            seq = lines[k]
            f = seq[t % len(seq)]
            x0, y0 = (k % cols) * cw, (k // cols) * ch
            frame.paste(f, (x0 + (cw - f.width) // 2, y0 + 8 + (32 - f.height)), f)
        out.append(frame.resize((frame.width * scale, frame.height * scale), Image.NEAREST)
                   .convert("P", palette=Image.ADAPTIVE, colors=255))
    out[0].save(os.path.join(OUT, "v2.gif"), save_all=True, append_images=out[1:], duration=tick, loop=0)


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    items = entries()
    comparison(items)
    gif(items)
    print("inimigos v2: comparacao e gif")


if __name__ == "__main__":
    main()
