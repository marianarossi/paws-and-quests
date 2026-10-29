from __future__ import annotations

import json
import os
import subprocess
import sys
import time

from PIL import Image

import gen_zones
from gen_bestiary import write
from vec import ASSETS, DOCS_PREVIEW, ROOT, rgba

GODOT = os.path.normpath(os.path.join(ROOT, "..", "Godot_v4.6.3-stable_win64", "Godot_v4.6.3-stable_win64_console.exe"))
OUT = os.path.join(DOCS_PREVIEW, "zonas")
ORDER = list(gen_zones.THEMES)


def name_of(zone: str) -> str:
    return "%02d_%s.png" % (ORDER.index(zone) + 1, zone)


def capture(zone: str) -> None:
    shot = os.path.join(ROOT, "captures", "shot.png")
    if os.path.exists(shot):
        os.remove(shot)
    subprocess.run([GODOT, "--path", ROOT, "--", "--shot=2.5", "--map=zones", "--room=" + zone],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90, check=False)
    img = Image.open(shot).convert("RGB").resize((1280, 720), Image.NEAREST)
    for attempt in range(5):
        try:
            img.save(os.path.join(OUT, name_of(zone)))
            break
        except OSError:
            time.sleep(1.0)
    os.remove(shot)


def sheets() -> None:
    for start in range(0, len(ORDER), 4):
        group = ORDER[start:start + 4]
        sheet = Image.new("RGBA", (1280, 2 * (360 + 22)), rgba("#151229"))
        for k, zone in enumerate(group):
            path = os.path.join(OUT, name_of(zone))
            if not os.path.exists(path):
                continue
            data = json.load(open(os.path.join(ASSETS, "themes", zone + ".json"), encoding="utf-8"))
            x0, y0 = (k % 2) * 640, (k // 2) * 382
            sheet.paste(Image.open(path).resize((640, 360), Image.NEAREST), (x0, y0 + 22))
            end = write(sheet, x0 + 6, y0 + 3, "%02d" % (start + k + 1), "#ff8ad0")
            end = write(sheet, end + 5, y0 + 3, data["title"], "#ffffff")
            ground = data.get("ground", "")
            write(sheet, x0 + 6, y0 + 12, ground if len(ground) <= 86 else ground[:86].rsplit(" ", 1)[0] + "...", "#9fb0e0")
        sheet.convert("RGB").save(os.path.join(OUT, "folha_%d.png" % (start // 4 + 1)))


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    zones = [a for a in sys.argv[1:] if not a.startswith("--")] or ORDER
    if "--sheets" not in sys.argv:
        for zone in zones:
            capture(zone)
            print("captura %s" % zone)
    sheets()


if __name__ == "__main__":
    main()
