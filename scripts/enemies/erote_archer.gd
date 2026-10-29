class_name EroteArcher
extends Enemy

const SHEET := "res://assets/sprites/enemies/erote_archer.json"
const AIM := Color("ff5fb0")

enum State { HOVER, WINDUP, FIRE }

var sight := 230.0
var climb := 45.0
var distance := 64.0
var leash := 96.0
var every := 2.6
var warn := 0.8
var arrow_speed := 250.0
var volley := 3
var volley_gap := 0.14

var state := State.HOVER
var _timer := 0.0
var _cool := 1.0
var _time := 0.0
var _retreat := 0.0
var _aim_length := 0.0
var _left := 0


static func create(def: Dictionary, center: Vector2, in_room: String) -> EroteArcher:
	var erote := EroteArcher.new()
	erote.position = center
	erote.room_id = in_room
	erote.every = float(def.get("every", erote.every))
	erote.leash = float(def.get("leash", erote.leash))
	erote.volley = int(def.get("volley", erote.volley))
	return erote


func _ready() -> void:
	super()
	material = Lights.unshaded()
	var circle := CircleShape2D.new()
	circle.radius = 6.0
	setup_body(SHEET, &"move", Vector2(0, -1), circle, Vector2(0, 0))


func _physics_process(delta: float) -> void:
	if not is_active():
		return
	_time += delta
	_timer -= delta
	_cool -= delta
	var player := target()
	var aim: Vector2 = get_parent().to_local(Combat.aim_point(player)) if player else Vector2.INF
	var near := player != null and absf(aim.x - position.x) < sight
	match state:
		State.HOVER:
			play(&"move")
			if near:
				face(int(signf(aim.x - position.x)))
				var goal_y := clampf(aim.y, _home.y - leash, _home.y + leash)
				position.y = move_toward(position.y, goal_y, climb * delta)
			var home_x := _home.x - facing * _retreat
			if near and absf(aim.x - home_x) < distance:
				home_x = clampf(aim.x - facing * distance, _home.x - leash, _home.x + leash)
			position.x = move_toward(position.x, home_x, 40.0 * delta)
			_retreat = maxf(_retreat - 6.0 * delta, 0.0)
			if near and _cool <= 0.0 and absf(aim.y - position.y) < 8.0:
				state = State.WINDUP
				_timer = Combat.telegraph_time(warn)
				play(&"windup")
				AudioManager.play_sfx(&"bow_draw", -4.0, 0.06)
		State.WINDUP:
			_aim_length = clear_distance(_bow(), Vector2(facing, 0), sight + 40.0)
			queue_redraw()
			if _timer <= 0.0:
				state = State.FIRE
				_timer = 0.0
				_left = volley
				_cool = every
				_retreat = 26.0
				queue_redraw()
		State.FIRE:
			if _timer <= 0.0:
				if _left > 0:
					play(&"attack")
					_sprite.frame = 0
					EnemyShot.fire(get_parent(), &"arrow", _bow(), Vector2(facing * arrow_speed, 0), {"life": 2.0, "radius": 2.5})
					AudioManager.play_sfx(&"twang", -2.0, 0.08)
					_left -= 1
					_timer = volley_gap if _left > 0 else 0.35
				else:
					state = State.HOVER
	position.y += sin(_time * 3.5) * 0.15


func _bow() -> Vector2:
	return global_position + Vector2(facing * 15.0, -1.0)


func _draw() -> void:
	if state != State.WINDUP:
		return
	var blink := 0.08 if _timer < 0.3 else 0.16
	if fmod(_timer, blink * 2.0) > blink:
		return
	var start := to_local(_bow())
	var step := 6.0
	var d := 4.0
	while d < _aim_length:
		draw_rect(Rect2(round(start.x + facing * d), round(start.y), 3, 1), AIM)
		d += step


func _on_revived() -> void:
	state = State.HOVER
	_cool = 1.0
	_retreat = 0.0
	queue_redraw()
	play(&"move")
