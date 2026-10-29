class_name Mine
extends Area2D

enum Phase { SLEEP, ARMING, CHASE, GONE }

const SHEET := "res://assets/sprites/combat/mine.json"
const RADIUS := 5.0
const RING_DOTS := 20

var radius := 72.0
var warn := 0.55
var speed := 135.0
var turn := 150.0
var chase_time := 2.6
var respawn := 3.5
var room_id := ""

var phase := Phase.SLEEP

var _home := Vector2.ZERO
var _velocity := Vector2.ZERO
var _timer := 0.0
var _time := 0.0
var _sprite: AnimatedSprite2D


static func create(def: Dictionary, center: Vector2, in_room: String) -> Mine:
	var mine := Mine.new()
	mine.position = center
	mine.room_id = in_room
	mine.radius = float(def.get("radius", mine.radius))
	mine.warn = float(def.get("warn", mine.warn))
	mine.speed = float(def.get("speed", mine.speed))
	mine.turn = float(def.get("turn", mine.turn))
	mine.chase_time = float(def.get("chase", mine.chase_time))
	mine.respawn = float(def.get("respawn", mine.respawn))
	return mine


func _ready() -> void:
	collision_layer = Combat.PROJECTILE_LAYER
	collision_mask = Combat.WORLD_LAYER
	z_index = 12
	material = Lights.unshaded()
	add_to_group(Combat.PROJECTILE_GROUP)
	var circle := CircleShape2D.new()
	circle.radius = RADIUS
	var shape := CollisionShape2D.new()
	shape.shape = circle
	add_child(shape)
	_sprite = AnimatedSprite2D.new()
	_sprite.sprite_frames = SpriteSheet.frames(SHEET)
	_sprite.material = Lights.unshaded()
	_sprite.play(&"sleep")
	add_child(_sprite)
	_home = position
	_time = position.x * 0.05
	body_entered.connect(_on_body_entered)
	Events.player_respawned.connect(_reset)


func telegraph() -> float:
	return Combat.telegraph_time(warn)


func _physics_process(delta: float) -> void:
	_time += delta
	var target := _target()
	match phase:
		Phase.SLEEP:
			_sprite.position = Vector2(0, roundf(sin(_time * 1.8) * 2.0))
			if target and global_position.distance_to(Combat.aim_point(target)) < radius:
				phase = Phase.ARMING
				_timer = telegraph()
				_sprite.play(&"armed")
				AudioManager.play_sfx(&"mine_arm", -4.0)
		Phase.ARMING:
			_timer -= delta
			_sprite.position = Vector2(randi_range(-1, 1), randi_range(-1, 1))
			if _timer <= 0.0:
				if target == null:
					_reset()
				else:
					phase = Phase.CHASE
					_timer = chase_time
					_sprite.position = Vector2.ZERO
					_velocity = (Combat.aim_point(target) - global_position).normalized() * speed
		Phase.CHASE:
			_timer -= delta
			if target:
				_velocity = Combat.steer(_velocity, global_position, Combat.aim_point(target), deg_to_rad(turn), delta)
			global_position += _velocity * delta
			if _timer <= 0.0:
				pop()
			elif _timer < 0.6:
				_sprite.modulate.a = 0.4 if fmod(_timer, 0.12) < 0.06 else 1.0
		Phase.GONE:
			_timer -= delta
			if respawn > 0.0 and _timer <= 0.0 and (target == null or _home.distance_to(get_parent().to_local(Combat.aim_point(target))) > radius + 24.0):
				_reset()
	queue_redraw()


func pop(loud := true) -> void:
	if phase == Phase.GONE:
		return
	Combat.burst(get_parent(), global_position, Combat.PINK, 14, 130.0)
	if loud:
		AudioManager.play_sfx(&"spark_pop", -2.0, 0.1)
	phase = Phase.GONE
	_timer = respawn
	visible = false
	set_deferred(&"monitorable", false)
	set_deferred(&"monitoring", false)


func _reset() -> void:
	position = _home
	reset_physics_interpolation()
	phase = Phase.SLEEP
	visible = true
	_sprite.modulate.a = 1.0
	_sprite.play(&"sleep")
	set_deferred(&"monitorable", true)
	set_deferred(&"monitoring", true)


func _target() -> Player:
	if room_id != "" and Game.current_room != room_id:
		return null
	return Combat.find_player(self)


func _on_body_entered(_body: Node2D) -> void:
	if phase == Phase.CHASE:
		pop()


func _draw() -> void:
	var ring := radius
	var color := Color(Combat.MAGENTA, 0.22)
	match phase:
		Phase.SLEEP:
			pass
		Phase.ARMING:
			var progress := 1.0 - _timer / telegraph()
			ring = lerpf(radius, 9.0, progress)
			color = Color(Combat.PINK, 0.4 + 0.6 * progress)
		_:
			return
	for i in RING_DOTS:
		var dot := Vector2.from_angle(TAU * i / RING_DOTS + _time * 0.4) * ring
		draw_rect(Rect2(dot.round() - Vector2.ONE, Vector2(2, 2)), color)
