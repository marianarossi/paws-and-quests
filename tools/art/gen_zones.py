from __future__ import annotations

import json
import math
import os
import sys

from PIL import Image, ImageDraw

import gen_backgrounds as forest_kit
import gen_terrain
from vec import ASSETS, DOCS_PREVIEW, save_json
from zonekit import (H, W, Art, aurora, birds, boat, cave, chains, cloud_bank, column, crystal, crystals, cumulus, cypress,
                     dead_tree, disc, fog, foliage, forge, giant_tree, islands, kelp, lake, land, lavafall, light_spill,
                     lightning, mist, peaks, pine, plates, profile, rays, reeds, rock_pillars, roots, round_tree, scatter, sea,
                     sky, sparkles, stars, statue_dog, storm_ceiling, strata_lines, stratus, temple, tone, village)

THEMES: dict = {}


def theme(fn):
    THEMES[fn.__name__] = fn
    return fn


def terrain(stone: str, grass: str, soil: str, moss: str | None = None, root: str | None = None, accent: str | None = None, **flags) -> dict:
    moss = moss or tone(grass, -0.3, -0.2)
    root = root or tone(soil, 0.25, -0.1)
    pal = {
        "edge": tone(stone, -0.72, 0.1), "gap": tone(stone, -0.6, 0.05),
        "earth": tone(stone, -0.42), "earth_l": tone(stone, -0.22), "earth_d": tone(stone, -0.52),
        "stones": [(tone(stone, -0.12), tone(stone, 0.38, -0.15), tone(stone, -0.32)),
                   (stone, tone(stone, 0.48, -0.18), tone(stone, -0.24)),
                   (tone(stone, 0.12), tone(stone, 0.6, -0.2), tone(stone, -0.16)),
                   (tone(stone, -0.05, 0.1, 0.06), tone(stone, 0.4, 0.0, 0.06), tone(stone, -0.3, 0.1, 0.06))],
        "rim": tone(stone, 0.5, -0.2), "shadow": tone(stone, -0.6, 0.05),
        "grass": grass, "grass_l": tone(grass, 0.45, -0.35), "grass_d": tone(grass, -0.38, 0.1),
        "moss": moss, "moss_d": tone(moss, -0.35, -0.1),
        "root": root, "root_l": tone(root, 0.4, -0.2),
        "soil": soil, "soil_l": tone(soil, 0.28), "soil_d": tone(soil, -0.28),
        "pebble": accent or tone(stone, 0.6, -0.3),
    }
    pal.update(flags)
    return pal


def triples(*bases: str, light: float = 0.42, dark: float = -0.26) -> list:
    return [(b, tone(b, light, -0.15), tone(b, dark)) for b in bases]


def stack(*arts: Art) -> Image.Image:
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for art in arts:
        out.alpha_composite(art.img)
    return out


def wood_tone(body: str) -> dict:
    return {"body": body, "lit": tone(body, 0.32, -0.15), "dark": tone(body, -0.16, 0.05),
            "leaf": tone(body, -0.1, 0.05, 0.02), "leaf_m": tone(body, 0.12, 0.0, 0.02), "leaf_l": tone(body, 0.34, -0.12, 0.02)}


def woods(zone: str, mist: str, trunks: tuple, seed: int = 0) -> list:
    setup = [("far", 11, dict(trunks=17, widths=(16, 34), haze=170, canopy=(0.8, -10.0)), 0.05),
             ("mid2", 23, dict(trunks=11, widths=(26, 52), haze=150, branches=1, vines=6, canopy=(1.0, -15.0)), 0.12),
             ("mid", 37, dict(trunks=7, widths=(40, 78), haze=120, branches=2, bark=True, ferns=5, vines=7, canopy=(1.15, -30.0)), 0.24),
             ("near", 53, dict(trunks=4, widths=(70, 120), haze=70, branches=2, bark=True, ferns=7, vines=5, canopy=(1.0, -75.0)), 0.42)]
    keep = forest_kit.MIST
    forest_kit.MIST = mist
    out = []
    for (name, base_seed, options, scale), body in zip(setup, trunks):
        forest_kit.forest_layer(f"{zone}_{name}", base_seed + seed, wood_tone(body), **options)
        out.append((f"{zone}_{name}.png", scale))
    forest_kit.MIST = keep
    return out


def build(zone: str, fast: bool = False) -> dict:
    spec = THEMES[zone]()
    files = []
    spec["sky"].save(f"{zone}_sky")
    for i, entry in enumerate(spec["layers"]):
        art, scale = entry[0], entry[1]
        extra = entry[2] if len(entry) > 2 else {}
        name = art if isinstance(art, str) else art.save(f"{zone}_{i + 1}")
        files.append(dict({"texture": name, "scale": scale}, **extra))
    if not fast:
        gen_terrain.PALETTES[zone] = spec["terrain"]
        gen_terrain.make_terrain(zone)
    data = {"id": zone, "title": spec["title"], "family": spec["family"], "idea": spec["idea"], "ground": spec.get("ground", ""),
            "terrain": f"{zone}_terrain.png", "sky": f"{zone}_sky.png", "layers": files}
    for key in ("decor", "platform", "water_platform", "fore", "critters", "ambience", "music", "checkpoint", "ambient", "decor_tint", "platform_tint", "decor_density", "ceiling_density", "particles", "particle_color",
                "water_top", "water_deep", "water_foam", "spring_colors", "depth_color", "depth_strength"):
        if key in spec:
            data[key] = spec[key]
    save_json(data, "themes", f"{zone}.json")
    return data


@theme
def arcadia() -> dict:
    heaven = sky([(0, "#3d74c7"), (70, "#5594dc"), (135, "#86bfee"), (190, "#bfe1f4"), (232, "#f3e9c4"), (262, "#fbdca0")], smooth=2)
    disc(heaven, 520, 64, 18, "#fff8d6", "#ffeeb0", 3.0, 0.5)
    stratus(heaven, 3, 8, 170, 236, ("#ffffff", "#f6e6c0"), (40, 140))
    clouds = Art()
    cumulus(clouds, 5, 4, 150, 214, (100, 200), ("#ffffff", "#f6fafe", "#dbe8f5", "#b6cbe4"), (0.5, -0.7), 0.55)
    range_ = Art()
    peaks(range_, 2, [(70, 150, 130), (214, 178, 100), (372, 138, 150), (546, 170, 120)],
          ("#d6e8f4", "#c2daee", "#aecbe4", "#9cbcd8", "#8eaecd"), 1, 252, snow=("#ffffff", "#e2eef8", 16), haze=("#dcedf4", 196, 0.9))
    far = Art()
    far_line = profile(3, 232, 34)
    land(far, far_line, "#8fc0c4", "#a9d6cf", "#7fb0bb", depth=0.6, seed=3)
    village(far, far_line, 180, 8, "#6f9aa8", "#587f92", "#fff0b0")
    mid = Art()
    mid_line = profile(8, 268, 40)
    for x, h in scatter(21, 16, 26, 48):
        round_tree(mid, x, mid_line[x] + 4, h, x, "#4a7a5c", ("#5fae6e", "#8fd07c", "#488f66"))
    land(mid, mid_line, "#62ac74", "#8ccb82", "#4e9668", depth=0.5, seed=8)
    near = Art()
    near_line = profile(13, 322, 30)
    for x, h in scatter(33, 6, 70, 120):
        round_tree(near, x, near_line[x] + 6, h, x + 5, "#1f4a3e", ("#2c7a58", "#4aa468", "#205e4e"))
    land(near, near_line, "#2f8058", "#46a066", "#236a50", depth=0.5, seed=13)
    reeds(near, 5, 359, 70, ("#1c4f42", "#2f7a55"), (10, 34), ("#fff3c0", "#bfe4ff", "#ffffff"))
    return dict(
        title="Prado de Arcádia", family="Ember Camp",
        idea="O acampamento de dia: colinas verdes, árvores redondas, vila e moinho, serra azulada ao longe e cúmulos altos.",
        ground="Pedra quente com terra e relva em flor (brancas, amarelas e azuis).",
        sky=heaven, layers=[(clouds, 0.02, {"autoscroll": -1.5}), (range_, 0.03), (far, 0.05), (mid, 0.14), (near, 0.36)],
        terrain=terrain("#6f6558", "#58c466", "#7a5238", flowers=["#ffffff", "#ffe36a", "#bfe4ff"], flower_chance=0.5),
        ambient="#fffbf0", particles="motes", particle_color="#fff6c0",
        water_top="#7fd8ee80", water_deep="#2f6faabd", water_foam="#f4fffff2", spring_colors=["lilac", "pink"])


