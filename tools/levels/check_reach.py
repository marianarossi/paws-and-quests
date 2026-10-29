from __future__ import annotations

import glob
import os
import sys
from collections import deque

SOLID = "#"
SUPPORT = "#=~"
DEADLY = "^v<>"
JUMP_UP, JUMP_RUN = 3, 7
DASH_RUN, DASH_UP = 4, 3
SPRING_UP = 5


def load(path: str) -> tuple[str, list[str], bool]:
    text = open(path, encoding="utf-8").read().replace("\r", "")
    parts = text.split("---")
    rows = [r for r in parts[1].strip("\n").split("\n")]
    width = max(len(r) for r in rows)
    name = os.path.basename(path)
    defs = parts[2] if len(parts) > 2 else ""
    rows = [r.ljust(width, ".") for r in rows]
    return name, with_ruins(with_pieces(with_movers(rows, defs), defs), defs), " gift" not in defs


PIECES = {"fall": "#", "beat": "=", "step": "="}


def with_pieces(rows: list[str], defs: str) -> list[str]:
    swap = {}
    for line in defs.split(chr(10)):
        if ":" in line and not line.startswith(";"):
            letter, rest = line.split(":", 1)
            kind = rest.split()[0] if rest.split() else ""
            if kind in PIECES and len(letter.strip()) == 1:
                swap[letter.strip()] = PIECES[kind]
    return ["".join(swap.get(c, c) for c in r) for r in rows]


PROPS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "sprites", "props")


