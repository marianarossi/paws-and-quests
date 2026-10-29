from __future__ import annotations

import io
import os

OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "levels", "ember"))
TALL = 45
FLOOR = 42
E1 = (0, 8)
C0_W = 40
C0 = (-C0_W, FLOOR - 20)
E2 = (96, 0)
DEEP = 3
G1 = (206, 0)
G2 = (318, 0)
G3 = (428, 0)
G4 = (540, 0)
G5 = (600, 0)
H1 = (720, 0)
H2 = (820, 0)
H3 = (910, -40)
H4 = (954, -60)
H5 = (1064, -45)
H6 = (1110, -10)
O0 = (1220, -60)
O1 = (1400, 0)
O2 = (1520, 0)
O3 = (1630, 0)
O4 = (1740, 0)
O5 = (1870, -46)
O6 = (1918, -46)
O7 = (2088, 0)
Z1 = (2400, 0)
Z1_W = 112
Z2_W = 40
Z2 = (Z1[0] + Z1_W, FLOOR - 20)


class Grid:
    def __init__(self, w: int, h: int, floor: int, left_open: bool = True, right_open: bool = True, roof: bool = True) -> None:
        self.w, self.h, self.floor = w, h, floor
        self.g = [["."] * w for _ in range(h)]
        self.fill(0, floor, w - 1, h - 1)
        if roof:
            self.fill(0, 0, w - 1, 1)
            top = floor - 5
            self.fill(0, 0, 1, top if left_open else floor - 1)
            self.fill(w - 2, 0, w - 1, top if right_open else floor - 1)

    def fill(self, x0: int, y0: int, x1: int, y1: int, ch: str = "#") -> None:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if 0 <= x < self.w and 0 <= y < self.h:
                    self.g[y][x] = ch

    def put(self, x: int, y: int, ch: str) -> None:
        self.g[y][x] = ch

    def stand(self, x: int, ch: str) -> None:
        self.put(x, self.floor - 1, ch)

    def island(self, x0: int, y: int, x1: int, on_top: dict | None = None) -> None:
        self.fill(x0, y, x1, y + 1)
        for x, ch in (on_top or {}).items():
            self.put(x, y - 1, ch)

    def mound(self, x0: int, x1: int, height: int) -> None:
        for k in range(height):
            self.fill(x0 + k, self.floor - 1 - k, x1 - k, self.floor - 1 - k)

    def log(self, x0: int, y: int, x1: int) -> None:
        self.fill(x0, y, x1, y, "=")

    def pit(self, x0: int, x1: int) -> None:
        self.fill(x0, self.floor, x1, self.floor, "^")

    def pond(self, x0: int, x1: int, depth: int = 2) -> None:
        self.fill(x0, self.floor, x1, self.floor + depth - 1, "W")

    def hole(self, x0: int, x1: int) -> None:
        self.fill(x0, self.floor, x1, self.h - 1, ".")

    def campfire(self, x: int) -> None:
        self.stand(x, "C")

    def floating(self, x0: int, y: int, x1: int, depth: int = 3, on_top: dict | None = None) -> None:
        inset = 0
        for k in range(depth):
            if x1 - x0 - 2 * inset < 1:
                break
            self.fill(x0 + inset, y + k, x1 - inset, y + k)
            inset += 1 + k // 2
        for x, ch in (on_top or {}).items():
            self.put(x, y - 1, ch)

    def save(self, name: str, comment: str, pos: tuple, area: str, defs: tuple = (), zone: str | None = None, header: tuple = ()) -> None:
        zone = zone or {"ember_camp": "ember", "twilight_grove": "twilight_grove"}.get(area, "forest")
        text = "; %s\nid: %s\nzone: %s\narea: %s\npos: %d,%d\n%s---\n" % (comment, name, zone, area, pos[0], pos[1], "".join(h + "\n" for h in header))
        text += "\n".join("".join(r) for r in self.g) + "\n"
        if defs:
            text += "---\n" + "\n".join(defs) + "\n"
        io.open(os.path.join(OUT, name + ".room"), "w", encoding="utf-8", newline="\n").write(text)


def camp_site() -> None:
    w, f = C0_W, FLOOR - C0[1]
    r = Grid(w, f + DEEP, f, roof=False)
    r.fill(0, 0, 2, f - 1)
    r.fill(3, 0, 3, 6)
    r.fill(3, 0, 4, 2)
    for x in range(5, w):
        r.stand(x, "k")
    r.stand(10, "t")
    r.stand(12, "y")
    r.stand(15, "b")
    r.stand(16, "d")
    r.stand(19, "P")
    r.stand(20, "C")
    r.save("c0", "Ember Camp 0: o acampamento, onde o jogo comeca. A abertura: a bolinha, o cachorro que foge para a direita, o trovao e o clarao.",
           C0, "ember_camp", ("t: sprite file=camp_tent.png left=1 z=-1 light=ffb36b lr=44 lx=43 ly=34",
                              "b: sprite file=camp_bowl.png z=0", "d: dog anim=lie camp=1", "k: clear", "y: diary"))


