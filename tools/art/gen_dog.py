from __future__ import annotations

import math
import sys

from PIL import Image

from vec import rgba, save, save_json

FRAME = 32
SOLE_Y = 30
AX = 16

PAL = {
    "O": "#421d2e",
    "J": "#2f1329",
    "p": "#5f3348",
    "w": "#eae2da",
    "h": "#f4f0eb",
    "g": "#d0b6b2",
    "G": "#a8898f",
    "t": "#b6825a",
    "T": "#9d6848",
    "L": "#c0977e",
    "m": "#ccb189",
    "N": "#8a5752",
    "k": "#c97d86",
    "z": "#f4f0eb",
}
OUTLINE = "O"

LEG_DROP = 0
EAR_NEAR_AT = (1, -3)
EAR_FAR_AT = (4, -2)
EAR_SEAM = False
NECK = [".t", "hw"]
COLLAR: list[tuple[int, int, str]] = []


HEADS = {
    "n": [
        "..tmmtt.....",
        ".tmmttttt...",
        "ttttttJht...",
        "ttttttJJtLLJ",
        "wttttLLLLLLL",
        "wwwwwwwwNwww",
        ".wwwwwwwww..",
    ],
    "blink": [
        "..tmmtt.....",
        ".tmmttttt...",
        "ttttttttt...",
        "ttttttJJtLLJ",
        "wttttLLLLLLL",
        "wwwwwwwwNwww",
        ".wwwwwwwww..",
    ],
    "pant": [
        "..tmmtt.....",
        ".tmmttttt...",
        "ttttttJht...",
        "ttttttJJtLLJ",
        "wttttLLLLLLL",
        "wwwwwwwJJJJ.",
        ".wwwwwwwkkJ.",
        "........kk..",
    ],
    "bark": [
        "..tmmtt......",
        ".tmmttttt....",
        "ttttttJht....",
        "ttttttJJtLLLJ",
        "wttttLLLLLLL.",
        "wwwwwwwJJJJ..",
        ".wwwwwwJkJJw.",
        "..wwwwwwwww..",
    ],
    "sleep": [
        "..tmmtt.....",
        ".tmmttttt...",
        "ttttttttt...",
        "ttttttJJtLLJ",
        "wttttLLLLLLL",
        "wwwwwwwwNwww",
        ".wwwwwwwww..",
    ],
}
HEAD_W = 12

EAR_NEAR = {
    "up": ["t...", "tt..", "tgt.", "tggt"],
    "perk": [".t..", ".tt.", "tgt.", "tggt"],
    "back": ["....", "tt..", "ttgt", ".tgt"],
    "flop": ["....", "....", "ttt.", ".tgt"],
}
EAR_FAR = {
    "up": ["T..", "TT.", "TpT"],
    "perk": [".T.", "TT.", "TpT"],
    "back": ["...", "TT.", "TpT"],
    "flop": ["...", "...", "TTT"],
}

TORSO = {
    "stand": [
        ".hhtmmthhhh..",
        "wwtttttTwwwww",
        "wwwTTTwwwwwww",
        ".gggwwwwwwgg.",
    ],
    "long": [
        ".hhmmmmmhhhh...",
        "wwttttttTwwwwww",
        "wwwTTTTTwwwwwww",
        "..ggggwwwwwgg..",
    ],
    "short": [
        ".hhmmmhhhh.",
        "wwttttTwwww",
        "wwwTTTwwwww",
        ".ggwwwwwgg.",
    ],
}

TAILS = {
    "up": [".hh..", "hww..", ".ww..", "..ww.", "...ww"],
    "left": ["hh....", "hwww..", ".gwww.", "....ww"],
    "right": ["..hh.", ".hww.", "..ww.", "..ww.", "...ww"],
    "flat": ["hhh...", "wwwwww"],
    "down": ["...ww", "..ww.", ".ww..", "hw...", "h...."],
}


class Layer:
    def __init__(self) -> None:
        self.px: dict[tuple[int, int], str] = {}

    def put(self, x: int, y: int, c: str) -> None:
        if 0 <= x < FRAME and 0 <= y < FRAME:
            self.px[(x, y)] = c

    def stamp(self, rows: list[str], at: tuple[int, int], flip: bool = False) -> None:
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch != ".":
                    x = at[0] + (len(row) - 1 - i if flip else i)
                    self.put(x, at[1] + j, ch)

    def limb(self, a: tuple[int, int], b: tuple[int, int], c: str, w: int = 2) -> None:
        steps = max(abs(b[0] - a[0]), abs(b[1] - a[1]), 1)
        for i in range(steps + 1):
            x = round(a[0] + (b[0] - a[0]) * i / steps)
            y = round(a[1] + (b[1] - a[1]) * i / steps)
            for k in range(w):
                self.put(x + k, y, c)


