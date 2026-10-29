class_name Background
extends Node2D

const SCREEN := Vector2(640, 360)
const ART_SCALE := 1.0

const CLIP := preload("res://shaders/zone_clip.gdshader")
const SHIMMER := preload("res://shaders/shimmer.gdshader")
const FLAP := preload("res://shaders/flap.gdshader")
const MAX_RECTS := 16
const GROUP := &"background"
const FILL_DEPTH := 720.0

var _layers: Array[Parallax2D] = []
var _sky: TextureRect
var _rooms: Array[Rect2] = []
var _clip: ShaderMaterial
var _flash: Tween
var _flash_layers: Array[Sprite2D] = []
var _bolt_layers := {}


func setup(theme: ZoneTheme, rooms: Array[Rect2] = [], ground_y := -1.0) -> void:
	z_index = -100
	add_to_group(GROUP)
	_rooms = rooms.slice(0, MAX_RECTS)
	_clip = ShaderMaterial.new()
	_clip.shader = CLIP
	var ground := 0.0
	for room in _rooms:
		ground = maxf(ground, room.end.y)
	if ground_y >= 0.0:
		ground = ground_y
	set_process(false)

	var sky_layer := CanvasLayer.new()
	sky_layer.layer = -100
	add_child(sky_layer)
	var sky := TextureRect.new()
	sky.texture = load(theme.sky)
	sky.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	sky.stretch_mode = TextureRect.STRETCH_SCALE
	sky.size = SCREEN
	sky.mouse_filter = Control.MOUSE_FILTER_IGNORE
	sky.material = _clip
	sky_layer.add_child(sky)
	_sky = sky

	for i in theme.layers.size():
		var layer: Dictionary = theme.layers[i]
		var texture: Texture2D = load(layer["texture"])
		var parallax := Parallax2D.new()
		parallax.scroll_scale = layer["scale"]
		parallax.repeat_size = Vector2(texture.get_width() * ART_SCALE, 0)
		parallax.repeat_times = 3
		parallax.autoscroll = layer.get("autoscroll", Vector2.ZERO)
		parallax.scroll_offset = Vector2(0.0, parallax.scroll_scale.y * (ground - SCREEN.y))
		parallax.z_index = i
		parallax.physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_OFF
		var sprite := Sprite2D.new()
		sprite.texture = texture
		sprite.centered = false
		sprite.scale = Vector2.ONE * ART_SCALE
		sprite.position = Vector2(0, layer.get("y", 0.0))
		sprite.material = _clip
		if layer.get("shimmer", false):
			var shimmer := ShaderMaterial.new()
			shimmer.shader = SHIMMER
			sprite.material = shimmer
		if layer.has("flap"):
			var frames: int = layer.get("frames", 2)
			sprite.region_enabled = true
			sprite.region_rect = Rect2(0, 0, texture.get_width(), texture.get_height() / frames)
			var flap := ShaderMaterial.new()
			flap.shader = FLAP
			flap.set_shader_parameter(&"fps", layer["flap"])
			flap.set_shader_parameter(&"frames", float(frames))
			sprite.material = flap
		if layer.get("flash", false):
			sprite.modulate.a = 0.0
			_flash_layers.append(sprite)
		if layer.has("bolts"):
			_bolt_layers[layer["bolts"]] = i
		parallax.add_child(sprite)
		if layer.has("fill"):
			var below := ColorRect.new()
			below.color = layer["fill"]
			below.position = Vector2(0, sprite.position.y + texture.get_height())
			below.size = Vector2(texture.get_width(), FILL_DEPTH)
			below.mouse_filter = Control.MOUSE_FILTER_IGNORE
			below.material = _clip
			parallax.add_child(below)
		add_child(parallax)
		_layers.append(parallax)


func flash(strength: float) -> void:
	if _flash:
		_flash.kill()
	var bright := Color(1.0 + strength * 0.75, 1.0 + strength * 0.9, 1.0 + strength * 1.15)
	modulate = bright
	_sky.modulate = bright
	_flash = create_tween().set_parallel().set_trans(Tween.TRANS_EXPO).set_ease(Tween.EASE_OUT)
	_flash.tween_property(self, "modulate", Color.WHITE, 0.35 + strength * 0.4)
	_flash.tween_property(_sky, "modulate", Color.WHITE, 0.35 + strength * 0.4)
	for sprite in _flash_layers:
		sprite.modulate.a = minf(1.0, strength * 1.4)
		_flash.tween_property(sprite, "modulate:a", 0.0, 0.6 + strength * 0.6)


func add_behind(node: Node2D, where: String) -> Node2D:
	if not _bolt_layers.has(where):
		return null
	var holder := Parallax2D.new()
	holder.scroll_scale = Vector2.ZERO
	holder.z_index = int(_bolt_layers[where]) - 1
	holder.physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_OFF
	holder.add_child(node)
	add_child(holder)
	move_child(holder, _layers[_bolt_layers[where]].get_index())
	return holder


func set_clipping(on: bool) -> void:
	set_process(on and not _rooms.is_empty())
	if not on:
		_clip.set_shader_parameter(&"count", 0)