def camp() -> None:
    r = Grid(96, FLOOR - E1[1] + DEEP, FLOOR - E1[1], roof=False)
    f = r.floor
    r.stand(6, "P")
    r.stand(9, "C")
    r.stand(12, "m")
    r.stand(15, "j")
    r.fill(18, f - 1, 33, f - 1)
    r.fill(22, f - 2, 33, f - 2)
    r.put(23, f - 3, "k")
    r.fill(26, f - 4, 33, f - 3)
    r.put(28, f - 5, "C")
    r.hole(34, 37)
    r.fill(38, f - 4, 45, f - 1)
    r.hole(46, 51)
    r.fill(52, f - 4, 60, f - 1)
    r.fill(54, f - 5, 55, f - 5, "^")
    r.put(60, f - 5, "M")
    r.hole(61, 62)
    r.fill(63, f - 8, 73, f - 1)
    r.put(65, f - 9, "C")
    r.fill(66, 9, 69, 21)
    r.fill(67, 22, 69, 22)
    r.fill(68, 23, 69, 23)
    r.put(71, f - 9, "l")
    r.put(67, 7, "q")
    r.fill(74, 17, 77, f - 1)
    r.put(76, 16, "g")
    r.hole(78, 88)
    r.fill(78, 24, 80, 24, "a")
    r.fill(89, 21, 95, f - 1)
    r.put(90, 20, "C")
    r.put(93, 19, "r")
    r.put(95, 20, "P")
    r.save("e1", "Ember Camp 1: o acampamento ao por do sol. Tutorial sem o dash: pular, buracos sem fundo, espinhos, mola, pulo de parede, agarrar a parede e o tronco; no fim a rosa de Afrodite da o dash.",
           E1, "ember_camp", ("m: hint text=HINT_MOVE", "j: hint text=HINT_JUMP", "k: hint text=HINT_JUMP_HOLD",
                              "l: hint text=HINT_WALL", "g: hint text=HINT_GRAB", "a: mover to=8,0 time=2.2",
                              "r: gift ability=dash", "q: feather"))


def meadow() -> None:
    r = Grid(110, FLOOR + DEEP, FLOOR, roof=False)
    top = 29
    r.fill(0, top, 7, FLOOR - 1)
    r.put(1, top - 1, "P")
    r.put(3, top - 1, "C")
    r.put(6, top - 1, "d")
    r.hole(8, 16)
    r.fill(17, top, 33, FLOOR - 1)
    r.put(19, top - 1, "C")
    r.put(23, top - 1, "u")
    r.fill(28, top - 6, 33, top - 1)
    r.put(31, top - 7, "i")
    r.hole(34, 90)
    r.floating(39, 18, 45)
    r.put(43, 17, "p")
    r.put(53, 15, "*")
    r.put(57, 12, "q")
    r.floating(62, 18, 68)
    r.put(64, 17, "C")
    r.fill(74, 18, 76, 18, "~")
    r.put(84, 15, "*")
    r.fill(91, 19, 97, FLOOR - 1)
    for y, x0, x1 in ((22, 98, 99), (28, 98, 100), (34, 98, 99), (40, 98, 99)):
        r.fill(x0, y, x1, y)
        r.fill(x0, y + 1, x0, y + 1)
    for y, x0, x1 in ((25, 102, 105), (31, 103, 107), (37, 102, 106)):
        r.floating(x0, y, x1, depth=2)
    r.stand(106, "C")
    r.stand(108, "P")
    r.save("e2", "Ember Camp 2: o prado ao por do sol. Tutorial do dash com buracos sem fundo: abismo, dash para cima, diagonal, a pata, laje e dois dashes; descida aos saltos para o Twilight Grove.",
           E2, "ember_camp", ("d: hint text=HINT_DASH", "u: hint text=HINT_DASH_UP", "i: hint text=HINT_DASH_DIAGONAL",
                              "p: hint text=HINT_PAW", "q: feather"))


GROUND_EXTRA = 5
NIGHT_HEADER = ("camfloor: -1,0,%d" % TALL, "bgfloor: %d" % TALL)
NUT = "speed=32"


def night_grid(w: int) -> Grid:
    return Grid(w, TALL + GROUND_EXTRA, FLOOR, roof=False)


def grove_1() -> None:
    r = night_grid(112)
    f = FLOOR
    r.stand(1, "P")
    r.mound(4, 11, 1)
    r.put(8, f - 2, "C")
    r.stand(28, "o")
    r.pit(35, 37)
    r.fill(40, f - 1, 41, f - 1)
    r.island(44, 37, 52, {50: "O"})
    r.stand(46, "e")
    r.fill(54, f - 1, 55, f - 1)
    r.pit(56, 59)
    r.fill(60, f - 2, 61, f - 1)
    r.pit(62, 65)
    r.mound(68, 76, 2)
    r.put(72, f - 3, "C")
    r.pit(79, 81)
    r.fill(82, f, 90, f + 1, ".")
    r.put(83, f + 1, "d")
    r.put(86, f + 1, "e")
    r.put(89, f + 1, "d")
    r.pit(91, 93)
    r.island(97, 38, 102, {100: "u"})
    r.put(101, 27, "n")
    r.fill(105, 35, 108, f - 1)
    r.floating(78, 35, 81)
    r.put(86, 31, "*")
    r.put(91, 30, "*")
    r.floating(95, 30, 100, 3, {97: "^"})
    r.put(97, 27, "q")
    r.save("g1", "Twilight Grove 1: entrada do bosque. Balanos (a bolota) e os primeiros espinhos; no fim bolota e nuvenzinha juntas; desvio opcional de patas por cima.",
           G1, "twilight_grove", ("o: acorn dir=-1 edge=turn " + NUT, "O: acorn dir=-1 " + NUT, "d: acorn dir=-1 " + NUT,
                                  "e: acorn dir=1 " + NUT, "u: acorn dir=1 edge=turn " + NUT,
                                  "n: emitter pattern=aimed every=2.6 reach=160", "q: feather"), header=NIGHT_HEADER)


def grove_2() -> None:
    r = night_grid(110)
    f = FLOOR
    r.stand(1, "P")
    r.mound(3, 9, 1)
    r.put(6, f - 2, "C")
    r.stand(14, "h")
    r.island(18, 37, 22)
    r.island(28, 37, 32)
    r.stand(24, "d")
    r.stand(35, "e")
    r.fill(40, f - 1, 40, f - 1)
    r.put(34, 28, "a")
    r.pit(42, 66)
    for x0 in (44, 51, 58):
        r.floating(x0, 39, x0 + 3, 2)
    r.put(53, 28, "b")
    r.put(52, 32, "q")
    r.mound(69, 76, 2)
    r.put(72, f - 3, "C")
    r.hole(78, 99)
    r.floating(80, 37, 83, 2)
    r.put(88, 33, "*")
    r.put(93, 31, "*")
    r.put(90, 22, "c")
    r.floating(98, 33, 106, 3, {104: "u"})
    r.save("g2", "Twilight Grove 2: clareira das nuvens. As nuvenzinhas e as faiscas: abrigos com bolotas, ilhas sobre espinhos, patas sobre o buraco debaixo de uma rajada.",
           G2, "twilight_grove", ("h: hint text=HINT_DASH_SPARK", "a: emitter pattern=aimed every=3 speed=100 reach=208",
                                  "b: emitter pattern=aimed every=2.2 reach=176", "c: emitter pattern=burst every=2.6 reach=176",
                                  "d: acorn dir=-1 " + NUT, "e: acorn dir=1 " + NUT, "u: acorn dir=-1 edge=turn " + NUT,
                                  "q: feather"),
           header=NIGHT_HEADER)


