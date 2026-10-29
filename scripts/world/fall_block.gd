class_name FallBlock
extends AnimatableBody2D

enum State { IDLE, SHAKING, FALLING, GONE }

const TEXTURE := preload("res://assets/sprites/props/fall_block.png")
const TILE := 16
const PLAYER_LAYER := 2

@export var shake_time := 0.45
@export var gravity := 700.0
@export var max_speed := 230.0
@export var fall_time := 2.2
@export var respawn_time := 3.0

var state := State.IDLE

var _tiles := 1
var _origin := Vector2.ZERO
var _timer := 0.0
var _speed := 0.0
var _visual: Node2D
var _shape: CollisionShape2D


static func create(tiles: int, top_left: Vector2) -> FallBlock:
	var block := FallBlock.new()
	block.position = top_left
	block._tiles = maxi(1, tiles)
	return block


func _ready() -> void:
	sync_to_physics = false
	collision_layer = Combat.WORLD_LAYER
	collision_mask = Combat.WORLD_LAYER
	_origin = position
	add_to_group(World.RESET_GROUP)
	var width := _tiles * TILE
	_visual = Node2D.new()
	add_child(_visual)
	for i in _tiles:
		var part := 1
		if _tiles > 1:
			part = 0 if i == 0 else (2 if i == _tiles - 1 else 1)
		var region := AtlasTexture.new()
		region.atlas = TEXTURE
		region.region = Rect2(part * TILE, 0, TILE, TILE)
		var sprite := Sprite2D.new()
		sprite.texture = region
		sprite.centered = false
		sprite.position.x = i * TILE
		_visual.add_child(sprite)
	var box := RectangleShape2D.new()
	box.size = Vector2(width, TILE)
	_shape = CollisionShape2D.new()
	_shape.shape = box
	_shape.position = Vector2(width, TILE) * 0.5
	add_child(_shape)
	var sensor := Area2D.new()
	sensor.collision_layer = 0
	sensor.collision_mask = PLAYER_LAYER
	var sensor_box := RectangleShape2D.new()
	sensor_box.size = Vector2(width + 6, TILE + 6)
	var sensor_shape := CollisionShape2D.new()
	sensor_shape.shape = sensor_box
	sensor_shape.position = Vector2(width, TILE) * 0.5
	sensor.add_child(sensor_shape)
	add_child(sensor)
	sensor.body_entered.connect(_on_touched)


func _on_touched(body: Node2D) -> void:
	var player := body as Player
	if state != State.IDLE or player == null:
		return
	var on_top := player.global_position.y <= global_position.y + 2.0 and player.velocity.y >= 0.0
	if on_top or player.is_dashing:
		trigger()


func trigger() -> void:
	if state != State.IDLE:
		return
	state = State.SHAKING
	_timer = Combat.telegraph_time(shake_time)
	AudioManager.play_sfx(&"crumble", -4.0, 0.1)


func _physics_process(delta: float) -> void:
	match state:
		State.SHAKING:
			_timer -= delta
			_visual.position = Vector2(randi_range(-1, 1), 0)
			if _timer <= 0.0:
				_visual.position = Vector2.ZERO
				state = State.FALLING
				_timer = fall_time
				_speed = 0.0
		State.FALLING:
			_timer -= delta
			_speed = minf(max_speed, _speed + gravity * delta)
			var step := Vector2(0, _speed * delta)
			if test_move(global_transform, step) or _timer <= 0.0:
				_break()
			else:
				position += step
		State.GONE:
			_timer -= delta
			if _timer <= 0.0 and not _player_in_way():
				_restore()


func _break() -> void:
	state = State.GONE
	_timer = respawn_time
	_shape.set_deferred(&"disabled", true)
	AudioManager.play_sfx(&"clank", -8.0, 0.15)
	Combat.burst(get_parent(), global_position + Vector2(_tiles * TILE * 0.5, TILE * 0.5), Color("#eadfd0"), 10, 70.0)
	var tween := create_tween()
	tween.tween_property(_visual, "modulate:a", 0.0, 0.15)


func _restore() -> void:
	state = State.IDLE
	position = _origin
	_shape.set_deferred(&"disabled", false)
	_visual.modulate.a = 0.0
	create_tween().tween_property(_visual, "modulate:a", 1.0, 0.35)


func reset_on_death() -> void:
	state = State.IDLE
	position = _origin
	_speed = 0.0
	_shape.set_deferred(&"disabled", false)
	_visual.position = Vector2.ZERO
	_visual.modulate.a = 1.0


func _player_in_way() -> bool:
	var player := Combat.find_player(self)
	if player == null:
		return false
	var area := Rect2(get_parent().to_global(_origin) + Vector2(-1, -1), Vector2(_tiles * TILE + 2, TILE + 2))
	var body := Rect2(player.global_position + Vector2(-4, -17), Vector2(8, 17))
	return area.intersects(body)