def compose(layers: list[tuple[Layer, set[int]]]) -> Image.Image:
    img = Image.new("RGBA", (FRAME, FRAME), (0, 0, 0, 0))
    out = img.load()
    owner: dict[tuple[int, int], int] = {}
    for idx, (L, cuts) in enumerate(layers):
        for (x, y) in L.px:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + dx, y + dy)
                if n in L.px or not (0 <= n[0] < FRAME and 0 <= n[1] < FRAME):
                    continue
                if n in owner and owner[n] not in cuts:
                    continue
                out[n] = rgba(PAL[OUTLINE])
        for (x, y), c in L.px.items():
            out[x, y] = rgba(PAL[c])
            owner[(x, y)] = idx
    return img


SIT = [
    ".......hhww.",
    "......hwwwww",
    ".....httTwww",
    "....htttwwww",
    "...htttTwwww",
    "..hwTTwwwwww",
    ".hwwwwwOwww.",
    "hwwwwwOwOwwG",
    "wwwwwOwwOwwG",
    "gggwwwwwOwwG",
]
LIE = [
    "...hhtmmthhh......",
    ".hwwtttttTwww.....",
    "hwwOwTTTwwwwww....",
    "wwOwwwwwwwwwwwwww.",
    "ggOgggggggggwwOwww",
]
TAILS_GROUND = {
    "a": ["hhwww"],
    "b": ["h....", ".hwww"],
    "c": ["hh...", "..www"],
}
SMALL_Z = ["zzz", ".z.", "zzz"]
BIG_Z = ["zzzz", "..z.", ".z..", "zzzz"]


def pose(**kw) -> dict:
    p = dict(kind="stand", body=(0, 0), torso="stand", head=(0, 0), face="n", ear="up",
             tail="up", legs=STAND_LEGS, knee={}, marks=(), neck=True, head_seam=False)
    p.update(kw)
    return p


STAND_LEGS = dict(fn=(0, SOLE_Y), ff=(-2, SOLE_Y), bn=(0, SOLE_Y), bf=(2, SOLE_Y))


def frame(p: dict) -> Image.Image:
    bx, by = p["body"]
    legs_far, ear_far, mid, body, top = Layer(), Layer(), Layer(), Layer(), Layer()
    head = Layer() if p["head_seam"] else body
    ear_layer = Layer() if EAR_SEAM else head
    ear = p["ear"]

    def head_at(hx: int, hy: int) -> None:
        ear_far.stamp(EAR_FAR[ear], (hx + EAR_FAR_AT[0], hy + EAR_FAR_AT[1]))
        head.stamp(HEADS[p["face"]], (hx, hy))
        if p["neck"]:
            head.stamp(NECK, (hx - 2, hy + 4))
        for dx, dy, c in COLLAR if p["neck"] else ():
            head.put(hx + dx, hy + dy, c)
        ear_layer.stamp(EAR_NEAR[ear], (hx + EAR_NEAR_AT[0], hy + EAR_NEAR_AT[1]))

    if p["kind"] == "stand":
        torso = TORSO[p["torso"]]
        tw = len(torso[0])
        tx = AX - 7 + bx - (tw - 13) // 2
        ty = 24 + by + LEG_DROP
        hip_back = (tx + 1, ty + 2)
        hip_front = (tx + tw - 4, ty + 2)

        def leg(layer: Layer, hip: tuple[int, int], key: str, c: str) -> None:
            fx, fy = p["legs"][key]
            foot = (hip[0] + fx, fy)
            knee = p["knee"].get(key)
            if knee:
                k = (hip[0] + knee[0], hip[1] + knee[1])
                layer.limb(hip, k, c)
                layer.limb(k, foot, c)
            else:
                layer.limb(hip, foot, c)
            layer.put(foot[0] + 2, foot[1], c)

        leg(legs_far, hip_back, "bf", "G")
        leg(legs_far, hip_front, "ff", "G")
        tail = TAILS[p["tail"]]
        mid.stamp(tail, (tx - len(tail[0]) + 2, ty - len(tail) + 2))
        leg(body, hip_back, "bn", "w")
        leg(body, hip_front, "fn", "w")
        body.stamp(torso, (tx, ty))
        head_at(tx + tw - 5 + p["head"][0], ty - 6 + p["head"][1])
    elif p["kind"] == "sit":
        sx, sy = AX - 7 + bx, SOLE_Y - len(SIT) + 1 + by
        tail = TAILS_GROUND[p["tail"]]
        mid.stamp(tail, (sx - 4, SOLE_Y - len(tail) + 1))
        body.stamp(SIT, (sx, sy))
        head_at(sx + 6 + p["head"][0], sy - 5 + p["head"][1])
    else:
        lx, ly = AX - 9 + bx, SOLE_Y - len(LIE) + 1
        tail = TAILS_GROUND[p["tail"]]
        mid.stamp(tail, (lx - 4, SOLE_Y - len(tail) + 1))
        body.stamp(LIE, (lx, ly))
        if by < 0:
            body.stamp(["hhtmmth"], (lx + 3, ly - 1))
        head_at(lx + 9 + p["head"][0], ly - 5 + p["head"][1])
    for x, y, rows in p["marks"]:
        top.stamp(rows, (x, y))
    layers = [(legs_far, set()), (ear_far, set()), (mid, {0, 1}), (body, {1, 2})]
    if head is not body:
        layers.append((head, {1, 2, 3}))
    if ear_layer is not head:
        layers.append((ear_layer, set(range(1, len(layers)))))
    layers.append((top, set(range(len(layers)))))
    return compose(layers)