def grove_3() -> None:
    r = night_grid(112)
    f = FLOOR
    r.stand(1, "P")
    r.mound(3, 10, 1)
    r.put(6, f - 2, "C")
    r.fill(18, 33, 34, 35)
    r.fill(13, 39, 16, 39)
    r.fill(44, 30, 48, 30, "^")
    r.put(46, 27, "q")
    r.put(28, 36, "a")
    r.fill(40, 31, 52, 33)
    r.put(43, 34, "a")
    r.put(50, 34, "a")
    r.fill(56, 35, 68, 36)
    r.fill(57, 37, 59, 37, "v")
    r.put(65, 37, "a")
    r.mound(72, 79, 2)
    r.put(75, f - 3, "C")
    r.floating(81, 37, 83, 2)
    r.fill(85, 33, 104, 35)
    r.put(89, 36, "b")
    r.put(95, 36, "b")
    r.put(101, 36, "b")
    r.stand(92, "d")
    r.stand(97, "e")
    r.stand(102, "d")
    r.fill(90, 32, 91, 32, "^")
    r.fill(97, 32, 98, 32, "^")
    r.put(95, 27, "c")
    r.fill(107, f - 1, 107, f - 1)
    r.save("g3", "Twilight Grove 3: sob as copas. Os morcegos pendurados debaixo das copas; espinhos no teto; duas rotas no fim, debaixo de uma nuvenzinha.",
           G3, "twilight_grove", ("a: bat reach=40", "b: bat reach=36", "c: emitter pattern=aimed every=2.4 reach=160",
                                  "d: acorn dir=-1 " + NUT, "e: acorn dir=1 " + NUT, "q: feather"), header=NIGHT_HEADER)


def grove_4() -> None:
    r = night_grid(60)
    f = FLOOR
    r.fill(0, 0, 2, 35)
    r.fill(57, 12, 59, f - 1)
    r.fill(46, 10, 59, 11)
    r.stand(4, "P")
    r.stand(7, "C")
    r.floating(12, 38, 16, 2)
    r.fill(20, 34, 56, 35)
    r.put(44, 33, "o")
    r.fill(26, 28, 33, 29)
    r.put(30, 27, "b")
    r.fill(51, 20, 52, 31)
    r.put(53, 25, ">")
    r.put(53, 26, ">")
    r.put(56, 29, "<")
    r.put(56, 22, "<")
    r.fill(40, 20, 52, 21)
    r.put(50, 19, "C")
    r.fill(33, 17, 35, 17, "~")
    r.put(28, 13, "*")
    r.fill(14, 12, 24, 13)
    r.put(20, 11, "u")
    r.fill(13, 4, 19, 5)
    r.put(16, 3, "B")
    r.put(9, 8, "*")
    r.put(3, 12, "q")
    r.fill(27, 8, 29, 8, "m")
    r.put(50, 1, "e")
    r.save("g4", "Twilight Grove 4: a subida. Dois Brontes no alto a atirar bombinhas; bolotas nos patamares; chamine de pulo de parede com espinhos; laje, pata e tronco ate a saida la em cima.",
           G4, "twilight_grove", ("b: bronte every=2.2 fuse=0.6 sight=220 dir=1", "B: bronte every=2.4 fuse=0.6 dir=1",
                                  "o: acorn dir=-1 edge=turn " + NUT, "u: acorn dir=1 edge=turn " + NUT,
                                  "m: mover to=12,0 time=2.6", "e: emitter pattern=aimed every=2.4 reach=200 reach_y=160",
                                  "q: feather"),
           header=NIGHT_HEADER)


def grove_5() -> None:
    r = night_grid(120)
    r.hole(3, 107)
    r.fill(0, 10, 2, r.h - 1)
    r.fill(0, 10, 8, 11)
    r.put(1, 9, "P")
    r.put(5, 9, "C")
    r.island(13, 12, 20, {19: "o"})
    r.island(26, 15, 40, {30: "o", 38: "o"})
    r.island(36, 6, 42, {39: "b"})
    r.fill(44, 17, 45, 17, "~")
    r.put(51, 15, "*")
    r.put(50, 11, "q")
    r.island(58, 17, 65, {62: "C"})
    r.island(68, 30, 92, {80: "u", 88: "u"})
    r.fill(70, 23, 90, 24)
    r.put(74, 25, "k")
    r.put(84, 25, "k")
    r.fill(77, 22, 78, 22, "^")
    r.island(78, 14, 84, {81: "B"})
    r.put(94, 20, "f")
    r.fill(94, 29, 95, 29, "~")
    r.put(102, 26, "*")
    r.put(99, 16, "r")
    r.island(110, 30, 116, {114: "C"})
    r.save("g5", "Twilight Grove 5: a travessia. Desfiladeiro sem fundo com tudo junto: bolotas, dois Brontes no alto, morcegos, nuvenzinhas, lajes e patas.",
           G5, "twilight_grove", ("o: acorn dir=-1 edge=turn " + NUT, "u: acorn dir=-1 edge=turn " + NUT,
                                  "b: bronte every=2.2 fuse=0.6 dir=-1", "B: bronte every=2.4 fuse=0.6 sight=200 sight_y=270 dir=-1",
                                  "k: bat reach=40", "f: emitter pattern=aimed every=2.4 reach=160",
                                  "r: emitter pattern=burst every=2.6 reach=120", "q: feather"), header=NIGHT_HEADER)


