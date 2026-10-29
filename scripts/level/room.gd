class_name Room
extends Node2D

const TILE := 16

var data: RoomData
var bounds := Rect2()
var spawn_points: Array[Vector2] = []
var spawn_point := Vector2.ZERO


func nearest_spawn(to: Vector2) -> Vector2:
	var best := spawn_point
	for point in spawn_points:
		if point.distance_squared_to(to) < best.distance_squared_to(to):
			best = point
	return best


static func cell_to_feet(cell: Vector2i) -> Vector2:
	return Vector2(cell.x * TILE + TILE * 0.5, (cell.y + 1) * TILE)
