from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFont

import gen_hero as g
from vec import ASSETS, DOCS_PREVIEW, rgba, save, save_json

EYE_LETTERS = set("eqf")
TICK = [0]

SHARK = [
    "...Y...",
    ".YYYY.Y",
    "YqYYYYY",
    ".yyyy.y",
]

NPCS = {
    "fisher": dict(
        name="Fisher (ref. 1)",
        hair="#5e4231", top=1, eye_rows=[7],
        head=[
            "..H..hH..H..",
            ".hHhhHHhhHh.",
            "uhhHhhhHhhH.",
            "uhhhhhhhhhh.",
            "uuhhhsShhSh.",
            "uhhhSSSSSSS.",
            "uhhzSSddSSSn",
            "uhhzSSeSSSnn",
            "uhgzSSSSSSn.",
            "uubbSSMMMM..",
            ".ubbbbMMMb..",
            "..bbbbbbb...",
        ],
        torso=[
            "KCCCCC",
            "KKCCCC",
            "QKCTCC",
            "QKCCCC",
            "QKCTCC",
            "QQCCCC",
            "QQCCCQ",
        ],
        back=(["K.", "KC", "KC", "CC"], (10, 17)),
        pal={
            "d": "#2a1d17", "e": "#2a1d17", "b": "#7a6658", "g": "#5b4a40", "M": "#2a1f1a", "B": "#7a6658",
            "s": "#dcc0aa", "S": "#ead3c0", "z": "#b79a87", "n": "#d4a48f",
            "C": "#3d4150", "K": "#595e70", "Q": "#282a38", "T": "#d8cfb8",
            "W": "#4a4e5e", "v": "#2e3040",
            "j": "#24252e", "J": "#33343f", "o": "#3b2f2a", "O": "#55453c", "k": "#241c19",
            "Y": "#e6bb4c", "y": "#b4832c", "q": "#2a1d17",
        },
        sharks=True,
    ),
    "drifter": dict(
        name="Drifter (ref. 3)",
        hair="#8f6d50", top=1, eye_rows=[6],
        head=[
            "...hHHHh...",
            ".hhHHHHHHh.",
            "uhhhHHhhHHh",
            "uhhhhhSShHh",
            "uuhhSSSSShh",
            "uuhsSddSdd.",
            "uuhzSeSSfSn",
            "uhhzSSSSSnn",
            "uhhbbSSbbb.",
            "uuhbbbMMbb.",
            "uuhbbbbbbb.",
            ".u.gbbbbb..",
        ],
        torso=[
            "Wwssww",
            "WwwsWw",
            "vWwwWw",
            "vWwwww",
            "vWWwww",
            "kkk3kk",
        ],
        back=None,
        forearm=True,
        pal={
            "d": "#3e2c20", "e": "#6f8f80", "f": "#6f8f80",
            "b": "#6e5240", "B": "#8f6d50", "g": "#4b3628", "M": "#5a412f",
            "s": "#d9a581", "S": "#ebbf9b", "z": "#b5835f", "n": "#d08e74",
            "w": "#f4f3ee", "W": "#d4d6de", "v": "#a3a6b6",
            "k": "#4a3326", "3": "#c9a25a",
            "j": "#3a3530", "J": "#4c463f", "o": "#6a4a36", "O": "#8a6449",
        },
    ),
    "dad": dict(
        name="Dad (ref. 4)",
        hair="#7a5236", top=1, eye_rows=[6, 7],
        head=[
            "...HHHHh...",
            ".hhHHHHHHh.",
            "uhhhhHHHhHh",
            "uhhhhhhhhh.",
            "uhhsSSSSSS.",
            "uhsSddSSdd.",
            "uhzSSqeSqe.",
            "uhzSSqqSqqn",
            "uhhSSSSSSnn",
            "uubbbMMMMM.",
            ".ubbbbMbbb.",
            "..bbbbbbb..",
        ],
        torso=[
            "WxqTqw",
            "WwxTYw",
            "vWwYTx",
            "vxwTYw",
            "vWwxTw",
            "jjjJJJ",
        ],
        back=None,
        pal={
            "d": "#3a2418", "e": "#5b3424", "q": "#f6f1ea",
            "b": "#8a6650", "B": "#7a5236", "g": "#6a4c3a", "M": "#3a2418",
            "s": "#e7ab8f", "S": "#f4c3a8", "z": "#c38a72", "n": "#e09a84",
            "w": "#f1e9c8", "W": "#d9cea0", "v": "#b2a77c", "x": "#c8b77a",
            "T": "#d9822b", "Y": "#5f9e4f",
            "j": "#5a4636", "J": "#6e5643", "o": "#3e2a20", "O": "#5a3f30", "k": "#2a1c16",
        },
    ),
    "fisher_color": dict(
        name="Fisher, cores (ref. 1/2)",
        hair="#4b3527", top=1, eye_rows=[7],
        head=None,
        torso=[
            "RRCCCC",
            "KRRCCC",
            "QKCTCC",
            "QKCCCC",
            "QKCTCC",
            "QQCCCC",
            "QQCCCQ",
        ],
        back=(["K.", "KC", "KC", "CC"], (10, 17)),
        pal={
            "d": "#24180f", "e": "#24180f", "b": "#5c4636", "g": "#43332a", "M": "#1f1612", "B": "#5c4636",
            "s": "#d8a17d", "S": "#ebbb98", "z": "#b37f5e", "n": "#cf8a6e",
            "C": "#9a6a44", "K": "#b98657", "Q": "#6d4a31", "T": "#efe3c4", "R": "#b8413e",
            "W": "#a8774d", "v": "#7a5336",
            "j": "#2e3346", "J": "#3d4459", "o": "#4a342a", "O": "#664a3b", "k": "#2a1d17",
            "q": "#24180f",
        },
    ),
}
NPCS["fisher_color"]["head"] = NPCS["fisher"]["head"]

