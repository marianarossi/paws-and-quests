class_name EmpusaBat
extends Enemy

const SHEET := "res://assets/sprites/enemies/empusa_bat.json"

enum State { HANG, PEEK, DROP, CRUISE, RETURN }

var reach_x := 40.0
var reach_y := 160.0
var warn := 0.55
var drop_ahead := 36.0
var cruise_speed := 115.0
var cruise_length := 200.0
var fly_speed := 70.0

var state := State.HANG
var _timer := 0.0
var _drop_time := 0.5
var _from := Vector2.ZERO
var _ctrl := Vector2.ZERO
var _to := Vector2.ZERO
var _dir := 1
var _flown := 0.0


static func create(def: Dictionary, perch: Vector2, in_room: String) -> EmpusaBat:
	var bat := EmpusaBat.new()
	bat.position = perch
	bat.room_id = in_room
	bat.reach_x = float(def.get("reach", bat.reach_x))
	bat.warn = float(def.get("warn", bat.warn))
	bat.cruise_length = float(def.get("length", bat.cruise_length))
	return bat


func _ready() -> void:
	super()
	var circle := CircleShape2D.new()
	circle.radius = 5.0
	setup_body(SHEET, &"hang", Vector2.ZERO, circle, Vector2(0, 1))


func _physics_process(delta: float) -> void:
	if not is_active():
		return
	match state:
		State.HANG:
			var player := target()
			if player and _below(player):
				state = State.PEEK
				_timer = Combat.telegraph_time(warn)
				play(&"peek")
		State.PEEK:
			_timer -= delta
			if _timer <= 0.0:
				var player := target()
				if player:
					_start_drop(get_parent().to_local(Combat.aim_point(player)))
				else:
					_hang()
		State.DROP:
			_timer += delta
			var t := minf(_timer / _drop_time, 1.0)
			var u := 1.0 - t
			position = _from * u * u + _ctrl * 2.0 * u * t + _to * t * t
			if t >= 1.0:
				state = State.CRUISE
				_flown = 0.0
		State.CRUISE:
			position.x += _dir * cruise_speed * delta
			_flown += cruise_speed * delta
			if _flown > cruise_length or wall_ahead(_dir, 7.0, 0.0):
				state = State.RETURN
				play(&"move")
		State.RETURN:
			position = position.move_toward(_home, fly_speed * delta)
			face(int(signf(_home.x - position.x)))
			if position.distance_to(_home) < 1.0:
				_hang()


func _below(player: Player) -> bool:
	var d := Combat.aim_point(player) - global_position
	return absf(d.x) < reach_x and d.y > 0.0 and d.y < reach_y


func _start_drop(goal: Vector2) -> void:
	state = State.DROP
	_timer = 0.0
	_dir = int(signf(goal.x - position.x)) if absf(goal.x - position.x) > 2.0 else facing
	_from = position
	var level := maxf(goal.y, position.y + 24.0)
	_to = Vector2(position.x + _dir * drop_ahead, level)
	_ctrl = Vector2(position.x, level)
	_drop_time = clampf((level - position.y) / 160.0, 0.35, 0.9)
	face(_dir)
	play(&"attack")
	AudioManager.play_sfx(&"swoop", -3.0, 0.08)


func _hang() -> void:
	state = State.HANG
	position = _home
	face(1)
	play(&"hang")


func _on_revived() -> void:
	_hang()
