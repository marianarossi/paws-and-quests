from __future__ import annotations

import glob
import io
import os

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(ROOT, "levels", "dev", "zones")
W, H = 40, 23


def showcase() -> list[str]:
    g = [["."] * W for _ in range(H)]

    def fill(x0: int, y0: int, x1: int, y1: int, ch: str = "#") -> None:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                g[y][x] = ch

    fill(0, 0, W - 1, 1)
    fill(0, 20, W - 1, 22)
    fill(0, 0, 1, 19)
    fill(W - 2, 0, W - 1, 19)
    fill(9, 2, 15, 4)
    fill(12, 17, 15, 19)
    fill(18, 11, 24, 12)
    fill(21, 20, 29, 21, "W")
    fill(26, 15, 29, 15, "=")
    fill(32, 13, 37, 19)
    fill(34, 7, 37, 12)
    g[19][4] = "P"
    g[19][7] = "C"
    g[19][17] = "M"
    g[19][30] = "^"
    g[19][31] = "^"
    g[8][21] = "*"
    return ["".join(r) for r in g]


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    for old in glob.glob(os.path.join(OUT, "*.room")):
        os.remove(old)
    rows = showcase()
    zones = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(ROOT, "assets", "themes", "*.json")))
    for i, zone in enumerate(["forest", "ember"] + zones):
        text = "; Sala de mostra do cenario '%s'.\nid: %s\nzone: %s\npos: 0,%d\n---\n%s\n" % (zone, zone, zone, i * 40, "\n".join(rows))
        io.open(os.path.join(OUT, zone + ".room"), "w", encoding="utf-8", newline="\n").write(text)
    print("salas de mostra: %d" % (len(zones) + 2))


if __name__ == "__main__":
    main()
