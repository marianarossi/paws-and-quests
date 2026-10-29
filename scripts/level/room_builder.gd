class_name RoomBuilder

const TILE := Room.TILE
const MAX_GLOW_LIGHTS := 28
const SUBMERGED_DEPTH := 48.0
const DECOR_OVERHANG := 2.0
const FROG_CHANCE := 0.07
const MAX_FROGS := 14
const DRIFT := preload("res://shaders/drift.gdshader")
const DEPTH_ALPHA: Array[float] = [0.0, 0.0, 0.3, 0.52, 0.68]


const SPIKE_SINK := {&"olympus_dawn": 3.0}


static func build(data: RoomData, theme: ZoneTheme, with_decor := true) -> Room:
	var room := Room.new()
	room.name = "Room_" + data.id
	room.data = data
	room.position = Vector2(data.world_cell) * TILE
	room.bounds = Rect2(room.position, Vector2(data.width, data.height) * TILE)

	var collision := TileMapLayer.new()
	collision.name = "Collision"
	collision.tile_set = TerrainTiles.collision_set()
	collision.visible = false
	var platforms := _art_layer("Platforms", TerrainTiles.art_set(theme.platform_atlas, 3, 1))
	platforms.position.y = -TerrainTiles.PLATFORM_ART_TOP
	var water_atlas := theme.water_platform_atlas if theme.water_platform_atlas != "" else theme.platform_atlas
	var floating := _art_layer("FloatingPlatforms", TerrainTiles.art_set(water_atlas, 3, 1))
	floating.position.y = -TerrainTiles.PLATFORM_ART_TOP
	floating.z_index = 12
	var props := Node2D.new()
	props.name = "Props"

	for y in data.height:
		for x in data.width:
			var cell := Vector2i(x, y)
			var character := data.rows[y][x]
			var starts_run := data.raw_cell(x - 1, y) != character
			match character:
				".":
					pass
				"#":
					collision.set_cell(cell, 0, TerrainTiles.SOLID)
				"=":
					collision.set_cell(cell, 0, TerrainTiles.ONE_WAY)
					var part := 0 if data.cell(x - 1, y) != "=" else (2 if data.cell(x + 1, y) != "=" else 1)
					(floating if _wet(data, x, y) else platforms).set_cell(cell, 0, Vector2i(part, 0))
				"P":
					room.spawn_points.append(room.position + Room.cell_to_feet(cell))
				"C":
					props.add_child(Checkpoint.create(Room.cell_to_feet(cell), theme.checkpoint))
				"M":
					props.add_child(Spring.create(Room.cell_to_feet(cell), theme.spring_colors[(cell.x + cell.y) % theme.spring_colors.size()]))
				"*":
					props.add_child(DashCrystal.create(Vector2(cell) * TILE + Vector2(TILE, TILE) * 0.5))
				"^", "v", "<", ">":
					props.add_child(Spikes.create(character, Vector2(cell) * TILE + Vector2(TILE, TILE) * 0.5, SPIKE_SINK.get(data.zone, 0.0)))
				"~":
					if starts_run:
						props.add_child(CrumblePlatform.create(data.run_length(x, y), Vector2(cell) * TILE))
				_:
					if starts_run and data.defs.has(character):
						var entity := _build_entity(data.defs[character], data.run_length(x, y), Vector2(cell) * TILE, data.id, Vector2(data.width, data.height) * TILE)
						if entity:
							props.add_child(entity)
	room.spawn_points.sort_custom(func(a: Vector2, b: Vector2) -> bool: return a.x < b.x)
	if not room.spawn_points.is_empty():
		room.spawn_point = room.spawn_points[0]

	for x in data.width:
		if _wet(data, x, data.height - 1):
			collision.set_cell(Vector2i(x, data.height), 0, TerrainTiles.SOLID)
	room.add_child(collision)
	room.add_child(_build_terrain(data, theme))
	room.add_child(_build_depth_shade(data, theme))
	if with_decor and theme.decor_density > 0.0:
		room.add_child(_build_decor(data, theme))
	if with_decor and theme.critters == "frogs":
		room.add_child(_build_frogs(data))
	platforms.modulate = theme.platform_tint
	room.add_child(platforms)
	floating.modulate = theme.platform_tint
	room.add_child(floating)
	var water := _build_water(data, theme)
	if water:
		room.add_child(water)
	room.add_child(props)
	if theme.fore != "":
		room.add_child(_build_fore(data, theme))
	return room


