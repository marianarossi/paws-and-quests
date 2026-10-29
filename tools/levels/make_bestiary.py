from __future__ import annotations

import os

W, H = 80, 23
FLOOR = 20
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "levels", "dev", "bestiary")


def grid() -> list[list[str]]:
    g = [["." for _ in range(W)] for _ in range(H)]
    for y in range(FLOOR, H):
        for x in range(W):
            g[y][x] = "#"
    for y in range(H):
        g[y][0] = g[y][1] = "#"
        g[y][W - 1] = g[y][W - 2] = "#"
    for x in range(W):
        g[0][x] = "#"
    return g


def opening(g, side: str) -> None:
    xs = (0, 1) if side == "left" else (W - 2, W - 1)
    for y in range(FLOOR - 6, FLOOR):
        for x in xs:
            g[y][x] = "."


def box(g, x0: int, y0: int, x1: int, y1: int, ch: str = "#") -> None:
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            g[y][x] = ch


def put(g, x: int, y: int, ch: str) -> None:
    g[y][x] = ch


def write(name: str, header: list[str], g, defs: list[str]) -> None:
    os.makedirs(ROOT, exist_ok=True)
    lines = header + ["---"] + ["".join(row) for row in g] + ["---"] + defs
    with open(os.path.join(ROOT, name + ".room"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def grove() -> None:
    g = grid()
    opening(g, "right")
    put(g, 3, FLOOR - 1, "P")
    put(g, 6, FLOOR - 1, "C")
    box(g, 12, 1, 30, 9)
    put(g, 17, 10, "b")
    put(g, 26, 10, "b")
    put(g, 36, FLOOR - 1, "o")
    box(g, 40, 15, 47, 15)
    put(g, 44, 14, "O")
    box(g, 52, FLOOR - 1, 52, FLOOR - 1)
    box(g, 66, FLOOR - 1, 66, FLOOR - 1)
    put(g, 72, FLOOR - 1, "c")
    put(g, 46, 6, "e")
    write("i1", ["; Teste do bestiário: Twilight Grove. Gerado por tools/levels/make_bestiary.py",
                 "id: i1", "zone: twilight_grove", "area: twilight_grove", "pos: 0,0"], g,
          ["b: bat reach=40", "o: acorn dir=1", "O: acorn dir=-1", "c: bronte dir=-1",
           "e: emitter pattern=aimed every=2.4"])


def hollow() -> None:
    g = grid()
    opening(g, "left")
    opening(g, "right")
    put(g, 4, FLOOR - 1, "P")
    put(g, 6, FLOOR - 1, "C")
    put(g, 16, FLOOR - 1, "t")
    box(g, 30, 14, 38, 14, "=")
    put(g, 34, FLOOR - 1, "k")
    box(g, 26, FLOOR - 1, 26, FLOOR - 1)
    box(g, 42, FLOOR - 1, 42, FLOOR - 1)
    put(g, 54, 11, "y")
    box(g, 46, 8, 50, 8, "=")
    box(g, 57, 8, 61, 8, "=")
    box(g, 51, 15, 56, 15, "=")
    box(g, 62, FLOOR - 3, 63, FLOOR - 1)
    write("i2", ["; Teste do bestiário: Glimmer Hollow. Gerado por tools/levels/make_bestiary.py",
                 "id: i2", "zone: glow_lake", "area: glimmer_hollow", "pos: 80,0"], g,
          ["t: toad hop=1.1 every=1.4", "k: crab dir=-1", "y: eye span=64 sweep=64"])


def olympus() -> None:
    g = grid()
    opening(g, "left")
    opening(g, "right")
    put(g, 4, FLOOR - 1, "P")
    put(g, 6, FLOOR - 1, "C")
    put(g, 20, 15, "a")
    box(g, 13, 16, 17, 16, "=")
    box(g, 24, 13, 28, 13, "=")
    box(g, 33, FLOOR - 4, 34, FLOOR - 1)
    box(g, 52, FLOOR - 4, 53, FLOOR - 1)
    put(g, 46, FLOOR - 1, "n")
    box(g, 40, 13, 46, 13, "=")
    put(g, 60, FLOOR - 1, "s")
    write("i3", ["; Teste do bestiário: Amanhecer no Olimpo. Gerado por tools/levels/make_bestiary.py",
                 "id: i3", "zone: olympus_dawn", "area: little_olympus", "pos: 160,0"], g,
          ["a: archer every=2.6 leash=96", "n: minotaur dir=-1", "s: skeleton wake=110"])


def tartarus() -> None:
    g = grid()
    opening(g, "left")
    opening(g, "right")
    put(g, 4, FLOOR - 1, "P")
    put(g, 6, FLOOR - 1, "C")
    put(g, 24, 6, "j")
    put(g, 40, 7, "w")
    box(g, 64, 14, 70, 14, "=")
    write("i4", ["; Teste do bestiário: os do Tártaro (sem fase ainda). Gerado por tools/levels/make_bestiary.py",
                 "id: i4", "zone: tartarus", "pos: 240,0"], g,
          ["j: harpy span=130 feathers=3", "w: nimbus span=220 sparks=3"])


def peak() -> None:
    g = grid()
    opening(g, "left")
    put(g, 4, FLOOR - 1, "P")
    put(g, 6, FLOOR - 1, "C")
    box(g, 26, 8, 28, FLOOR - 1)
    put(g, 20, 10, "u")
    box(g, 58, 13, 62, 13, "=")
    put(g, 75, 15, "v")
    write("i5", ["; Teste do bestiário: céu e cume (sem fase ainda). Gerado por tools/levels/make_bestiary.py",
                 "id: i5", "zone: snow_peak", "pos: 320,0"], g,
          ["u: shade speed=20", "v: gust dir=-1 push=110"])


if __name__ == "__main__":
    grove()
    hollow()
    olympus()
    tartarus()
    peak()
    print("bestiario: salas i1 a i5 em levels/dev/bestiary")
