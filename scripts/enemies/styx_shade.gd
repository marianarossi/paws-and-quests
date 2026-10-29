class_name StyxShade
extends Enemy

const SHEET := "res://assets/sprites/enemies/styx_shade.json"

enum State { DRIFT, WINDUP, LUNGE, FADE }

var speed := 20.0
var sight := 180.0
var strike_range := 84.0
var warn := 0.6
var lunge_speed := 210.0
var lunge_time := 0.45
var every := 1.4
var keep := 52.0
var min_strike := 34.0

var state := State.DRIFT
var _timer := 0.0
var _cool := 1.0
var _time := 0.0
var _aim := Vector2.RIGHT


static func create(def: Dictionary, center: Vector2, in_room: String) -> StyxShade:
	var shade := StyxShade.new()
	shade.position = center
	shade.room_id = in_room
	shade.speed = float(def.get("speed", shade.speed))
	return shade


func _ready() -> void:
	super()
	var circle := CircleShape2D.new()
	circle.radius = 7.0
	setup_body(SHEET, &"move", Vector2(0, 1), circle, Vector2.ZERO)
	_ghost(true)


func _physics_process(delta: float) -> void:
	if not is_active():
		return
	_timer -= delta
	_cool -= delta
	_time += delta
	var player := target()
	var aim: Vector2 = get_parent().to_local(Combat.aim_point(player)) if player else _home
	match state:
		State.DRIFT:
			play(&"move")
			var goal := _home
			if player and position.distance_to(aim) < sight:
				var away := (position - aim).normalized() if position.distance_to(aim) > 1.0 else Vector2.UP
				goal = aim + away * keep
			position = position.move_toward(goal, speed * delta)
			position.y += sin(_time * 2.5) * 0.2
			face(int(signf(aim.x - position.x)) if absf(aim.x - position.x) > 2.0 else facing)
			var gap := position.distance_to(aim)
			if player and _cool <= 0.0 and gap < strike_range and gap > min_strike:
				state = State.WINDUP
				_timer = Combat.telegraph_time(warn)
				_aim = (aim - position).normalized()
				strip(&"attack", 0, 2, _timer)
				_ghost(false)
				AudioManager.play_sfx(&"swoop", -6.0, 0.15)
		State.WINDUP:
			position -= _aim * 8.0 * delta
			if _timer <= 0.0:
				state = State.LUNGE
				_timer = lunge_time
				strip(&"attack", 3, 4, 0.15)
		State.LUNGE:
			position += _aim * lunge_speed * delta
			if _timer <= 0.0:
				state = State.FADE
				_timer = 0.3
				_ghost(true)
		State.FADE:
			if _timer <= 0.0:
				state = State.DRIFT
				_cool = every


func _ghost(on: bool) -> void:
	set_deferred(&"monitorable", not on)
	if on:
		var tween := create_tween()
		tween.tween_property(_sprite, "modulate:a", 0.35, 0.2)
	else:
		_sprite.modulate.a = 1.0


func _on_revived() -> void:
	state = State.DRIFT
	_cool = 1.0
	_ghost(true)
	play(&"move")
