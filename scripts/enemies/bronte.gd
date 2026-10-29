class_name Bronte
extends Enemy

const SHEET := "res://assets/sprites/enemies/bronte.json"

enum State { WALK, WINDUP, THROW }

var speed := 20.0
var sight := 280.0
var sight_y := 200.0
var warn := 0.6
var every := 2.2
var fuse := 0.9
var blast_radius := 26.0
var too_close := 40.0
var max_lead := 96.0

var state := State.WALK
var _timer := 0.0
var _cool := 0.0


static func create(def: Dictionary, feet: Vector2, in_room: String) -> Bronte:
	var cyclops := Bronte.new()
	cyclops.position = feet
	cyclops.room_id = in_room
	cyclops.every = float(def.get("every", cyclops.every))
	cyclops.fuse = float(def.get("fuse", cyclops.fuse))
	cyclops.blast_radius = float(def.get("radius", cyclops.blast_radius))
	cyclops.sight = float(def.get("sight", cyclops.sight))
	cyclops.sight_y = float(def.get("sight_y", cyclops.sight_y))
	cyclops.facing = int(def.get("dir", "-1"))
	return cyclops


func _ready() -> void:
	super()
	var box := RectangleShape2D.new()
	box.size = Vector2(12, 13)
	setup_body(SHEET, &"move", Vector2(0, -15), box, Vector2(0, -7))
	face(facing)


func _physics_process(delta: float) -> void:
	if not is_active():
		return
	_timer -= delta
	_cool -= delta
	var player := target()
	match state:
		State.WALK:
			if player and _in_sight(player):
				var dx := player.global_position.x - global_position.x
				face(int(signf(dx)))
				if absf(dx) < too_close and not blocked(-facing, 10.0):
					position.x -= facing * speed * delta
					play(&"move")
				else:
					_sprite.pause()
				if _cool <= 0.0:
					state = State.WINDUP
					_timer = Combat.telegraph_time(warn)
					strip(&"windup", 0, 2, _timer)
					AudioManager.play_sfx(&"fuse", -8.0, 0.08)
				return
			if blocked(facing, 10.0):
				face(-facing)
			position.x += facing * speed * delta
			play(&"move")
		State.WINDUP:
			if player:
				face(int(signf(player.global_position.x - global_position.x)))
			if _timer <= 0.0:
				state = State.THROW
				_timer = 0.4
				_cool = every
				strip(&"attack", 0, 2, 0.3)
				_throw(player)
		State.THROW:
			if _timer <= 0.0:
				state = State.WALK


func _in_sight(player: Player) -> bool:
	var d := player.global_position - global_position
	return absf(d.x) < sight and absf(d.y) < sight_y


func _throw(player: Player) -> void:
	var hand := global_position + Vector2(facing * 9.0, -16.0)
	var goal := player.global_position if player else hand + Vector2(facing * 80.0, 16.0)
	var flight := clampf(absf(goal.x - hand.x) / 120.0, 0.55, 1.1)
	if player:
		goal.x += clampf(player.velocity.x * flight, -max_lead, max_lead)
		flight = clampf(absf(goal.x - hand.x) / 120.0, 0.55, 1.1)
	var vel := Vector2((goal.x - hand.x) / flight, (goal.y - hand.y - 0.5 * ThunderBomb.GRAVITY * flight * flight) / flight)
	ThunderBomb.throw(get_parent(), hand, vel, fuse, blast_radius)
	AudioManager.play_sfx(&"swoop", -6.0, 0.1)


func _on_revived() -> void:
	state = State.WALK
	_cool = 0.2
	play(&"move")
