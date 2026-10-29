from __future__ import annotations

from PIL import Image

import gen_dog as g
from vec import save, save_json

PAL = {
    "O": "#0c0a12",
    "J": "#0c0a12",
    "p": "#3a3350",
    "w": "#2e2a40",
    "h": "#5e5680",
    "g": "#201d2e",
    "G": "#181524",
    "t": "#2e2a40",
    "T": "#1d1a29",
    "L": "#4a4462",
    "m": "#5e5680",
    "N": "#0c0a12",
    "n": "#6a6286",
    "e": "#f5c542",
    "y": "#f5c542",
    "Y": "#b97f24",
    "k": "#e07a8e",
    "z": "#f4f0eb",
}

HEADS = {
    "n": [
        "..tmmmt.....",
        ".tmmmttttt..",
        "tttttteht...",
        "ttttttJetLLn",
        "tttttLLLLLLJ",
        "tttttLLLNLL.",
        ".ttttLLLL...",
    ],
    "blink": [
        "..tmmmt.....",
        ".tmmmttttt..",
        "tttttttttt..",
        "ttttttJJtLLn",
        "tttttLLLLLLJ",
        "tttttLLLNLL.",
        ".ttttLLLL...",
    ],
    "pant": [
        "..tmmmt.....",
        ".tmmmttttt..",
        "tttttteht...",
        "ttttttJetLLn",
        "tttttLLLLLLJ",
        "tttttLLJJJJ.",
        ".ttttLLkkJ..",
        ".......kk...",
    ],
    "bark": [
        "..tmmmt......",
        ".tmmmttttt...",
        "tttttteht....",
        "ttttttJetLLLn",
        "tttttLLLLLLJ.",
        "tttttLJJJJ...",
        ".ttttJkJJL...",
        "..tttLLLL....",
    ],
    "sleep": [
        "..tmmmt.....",
        ".tmmmttttt..",
        "tttttttttt..",
        "ttttttJJtLLn",
        "tttttLLLLLLJ",
        "tttttLLLNLL.",
        ".ttttLLLL...",
    ],
}

EAR_NEAR = {
    "up": ["...mm.", "..mTTT", "..TTTT", "..TTT.", "..TTT.", "...T.."],
    "perk": ["...mm.", "..mTTT", "..TTTT", "...TT."],
    "back": ["..mmm.", "TTTTTT", "TT...."],
    "flop": ["......", "..mmm.", "..TTTT", "..TTTT", "...TT."],
}
EAR_FAR = {
    "up": ["TT.", "TTT"],
    "perk": [".TT", "TTT"],
    "back": ["TT.", "TTT"],
    "flop": ["...", "TTT"],
}

TORSO = {
    "stand": [
        ".hhhmmhhhh...",
        "wwwwwwwwwwwww",
        "wwwwwwwwwwwww",
        ".gggwwwwwggg.",
    ],
    "long": [
        ".hhhmmmhhhh....",
        "wwwwwwwwwwwwwww",
        "wwwwwwwwwwwwwww",
        "..gggwwwwwggg..",
    ],
    "short": [
        ".hhmmhhhh..",
        "wwwwwwwwwww",
        "wwwwwwwwwww",
        ".ggwwwwwgg.",
    ],
}

TAILS = {
    "up": ["hh.", ".w.", ".ww"],
    "right": ["..h", ".hw", ".ww"],
    "left": ["h..", "hw.", ".ww"],
    "flat": ["hhww"],
    "down": [".ww", "hw.", "h.."],
}
TAILS_GROUND = {
    "a": ["hww"],
    "b": ["h..", ".ww"],
    "c": ["hh.", "..w"],
}

SIT = g.SIT[:3] + g.SIT[4:]

COLLAR = [(-1, 4, "Y"), (0, 4, "y"), (0, 5, "y"), (0, 6, "Y"), (1, 6, "y"), (1, 7, "y")]


PAL.update({
    "i": "#4a3550",
    "c": "#2e2a40",
    "C": "#201d2e",
})
CHEST = {
    "c": "#eae2da",
    "C": "#d0b6b2",
}