@theme
def twilight_grove() -> dict:
    import gen_bg_grove
    art = gen_bg_grove.build()
    return dict(
        title="Twilight Grove", family="Floresta",
        idea="A parte mais densa da floresta, já de noite: lua em quarto, último clarão do pôr do sol no horizonte, pinheiros altos e juntos, raios de luar entre os ramos e névoa em tons pastel.",
        ground="Pedra arroxeada com terra e relva verde-água, com florzinhas claras.",
        sky=art["sky"], layers=art["layers"], decor="grove_decor.json",
        terrain=terrain("#3d3a6a", "#3f9a8c", "#4c3654", flowers=["#bfe4ff", "#fff0b0"], flower_chance=0.25),
        ambient="#b4b8f0", particles="fireflies", particle_color="#ffd27a", decor_tint="#c8d0f0", decor_density=1.0,
        water_top="#8a9ad880", water_deep="#1e2260bd", water_foam="#e6ecfff2", spring_colors=["aqua", "pink"])


@theme
def canopy() -> dict:
    heaven = sky([(0, "#a8dcae"), (110, "#c6eab6"), (220, "#e4f4be"), (300, "#f6f8cc")], smooth=2)
    disc(heaven, 330, 46, 26, "#fffde0", "#fff6b0", 3.2, 0.5)
    layers = woods("canopy", "#eaf7c4", ("#9fd39a", "#6fb47c", "#3f8a5e", "#1d5a40"))
    light = Art()
    rays(light, 4, 9, "#fffbd0", 34, -170)
    layers.insert(2, (light, 0.16))
    return dict(
        title="Copas de Whisperwood", family="Whisperwood",
        idea="Lá em cima, nas copas: luz verde-clara do sol filtrada pelas folhas, troncos e ramos como caminho.",
        ground="Madeira: o veio de um ramo gigante, coberto de musgo e folhas.",
        sky=heaven, layers=layers,
        terrain=terrain("#7a5238", "#62c24e", "#4a3226", moss="#3f8a4a", pattern="strata", pattern_args={"wave": 5.0}, band="none",
                        stones=triples("#7a5238", "#8a6040", "#6a4630", "#94683e"), gap="#3c261c", edge="#22140e",
                        flowers=["#fff6a0", "#ffffff"], flower_chance=0.2),
        ambient="#fbfff0", particles="petals", particle_color="#a8dc6a", decor_tint="#f0ffd0",
        water_top="#9fe8b080", water_deep="#2f7a5abd", water_foam="#f4ffe8f2", spring_colors=["lilac", "pink"])


@theme
def moth_glade() -> dict:
    heaven = sky([(0, "#2a1e4c"), (90, "#4a2f6c"), (170, "#864a8c"), (240, "#d488a8"), (300, "#f6c6c2")], smooth=2)
    layers = woods("moth_glade", "#f6cfe0", ("#c79ac4", "#96609c", "#5a3274", "#2a1842"), 4)
    light = Art()
    rays(light, 9, 7, "#ffe0f0", 30, -150)
    haze = Art()
    mist(haze, 6, 226, 316, 10, "#ffd8ec", (120, 300), (2, 5))
    layers.insert(2, (light, 0.16))
    layers.insert(4, (haze, 0.3, {"autoscroll": -5}))
    return dict(
        title="Clareira das Mariposas", family="Whisperwood",
        idea="Uma abertura na floresta com névoa rosada, luz de lado e flores que brilham; a casa das Gloommoths.",
        ground="Pedra lilás com terra e relva lilás, com flores que brilham.",
        sky=heaven, layers=layers,
        terrain=terrain("#4c3464", "#a890ea", "#5a3a58", moss="#7a5aa8", flowers=["#ffffff", "#ffe9a0", "#bff4ff"], flower_chance=0.45),
        ambient="#f2dcff", particles="fireflies", particle_color="#ffd8f4", decor_tint="#e8c8f8",
        water_top="#f0a8d880", water_deep="#4a2a70bd", water_foam="#fff0f8f2", spring_colors=["aqua", "green"])


@theme
def deep_wood() -> dict:
    heaven = sky([(0, "#05111e"), (120, "#0a2030"), (230, "#113a4a"), (310, "#1c5a5e")], smooth=2)
    layers = woods("deep_wood", "#1c5a5e", ("#1f5a66", "#164452", "#0f2f40", "#07151f"), 9)
    light = Art()
    rays(light, 2, 6, "#8ff4e4", 26, -120, (10, 34))
    layers.insert(2, (light, 0.16))
    return dict(
        title="Bosque Fundo", family="Whisperwood",
        idea="O coração da floresta: quase sem luz, troncos enormes, feixes verde-água e vagalumes azulados.",
        ground="Pedra escura atravessada por raízes grossas, com musgo verde-água.",
        sky=heaven, layers=layers,
        terrain=terrain("#202c48", "#2fa08e", "#2a2c3c", moss="#1f6a70", accent="#7ff0d0", root="#6a5648", extras=["roots"]),
        ambient="#9ac4dc", particles="fireflies", particle_color="#7ff0e0", decor_tint="#a8d8e8",
        water_top="#5ad0c080", water_deep="#0a2a40c4", water_foam="#c8fff4f2", spring_colors=["lilac", "pink"])


@theme
def glow_lake() -> dict:
    import gen_bg_hollow
    art = gen_bg_hollow.build()
    return dict(
        title="Glimmer Hollow", family="Floresta",
        idea="Uma clareira com um grande lago, de noite: a lua e o seu rasto a tremeluzir na água, um maciço de montanha com neve espelhado, vitórias-régias, névoa rente à água, juncos e sapinhos.",
        ground="Terra castanha que passa a ameixa e a pedra azul-violeta, com relva verde-menta e florzinhas claras.",
        sky=art["sky"], layers=art["layers"], water_platform=art["platform"], decor="grove_decor.json",
        terrain=terrain("#35377a", "#58d6a8", "#6e4a38", moss="#2f8f86", flowers=["#c8f4ff", "#fff0c8", "#ffd0e8"], flower_chance=0.22,
                        earth="#51384e", earth_l="#684858", earth_d="#3e2b42", earth_chance=0.52, extras=("rootlets",)),
        ambient="#c0c0ff", particles="fireflies", particle_color="#d8ff8a", decor_tint="#d0d4f8", decor_density=0.8,
        critters="frogs", ambience="lake_loop", music="burrow_echoes",
        water_top="#7f88e84c", water_deep="#0e0c36fa", water_foam="#e4dcfff0", spring_colors=["pink", "green"])


ICE = ("#d4f8ff", "#5ad0f4", "#2a68b0")
LILAC = ("#f0e0ff", "#b08af0", "#6040a8")