static func _build_entity(def: Dictionary, tiles: int, top_left: Vector2, room_id: String, room_size := Vector2.ZERO) -> Node2D:
	var center := top_left + Vector2(TILE, TILE) * 0.5
	match def.get("type", ""):
		"mover":
			var travel := RoomData.to_vector(def.get("to", "0,0")) * TILE
			return MovingPlatform.create(tiles, top_left, travel, float(def.get("time", "2.0")))
		"emitter":
			return Emitter.create(def, center, room_id)
		"mine":
			return Mine.create(def, center, room_id)
		"beam":
			return Beam.create(def, center, room_id)
		"bat":
			return EmpusaBat.create(def, top_left + Vector2(TILE * 0.5, TILE), room_id)
		"bronte":
			return Bronte.create(def, top_left + Vector2(TILE * 0.5, TILE), room_id)
		"toad":
			return MiasmaToad.create(def, top_left + Vector2(TILE * 0.5, TILE), room_id)
		"crab":
			return Karkinos.create(def, top_left + Vector2(TILE * 0.5, TILE), room_id)
		"eye":
			return ArgesEye.create(def, center, room_id)
		"archer":
			return EroteArcher.create(def, center, room_id)
		"minotaur":
			return MinotaurCalf.create(def, top_left + Vector2(TILE * 0.5, TILE), room_id)
		"skeleton":
			return Spartoi.create(def, top_left + Vector2(TILE * 0.5, TILE), room_id)
		"acorn":
			return Balanos.create(def, top_left + Vector2(TILE * 0.5, TILE), room_id)
		"shade":
			return StyxShade.create(def, center, room_id)
		"harpy":
			return Harpy.create(def, center, room_id)
		"nimbus":
			return Nephele.create(def, center, room_id)
		"gust":
			return BoreasGust.create(def, center, room_id)
		"ruin":
			return Ruin.create(def, top_left)
		"fall":
			return FallBlock.create(tiles, top_left)
		"beat":
			return BeatCloud.create(def, tiles, top_left, room_id)
		"step":
			return CloudStep.create(def, tiles, top_left, room_id)
		"chase":
			return StormChase.create(def, room_id, room_size.y)
		"vista":
			return Vista.create(def, room_id)
		"glow":
			return SkyGlow.create(center, String(def.get("to", "")))
		"feather":
			return Feather.create(center, "%s:%d,%d" % [room_id, int(top_left.x / TILE), int(top_left.y / TILE)])
		"gate":
			return Gate.create(top_left + Vector2(TILE * 0.5, TILE), String(def.get("to", "")))
		"inner_door":
			return PalaceDoor.create(top_left)
		"storm":
			return Storm.create(def, room_id)
		"hunt":
			return StormHunt.create(def, room_id)
		"strike":
			return LightningStrike.create(def, top_left + Vector2(TILE * 0.5, TILE), room_id)
		"ledge":
			var ledge := StaticBody2D.new()
			ledge.position = top_left
			ledge.collision_layer = Combat.WORLD_LAYER
			ledge.collision_mask = 0
			var box := RectangleShape2D.new()
			box.size = Vector2(tiles * TILE, 4)
			var shape := CollisionShape2D.new()
			shape.shape = box
			shape.position = Vector2(tiles * TILE * 0.5, 2)
			shape.one_way_collision = true
			ledge.add_child(shape)
			return ledge
		"sprite":
			var art := Sprite2D.new()
			art.texture = load("res://assets/sprites/props/" + String(def.get("file", "")))
			art.centered = false
			var x := float(def.get("dx", "0")) + (0.0 if def.has("left") else TILE * 0.5 - art.texture.get_width() * 0.5)
			art.position = (top_left + Vector2(x, TILE - art.texture.get_height() + float(def.get("sink", "0")))).round()
			art.z_index = int(def.get("z", "-1"))
			if def.has("glow"):
				var glow := Sprite2D.new()
				glow.texture = load("res://assets/sprites/props/" + String(def["glow"]))
				glow.centered = false
				var frames := int(def.get("frames", "1"))
				glow.region_enabled = true
				glow.region_rect = Rect2(0, 0, glow.texture.get_width(), glow.texture.get_height() / frames)
				var flap := ShaderMaterial.new()
				flap.shader = preload("res://shaders/flap.gdshader")
				flap.set_shader_parameter(&"fps", float(def.get("fps", "8")))
				flap.set_shader_parameter(&"frames", float(frames))
				glow.material = flap
				art.add_child(glow)
			if def.has("light"):
				var light := Lights.point(Color(String(def["light"])), float(def.get("lr", "40")), float(def.get("le", "0.9")))
				light.position = Vector2(float(def.get("lx", str(art.texture.get_width() * 0.5))), float(def.get("ly", str(art.texture.get_height() * 0.5))))
				art.add_child(light)
			return art
		"hint":
			return Hint.create(top_left + Vector2(TILE * 0.5, TILE), String(def.get("text", "")))
		"diary":
			return Diary.create(top_left + Vector2(TILE * 0.5, TILE))
		"gift":
			return Gift.create(center, StringName(def.get("ability", "dash")))
		"dog":
			var dog := DogNpc.create(top_left + Vector2(TILE * 0.5, TILE), String(def.get("sheet", "dog")),
					StringName(def.get("anim", "idle")), -1 if def.has("left") else 1)
			dog.z_index = int(def.get("z", "1"))
			dog.camp = def.has("camp")
			return dog
		"fight":
			return ThroneFight.create(def, top_left + Vector2(TILE * 0.5, TILE), room_id)
		"ball":
			return FetchBall.create(top_left + Vector2(TILE * 0.5, TILE - FetchBall.RADIUS))
		"paved":
			return null
		"clear":
			return null
	push_warning("tipo de entidade desconhecido: %s" % def.get("type", "?"))
	return null