def water(r: Grid, x0: int, x1: int, y0: int | None = None, y1: int | None = None) -> None:
    r.fill(x0, r.floor if y0 is None else y0, x1, r.h - 1 if y1 is None else y1, "W")


def islet(r: Grid, x0: int, x1: int, rise: int, on_top: dict | None = None, bottom: int | None = None) -> None:
    r.fill(x0, r.floor - rise, x1, r.h - 1 if bottom is None else bottom)
    for x, ch in (on_top or {}).items():
        r.put(x, r.floor - rise - 1, ch)


def pads(r: Grid, *spans: tuple[int, int]) -> None:
    for x0, x1 in spans:
        r.log(x0, r.floor, x1)


def spire(r: Grid, x0: int, x1: int, top: int, bottom: int = 46) -> None:
    r.fill(x0, top, x1, bottom)


def lake_header(pos_y: int, camfloor: int | None = None) -> tuple:
    head = ("bgfloor: %d" % (TALL - pos_y),)
    return head + (("camfloor: -1,0,%d" % camfloor,) if camfloor is not None else ())


def hollow_1() -> None:
    r = night_grid(100)
    f = FLOOR
    r.stand(1, "P")
    r.mound(3, 8, 1)
    r.put(5, f - 2, "C")
    water(r, 10, 91)
    spire(r, 12, 14, 39)
    spire(r, 18, 19, 37)
    spire(r, 23, 37, 39)
    r.put(26, 38, "t")
    r.fill(31, 37, 31, 38)
    r.fill(33, 29, 34, 34)
    spire(r, 38, 40, 26)
    r.put(37, 31, "<")
    r.put(46, 22, "*")
    r.put(46, 18, "q")
    r.fill(41, FLOOR, 51, r.h - 1)
    r.fill(41, FLOOR - 1, 51, FLOOR - 1, "^")
    spire(r, 52, 58, 28)
    r.put(55, 27, "C")
    r.fill(62, 32, 84, 33)
    r.fill(62, 34, 84, 34, "v")
    for x0, x1 in ((61, 63), (67, 68), (72, 74), (78, 79)):
        spire(r, x0, x1, 39)
    spire(r, 83, 90, 39, r.h - 1)
    r.put(76, 37, "q")
    r.put(88, 38, "u")
    r.save("h1", "Glimmer Hollow 1: os rochedos. Pilares a sair do lago, chamine com espinho, dash pela pata, corredor com espinhos no teto; sapos.",
           H1, "glimmer_hollow", ("t: toad hop=1.2 every=1.5", "u: toad hop=1.0 every=1.3 dir=-1", "q: feather"), zone="glow_lake", header=NIGHT_HEADER)


def hollow_2() -> None:
    r = Grid(90, 66, FLOOR, roof=False)
    f = FLOOR
    r.stand(1, "P")
    r.mound(3, 7, 1)
    r.put(5, f - 2, "C")
    r.stand(9, "h")
    water(r, 10, 86, f, 61)
    r.fill(18, 26, 21, 54)
    r.fill(18, 25, 21, 25, "^")
    r.fill(22, 40, 48, 49)
    r.fill(22, 39, 48, 39, "^")
    r.fill(30, 57, 32, 61)
    r.fill(37, 50, 39, 54)
    r.fill(43, 56, 45, 61)
    for x, y in ((26, 56), (34, 58), (41, 53)):
        r.put(x, y, "n")
    islet(r, 55, 62, 2, {58: "C"}, bottom=61)
    islet(r, 66, 71, 1, {69: "k"}, bottom=50)
    pads(r, (74, 75))
    islet(r, 78, 82, 1, {80: "K"}, bottom=50)
    pads(r, (84, 85))
    r.put(74, 56, "n")
    r.fill(77, 62, 80, 63, "W")
    r.put(78, 63, "q")
    r.put(83, 54, "n")
    r.put(76, 30, "y")
    r.fill(87, f, 89, r.h - 1)
    r.save("h2", "Glimmer Hollow 2: o fundo do lago. Muralha que so se passa a mergulhar, tunel submerso com minas, ilhotas com caranguejos debaixo do olho ou rota por baixo delas.",
           H2, "glimmer_hollow", ("h: hint text=HINT_DIVE", "n: mine radius=52 speed=80 chase=2.4 respawn=4",
                                  "k: crab dir=-1 sight=110", "K: crab dir=1 sight=120 speed=65", "y: eye span=80",
                                  "q: feather"),
           zone="glow_lake", header=lake_header(H2[1]))


def hollow_3() -> None:
    r = Grid(44, 86, 82, roof=False)
    f = r.floor
    r.fill(0, 0, 1, f - 6)
    r.fill(42, 8, 43, r.h - 1)
    r.fill(34, 6, 43, 7)
    r.stand(3, "P")
    r.stand(6, "C")
    r.fill(16, f, 22, r.h - 1, "W")
    r.fill(10, f - 3, 12, f - 3, "e")
    r.fill(15, 62, 35, 63)
    r.put(24, 61, "t")
    r.fill(30, 40, 31, 58)
    r.fill(36, 38, 37, 58)
    r.put(32, 50, ">")
    r.put(35, 45, "<")
    r.put(35, 54, "<")
    r.fill(38, 38, 41, 39)
    r.put(39, 37, "C")
    r.fill(22, 35, 24, 35, "~")
    r.put(16, 30, "*")
    r.fill(3, 27, 11, 28)
    r.put(21, 41, "y")
    r.fill(13, 25, 15, 25, "f")
    r.put(5, 10, "q")
    r.put(20, 17, "n")
    r.fill(18, 12, 22, 13)
    r.fill(27, 10, 29, 10, "~")
    r.put(31, 7, "*")
    r.fill(34, 8, 41, 8, "v")
    r.save("h3", "Glimmer Hollow 3: a torre. Sala alta: elevadores, chamine com espinhos, laje e pata com o olho por baixo, mina, laje e pata ate a saida no cimo, com espinhos por baixo do patamar.",
           H3, "glimmer_hollow", ("e: mover to=0,-15 time=3.2", "f: mover to=0,-12 time=2.8", "t: toad hop=1.1 every=1.4",
                                  "y: eye span=64", "n: mine radius=56 speed=100 respawn=3", "q: feather"),
           zone="glow_lake", header=lake_header(H3[1]))


