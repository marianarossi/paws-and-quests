class_name MinotaurCalf
extends Enemy

const SHEET := "res://assets/sprites/enemies/minotaur_calf.json"

enum State { WALK, WINDUP, CHARGE, SKID, STUN }

var walk_speed := 18.0
var charge_speed := 170.0
var sight := 160.0
var warn := 0.7
var stun_time := 1.6

var state := State.WALK
var _timer := 0.0
var _alerted := false
var _speed := 0.0


static func create(def: Dictionary, feet: Vector2, in_room: String) -> MinotaurCalf:
	var calf := MinotaurCalf.new()
	calf.position = feet
	calf.room_id = in_room
	calf.charge_speed = float(def.get("charge", calf.charge_speed))
	calf.facing = int(def.get("dir", "-1"))
	return calf


func _ready() -> void:
	super()
	var box := RectangleShape2D.new()
	box.size = Vector2(20, 16)
	setup_body(SHEET, &"move", Vector2(2, -15), box, Vector2(1, -9))
	face(facing)


func _physics_process(delta: float) -> void:
	if not is_active():
		return
	_timer -= delta
	var player := target()
	match state:
		State.WALK:
			play(&"move")
			if player and _sees(player):
				_alerted = true
				face(int(signf(player.global_position.x - global_position.x)))
				if _timer <= 0.0:
					state = State.WINDUP
					_timer = Combat.telegraph_time(warn)
					play(&"windup")
					AudioManager.play_sfx(&"snort", -2.0, 0.08)
					return
			if not floor_at(global_position):
				return
			if blocked(facing, 14.0):
				face(-facing)
			position.x += facing * walk_speed * delta
		State.WINDUP:
			if _timer <= 0.0:
				state = State.CHARGE
				_speed = charge_speed
				play(&"attack")
				AudioManager.play_sfx(&"charge", -4.0, 0.06)
		State.CHARGE:
			if clear_distance(global_position + Vector2(0, -8), Vector2(facing, 0), 14.0) < 14.0:
				_crash()
			elif not floor_at(global_position + Vector2(facing * 12.0, 0)):
				state = State.SKID
				_timer = 0.35
			else:
				position.x += facing * _speed * delta
		State.SKID:
			_speed = move_toward(_speed, 0.0, charge_speed * 4.0 * delta)
			if floor_at(global_position + Vector2(facing * 6.0, 0)):
				position.x += facing * _speed * delta
			if _timer <= 0.0:
				state = State.WALK
				_timer = 0.8
				face(-facing)
		State.STUN:
			if _timer <= 0.0:
				state = State.WALK
				_timer = 0.5


func _sees(player: Player) -> bool:
	var d := player.global_position - global_position
	if absf(d.y) > 24.0 or absf(d.x) > sight:
		return false
	return _alerted or signf(d.x) == facing


func _crash() -> void:
	state = State.STUN
	_timer = Combat.telegraph_time(stun_time)
	position.x -= facing * 4.0
	play(&"stun")
	AudioManager.play_sfx(&"hit", 0.0, 0.05)
	Combat.burst(get_parent(), global_position + Vector2(facing * 12.0, -10.0), Color.WHITE, 10, 120.0)


func _on_revived() -> void:
	state = State.WALK
	_alerted = false
	_timer = 0.0
	play(&"move")
