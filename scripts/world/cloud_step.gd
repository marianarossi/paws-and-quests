class_name CloudStep
extends StaticBody2D

const TEXTURE := preload("res://assets/sprites/props/cloud_step.png")
const TILE := 16
const FADE := 0.4

static var _jumps: Dictionary[String, int] = {}
static var _started: Dictionary[String, bool] = {}

var order := 0
var near := 72.0
var room_id := ""
var shown := false

var _tiles := 3
var _visual: Node2D
var _shape: CollisionShape2D
var _player: Player


static func create(def: Dictionary, tiles: int, top_left: Vector2, in_room: String) -> CloudStep:
	var step := CloudStep.new()
	step.position = top_left
	step._tiles = maxi(1, tiles)
	step.order = int(def.get("order", "0"))
	step.near = float(def.get("near", "72"))
	step.room_id = in_room
	return step


static func reset_all() -> void:
	_jumps.clear()
	_started.clear()


func _ready() -> void:
	collision_layer = Combat.WORLD_LAYER
	collision_mask = 0
	_visual = Node2D.new()
	add_child(_visual)
	for i in _tiles:
		var part := 0 if i == 0 else (2 if i == _tiles - 1 else 1)
		var region := AtlasTexture.new()
		region.atlas = TEXTURE
		region.region = Rect2(part * TILE, 0, TILE, TILE)
		var sprite := Sprite2D.new()
		sprite.texture = region
		sprite.centered = false
		sprite.position = Vector2(i * TILE, -TerrainTiles.PLATFORM_ART_TOP)
		_visual.add_child(sprite)
	var box := RectangleShape2D.new()
	box.size = Vector2(_tiles * TILE, 5)
	_shape = CollisionShape2D.new()
	_shape.shape = box
	_shape.position = Vector2(_tiles * TILE * 0.5, 2.5)
	_shape.one_way_collision = true
	_shape.disabled = true
	add_child(_shape)
	_visual.modulate.a = 0.0
	if _should_show():
		_show(false)


func _physics_process(_delta: float) -> void:
	if order == 0 and (_player == null or not is_instance_valid(_player)):
		_player = Combat.find_player(self)
		if _player:
			_player.jumped.connect(_on_jumped)
	if shown:
		return
	if _player == null:
		_player = Combat.find_player(self)
	if order == 0 and _player and Game.current_room == room_id \
			and absf(_player.global_position.x - global_position.x) < near + _tiles * TILE * 0.5:
		_started[room_id] = true
	if _should_show():
		_show(true)


func _on_jumped(_kind: StringName) -> void:
	if order == 0 and _started.get(room_id, false) and Game.current_room == room_id:
		_jumps[room_id] = _jumps.get(room_id, 0) + 1


func _should_show() -> bool:
	if not _started.get(room_id, false):
		return false
	return order == 0 or _jumps.get(room_id, 0) >= order


func _show(fade: bool) -> void:
	shown = true
	_shape.set_deferred(&"disabled", false)
	if fade:
		AudioManager.play_sfx(&"crystal", -10.0, 0.1)
		create_tween().tween_property(_visual, "modulate:a", 1.0, FADE)
	else:
		_visual.modulate.a = 1.0
