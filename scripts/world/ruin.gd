class_name Ruin
extends StaticBody2D

const TILE := 16


static func create(def: Dictionary, top_left: Vector2) -> Ruin:
	var ruin := Ruin.new()
	ruin.position = top_left
	ruin.collision_layer = Combat.WORLD_LAYER
	ruin.collision_mask = 0
	ruin.z_index = -1
	var texture: Texture2D = load("res://assets/sprites/props/" + String(def.get("file", "")))
	var art := Sprite2D.new()
	art.texture = texture
	art.centered = false
	ruin.add_child(art)
	var size := Vector2(floori(texture.get_width() / float(TILE)), floori(texture.get_height() / float(TILE))) * TILE
	var box := RectangleShape2D.new()
	box.size = size
	var shape := CollisionShape2D.new()
	shape.shape = box
	shape.position = size * 0.5
	ruin.add_child(shape)
	return ruin
