class_name Karkinos
extends Enemy

const SHEET := "res://assets/sprites/enemies/karkinos.json"

enum State { SCUTTLE, PAUSE, WINDUP, LUNGE, RECOVER, GUARD }

var speed := 55.0
var burst := 0.5
var rest := 0.6
var sight := 110.0
var lunge_speed := 240.0
var lunge_reach := 120.0
var recover := 0.55
var every := 1.6
var warn := 0.5

var state := State.PAUSE
var _timer := 0.4
var _cool := 0.5
var _dir := -1
var _travelled := 0.0
var _goal := 0.0
var _claw: CollisionShape2D


static func create(def: Dictionary, feet: Vector2, in_room: String) -> Karkinos:
	var crab := Karkinos.new()
	crab.position = feet
	crab.room_id = in_room
	crab.speed = float(def.get("speed", crab.speed))
	crab.sight = float(def.get("sight", crab.sight))
	crab._dir = int(def.get("dir", "-1"))
	return crab


func _ready() -> void:
	super()
	var box := RectangleShape2D.new()
	box.size = Vector2(18, 10)
	setup_body(SHEET, &"move", Vector2(0, -15), box, Vector2(0, -7))
	var pincer := RectangleShape2D.new()
	pincer.size = Vector2(10, 9)
	_claw = CollisionShape2D.new()
	_claw.shape = pincer
	_claw.position = Vector2(13, -11)
	_claw.disabled = true
	add_child(_claw)


func _physics_process(delta: float) -> void:
	if not is_active():
		return
	_timer -= delta
	_cool -= delta
	match state:
		State.SCUTTLE:
			if blocked(_dir, 12.0):
				_dir = -_dir
			position.x += _dir * speed * delta
			if _timer <= 0.0:
				state = State.PAUSE
				_timer = rest
				_sprite.pause()
			_try_attack()
		State.PAUSE:
			if _try_attack():
				return
			if _timer <= 0.0:
				var player := target()
				if player and absf(player.global_position.x - global_position.x) < 160.0:
					_dir = int(signf(player.global_position.x - global_position.x))
				state = State.SCUTTLE
				_timer = burst
				face(1)
				_sprite.play(&"move")
		State.WINDUP:
			if _timer <= 0.0:
				state = State.LUNGE
				_travelled = 0.0
				play(&"attack")
				_claw.position.x = 13.0 * _dir
				_claw.set_deferred(&"disabled", false)
				AudioManager.play_sfx(&"snap", -2.0, 0.1)
		State.LUNGE:
			var step := lunge_speed * delta
			if blocked(_dir, 12.0) or _travelled >= _goal:
				_end_lunge()
				return
			position.x += _dir * step
			_travelled += step
		State.RECOVER:
			if _timer <= 0.0:
				state = State.PAUSE
				_timer = 0.2
				face(1)
				play(&"move")
				_sprite.pause()
		State.GUARD:
			if _timer <= 0.0:
				state = State.PAUSE
				_timer = 0.2
				face(1)
				play(&"move")


func _try_attack() -> bool:
	var player := target()
	if player == null or _cool > 0.0:
		return false
	var d := player.global_position - global_position
	if absf(d.x) > sight or absf(d.y) > 24.0:
		return false
	_dir = int(signf(d.x))
	face(_dir)
	_goal = minf(absf(d.x) + 20.0, lunge_reach)
	state = State.WINDUP
	_timer = Combat.telegraph_time(warn)
	play(&"windup")
	return true


func _end_lunge() -> void:
	state = State.RECOVER
	_timer = recover
	_cool = every
	_claw.set_deferred(&"disabled", true)


func _on_revived() -> void:
	state = State.PAUSE
	_timer = 0.4
	_cool = 0.5
	_claw.set_deferred(&"disabled", true)
	face(1)
	play(&"move")
