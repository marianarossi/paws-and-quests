class_name BoreasGust
extends Enemy

const SHEET := "res://assets/sprites/enemies/boreas_gust.json"
const STREAK := Color("e6f4ff")

enum State { DRIFT, PUFF, BLOW }

var drift := 32.0
var warn := 0.6
var blow := 1.2
var push := 110.0
var reach := 190.0
var half_height := 14.0
var every := 2.4

var state := State.DRIFT
var _timer := 0.0
var _cool := 1.0
var _time := 0.0
var _drift_time := 0.0
var _length := 0.0


static func create(def: Dictionary, center: Vector2, in_room: String) -> BoreasGust:
	var gust := BoreasGust.new()
	gust.position = center
	gust.room_id = in_room
	gust.facing = int(def.get("dir", "1"))
	gust.push = float(def.get("push", gust.push))
	gust.drift = float(def.get("drift", gust.drift))
	gust.reach = float(def.get("reach", gust.reach))
	return gust


func _ready() -> void:
	super()
	material = Lights.unshaded()
	var circle := CircleShape2D.new()
	circle.radius = 7.0
	setup_body(SHEET, &"move", Vector2(1, 1), circle, Vector2.ZERO)
	face(facing)


func _physics_process(delta: float) -> void:
	if not is_active():
		return
	_timer -= delta
	_cool -= delta
	_time += delta
	match state:
		State.DRIFT:
			play(&"move")
			_drift_time += delta
			position.y = _home.y + sin(_drift_time * 0.9) * drift
			if _cool <= 0.0 and target():
				state = State.PUFF
				_timer = Combat.telegraph_time(warn)
				strip(&"attack", 0, 2, _timer)
		State.PUFF:
			if _timer <= 0.0:
				state = State.BLOW
				_timer = blow
				strip(&"attack", 3, 4, 0.0)
				_length = clear_distance(global_position, Vector2(facing, 0), reach)
				EnemyShot.fire(get_parent(), &"icicle", global_position + Vector2(facing * 8.0, 1.0), Vector2(facing * 150.0, 0),
						{"life": 2.0, "radius": 3.0})
				AudioManager.play_sfx(&"gust", -2.0, 0.08)
		State.BLOW:
			_sprite.frame = 3 + int(_time * 8.0) % 2
			_push_player()
			queue_redraw()
			if _timer <= 0.0:
				state = State.DRIFT
				_cool = every
				strip(&"attack", 5, 5, 0.0)
				queue_redraw()


func _push_player() -> void:
	var player := target()
	if player == null:
		return
	var d := Combat.aim_point(player) - global_position
	if d.x * facing > 0.0 and absf(d.x) < _length and absf(d.y) < half_height + 6.0:
		player.wind = facing * push * (1.0 - 0.5 * absf(d.x) / _length)


func _draw() -> void:
	if state != State.BLOW:
		return
	for k in 7:
		var y := -half_height + (k * 2.0 * half_height / 6.0)
		var x := fmod(_time * 260.0 + k * 37.0, _length)
		var w := 10.0 + (k % 3) * 6.0
		var x0 := minf(x, _length - w)
		draw_rect(Rect2(Vector2(facing * x0 - (w if facing < 0 else 0.0), y).round(), Vector2(w, 1)), Color(STREAK, 0.55))


func _on_revived() -> void:
	state = State.DRIFT
	_cool = 1.0
	play(&"move")
	queue_redraw()