def _open_eye(rows: list[str]) -> list[str]:
    rows = list(rows)
    if "Jh" in rows[2]:
        rows[2] = rows[2].replace("Jh", "eh", 1)
        rows[3] = rows[3].replace("JJ", "Je", 1)
    return rows


HEADS_V2 = {k: _open_eye(v) for k, v in g.HEADS.items()}
for _k in ("n", "blink", "pant", "sleep"):
    HEADS_V2[_k][3] = HEADS_V2[_k][3][:-1] + "n"
for _k, _rows in HEADS_V2.items():
    HEADS_V2[_k] = _rows[:4] + [r.replace("w", "c") for r in _rows[4:]]

EAR_NEAR_V2 = {k: [r.replace("g", "i") for r in v] for k, v in g.EAR_NEAR.items()}
EAR_FAR_V2 = g.EAR_FAR

TORSO_V2 = {
    "stand": [
        ".hhhmmhhhh...",
        "wwwwwwwwwwccc",
        "wwwwwwwwwwccc",
        ".gggwwwwwgCC.",
    ],
    "long": [
        ".hhhmmmhhhh....",
        "wwwwwwwwwwwwccc",
        "wwwwwwwwwwwwccc",
        "..gggwwwwwggCC.",
    ],
    "short": [
        ".hhmmhhhh..",
        "wwwwwwwwccc",
        "wwwwwwwwccc",
        ".ggwwwwgCC.",
    ],
}


def _chest(rows: list[str], x0: int, y0: int, y1: int) -> list[str]:
    out = []
    for j, r in enumerate(rows):
        if y0 <= j <= y1:
            r = r[:x0] + "".join("c" if ch in "wh" else ch for ch in r[x0:])
        out.append(r)
    return out


_LIE0, _NECK0 = g.LIE, g.NECK
SIT_V2 = _chest(SIT, 8, 0, 4)
LIE_V2 = _chest(g.LIE, 11, 1, 2)
NECK_V2 = _NECK0


def use(v1: bool = False, chest: bool = True) -> None:
    pal = dict(PAL)
    if chest:
        pal.update(CHEST)
    g.PAL = pal
    g.TAILS = TAILS
    g.TAILS_GROUND = TAILS_GROUND
    g.LEG_DROP = 1
    g.COLLAR = COLLAR
    if v1:
        g.HEADS, g.EAR_NEAR, g.EAR_FAR = HEADS, EAR_NEAR, EAR_FAR
        g.EAR_NEAR_AT, g.EAR_FAR_AT, g.EAR_SEAM = (-1, -1), (4, -1), True
        g.TORSO, g.SIT, g.LIE, g.NECK = TORSO, SIT, _LIE0, _NECK0
        return
    g.HEADS, g.EAR_NEAR, g.EAR_FAR = HEADS_V2, EAR_NEAR_V2, EAR_FAR_V2
    g.EAR_NEAR_AT, g.EAR_FAR_AT, g.EAR_SEAM = (1, -3), (4, -2), False
    g.TORSO, g.SIT, g.LIE, g.NECK = TORSO_V2, SIT_V2, LIE_V2, NECK_V2


def build(chest: bool = True, v1: bool = False):
    use(v1=v1, chest=chest)
    return g.build("zeus_dog.png")


def shadow() -> Image.Image:
    use()
    g.PAL = {k: ("#f5c542" if k == "e" else "#0c0a12") for k in PAL}
    sheet, meta = g.build("zeus_dog_shadow.png")
    row = meta["animations"]["run"]["row"]
    return sheet.crop((2 * g.FRAME, row * g.FRAME, 3 * g.FRAME, (row + 1) * g.FRAME))


def main() -> None:
    import sys
    save(shadow(), "sprites", "zeus_dog", "zeus_dog_shadow.png")
    sheet, meta = build(chest="--no-chest" not in sys.argv, v1="--v1" in sys.argv)
    save(sheet, "sprites", "zeus_dog", "zeus_dog.png")
    save_json(meta, "sprites", "zeus_dog", "zeus_dog.json")
    print("cao de Zeus: ok")


if __name__ == "__main__":
    main()
