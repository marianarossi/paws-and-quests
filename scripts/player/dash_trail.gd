class_name DashTrail
extends Node2D

const LIFETIME := 0.4
const STAGES: Array = [
	[0.08, 6.0, Color("f4f8ff")],
	[0.22, 5.0, Color("9fb4e8")],
	[0.42, 4.0, Color("5b78c4")],
	[0.62, 3.0, Color("41599a")],
	[0.82, 2.0, Color("2f4372")],
	[1.0, 1.0, Color("212f52")],
]
const CORE := Color("f4f8ff")
const EDGE := Color("9fb4e8")
const GLINT := Color("d6e2ff")

var _points: PackedVector2Array = []
var _ages: PackedFloat32Array = []


func _ready() -> void:
	z_index = 9
	physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_OFF
	material = Lights.unshaded()
	set_process(false)


func add_point(at: Vector2) -> void:
	_points.append(at.round())
	_ages.append(0.0)
	set_process(true)


func _process(delta: float) -> void:
	var expired := 0
	for i in _ages.size():
		_ages[i] += delta
		if _ages[i] >= LIFETIME:
			expired = i + 1
	if expired > 0:
		_points = _points.slice(expired)
		_ages = _ages.slice(expired)
	if _points.is_empty():
		set_process(false)
	queue_redraw()


func _draw() -> void:
	for i in _points.size():
		var age := _ages[i] / LIFETIME
		var side := 1.0
		for stage: Array in STAGES:
			if age <= stage[0]:
				side = stage[1]
				_square(_points[i], side, stage[2])
				break
		var along := Vector2.RIGHT
		if i > 0 and _points[i] != _points[i - 1]:
			along = (_points[i] - _points[i - 1]).normalized()
		var across := Vector2(-along.y, along.x)
		if age < 0.3 and side > 2.0:
			_square(_points[i], side - 3.0, CORE)
		if age < 0.7 and i % 2 == 0:
			var reach := side * 0.5 + 2.0
			_square(_points[i] + across * reach, 1.0, EDGE)
			_square(_points[i] - across * reach, 1.0, EDGE)
		if i % 5 == 2 and age > 0.25:
			var drift := 4.0 + age * 7.0
			_square(_points[i] + across * (drift if i % 2 == 0 else -drift), 2.0 if age < 0.6 else 1.0, GLINT)


func _square(at: Vector2, side: float, color: Color) -> void:
	draw_rect(Rect2((at - Vector2(side, side) * 0.5).floor(), Vector2(side, side)), color)
