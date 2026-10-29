class_name Gate
extends Node2D

signal opened
signal entered

const ART := "res://assets/sprites/props/"
const OPEN_TIME := 2.8
const APPROACH := 120.0

@export var open_on_approach := true
@export var to := ""

var _left: Sprite2D
var _right: Sprite2D
var _door := Rect2()
var _origin := Vector2.ZERO
var _is_open := false
var _progress := -1.0
var _was_inside := false


static func create(feet: Vector2, to_room := "") -> Gate:
	var gate := Gate.new()
	gate.position = feet
	gate.to = to_room
	return gate


func _ready() -> void:
	var data: Dictionary = (load(ART + "gate.json") as JSON).data
	var door: Array = data["door"]
	_door = Rect2(door[0], door[1], door[2], door[3])
	_origin = Vector2(-float(data["feet_x"]), -float(data["size"][1]))
	z_index = 0
	_sprite("gate_back", _origin + _door.position)
	_left = _sprite("gate_door_l", _origin + _door.position)
	_right = _sprite("gate_door_r", _origin + _door.position + Vector2(_door.size.x * 0.5, 0))
	_sprite("gate_main", _origin)


func is_open() -> bool:
	return _is_open


func open() -> void:
	if _is_open:
		return
	_is_open = true
	_progress = 0.0
	AudioManager.play_sfx(&"gate_open")
	var camera := get_viewport().get_camera_2d()
	if camera and camera.has_method(&"shake"):
		camera.call(&"shake", 1.5, OPEN_TIME)


func _physics_process(delta: float) -> void:
	var player := get_tree().get_first_node_in_group(Combat.PLAYER_GROUP) as Node2D
	if player == null:
		return
	var offset := player.global_position - global_position
	if open_on_approach and not _is_open and absf(offset.x) < APPROACH and offset.y > -_door.size.y and offset.y < 24.0:
		open()
	var inside := _is_open and _progress < 0.0 and absf(offset.x) < _door.size.x * 0.3 and offset.y > -_door.size.y and offset.y < 8.0
	if inside and not _was_inside:
		entered.emit()
		if to != "":
			Events.door_entered.emit(to)
	_was_inside = inside
	if _progress < 0.0:
		return
	_progress = minf(1.0, _progress + delta / OPEN_TIME)
	var eased := _progress * _progress * (3.0 - 2.0 * _progress)
	var half := _door.size.x * 0.5
	var slide := roundf((half - 3.0) * eased)
	_left.position = _origin + _door.position + Vector2(-slide, 0)
	_right.position = _origin + _door.position + Vector2(half + slide, 0)
	if _progress >= 1.0:
		_progress = -1.0
		opened.emit()


func _sprite(file: String, at: Vector2) -> Sprite2D:
	var sprite := Sprite2D.new()
	sprite.texture = load(ART + file + ".png")
	sprite.centered = false
	sprite.position = at
	add_child(sprite)
	return sprite
