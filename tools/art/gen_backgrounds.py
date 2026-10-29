from __future__ import annotations

import math

from PIL import Image, ImageChops, ImageDraw, ImageOps

from vec import curve, ellipse, hash01, mix, rgba, ribbon, save

W, H = 1920, 720
MIST = "#c4f3e2"


def vgrad(w: int, h: int, stops: list[tuple[float, str]]) -> Image.Image:
    column = Image.new("RGBA", (1, h))
    px = column.load()
    for y in range(h):
        t = y / (h - 1)
        for (t0, a), (t1, b) in zip(stops, stops[1:]):
            if t0 <= t <= t1:
                px[0, y] = mix(a, b, (t - t0) / (t1 - t0))
                break
    return column.resize((w, h))


def glow(w: int, h: int, color: str, strength: float, power: float) -> Image.Image:
    alpha = ImageOps.invert(Image.radial_gradient("L")).point(lambda v: int(255 * strength * (v / 255) ** power))
    layer = Image.new("RGBA", (w, h), rgba(color))
    layer.putalpha(alpha.resize((w, h), Image.BICUBIC))
    return layer


def paste_center(base: Image.Image, layer: Image.Image, cx: int, cy: int) -> None:
    tmp = Image.new("RGBA", base.size, (0, 0, 0, 0))
    tmp.paste(layer, (cx - layer.width // 2, cy - layer.height // 2))
    base.alpha_composite(tmp)


def halve(img: Image.Image) -> Image.Image:
    return img.resize((img.width // 2, img.height // 2), Image.NEAREST)


def stepped_ramp(height: int, top: int, bottom: int, steps: int, start: float = 0.0) -> Image.Image:
    ramp = Image.new("L", (1, height))
    for y in range(height):
        t = max(0.0, (y / height - start) / (1.0 - start))
        ramp.putpixel((0, y), int(top + (bottom - top) * math.floor(t * steps) / steps))
    return ramp


def sky() -> None:
    img = vgrad(640, 360, [(0.0, "#0c1630"), (0.42, "#163f5c"), (0.8, "#2a777f"), (1.0, "#3c988f")])
    paste_center(img, glow(850, 500, "#86e2cf", 0.72, 1.25), 410, 225)
    paste_center(img, glow(230, 230, "#fdf9e4", 0.5, 1.7), 440, 125)
    paste_center(img, glow(450, 280, "#f0fbe2", 0.6, 1.6), 420, 235)
    img = img.convert("RGB").quantize(colors=18, dither=Image.Dither.NONE).convert("RGBA")
    d = ImageDraw.Draw(img)
    for k in range(150):
        x, y = int(hash01(k, 1, 5) * 640), int(hash01(k, 2, 5) ** 1.5 * 200)
        h = hash01(k, 3, 5)
        d.point((x, y), fill=rgba("#f1fdff" if h > 0.6 else "#a9d8e0" if h > 0.25 else "#5f9fb2"))
        if h > 0.94:
            d.point([(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)], fill=rgba("#a9d8e0"))
    d.ellipse([440 - 31, 125 - 31, 440 + 31, 125 + 31], fill=rgba("#fcf8e8"))
    d.ellipse([440 - 31, 125 - 31, 440 + 25, 125 + 25], fill=rgba("#fffdf3"))
    for cx, cy, r in ((431, 116, 6), (452, 134, 4), (436, 141, 3), (453, 113, 2)):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=rgba("#e6e2cd"))
    save(img, "backgrounds", "forest_sky.png")


class Layer:

    def __init__(self, seed: int, colors: dict):
        self.seed, self.col = seed, colors
        self.img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def poly(self, pts: list, color: str) -> None:
        for off in (-W, 0, W):
            self.d.polygon([(x + off, y) for x, y in pts], fill=rgba(self.col.get(color, color)))

    def clump(self, cx: float, cy: float, r: float, seed: int) -> None:
        for tone, count, spread, size, shift in (("leaf", 7, 0.7, 0.5, 0.0), ("leaf_m", 5, 0.5, 0.36, -0.18), ("leaf_l", 3, 0.36, 0.22, -0.32)):
            for i in range(count):
                a = hash01(i, seed, 31) * 6.283
                dist = r * spread * math.sqrt(hash01(i, seed, 32))
                rr = r * size * (0.75 + 0.5 * hash01(i, seed, 33))
                self.poly(ellipse((cx + math.cos(a) * dist + r * shift * 0.5, cy + math.sin(a) * dist * 0.75 + r * shift), rr, rr * 0.86, 0.0, 14), tone)
        for i in range(46):
            a = hash01(i, seed, 41) * 6.283
            dist = r * (0.3 + 0.95 * hash01(i, seed, 42))
            size = 3.0 + 4.0 * hash01(i, seed, 43)
            inner = dist < r * 0.75
            tone = ("leaf_l", "leaf_m", "leaf")[i % 3] if inner else ("leaf", "leaf_m")[i % 2]
            self.poly(ellipse((cx + math.cos(a) * dist, cy + math.sin(a) * dist * 0.8 - (r * 0.1 if inner else 0.0)), size, size * 0.5, a + 0.6, 8), tone)

    def vine(self, x: float, y0: float, length: float, seed: int) -> None:
        line = curve([(x + 9 * math.sin(i * 0.9 + seed), y0 + i * length / 7) for i in range(8)])
        self.poly(ribbon(line, 1.6, 1.2), "leaf")
        for i, p in enumerate(line[::4]):
            side = 1 if i % 2 else -1
            self.poly(ellipse((p[0] + side * 5, p[1]), 5, 2.6, side * 0.5, 8), "leaf_m" if i % 3 else "leaf_l")

    def trunk(self, x: float, w: float, k: int, branches: int, bark: bool) -> None:
        s = self.seed + k * 7
        amp = w * (0.25 + 0.6 * hash01(k, 1, s))
        freq, ph = 0.7 + hash01(k, 2, s), 6.283 * hash01(k, 3, s)

        def cx(y: float) -> float:
            return x + amp * math.sin(y / H * math.pi * freq + ph)

        def half(y: float) -> float:
            t = max(0.0, min(1.0, y / H))
            return w * 0.5 * (0.8 + 0.2 * t + 1.1 * max(0.0, (t - 0.8) / 0.2) ** 2)

        ys = list(range(-40, H + 41, 24))
        left = [(cx(y) - half(y), y) for y in ys]
        right = [(cx(y) + half(y), y) for y in ys]
        self.poly(left + right[::-1], "body")
        self.poly([(cx(y) + half(y) * 0.3, y) for y in ys] + right[::-1], "lit")
        self.poly(left + [(cx(y) - half(y) * 0.45, y) for y in ys][::-1], "dark")
        if bark:
            for b in range(12):
                off = -0.75 + 1.5 * hash01(b, k, s)
                y0 = hash01(b, k, s + 1) * H
                line = [(cx(y) + half(y) * off, y) for y in range(int(y0), int(y0 + 30 + 80 * hash01(b, k, s + 2)), 10)]
                self.poly(ribbon(line, max(1.0, w * 0.014), 1.0), "dark" if off < 0.25 else "body")
            for b in range(2):
                ky = 120 + hash01(b, k, s + 6) * 420
                self.poly(ellipse((cx(ky) - half(ky) * 0.1, ky), w * 0.11, w * 0.16), "dark")
                self.poly(ellipse((cx(ky) - half(ky) * 0.1, ky), w * 0.05, w * 0.09), "body")
        for b in range(branches):
            side = 1 if hash01(b, k, s + 3) < 0.5 else -1
            y0 = 60 + hash01(b, k, s + 4) * 330
            length = w * (1.6 + 2.2 * hash01(b, k, s + 5))
            p0 = (cx(y0) + side * half(y0) * 0.6, y0)
            line = curve([p0, (p0[0] + side * length * 0.5, y0 - length * 0.16), (p0[0] + side * length, y0 - length * 0.5)])
            self.poly(ribbon(line, w * 0.13, 1.5), "body")
            self.clump(p0[0] + side * length, y0 - length * 0.55, min(84.0, max(22.0, length * 0.34)), s + b)

    def fern(self, x: float, base_y: float, size: float) -> None:
        for f in range(6):
            lean = (f - 2.5) / 2.5
            tip = (x + lean * size * 0.95, base_y - size * (1.0 - 0.45 * abs(lean)))
            stem = curve([(x, base_y), (x + lean * size * 0.4, base_y - size * 0.75), tip], 8)
            self.poly(ribbon(stem, 1.6, 1.0), "leaf")
            for i in range(2, len(stem) - 1):
                t = i / len(stem)
                ang = math.atan2(stem[i + 1][1] - stem[i][1], stem[i + 1][0] - stem[i][0])
                reach = size * 0.2 * (1 - t) + 2.5
                for sgn in (-1, 1):
                    c = (stem[i][0] + math.cos(ang + sgn * 1.25) * reach * 0.55, stem[i][1] + math.sin(ang + sgn * 1.25) * reach * 0.55)
                    self.poly(ellipse(c, reach * 0.62, max(1.2, reach * 0.24), ang + sgn * 1.25, 8), "leaf_m" if (i + f) % 2 else "leaf_l")

    def grass(self, x: float, base_y: float, height: float, seed: int) -> None:
        for i in range(5):
            bend = (hash01(i, seed, 51) - 0.5) * height * 0.9
            hh = height * (0.5 + 0.5 * hash01(i, seed, 52))
            bx = x + (i - 2) * 5
            self.poly(ribbon(curve([(bx, base_y), (bx + bend * 0.4, base_y - hh * 0.6), (bx + bend, base_y - hh)]), 2.2, 1.0), "leaf_m" if i % 2 else "leaf")

    def finish(self, haze: int) -> Image.Image:
        if haze > 0:
            mist = Image.new("RGBA", (W, H), rgba(MIST))
            mist.putalpha(ImageChops.multiply(self.img.getchannel("A"), stepped_ramp(H, 0, haze, 7, 0.35).resize((W, H))))
            self.img.alpha_composite(mist)
        return halve(self.img)


def forest_layer(name: str, seed: int, colors: dict, trunks: int, widths: tuple[float, float], haze: int,
                 branches: int = 0, bark: bool = False, ferns: int = 0, vines: int = 0,
                 canopy: tuple[float, float] = (1.0, -20.0)) -> None:
    layer = Layer(seed, colors)
    for k in range(trunks):
        x = (k + 0.15 + 0.7 * hash01(k, 0, seed)) * W / trunks
        layer.trunk(x, widths[0] + (widths[1] - widths[0]) * hash01(k, 9, seed), k, branches, bark)
    for v in range(vines):
        layer.vine((v + hash01(v, 21, seed)) * W / vines, -10, 110 + 190 * hash01(v, 22, seed), seed + v)
    x, k = 0.0, 0
    while x < W:
        r = (60 + 60 * hash01(k, 11, seed)) * canopy[0]
        layer.clump(x, canopy[1] + 50 * hash01(k, 12, seed), r, seed + 100 + k)
        x += r * (0.9 + 0.7 * hash01(k, 13, seed))
        k += 1
    x, k = 0.0, 0
    while x < W:
        r = 34 + 40 * hash01(k, 14, seed)
        layer.clump(x, H - 6 + 22 * hash01(k, 15, seed), r, seed + 200 + k)
        x += r * (1.3 + 1.2 * hash01(k, 16, seed))
        k += 1
    for f in range(ferns):
        fx = (f + hash01(f, 17, seed)) * W / ferns
        layer.fern(fx, H - 20 - 30 * hash01(f, 18, seed), 70 + 60 * hash01(f, 19, seed))
        layer.grass(fx + 90, H - 30, 46 + 30 * hash01(f, 20, seed), seed + f)
    save(layer.finish(haze), "backgrounds", f"{name}.png")


def rays() -> None:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for i in range(9):
        x0 = (i + hash01(i, 1, 3)) * W / 9
        tw = 26 + 70 * hash01(i, 2, 3)
        quad = [(x0, -20), (x0 + tw, -20), (x0 + tw * 2.4 - 280, H), (x0 - 280, H)]
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        for off in (-W, 0, W):
            d.polygon([(x + off, y) for x, y in quad], fill=rgba("#fbffe6", int(30 + 26 * hash01(i, 3, 3))))
        img.alpha_composite(layer)
    img.putalpha(ImageChops.multiply(img.getchannel("A"), stepped_ramp(H, 255, 60, 5).resize((W, H))))
    save(halve(img), "backgrounds", "forest_rays.png")


def fog() -> None:
    hh = 300
    img = Image.new("RGBA", (W, hh), (0, 0, 0, 0))
    for k in range(30):
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        x, y = hash01(k, 1, 21) * W, 90 + hash01(k, 2, 21) * 120
        rx, ry = 150 + 260 * hash01(k, 3, 21), 10 + 22 * hash01(k, 4, 21)
        for off in (-W, 0, W):
            d.ellipse([x + off - rx, y - ry, x + off + rx, y + ry], fill=rgba("#d4f8ec", 22))
        img.alpha_composite(layer)
    save(halve(img), "backgrounds", "forest_fog.png")


def main() -> None:
    sky()
    forest_layer("forest_far", 11, {"body": "#74bdb5", "lit": "#98d9cb", "dark": "#69b2ad", "leaf": "#62ada9", "leaf_m": "#78c0b7", "leaf_l": "#93d5c8"},
                 trunks=17, widths=(16, 34), haze=170, canopy=(0.8, -10.0))
    forest_layer("forest_mid2", 23, {"body": "#3f8f96", "lit": "#66b6b0", "dark": "#367f89", "leaf": "#33798a", "leaf_m": "#4696a0", "leaf_l": "#65b7b0"},
                 trunks=11, widths=(26, 52), haze=150, branches=1, vines=6, canopy=(1.0, -15.0))
    rays()
    forest_layer("forest_mid", 37, {"body": "#22587a", "lit": "#3f9398", "dark": "#1b4370", "leaf": "#1c4b72", "leaf_m": "#276c84", "leaf_l": "#3c9296"},
                 trunks=7, widths=(40, 78), haze=120, branches=2, bark=True, ferns=5, vines=7, canopy=(1.15, -30.0))
    forest_layer("forest_near", 53, {"body": "#142c52", "lit": "#235d72", "dark": "#0e1f40", "leaf": "#11264a", "leaf_m": "#173d5c", "leaf_l": "#215a70"},
                 trunks=4, widths=(70, 120), haze=70, branches=2, bark=True, ferns=7, vines=5, canopy=(1.0, -75.0))
    fog()
    print("fundos: ok")


if __name__ == "__main__":
    main()