static func _art_layer(layer_name: String, tile_set: TileSet) -> TileMapLayer:
	var layer := TileMapLayer.new()
	layer.name = layer_name
	layer.tile_set = tile_set
	layer.scale = Vector2.ONE * TerrainTiles.ART_SCALE
	layer.collision_enabled = false
	return layer


static func _build_terrain(data: RoomData, theme: ZoneTheme) -> TileMapLayer:
	var terrain := _art_layer("Terrain", TerrainTiles.art_set(theme.terrain_atlas, TerrainTiles.TERRAIN_ATLAS_COLUMNS, TerrainTiles.TERRAIN_ATLAS_ROWS))
	terrain.position = Vector2(-TILE * 0.5, -TILE * 0.5)
	var clip := ShaderMaterial.new()
	clip.shader = preload("res://shaders/room_clip.gdshader")
	var origin := Vector2(data.world_cell) * TILE
	var end := origin + Vector2(data.width, data.height) * TILE
	clip.set_shader_parameter(&"rect", Vector4(origin.x, origin.y, end.x, end.y))
	terrain.material = clip
	for j in data.height + 1:
		for i in data.width + 1:
			var mask := 0
			for corner in 4:
				if data.is_solid(i - 1 + (corner & 1), j - 1 + (corner >> 1)):
					mask |= 1 << corner
			if mask != 0:
				var soil := 0
				if mask == 15:
					if not data.is_solid(i - 1, j - 2):
						soil |= TerrainTiles.SOIL_LEFT
					if not data.is_solid(i, j - 2):
						soil |= TerrainTiles.SOIL_RIGHT
				terrain.set_cell(Vector2i(i, j), 0, TerrainTiles.terrain_cell(mask, data.world_cell + Vector2i(i, j), soil))
	return terrain


static func _build_depth_shade(data: RoomData, theme: ZoneTheme) -> Sprite2D:
	var depth := data.solid_depth()
	var image := Image.create(data.width, data.height, false, Image.FORMAT_RGBA8)
	for y in data.height:
		for x in data.width:
			var d := mini(depth[y * data.width + x], DEPTH_ALPHA.size() - 1)
			image.set_pixel(x, y, Color(theme.depth_color, DEPTH_ALPHA[d] * theme.depth_strength))
	var shade := Sprite2D.new()
	shade.name = "DepthShade"
	shade.texture = ImageTexture.create_from_image(image)
	shade.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	shade.centered = false
	shade.scale = Vector2(TILE, TILE)
	return shade


