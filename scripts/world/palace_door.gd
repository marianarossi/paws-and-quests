class_name PalaceDoor
extends Node2D

const ART := "res://assets/sprites/props/"
const GROUP := &"slam_door"
const SLAM_TIME := 0.16
const WALL_W := 224
const DOOR_X := 72

var _left: Sprite2D
var _right: Sprite2D
var _light: PointLight2D
var _door := Vector2.ZERO
var _closed := false


static func create(top_left: Vector2) -> PalaceDoor:
	var door := PalaceDoor.new()
	door.position = top_left + Vector2(0, Room.TILE)
	return door


func _ready() -> void:
	add_to_group(GROUP)
	z_index = -1
	var wall: Texture2D = load(ART + "palace_door.png")
	var leaf: Texture2D = load(ART + "gate_door_l.png")
	_door = Vector2(DOOR_X, -leaf.get_height())
	var outside := _sprite("palace_outside", _door)
	outside.material = Lights.unshaded()
	var half := leaf.get_width()
	_left = _sprite("gate_door_l", _door + Vector2(-half + 3, 0))
	_right = _sprite("gate_door_r", _door + Vector2(half * 2 - 3, 0))
	_sprite("palace_door", Vector2(0, -wall.get_height()))
	_light = Lights.point(Color(1.0, 0.78, 0.7), 120.0, 0.9)
	_light.position = _door + Vector2(half, leaf.get_height() * 0.6)
	add_child(_light)


func slam() -> void:
	if _closed:
		return
	_closed = true
	var half := float(_left.texture.get_width())
	var tween := create_tween().set_parallel().set_trans(Tween.TRANS_EXPO).set_ease(Tween.EASE_IN)
	tween.tween_property(_left, "position", _door, SLAM_TIME)
	tween.tween_property(_right, "position", _door + Vector2(half, 0), SLAM_TIME)
	tween.tween_property(_light, "energy", 0.0, SLAM_TIME)
	tween.chain().tween_callback(func() -> void: AudioManager.play_sfx(&"door_slam", 0.0, 0.0))


func _sprite(file: String, at: Vector2) -> Sprite2D:
	var sprite := Sprite2D.new()
	sprite.texture = load(ART + file + ".png")
	sprite.centered = false
	sprite.position = at
	add_child(sprite)
	return sprite
