class_name Spikes
extends Area2D

const TEXTURE := preload("res://assets/sprites/props/spikes.png")
const HAZARD_LAYER := 4
const ANGLES := {"^": 0.0, ">": PI * 0.5, "v": PI, "<": -PI * 0.5}


static func create(direction: String, center: Vector2, sink := 0.0) -> Spikes:
	var spikes := Spikes.new()
	spikes.position = center
	spikes.rotation = ANGLES[direction]
	spikes.collision_layer = HAZARD_LAYER
	spikes.collision_mask = 0
	spikes.monitoring = false
	var sprite := Sprite2D.new()
	sprite.texture = TEXTURE
	sprite.region_enabled = true
	sprite.region_rect = Rect2(16 * posmod(floori(center.x / 16.0) + floori(center.y / 16.0), 2), 0, 16, 16)
	sprite.material = Lights.unshaded()
	sprite.position.y = sink
	spikes.add_child(sprite)
	var box := RectangleShape2D.new()
	box.size = Vector2(12, 7)
	var shape := CollisionShape2D.new()
	shape.shape = box
	shape.position = Vector2(0, 4.5)
	spikes.add_child(shape)
	return spikes
