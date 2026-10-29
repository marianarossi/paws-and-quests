class_name Vista
extends Node2D

const TILE := 16

var from_x := 0.0
var to_x := 0.0
var amount := 0.5
var room_id := ""

var _inside := false


static func create(def: Dictionary, in_room: String) -> Vista:
	var vista := Vista.new()
	vista.from_x = float(def.get("from", "0")) * TILE
	vista.to_x = float(def.get("to", "0")) * TILE
	vista.amount = clampf(float(def.get("zoom", "0.5")), 0.25, 1.0)
	vista.room_id = in_room
	return vista


func _physics_process(_delta: float) -> void:
	var camera := get_viewport().get_camera_2d() as RoomCamera
	if camera == null:
		return
	var player := Combat.find_player(self)
	var inside := false
	if player and Game.current_room == room_id and not player.seated:
		var px: float = player.global_position.x - (get_parent() as Node2D).global_position.x
		inside = px >= from_x and px <= to_x
	if inside == _inside:
		return
	_inside = inside
	camera.held = inside
	if inside:
		camera.zoom_to(amount, 1.6)
	else:
		camera.release_zoom(1.0)


func _exit_tree() -> void:
	if _inside:
		var camera := get_viewport().get_camera_2d() as RoomCamera
		if camera:
			camera.held = false
			camera.release_zoom(0.6)
