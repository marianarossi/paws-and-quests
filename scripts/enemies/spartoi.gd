class_name Spartoi
extends Enemy

const SHEET := "res://assets/sprites/enemies/spartoi.json"

enum State { BURIED, RISE, WALK, WINDUP, THROW }

var wake := 100.0
var speed := 22.0
var throw_range := 170.0
var every := 2.4
var warn := 0.6
var spears: Array[Vector2] = [Vector2(95.0, -175.0), Vector2(150.0, -125.0), Vector2(215.0, -70.0)]

var state := State.BURIED
var _timer := 0.0
var _cool := 0.8


static func create(def: Dictionary, feet: Vector2, in_room: String) -> Spartoi:
	var bones := Spartoi.new()
	bones.position = feet
	bones.room_id = in_room
	bones.wake = float(def.get("wake", bones.wake))
	bones.facing = int(def.get("dir", "-1"))
	return bones


func _ready() -> void:
	super()
	var box := RectangleShape2D.new()
	box.size = Vector2(8, 20)
	setup_body(SHEET, &"rise", Vector2(0, -15), box, Vector2(0, -11))
	face(facing)
	_bury()


func _physics_process(delta: float) -> void:
	if Game.current_room != room_id:
		return
	_timer -= delta
	if not alive:
		return
	_cool -= delta
	var player := target()
	match state:
		State.BURIED:
			if player and global_position.distance_to(player.global_position) < wake:
				_rise()
		State.RISE:
			if _timer < 0.35:
				monitorable = true
			if _timer <= 0.0:
				state = State.WALK
				play(&"move")
		State.WALK:
			if not player:
				_sprite.pause()
				return
			var dx := player.global_position.x - global_position.x
			face(int(signf(dx)))
			if _cool <= 0.0 and absf(dx) < throw_range and absf(player.global_position.y - global_position.y) < 48.0:
				state = State.WINDUP
				_timer = Combat.telegraph_time(warn)
				play(&"windup")
				return
			if absf(dx) > 44.0 and not blocked(facing, 8.0):
				position.x += facing * speed * delta
				play(&"move")
			else:
				_sprite.pause()
		State.WINDUP:
			if _timer <= 0.0:
				state = State.THROW
				_timer = 0.4
				_cool = every
				play(&"attack")
				for v in spears:
					EnemyShot.fire(get_parent(), &"bone_spear", global_position + Vector2(facing * 8.0, -13.0),
							Vector2(facing * v.x, v.y), {"gravity": 330.0, "life": 3.0, "radius": 2.5})
				AudioManager.play_sfx(&"twang", -4.0, 0.12)
		State.THROW:
			if _timer <= 0.0:
				state = State.WALK


func _bury() -> void:
	state = State.BURIED
	visible = true
	set_deferred(&"monitorable", false)
	_sprite.play(&"rise")
	_sprite.pause()
	_sprite.frame = 0


func _rise() -> void:
	state = State.RISE
	_timer = 0.65
	alive = true
	visible = true
	_sprite.position = _sprite_base * Vector2(facing, 1)
	play(&"rise")
	AudioManager.play_sfx(&"crumble", -8.0, 0.1)


func _on_revived() -> void:
	_cool = 0.8
	_bury()
