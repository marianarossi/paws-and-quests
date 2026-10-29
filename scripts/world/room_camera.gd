class_name RoomCamera
extends Camera2D

signal transition_finished

@export var follow_speed := 9.0
@export var target_offset := Vector2(0, -24)

var target: Node2D
var bounds := Rect2()
var floor_zone := Vector3.ZERO

var _from := Vector2.ZERO
var _progress := 1.0
var _duration := 0.4
var _shake_left := 0.0
var _shake_total := 0.0
var _shake_strength := 0.0
var held := false
var _zoom_goal := 1.0
var _zoom_speed := 1.0


func _ready() -> void:
	process_callback = Camera2D.CAMERA2D_PROCESS_PHYSICS
	position_smoothing_enabled = false
	make_current()


func follow(new_target: Node2D, room_bounds: Rect2) -> void:
	target = new_target
	bounds = room_bounds
	_progress = 1.0
	global_position = _desired()
	reset_physics_interpolation()


func transition_to(room_bounds: Rect2, duration := 0.4) -> void:
	bounds = room_bounds
	_from = global_position
	_duration = duration
	_progress = 0.0


func focus_zoom(amount: float) -> void:
	_zoom_goal = amount
	zoom = Vector2.ONE * amount


func zoom_to(amount: float, duration := 1.5) -> void:
	_zoom_speed = absf(amount - zoom.x) / maxf(0.1, duration)
	_zoom_goal = amount


func release_zoom(duration := 1.8) -> void:
	_zoom_speed = absf(zoom.x - 1.0) / maxf(0.1, duration)
	_zoom_goal = 1.0


func is_zoomed() -> bool:
	return _zoom_goal != 1.0


func shake(strength: float, duration: float) -> void:
	_shake_strength = strength
	_shake_total = duration
	_shake_left = duration


func _physics_process(delta: float) -> void:
	if target == null:
		return
	if zoom.x != _zoom_goal:
		zoom = Vector2.ONE * move_toward(zoom.x, _zoom_goal, _zoom_speed * delta)
	if _progress < 1.0:
		_progress = minf(1.0, _progress + delta / _duration)
		global_position = _from.lerp(_desired(), ease(_progress, -2.5))
		if _progress >= 1.0:
			transition_finished.emit()
	else:
		global_position = _clamped(global_position.lerp(_desired(), 1.0 - exp(-follow_speed * delta)))
	if _shake_left > 0.0:
		_shake_left -= delta
		var amount := _shake_strength * maxf(0.0, _shake_left / _shake_total)
		offset = Vector2(randf_range(-amount, amount), randf_range(-amount, amount)).round()
	else:
		offset = Vector2.ZERO


func _desired() -> Vector2:
	return _clamped(target.global_position + target_offset)


func _clamped(point: Vector2) -> Vector2:
	var half := get_viewport_rect().size * 0.5 / zoom
	if bounds.size.x <= half.x * 2.0:
		point.x = bounds.get_center().x
	else:
		point.x = clampf(point.x, bounds.position.x + half.x, bounds.end.x - half.x)
	if bounds.size.y <= half.y * 2.0:
		point.y = bounds.get_center().y
	else:
		var bottom := bounds.end.y
		if floor_zone != Vector3.ZERO:
			bottom = lerpf(bottom, floor_zone.z, smoothstep(floor_zone.x, floor_zone.y, target.global_position.x))
		point.y = clampf(point.y, bounds.position.y + half.y, bottom - half.y)
	return point