def hollow_4() -> None:
    r = Grid(110, 50, 49, roof=False)
    r.fill(0, 0, r.w - 1, r.h - 1, ".")
    r.fill(0, 26, 8, 28)
    r.put(1, 25, "P")
    r.put(4, 25, "C")
    r.fill(13, 24, 17, 26)
    r.put(22, 18, "*")
    r.put(22, 13, "*")
    r.put(28, 12, "q")
    r.fill(26, 19, 29, 20)
    r.fill(25, 13, 30, 14)
    r.fill(25, 15, 30, 15, "v")
    r.fill(32, 24, 44, 25)
    r.put(41, 23, "k")
    r.fill(48, 22, 50, 22, "~")
    r.put(55, 18, "*")
    r.put(52, 15, "n")
    r.put(57, 23, "n")
    r.fill(61, 22, 70, 25)
    r.put(66, 21, "C")
    r.fill(73, 13, 96, 14)
    r.fill(73, 15, 96, 15, "v")
    r.fill(73, 22, 96, 23)
    r.fill(73, 21, 96, 21, "^")
    for x0, x1 in ((77, 78), (84, 85), (91, 92)):
        r.fill(x0, 21, x1, 21, ".")
    r.put(88, 18, "n")
    r.fill(97, 22, 109, 26)
    r.save("h4", "Glimmer Hollow 4: o penhasco. La no alto, sem chao: patas, rochedo com espinhos por cima, caranguejo, minas e um tubo de espinhos.",
           H4, "glimmer_hollow", ("k: crab dir=-1 sight=120", "n: mine radius=64 speed=110 respawn=3", "q: feather"),
           zone="glow_lake", header=lake_header(H4[1]))


def hollow_5() -> None:
    r = Grid(46, 90, 89, roof=False)
    r.fill(0, 0, r.w - 1, r.h - 1, ".")
    r.fill(0, 7, 9, 9)
    r.put(1, 6, "P")
    r.put(4, 6, "C")
    r.fill(0, 10, 1, r.h - 1)
    r.fill(44, 0, 45, 59)
    r.fill(14, 16, 28, 17)
    r.fill(14, 18, 28, 18, "v")
    r.put(24, 15, "t")
    r.fill(18, 26, 43, 27)
    r.put(40, 25, "k")
    r.fill(2, 36, 24, 37)
    r.put(4, 35, "C")
    r.put(32, 41, "y")
    r.fill(20, 48, 43, 49)
    r.fill(25, 47, 29, 47, "^")
    r.put(12, 54, "n")
    r.fill(2, 60, 30, 61)
    r.fill(12, 59, 14, 59, "^")
    r.put(8, 59, "u")
    water(r, 2, 33, 72)
    r.fill(9, 62, 16, 62, "v")
    r.put(5, 65, "q")
    r.put(20, 80, "n")
    r.fill(34, 72, 43, r.h - 1)
    r.fill(44, 72, 45, r.h - 1)
    r.save("h5", "Glimmer Hollow 5: a descida. Zigue-zague para baixo entre espinhos, com sapos, caranguejo, o olho e minas, ate uma piscina.",
           H5, "glimmer_hollow", ("t: toad hop=1.0 every=1.3", "u: toad hop=1.0 every=1.2", "k: crab dir=-1 sight=120 speed=65",
                                  "y: eye span=128 spin=1.3", "n: mine radius=56 speed=90 respawn=3.5", "q: feather"),
           zone="glow_lake", header=lake_header(H5[1]))


def hollow_6() -> None:
    r = Grid(110, 60, 52, roof=False)
    f = r.floor
    r.fill(0, 37, 9, r.h - 1)
    r.put(1, 36, "P")
    r.put(5, 36, "C")
    r.fill(10, 42, 14, r.h - 1)
    r.fill(15, 47, 18, r.h - 1)
    water(r, 19, 86)
    pads(r, (21, 22))
    r.fill(25, f - 1, 27, f - 1, "a")
    islet(r, 40, 45, 3, {43: "t"})
    r.fill(48, f - 1, 50, f - 1, "b")
    islet(r, 53, 62, 11, {58: "C"})
    islet(r, 66, 72, 2, {70: "k"})
    pads(r, (75, 76))
    r.fill(78, f - 1, 80, f - 1, "d")
    r.put(80, 38, "y")
    r.put(88, 40, "n")
    r.fill(87, f - 2, 96, r.h - 1)
    r.put(93, f - 3, "u")
    r.put(90, f - 3, "h")
    r.fill(97, f - 4, 103, r.h - 1)
    r.put(98, f - 5, "e")
    r.put(102, f - 7, "g")
    r.fill(104, f - 8, 109, r.h - 1)
    r.put(105, f - 9, "C")
    r.put(108, f - 9, "j")
    r.save("h6", "Glimmer Hollow 6: antes do amanhecer. Do morro para o lago em troncos que andam na agua, sapos, caranguejo, olho e nuvenzinha, ate ao morrinho.",
           H6, "glimmer_hollow", ("a: mover to=10,0 time=2.4", "b: mover to=0,-9 time=2.2", "d: mover to=7,0 time=2",
                                  "t: toad hop=1.0 every=1.2", "u: toad hop=1.0 every=1.2 dir=-1", "k: crab dir=-1 sight=120 speed=65",
                                  "y: eye span=96 spin=1.3", "n: emitter pattern=aimed every=2.4 reach=144",
                                  "e: ruin file=ruin_drum_b.png", "g: ruin file=ruin_col_g.png",
                                  "h: sprite file=deco_capital.png sink=5", "j: sprite file=deco_column_far.png z=-2 sink=2"),
           zone="glow_lake", header=lake_header(H6[1], 55))


OLY_DEFS = ("f: fall", "F: fall", "A: beat group=a", "B: beat group=b", "q: feather")


