class_name Harpy
extends Enemy

const SHEET := "res://assets/sprites/enemies/harpy.json"

enum State { FLY, SCREECH, SHAKE }

var span := 130.0
var dip := 40.0
var crossing := 3.2
var every := 2.4
var warn := 0.5
var feathers := 3
var feather_speed := 105.0

var state := State.FLY
var _timer := 0.0
var _cool := 1.0
var _phase := 0.0


static func create(def: Dictionary, center: Vector2, in_room: String) -> Harpy:
	var bird := Harpy.new()
	bird.position = center
	bird.room_id = in_room
	bird.span = float(def.get("span", bird.span))
	bird.feathers = int(def.get("feathers", bird.feathers))
	return bird


func _ready() -> void:
	super()
	var circle := CircleShape2D.new()
	circle.radius = 7.0
	setup_body(SHEET, &"move", Vector2(0, 1), circle, Vector2.ZERO)


func _physics_process(delta: float) -> void:
	if not is_active():
		return
	_timer -= delta
	_cool -= delta
	var slow := 0.55 if state != State.FLY else 1.0
	_phase += delta * PI / crossing * slow
	var x := -cos(_phase) * span
	var y := (1.0 - absf(cos(_phase))) * dip
	var before := position.x
	position = _home + Vector2(x, y)
	face(int(signf(position.x - before)) if absf(position.x - before) > 0.01 else facing)
	var player := target()
	match state:
		State.FLY:
			play(&"move")
			if player and _cool <= 0.0:
				var d := player.global_position - global_position
				if absf(d.x) < 70.0 and d.y > 10.0 and d.y < 160.0:
					state = State.SCREECH
					_timer = Combat.telegraph_time(warn)
					strip(&"attack", 0, 1, _timer)
					AudioManager.play_sfx(&"screech", -4.0, 0.1)
		State.SCREECH:
			if _timer <= 0.0:
				state = State.SHAKE
				_timer = 0.3
				strip(&"attack", 2, 4, 0.3)
				_shake(player)
		State.SHAKE:
			if _timer <= 0.0:
				state = State.FLY
				_cool = every


func _shake(player: Player) -> void:
	var down := (Combat.aim_point(player) - global_position).normalized() if player else Vector2.DOWN
	if down.y < 0.4:
		down = Vector2(signf(down.x) * 0.9, 0.45).normalized()
	for k in feathers:
		var spread := deg_to_rad(-30.0 + 60.0 * k / maxf(feathers - 1, 1))
		EnemyShot.fire(get_parent(), &"feather", global_position + Vector2(0, 6), down.rotated(spread) * feather_speed, {"life": 3.0, "radius": 3.0})
	AudioManager.play_sfx(&"shot", -4.0, 0.1)


func _on_revived() -> void:
	state = State.FLY
	_cool = 1.0
	_phase = 0.0
	play(&"move")
