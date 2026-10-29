from __future__ import annotations

import colorsys

from PIL import Image

import gen_hero as g
from vec import rgba, save, save_json

HATS = ["none", "beanie", "cap", "bucket", "ranger"]
BEARDS = ["full", "stubble", "mustache", "none"]
GLASSES = ["none", "round", "shades"]
SCARVES = ["none", "scarf"]
STEP = 4


def _rgb(h: str) -> tuple[int, int, int]:
    r, gg, b, _ = rgba(h)
    return r, gg, b


def _hex(c) -> str:
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(v))) for v in c)


def mul(h: str, k: float, cool: float = 0.0) -> str:
    r, gg, b = _rgb(h)
    return _hex((r * k - 6 * cool, gg * k - 2 * cool, b * k + 8 * cool))


def lift(h: str, t: float, warm: float = 0.0) -> str:
    r, gg, b = _rgb(h)
    return _hex((r + (255 - r) * t + 6 * warm, gg + (255 - gg) * t + 3 * warm, b + (255 - b) * t - 6 * warm))


def hair(h_light: str) -> dict[str, str]:
    return {"H": h_light, "h": mul(h_light, 0.72), "u": mul(h_light, 0.45, 0.5),
            "B": mul(h_light, 0.9), "b": mul(h_light, 0.72), "g": mul(h_light, 0.48, 0.5),
            "d": mul(h_light, 0.27, 0.5)}


def jacket(w: str) -> dict[str, str]:
    return {"w": w, "W": mul(w, 0.85, 0.5), "v": mul(w, 0.63, 1.0)}


def pack(base: str) -> dict[str, str]:
    return {"G": base, "t": mul(base, 0.86, 0.3), "a": lift(base, 0.28, 1.0), "m": mul(base, 0.6, 1.0)}


def pants(front: str) -> dict[str, str]:
    return {"J": front, "j": mul(front, 0.77, 0.6)}


def boots(light: str) -> dict[str, str]:
    return {"O": light, "o": mul(light, 0.81, 0.4), "k": mul(light, 0.53, 1.0)}


def hat(base: str, band: str) -> dict[str, str]:
    return {"P": lift(base, 0.22, 1.0), "p": base, "q": mul(base, 0.68, 1.0), "r": band}


def scarf(base: str, stripe: str) -> dict[str, str]:
    return {"F": stripe, "i": base, "I": mul(base, 0.68, 1.0)}


def skin(S: str, s: str, z: str, n: str, c: str) -> dict[str, str]:
    return {"S": S, "s": s, "z": z, "n": n, "c": c}


P = g.PAL
GEORGE_HAIR = {k: _hex(g.hair_rgb(k)[:3]) for k in "Hhu"} | {k: P[k] for k in "Bbgd"}