@theme
def crystal_cave() -> dict:
    heaven = sky([(0, "#07071a"), (120, "#0e0e30"), (240, "#161648"), (330, "#1e1e5c")], smooth=1)
    back = Art()
    back.glow(170, 210, 170, "#26349a", 0.55, 1.3)
    back.glow(470, 150, 180, "#44289a", 0.5, 1.3)
    for x, length, ang, half, hue in ((70, 340, 0.52, 20, 0), (292, 400, -0.34, 27, 1), (486, 310, 0.78, 17, 0), (610, 380, -0.62, 23, 1)):
        crystal(back, x, 372, length, ang, half, (("#3e54b4", "#2c3e98", "#1f2c78"), ("#5e42b4", "#48329a", "#34267a"))[hue])
    rock_pillars(back, 6, 3, ("#141438", "#22225a", "#0f0f2c"), (12, 26))
    far = Art()
    cave(far, 3, ("#1c1c48", "#34347c", "#151538"), (60, 40), (300, 36), (11, 9), 40)
    floor, roof = [], []
    for i, (x, s) in enumerate(scatter(41, 6, 30, 50)):
        floor.append((x, 300 - (i % 3) * 10, s, ICE if i % 2 else LILAC, "#5ad6ff" if i % 2 else "#b48aff"))
    for i, (x, s) in enumerate(scatter(53, 4, 24, 40)):
        roof.append((x, 62 + (i % 2) * 8, s, LILAC if i % 2 else ICE, "#b48aff" if i % 2 else "#5ad6ff"))
    light_spill(far, [(x, y - s * 0.5, s * 2.4, glow) for x, y, s, _, glow in floor] + [(x, y + s * 0.5, s * 2.2, glow) for x, y, s, _, glow in roof], 0.8)
    for x, y, s, hue, glow in floor:
        crystals(far, x, y, s, x, hue, glow)
    for x, y, s, hue, glow in roof:
        crystals(far, x, y, s, x + 2, hue, glow, down=True)
    sparkles(far, 3, 26, (0, 60, W, 300))
    mid = Art()
    cave(mid, 12, ("#121232", "#2a2a66", "#0c0c24"), (36, 30), (326, 30), (8, 6), 60)
    big = [(96, 326, 76, ICE, "#7ae0ff"), (330, 334, 58, LILAC, "#c8a0ff"), (556, 322, 84, ICE, "#7ae0ff")]
    hung = [(214, 40, 50, LILAC, "#c8a0ff"), (452, 46, 62, ICE, "#7ae0ff")]
    light_spill(mid, [(x, y - s * 0.4, s * 2.0, glow) for x, y, s, _, glow in big] + [(x, y + s * 0.4, s * 1.8, glow) for x, y, s, _, glow in hung], 0.85)
    for x, y, s, hue, glow in big:
        crystals(mid, x, y, s, x + 1, hue, glow, count=6)
    for x, y, s, hue, glow in hung:
        crystals(mid, x, y, s, x + 2, hue, glow, down=True, count=5)
    sparkles(mid, 8, 18, (0, 40, W, 330))
    near = Art()
    cave(near, 20, ("#070716", "#15153a", "#04040e"), (14, 22), (350, 18), (5, 4), 80)
    for x, s, ang in ((30, 110, 0.3), (600, 130, -0.25)):
        crystal(near, x, 366, s, ang, 13, ("#1c1c50", "#0e0e2c", "#070716"))
    return dict(
        title="Galerias de Cristal", family="Glimmer Hollow",
        idea="Glimmer Hollow por dentro: prismas gigantes ao fundo, cachos de cristal azul e lilás que iluminam a rocha à volta, brilhos no ar.",
        ground="Rocha escura com cristais embutidos e veios que brilham; lascas de cristal no chão e nos tetos.",
        sky=heaven, layers=[(back, 0.04), (far, 0.09), (mid, 0.2), (near, 0.46)],
        terrain=terrain("#30345e", "#6ad6f4", "#262648", moss="#8fe6ff", accent="#8fe6ff", extras=["crystals"], gems=[ICE, LILAC],
                        cover="shards", band="none", hang="shards", hang_body="#6ad6f4", hang_tip="#e6fbff",
                        grass_l="#e6fbff", grass_d="#2f6fb8", tufts=False, side_moss=False, corner_tuft=False, radius=5.0),
        ambient="#a8b6f4", particles="motes", particle_color="#8fe6ff", decor_density=0.0, ceiling_density=0.0,
        water_top="#6ad6ff80", water_deep="#1a2a80c4", water_foam="#d0f8fff2", spring_colors=["lilac", "aqua"])


@theme
def root_cavern() -> dict:
    heaven = sky([(0, "#170d08"), (140, "#27170e"), (260, "#3c2212"), (340, "#5a3418")], smooth=1)
    far = Art()
    cave(far, 5, ("#3a2616", "#70481f", "#2c1c10"), (50, 36), (310, 30), (8, 6), 36)
    lamps = [(90, 150), (240, 210), (400, 130), (560, 200)]
    light_spill(far, [(x, y, 70, "#ffb050") for x, y in lamps], 0.6)
    for i, (x, y) in enumerate(lamps):
        far.glow(x, y, 30, "#ff9a2a", 0.55, 1.2)
        far.rect(x - 1, y - 2, x + 1, y + 1, "#ffe08a")
        far.line([(x, y - 3), (x, y - 40 - i * 9)], "#2c1c10", 1)
    behind = Art()
    roots(behind, 3, 5, ("#4c311d", "#8a5c30", "#33200f"), (60, 280), (9, 20))
    mid = Art()
    cave(mid, 14, ("#22150b", "#4c311d", "#190e07"), (30, 26), (332, 24), (6, 5), 50)
    roots(mid, 9, 3, ("#2c1c10", "#5a3c20", "#1c1008"), (40, 300), (14, 30))
    near = Art()
    cave(near, 22, ("#0f0804", "#2c1c10", "#080402"), (12, 20), (352, 16), (4, 3), 70)
    return dict(
        title="Caverna das Raízes", family="Glimmer Hollow",
        idea="Por baixo da árvore gigante: raízes grossas atravessam a gruta e fazem de ponte, à luz de lanternas de âmbar.",
        ground="Terra castanha tecida de raízes cor de âmbar, com musgo seco por cima.",
        sky=heaven, layers=[(far, 0.06), (behind, 0.13), (mid, 0.24), (near, 0.46)],
        terrain=terrain("#4c3826", "#8a9a3e", "#5c3c24", moss="#5a6a2c", root="#9a6830", extras=["roots"]),
        ambient="#ffd9a8", particles="motes", particle_color="#ffcf80", decor_tint="#ffe0b0",
        water_top="#d8b05a80", water_deep="#3a240ec4", water_foam="#fff0c8f2", spring_colors=["aqua", "lilac"])