def oly_grid(w: int, h: int) -> Grid:
    r = Grid(w, h, h - 1, roof=False)
    r.fill(0, 0, w - 1, h - 1, ".")
    return r


def oly_header(pos_y: int) -> tuple:
    return ("bgfloor: %d" % (TALL - pos_y),)


def blocks(r: Grid, y: int, *xs: int, w: int = 2) -> None:
    for k, x in enumerate(xs):
        r.fill(x, y, x + w - 1, y, "fF"[k % 2])


def beats(r: Grid, *clouds: tuple) -> None:
    for x, y, group in clouds:
        r.fill(x, y, x + 2, y, group)


def ascent() -> None:
    r = oly_grid(100, 100)
    for x0, x1, top in ((0, 8, 94), (9, 21, 93), (22, 31, 91), (32, 36, 88), (37, 38, 84),
                        (39, 42, 77), (43, 46, 75), (47, 52, 79), (53, 61, 72)):
        r.fill(x0, top, x1, r.h - 1)
    r.fill(60, 81, 61, r.h - 1, ".")
    r.fill(58, 89, 59, r.h - 1, ".")
    r.put(2, 93, "P")
    ruins = ((11, 92, "ruin_step_a"), (14, 90, "ruin_step_b"), (17, 88, "ruin_step_c"),
             (23, 85, "ruin_col_a"), (27, 82, "ruin_col_b"),
             (35, 80, "ruin_col_c"),
             (43, 74, "ruin_drum_a"), (48, 71, "ruin_col_d"), (51, 68, "ruin_wall_a"),
             (55, 66, "ruin_col_e"), (60, 66, "ruin_col_f"), (54, 65, "ruin_beam_a"))
    letters = "abcdefghijkmnoqrstuwxyz"
    defs = []
    for k, (x, y, name) in enumerate(ruins):
        r.put(x, y, letters[k])
        defs.append("%s: ruin file=%s.png" % (letters[k], name))
    for k, (x, y, name, extra) in enumerate(((30, 90, "deco_column_far", "z=-2 sink=2"),
                                            (41, 76, "deco_column_far_b", "z=-2 sink=2"),
                                            (33, 87, "deco_capital", "sink=5")), len(ruins)):
        r.put(x, y, letters[k])
        defs.append("%s: sprite file=%s.png %s" % (letters[k], name, extra))
    r.put(58, 64, "C")
    clouds = ((65, 62), (70, 59), (75, 56), (80, 53), (85, 50), (90, 47), (85, 44), (80, 41), (75, 38), (70, 35))
    for k, (x, y) in enumerate(clouds):
        r.fill(x, y, x + 2, y, str(k))
    for y in (31, 27, 23, 19, 15):
        r.put(67, y, "*")
    r.put(67, 10, "L")
    r.put(1, 1, "V")
    r.save("o0", "Subida ao ceu: encosta de ruinas de marmore ate ao portico da ponta, zoom out sobre o abismo, nuvens rosa que aparecem a cada pulo, fila de patas e o brilho que leva ao Olimpo.",
           O0, "glimmer_hollow",
           tuple(defs) + ("0: step order=0 near=56",) + tuple("%d: step order=%d" % (k, k) for k in range(1, len(clouds)))
           + ("L: glow to=o1", "V: vista from=50 to=70 zoom=0.75"),
           zone="glow_lake", header=lake_header(O0[1]))


def olympus_1() -> None:
    r = oly_grid(120, TALL + 9)
    y = 34
    r.floating(0, y, 13, 6, {2: "P", 7: "C"})
    blocks(r, y, 17, w=3)
    r.floating(14, y + 7, 31, 4)
    r.floating(23, y, 33, 5)
    blocks(r, y + 2, 37, 43, 49)
    r.floating(53, y + 7, 64, 5, {58: "C"})
    blocks(r, y + 7, *range(66, 86, 2))
    r.floating(88, y + 7, 96, 4)
    r.put(71, y + 1, "*")
    r.put(76, y - 3, "*")
    r.put(81, y - 6, "q")
    blocks(r, y + 4, 99)
    r.log(103, y + 1, 105)
    blocks(r, y - 1, 108)
    r.floating(111, y, 119, 4)
    r.put(104, y - 9, "r")
    r.save("o1", "Little Olympus 1: terracos do amanhecer. Lajes de marmore que caem: sozinha, em escada, em ponte e debaixo das flechas do cupido.",
           O1, "little_olympus", OLY_DEFS + ("r: archer every=2.6 leash=96",), zone="olympus_dawn", header=oly_header(O1[1]))


def olympus_2() -> None:
    r = oly_grid(110, TALL + 9)
    y = 34
    r.floating(0, y, 11, 6, {2: "P", 6: "C"})
    beats(r, (14, y, "A"), (19, y, "B"), (24, y, "A"), (29, y, "B"), (34, y, "A"))
    r.floating(13, y + 6, 51, 5)
    r.floating(47, y + 3, 51, 2)
    r.floating(39, y, 46, 4)
    beats(r, (50, y - 2, "B"), (55, y - 4, "A"), (60, y - 6, "B"), (65, y - 8, "A"))
    r.floating(70, y - 8, 80, 5, {75: "C"})
    r.fill(53, y - 1, 73, y - 1, "^")
    r.fill(53, y, 73, y)
    r.fill(53, y + 1, 71, y + 1, "v")
    r.fill(72, y + 1, 73, y + 7)
    beats(r, (53, y + 6, "A"), (57, y + 6, "B"), (61, y + 6, "A"), (65, y + 6, "B"))
    r.fill(68, y + 6, 71, y + 7)
    r.put(70, y + 5, "q")
    beats(r, (88, y - 7, "B"), (95, y - 10, "A"))
    r.floating(100, y - 10, 109, 5)
    r.put(106, y - 11, "k")
    r.put(98, y - 22, "w")
    r.save("o2", "Little Olympus 2: compasso. Nuvens ao ritmo (A e B trocam a cada 1,6 s): sobre uma ilha, em escada, no contratempo e debaixo da Nephele.",
           O2, "little_olympus", OLY_DEFS + ("w: nimbus span=120 speed=55", "k: skeleton wake=90"),
           zone="olympus_dawn", header=oly_header(O2[1]))


