from __future__ import annotations

import math

from PIL import Image

from vec import rgba, save, save_json

FRAME = 32
OUTLINE = "#222034"

HAIR_COLOR = "#9a5a38"
HAIR_SHADES = {"H": 1.0, "h": 0.72, "u": 0.45}

PAL = {
    "d": "#2a1810",
    "b": "#6f4128", "B": "#8a5233", "g": "#4a2b1b",
    "s": "#e4b58f", "S": "#f3cda9", "z": "#c48f6c", "n": "#d9957a", "c": "#e8998a",
    "e": "#1d4d36", "f": "#1d4d36",
    "w": "#4b4b88", "W": "#3f3f74", "v": "#2f2f58",
    "M": "#4b4b88",
    "t": "#2f8063", "G": "#37946e", "a": "#52ae86", "m": "#195d41",
    "j": "#3a3c48", "J": "#4c4f5c",
    "o": "#5a4036", "O": "#6f5143", "k": "#3b2a24",
    "1": "#fffaf0", "2": "#f1dfbc", "3": "#dba55e", "4": "#9c6336",
    "x": "#3b2a24",
    "y": "#ab7c5e",
    "P": "#e0705a", "p": "#c04a3a", "q": "#8a3030", "r": "#f0e0c8",
    "F": "#f0e0c8", "i": "#c04a3a", "I": "#8a3030",
    "K": "#3a2a28", "L": "#262838", "l": "#9ab4d8",
}

HEAD = [
    "......hHH.",
    "..hhHHHHHh",
    "uhhhhhhHHh",
    "uhhsSSSSSh",
    "uhhSSSSSS.",
    "shbSSeSfS.",
    "zhbbSeSfSn",
    "uhbbSSsSS.",
    "uubbbBbbb.",
    ".ugbbbbbb.",
    "..ggbbbb..",
]
TUFT = {
    "back": (["...hHH....", ".hhHHHHHh."], 0),
    "up": (["......H...", ".....hHH..", "..hhHHHHHh"], 1),
    "up2": ([".......H..", ".....hHH..", "..hhHHHHHh"], 1),
    "sway": ([".....hHH..", "..hhHHHHHh"], 0),
}

TORSO = [
    "WwwwMw",
    "WttwMw",
    "WWttMw",
    "vWwttM",
    "vWWwtt",
    "jjjJJJ",
]
PACK = [
    ".GG",
    "GaG",
    "GGm",
    "GGm",
    "mGm",
    ".mm",
]
BOOT_FRONT = ["OO.", "ooo"]
BOOT_BACK = ["oo.", "kkk"]

LOOK_DEFAULT = {"hat": "none", "beard": "full", "glasses": "none", "scarf": "none"}

BEARDS = {
    "full": HEAD[5:],
    "stubble": [
        "shhSSeSfS.",
        "zhySSeSfSn",
        "uhyySSsSS.",
        ".uyyyyyyy.",
        "..yyyyyy..",
        "...yyy....",
    ],
    "mustache": [
        "shhSSeSfS.",
        "zhhSSeSfSn",
        "uhzSSSSSS.",
        ".uzSSbBbb.",
        "..zzSSSs..",
        "...zzz....",
    ],
    "none": [
        "shhSSeSfS.",
        "zhhSSeSfSn",
        "uhzSSSSSS.",
        ".uzSSSSSs.",
        "..zzSSSs..",
        "...zzz....",
    ],
}
HATS = {
    "none": None,
    "beanie": ([
        "...pPPPp....",
        "..pPPPPPpp..",
        ".pPPPPPPPpq.",
        ".qpqpqpqpqq.",
    ], (-1, -2)),
    "cap": ([
        "...ppPPp.....",
        "..pPPPPPPp...",
        ".qpPPPPPPPp..",
        ".qqpppppqqqqq",
    ], (-1, -1)),
    "bucket": ([
        "...pPPPPp...",
        "..pPPPPPPp..",
        "..prrrrrrp..",
        "qppppppppppq",
        "q..........q",
    ], (-1, -1)),
    "ranger": ([
        "....pPPp......",
        "...pPPpPPp....",
        "...pPPPPPp....",
        "...rrrrrrr....",
        "qqppppppppppq.",
    ], (-2, -2)),
}
GLASSES = {
    "none": None,
    "round": ([
        ".KK.KK",
        "K..K..",
    ], (3, 4)),
    "shades": ([
        "KLlKLl",
        ".LL.LL",
    ], (3, 5)),
}
SCARF_NECK = ([
    "iFiFiFii",
    "IiiiiiiI",
], (12, 21))
SCARF_TAIL = {
    "hang": (["i", "F", "I"], (12, 23)),
    "fly": (["FiFi.", ".IiiI"], (8, 22)),
    "up": (["i", "F", "i"], (11, 19)),
}