@theme
def misty_ridge() -> dict:
    heaven = sky([(0, "#6f9cc6"), (90, "#93b6d8"), (170, "#bdd2e6"), (236, "#e2e9ea"), (290, "#f4efe0")], smooth=2)
    disc(heaven, 150, 84, 17, "#fffef4", "#ffffff", 4.2, 0.55)
    stratus(heaven, 2, 9, 40, 150, ("#ffffff", "#dbe6f0"), (60, 200))
    far = Art()
    peaks(far, 4, [(96, 128, 150), (262, 70, 176), (420, 134, 130), (560, 96, 156)],
          ("#f6fafd", "#d9e4ef", "#c0d0e2", "#a8bcd4", "#98aecb"), -1, 300, snow=("#ffffff", "#dde8f3", 50), haze=("#e9eff2", 196, 0.95), fan=6.0)
    birds(far, 3, 7, 60, 140, "#7f97b4")
    veil1 = Art()
    mist(veil1, 2, 196, 250, 7, "#f6f8f8", (160, 380), (5, 13))
    second = Art()
    peaks(second, 9, [(30, 214, 84), (136, 180, 100), (250, 222, 80), (352, 168, 112), (470, 208, 90), (580, 186, 96)],
          ("#c4d4e6", "#a8bdd6", "#8da6c4", "#7690b2", "#6680a4"), -1, 330, trees=("#5c7a98", "#4c6a8a", 268, 16), haze=("#d2deea", 262, 0.75), rough=1.3)
    veil2 = Art()
    mist(veil2, 6, 250, 296, 6, "#eef3f6", (140, 340), (4, 10))
    third = Art()
    third_line = profile(15, 302, 60, 0.4)
    for x, h in scatter(31, 22, 24, 54):
        pine(third, x, third_line[x] + 4, int(h), x, "#3f5f7c", "#345270")
    land(third, third_line, "#5c7a9a", "#7494b0", "#4e6a8a", depth=0.5, seed=15, haze=("#b6c9da", 300, 0.5), light=-1)
    near = Art()
    near_line = profile(21, 344, 18)
    for x, h in scatter(43, 6, 100, 180):
        pine(near, x, near_line[x] + 6, int(h), x + 3, "#1c3650", "#152a40")
    land(near, near_line, "#1c3650", seed=21)
    veil3 = Art()
    fog(veil3, 8, "#eef4f8", 270, 340, 16, 30)
    return dict(
        title="Encosta em Névoa", family="Thunder Ridge",
        idea="A subida da montanha de manhã: um pico nevado em facetas, uma segunda serra com a linha das árvores, faixas de névoa entre elas e pinheiros.",
        ground="Ardósia em camadas inclinadas, com terra e relva de montanha em flor.",
        sky=heaven, layers=[(far, 0.03), (veil1, 0.05, {"autoscroll": -2}), (second, 0.08), (veil2, 0.11, {"autoscroll": -4}),
                            (third, 0.17), (near, 0.4), (veil3, 0.5, {"autoscroll": -7})],
        terrain=terrain("#5c6a82", "#5aa27a", "#5c4c46", pattern="strata", pattern_args={"tilt": 0.25, "wave": 2.0},
                        stones=triples("#5c6a82", "#6a7890", "#525e76", "#62788a"), flowers=["#ffffff", "#fff0a0", "#cfe0ff"], flower_chance=0.35),
        ambient="#eaf2ff", particles="motes", particle_color="#ffffff",
        water_top="#9fc8e080", water_deep="#2f4f78c0", water_foam="#fffffff2", spring_colors=["lilac", "pink"])


@theme
def ochre_cliffs() -> dict:
    heaven = sky([(0, "#c68848"), (90, "#d8a05a"), (180, "#e9c078"), (260, "#f5dc9c"), (310, "#fbeab8")], smooth=2)
    disc(heaven, 430, 120, 34, "#fff4cc", "#ffe6a0", 2.4, 0.5)
    stratus(heaven, 6, 8, 60, 200, ("#fbe6b4", "#e2b070"), (60, 220))
    far = Art()
    mesas = [max(p, 186) for p in profile(5, 250, 110, 0.3)]
    land(far, mesas, "#d8a868", "#eac488", "#c4925a", depth=0.6, seed=5, haze=("#f0d290", 236, 0.7))
    strata_lines(far, ("#d8a868", "#e4b878", "#c08c56"), 5, 9)
    mid = Art()
    peaks(mid, 8, [(70, 214, 70), (200, 182, 90), (330, 226, 70), (452, 176, 100), (584, 206, 80)],
          ("#f0b060", "#d8944e", "#b8743c", "#96582e", "#7c4626"), 1, 330, rough=1.5)
    strata_lines(mid, ("#b8743c", "#c88848", "#96582e"), 8, 7)
    for x, h in scatter(27, 6, 18, 34):
        dead_tree(mid, x, 322, h, (x % 5 - 2) * 0.06, x, "#4a2a1c", 3)
    near = Art()
    land(near, profile(17, 356, 100, 0.9, (2, 3, 5, 8, 13)), "#3c2014", "#5c3420", None, depth=0.3, seed=17)
    return dict(
        title="Falésias Ocres", family="Thunder Ridge",
        idea="A parede da montanha ao sol: mesas ao longe, picos de rocha em camadas ocre e ferrugem, árvores secas e poeira no ar.",
        ground="Arenito em camadas deitadas, creme e ferrugem, com areia e erva seca por cima.",
        sky=heaven, layers=[(far, 0.04), (mid, 0.15), (near, 0.42)],
        terrain=terrain("#a26a3e", "#d8c060", "#8a5a34", moss="#8a7a34", pattern="strata", pattern_args={"wave": 3.0},
                        stones=triples("#a8683a", "#c88a4c", "#8c5430", "#dcae6c"), cover="thin", hang=False,
                        grass_l="#f6e6a8", grass_d="#b89a48", blade="#d8c060"),
        ambient="#ffe8c8", particles="motes", particle_color="#ffe2a0", decor_tint="#e8d090", decor_density=0.35, ceiling_density=0.0,
        water_top="#d8c07080", water_deep="#6a5a2ac0", water_foam="#fff8d8f2", spring_colors=["aqua", "lilac"])


@theme
def storm_crest() -> dict:
    heaven = sky([(0, "#0e131f"), (90, "#1a2234"), (180, "#2a364e"), (260, "#42526a"), (320, "#5c6e84")], smooth=2)
    clouds = Art()
    flash = ("#dfe6fa", "#9aa9d6", "#5a6a9c", "#2c3650")
    lightning(clouds, 170, 60, 200, 256, 3, forks=4, glow=20)
    lightning(clouds, 452, 64, 420, 214, 8, forks=3)
    lightning(clouds, 330, 60, 350, 150, 5, forks=2, glow=12)
    storm_ceiling(clouds, 4, 64, 30, (36, 72), ("#4a5878", "#232c40", "#121824"), ((170, 80), (452, 60), (330, 40)), flash)
    far = Art()
    peaks(far, 6, [(50, 150, 70), (160, 196, 60), (268, 128, 84), (388, 184, 66), (498, 142, 78), (600, 190, 60)],
          ("#8fa2c8", "#5c6c8c", "#3a465e", "#2a3448", "#1e2636"), -1, 310, haze=("#42526a", 264, 0.6), rough=1.5)
    mid = Art()
    peaks(mid, 12, [(100, 220, 60), (236, 250, 54), (360, 206, 70), (486, 244, 56), (590, 216, 62)],
          ("#7f92b8", "#34425c", "#1c2434", "#141a28", "#0e121c"), -1, 350, rough=1.6)
    near = Art()
    land(near, profile(20, 358, 86, 0.95, (2, 3, 5, 8, 13)), "#0a0e18", None, None, seed=20, rim="#2c364a")
    return dict(
        title="Crista da Tempestade", family="Thunder Ridge",
        idea="O troço da perseguição: nuvens negras que acendem por dentro, relâmpagos com ramos, picos em bico com a aresta iluminada e chuva.",
        ground="Colunas de basalto molhado, azul-escuro, com erva rala.",
        sky=heaven, layers=[(clouds, 0.02, {"autoscroll": -6}), (far, 0.05), (mid, 0.16), (near, 0.44)],
        terrain=terrain("#303850", "#4c7c7e", "#2c2c38", pattern="basalt", band="none",
                        stones=triples("#303850", "#3a445e", "#283044", "#34486a"), gap="#141a28", wobble=0.7, radius=4.5),
        ambient="#a8b6d8", particles="rain", particle_color="#c8d8f0", decor_tint="#9ab0c8", decor_density=0.3, ceiling_density=0.08,
        water_top="#6a8ab080", water_deep="#1a2440c4", water_foam="#d8e8fff2", spring_colors=["pink", "lilac"])


