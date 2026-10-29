extends Node

const DUST_COLOR := Color(0.82, 0.85, 0.95)
const SPARK_COLOR := Color("fff7dc")
const LAND_THRESHOLD := 140.0
const TRAIL_OFFSET := Vector2(0, -10)

var _trail: DashTrail
var _sparks: CPUParticles2D

@onready var player: Player = get_parent()


func _ready() -> void:
	player.jumped.connect(_on_jumped)
	player.landed.connect(_on_landed)
	player.dash_started.connect(_on_dash_started)
	player.died.connect(_on_died)
	player.respawned.connect(_on_respawned)
	_trail = DashTrail.new()
	add_child(_trail)
	_sparks = _make_sparks()
	player.add_child.call_deferred(_sparks)


func _physics_process(delta: float) -> void:
	_sparks.emitting = player.is_dashing and player.velocity != Vector2.ZERO
	if _sparks.emitting:
		_trail.add_point(player.global_position + TRAIL_OFFSET)
	var body := player.body_sprite
	body.self_modulate = body.self_modulate.lerp(Color.WHITE, 1.0 - exp(-22.0 * delta))


func _on_jumped(kind: StringName) -> void:
	match kind:
		&"double":
			AudioManager.play_sfx(&"double_jump")
			_puff(player.global_position, Vector2.DOWN, 10, 70.0, 70.0)
		&"wall", &"wall_bounce":
			AudioManager.play_sfx(&"wall_jump")
			_puff(player.global_position + Vector2(-player.facing * 4, -8), Vector2(player.facing, 0), 6, 60.0, 50.0)
		&"spring":
			_puff(player.global_position, Vector2.UP, 8, 80.0, 60.0)
		&"swim":
			AudioManager.play_sfx(&"swim", -4.0)
			_puff(player.global_position + Vector2(0, -4), Vector2.DOWN, 5, 40.0, 60.0, Color(0.85, 0.95, 1.0))
		_:
			AudioManager.play_sfx(&"jump")
			_puff(player.global_position, Vector2.UP, 5, 45.0, 75.0)


func _on_landed(fall_speed: float) -> void:
	if fall_speed < LAND_THRESHOLD:
		return
	AudioManager.play_sfx(&"land", linear_to_db(clampf(fall_speed / 240.0, 0.4, 1.0)))
	_puff(player.global_position, Vector2.UP, 8, 55.0, 80.0)


func _on_dash_started(direction: Vector2) -> void:
	AudioManager.play_sfx(&"dash")
	player.body_sprite.self_modulate = Color(4, 4, 4)
	_puff(player.global_position + TRAIL_OFFSET, -direction, 12, 130.0, 55.0, SPARK_COLOR)


func _on_died() -> void:
	AudioManager.play_sfx(&"death")
	var center := player.global_position + TRAIL_OFFSET
	for color: Color in [HeroLook.color("w"), HeroLook.color("J"), HeroLook.color("o"), HeroLook.color("s")]:
		_puff(center, Vector2.UP, 6, 150.0, 180.0, color)


func _on_respawned() -> void:
	AudioManager.play_sfx(&"respawn")
	_puff(player.global_position, Vector2.UP, 8, 60.0, 90.0, SPARK_COLOR)


func _puff(at: Vector2, direction: Vector2, amount: int, speed: float, spread: float, color := DUST_COLOR) -> void:
	var dust := CPUParticles2D.new()
	dust.one_shot = true
	dust.amount = amount
	dust.lifetime = 0.38
	dust.explosiveness = 0.92
	dust.direction = direction
	dust.spread = spread
	dust.gravity = Vector2(0, -30)
	dust.initial_velocity_min = speed * 0.35
	dust.initial_velocity_max = speed
	dust.damping_min = 80.0
	dust.damping_max = 140.0
	dust.scale_amount_min = 1.0
	dust.scale_amount_max = 3.0
	var fade := Gradient.new()
	fade.colors = PackedColorArray([color, Color(color, 0.0)])
	dust.color_ramp = fade
	dust.z_index = player.z_index - 1
	player.get_parent().add_child(dust)
	dust.global_position = at
	dust.emitting = true
	dust.finished.connect(dust.queue_free)


func _make_sparks() -> CPUParticles2D:
	var sparks := CPUParticles2D.new()
	sparks.name = "DashSparks"
	sparks.emitting = false
	sparks.amount = 22
	sparks.lifetime = 0.4
	sparks.local_coords = false
	sparks.position = TRAIL_OFFSET
	sparks.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	sparks.emission_rect_extents = Vector2(4, 9)
	sparks.spread = 180.0
	sparks.gravity = Vector2(0, 40)
	sparks.initial_velocity_min = 4.0
	sparks.initial_velocity_max = 26.0
	sparks.scale_amount_min = 1.0
	sparks.scale_amount_max = 2.0
	var ramp := Gradient.new()
	ramp.offsets = PackedFloat32Array([0.0, 0.3, 0.75, 1.0])
	ramp.colors = PackedColorArray([SPARK_COLOR, Color("9fb4e8"), Color("41599a"), Color("41599a", 0.0)])
	sparks.color_ramp = ramp
	sparks.material = Lights.unshaded()
	sparks.z_index = -1
	return sparks