TORSO_AT = (13, 21)
PACK_AT = (10, 20)
SHOULDER_FRONT = (15, 23)
SHOULDER_BACK = (13, 23)
HIP_Y = 27
SOLE_Y = 30

HAIR_LETTERS = set(HAIR_SHADES)


def hair_rgb(letter: str) -> tuple[int, int, int, int]:
    r, g, b, _ = rgba(HAIR_COLOR)
    k = HAIR_SHADES[letter]
    return (round(r * k), round(g * k), round(b * k), 255)


class Pix:

    def __init__(self) -> None:
        self.px: dict[tuple[int, int], str] = {}
        self.part: dict[tuple[int, int], str] = {}
        self.current = ""

    def put(self, x: int, y: int, letter: str) -> None:
        if 0 <= x < FRAME and 0 <= y < FRAME:
            self.px[(x, y)] = letter
            self.part[(x, y)] = self.current

    def stamp(self, rows: list[str], at: tuple[int, int]) -> None:
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch != ".":
                    self.put(at[0] + i, at[1] + j, ch)

    def block(self, x: int, y: int, w: int, h: int, letter: str) -> None:
        for j in range(h):
            for i in range(w):
                self.put(x + i, y + j, letter)

    def limb(self, a: tuple[int, int], b: tuple[int, int], letter: str) -> None:
        steps = max(abs(b[0] - a[0]), abs(b[1] - a[1]), 1)
        upright = abs(b[1] - a[1]) >= abs(b[0] - a[0])
        for i in range(steps + 1):
            x = round(a[0] + (b[0] - a[0]) * i / steps)
            y = round(a[1] + (b[1] - a[1]) * i / steps)
            self.block(x, y, 2 if upright else 1, 1 if upright else 2, letter)

    def final(self) -> dict[tuple[int, int], str]:
        out: dict[tuple[int, int], str] = {}
        for (x, y), letter in self.px.items():
            if self.part[(x, y)] == "pack" and self._beside_body(x, y):
                out[x, y] = "@"
            else:
                out[x, y] = letter
        for (x, y) in list(self.px):
            if self.part[(x, y)] == "thin":
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + dx, y + dy)
                if n not in self.px and 0 <= n[0] < FRAME and 0 <= n[1] < FRAME:
                    out[n] = "@"
        return out

    def image(self, pal: dict[str, str]) -> Image.Image:
        body = Image.new("RGBA", (FRAME, FRAME), (0, 0, 0, 0))
        out = body.load()
        for (x, y), letter in self.final().items():
            if letter == "@":
                out[x, y] = rgba(OUTLINE)
            elif letter in pal:
                out[x, y] = rgba(pal[letter])
            elif letter in HAIR_LETTERS:
                out[x, y] = hair_rgb(letter)
            else:
                out[x, y] = rgba(PAL[letter])
        return body

    def _beside_body(self, x: int, y: int) -> bool:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if self.part.get((x + dx, y + dy), "pack") not in ("pack", "arm_back"):
                return True
        return False


def pose(**kw) -> dict:
    p = dict(body=(0, 0), head=(0, 0), pack=(0, 0), ff=(16, SOLE_Y), bf=(13, SOLE_Y),
             fh=(16, 26), bh=(13, 26), fe=None, be=None, fist=2, arm_behind=False,
             tuft="", blink=False, eyes="", stick=None, marks=())
    p.update(LOOK_DEFAULT)
    p.update(kw)
    return p


def idle_pose(i: int) -> dict:
    k = i % 6
    bob = (0, 0, 1, 1, 1, 0)[k]
    lag = (0, 0, 0, 1, 1, 1)[k]
    return pose(head=(0, bob), pack=(0, lag), fh=(16, 26 + bob), bh=(13, 26 + lag),
                blink=i == 9, tuft="sway" if i in (3, 4) else "")


def run_pose(i: int, frames: int = 8) -> dict:
    a = 2 * math.pi * i / frames

    def foot(x: float, hip: int) -> tuple[int, int]:
        return (round(hip + 3.4 * math.cos(x)), SOLE_Y - round(2.6 * max(0.0, -math.sin(x))))

    down = 1 if i % 4 == 1 else 0
    lag = 1 if i % 4 == 2 else 0
    swing = round(1.2 * abs(math.cos(a)))
    return pose(body=(0, down), head=(1, 0), pack=(0, lag - down),
                ff=foot(a, 15), bf=foot(a + math.pi, 14),
                fh=(round(15.5 - 3.6 * math.cos(a)), 25 - swing + down),
                bh=(round(14.5 + 3.6 * math.cos(a)), 25 - swing + down), tuft="back")


