class_name Nephele
extends Enemy

const SHEET := "res://assets/sprites/enemies/nephele.json"

enum State { PASS, WAIT }

var span := 220.0
var speed := 60.0
var heights := 24.0
var pause := 1.4
var warn := 0.6
var sparks := 3
var fan := 50.0
var shot := ShotSpec.new()

var state := State.WAIT
var _timer := 0.4
var _dir := -1
var _armed := false
var _dropping := 0
var _drop_timer := 0.0


static func create(def: Dictionary, center: Vector2, in_room: String) -> Nephele:
	var cloud := Nephele.new()
	cloud.position = center
	cloud.room_id = in_room
	cloud.span = float(def.get("span", cloud.span))
	cloud.speed = float(def.get("speed", cloud.speed))
	cloud.sparks = int(def.get("sparks", cloud.sparks))
	cloud.fan = float(def.get("fan", cloud.fan))
	cloud.shot.speed = float(def.get("shot_speed", 90.0))
	cloud.shot.turn_rate = 0.0
	cloud.shot.homing_time = 0.0
	cloud.shot.lifetime = 4.0
	return cloud


func _ready() -> void:
	super()
	material = Lights.unshaded()
	var box := RectangleShape2D.new()
	box.size = Vector2(26, 14)
	setup_body(SHEET, &"move", Vector2(0, 2), box, Vector2(0, 0))
	_hide()
	_timer = 0.4


func _physics_process(delta: float) -> void:
	if not is_active():
		return
	_timer -= delta
	match state:
		State.WAIT:
			if _timer <= 0.0:
				_start_pass()
		State.PASS:
			position.x += _dir * speed * delta
			var player := target()
			if _armed and player:
				var ahead := (player.global_position.x - global_position.x) * _dir
				var lead := speed * Combat.telegraph_time(warn) + 8.0
				if ahead > 0.0 and ahead < lead and player.global_position.y > global_position.y:
					_armed = false
					_drop_timer = Combat.telegraph_time(warn)
					_dropping = sparks
					strip(&"windup", 0, 2, _drop_timer)
					AudioManager.play_sfx(&"charge", -6.0, 0.08)
			if _dropping > 0:
				_drop_timer -= delta
				if _drop_timer <= 0.0:
					_release()
			if (position.x - _home.x) * _dir > span:
				_fade_out()


func _start_pass() -> void:
	state = State.PASS
	_dir = -_dir
	position = _home + Vector2(-_dir * span, randf_range(-heights, heights))
	face(_dir)
	visible = true
	_armed = true
	_dropping = 0
	play(&"move")
	_sprite.modulate.a = 0.0
	var tween := create_tween()
	tween.tween_property(_sprite, "modulate:a", 1.0, 0.4)
	tween.tween_callback(func() -> void: set_deferred(&"monitorable", true))


func _release() -> void:
	_dropping = 0
	play(&"attack")
	var pool := ProjectilePool.of(self)
	for k in sparks:
		var a := -fan + 2.0 * fan * k / maxf(sparks - 1, 1)
		pool.spawn(global_position + Vector2(0, 10), Vector2.DOWN.rotated(deg_to_rad(a)), shot, target())
	AudioManager.play_sfx(&"shot", -4.0, 0.08)
	_after_drop.call_deferred()


func _after_drop() -> void:
	await get_tree().create_timer(0.4).timeout
	if state == State.PASS:
		play(&"move")


func _fade_out() -> void:
	state = State.WAIT
	_timer = pause + 0.4
	set_deferred(&"monitorable", false)
	var tween := create_tween()
	tween.tween_property(_sprite, "modulate:a", 0.0, 0.4)


func _hide() -> void:
	state = State.WAIT
	_timer = pause
	visible = false
	set_deferred(&"monitorable", false)


func _on_revived() -> void:
	_dir = -1
	_hide()
	_timer = 0.4