static func _build_water(data: RoomData, theme: ZoneTheme) -> Node2D:
	var holder: Node2D = null
	var start := 0
	var spans := _water_spans(data, 0)
	for x in range(1, data.width + 1):
		var here := _water_spans(data, x) if x < data.width else PackedInt32Array()
		if here == spans:
			continue
		for i in range(0, spans.size(), 3):
			if holder == null:
				holder = Node2D.new()
				holder.name = "Water"
			var top_left := Vector2(start, spans[i]) * TILE
			var open_air := spans[i + 2] == 1
			holder.add_child(Water.create(top_left, Vector2(x - start, spans[i + 1] - spans[i] + 1) * TILE, open_air, theme,
					0.0 if open_air else SUBMERGED_DEPTH))
		start = x
		spans = here
	return holder


static func _water_spans(data: RoomData, x: int) -> PackedInt32Array:
	var spans := PackedInt32Array()
	var y := 0
	while y < data.height:
		if _wet(data, x, y):
			var first := y
			while y + 1 < data.height and _wet(data, x, y + 1):
				y += 1
			spans.append(first)
			spans.append(y)
			var above := data.raw_cell(x, first - 1)
			spans.append(0 if above == RoomData.SOLID or above in "^v<>" else 1)
		y += 1
	return spans


static func _build_fore(data: RoomData, theme: ZoneTheme) -> Sprite2D:
	var texture: Texture2D = load(theme.fore)
	var fore := Sprite2D.new()
	fore.name = "Fore"
	fore.texture = texture
	fore.centered = false
	fore.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
	fore.region_enabled = true
	var columns := data.width
	while columns > 0 and data.is_solid(columns - 1, data.height - 1):
		columns -= 1
	fore.region_rect = Rect2(0, 0, columns * TILE + (8 if columns < data.width else 0), texture.get_height())
	fore.position = Vector2(0, data.height * TILE - texture.get_height() + 6.0)
	fore.z_index = 20
	var drift := ShaderMaterial.new()
	drift.shader = DRIFT
	fore.material = drift
	return fore


static func _build_frogs(data: RoomData) -> Node2D:
	var holder := Node2D.new()
	holder.name = "Frogs"
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(data.id + "frogs")
	for y in range(1, data.height):
		for x in data.width:
			if holder.get_child_count() >= MAX_FROGS or not data.is_solid(x, y) or data.cell(x, y - 1) != ".":
				continue
			if rng.randf() >= FROG_CHANCE:
				continue
			var run := _flat_run(data, x, y)
			if run.y - run.x >= TILE * 2.0:
				holder.add_child(Frog.create(Vector2(x * TILE + TILE * 0.5, y * TILE), run.x + 6.0, run.y - 6.0, rng.randi()))
	return holder


static func _wet(data: RoomData, x: int, y: int) -> bool:
	var character := data.raw_cell(x, y)
	if character == RoomData.WATER or (character == "=" and data.raw_cell(x, y + 1) == RoomData.WATER):
		return true
	return _submerged_entity(data, x, y)


static func _submerged_entity(data: RoomData, x: int, y: int) -> bool:
	var character := data.raw_cell(x, y)
	if character == "" or character in ".#=^v<>":
		return false
	if data.raw_cell(x, y - 1) == RoomData.WATER:
		return true
	var left := x - 1
	while data.raw_cell(left, y) == character:
		left -= 1
	var right := x + 1
	while data.raw_cell(right, y) == character:
		right += 1
	return data.raw_cell(left, y) == RoomData.WATER or data.raw_cell(right, y) == RoomData.WATER