def olympus_3() -> None:
    r = oly_grid(110, TALL + 9)
    y = 24
    r.floating(0, y, 11, 6, {2: "P", 6: "C"})
    r.floating(14, y + 2, 40, 4)
    r.put(41, y - 1, "h")
    r.floating(44, y + 2, 60, 4)
    r.fill(49, y + 1, 52, y + 1, "^")
    r.put(61, y - 2, "j")
    r.floating(63, y + 2, 70, 4, {65: "C"})
    r.put(68, y - 3, "g")
    r.put(78, y - 1, "*")
    r.floating(85, y, 97, 4)
    r.put(98, y - 6, "e")
    r.put(108, y - 3, "u")
    r.put(92, y - 13, "r")
    r.floating(102, y, 109, 5)
    r.put(74, y - 6, "*")
    r.put(78, y - 6, "*")
    r.fill(80, y - 8, 84, y - 7)
    r.put(82, y - 9, "q")
    r.save("o3", "Little Olympus 3: vento norte. O Boreas Gust empurra para tras e para cima de espinhos, e tambem leva o George por cima de um vao largo.",
           O3, "little_olympus", OLY_DEFS + ("h: gust dir=-1 push=100", "j: gust dir=-1 push=120", "g: gust dir=1 push=150 drift=8 reach=260",
                                             "e: gust dir=1 push=110", "u: gust dir=-1 push=110", "r: archer every=2.8 leash=80"),
           zone="olympus_dawn", header=oly_header(O3[1]))


def olympus_4() -> None:
    r = oly_grid(130, TALL + 9)
    b = 28
    r.floating(0, 24, 11, 6, {2: "P", 6: "C"})
    r.fill(14, b, 44, b + 1)
    r.fill(22, b - 3, 23, b - 1)
    r.put(40, b - 1, "n")
    r.fill(48, b, 70, b + 1)
    r.put(66, b - 1, "o")
    r.log(52, b - 5, 56)
    r.floating(74, 24, 82, 5, {78: "C"})
    r.fill(86, b, 118, b + 1)
    r.fill(90, b + 2, 112, b + 2, "v")
    r.put(87, b - 1, "m")
    r.put(100, b - 1, "k")
    r.put(110, b - 1, "s")
    r.fill(114, b - 3, 115, b - 1)
    r.floating(118, 34, 129, 5)
    for x0 in range(83, 116, 4):
        r.fill(x0, 34, x0 + 1, 34)
    r.put(109, 32, "q")
    r.save("o4", "Little Olympus 4: ponte do minotauro. Minotauros tontos nos pilares e a travar nas beiras, Spartoi a nascer da ponte; por baixo, a rota da pena.",
           O4, "little_olympus", OLY_DEFS + ("n: minotaur dir=-1", "o: minotaur dir=-1", "m: minotaur dir=1 charge=150",
                                             "k: skeleton wake=100", "s: skeleton wake=90"),
           zone="olympus_dawn", header=oly_header(O4[1]))


def olympus_5() -> None:
    r = oly_grid(48, 100)
    g = 80
    r.fill(0, 0, 3, g - 6)
    r.fill(0, g, 16, g + 2)
    r.put(1, g - 1, "P")
    r.put(6, g - 1, "C")
    r.fill(44, 14, 47, r.h - 1)
    for k, x in enumerate((19, 24, 29, 34)):
        r.fill(x, g - 3 - 3 * k, x + 1, g - 3 - 3 * k, "fF"[k % 2])
    r.fill(38, g - 15, 43, g - 14)
    r.fill(37, 45, 38, g - 18)
    r.fill(39, 54, 39, 56, ">")
    r.fill(43, 50, 43, 51, "<")
    r.put(41, 58, "r")
    r.put(10, 56, "t")
    r.fill(28, 44, 38, 45)
    r.put(31, 43, "C")
    r.fill(44, 41, 45, 43, ".")
    r.fill(44, 40, 45, 40, "v")
    r.put(45, 43, "q")
    blocks(r, 41, 22)
    blocks(r, 38, 17)
    blocks(r, 35, 12)
    r.put(14, 31, "*")
    r.fill(4, 28, 12, 29)
    r.put(6, 27, "k")
    for k, x in enumerate((15, 20, 25, 30)):
        r.fill(x, 25 - 3 * k, x + 1, 25 - 3 * k, "fF"[k % 2])
    r.fill(32, 14, 47, 15)
    r.put(24, 4, "w")
    r.save("o5", "Little Olympus 5: escadaria que desaba. Subida vertical em lajes que caem, chamine com espinhos, cupidos, Spartoi e a Nephele la em cima.",
           O5, "little_olympus", OLY_DEFS + ("r: archer every=2.8 leash=64", "t: archer every=3.0 leash=64",
                                             "k: skeleton wake=90", "w: nimbus span=150 speed=55"),
           zone="olympus_dawn", header=oly_header(O5[1]))


def olympus_6() -> None:
    r = oly_grid(170, 86)
    r.fill(0, 14, 10, 15)
    r.put(1, 13, "P")
    r.put(5, 13, "C")
    r.floating(14, 18, 24, 4)
    blocks(r, 21, 28)
    r.floating(33, 24, 42, 4)
    beats(r, (46, 27, "A"), (51, 29, "B"), (56, 31, "A"))
    r.floating(61, 34, 72, 5)
    r.put(69, 31, "g")
    r.put(80, 34, "*")
    r.floating(86, 40, 95, 4)
    blocks(r, 44, *range(99, 113, 2))
    r.put(110, 37, "r")
    beats(r, (116, 48, "B"), (121, 51, "A"), (126, 54, "B"))
    r.floating(131, 58, 142, 4, {137: "C"})
    r.fill(145, 62, 146, 76)
    r.fill(147, 70, 147, 72, ">")
    r.fill(155, 50, 156, 74)
    r.fill(154, 63, 154, 66, "<")
    r.fill(148, 80, 169, 82)
    r.fill(148, 79, 156, 79, "^")
    r.put(80, 28, "q")
    r.put(1, 1, "X")
    r.save("o6", "Little Olympus 6: fuga da tempestade. A frente da trovoada persegue o George a descer ate ao palacio, sem fogueira a meio: ilhas, lajes, nuvens ao ritmo, patas, rajada e cupido; descida com espinhos no chao.",
           O6, "little_olympus", OLY_DEFS + ("g: gust dir=1 push=150 drift=8 reach=260", "r: archer every=3.0 leash=64",
                                             "X: chase speed=100 starts=1 to=128"),
           zone="olympus_dawn", header=oly_header(O6[1]))