PIECES: dict[str, tuple[str, list[tuple[str, str, dict[str, str]]]]] = {
    "skin": ("Ssznc", [
        ("tone1", "COLOR_TONE_1", skin(P["S"], P["s"], P["z"], P["n"], P["c"])),
        ("tone2", "COLOR_TONE_2", skin("#f6dcc4", "#eac2a4", "#c9967c", "#dca08a", "#eea294")),
        ("tone3", "COLOR_TONE_3", skin("#f2cfa0", "#e0b37e", "#bb8858", "#cf946a", "#e29c80")),
        ("tone4", "COLOR_TONE_4", skin("#e0b088", "#c99368", "#a06c48", "#b47a56", "#cf866e")),
        ("tone5", "COLOR_TONE_5", skin("#c48c62", "#a8704a", "#7e4e32", "#92583c", "#b06a50")),
        ("tone6", "COLOR_TONE_6", skin("#a06a46", "#875434", "#623a24", "#70432a", "#8e5440")),
        ("tone7", "COLOR_TONE_7", skin("#7e5036", "#663e28", "#48281a", "#52301e", "#704030")),
        ("tone8", "COLOR_TONE_8", skin("#f4d4c0", "#e9b8a2", "#c88e7e", "#dc9e8e", "#ee9c96")),
    ]),
    "hair": ("HhuBbgd", [
        ("auburn", "COLOR_AUBURN", GEORGE_HAIR),
        ("chestnut", "COLOR_CHESTNUT", hair("#7d5741")),
        ("dark_brown", "COLOR_DARK_BROWN", hair("#5c4032")),
        ("black", "COLOR_BLACK", hair("#46404e")),
        ("blonde", "COLOR_BLONDE", hair("#d8ae5c")),
        ("platinum", "COLOR_PLATINUM", hair("#ece2c4")),
        ("ginger", "COLOR_GINGER", hair("#d4703a")),
        ("silver", "COLOR_SILVER", hair("#bcbccc")),
        ("blue", "COLOR_BLUE", hair("#5a7ac4")),
        ("mint", "COLOR_MINT", hair("#62b896")),
    ]),
    "eyes": ("ef", [
        ("green", "COLOR_GREEN", {"e": P["e"], "f": P["f"]}),
        ("brown", "COLOR_BROWN", {"e": "#4a2c1c", "f": "#4a2c1c"}),
        ("blue", "COLOR_BLUE", {"e": "#244a8c", "f": "#244a8c"}),
        ("hazel", "COLOR_HAZEL", {"e": "#5c5420", "f": "#5c5420"}),
        ("gray", "COLOR_GRAY", {"e": "#465062", "f": "#465062"}),
        ("amber", "COLOR_AMBER", {"e": "#7c4a12", "f": "#7c4a12"}),
        ("dark", "COLOR_DARK", {"e": "#1c1824", "f": "#1c1824"}),
        ("teal", "COLOR_TEAL", {"e": "#145a5a", "f": "#145a5a"}),
    ]),
    "jacket": ("wWv", [
        ("indigo", "COLOR_INDIGO", {k: P[k] for k in "wWv"}),
        ("forest", "COLOR_FOREST", jacket("#527a58")),
        ("red", "COLOR_RED", jacket("#b04a3c")),
        ("mustard", "COLOR_MUSTARD", jacket("#c8962e")),
        ("navy", "COLOR_NAVY", jacket("#34507e")),
        ("olive", "COLOR_OLIVE", jacket("#6e7438")),
        ("brown", "COLOR_BROWN", jacket("#80563a")),
        ("charcoal", "COLOR_CHARCOAL", jacket("#4e4e58")),
        ("teal", "COLOR_TEAL", jacket("#2e807a")),
        ("orange", "COLOR_ORANGE", jacket("#c86434")),
    ]),
    "pack": ("tGam", [
        ("green", "COLOR_GREEN", {k: P[k] for k in "tGam"}),
        ("orange", "COLOR_ORANGE", pack("#d07a30")),
        ("red", "COLOR_RED", pack("#b8403a")),
        ("blue", "COLOR_BLUE", pack("#3c6cb8")),
        ("yellow", "COLOR_YELLOW", pack("#d4ae3c")),
        ("brown", "COLOR_BROWN", pack("#8a5c38")),
        ("gray", "COLOR_GRAY", pack("#6c7282")),
        ("teal", "COLOR_TEAL", pack("#2c9c98")),
        ("olive", "COLOR_OLIVE", pack("#7c8240")),
        ("black", "COLOR_BLACK", pack("#40404c")),
    ]),
    "pants": ("jJ", [
        ("charcoal", "COLOR_CHARCOAL", {k: P[k] for k in "jJ"}),
        ("denim", "COLOR_DENIM", pants("#3e5e8e")),
        ("khaki", "COLOR_KHAKI", pants("#a48e5c")),
        ("brown", "COLOR_BROWN", pants("#6e4c34")),
        ("black", "COLOR_BLACK", pants("#2c2a34")),
        ("olive", "COLOR_OLIVE", pants("#5e643a")),
        ("navy", "COLOR_NAVY", pants("#2e385c")),
        ("gray", "COLOR_GRAY", pants("#7c7e8a")),
        ("rust", "COLOR_RUST", pants("#803e30")),
        ("sand", "COLOR_SAND", pants("#c2aa7a")),
    ]),
    "boots": ("oOk", [
        ("brown", "COLOR_BROWN", {k: P[k] for k in "oOk"}),
        ("black", "COLOR_BLACK", boots("#4a4652")),
        ("tan", "COLOR_TAN", boots("#a87e4c")),
        ("red", "COLOR_RED", boots("#943c32")),
        ("gray", "COLOR_GRAY", boots("#6e7080")),
        ("olive", "COLOR_OLIVE", boots("#5e6442")),
        ("cream", "COLOR_CREAM", boots("#cec4b0")),
        ("navy", "COLOR_NAVY", boots("#3c4c7c")),
    ]),
    "hat_color": ("Ppqr", [
        ("red", "COLOR_RED", hat("#c04a3a", "#f0e0c8")),
        ("mustard", "COLOR_MUSTARD", hat("#c8962e", "#5a3a22")),
        ("forest", "COLOR_FOREST", hat("#4e7a56", "#d8c890")),
        ("navy", "COLOR_NAVY", hat("#34507e", "#e8e0cc")),
        ("orange", "COLOR_ORANGE", hat("#d0703a", "#3a2a30")),
        ("gray", "COLOR_GRAY", hat("#7c808e", "#3a3c4c")),
        ("brown", "COLOR_BROWN", hat("#8a6040", "#3a2418")),
        ("cream", "COLOR_CREAM", hat("#d8ccb0", "#6a4a34")),
        ("teal", "COLOR_TEAL", hat("#2e8a84", "#f0e0c8")),
        ("black", "COLOR_BLACK", hat("#3c3a48", "#c04a3a")),
    ]),
    "scarf_color": ("FiI", [
        ("red", "COLOR_RED", scarf("#c04a3a", "#f0e0c8")),
        ("mustard", "COLOR_MUSTARD", scarf("#c8962e", "#f4e2b0")),
        ("forest", "COLOR_FOREST", scarf("#4e7a56", "#d8c890")),
        ("navy", "COLOR_NAVY", scarf("#34507e", "#e8e0cc")),
        ("orange", "COLOR_ORANGE", scarf("#d0703a", "#f6d4a8")),
        ("gray", "COLOR_GRAY", scarf("#7c808e", "#d0d2dc")),
        ("cream", "COLOR_CREAM", scarf("#d8ccb0", "#b04a3c")),
        ("teal", "COLOR_TEAL", scarf("#2e8a84", "#d8f0e8")),
        ("brown", "COLOR_BROWN", scarf("#8a6040", "#e0c8a0")),
        ("white", "COLOR_WHITE", scarf("#e8e4dc", "#7c8090")),
    ]),
}
SHAPES = {
    "hat": [(h, "HAT_" + h.upper()) for h in HATS],
    "beard": [(b, "BEARD_" + b.upper()) for b in BEARDS],
    "glasses": [(x, "GLASSES_" + x.upper()) for x in GLASSES],
    "scarf": [(x, "SCARF_" + x.upper()) for x in SCARVES],
}
FIXED = ["@", "1", "2", "3", "4", "x", "K", "L", "l"]
DERIVED = {"y": ("s", "b", 0.45), "M": ("w", "w", 0.0)}