@theme
def snow_peak() -> dict:
    heaven = sky([(0, "#080d2a"), (100, "#0e2450"), (190, "#1a4476"), (260, "#2c6a92"), (320, "#5a9cb0")], smooth=2)
    stars(heaven, 5, 130, 180)
    aurora(heaven, 2, ("#e0fff2", "#4fe6a8", "#7f74e6"), 26, 74, 3)
    far = Art()
    peaks(far, 6, [(84, 150, 110), (236, 104, 140), (404, 160, 110), (548, 120, 130)],
          ("#8fb4e0", "#6088bc", "#44689c", "#345486", "#284474"), 1, 300, snow=("#f2fbff", "#a9c8ee", 60), haze=("#4c8ca4", 250, 0.55), fan=6.0)
    mid = Art()
    mid_line = profile(11, 290, 70, 0.55)
    land(mid, mid_line, "#27426e", "#365a8c", "#1d3358", depth=0.5, snow=("#dcefff", "#8fb4e0", 14), seed=11)
    for x, h in scatter(23, 14, 30, 60):
        pine(mid, x, mid_line[x] + 4, int(h), x, "#1f3a5e", "#172c4a", None, "#e6f4ff")
    near = Art()
    near_line = profile(19, 338, 26)
    for x, h in scatter(37, 5, 110, 190):
        pine(near, x, near_line[x] + 6, int(h), x + 9, "#0f2038", "#0a1628", None, "#cfe4f8")
    land(near, near_line, "#e4f1ff", "#ffffff", "#a9c8ea", depth=0.7, seed=19)
    return dict(
        title="Cume de Bóreas", family="Thunder Ridge",
        idea="O alto da montanha à noite: picos nevados em facetas, pinheiros carregados e cortinas de aurora verdes e violeta.",
        ground="Gelo de glaciar em camadas azuis com reflexos, capa grossa de neve e pingentes nos tetos.",
        sky=heaven, layers=[(far, 0.04), (mid, 0.14), (near, 0.4)],
        terrain=terrain("#4c6c9c", "#eef6ff", "#5a6a8c", moss="#bfe0ff", accent="#eaf8ff", pattern="strata", pattern_args={"wave": 1.5},
                        stones=triples("#5a84c0", "#6c98d0", "#4a72ac", "#8ab4e4", light=0.3, dark=-0.18), gap="#34589a", edge="#1c2c58",
                        extras=["sheen"], cover="snow", band="none", hang="ice", hang_body="#bfe4ff", hang_tip="#ffffff",
                        grass_l="#ffffff", grass_d="#a9c8ee", shadow="#3a5a94", rim="#bfe0ff", tufts=False, side_moss=False),
        ambient="#c4dcff", particles="snow", particle_color="#ffffff", decor_density=0.0, ceiling_density=0.0, platform_tint="#c8dcf4",
        water_top="#a8e0ff80", water_deep="#2a5a9ac0", water_foam="#fffffff2", spring_colors=["pink", "lilac"])


@theme
def cloud_sea() -> dict:
    heaven = sky([(0, "#100c2e"), (80, "#1e1850"), (160, "#382878"), (230, "#62489a"), (290, "#9474bc"), (330, "#b89ad4")], smooth=2)
    stars(heaven, 13, 150, 210)
    disc(heaven, 440, 112, 62, "#f8f2e0", "#c8b8f8", 1.9, 0.5, craters=True, rim="#fffdf0")
    stratus(heaven, 7, 5, 84, 150, ("#d8ccf8", "#8c78c8"), (70, 190))
    towers = Art()
    cumulus(towers, 21, 3, 214, 250, (130, 240), ("#f4eeff", "#cfc2f6", "#a290dc", "#7862b8"), (0.45, -0.7), 0.62, (60, 262, 604))
    far = Art()
    temple(far, 150, 244, 86, 60, 5, ("#8e84c8", "#d4ccf8", "#665ca6"))
    for x, h in ((232, 46), (250, 30)):
        column(far, x, 246, h, 7, ("#8e84c8", "#d4ccf8", "#665ca6"), 1, x == 250, x)
    cloud_bank(far, 3, 252, 22, (18, 40), ("#f0eaff", "#bcacee", "#8e7ad0", "#6a56a8"), 1, True, 3, "#4a3c86")
    mid = Art()
    for x, h, broken in ((80, 120, False), (118, 70, True), (520, 130, False), (566, 100, False), (604, 60, True)):
        column(mid, x, 300, h, 13, ("#7468b8", "#c4b8f4", "#4c4290"), 1, broken, x)
    cloud_bank(mid, 9, 292, 26, (26, 56), ("#d4c8f8", "#9484d4", "#6250a4", "#40327a"), 1, True, 3, "#2a2260")
    near = Art()
    cloud_bank(near, 15, 336, 24, (34, 68), ("#a898e0", "#6050a2", "#34286c", "#1e1846"), 1, True, 2, "#120e30")
    return dict(
        title="Mar de Nuvens do Olimpo", family="Little Olympus",
        idea="Acima das nuvens, de noite: uma lua enorme atrás da ação, torres de cúmulos ao luar, colunas e um templo a sair de um mar de nuvens.",
        ground="Nuvem: anda-se sobre cachos brancos e lilases, de topo fofo e iluminado pela lua.",
        sky=heaven, layers=[(towers, 0.02, {"autoscroll": -1.5}), (far, 0.04), (mid, 0.14), (near, 0.4, {"autoscroll": -3})],
        terrain=terrain("#bdb0ec", "#f0eaff", "#bdb0ec", pattern="cloud", cover="cloud", band="none", cover_shadow=False,
                        stones=[("#b8aaea", "#dcd2fa", "#9684d6"), ("#c4b8f0", "#e6defc", "#a090dc"), ("#ad9ee4", "#d2c6f6", "#8a78cc")],
                        grass_l="#ffffff", grass_d="#d2c6f6", moss="#e6defc", edge="#6c58b4", rim="#f6f2ff", shadow="#8672c8",
                        wobble=1.7, radius=7.0, tufts=False, side_moss=False, hang="wisps", hang_body="#dcd2fa", hang_tip="#b8aaea"),
        depth_color="#4a3a9a", depth_strength=0.75,
        ambient="#d6d0ff", particles="motes", particle_color="#fff0c0", decor_density=0.0, ceiling_density=0.0, platform_tint="#d8d0ff",
        water_top="#b0a0f080", water_deep="#3a2a80c0", water_foam="#f4f0fff2", spring_colors=["pink", "aqua"])


@theme
def zeus_palace() -> dict:
    import gen_bg_palace
    art = gen_bg_palace.build()
    return dict(
        title="Thunder Court", family="Little Olympus",
        idea="O salão do trono de Zeus, abandonado desde que ele sumiu (só ficou o cão a tomar conta): colunas colossais com hera e teias, e a tempestade a rebentar lá fora; o trono gigante e, no assento, a almofada pequenina do cão.",
        ground="O mármore liso do portão, com a sombra da tempestade por cima (arroxeado).",
        sky=art["sky"], layers=art["layers"],
        terrain=terrain("#a092b8", "#d6cae2", "#7e7098", pattern="marble", band="frieze", frieze="#b8a070",
                        stones=triples("#a092b8", "#a99cc0", "#9486ae", light=0.3, dark=-0.22), gap="#4c4068", edge="#2a2240",
                        rim="#e2d8ee", shadow="#5c4e7a", grass_l="#f0eaf8", grass_d="#8c7eae", moss="#c8bce0",
                        wobble=0.0, radius=2.5, tufts=False, side_moss=False, hang=False, corner_tuft=False, blades=False),
        ambient="#948ac2", particles="drizzle", particle_color="#b8c8f4", decor_density=0.0, ceiling_density=0.0,
        ambience="storm_loop", music="", platform_tint="#b8b0e0", spring_colors=["aqua", "lilac"])