def with_ruins(rows: list[str], defs: str) -> list[str]:
    from PIL import Image
    grid = [list(r) for r in rows]
    for line in defs.split(chr(10)):
        if ": ruin" not in line or "file=" not in line:
            continue
        letter = line.split(":")[0].strip()
        w, h = Image.open(os.path.join(PROPS, line.split("file=")[1].split()[0])).size
        for y, r in enumerate(rows):
            for x, c in enumerate(r):
                if c != letter or (x > 0 and r[x - 1] == letter):
                    continue
                for cy in range(y, min(len(grid), y + h // 16)):
                    for cx in range(x, min(len(grid[0]), x + w // 16)):
                        if grid[cy][cx] in "." + letter:
                            grid[cy][cx] = SOLID
    return ["".join(r) for r in grid]


def with_movers(rows: list[str], defs: str) -> list[str]:
    grid = [list(r) for r in rows]
    for line in defs.split(chr(10)):
        if ": mover" not in line or "to=" not in line:
            continue
        letter = line.split(":")[0].strip()
        dx, dy = (int(v) for v in line.split("to=")[1].split()[0].split(","))
        steps = max(abs(dx), abs(dy), 1)
        cells = [(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if c == letter]
        for x, y in cells:
            for k in range(steps + 1):
                cx, cy = x + round(dx * k / steps), y + round(dy * k / steps)
                if 0 <= cy < len(grid) and 0 <= cx < len(grid[0]) and grid[cy][cx] in "." + letter:
                    grid[cy][cx] = "="
    return ["".join(r) for r in grid]


class Room:
    def __init__(self, rows: list[str]) -> None:
        self.rows = rows
        self.h, self.w = len(rows), len(rows[0])

    def at(self, x: int, y: int) -> str:
        if x < 0 or x >= self.w or y < 0:
            return SOLID
        if y >= self.h:
            return "."
        return self.rows[y][x]

    def free(self, x: int, y: int) -> bool:
        return self.at(x, y) != SOLID

    def standable(self, x: int, y: int) -> bool:
        c = self.at(x, y)
        return c != SOLID and c not in DEADLY and c != "W" and 0 <= y < self.h and self.at(x, y + 1) in SUPPORT

    def clear(self, ax: int, ay: int, bx: int, by: int) -> bool:
        top = max(0, min(ay, by) - 1)
        step = 1 if bx >= ax else -1
        up = all(self.free(ax, y) for y in range(top, ay + 1))
        across = all(self.free(x, top) for x in range(ax, bx + step, step))
        down = all(self.free(bx, y) for y in range(top, by + 1))
        if up and across and down:
            return True
        n = max(abs(bx - ax), abs(by - ay), 1)
        return all(self.free(round(ax + (bx - ax) * k / n), round(ay + (by - ay) * k / n)) for k in range(n + 1))


def chimney_top(room: Room, ax: int, ay: int) -> tuple[int, int] | None:
    best = None
    for left in range(ax - 5, ax):
        for right in range(ax + 1, ax + 6):
            if not 2 <= right - left - 1 <= 5:
                continue
            y, skipped = ay - 1, 0
            while y >= 0 and not (room.at(left, y) == SOLID and room.at(right, y) == SOLID) and skipped < 4:
                y, skipped = y - 1, skipped + 1
            rows = 0
            while y >= 0 and room.at(left, y) == SOLID and room.at(right, y) == SOLID \
                    and all(room.free(x, y) for x in range(left + 1, right)):
                y, rows = y - 1, rows + 1
            if rows >= 3 and (best is None or y + 1 < best[1]):
                best = ((left + right) // 2, y + 1)
    return best


def reachable(room: Room, dash: bool = True) -> tuple[set, list, list]:
    nodes = [(x, y) for y in range(room.h) for x in range(room.w)
             if room.standable(x, y) or room.at(x, y) in "*W"]
    starts = sorted((x, y) for (x, y) in nodes if room.at(x, y) == "P")
    seen = set(starts[:1])
    queue = deque(starts[:1])
    chimneys: dict = {}
    while queue:
        ax, ay = queue.popleft()
        kind = room.at(ax, ay)
        for bx, by in nodes:
            if (bx, by) in seen:
                continue
            rise, run = ay - by, abs(bx - ax)
            target = room.at(bx, by)
            if kind == "W":
                ok = (target == "W" and run + abs(rise) == 1) or (room.at(ax, ay - 1) != "W" and rise <= JUMP_UP and run <= 5)
            elif kind == "*":
                ok = dash and ((rise <= DASH_UP + 1 and run <= 5) or (rise <= 0 and run <= 9))
            else:
                up = SPRING_UP if kind == "M" else JUMP_UP
                ok = (rise <= up and run <= JUMP_RUN - max(0, min(rise, JUMP_UP))) or (rise < 0 and run <= 9)
                if dash:
                    ok = ok or (rise <= up and run <= JUMP_RUN + DASH_RUN - max(0, min(rise, JUMP_UP)))
                    ok = ok or (rise <= up + DASH_UP and run <= 4) or (rise <= up + 2 and run <= 6)
                if not ok:
                    shaft = chimneys.get((ax, ay))
                    if shaft is None:
                        shaft = chimneys[(ax, ay)] = chimney_top(room, ax, ay) or (0, -99)
                    cx, top = shaft
                    ok = top >= 0 and by >= top - JUMP_UP and abs(bx - cx) <= 6 and room.clear(cx, top, bx, by)
            if ok and room.clear(ax, ay, bx, by):
                seen.add((bx, by))
                queue.append((bx, by))
    fires = [(x, y) for y in range(room.h) for x in range(room.w) if room.at(x, y) == "C"]
    exits = []
    for x, side in ((0, "esquerda"), (room.w - 1, "direita")):
        doors = [y for y in range(room.h) if room.standable(x, y) or (room.free(x, y) and room.standable(x + (1 if x == 0 else -1), y))]
        if doors:
            exits.append((side, any((x, y) in seen or (x + (1 if x == 0 else -1), y) in seen for y in doors)))
    return seen, [(f, f in seen) for f in fires], exits


def main() -> None:
    paths: list[str] = []
    for arg in sys.argv[1:]:
        if arg == "-v":
            continue
        paths += sorted(glob.glob(os.path.join(arg, "*.room"))) if os.path.isdir(arg) else [arg]
    bad = 0
    for path in paths:
        name, rows, dash = load(path)
        seen, fires, exits = reachable(Room(rows), dash)
        missing = [f for f, ok in fires if not ok]
        closed = [side for side, ok in exits if not ok]
        status = "ok" if not missing and not closed else "FALTA"
        room = Room(rows)
        ground = [(x, y) for y in range(room.h) for x in range(room.w) if room.standable(x, y)]
        lost = sorted({(min(x for x, yy in ground if yy == y and (x, yy) not in seen and abs(x - x0) < 12), y)
                       for x0, y in ground if (x0, y) not in seen})
        print("%-10s %-5s %-8s fogueiras %d/%d  saidas %s  chao alcancado %d%%%s%s" % (
            name, status, "" if dash else "sem dash", len(fires) - len(missing), len(fires),
            ", ".join("%s:%s" % (side, "sim" if ok else "NAO") for side, ok in exits) or "-",
            round(100 * sum(1 for g in ground if g in seen) / max(1, len(ground))),
            ("   fogueiras por alcancar: %s" % missing) if missing else "",
            ("   plataformas por alcancar (x, y): %s" % lost[:12]) if lost and "-v" in sys.argv else ""))
        bad += len(missing) + len(closed)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
