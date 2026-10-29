class_name BeatCloud
extends StaticBody2D

const TEXTURE := preload("res://assets/sprites/props/beat_cloud.png")
const TILE := 16
const WARN := 0.4

static var _clock := 0.0
static var _clock_frame := -1
static var _last_beat := -1

var period := 1.6
var group := 0
var room_id := ""

var _tiles := 3
var _lit: Array[Sprite2D] = []
var _dim: Array[Sprite2D] = []
var _shape: CollisionShape2D
var _solid := true


static func create(def: Dictionary, tiles: int, top_left: Vector2, in_room: String) -> BeatCloud:
	var cloud := BeatCloud.new()
	cloud.position = top_left
	cloud._tiles = maxi(1, tiles)
	cloud.group = 1 if String(def.get("group", "a")).to_lower() == "b" else 0
	cloud.period = maxf(0.6, float(def.get("period", "1.6")))
	cloud.room_id = in_room
	return cloud


static func clock() -> float:
	return _clock


static func lit_group(t: float, beat_period: float) -> int:
	return int(floorf(t / beat_period)) % 2


func _ready() -> void:
	collision_layer = Combat.WORLD_LAYER
	collision_mask = 0
	for i in _tiles:
		var part := 0 if i == 0 else (2 if i == _tiles - 1 else 1)
		if _tiles == 1:
			part = 1
		_lit.append(_part(part, group * 2))
		_dim.append(_part(part, group * 2 + 1))
	var box := RectangleShape2D.new()
	box.size = Vector2(_tiles * TILE, 5)
	_shape = CollisionShape2D.new()
	_shape.shape = box
	_shape.position = Vector2(_tiles * TILE * 0.5, 2.5)
	_shape.one_way_collision = true
	add_child(_shape)
	_apply(lit_group(_clock, period) == group, 1.0)


func _part(part: int, row: int) -> Sprite2D:
	var region := AtlasTexture.new()
	region.atlas = TEXTURE
	region.region = Rect2(part * TILE, row * TILE, TILE, TILE)
	var sprite := Sprite2D.new()
	sprite.texture = region
	sprite.centered = false
	sprite.position = Vector2((_lit.size() if row % 2 == 0 else _dim.size()) * TILE, -TerrainTiles.PLATFORM_ART_TOP)
	add_child(sprite)
	return sprite


func _physics_process(delta: float) -> void:
	var frame := Engine.get_physics_frames()
	if frame != _clock_frame:
		_clock_frame = frame
		_clock += delta
		var beat := int(floorf(_clock / period))
		if beat != _last_beat:
			_last_beat = beat
			if Game.current_room == room_id:
				AudioManager.play_sfx(&"menu_move", -12.0, 0.0)
	var on := lit_group(_clock, period) == group
	var left := period - fmod(_clock, period)
	var alpha := 1.0
	if on and left < WARN:
		alpha = 0.35 if int(left * 12.5) % 2 == 0 else 1.0
	_apply(on, alpha)


func _apply(on: bool, alpha: float) -> void:
	if on != _solid:
		_solid = on
		_shape.set_deferred(&"disabled", not on)
	for sprite in _lit:
		sprite.visible = on
		sprite.modulate.a = alpha
	for sprite in _dim:
		sprite.visible = not on


func is_solid() -> bool:
	return _solid
