class_name Frog
extends Node2D

const SHEET := preload("res://assets/sprites/props/frog.png")
const FRAME := Vector2(10, 8)
const SIT := 0
const CROUCH := 1
const LEAP := 2
const CROUCH_TIME := 0.14
const HOP_TIME := 0.42

var _min_x := 0.0
var _max_x := 0.0
var _ground_y := 0.0
var _rng := RandomNumberGenerator.new()
var _sprite: Sprite2D
var _wait := 0.0
var _hop := -1.0
var _from_x := 0.0
var _to_x := 0.0
var _height := 8.0


static func create(feet: Vector2, min_x: float, max_x: float, seed_value: int) -> Frog:
	var frog := Frog.new()
	frog.position = feet
	frog._ground_y = feet.y
	frog._min_x = min_x
	frog._max_x = max_x
	frog._rng.seed = seed_value
	return frog


func _ready() -> void:
	z_index = 2
	_sprite = Sprite2D.new()
	_sprite.texture = SHEET
	_sprite.centered = false
	_sprite.region_enabled = true
	_sprite.position = Vector2(-FRAME.x * 0.5, -FRAME.y + 1.0)
	_sprite.flip_h = _rng.randf() < 0.5
	add_child(_sprite)
	_show(SIT)
	_wait = _rng.randf_range(0.5, 5.0)


func _process(delta: float) -> void:
	if _hop < 0.0:
		_wait -= delta
		if _wait <= 0.0:
			_start_hop()
		elif _wait < CROUCH_TIME:
			_show(CROUCH)
		return
	_hop += delta / HOP_TIME
	if _hop >= 1.0:
		_hop = -1.0
		position = Vector2(_to_x, _ground_y)
		_show(SIT)
		_wait = _rng.randf_range(1.4, 5.5)
		return
	position = Vector2(lerpf(_from_x, _to_x, _hop), _ground_y - _height * 4.0 * _hop * (1.0 - _hop)).round()
	_show(LEAP if _hop < 0.8 else CROUCH)


func _start_hop() -> void:
	var direction := 1.0 if _rng.randf() < 0.5 else -1.0
	var distance := _rng.randf_range(10.0, 26.0)
	if position.x + direction * distance < _min_x or position.x + direction * distance > _max_x:
		direction = -direction
	_from_x = position.x
	_to_x = clampf(position.x + direction * distance, _min_x, _max_x)
	_height = _rng.randf_range(6.0, 11.0)
	_sprite.flip_h = direction < 0.0
	_hop = 0.0


func _show(frame: int) -> void:
	_sprite.region_rect = Rect2(frame * FRAME.x, 0, FRAME.x, FRAME.y)
