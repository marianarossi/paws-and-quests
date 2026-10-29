from __future__ import annotations

import io
import os

OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "levels", "dev", "design"))


class Grid:
    def __init__(self, w: int, h: int) -> None:
        self.w, self.h = w, h
        self.g = [["."] * w for _ in range(h)]

    def fill(self, x0: int, y0: int, x1: int, y1: int, ch: str = "#") -> None:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if 0 <= x < self.w and 0 <= y < self.h:
                    self.g[y][x] = ch

    def put(self, x: int, y: int, ch: str) -> None:
        self.g[y][x] = ch

    def save(self, name: str, comment: str, pos: tuple, defs: tuple = ()) -> None:
        text = "; %s\nid: %s\nzone: forest\npos: %d,%d\n---\n" % (comment, name, pos[0], pos[1])
        text += "\n".join("".join(r) for r in self.g) + "\n"
        if defs:
            text += "---\n" + "\n".join(defs) + "\n"
        io.open(os.path.join(OUT, name + ".room"), "w", encoding="utf-8", newline="\n").write(text)


def celeste() -> None:
    r = Grid(40, 23)
    r.fill(0, 0, 39, 1)
    r.fill(0, 0, 1, 22)
    r.fill(38, 0, 39, 22)
    r.fill(2, 20, 9, 22)
    r.put(3, 19, "P")
    r.fill(10, 20, 15, 22)
    r.put(12, 14, "*")
    r.fill(13, 12, 15, 12, "=")
    r.fill(16, 21, 23, 22)
    r.fill(16, 20, 23, 20, "^")
    r.put(19, 14, "*")
    r.fill(24, 17, 26, 22)
    r.fill(27, 21, 33, 22)
    r.fill(27, 20, 33, 20, "^")
    r.put(29, 13, "*")
    r.put(32, 9, "*")
    r.fill(34, 8, 37, 22)
    r.put(36, 7, "C")
    r.save("d1", "Estudo Celeste: uma tela, uma mecanica (pata de dash) ensinada em tres passos.", (0, 0))


def ori() -> None:
    r = Grid(40, 46)
    r.fill(0, 0, 1, 45)
    r.fill(38, 0, 39, 45)
    r.fill(0, 43, 39, 45)
    r.fill(0, 0, 39, 1)
    r.put(5, 42, "P")
    r.put(8, 42, "C")
    r.put(20, 42, "M")
    r.fill(17, 34, 23, 35)
    r.fill(27, 30, 30, 30, "=")
    r.fill(32, 26, 37, 27)
    r.put(34, 25, "h")
    r.fill(24, 22, 27, 22, "=")
    r.fill(14, 18, 21, 19)
    r.fill(22, 10, 23, 19)
    r.fill(28, 8, 37, 9)
    r.put(35, 7, "C")
    r.put(27, 14, "*")
    r.fill(2, 26, 9, 27)
    r.fill(10, 20, 11, 27)
    r.put(5, 25, "C")
    r.put(12, 30, "g")
    r.fill(6, 33, 9, 33, "~")
    r.save("d2", "Estudo Ori: sala vertical com caminho principal e um recanto opcional escondido.", (100, 0),
           ("h: acorn edge=turn", "g: emitter pattern=aimed every=2.6"))


def shovel() -> None:
    r = Grid(80, 23)
    r.fill(0, 0, 79, 1)
    r.fill(0, 20, 79, 22)
    r.fill(0, 0, 1, 19)
    r.fill(78, 0, 79, 19)
    r.put(3, 19, "P")
    r.put(6, 19, "C")
    r.fill(9, 19, 10, 19)
    r.put(15, 19, "h")
    r.fill(22, 17, 24, 19)
    r.fill(27, 16, 33, 17)
    r.put(30, 15, "h")
    r.fill(36, 20, 42, 20, "^")
    r.put(46, 19, "C")
    r.fill(52, 20, 66, 20, "^")
    r.fill(55, 17, 57, 17, "=")
    r.fill(60, 15, 63, 16)
    r.put(61, 14, "h")
    r.put(66, 12, "g")
    r.fill(69, 17, 71, 19)
    r.put(75, 19, "C")
    r.save("d3", "Estudo Shovel Knight: cada obstaculo primeiro sozinho, depois combinado; fogueira a meio.", (200, 0),
           ("h: acorn edge=turn", "g: emitter pattern=aimed every=2.6"))


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    celeste()
    ori()
    shovel()
    print("salas de estudo: ok")


if __name__ == "__main__":
    main()
