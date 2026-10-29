class_name MiasmaToad
extends Enemy

const SHEET := "res://assets/sprites/enemies/miasma_toad.json"
const TONGUE := Color("ff8ad0")
const TONGUE_EDGE := Color("c0297f")

enum State { IDLE, CROUCH, AIR, LAND, TONGUE_WINDUP, TONGUE }

var hop_every := 1.1
var hop_vx := 75.0
var hop_vy := 165.0
var hop_gravity := 520.0
var sight := 170.0
var tongue_reach := 68.0
var warn := 0.9
var every := 1.4
var too_close := 40.0

var state := State.IDLE
var _timer := 0.0
var _hop_cool := 0.8
var _cool := 0.6
var _vel := Vector2.ZERO
var _dir := -1
var _aim := Vector2.RIGHT
var _tongue_len := 0.0
var _tongue_max := 0.0
var _tongue_age := 0.0
var _tongue_area: Area2D
var _tongue_shape: SegmentShape2D


static func create(def: Dictionary, feet: Vector2, in_room: String) -> MiasmaToad:
	var toad := MiasmaToad.new()
	toad.position = feet
	toad.room_id = in_room
	toad.hop_every = float(def.get("hop", toad.hop_every))
	toad.every = float(def.get("every", toad.every))
	toad.facing = int(def.get("dir", "-1"))
	return toad


func _ready() -> void:
	super()
	material = Lights.unshaded()
	var box := RectangleShape2D.new()
	box.size = Vector2(18, 10)
	setup_body(SHEET, &"idle", Vector2(0, -15), box, Vector2(0, -6))
	face(facing)
	_tongue_area = Area2D.new()
	_tongue_area.collision_layer = HAZARD_LAYER
	_tongue_area.collision_mask = 0
	_tongue_area.monitoring = false
	_tongue_area.monitorable = false
	_tongue_shape = SegmentShape2D.new()
	var shape := CollisionShape2D.new()
	shape.shape = _tongue_shape
	_tongue_area.add_child(shape)
	add_child(_tongue_area)


func _physics_process(delta: float) -> void:
	if not is_active():
		return
	_hop_cool -= delta
	_cool -= delta
	_timer -= delta
	match state:
		State.IDLE:
			play(&"idle")
			_decide()
		State.CROUCH:
			if _timer <= 0.0:
				state = State.AIR
				_vel = Vector2(_dir * hop_vx, -hop_vy)
				_timer = 0.08
		State.AIR:
			_fly(delta)
		State.LAND:
			if _timer <= 0.0:
				state = State.IDLE
				_hop_cool = hop_every
		State.TONGUE_WINDUP:
			if _timer <= 0.0:
				state = State.TONGUE
				_tongue_age = 0.0
				_tongue_len = 0.0
				_tongue_max = clear_distance(_mouth(), _aim, tongue_reach)
				_tongue_area.set_deferred(&"monitorable", true)
				play(&"attack")
				AudioManager.play_sfx(&"tongue", -2.0, 0.08)
		State.TONGUE:
			_tongue_age += delta
			var t := _tongue_age
			if t < 0.08:
				_tongue_len = _tongue_max * t / 0.08
			elif t < 0.2:
				_tongue_len = _tongue_max
			elif t < 0.34:
				_tongue_len = _tongue_max * (1.0 - (t - 0.2) / 0.14)
			else:
				_tongue_len = 0.0
				_tongue_area.set_deferred(&"monitorable", false)
				state = State.IDLE
				_cool = every
				_hop_cool = 0.5
			var mouth := to_local(_mouth())
			_tongue_shape.a = mouth
			_tongue_shape.b = mouth + _aim * maxf(_tongue_len, 0.5)
			queue_redraw()


func _decide() -> void:
	var player := target()
	if player and _cool <= 0.0:
		var d := player.global_position - global_position
		var to_aim := Combat.aim_point(player) - _mouth()
		if to_aim.length() < tongue_reach and d.y < 24.0:
			_start_tongue(player)
			return
	if _hop_cool > 0.0:
		return
	var dx: float = player.global_position.x - global_position.x if player else 0.0
	if player and absf(dx) < too_close:
		_dir = -int(signf(dx)) if absf(dx) > 1.0 else -facing
	elif player and absf(dx) < sight:
		_dir = int(signf(dx))
	else:
		_dir = _wander_dir()
	if _can_land(_dir * hop_vx * (2.0 * hop_vy / hop_gravity)):
		face(_dir)
		state = State.CROUCH
		_timer = 0.14
		_frame(0)
	else:
		face(-_dir)
		_hop_cool = 0.6


func _start_tongue(player: Player) -> void:
	face(int(signf(player.global_position.x - global_position.x)))
	_aim = (Combat.aim_point(player) - _mouth()).normalized()
	if _aim.y > 0.35:
		_aim = Vector2(signf(_aim.x), 0.35).normalized()
	state = State.TONGUE_WINDUP
	_timer = Combat.telegraph_time(warn)
	play(&"windup")
	AudioManager.play_sfx(&"croak", -2.0, 0.1)


func _fly(delta: float) -> void:
	_vel.y += hop_gravity * delta
	if clear_distance(global_position + Vector2(0, -6), Vector2(signf(_vel.x), 0), 11.0) < 11.0:
		_vel.x = 0.0
	position += _vel * delta
	_frame(1 if _timer > 0.0 else (2 if _vel.y < -60.0 else (3 if _vel.y < 60.0 else 4)))
	if _vel.y > 0.0:
		var ground := ground_below(global_position, _vel.y * delta + 2.0)
		if ground != INF:
			global_position.y = ground
			_frame(5)
			_timer = 0.16
			AudioManager.play_sfx(&"land", -10.0, 0.1)
			state = State.LAND
	if global_position.y > _home.y + 600.0:
		revive()


func _mouth() -> Vector2:
	return global_position + Vector2(facing * 8.0, -7.0)


func _frame(i: int) -> void:
	if _sprite.animation != &"move":
		_sprite.play(&"move")
	_sprite.pause()
	_sprite.frame = i


func _wander_dir() -> int:
	if absf(position.x - _home.x) > 48.0:
		return int(signf(_home.x - position.x))
	return -facing if randf() < 0.4 else facing


func _can_land(dx: float) -> bool:
	var dir := Vector2(signf(dx), 0)
	if clear_distance(global_position + Vector2(0, -8), dir, absf(dx)) < absf(dx):
		return false
	return floor_at(global_position + Vector2(dx, 0)) and floor_at(global_position + Vector2(dx * 0.5, 0))


func _draw() -> void:
	if state == State.TONGUE and _tongue_len > 0.5:
		var a := to_local(_mouth())
		var b := a + _aim * _tongue_len
		draw_line(a + Vector2(0, 1), b + Vector2(0, 1), TONGUE_EDGE, 1.0)
		draw_line(a, b, TONGUE, 2.0)
		draw_rect(Rect2((b - Vector2(1.5, 1.5)).round(), Vector2(4, 4)), TONGUE_EDGE)
		draw_rect(Rect2((b - Vector2(0.5, 0.5)).round(), Vector2(2, 2)), TONGUE)


func _on_revived() -> void:
	state = State.IDLE
	_hop_cool = 0.8
	_cool = 0.6
	_tongue_len = 0.0
	_tongue_area.set_deferred(&"monitorable", false)
	queue_redraw()
	play(&"idle")
