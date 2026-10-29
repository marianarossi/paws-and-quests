class_name ZoneTheme
extends RefCounted

const BG := "res://assets/backgrounds/"
const TILES := "res://assets/tiles/"
const THEMES := "res://assets/themes/"

static var _cache: Dictionary[StringName, ZoneTheme] = {}

var id: StringName
var terrain_atlas := ""
var platform_atlas := ""
var water_platform_atlas := ""
var sky := ""
var layers: Array[Dictionary] = []
var ambient := Color.WHITE
var decor_json := ""
var decor_density := 0.0
var ceiling_density := 0.0
var particles := ""
var particle_color := Color(0.77, 1.0, 0.6)
var water_top := Color(0.36, 0.84, 0.82, 0.5)
var water_deep := Color(0.10, 0.28, 0.48, 0.74)
var water_foam := Color(0.86, 1.0, 0.96, 0.95)
var decor_tint := Color.WHITE
var platform_tint := Color.WHITE
var depth_color := Color(0.05, 0.04, 0.11)
var depth_strength := 1.0
var title := ""
var fore := ""
var critters := ""
var ambience := ""
var checkpoint := "res://assets/sprites/props/campfire.json"
var music := "campfire_trail"
var spring_colors: Array[String] = ["lilac", "pink"]


static func clear_cache() -> void:
	_cache.clear()


static func of(zone: StringName) -> ZoneTheme:
	if not _cache.has(zone):
		match zone:
			&"ember":
				_cache[zone] = _ember()
			&"forest":
				_cache[zone] = _forest()
			_:
				var path := THEMES + String(zone) + ".json"
				_cache[zone] = _from_file(path) if ResourceLoader.exists(path) else _forest()
	return _cache[zone]


static func _forest() -> ZoneTheme:
	var theme := ZoneTheme.new()
	theme.id = &"forest"
	theme.terrain_atlas = TILES + "forest_terrain.png"
	theme.platform_atlas = TILES + "forest_platform.png"
	theme.sky = BG + "forest_sky.png"
	theme.layers = [
		{"texture": BG + "forest_far.png", "scale": Vector2(0.05, 0.0)},
		{"texture": BG + "forest_mid2.png", "scale": Vector2(0.12, 0.0)},
		{"texture": BG + "forest_rays.png", "scale": Vector2(0.16, 0.0)},
		{"texture": BG + "forest_mid.png", "scale": Vector2(0.24, 0.0)},
		{"texture": BG + "forest_fog.png", "scale": Vector2(0.3, 0.0), "y": 150.0, "autoscroll": Vector2(-5, 0)},
		{"texture": BG + "forest_near.png", "scale": Vector2(0.42, 0.0)},
		{"texture": BG + "forest_fog.png", "scale": Vector2(0.55, 0.0), "y": 205.0, "autoscroll": Vector2(-9, 0)},
	]
	theme.ambient = Color(0.74, 0.82, 0.96)
	theme.decor_json = "res://assets/sprites/decor/forest_decor.json"
	theme.decor_density = 0.7
	theme.ceiling_density = 0.3
	theme.particles = "fireflies"
	theme.title = "Whisperwood"
	return theme