JUMP = [
    pose(body=(0, -1), head=(0, -1), pack=(0, 2), ff=(16, SOLE_Y), bf=(13, SOLE_Y), fh=(17, 26), bh=(12, 25)),
    pose(head=(0, -1), pack=(0, 1), ff=(17, 28), bf=(12, 29), fh=(19, 21), bh=(11, 25)),
]
APEX = [
    pose(ff=(17, 28), bf=(12, 28), fh=(19, 23), bh=(10, 23)),
    pose(ff=(17, 28), bf=(12, 28), fh=(19, 23), bh=(10, 24), pack=(0, -1), tuft="sway"),
]
FALL = [
    pose(pack=(0, -1), ff=(17, SOLE_Y), bf=(12, 28), fh=(21, 19), bh=(10, 20), tuft="up"),
    pose(pack=(0, -1), ff=(17, SOLE_Y), bf=(12, 28), fh=(21, 18), bh=(10, 21), tuft="up2"),
]
LAND = [
    pose(body=(0, 1), head=(0, 1), pack=(0, 1), ff=(17, SOLE_Y), bf=(11, SOLE_Y), fh=(19, 26), bh=(10, 26)),
    pose(head=(0, 1), pack=(0, 1), ff=(17, SOLE_Y), bf=(12, SOLE_Y), fh=(18, 26), bh=(11, 26)),
]
WALL = [
    pose(head=(-1, 0), pack=(0, 0), ff=(17, 28), bf=(16, SOLE_Y), fh=(19, 19), bh=(19, 23), tuft="up"),
    pose(head=(-1, 0), pack=(0, -1), ff=(17, 28), bf=(16, 29), fh=(19, 19), bh=(19, 23), tuft="up2"),
]
DASH = [
    pose(head=(2, 2), body=(1, 1), pack=(0, -1), ff=(10, 29), bf=(8, 27), fh=(23, 23), bh=(11, 25), fist=3, tuft="back"),
    pose(head=(2, 2), body=(1, 1), pack=(0, -2), ff=(10, 29), bf=(8, 27), fh=(23, 23), bh=(11, 25), fist=3, tuft="back"),
]
DASH_UP = [
    pose(body=(0, -1), head=(0, -1), pack=(0, 2), fh=(17, 6), arm_behind=True, bh=(12, 26), fist=3, ff=(16, SOLE_Y), bf=(14, SOLE_Y), tuft="back"),
    pose(body=(0, -1), head=(0, -1), pack=(0, 3), fh=(17, 6), arm_behind=True, bh=(12, 26), fist=3, ff=(16, SOLE_Y), bf=(14, 29), tuft="back"),
]
DASH_DOWN = [
    pose(head=(0, 1), pack=(0, -2), fh=(18, 25), bh=(11, 25), ff=(17, 27), bf=(12, 27), tuft="up"),
    pose(head=(0, 1), pack=(0, -3), fh=(18, 25), bh=(11, 25), ff=(17, 27), bf=(12, 27), tuft="up2"),
]
PUSH = [
    pose(head=(-1, 1), fh=(19, 23), bh=(19, 25), ff=(15, SOLE_Y), bf=(10, SOLE_Y)),
    pose(head=(-1, 1), pack=(0, 1), fh=(19, 23), bh=(19, 25), ff=(15, SOLE_Y), bf=(11, SOLE_Y)),
]

SIT = [
    pose(body=(0, 2), fh=(17, 28), bh=(13, 28), ff=(19, SOLE_Y), bf=(17, SOLE_Y)),
    pose(body=(0, 2), head=(0, 1), pack=(0, 1), fh=(17, 28), bh=(13, 28), ff=(19, SOLE_Y), bf=(17, SOLE_Y)),
]
SEATED = dict(body=(0, 2), ff=(19, SOLE_Y), bf=(17, SOLE_Y), bh=(13, 28))
SMALL_Z = ["111", ".1.", "111"]
BIG_Z = ["1111", "..1.", ".1..", "1111"]


def roast_pose(i: int) -> dict:
    bob = i % 2
    if i < 6:
        tone = "112233"[i]
        return pose(**SEATED, head=(0, 0), fh=(20, 25), stick=(28, 23 - bob, tone))
    if i < 8:
        return pose(**SEATED, head=(1 if i == 7 else 0, 0), fe=(19, 27), fh=(20, 24), stick=(24, 20, "3"))
    if i < 11:
        return pose(**SEATED, head=(0, (0, 1, 0)[i - 8]), fe=(19, 27), fh=(20, 24), stick=(24, 20, ""), blink=i == 9)
    return pose(**SEATED, fh=(19, 26), stick=(26, 23, "1"))