static func _build_decor(data: RoomData, theme: ZoneTheme) -> Node2D:
	var decor := Node2D.new()
	decor.name = "Decor"
	decor.modulate = theme.decor_tint
	var meta: Dictionary = (load(theme.decor_json) as JSON).data
	var texture: Texture2D = load(theme.decor_json.get_base_dir().path_join(meta["image"]))
	var floor_items: Array = []
	var ceiling_items: Array = []
	for item: Dictionary in meta["items"]:
		(ceiling_items if item.get("anchor", "floor") == "ceiling" else floor_items).append(item)
	var small_items: Array = floor_items.filter(func(entry: Dictionary) -> bool: return float(entry["rect"][2]) <= TILE + 6.0)
	var calm_items: Array = small_items.filter(func(entry: Dictionary) -> bool: return entry.get("motion", "none") != "none")
	var spread := 4 if theme.decor_density <= 1.0 else 7
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(data.id)
	var lights := 0
	var calm := {}
	var bare := {}
	for y in data.height:
		for x in data.width:
			var kind: String = data.defs.get(data.rows[y][x], {}).get("type", "")
			if kind == "clear" or kind == "diary":
				calm[x] = true
			elif kind == "paved" or kind == "gate":
				bare[x] = true
	for y in data.height:
		for x in data.width:
			if not data.is_solid(x, y):
				continue
			var on_floor := y > 0 and (data.cell(x, y - 1) == "." or data.defs.has(data.cell(x, y - 1)))
			var on_ceiling := y < data.height - 1 and data.cell(x, y + 1) == "."
			for n in (ceili(theme.decor_density) if on_floor and not bare.has(x) else 0):
				if rng.randf() >= theme.decor_density - n:
					continue
				var item := _pick(calm_items if calm.has(x) else floor_items, rng)
				var run := _flat_run(data, x, y)
				if _visible_width(item) > run.y - run.x + 2.0 * DECOR_OVERHANG:
					item = _pick(small_items, rng)
				var sprite := _decor_sprite(item, texture, rng, decor.get_child_count())
				var size := sprite.region_rect.size
				var half := _visible_width(item) * 0.5 - DECOR_OVERHANG
				var center := x * TILE + TILE * 0.5 + rng.randi_range(-spread, spread)
				center = clampf(center, minf(run.x + half, (run.x + run.y) * 0.5), maxf(run.y - half, (run.x + run.y) * 0.5))
				sprite.position = Vector2(center - size.x * 0.5, y * TILE - size.y + 1.0).round()
				decor.add_child(sprite)
				if item["glow"] != null and lights < MAX_GLOW_LIGHTS:
					var glow: Array = item["glow"]
					var light := Lights.point(Color(glow[0], glow[1], glow[2]), float(item["glow_radius"]), 0.8)
					light.position = Vector2(x * TILE + TILE * 0.5, y * TILE - size.y * 0.6)
					decor.add_child(light)
					lights += 1
			if on_ceiling and not ceiling_items.is_empty() and rng.randf() < theme.ceiling_density:
				var sprite := _decor_sprite(_pick(ceiling_items, rng), texture, rng, decor.get_child_count())
				sprite.position = Vector2(x * TILE + TILE * 0.5 - sprite.region_rect.size.x * 0.5 + rng.randi_range(-5, 5), (y + 1) * TILE - 3.0).round()
				decor.add_child(sprite)
	return decor


static func _flat_run(data: RoomData, x: int, y: int) -> Vector2:
	var left := x
	while x - left < 4 and left > 0 and data.is_solid(left - 1, y) and not data.is_solid(left - 1, y - 1):
		left -= 1
	var right := x
	while right - x < 4 and right < data.width - 1 and data.is_solid(right + 1, y) and not data.is_solid(right + 1, y - 1):
		right += 1
	return Vector2(left * TILE, (right + 1) * TILE)


static func _visible_width(item: Dictionary) -> float:
	return float(item["rect"][2]) - (0.0 if item.get("motion", "none") == "none" else 6.0)


static func _decor_sprite(item: Dictionary, texture: Texture2D, rng: RandomNumberGenerator, index := 0) -> Sprite2D:
	var rect: Array = item["rect"]
	var sprite := Sprite2D.new()
	sprite.texture = texture
	sprite.region_enabled = true
	sprite.region_rect = Rect2(rect[0], rect[1], rect[2], rect[3])
	sprite.region_filter_clip_enabled = true
	sprite.centered = false
	sprite.flip_h = rng.randf() < 0.5
	sprite.material = Sway.material(item.get("motion", "none"), item.get("anchor", "floor") == "ceiling", index * 5)
	if rng.randf() < float(item.get("front", 0.0)):
		sprite.z_index = 20
	return sprite


static func _pick(items: Array, rng: RandomNumberGenerator) -> Dictionary:
	var total := 0.0
	for item: Dictionary in items:
		total += float(item["weight"])
	var roll := rng.randf() * total
	var acc := 0.0
	for item: Dictionary in items:
		acc += float(item["weight"])
		if roll <= acc:
			return item
	return items[-1]