@theme
def olympus_dawn() -> dict:
    import gen_bg_olympus
    art = gen_bg_olympus.build()
    return dict(
        title="Amanhecer no Olimpo", family="Little Olympus",
        idea="Muito acima das nuvens, ao nascer do sol: torres de cúmulos de várias cores, ilhas de rocha a flutuar com cascatas, templos ao longe e ruínas de mármore com hera.",
        ground="Pedra clara e terra rosada com relva verde e florzinhas (o chão da primeira versão, com menos pedra).",
        sky=art["sky"], layers=art["layers"], platform=art["platform"], decor=art["decor"], fore=art["fore"],
        terrain=terrain("#e2d8c6", "#7cc86a", "#c4ac8c", moss="#5aa860", accent="#f0c860",
                        earth="#c9a694", earth_l="#dcbeaa", earth_d="#b48e86", earth_chance=0.5,
                        flowers=["#ffb4cc", "#fff6e8", "#ffe391"], flower_chance=0.2),
        ambient="#fff6ec", particles="petals", particle_color="#fff0f4", decor_density=0.85, ceiling_density=0.5, music="extra_scene",
        water_top="#ffd8c880", water_deep="#c07a90b0", water_foam="#fffffff2", spring_colors=["lilac", "aqua"])


@theme
def thunder_court() -> dict:
    heaven = sky([(0, "#0a0c22"), (90, "#161a44"), (180, "#282864"), (250, "#403884"), (300, "#6452a0")], smooth=2)
    stars(heaven, 17, 80, 140)
    clouds = Art()
    spark = ("#ffffff", "#dcd2ff", "#9a8cf0")
    lightning(clouds, 330, 40, 304, 240, 5, spark, 4, 22)
    lightning(clouds, 118, 50, 150, 176, 9, spark, 2, 14)
    lightning(clouds, 548, 46, 506, 196, 14, spark, 3, 14)
    storm_ceiling(clouds, 6, 48, 28, (34, 72), ("#5a56a0", "#2a2860", "#16143c"), ((330, 90), (118, 56), (548, 60)),
                  ("#e0daff", "#a29cdc", "#625ea8", "#30306a"))
    far = Art()
    stone = ("#55528e", "#9a96d4", "#38366c")
    temple(far, 320, 252, 230, 136, 8, stone)
    statue_dog(far, 110, 252, 22, stone)
    statue_dog(far, 536, 252, 22, stone)
    light_spill(far, [(330, 110, 150, "#d8d0ff"), (118, 200, 70, "#c8c0ff"), (540, 200, 70, "#c8c0ff")], 0.6)
    for x in (176, 464):
        far.rect(x - 4, 240, x + 4, 242, "#38366c")
        far.rect(x - 1, 242, x + 1, 252, "#38366c")
        far.glow(x, 232, 22, "#c8c0ff", 0.5, 1.3)
        far.poly([(x - 3, 240), (x, 226), (x + 3, 240)], "#f4f0ff")
    water = Art()
    lake(water, stack(heaven, clouds, far), 252, "#4a4690", "#141236", 0.66, "#d8ccff", 4)
    near = Art()
    column(near, 52, 372, 384, 34, ("#16143a", "#34326e", "#0c0a24"))
    column(near, 586, 372, 384, 34, ("#16143a", "#34326e", "#0c0a24"))
    return dict(
        title="Terraço do Trovão", family="Little Olympus",
        idea="A arena do Bolt: um terraço de mármore escuro com um espelho de água; o templo e as estátuas de cães acendem com os relâmpagos que rasgam as nuvens.",
        ground="Mármore azul-escuro em silhares, com uma lâmina de água rasa por cima e uma cornija de dentículos dourados.",
        sky=heaven, layers=[(clouds, 0.02, {"autoscroll": -5}), (far, 0.08), (water, 0.08), (near, 0.5)],
        terrain=terrain("#3c4070", "#8a98e8", "#2c2c58", pattern="marble", cover="water", band="frieze", frieze="#d8c88c",
                        stones=triples("#3c4070", "#454a7e", "#353864", light=0.3, dark=-0.22), gap="#1e1e46", edge="#10102a",
                        rim="#9aa0dc", shadow="#22224e", grass_l="#f0f4ff", grass_d="#5a64b8", moss="#b4c0f8",
                        wobble=0.0, radius=2.5, tufts=False, side_moss=False, hang=False, corner_tuft=False),
        ambient="#c8ccff", particles="motes", particle_color="#e6dcff", decor_density=0.0, ceiling_density=0.0, platform_tint="#b8b8f0",
        water_top="#9a90e880", water_deep="#1c1850c4", water_foam="#f0e8fff2", spring_colors=["aqua", "green"])


@theme
def styx() -> dict:
    heaven = sky([(0, "#04090b"), (110, "#09181a"), (220, "#112e30"), (300, "#1b4842"), (340, "#27604c")], smooth=2)
    far = Art()
    peaks(far, 6, [(70, 150, 60), (190, 110, 70), (330, 164, 56), (450, 96, 80), (580, 140, 64)],
          ("#2c7060", "#1c4a44", "#143834", "#0f2c2a", "#0b2020"), 1, 290, haze=("#27604c", 226, 0.6), rough=1.5)
    cave(far, 4, ("#102c2c", "#2c7060", "#0b2020"), (36, 28), None, (10, 0), 50)
    river = Art()
    lake(river, stack(heaven, far), 266, "#2a8a6a", "#06201c", 0.5, "#8fffd0", 6)
    ferry = Art()
    boat(ferry, 380, 288, "#03100e", "#b8ffe0")
    mid = Art()
    mid_line = profile(13, 322, 30, 0.4)
    for x, h in scatter(35, 7, 22, 44):
        dead_tree(mid, x, mid_line[x] + 2, h, (x % 7 - 3) * 0.05, x, "#061412", 3)
    for x in (70, 300, 520):
        mid.glow(x, mid_line[x] - 14, 30, "#7fffd0", 0.45, 1.3)
        mid.rect(x - 2, mid_line[x] - 8, x + 2, mid_line[x], "#0c2420")
        mid.poly([(x - 3, mid_line[x] - 8), (x, mid_line[x] - 20), (x + 3, mid_line[x] - 8)], "#c8fff0")
    land(mid, mid_line, "#081a18", None, None, seed=13, rim="#1c4a44")
    veil = Art()
    mist(veil, 5, 256, 318, 7, "#3fb890", (140, 320), (3, 8))
    near = Art()
    cave(near, 21, ("#030908", "#0c2420", "#010403"), (10, 18), (352, 14), (4, 4), 70)
    return dict(
        title="Margens do Estige", family="Submundo",
        idea="O rio dos mortos: água verde que brilha, a barca de Caronte ao longe, agulhas de rocha, braseiros de chama fria e almas a subir.",
        ground="Terra escura com ossos e caveiras, crosta de cinza por cima.",
        sky=heaven, layers=[(far, 0.04), (river, 0.04), (ferry, 0.07), (mid, 0.2), (veil, 0.3, {"autoscroll": -4}), (near, 0.46)],
        terrain=terrain("#213636", "#6c9c8c", "#1c2626", moss="#3a6a5c", accent="#dcecd8", extras=["bones"], cover="thin",
                        grass_l="#a8d4c0", grass_d="#3a5c54", blade="#8fffd0"),
        ambient="#a8dcc8", particles="embers", particle_color="#8fffd0", decor_tint="#8ab8a8", decor_density=0.3,
        water_top="#4fe0a08c", water_deep="#06302ac8", water_foam="#d0fff0f2", spring_colors=["lilac", "pink"])