def think_pose(i: int) -> dict:
    dots = [(22, 14, ["1"]), (24, 11, ["11", "11"]), (26, 6, [".11.", "1111", "1111", ".11."])][:max(0, min(3, i))]
    return pose(**SEATED, head=(0, -1 if i > 0 else 0), fe=(19, 27), fh=(18, 23), marks=tuple(dots), blink=i == 5)


def sleep_pose(i: int) -> dict:
    zs = [[(22, 13, SMALL_Z)], [(23, 10, SMALL_Z)], [(24, 7, SMALL_Z), (21, 13, SMALL_Z)], [(25, 3, BIG_Z), (22, 10, SMALL_Z)]][i]
    breath = (0, 0, 1, 1)[i]
    return pose(**SEATED, head=(1, 2 + breath), pack=(0, breath), fh=(17, 28), eyes="closed", marks=tuple(zs))


def swim_pose(i: int) -> dict:
    reach = (23, 21, 18, 20)[i]
    kick = (0, 1, 0, -1)[i]
    return pose(head=(2, 2), body=(1, 1), pack=(0, -1), ff=(10, 29 + kick), bf=(8, 27 - kick),
                fh=(reach, 23 + (i % 2)), bh=(11 + (i % 2), 25), tuft="back")


def float_pose(i: int) -> dict:
    bob = (0, 0, 1, 1)[i]
    kick = (0, 1, 0, -1)[i]
    return pose(head=(0, bob), pack=(0, bob), fh=(20, 23 + (i % 2)), bh=(9, 23 + ((i + 1) % 2)),
                ff=(17, SOLE_Y - 1 - max(0, kick)), bf=(12, SOLE_Y - 1 - max(0, -kick)))


CROUCH = [
    pose(body=(0, 2), head=(0, 1), pack=(0, 1), fh=(18, 27), bh=(11, 27), ff=(17, SOLE_Y), bf=(12, SOLE_Y)),
    pose(body=(0, 2), head=(0, 2), pack=(0, 1), fh=(18, 27), bh=(11, 27), ff=(17, SOLE_Y), bf=(12, SOLE_Y)),
]

ANIMS = [
    ("idle", 7, True, [idle_pose(i) for i in range(12)]),
    ("run", 14, True, [run_pose(i) for i in range(8)]),
    ("jump", 12, False, JUMP),
    ("apex", 6, True, APEX),
    ("fall", 8, True, FALL),
    ("land", 12, False, LAND),
    ("wall_slide", 6, True, WALL),
    ("dash", 14, True, DASH),
    ("dash_up", 14, True, DASH_UP),
    ("dash_down", 14, True, DASH_DOWN),
    ("push", 5, True, PUSH),
    ("sit", 2, True, SIT),
    ("crouch", 3, True, CROUCH),
    ("sit_roast", 3, True, [roast_pose(i) for i in range(12)]),
    ("sit_think", 2, False, [think_pose(i) for i in range(6)]),
    ("sleep", 2, True, [sleep_pose(i) for i in range(4)]),
    ("swim", 7, True, [swim_pose(i) for i in range(4)]),
    ("float", 4, True, [float_pose(i) for i in range(4)]),
]
COLS = max(len(a[3]) for a in ANIMS)


def offset(at: tuple[int, int], by: tuple[int, int]) -> tuple[int, int]:
    return (at[0] + by[0], at[1] + by[1])


def draw_head(c: Pix, p: dict) -> None:
    rows, extra = list(HEAD), 0
    rows[5:] = BEARDS[p.get("beard", "full")]
    hat = HATS.get(p.get("hat", "none"))
    if p["tuft"] in TUFT and not hat:
        top, extra = TUFT[p["tuft"]]
        rows = top + rows[2:]
    if p["blink"] or p["eyes"]:
        rows[5 + extra] = rows[5 + extra].replace("e", "S").replace("f", "S")
    if p["eyes"] == "closed":
        rows[6 + extra] = rows[6 + extra].replace("e", "d").replace("f", "d")
    at = offset((11, 11), offset(p["body"], p["head"]))
    c.stamp(rows, (at[0], at[1] - extra))
    part = c.current
    if hat:
        c.current = "hat"
        c.stamp(hat[0], offset(at, hat[1]))
    glasses = GLASSES.get(p.get("glasses", "none"))
    if glasses:
        c.current = "glasses"
        c.stamp(glasses[0], offset(at, glasses[1]))
    c.current = part


