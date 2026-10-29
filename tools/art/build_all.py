import gen_backgrounds
import gen_bestiary
import gen_bg_ember
import gen_combat
import gen_font
import gen_hazards
import gen_hero
import gen_hero_look
import gen_hero_preview
import gen_preview
import gen_props
import gen_terrain
import gen_zones

if __name__ == "__main__":
    gen_terrain.main()
    gen_hero.main()
    gen_hero_look.main()
    gen_props.main()
    gen_hazards.main()
    gen_combat.main()
    gen_bestiary.main()
    gen_font.main()
    gen_backgrounds.main()
    gen_bg_ember.main()
    for zone in gen_zones.THEMES:
        gen_zones.build(zone)
    gen_preview.main()
    gen_hero_preview.main()