static func _ember() -> ZoneTheme:
	var theme := _forest()
	theme.id = &"ember"
	theme.terrain_atlas = TILES + "ember_terrain.png"
	theme.sky = BG + "ember_sky.png"
	theme.layers = [
		{"texture": BG + "ember_clouds.png", "scale": Vector2(0.02, 0.0), "autoscroll": Vector2(-2, 0)},
		{"texture": BG + "ember_hills.png", "scale": Vector2(0.05, 0.02)},
		{"texture": BG + "ember_pines_far.png", "scale": Vector2(0.1, 0.045)},
		{"texture": BG + "ember_pines_mid2.png", "scale": Vector2(0.17, 0.08)},
		{"texture": BG + "ember_pines_mid.png", "scale": Vector2(0.27, 0.13)},
		{"texture": BG + "ember_pines_near.png", "scale": Vector2(0.42, 0.2)},
	]
	theme.decor_json = "res://assets/sprites/decor/ember_decor.json"
	theme.decor_density = 0.9
	theme.ceiling_density = 0.25
	theme.ambient = Color(0.98, 0.86, 0.84)
	theme.spring_colors = ["aqua", "lilac"]
	theme.particles = "fireflies"
	theme.particle_color = Color(1.0, 0.86, 0.5)
	theme.water_top = Color(0.52, 0.74, 0.86, 0.5)
	theme.water_deep = Color(0.16, 0.22, 0.5, 0.78)
	theme.water_foam = Color(1.0, 0.93, 0.78, 0.95)
	theme.title = "Ember Camp"
	return theme


static func _from_file(path: String) -> ZoneTheme:
	var data: Dictionary = (load(path) as JSON).data
	var theme := _forest()
	theme.id = StringName(String(data["id"]))
	theme.title = String(data.get("title", data["id"]))
	theme.terrain_atlas = TILES + String(data["terrain"])
	theme.sky = BG + String(data["sky"])
	theme.layers = []
	for layer: Dictionary in data["layers"]:
		var entry := {"texture": BG + String(layer["texture"]), "scale": Vector2(float(layer["scale"]), float(layer.get("scale_y", 0.0)))}
		if layer.has("y"):
			entry["y"] = float(layer["y"])
		if layer.has("autoscroll"):
			entry["autoscroll"] = Vector2(float(layer["autoscroll"]), 0.0)
		if layer.get("shimmer", false):
			entry["shimmer"] = true
		if layer.has("flap"):
			entry["flap"] = float(layer["flap"])
			entry["frames"] = int(layer.get("frames", 2))
		if layer.has("fill"):
			entry["fill"] = Color(String(layer["fill"]))
		if layer.get("flash", false):
			entry["flash"] = true
		if layer.has("bolts"):
			entry["bolts"] = String(layer["bolts"])
		theme.layers.append(entry)
	theme.ambient = Color(String(data.get("ambient", "#ffffff")))
	theme.decor_tint = Color(String(data.get("decor_tint", "#ffffff")))
	theme.platform_tint = Color(String(data.get("platform_tint", "#ffffff")))
	if data.has("depth_color"):
		theme.depth_color = Color(String(data["depth_color"]))
	theme.depth_strength = float(data.get("depth_strength", 1.0))
	theme.decor_density = float(data.get("decor_density", theme.decor_density))
	theme.ceiling_density = float(data.get("ceiling_density", theme.ceiling_density))
	theme.particles = String(data.get("particles", ""))
	theme.critters = String(data.get("critters", ""))
	if data.has("fore"):
		theme.fore = BG + String(data["fore"])
	theme.ambience = String(data.get("ambience", ""))
	theme.music = String(data.get("music", theme.music))
	if data.has("checkpoint"):
		theme.checkpoint = "res://assets/sprites/props/" + String(data["checkpoint"])
	if data.has("platform"):
		theme.platform_atlas = TILES + String(data["platform"])
	if data.has("water_platform"):
		theme.water_platform_atlas = TILES + String(data["water_platform"])
	if data.has("decor"):
		theme.decor_json = "res://assets/sprites/decor/" + String(data["decor"])
	theme.particle_color = Color(String(data.get("particle_color", "#ffffff")))
	theme.water_top = Color(String(data.get("water_top", "#5cd6d180")))
	theme.water_deep = Color(String(data.get("water_deep", "#1a477abd")))
	theme.water_foam = Color(String(data.get("water_foam", "#dbfff5f2")))
	var springs: Array[String] = []
	for color: String in data.get("spring_colors", ["lilac", "pink"]):
		springs.append(color)
	theme.spring_colors = springs
	return theme