def draw_scarf(c: Pix, p: dict) -> None:
    if p.get("scarf", "none") == "none":
        return
    part = c.current
    c.current = "scarf"
    body = p["body"]
    kind = {"back": "fly", "up": "up", "up2": "up"}.get(p["tuft"], "hang")
    tail, at = SCARF_TAIL[kind]
    c.stamp(tail, offset(at, body))
    c.stamp(SCARF_NECK[0], offset(SCARF_NECK[1], body))
    c.current = part


def draw_leg(c: Pix, hip_x: int, foot: tuple[int, int], body: tuple[int, int], front: bool) -> None:
    top = (hip_x + body[0], HIP_Y + body[1])
    ankle = (foot[0], max(top[1], foot[1] - 2))
    c.limb(top, ankle, "J" if front else "j")
    c.stamp(BOOT_FRONT if front else BOOT_BACK, (foot[0], foot[1] - 1))


def draw_arm(c: Pix, shoulder: tuple[int, int], hand: tuple[int, int], front: bool, fist: int = 2,
             elbow: tuple[int, int] | None = None) -> None:
    sleeve = "W" if front else "v"
    if elbow:
        c.limb(shoulder, elbow, sleeve)
        c.limb(elbow, hand, sleeve)
    else:
        c.limb(shoulder, hand, sleeve)
    c.block(hand[0], hand[1], fist, fist, "s" if front else "z")
    if front:
        c.put(hand[0], hand[1], "S")
        if fist > 2:
            c.put(hand[0] + 1, hand[1], "S")


def draw_pack(c: Pix, p: dict) -> None:
    at = offset(PACK_AT, offset(p["body"], p["pack"]))
    c.stamp(PACK, at)


def draw_frame(p: dict) -> Pix:
    c = Pix()
    body = p["body"]
    c.current = "arm_back"
    draw_arm(c, offset(SHOULDER_BACK, body), p["bh"], front=False, elbow=p["be"])
    c.current = "pack"
    draw_pack(c, p)
    c.current = "legs"
    draw_leg(c, 13, p["bf"], body, front=False)
    draw_leg(c, 16, p["ff"], body, front=True)
    c.current = "torso"
    c.stamp(TORSO, offset(TORSO_AT, body))
    draw_scarf(c, p)
    if p["arm_behind"]:
        c.current = "arm_front"
        draw_arm(c, offset(SHOULDER_FRONT, body), p["fh"], front=True, fist=p["fist"], elbow=p["fe"])
    c.current = "head"
    draw_head(c, p)
    if not p["arm_behind"]:
        c.current = "arm_front"
        draw_arm(c, offset(SHOULDER_FRONT, body), p["fh"], front=True, fist=p["fist"], elbow=p["fe"])
    if p["stick"]:
        tip_x, tip_y, tone = p["stick"]
        hand = (p["fh"][0] + 1, p["fh"][1])
        steps = max(abs(tip_x - hand[0]), abs(tip_y - hand[1]), 1)
        c.current = "thin"
        for k in range(steps + 1):
            c.put(round(hand[0] + (tip_x - hand[0]) * k / steps), round(hand[1] + (tip_y - hand[1]) * k / steps), "x")
        if tone:
            c.current = "item"
            c.block(tip_x - 1, tip_y - 1, 3, 3, tone)
            c.put(tip_x - 1, tip_y - 1, "1" if tone != "4" else "3")
            if tone in "34":
                c.put(tip_x + 1, tip_y + 1, "4")
    c.current = "item"
    for x, y, rows in p["marks"]:
        c.stamp(rows, (x, y))
    return c


def build(pal: dict[str, str] | None = None) -> tuple[Image.Image, dict]:
    pal = pal or PAL
    sheet = Image.new("RGBA", (FRAME * COLS, FRAME * len(ANIMS)), (0, 0, 0, 0))
    meta = {"image": "hero.png", "frame_w": FRAME, "frame_h": FRAME, "scale": 1.0, "animations": {}}
    for row, (name, fps, loop, poses) in enumerate(ANIMS):
        meta["animations"][name] = {"row": row, "frames": len(poses), "fps": fps, "loop": loop}
        for col, p in enumerate(poses):
            sheet.paste(draw_frame(p).image(pal), (col * FRAME, row * FRAME))
    return sheet, meta


def main() -> None:
    sheet, meta = build()
    save(sheet, "sprites", "hero", "hero.png")
    save_json(meta, "sprites", "hero", "hero.json")
    print("personagem: ok")


if __name__ == "__main__":
    main()
