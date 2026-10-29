class_name ArgesEye
extends Enemy

const SHEET := "res://assets/sprites/enemies/arges_eye.json"
const LIGHT := Color("e6f4ff")
const GAZE := Color("ff5fb0")
const GAZE_HOT := Color("ffd0ee")

enum State { PATROL, LOCK, GAZE, REST }

var span := 64.0
var speed := 22.0
var reach := 190.0
var cone := 30.0
var spin := 1.1
var warn := 0.8
var gaze_time := 1.3
var sweep := 64.0
var beam_reach := 280.0
var rest := 1.6

var state := State.PATROL
var _timer := 0.0
var _time := 0.0
var _dir := 1
var _beam_angle := PI * 0.5
var _from := Vector2.ZERO
var _to := Vector2.ZERO
var _length := 0.0
var _gaze: Area2D
var _gaze_shape: SegmentShape2D


static func create(def: Dictionary, center: Vector2, in_room: String) -> ArgesEye:
	var eye := ArgesEye.new()
	eye.position = center
	eye.room_id = in_room
	eye.span = float(def.get("span", eye.span))
	eye.sweep = float(def.get("sweep", eye.sweep))
	eye.reach = float(def.get("reach", eye.reach))
	eye.spin = float(def.get("spin", eye.spin))
	return eye


func _ready() -> void:
	super()
	material = Lights.unshaded()
	var circle := CircleShape2D.new()
	circle.radius = 6.0
	setup_body(SHEET, &"move", Vector2(0, 1), circle, Vector2.ZERO)
	add_child(Lights.point(LIGHT, 40.0, 0.5))
	_gaze = Area2D.new()
	_gaze.collision_layer = HAZARD_LAYER
	_gaze.collision_mask = 0
	_gaze.monitoring = false
	_gaze.monitorable = false
	_gaze_shape = SegmentShape2D.new()
	var shape := CollisionShape2D.new()
	shape.shape = _gaze_shape
	_gaze.add_child(shape)
	add_child(_gaze)


func _physics_process(delta: float) -> void:
	if not is_active():
		return
	_time += delta
	_timer -= delta
	var player := target()
	position.y = _home.y + sin(_time * 3.0) * 2.0
	match state:
		State.PATROL:
			play(&"move")
			position.x += _dir * speed * delta
			if absf(position.x - _home.x) > span:
				_dir = int(signf(_home.x - position.x))
			face(_dir)
			_beam_angle = wrapf(_beam_angle + spin * delta, -PI, PI)
			if player and _in_light(player):
				_lock(player)
		State.LOCK:
			if _timer <= 0.0:
				state = State.GAZE
				_timer = gaze_time
				_gaze.set_deferred(&"monitorable", true)
				play(&"attack")
				AudioManager.play_sfx(&"beam", -4.0, 0.06)
		State.GAZE:
			var t := clampf(1.0 - _timer / gaze_time, 0.0, 1.0)
			var point := _from.lerp(_to, t)
			var dir := (point - global_position).normalized()
			_length = clear_distance(global_position, dir, beam_reach)
			_beam_angle = dir.angle()
			_gaze_shape.a = Vector2.ZERO
			_gaze_shape.b = dir * _length
			if _timer <= 0.0:
				state = State.REST
				_timer = rest
				_gaze.set_deferred(&"monitorable", false)
				play(&"move")
		State.REST:
			if _timer <= 0.0:
				state = State.PATROL
	queue_redraw()


func _in_light(player: Player) -> bool:
	var to := Combat.aim_point(player) - global_position
	if to.length() > reach:
		return false
	if absf(angle_difference(to.angle(), _beam_angle)) > deg_to_rad(cone):
		return false
	return clear_distance(global_position, to, to.length()) >= to.length() - 2.0


func _lock(player: Player) -> void:
	state = State.LOCK
	_timer = Combat.telegraph_time(warn)
	var aim := Combat.aim_point(player)
	var to := aim - global_position
	var side := to.orthogonal().normalized()
	if absf(to.x) > 8.0 and to.y > absf(to.x) * 0.5:
		if signf(side.x) != signf(to.x):
			side = -side
	elif randf() < 0.5:
		side = -side
	_from = aim - side * sweep
	_to = aim + side * sweep
	face(int(signf(to.x)) if absf(to.x) > 2.0 else facing)
	play(&"windup")
	AudioManager.play_sfx(&"bolt_charge", -6.0, 0.06)


func _draw() -> void:
	match state:
		State.PATROL, State.REST:
			_draw_cone(LIGHT, 0.05 if state == State.REST else 0.13)
		State.LOCK:
			var start := (_from - global_position).normalized()
			var length := clear_distance(global_position, start, beam_reach)
			if fmod(_time, 0.16) < 0.1:
				draw_line(Vector2.ZERO, start * length, Color(GAZE, 0.6), 1.0)
			for k in 5:
				var p := _from.lerp(_to, (k + 1) / 5.0) - global_position
				draw_rect(Rect2(p.round() - Vector2(1, 1), Vector2(2, 2)), Color(GAZE, 0.55))
		State.GAZE:
			var end := Vector2.from_angle(_beam_angle) * _length
			draw_line(Vector2.ZERO, end, Color(GAZE, 0.5), 5.0)
			draw_line(Vector2.ZERO, end, GAZE, 3.0)
			draw_line(Vector2.ZERO, end, GAZE_HOT, 1.0)
			draw_rect(Rect2(end.round() - Vector2(2, 2), Vector2(4, 4)), GAZE_HOT)


func _draw_cone(col: Color, alpha: float) -> void:
	var length := clear_distance(global_position, Vector2.from_angle(_beam_angle), reach)
	if length < 6.0:
		return
	var half := deg_to_rad(cone)
	var points := PackedVector2Array([Vector2(0, 3)])
	for k in 7:
		var a := _beam_angle - half + 2.0 * half * k / 6.0
		var d := maxf(clear_distance(global_position, Vector2.from_angle(a), length), 4.0)
		points.append(Vector2.from_angle(a) * d)
	draw_colored_polygon(points, Color(col, alpha))
	draw_polyline(points, Color(col, alpha * 1.8), 1.0)


func _on_revived() -> void:
	state = State.PATROL
	_timer = 0.0
	_dir = 1
	_gaze.set_deferred(&"monitorable", false)
	play(&"move")