func _process(_delta: float) -> void:
	var to_screen := get_viewport().get_canvas_transform()
	var rects := PackedVector4Array()
	for room in _rooms:
		var a := to_screen * room.position / SCREEN
		var b := to_screen * room.end / SCREEN
		rects.append(Vector4(a.x, a.y, b.x, b.y))
	rects.resize(MAX_RECTS)
	_clip.set_shader_parameter(&"rects", rects)
	_clip.set_shader_parameter(&"count", _rooms.size())


static func make_ambient(theme: ZoneTheme) -> CPUParticles2D:
	var kind := theme.particles
	if kind == "":
		return null
	var color := theme.particle_color
	var bits := CPUParticles2D.new()
	bits.name = "Ambient"
	bits.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	bits.emission_rect_extents = SCREEN * 0.6
	bits.gravity = Vector2.ZERO
	bits.scale_amount_min = 1.0
	bits.scale_amount_max = 2.0
	bits.z_index = 5
	var ramp := Gradient.new()
	ramp.offsets = PackedFloat32Array([0.0, 0.2, 0.8, 1.0])
	ramp.colors = PackedColorArray([Color(color, 0.0), Color(color, 0.9), Color(color, 0.8), Color(color, 0.0)])
	var additive := true
	match kind:
		"fireflies":
			bits.amount = 36
			bits.lifetime = 6.0
			bits.direction = Vector2(1, -0.3)
			bits.spread = 180.0
			bits.initial_velocity_min = 3.0
			bits.initial_velocity_max = 10.0
			ramp.offsets = PackedFloat32Array([0.0, 0.2, 0.5, 0.8, 1.0])
			ramp.colors = PackedColorArray([Color(color, 0.0), Color(color, 0.9), Color(color.lightened(0.3), 0.35), Color(color, 0.9), Color(color, 0.0)])
		"motes":
			bits.amount = 44
			bits.lifetime = 8.0
			bits.direction = Vector2(1, 0.2)
			bits.spread = 180.0
			bits.initial_velocity_min = 1.0
			bits.initial_velocity_max = 5.0
			bits.scale_amount_max = 1.0
		"snow":
			bits.amount = 90
			bits.lifetime = 9.0
			bits.direction = Vector2(-0.25, 1)
			bits.spread = 14.0
			bits.initial_velocity_min = 16.0
			bits.initial_velocity_max = 38.0
			additive = false
		"rain":
			bits.amount = 130
			bits.lifetime = 1.1
			bits.direction = Vector2(-0.22, 1)
			bits.spread = 2.0
			bits.initial_velocity_min = 330.0
			bits.initial_velocity_max = 400.0
			bits.scale_amount_max = 1.0
			bits.texture = _streak_texture()
			bits.particle_flag_align_y = true
			additive = false
		"drizzle":
			bits.amount = 90
			bits.lifetime = 1.8
			bits.direction = Vector2(-0.14, 1)
			bits.spread = 3.0
			bits.initial_velocity_min = 170.0
			bits.initial_velocity_max = 220.0
			bits.scale_amount_max = 1.0
			bits.texture = _streak_texture(5, true)
			bits.particle_flag_align_y = true
			ramp.colors = PackedColorArray([Color(color, 0.0), Color(color, 0.6), Color(color, 0.5), Color(color, 0.0)])
			additive = false
		"embers":
			bits.amount = 46
			bits.lifetime = 4.5
			bits.direction = Vector2(0.15, -1)
			bits.spread = 22.0
			bits.gravity = Vector2(0, -6)
			bits.initial_velocity_min = 10.0
			bits.initial_velocity_max = 30.0
			ramp.colors = PackedColorArray([Color(color, 0.0), Color(color.lightened(0.4), 1.0), Color(color, 0.8), Color(color.darkened(0.4), 0.0)])
		"petals":
			bits.amount = 34
			bits.lifetime = 8.0
			bits.direction = Vector2(-0.7, 1)
			bits.spread = 25.0
			bits.gravity = Vector2(-2, 3)
			bits.initial_velocity_min = 10.0
			bits.initial_velocity_max = 26.0
			additive = false
		"bubbles":
			bits.amount = 40
			bits.lifetime = 7.0
			bits.direction = Vector2(0, -1)
			bits.spread = 10.0
			bits.gravity = Vector2(0, -4)
			bits.initial_velocity_min = 8.0
			bits.initial_velocity_max = 22.0
			additive = false
		_:
			push_warning("partículas de ambiente desconhecidas: %s" % kind)
			bits.free()
			return null
	bits.preprocess = bits.lifetime
	bits.color_ramp = ramp
	var look := CanvasItemMaterial.new()
	look.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD if additive else CanvasItemMaterial.BLEND_MODE_MIX
	look.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	bits.material = look
	return bits


static func _streak_texture(length := 6, fade := false) -> ImageTexture:
	var image := Image.create(1, length, false, Image.FORMAT_RGBA8)
	for y in length:
		image.set_pixel(0, y, Color(1, 1, 1, 0.25 + 0.75 * float(y + 1) / length if fade else 1.0))
	return ImageTexture.create_from_image(image)