ORIG = dict(draw_head=g.draw_head, draw_arm=g.draw_arm, draw_frame=g.draw_frame, TUFT=g.TUFT,
            TORSO=g.TORSO, TORSO_AT=g.TORSO_AT, PACK=g.PACK, PACK_AT=g.PACK_AT, HAIR_COLOR=g.HAIR_COLOR)


def setup(npc: dict) -> None:
    def draw_head(c: g.Pix, p: dict) -> None:
        rows = list(npc["head"])
        if p["blink"] or p["eyes"]:
            last = npc["eye_rows"][-1]
            for r in npc["eye_rows"]:
                fill = "d" if r == last else "S"
                if npc.get("tufts") and p["blink"] and not p["eyes"] and r == last:
                    continue
                rows[r] = "".join(fill if ch in EYE_LETTERS else ch for ch in rows[r])
        extra = 0
        if npc.get("tufts") and p["tuft"] in ORIG["TUFT"]:
            top, extra = ORIG["TUFT"][p["tuft"]]
            rows = top + rows[2:]
        at = g.offset((11, 11), g.offset(p["body"], p["head"]))
        c.stamp(rows, (at[0], at[1] - npc["top"] - extra))

    def draw_arm(c, shoulder, hand, front, fist=2, elbow=None):
        ORIG["draw_arm"](c, shoulder, hand, front, fist, elbow)
        if npc.get("forearm"):
            start = elbow or shoulder
            steps = max(abs(hand[0] - start[0]), abs(hand[1] - start[1]), 1)
            for i in range(steps // 2 + 1, steps + 1):
                x = round(start[0] + (hand[0] - start[0]) * i / steps)
                y = round(start[1] + (hand[1] - start[1]) * i / steps)
                for dx, dy in ((0, 0), (1, 0), (0, 1)):
                    if (x + dx, y + dy) in c.px and c.part.get((x + dx, y + dy)) == c.current:
                        c.px[(x + dx, y + dy)] = "s" if front else "z"

    def draw_frame(p: dict) -> g.Pix:
        c = ORIG["draw_frame"](p)
        if npc.get("sharks") and not p["eyes"]:
            c.current = "item"
            t = TICK[0]
            rows = [r[::-1] for r in SHARK]
            if t % 2:
                rows = [rows[0], rows[1], rows[2], "y" + rows[3][1:]]
            dy = (0, 0, 1, 2, 2, 1)[t % 6]
            c.stamp(rows, (5 + p["body"][0], 12 + dy + p["body"][1]))
        return c

    g.draw_head, g.draw_arm, g.TUFT = draw_head, draw_arm, {}
    g.TORSO, g.TORSO_AT = npc["torso"], (13, 21)
    g.PACK, g.PACK_AT = (npc["back"] or ([], (10, 20)))
    g.HAIR_COLOR = npc["hair"]
    g.draw_frame = draw_frame


def restore() -> None:
    for k, v in ORIG.items():
        setattr(g, k, v)


def build(npc_id: str) -> tuple[Image.Image, dict]:
    npc = NPCS[npc_id]
    setup(npc)
    pal = dict(g.PAL)
    pal.update(npc["pal"])
    try:
        sheet = Image.new("RGBA", (g.FRAME * g.COLS, g.FRAME * len(g.ANIMS)), (0, 0, 0, 0))
        meta = {"image": f"{npc_id}.png", "frame_w": g.FRAME, "frame_h": g.FRAME, "scale": 1.0, "animations": {}}
        for row, (name, fps, loop, poses) in enumerate(g.ANIMS):
            meta["animations"][name] = {"row": row, "frames": len(poses), "fps": fps, "loop": loop}
            for col, p in enumerate(poses):
                TICK[0] = col
                sheet.paste(g.draw_frame(p).image(pal), (col * g.FRAME, row * g.FRAME))
    finally:
        restore()
    return sheet, meta


F = g.FRAME
ROWS = {name: row for row, (name, _, _, _) in enumerate(g.ANIMS)}
try:
    FONT = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 16)