def idle(i: int) -> dict:
    tails = ["up", "right", "up", "left"]
    return pose(tail=tails[i % 4], face="blink" if i == 5 else "n",
                head=(0, 1 if i in (2, 3) else 0))


def pant(i: int) -> dict:
    tails = ["up", "right", "up", "left"]
    return pose(tail=tails[i % 4], face="pant", head=(0, i % 2))


def walk(i: int, n: int = 8) -> dict:
    legs = {}
    for key, ph in (("fn", 0.0), ("bf", 0.0), ("ff", 0.5), ("bn", 0.5)):
        t = (i / n + ph) % 1.0
        dx = round(2 * math.cos(2 * math.pi * t))
        lift = 1 if math.sin(2 * math.pi * t) > 0.3 else 0
        base = STAND_LEGS[key][0]
        legs[key] = (base + dx, SOLE_Y - lift)
    tails = ["up", "right", "up", "left"]
    return pose(legs=legs, tail=tails[(i // 2) % 4], head=(0, 1 if i % 4 == 2 else 0))


def run(i: int) -> dict:
    S = SOLE_Y
    frames = [
        dict(body=(0, -1), torso="short", legs=dict(fn=(-2, S), ff=(-3, S - 1), bn=(3, S - 1), bf=(2, S))),
        dict(body=(0, -2), legs=dict(fn=(3, S - 2), ff=(2, S - 3), bn=(-2, S), bf=(-3, S - 1)),
             knee=dict(fn=(2, 1))),
        dict(body=(0, -3), torso="long", legs=dict(fn=(4, S - 3), ff=(3, S - 2), bn=(-4, S - 2), bf=(-3, S - 3))),
        dict(body=(0, -2), legs=dict(fn=(2, S), ff=(1, S - 1), bn=(-3, S - 2), bf=(-2, S - 3))),
        dict(body=(0, -1), torso="short", legs=dict(fn=(-1, S), ff=(-2, S), bn=(1, S - 2), bf=(0, S - 2))),
        dict(body=(0, 0), torso="short", legs=dict(fn=(-2, S), ff=(-2, S), bn=(2, S - 1), bf=(3, S))),
    ]
    return pose(face="pant", ear="back", tail="flat", head=(1, 1 if i in (0, 4, 5) else 0), **frames[i])


S_ = SOLE_Y
JUMP = [
    pose(body=(0, -1), head=(0, -1), ear="back", tail="left",
         legs=dict(fn=(2, S_ - 3), ff=(1, S_ - 2), bn=(-2, S_), bf=(-1, S_ - 1)),
         knee=dict(fn=(2, 1), ff=(2, 1))),
    pose(body=(0, -1), head=(0, -1), ear="back", tail="left",
         legs=dict(fn=(3, S_ - 2), ff=(2, S_ - 2), bn=(-3, S_ - 1), bf=(-2, S_ - 1))),
]
FALL = [
    pose(body=(0, -1), ear="perk", tail="up",
         legs=dict(fn=(2, S_), ff=(1, S_ - 1), bn=(2, S_ - 2), bf=(3, S_ - 2))),
    pose(body=(0, -1), ear="perk", tail="right",
         legs=dict(fn=(2, S_), ff=(1, S_ - 1), bn=(2, S_ - 2), bf=(3, S_ - 2))),
]
LAND = [
    pose(body=(0, 1), head=(0, 1), ear="back", tail="left",
         legs=dict(fn=(1, S_), ff=(-1, S_), bn=(-1, S_), bf=(1, S_))),
    pose(),
]


def sit(i: int) -> dict:
    tails = ["a", "b", "a", "c"]
    return pose(kind="sit", tail=tails[i % 4], face="blink" if i == 6 else "n",
                ear="perk" if i in (2, 3) else "up")


def lie(i: int) -> dict:
    return pose(kind="lie", tail="a" if i % 4 else "b", face="blink" if i == 3 else "n",
                body=(0, -1 if i in (1, 2) else 0))


def sleep(i: int) -> dict:
    marks = [(), ((22, 15, SMALL_Z),), ((23, 13, SMALL_Z),), ((24, 10, BIG_Z),)][i]
    return pose(kind="lie", tail="a", face="sleep", ear="flop", neck=False, head_seam=True,
                head=(1, 3), body=(0, -1 if i % 2 else 0), marks=marks)


def bark(i: int) -> dict:
    return pose(face=["n", "bark", "bark", "n"][i], ear="perk",
                tail=["up", "right", "left", "up"][i],
                head=[(0, 0), (0, -1), (1, -1), (0, 0)][i],
                body=[(0, 0), (-1, 0), (-1, 0), (0, 0)][i])


def sniff(i: int) -> dict:
    tails = ["up", "right", "up", "left"]
    return pose(tail=tails[(i // 2) % 4], neck=False, head=(1 + (i % 2), 4),
                legs=dict(fn=(1, SOLE_Y), ff=(-1, SOLE_Y), bn=(0, SOLE_Y), bf=(2, SOLE_Y)))


def happy(i: int) -> dict:
    up = [0, -2, -3, -2, 0, 0][i]
    air = up < 0
    legs = dict(fn=(2, SOLE_Y + up - 1), ff=(1, SOLE_Y + up), bn=(-1, SOLE_Y + up),
                bf=(1, SOLE_Y + up)) if air else STAND_LEGS
    return pose(body=(0, up), face="pant", ear="perk" if air else "up",
                tail=["right", "left"][i % 2], legs=legs, knee=dict(fn=(2, 1)) if air else {})


ANIMS = [
    ("idle", 6, True, [idle(i) for i in range(8)]),
    ("pant", 8, True, [pant(i) for i in range(4)]),
    ("walk", 10, True, [walk(i) for i in range(8)]),
    ("run", 14, True, [run(i) for i in range(6)]),
    ("jump", 10, False, JUMP),
    ("fall", 8, True, FALL),
    ("land", 12, False, LAND),
    ("sit", 5, True, [sit(i) for i in range(8)]),
    ("lie", 3, True, [lie(i) for i in range(4)]),
    ("sleep", 2, True, [sleep(i) for i in range(4)]),
    ("bark", 10, True, [bark(i) for i in range(4)]),
    ("sniff", 8, True, [sniff(i) for i in range(8)]),
    ("happy", 10, True, [happy(i) for i in range(6)]),
]
COLS = max(len(a[3]) for a in ANIMS)


def build(image: str = "dog.png") -> tuple[Image.Image, dict]:
    sheet = Image.new("RGBA", (FRAME * COLS, FRAME * len(ANIMS)), (0, 0, 0, 0))
    meta = {"image": image, "frame_w": FRAME, "frame_h": FRAME, "scale": 1.0, "animations": {}}
    for row, (name, fps, loop, poses) in enumerate(ANIMS):
        meta["animations"][name] = {"row": row, "frames": len(poses), "fps": fps, "loop": loop}
        for col, p in enumerate(poses):
            sheet.paste(frame(p), (col * FRAME, row * FRAME))
    return sheet, meta


def main() -> None:
    sheet, meta = build()
    if "--preview" in sys.argv:
        out = sys.argv[sys.argv.index("--preview") + 1]
        sheet.save(out)
        return
    save(sheet, "sprites", "dog", "dog.png")
    save_json(meta, "sprites", "dog", "dog.json")
    print("cachorro: ok")


if __name__ == "__main__":
    main()