def mix(a: str, b: str, t: float) -> str:
    ca, cb = _rgb(a), _rgb(b)
    return _hex(tuple(x + (y - x) * t for x, y in zip(ca, cb)))


def letters() -> list[str]:
    out = list(FIXED)
    for piece_letters, _ in PIECES.values():
        out += list(piece_letters)
    out += list(DERIVED)
    return out


def is_magenta(h: str) -> bool:
    r, gg, b = (v / 255 for v in _rgb(h))
    hue, sat, val = colorsys.rgb_to_hsv(r, gg, b)
    return 0.78 < hue < 0.95 and sat > 0.35 and val > 0.3


def look_pal(choice: dict[str, str] | None = None) -> dict[str, str]:
    pal = {ch: g.PAL[ch] for ch in FIXED if ch != "@"}
    pal["@"] = g.OUTLINE
    for piece, (_, options) in PIECES.items():
        wanted = (choice or {}).get(piece, options[0][0])
        colors = next((o[2] for o in options if o[0] == wanted), options[0][2])
        pal.update(colors)
    for ch, (a, b, t) in DERIVED.items():
        pal[ch] = mix(pal[a], pal[b], t)
    return pal


def frame_letters(p: dict, look: dict[str, str]) -> dict[tuple[int, int], str]:
    return g.draw_frame(dict(p, **look)).final()


def sheet_from(fn) -> Image.Image:
    sheet = Image.new("RGBA", (g.FRAME * g.COLS, g.FRAME * len(g.ANIMS)), (0, 0, 0, 0))
    for row, (_, _, _, poses) in enumerate(g.ANIMS):
        for col, p in enumerate(poses):
            sheet.paste(fn(row, col, p), (col * g.FRAME, row * g.FRAME))
    return sheet