def palace_isle() -> None:
    deep = 9
    w = 118
    r = Grid(w, TALL + deep, FLOOR, roof=False)
    r.fill(0, 0, r.w - 1, r.h - 1, ".")
    y = 34
    r.floating(0, y, 4, 4, {1: "P", 3: "d"})
    r.floating(6, y + 3, 9, 2, {7: "C"})
    r.floating(11, y + 6, 13, 2)
    terrace = y + 9
    for k, x0 in enumerate((15, 15, 15, 16, 18, 21, 26, 33, 43, 56)):
        r.fill(x0, terrace + k, r.w - 1, terrace + k)
    for x0, x1, down in ((23, 24, 6), (31, 33, 8), (40, 41, 9), (50, 53, 10), (65, 68, 10), (81, 83, 10), (95, 97, 10), (108, 110, 10)):
        r.fill(x0, terrace + 3, x1, min(r.h - 1, terrace + down))
    r.put(16, terrace - 1, "P")
    r.fill(29, terrace - 1, r.w - 1, terrace - 1, "m")
    r.put(29, terrace - 1, "n")
    r.put(106, terrace - 1, "g")
    r.save("o7", "Little Olympus 7: a ilha do palacio. Corredor de pilares (a arena do guardiao, por fazer) e a porta do palacio, que leva ao salao do trono.",
           O7, "little_olympus", ("m: paved", "g: gate to=z1", "n: sprite file=gate_floor.png left=1 z=0 sink=68", "d: sprite file=gate_pillar_b.png"),
           zone="olympus_dawn", header=("camfloor: 4,15,%d" % (TALL + 1), "bgfloor: %d" % TALL))


def throne_room() -> None:
    r = Grid(Z1_W, TALL, FLOOR, roof=False)
    f = FLOOR - 1
    r.put(0, f, "d")
    r.put(1, f, "n")
    r.put(10, f, "P")
    r.put(15, f, "C")
    r.put(106, f, "C")
    for x in (34, 56, 78, 100):
        r.put(x, f, "K" if x in (56, 100) else "k")
    r.fill(61, f - 1, 62, f)
    r.put(61, f - 8, "q")
    r.fill(91, f, 93, f)
    r.put(45, f, "x")
    r.put(69, f, "z")
    r.put(87, f, "y")
    r.put(2, 1, "s")
    r.put(4, 1, "h")
    r.save("z1", "Thunder Court 1: o salao de entrada do palacio de Zeus. Colunas gigantes, tempestade, tres raios e dois blocos; a direita, a arena do trono (z2).",
           Z1, "thunder_court", ("n: sprite file=palace_floor.png left=1 dx=-16 z=0 sink=68", "d: inner_door",
                                 "k: sprite file=palace_column.png z=0", "K: sprite file=palace_column_clawed.png z=0",
                                 "s: storm every=4-11", "x: strike every=3.4 first=2", "z: strike every=3.4 first=3.7",
                                 "y: strike every=2.6 first=1.2", "h: hunt every=1.5 from=22 to=98", "q: feather"), zone="zeus_palace")


def throne_arena() -> None:
    w, f = Z2_W, FLOOR - Z2[1]
    r = Grid(w, f + DEEP, f, roof=False)
    s = f - 1
    r.put(0, s, "n")
    r.put(1, s, "P")
    r.fill(8, s - 3, 10, s - 3)
    r.fill(13, s - 5, 16, s - 5)
    r.fill(3, s - 8, 5, s - 8)
    r.fill(22, s, w - 1, s)
    r.fill(24, s - 1, w - 1, s - 1)
    r.fill(26, s - 2, w - 1, s - 2)
    r.put(32, s - 3, "t")
    r.fill(28, s - 8, 36, s - 8, "l")
    r.put(32, s - 9, "D")
    r.put(20, s, "b")
    r.put(27, s - 3, "F")
    r.put(14, s - 6, "o")
    r.put(2, 1, "s")
    spots = ("6,%d;18,%d" % (s, s), "9,%d;15,%d;29,%d" % (s - 4, s - 6, s - 3), "4,%d;14,%d;29,%d" % (s - 9, s - 6, s - 3))
    r.save("z2", "Thunder Court 2: a arena do trono. O jogo de bolinha com o cao de Zeus (chefe final); o cachorro do George na almofada do trono.",
           Z2, "thunder_court", ("n: sprite file=palace_floor.png left=1 dx=-16 z=0 sink=68",
                                 "t: sprite file=palace_throne.png z=0 sink=48", "l: ledge",
                                 "b: sprite file=palace_bowl.png z=0", "D: dog anim=lie left=1",
                                 "F: fight spots1=%s spots2=%s spots3=%s" % spots,
                                 "o: ball", "s: storm every=5-12 entry=0"), zone="zeus_palace")


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    for gone in ("w1.room", "c1.room"):
        old = os.path.join(OUT, gone)
        if os.path.exists(old):
            os.remove(old)
    camp_site()
    camp()
    meadow()
    for room in (grove_1, grove_2, grove_3, grove_4, grove_5):
        room()
    for room in (hollow_1, hollow_2, hollow_3, hollow_4, hollow_5, hollow_6):
        room()
    for room in (ascent, olympus_1, olympus_2, olympus_3, olympus_4, olympus_5, olympus_6, palace_isle):
        room()
    throne_room()
    throne_arena()
    print("salas ember: ok")


if __name__ == "__main__":
    main()
