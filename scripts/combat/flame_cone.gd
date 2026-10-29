class_name FlameCone
extends Area2D

const FLAME := Color("ff5fb0")
const FLAME_HOT := Color("ffd0ee")
const FLAME_DEEP := Color("c0297f")

var mouth := Vector2(9.0, -7.0)
var reach := 48.0
var spread := 11.0

var burning := false
var _dir := 1
var _time := 0.0
var _shape: ConvexPolygonShape2D


func _ready() -> void:
	collision_layer = Enemy.HAZARD_LAYER
	collision_mask = 0
	monitoring = false
	monitorable = false
	material = Lights.unshaded()
	_shape = ConvexPolygonShape2D.new()
	var shape := CollisionShape2D.new()
	shape.shape = _shape
	add_child(shape)


func ignite(on: bool, dir := 1) -> void:
	burning = on
	_dir = dir
	if on:
		var m := _mouth()
		var tip := m + Vector2(_dir * _length(), 0)
		_shape.set_point_cloud(PackedVector2Array([m + Vector2(0, -2), tip + Vector2(0, -spread), tip + Vector2(0, spread * 0.6), m + Vector2(0, 2)]))
	set_deferred(&"monitorable", on)
	queue_redraw()


func _physics_process(delta: float) -> void:
	if burning:
		_time += delta
		queue_redraw()


func _mouth() -> Vector2:
	return Vector2(mouth.x * _dir, mouth.y)


func _length() -> float:
	var from := global_position + _mouth()
	var ray := PhysicsRayQueryParameters2D.create(from, from + Vector2(_dir * reach, 0), Combat.WORLD_LAYER)
	var hit := get_world_2d().direct_space_state.intersect_ray(ray)
	return reach if hit.is_empty() else from.distance_to(hit["position"])


func _draw() -> void:
	if not burning:
		return
	var m := _mouth()
	var length := _length()
	var rng := RandomNumberGenerator.new()
	rng.seed = int(_time * 24.0)
	for k in 14:
		var t := rng.randf()
		var x := m.x + _dir * t * length
		var h := 2.0 + t * spread * rng.randf_range(0.6, 1.0)
		var y := m.y + rng.randf_range(-h, h * 0.6)
		var col := FLAME_HOT if t < 0.3 else (FLAME if t < 0.7 else FLAME_DEEP)
		var size := 3.0 if t < 0.6 else 2.0
		draw_rect(Rect2(Vector2(x, y).round(), Vector2(size, size)), col)