def index_image(px: dict[tuple[int, int], str], index: dict[str, int]) -> Image.Image:
    img = Image.new("RGBA", (g.FRAME, g.FRAME), (0, 0, 0, 0))
    out = img.load()
    for (x, y), ch in px.items():
        out[x, y] = (index[ch] * STEP, 0, 0, 255)
    return img


def color_image(px: dict[tuple[int, int], str], pal: dict[str, str]) -> Image.Image:
    img = Image.new("RGBA", (g.FRAME, g.FRAME), (0, 0, 0, 0))
    out = img.load()
    for (x, y), ch in px.items():
        out[x, y] = rgba(pal[ch])
    return img


def layer_diff(base: dict, more: dict, what: str) -> dict[tuple[int, int], str]:
    lost = [k for k in base if k not in more]
    assert not lost, f"{what}: o acessório apagaria pixels em {lost[:3]}"
    return {k: v for k, v in more.items() if base.get(k) != v}


def full_look(hat_id: str, beard: str, glasses: str, scarf_id: str) -> dict[str, str]:
    return {"hat": hat_id, "beard": beard, "glasses": glasses, "scarf": scarf_id}


def build() -> dict:
    order = letters()
    assert len(order) == len(set(order)), "letra repetida"
    assert len(order) < 256 // STEP, "letras de mais para o índice"
    index = {ch: i + 1 for i, ch in enumerate(order)}

    for row, (_, _, _, poses) in enumerate(g.ANIMS):
        for col, p in enumerate(poses):
            for beard in BEARDS:
                plain = {h: frame_letters(p, full_look(h, beard, "none", "none")) for h in HATS}
                for gl in GLASSES[1:]:
                    diffs = [layer_diff(plain[h], frame_letters(p, full_look(h, beard, gl, "none")), gl) for h in HATS]
                    assert all(d == diffs[0] for d in diffs), f"óculos {gl} mudam com o chapéu ({row},{col})"
                sc = [layer_diff(plain[h], frame_letters(p, full_look(h, beard, "none", "scarf")), "cachecol")
                      for h in HATS]
                assert all(d == sc[0] for d in sc), f"cachecol muda com o chapéu ({row},{col})"
                if beard == "full":
                    gl_d = layer_diff(plain["none"], frame_letters(p, full_look("none", beard, "round", "none")), "o")
                    sc_d = sc[0]
                    assert not (set(gl_d) & set(sc_d)), "óculos e cachecol tocam-se"

    for h in HATS:
        for beard in BEARDS:
            look = full_look(h, beard, "none", "none")
            img = sheet_from(lambda r, c, p: index_image(frame_letters(p, look), index))
            save(img, "sprites", "hero", "look", f"base_{h}_{beard}.png")
    for gl in GLASSES[1:]:
        img = sheet_from(lambda r, c, p: index_image(layer_diff(
            frame_letters(p, full_look("none", "full", "none", "none")),
            frame_letters(p, full_look("none", "full", gl, "none")), gl), index))
        save(img, "sprites", "hero", "look", f"glasses_{gl}.png")
    for beard in BEARDS:
        img = sheet_from(lambda r, c, p: index_image(layer_diff(
            frame_letters(p, full_look("none", beard, "none", "none")),
            frame_letters(p, full_look("none", beard, "none", "scarf")), "cachecol"), index))
        save(img, "sprites", "hero", "look", f"scarf_{beard}.png")

    fixed = look_pal()
    meta = {
        "step": STEP,
        "index": index,
        "fixed": {ch: fixed[ch] for ch in FIXED},
        "derived": {ch: list(v) for ch, v in DERIVED.items()},
        "pieces": {piece: {"letters": list(ls), "options": [
            {"id": oid, "name": key, "colors": colors} for oid, key, colors in options]}
            for piece, (ls, options) in PIECES.items()},
        "shapes": {kind: [{"id": sid, "name": key} for sid, key in opts] for kind, opts in SHAPES.items()},
    }
    for piece, (ls, options) in PIECES.items():
        for oid, _, colors in options:
            missing = [ch for ch in ls if ch in index and ch not in colors]
            assert not missing, f"{piece}/{oid} sem {missing}"
            bad = [c for c in colors.values() if is_magenta(c)]
            assert not bad, f"{piece}/{oid} magenta: {bad}"
    save_json(meta, "sprites", "hero", "look", "look.json")
    return meta


def main() -> None:
    build()
    print("personalização: ok")


if __name__ == "__main__":
    main()
