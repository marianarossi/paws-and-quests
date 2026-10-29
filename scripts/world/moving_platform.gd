class_name MovingPlatform
extends AnimatableBody2D

const ATLAS := preload("res://assets/tiles/forest_platform.png")
const TILE := 16

var travel := Vector2.ZERO
var period := 2.0

var _tiles := 3
var _origin := Vector2.ZERO
var _time := 0.0


static func create(tiles: int, top_left: Vector2, travel_px: Vector2, period_s: float) -> MovingPlatform:
	var platform := MovingPlatform.new()
	platform.position = top_left
	platform._tiles = tiles
	platform.travel = travel_px
	platform.period = maxf(0.2, period_s)
	return platform


func _ready() -> void:
	sync_to_physics = true
	_origin = position
	for i in _tiles:
		var part := 0 if i == 0 else (2 if i == _tiles - 1 else 1)
		var region := AtlasTexture.new()
		region.atlas = ATLAS
		region.region = Rect2(part * TILE, 0, TILE, TILE)
		var sprite := Sprite2D.new()
		sprite.texture = region
		sprite.centered = false
		sprite.position = Vector2(i * TILE, -TerrainTiles.PLATFORM_ART_TOP)
		add_child(sprite)
	var box := RectangleShape2D.new()
	box.size = Vector2(_tiles * TILE, 5)
	var shape := CollisionShape2D.new()
	shape.shape = box
	shape.position = Vector2(_tiles * TILE * 0.5, 2.5)
	shape.one_way_collision = true
	add_child(shape)


func _physics_process(delta: float) -> void:
	_time += delta
	position = _origin + travel * smoothstep(0.0, 1.0, pingpong(_time / period, 1.0))