except OSError:
    FONT = ImageFont.load_default()


def frame(sheet: Image.Image, anim: str, i: int) -> Image.Image:
    n = len(g.ANIMS[ROWS[anim]][3])
    i %= n
    r = ROWS[anim]
    return sheet.crop((i * F, r * F, (i + 1) * F, (r + 1) * F))


def backdrop(w: int, h: int) -> Image.Image:
    img = Image.new("RGBA", (w, h))
    top, bot = (64, 52, 110), (236, 150, 120)
    for y in range(h):
        t = y / h
        img.paste((*[round(a + (b - a) * t) for a, b in zip(top, bot)], 255), (0, y, w, y + 1))
    for name in ("ember_hills", "ember_pines_far", "ember_pines_mid"):
        path = os.path.join(ASSETS, "backgrounds", name + ".png")
        if os.path.exists(path):
            layer = Image.open(path).convert("RGBA")
            crop = layer.crop((0, max(0, layer.height - h), min(w, layer.width), layer.height))
            img.alpha_composite(crop, (0, h - crop.height))
    return img


def preview(sheets: dict[str, Image.Image]) -> None:
    out = os.path.join(DOCS_PREVIEW, "npcs")
    os.makedirs(out, exist_ok=True)
    hero = g.build()[0]
    cast = [("George (atual)", hero)] + [(NPCS[k]["name"], s) for k, s in sheets.items()]
    poses = [("idle", 0), ("idle", 9), ("run", 0), ("run", 4), ("jump", 1), ("fall", 0), ("dash", 0), ("wall_slide", 0), ("sit_roast", 2)]
    pad, scale, label_h = 4, 5, 28
    w, h = len(poses) * (F + pad) + pad, len(cast) * (F + 6)
    img = Image.new("RGBA", (w, h))
    row_bg = backdrop(w, F + 6)
    for j in range(len(cast)):
        img.paste(row_bg, (0, j * (F + 6)))
    d = ImageDraw.Draw(img)
    for j, (_, sheet) in enumerate(cast):
        y0 = j * (F + 6)
        d.rectangle([0, y0 + F - 2, w, y0 + F + 5], fill=(46, 58, 52, 255))
        d.rectangle([0, y0 + F - 2, w, y0 + F - 1], fill=(92, 168, 96, 255))
        for i, (anim, k) in enumerate(poses):
            img.alpha_composite(frame(sheet, anim, k), (pad + i * (F + pad), y0))
    big = img.resize((w * scale, h * scale), Image.NEAREST)
    sheet_img = Image.new("RGBA", (big.width, big.height + label_h * len(cast)), (24, 22, 40, 255))
    dd = ImageDraw.Draw(sheet_img)
    for j, (label, _) in enumerate(cast):
        y = j * ((F + 6) * scale + label_h)
        dd.text((10, y + 5), f"{j}. {label}" if j else label, fill=(255, 240, 220, 255), font=FONT)
        sheet_img.paste(big.crop((0, j * (F + 6) * scale, big.width, (j + 1) * (F + 6) * scale)), (0, y + label_h))
    sheet_img.convert("RGB").save(os.path.join(out, "npcs.png"))

    frames = []
    cw, ch = 44, 44
    bg = backdrop(cw * len(cast), ch)
    for t in range(48):
        f = bg.copy()
        dr = ImageDraw.Draw(f)
        dr.rectangle([0, ch - 6, f.width, ch], fill=(46, 58, 52, 255))
        dr.rectangle([0, ch - 6, f.width, ch - 5], fill=(92, 168, 96, 255))
        anim, k = ("idle", t // 2) if t < 16 else ("run", t) if t < 32 else ("sit_roast", (t - 32) // 2)
        for j, (_, sheet) in enumerate(cast):
            f.alpha_composite(frame(sheet, anim, k), (j * cw + (cw - F) // 2, ch - 5 - F))
        frames.append(f.resize((f.width * 6, f.height * 6), Image.NEAREST).convert("RGB"))
    pal = frames[20].quantize(colors=255, dither=Image.Dither.NONE)
    frames = [fr.quantize(palette=pal, dither=Image.Dither.NONE) for fr in frames]
    frames[0].save(os.path.join(out, "npcs.gif"), save_all=True, append_images=frames[1:], duration=110, loop=0)


GEORGE_SHAVED = [
    "......hHH.",
    "..hhHHHHHh",
    "uhhhhhhHHh",
    "uhhsSSSSSh",
    "uhhSddSdd.",
    "shzSSeSfS.",
    "zhzSSeSfS.",
    "uhsSSSSSS.",
    "uusSSSSSS.",
    ".usSSSSS..",
]
MUSTACHES = {
    "chevron": ["uhzSSSSSS.", "uuzSMMMMM.", ".uzzSSSS.."],
    "stubble": ["uhbSSSSSb.", "uubbMMMMM.", ".ubbbbbb.."],
    "handlebar": ["uhzSSSSSSM", "uuzSMMMMMM", ".uzzSSSS.."],
    "walrus": ["uhzSSSSSS.", "uuzSMMMMMM", ".uzzMMMM.."],
}


def george_head(stache: str) -> list[str]:
    return GEORGE_SHAVED[:7] + MUSTACHES[stache]


GEORGE_PACK = (ORIG["PACK"], ORIG["PACK_AT"])
SKIN = {"s": "#e4b58f", "S": "#f3cda9", "z": "#c48f6c", "c": "#e8998a"}

VARIANTS = {
    "v_flannel": dict(
        name="Flanela (cabelo preto, bigode em V, sem barba)",
        hair="#4a3a36", top=0, eye_rows=[5, 6], head=george_head("chevron"), back=GEORGE_PACK,
        torso=["xwxWxw", "xttxwx", "WwttxW", "vxwttx", "vWxwtt", "jjjJJJ"],
        pal={**SKIN, "d": "#1d1614", "e": "#3b2a20", "f": "#3b2a20", "M": "#2a201d", "b": "#8a6d5c",
             "w": "#c0463f", "W": "#8f2f2f", "v": "#6a2326", "x": "#2b1f26",
             "t": "#5b4636", "G": "#5b4636", "a": "#7a5f48", "m": "#3c2e24",
             "j": "#2c3346", "J": "#3b4560"},
    ),
    "v_tee": dict(
        name="T-shirt (ruivo, bigode + barba por fazer)",
        hair="#c06a3a", top=0, eye_rows=[5, 6], head=george_head("stubble"), back=GEORGE_PACK,
        torso=["Wwwwww", "Wttwww", "WWttww", "vWwttw", "vWWwtt", "jjjJJJ"],
        pal={**SKIN, "d": "#6b3418", "e": "#2f5f6a", "f": "#2f5f6a", "M": "#9a4a24", "b": "#d49a7a",
             "w": "#e6b94a", "W": "#c4952f", "v": "#94702a",
             "t": "#2f5a52", "G": "#2f5a52", "a": "#3f7a6c", "m": "#1f3d38",
             "j": "#3a3a40", "J": "#4c4c55"},
    ),
    "v_denim": dict(
        name="Ganga (loiro, bigode de guidão, sem barba)",
        hair="#e2c06e", top=0, eye_rows=[5, 6], head=george_head("handlebar"), back=GEORGE_PACK,
        torso=["Wqwwqw", "WttwWw", "WWttww", "vWwttw", "vWWwtt", "jjjJJJ"],
        pal={**SKIN, "d": "#8a6a2c", "e": "#3a5e8a", "f": "#3a5e8a", "M": "#8a6326", "b": "#d9a888",
             "w": "#7d9cc4", "W": "#5d7ca6", "v": "#45608a", "q": "#d8e2ee",
             "t": "#7a3b2e", "G": "#7a3b2e", "a": "#9a5440", "m": "#55281f",
             "j": "#4a3f33", "J": "#5e5142"},
    ),
    "v_polo": dict(
        name="Polo (grisalho, bigode de morsa, sem barba)",
        hair="#a9a4a0", top=0, eye_rows=[5, 6], head=george_head("walrus"), back=GEORGE_PACK,
        torso=["Wqqwww", "Wtt3ww", "WWtt3w", "vWwttw", "vWWwtt", "jjjJJJ"],
        pal={**SKIN, "d": "#5e5a58", "e": "#3a3430", "f": "#3a3430", "M": "#c9c4c0", "b": "#d0a888",
             "w": "#3f7a5a", "W": "#2f6048", "v": "#224634", "q": "#e6e2d4", "3": "#e6e2d4",
             "t": "#8a6a3a", "G": "#8a6a3a", "a": "#a8854e", "m": "#5e4626",
             "j": "#5a4a3a", "J": "#6e5c48"},
    ),
}


def still(cast: list[tuple[str, Image.Image]], filename: str) -> None:
    poses = [("idle", 0), ("idle", 9), ("run", 2), ("jump", 1), ("sit_roast", 2)]
    pad, scale, label_h = 6, 6, 28
    w, rh = len(poses) * (F + pad) + pad, F + 6
    row_img = Image.new("RGBA", (w, rh), (66, 54, 104, 255))
    d = ImageDraw.Draw(row_img)
    d.rectangle([0, F - 2, w, rh], fill=(46, 58, 52, 255))
    d.rectangle([0, F - 2, w, F - 1], fill=(92, 168, 96, 255))
    out = Image.new("RGB", (w * scale, len(cast) * (rh * scale + label_h)), (24, 22, 40))
    dd = ImageDraw.Draw(out)
    for j, (label, sheet) in enumerate(cast):
        r = row_img.copy()
        for i, (anim, k) in enumerate(poses):
            r.alpha_composite(frame(sheet, anim, k), (pad + i * (F + pad), 0))
        y = j * (rh * scale + label_h)
        dd.text((10, y + 5), label, fill=(255, 240, 220), font=FONT)
        out.paste(r.resize((w * scale, rh * scale), Image.NEAREST).convert("RGB"), (0, y + label_h))
    dir_ = os.path.join(DOCS_PREVIEW, "npcs")
    os.makedirs(dir_, exist_ok=True)
    try:
        out.save(os.path.join(dir_, filename))
    except OSError:
        print("aviso: nao deu para gravar", filename)


def shade(color: str, k: float) -> str:
    r, gg, b, _ = rgba(color)
    return "#%02x%02x%02x" % (min(255, round(r * k)), min(255, round(gg * k)), min(255, round(b * k)))


YOUNG_TOP = GEORGE_SHAVED[:4] + ["uhhSSSSSS.", "shzSSeSfS.", "zhzSSeSfS."]
STACHES3 = {
    "cheio": ["uhzSNNNNS.", "uuzSPMMPS.", ".uzzSSSS.."],
    "largo": ["uhzNNNNNN.", "uuzSPMMMP.", ".uzzSSSS.."],
    "curvo": ["uhzSMNNMS.", "uuzSMMMMS.", ".uzzSSSS.."],
    "guidao": ["uhzMNNNNM.", "uuzSPMMPS.", ".uzzSSSS.."],
    "ferradura": ["uhzSNNNNS.", "uuzSMSSMS.", ".uzzPSSP.."],
    "morsa": ["uhzSNNNNN.", "uuzSMMMMM.", ".uzzSPPS.."],
}
TORSOS3 = {
    "tee": ["Wwssww", "WWwwww", "vWwwww", "vWwwww", "vWWwww", "jjjJJJ"],
    "flannel": ["xwxWxw", "WxwxWx", "xWxwxw", "vxwxWx", "vWxwxw", "jjjJJJ"],
    "denim": ["Wqwwqw", "WWwqww", "vWwwwq", "vWwqww", "vWWwww", "jjjJJJ"],
    "henley": ["Wwsssw", "WWw3ww", "vWw3ww", "vWwwww", "vWWwww", "jjjJJJ"],
    "hoodie": ["WqwwqW", "WWqwqw", "vWwwww", "vWxxxw", "vWWwww", "jjjJJJ"],
}


def young(name: str, hair: str, stache: str, torso: str, eyes: str, cloth: dict) -> dict:
    return dict(
        name=name, hair=hair, top=0, eye_rows=[5, 6], tufts=True, back=None,
        head=YOUNG_TOP + STACHES3[stache], torso=TORSOS3[torso],
        pal={**SKIN, "d": shade(hair, 0.35), "e": eyes, "f": eyes,
             "N": shade(hair, 1.0), "M": shade(hair, 0.8), "P": shade(hair, 0.55), **cloth},
    )


JEANS = {"j": "#2c3a5a", "J": "#3b4c72"}
VARIANTS3 = {
    "y_dark_curve": young("9. Escuro, bigode curvo, flanela verde", "#5a4136", "curvo", "flannel", "#3f7a5a",
                          {"w": "#4f8a5a", "W": "#356642", "v": "#244a30", "x": "#1e2a24", **JEANS}),
    "y_dark_wide": young("10. Escuro, bigode largo, t-shirt azul-marinho", "#5a4136", "largo", "tee", "#1d4d36",
                         {"w": "#3d5288", "W": "#2d3e6a", "v": "#1f2c4e", "j": "#4a3e34", "J": "#5e5042"}),
    "y_brown_full": young("11. Castanho, bigode cheio, flanela vermelha", "#8a5a3a", "cheio", "flannel", "#1d4d36",
                          {"w": "#c0463f", "W": "#8f2f2f", "v": "#6a2326", "x": "#2b1f26", **JEANS}),
    "y_brown_handle": young("12. Castanho, guidão, camisa de ganga", "#8a5a3a", "guidao", "denim", "#3a5e8a",
                            {"w": "#7d9cc4", "W": "#5d7ca6", "v": "#45608a", "q": "#d8e2ee", "j": "#3a3530", "J": "#4c463f"}),
    "y_red_horse": young("13. Ruivo, ferradura, henley creme", "#c8673a", "ferradura", "henley", "#2f5f6a",
                         {"w": "#efe6cc", "W": "#cfc4a4", "v": "#a89e80", "3": "#8a6a4a", **JEANS}),
    "y_red_walrus": young("14. Ruivo, morsa, moletom mostarda", "#c8673a", "morsa", "hoodie", "#1d4d36",
                          {"w": "#e0b04a", "W": "#bf912f", "v": "#8f6c22", "q": "#f3ead0", "x": "#9a7426",
                           "j": "#3a3a40", "J": "#4c4c55"}),
}


def main() -> None:
    NPCS.update(VARIANTS)
    NPCS.update(VARIANTS3)
    sheets = {}
    for npc_id in NPCS:
        sheet, meta = build(npc_id)
        save(sheet, "sprites", "npcs", f"{npc_id}.png")
        save_json(meta, "sprites", "npcs", f"{npc_id}.json")
        sheets[npc_id] = sheet
    if "--v1" in os.sys.argv:
        preview({k: v for k, v in sheets.items() if k not in VARIANTS})
    cast = [("George (atual)", g.build()[0])]
    cast += [(f"{n}. {VARIANTS[k]['name']}", sheets[k]) for n, k in enumerate(VARIANTS, 5)]
    still(cast, "npcs_v2.png")
    still([cast[0]] + [(v["name"], sheets[k]) for k, v in VARIANTS3.items()], "npcs_v3.png")
    print("npcs: ok")


if __name__ == "__main__":
    main()
