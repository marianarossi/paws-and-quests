class_name EnemyShot
extends Area2D

const SHEET := "res://assets/sprites/enemies/shots.json"
const FADE_WARNING := 0.5

static var _frames_cache := {}

var kind: StringName = &"arrow"
var velocity := Vector2.ZERO
var fall := 0.0
var turn_rate := 0.0
var homing_time := 0.0
var lifetime := 4.0
var radius := 3.0
var stick := 0.0
var grow := 0.0

var _age := 0.0
var _target: Player
var _sprite: AnimatedSprite2D
var _done := false
var _stuck := false
var _shape: CircleShape2D


static func fire(parent: Node, shot_kind: StringName, at: Vector2, vel: Vector2, opts := {}) -> EnemyShot:
	var shot := EnemyShot.new()
	shot.kind = shot_kind
	shot.velocity = vel
	shot.fall = float(opts.get("gravity", 0.0))
	shot.turn_rate = float(opts.get("turn", 0.0))
	shot.homing_time = float(opts.get("homing", 0.0))
	shot.lifetime = float(opts.get("life", 4.0))
	shot.radius = float(opts.get("radius", 3.0))
	shot.stick = float(opts.get("stick", 0.0))
	shot.grow = float(opts.get("grow", 0.0))
	shot._target = Combat.find_player(parent)
	parent.add_child(shot)
	shot.global_position = at
	shot.reset_physics_interpolation()
	return shot


static func frames_of(shot_kind: StringName) -> SpriteFrames:
	if _frames_cache.has(shot_kind):
		return _frames_cache[shot_kind]
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(SHEET))
	var texture := load(SHEET.get_base_dir().path_join(data["image"])) as Texture2D
	var spec: Dictionary = data["shots"][String(shot_kind)]
	var frames := SpriteFrames.new()
	frames.remove_animation(&"default")
	frames.add_animation(&"fly")
	frames.set_animation_loop(&"fly", true)
	frames.set_animation_speed(&"fly", float(spec["fps"]))
	for i in int(spec["frames"]):
		var atlas := AtlasTexture.new()
		atlas.atlas = texture
		atlas.region = Rect2(float(spec["x"]) + i * float(spec["frame_w"]), float(spec["y"]), float(spec["frame_w"]), float(spec["frame_h"]))
		frames.add_frame(&"fly", atlas)
	_frames_cache[shot_kind] = frames
	return frames


func _ready() -> void:
	collision_layer = Combat.PROJECTILE_LAYER
	collision_mask = Combat.WORLD_LAYER
	z_index = 12
	add_to_group(Combat.PROJECTILE_GROUP)
	_shape = CircleShape2D.new()
	_shape.radius = radius
	var shape := CollisionShape2D.new()
	shape.shape = _shape
	add_child(shape)
	_sprite = AnimatedSprite2D.new()
	_sprite.sprite_frames = frames_of(kind)
	_sprite.material = Lights.unshaded()
	_sprite.play(&"fly")
	_sprite.rotation = velocity.angle()
	_sprite.visible = grow <= 0.0
	material = Lights.unshaded()
	add_child(_sprite)
	add_child(Lights.point(Combat.PINK, 22.0, 0.45))
	body_entered.connect(_on_body_entered)
	Events.player_died.connect(func(_at: Vector2) -> void: pop(false))


func _physics_process(delta: float) -> void:
	_age += delta
	if _age >= lifetime:
		pop(false)
		return
	if turn_rate > 0.0 and _age < homing_time and is_instance_valid(_target) and not _target.is_dead():
		velocity = Combat.steer(velocity, global_position, Combat.aim_point(_target), deg_to_rad(turn_rate), delta)
	if _stuck:
		return
	velocity.y += fall * delta
	global_position += velocity * delta
	_sprite.rotation = velocity.angle()
	if grow > 0.0:
		_shape.radius += grow * delta
		queue_redraw()
	if lifetime - _age < FADE_WARNING:
		modulate.a = 0.35 if fmod(_age, 0.12) < 0.06 else 1.0


func _draw() -> void:
	if grow > 0.0:
		draw_arc(Vector2.ZERO, _shape.radius, 0.0, TAU, 20, Combat.PINK, 2.0)
		draw_arc(Vector2.ZERO, maxf(_shape.radius - 2.0, 1.0), 0.0, TAU, 16, Combat.HOT, 1.0)


func _on_body_entered(_body: Node2D) -> void:
	if stick <= 0.0:
		pop()
	elif not _stuck:
		_stuck = true
		lifetime = _age + stick
		AudioManager.play_sfx(&"snap", -10.0, 0.15)


func pop(loud := true) -> void:
	if _done:
		return
	_done = true
	Combat.burst(get_parent(), global_position, Combat.PINK, 8 if loud else 4, 90.0 if loud else 40.0)
	if loud:
		AudioManager.play_sfx(&"spark_pop", -4.0, 0.12)
	queue_free()
