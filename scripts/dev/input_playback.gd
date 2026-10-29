class_name InputPlayback
extends Node

signal finished

var _events: Array = []
var _time := 0.0
var _index := 0


func _init() -> void:
	process_physics_priority = -100


func play(events: Array) -> void:
	_events = events.duplicate()
	_events.sort_custom(func(a: Array, b: Array) -> bool: return a[0] < b[0])
	_time = 0.0
	_index = 0
	set_physics_process(true)


func _physics_process(delta: float) -> void:
	while _index < _events.size() and _events[_index][0] <= _time:
		var event: Array = _events[_index]
		if event[2]:
			Input.action_press(event[1])
		else:
			Input.action_release(event[1])
		_index += 1
	_time += delta
	if _index >= _events.size():
		set_physics_process(false)
		finished.emit()