FIRE = ("#ffe890", "#ff8a20", "#a02c10")


@theme
def tartarus() -> dict:
    heaven = sky([(0, "#0d0404"), (110, "#220908"), (200, "#4a1408"), (270, "#8c300e"), (320, "#c85a18")], smooth=2)
    heaven.glow(320, 330, 330, "#ff8a20", 0.2, 1.2, 0.5)
    far = Art()
    chains(far, 4, 9, "#1c0806", (50, 190))
    peaks(far, 5, [(56, 130, 50), (166, 70, 62), (292, 150, 50), (418, 50, 74), (556, 116, 60)],
          ("#b0481c", "#7a2c14", "#501a10", "#38100c", "#260a08"), 1, 320, haze=("#c8521a", 228, 0.85), rough=1.7, fan=4.0)
    works = Art()
    forge(works, 118, 302, 96, 74, ("#1c0806", "#7a2c14"), FIRE)
    forge(works, 476, 304, 126, 98, ("#1c0806", "#7a2c14"), FIRE)
    lavafall(works, 300, 150, 302, 7, FIRE, 3)
    lavafall(works, 616, 190, 302, 5, FIRE, 9)
    pit = Art()
    plates(pit, 300, ("#ffe890", "#ff8a20", "#3a100a", "#7a2410"), 3)
    mid = Art()
    land(mid, profile(11, 354, 104, 0.95), "#200a08", "#c84e16", "#140605", depth=0.12, seed=11, rim="#e8742a")
    near = Art()
    cave(near, 23, ("#0c0403", "#3c1410", "#050201"), (12, 20), (352, 16), (5, 4), 80)
    chains(near, 9, 5, "#050201", (70, 170))
    return dict(
        title="Forjas do Tártaro", family="Submundo",
        idea="O fundo do submundo: agulhas de basalto, fornalhas de arco aceso, quedas de lava, um lago de lava com placas de crosta e correntes penduradas.",
        ground="Colunas de basalto negro com fendas de lava acesa, crosta de cinza com brasas e pingos de lava nos tetos.",
        sky=heaven, layers=[(far, 0.05), (works, 0.07), (pit, 0.08), (mid, 0.2), (near, 0.46)],
        terrain=terrain("#33201f", "#3a2420", "#3c1814", pattern="basalt", glow=FIRE, band="none", cover="thin",
                        stones=triples("#33201f", "#3c2624", "#2a1818", "#44221c", light=0.3), gap="#120706", edge="#0a0303",
                        rim="#7a3a24", shadow="#160808", grass_l="#6a3a2c", grass_d="#1c0c0a", moss="#4a2a22", blade="#ff9a3a",
                        hang="drips", hang_body="#ff8a20", hang_tip="#ffe890", tufts=False, side_moss=False, wobble=0.7, radius=4.5),
        ambient="#ffc8a8", particles="embers", particle_color="#ff9a3a", decor_density=0.0, ceiling_density=0.0,
        water_top="#ffb04099", water_deep="#a02c08d0", water_foam="#fff0a0f2", spring_colors=["aqua", "lilac"])


@theme
def elysium() -> dict:
    heaven = sky([(0, "#8cc2f0"), (90, "#bcdef8"), (170, "#f2e4f0"), (230, "#fff0c8"), (270, "#fff8e0")], smooth=2)
    disc(heaven, 320, 150, 46, "#fffdf0", "#fff4c0", 2.6, 0.5)
    clouds = Art()
    cumulus(clouds, 9, 4, 130, 214, (100, 210), ("#ffffff", "#fff8ec", "#fbe4d4", "#f0c4c4"), (0.0, -0.9), 0.58)
    range_ = Art()
    peaks(range_, 3, [(90, 170, 120), (250, 148, 140), (440, 176, 110), (580, 156, 120)],
          ("#f4f0fa", "#e2def0", "#d0cee6", "#c0c0dc", "#b4b4d2"), 1, 256, haze=("#f6f0e4", 208, 0.9))
    far = Art()
    far_line = profile(4, 244, 30)
    temple(far, 150, far_line[150] + 2, 70, 46, 5, ("#f4ecd8", "#ffffff", "#d0c4b0"))
    land(far, far_line, "#bfe6cc", "#d6f2d8", "#a8d8c0", depth=0.5, seed=4, haze=("#f2f4dc", 240, 0.5))
    mid = Art()
    mid_line = profile(10, 280, 36)
    for i, (x, h) in enumerate(scatter(21, 14, 30, 56)):
        if i % 3 == 0:
            cypress(mid, x, mid_line[x] + 3, int(h * 1.3), x, ("#3f8c6a", "#62b07c", "#2f745c"))
        else:
            round_tree(mid, x, mid_line[x] + 4, h, x, "#7a5a4a", ("#f4b0c8", "#ffd8e2", "#dc88ac"))
    land(mid, mid_line, "#8cd49c", "#b0e8a8", "#72c08c", depth=0.5, seed=10)
    near = Art()
    near_line = profile(18, 336, 22)
    land(near, near_line, "#3f9a64", "#62b870", "#2f8058", depth=0.5, seed=18)
    reeds(near, 7, 359, 90, ("#2f8058", "#3f9a64"), (10, 40), ("#ffffff", "#fff0a0", "#cfe4ff"))
    return dict(
        title="Campos Elísios", family="Além",
        idea="O descanso dos heróis: luz clara e dourada, cúmulos cor de pêssego, serra pálida, colinas suaves, ciprestes e árvores em flor.",
        ground="Muros de mármore antigo com terra dourada e um prado cheio de flores por cima.",
        sky=heaven, layers=[(clouds, 0.02, {"autoscroll": -1.5}), (range_, 0.03), (far, 0.05), (mid, 0.15), (near, 0.38)],
        terrain=terrain("#d8cfb8", "#6cd468", "#b48c5c", moss="#4fae5c", pattern="marble", radius=4.0, wobble=0.5,
                        stones=triples("#dcd2bc", "#e6dcc8", "#d0c4ac", light=0.14, dark=-0.14), gap="#a8987c", edge="#6c5c48",
                        flowers=["#ffffff", "#fff0a0", "#cfe4ff", "#ffc878"], flower_chance=0.7),
        depth_color="#5a4634", depth_strength=0.7,
        ambient="#fffff4", particles="petals", particle_color="#ffe0ec",
        water_top="#8fe4f080", water_deep="#3a8ac0b0", water_foam="#fffffff2", spring_colors=["lilac", "aqua"])


