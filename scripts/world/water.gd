class_name Water
extends Area2D

const PLAYER_LAYER := 2
const SHADER := preload("res://shaders/water.gdshader")
const PAD := 4.0
const SKIN := 5.0
const FLOAT_LINE := 12.0
const SPLASH_SPEED := 70.0
const RIPPLE_TIME := 0.7

var size := Vector2(96, 48)
var has_surface := true
var top_color := Color(0.36, 0.84, 0.82, 0.5)
var deep_color := Color(0.10, 0.28, 0.48, 0.74)
var foam_color := Color(0.86, 1.0, 0.96, 0.95)

var depth_above := 0.0

var _ripples: Array[Vector2] = []


static func create(top_left: Vector2, pixel_size: Vector2, with_surface: bool, theme: ZoneTheme, depth_above := 0.0) -> Water:
	var water := Water.new()
	water.position = top_left
	water.size = pixel_size
	water.has_surface = with_surface
	water.depth_above = depth_above
	water.top_color = theme.water_top
	water.deep_color = theme.water_deep
	water.foam_color = theme.water_foam
	return water


func _ready() -> void:
	collision_layer = 0
	collision_mask = PLAYER_LAYER
	z_index = 11
	var skin := SKIN if has_surface else 0.0
	var box := RectangleShape2D.new()
	box.size = Vector2(size.x, size.y - skin)
	var shape := CollisionShape2D.new()
	shape.shape = box
	shape.position = Vector2(size.x * 0.5, skin + (size.y - skin) * 0.5)
	add_child(shape)

	var surface := ColorRect.new()
	surface.position = Vector2(0, -PAD)
	surface.size = size + Vector2(0, PAD)
	surface.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var look := ShaderMaterial.new()
	look.shader = SHADER
	look.set_shader_parameter(&"size", size)
	look.set_shader_parameter(&"origin", global_position)
	look.set_shader_parameter(&"surface", has_surface)
	look.set_shader_parameter(&"top_depth", depth_above)
	look.set_shader_parameter(&"top_color", top_color)
	look.set_shader_parameter(&"deep_color", deep_color)
	look.set_shader_parameter(&"foam_color", foam_color)
	look.set_shader_parameter(&"reveal", true)
	surface.material = look
	add_child(surface)
	var back := ColorRect.new()
	var grow := Vector2(8, 8)
	back.position = Vector2(-grow.x, -PAD)
	back.size = size + Vector2(grow.x * 2.0, PAD + grow.y)
	back.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var back_look := look.duplicate() as ShaderMaterial
	back_look.set_shader_parameter(&"reveal", false)
	back_look.set_shader_parameter(&"size", size + Vector2(grow.x * 2.0, grow.y))
	back_look.set_shader_parameter(&"origin", global_position - Vector2(grow.x, 0.0))
	back.material = back_look
	back.z_as_relative = false
	back.z_index = -1
	add_child(back)
	add_child(_make_bubbles())
	material = Lights.unshaded()
	set_process(false)
	body_entered.connect(_on_body_entered)
	body_exited.connect(_on_body_exited)


func is_at_surface(feet: Vector2) -> bool:
	return has_surface and feet.y - 14.0 < global_position.y + SKIN


func _on_body_entered(body: Node2D) -> void:
	var player := body as Player
	if player == null:
		return
	player.enter_water(self)
	if has_surface and player.velocity.y > SPLASH_SPEED:
		_splash(player.global_position.x, clampf(player.velocity.y / 240.0, 0.4, 1.0))


func _on_body_exited(body: Node2D) -> void:
	var player := body as Player
	if player == null:
		return
	player.exit_water(self)
	if has_surface and player.velocity.y < -SPLASH_SPEED and player.global_position.y < global_position.y + size.y * 0.5:
		_splash(player.global_position.x, 0.5)


func _splash(world_x: float, strength: float) -> void:
	AudioManager.play_sfx(&"splash", linear_to_db(strength))
	var drops := CPUParticles2D.new()
	drops.one_shot = true
	drops.explosiveness = 0.95
	drops.amount = int(6 + 10 * strength)
	drops.lifetime = 0.55
	drops.direction = Vector2.UP
	drops.spread = 55.0
	drops.gravity = Vector2(0, 420)
	drops.initial_velocity_min = 50.0 * strength
	drops.initial_velocity_max = 150.0 * strength
	drops.scale_amount_min = 1.0
	drops.scale_amount_max = 2.0
	var fade := Gradient.new()
	fade.colors = PackedColorArray([foam_color, Color(top_color, 0.9), Color(top_color, 0.0)])
	drops.color_ramp = fade
	drops.material = Lights.unshaded()
	drops.z_index = 1
	add_child(drops)
	drops.global_position = Vector2(world_x, global_position.y + 1.0)
	drops.emitting = true
	drops.finished.connect(drops.queue_free)
	_ripples.append(Vector2(world_x - global_position.x, 0.0))
	set_process(true)


func _process(delta: float) -> void:
	for i in range(_ripples.size() - 1, -1, -1):
		_ripples[i].y += delta
		if _ripples[i].y >= RIPPLE_TIME:
			_ripples.remove_at(i)
	if _ripples.is_empty():
		set_process(false)
	queue_redraw()


func _draw() -> void:
	for ripple in _ripples:
		var age := ripple.y / RIPPLE_TIME
		var reach := 3.0 + age * 22.0
		var length := 5.0 - 3.0 * age
		var color := Color(foam_color, 1.0 - age)
		for side: float in [-1.0, 1.0]:
			var x := clampf(ripple.x + side * reach, 0.0, size.x - length)
			draw_rect(Rect2(Vector2(x, 0.0).floor(), Vector2(length, 1.0)), color)


func _make_bubbles() -> CPUParticles2D:
	var bubbles := CPUParticles2D.new()
	bubbles.amount = clampi(int(size.x * size.y / 900.0), 2, 14)
	bubbles.lifetime = 2.6
	bubbles.preprocess = 2.6
	bubbles.position = Vector2(size.x * 0.5, size.y * 0.6)
	bubbles.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	bubbles.emission_rect_extents = Vector2(size.x * 0.5 - 2.0, size.y * 0.35)
	bubbles.direction = Vector2.UP
	bubbles.spread = 12.0
	bubbles.gravity = Vector2(0, -14)
	bubbles.initial_velocity_min = 4.0
	bubbles.initial_velocity_max = 10.0
	bubbles.scale_amount_min = 1.0
	bubbles.scale_amount_max = 2.0
	var fade := Gradient.new()
	fade.offsets = PackedFloat32Array([0.0, 0.2, 0.8, 1.0])
	fade.colors = PackedColorArray([Color(foam_color, 0.0), Color(foam_color, 0.55), Color(foam_color, 0.45), Color(foam_color, 0.0)])
	bubbles.color_ramp = fade
	bubbles.material = Lights.unshaded()
	return bubbles
