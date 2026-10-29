class_name CrumblePlatform
extends StaticBody2D

enum State { IDLE, SHAKING, GONE }

const TEXTURE := preload("res://assets/sprites/props/crumble.png")
const TILE := 16
const PLAYER_LAYER := 2

@export var shake_time := 0.4
@export var respawn_time := 2.4

var _tiles := 1
var _state := State.IDLE
var _timer := 0.0
var _visual: Node2D
var _shape: CollisionShape2D


static func create(tiles: int, top_left: Vector2) -> CrumblePlatform:
	var platform := CrumblePlatform.new()
	platform.position = top_left
	platform._tiles = tiles
	return platform


func _ready() -> void:
	var width := _tiles * TILE
	_visual = Node2D.new()
	add_child(_visual)
	for i in _tiles:
		var sprite := Sprite2D.new()
		sprite.texture = TEXTURE
		sprite.centered = false
		sprite.position.x = i * TILE
		_visual.add_child(sprite)
	var box := RectangleShape2D.new()
	box.size = Vector2(width, 6)
	_shape = CollisionShape2D.new()
	_shape.shape = box
	_shape.position = Vector2(width * 0.5, 3)
	_shape.one_way_collision = true
	add_child(_shape)
	var sensor := Area2D.new()
	sensor.collision_layer = 0
	sensor.collision_mask = PLAYER_LAYER
	var sensor_box := RectangleShape2D.new()
	sensor_box.size = Vector2(width - 4, 4)
	var sensor_shape := CollisionShape2D.new()
	sensor_shape.shape = sensor_box
	sensor_shape.position = Vector2(width * 0.5, -2)
	sensor.add_child(sensor_shape)
	add_child(sensor)
	sensor.body_entered.connect(_on_stepped)


func _on_stepped(body: Node2D) -> void:
	var player := body as Player
	if _state == State.IDLE and player != null and player.velocity.y >= 0.0:
		_state = State.SHAKING
		_timer = shake_time


func _physics_process(delta: float) -> void:
	if _state == State.IDLE:
		return
	_timer -= delta
	if _state == State.SHAKING:
		_visual.position = Vector2(randi_range(-1, 1), 0)
		if _timer <= 0.0:
			_collapse()
	elif _timer <= 0.0:
		_restore()


func _collapse() -> void:
	_state = State.GONE
	_timer = respawn_time
	_shape.set_deferred(&"disabled", true)
	AudioManager.play_sfx(&"crumble")
	var tween := create_tween().set_parallel()
	tween.tween_property(_visual, "position:y", 28.0, 0.3).set_ease(Tween.EASE_IN).set_trans(Tween.TRANS_QUAD)
	tween.tween_property(_visual, "modulate:a", 0.0, 0.3)


func _restore() -> void:
	_state = State.IDLE
	_visual.position = Vector2.ZERO
	_shape.set_deferred(&"disabled", false)
	create_tween().tween_property(_visual, "modulate:a", 1.0, 0.2)