@theme
def poseidon_coast() -> dict:
    heaven = sky([(0, "#2478d0"), (80, "#4a9ce4"), (150, "#7cc0f0"), (200, "#b0dcf6"), (230, "#dcf2fa")], smooth=2)
    disc(heaven, 110, 60, 20, "#fffbe0", "#fff2b0", 3.2, 0.55)
    stratus(heaven, 8, 6, 100, 190, ("#ffffff", "#cfe6f6"), (50, 170))
    clouds = Art()
    cumulus(clouds, 12, 4, 216, 232, (130, 250), ("#ffffff", "#f4fafe", "#d6e8f6", "#a8c8e4"), (-0.5, -0.7), 0.62)
    birds(clouds, 4, 8, 70, 170, "#3a5c8c")
    ocean = Art()
    sea(ocean, 232, ("#4cc8d0", "#2a9ec0", "#166aa0"), "#e0fbff", 4, 110, "#fff8d0")
    islands(ocean, 6, 234, 4, ("#7fb4d0", "#a4d0e2"), (40, 110))
    for x, s in ((262, 7), (602, 5)):
        ocean.poly([(x, 240 - s * 2), (x + s, 240), (x - 1, 240)], "#ffffff")
        ocean.rect(x - s, 241, x + s + 1, 241, "#4a3a34")
    cape = Art()
    cliff = []
    for x in range(W):
        if 470 <= x <= 560:
            top = 150.0
        elif 330 < x < 470:
            top = 150 + 88 * ((470 - x) / 140) ** 1.7
        elif 560 < x < 612:
            top = 150 + 88 * ((x - 560) / 52) ** 0.7
        else:
            top = H + 8.0
        cliff.append(int(top + (3 * math.sin(x * 0.23) + 2 * math.sin(x * 0.71) if top < H else 0)))
    temple(cape, 500, cliff[500] + 3, 78, 54, 5, ("#f4eee0", "#ffffff", "#cdc2ac"), -1)
    for x, h in ((452, 30), (548, 36), (562, 26)):
        cypress(cape, x, cliff[x] + 2, h, x, ("#4f8a6a", "#72ae7c", "#3a7058"), -1)
    land(cape, cliff, "#c8b48c", "#e8d8b0", "#a08c68", depth=0.7, seed=7, light=-1)
    strata_lines(cape, ("#c8b48c", "#d8c8a0", "#a89470"), 7, 8)
    strata_lines(cape, ("#a08c68", "#ac9874", "#84704e"), 9, 8)
    near = Art()
    land(near, profile(15, 350, 46, 0.7), "#5c5040", "#84745c", "#40382c", depth=0.5, seed=15, light=-1)
    reeds(near, 3, 359, 50, ("#2c6a5c", "#3f8a70"), (10, 36))
    return dict(
        title="Costa de Poseidon", family="Além",
        idea="A beira-mar de dia: mar turquesa com o rasto do sol, ilhas e velas, cúmulos altos no horizonte e um cabo de calcário em camadas com um templo branco.",
        ground="Arenito em camadas com areia molhada e, por cima, areia clara com conchas.",
        sky=heaven, layers=[(clouds, 0.02, {"autoscroll": -1.5}), (ocean, 0.03), (cape, 0.06), (near, 0.4)],
        terrain=terrain("#c4a87c", "#f4e4b8", "#b0946a", moss="#6ab89a", root="#d8c090", pattern="strata", pattern_args={"wave": 2.0},
                        stones=triples("#c4a87c", "#d4b88c", "#b49868", "#dcc8a0", light=0.25, dark=-0.2), gap="#8a7250", edge="#5c4a34",
                        cover="thin", hang=False, grass_l="#fff8dc", grass_d="#d8c08c", blade="#ffffff", pebble="#fff4dc"),
        depth_color="#4a3a2c", depth_strength=0.7,
        ambient="#ffffff", particles="motes", particle_color="#ffffff", decor_tint="#f0f4d8", decor_density=0.2, ceiling_density=0.0,
        water_top="#5ce0e080", water_deep="#1a78b0b8", water_foam="#fffffff2", spring_colors=["pink", "lilac"])


@theme
def sunken_temple() -> dict:
    heaven = sky([(0, "#8ce8e4"), (50, "#4ec0cc"), (130, "#2488ac"), (220, "#145080"), (310, "#0b2c56")], smooth=2)
    light = Art()
    rays(light, 6, 10, "#c8fff8", 30, -90, (16, 60))
    far = Art()
    far_line = profile(4, 304, 40)
    for x, h, broken in ((60, 120, False), (96, 60, True), (220, 150, False), (256, 150, False), (292, 80, True), (470, 110, False), (580, 70, True)):
        column(far, x, far_line[x] + 3, h, 11, ("#226e98", "#3690b8", "#18587e"), 1, broken, x)
    land(far, far_line, "#1c6490", "#2a80a8", "#14507a", depth=0.5, seed=4, haze=("#145080", 296, 0.5))
    mid = Art()
    mid_line = profile(11, 328, 30)
    temple(mid, 400, mid_line[400] + 3, 150, 110, 6, ("#164c74", "#2c88b0", "#0e3458"), 1, 0.45, 3)
    kelp(mid, 5, 8, ("#0f5a5c", "#1f8a70"), (60, 160), 340)
    land(mid, mid_line, "#12456c", "#1f6890", "#0c3050", depth=0.5, seed=11)
    near = Art()
    kelp(near, 9, 9, ("#062238", "#0c3a4c"), (120, 260), 360)
    land(near, profile(19, 352, 24, 0.6), "#062238", None, None, seed=19, rim="#0c3a4c")
    return dict(
        title="Templo Submerso", family="Além",
        idea="Uma zona debaixo de água: luz que desce da superfície, colunas e um templo em ruínas, algas altas e bolhas.",
        ground="Fiadas de tijolo gasto com manchas de limo, tijolos em falta e algas por cima.",
        sky=heaven, layers=[(light, 0.1), (far, 0.06), (mid, 0.18), (near, 0.44)],
        terrain=terrain("#2c5c7c", "#40caa2", "#20485a", moss="#2a9a8a", accent="#c8fff8", pattern="bricks", band="none",
                        stones=triples("#2c5c7c", "#346888", "#265070"), wobble=0.5, radius=4.0, flowers=["#ffd0a0", "#fff0c0"], flower_chance=0.2),
        ambient="#b4e8ff", particles="bubbles", particle_color="#d8fbff", decor_tint="#a0e0e8",
        water_top="#8ff0f060", water_deep="#2a88b090", water_foam="#fffffff2", spring_colors=["pink", "lilac"])


def preview(zones: list[str], out: str) -> None:
    cols = 2
    sheet = Image.new("RGB", (W * cols, H * ((len(zones) + cols - 1) // cols)))
    base = os.path.join(ASSETS, "backgrounds")
    for k, zone in enumerate(zones):
        data = json.load(open(os.path.join(ASSETS, "themes", zone + ".json"), encoding="utf-8"))
        img = Image.open(os.path.join(base, data["sky"])).convert("RGBA")
        for layer in data["layers"]:
            art = Image.open(os.path.join(base, layer["texture"])).convert("RGBA")
            canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            canvas.alpha_composite(art.crop((0, 0, min(W, art.width), min(H, art.height))), (0, int(layer.get("y", 0))))
            img.alpha_composite(canvas)
        ImageDraw.Draw(img).text((6, 4), "%s  (%s)" % (data["title"], zone), fill=(255, 255, 255, 255))
        sheet.paste(img.convert("RGB"), ((k % cols) * W, (k // cols) * H))
    sheet.save(out)


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    fast = "--fast" in sys.argv
    zones = args or list(THEMES)
    for zone in zones:
        build(zone, fast)
        print("zona %-16s ok" % zone)
    if "--sheets" in sys.argv:
        os.makedirs(os.path.join(DOCS_PREVIEW, "zonas"), exist_ok=True)
        for i in range(0, len(zones), 4):
            preview(zones[i:i + 4], os.path.join(DOCS_PREVIEW, "zonas", "_rascunho_%d.png" % (i // 4 + 1)))


if __name__ == "__main__":
    main()
