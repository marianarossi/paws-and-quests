class_name Balanos
extends Enemy

const SHEET := "res://assets/sprites/enemies/balanos.json"
const GRAVITY := 600.0
const MAX_FALL := 240.0

var speed := 26.0
var turn_at_edges := false

var _vy := 0.0


static func create(def: Dictionary, feet: Vector2, in_room: String) -> Balanos:
	var nut := Balanos.new()
	nut.position = feet
	nut.room_id = in_room
	nut.speed = float(def.get("speed", nut.speed))
	nut.facing = int(def.get("dir", "-1"))
	nut.turn_at_edges = def.get("edge", "") == "turn"
	return nut


func _ready() -> void:
	super()
	var box := RectangleShape2D.new()
	box.size = Vector2(10, 10)
	setup_body(SHEET, &"move", Vector2(0, -15), box, Vector2(0, -5))
	face(facing)


func _physics_process(delta: float) -> void:
	if not is_active():
		return
	var ground := ground_below(global_position, maxf(_vy * delta, 0.0) + 2.0)
	if ground == INF:
		_vy = minf(_vy + GRAVITY * delta, MAX_FALL)
		position.y += _vy * delta
		if global_position.y > _home.y + 800.0:
			revive()
		return
	global_position.y = ground
	_vy = 0.0
	if wall_ahead(facing, 7.0) or (turn_at_edges and not floor_at(global_position + Vector2(facing * 7.0, 0))):
		face(-facing)
	position.x += facing * speed * delta
	play(&"move")


func _on_revived() -> void:
	_vy = 0.0
	play(&"move")
