class_name StateMachine
extends Node

signal state_changed(previous: StringName, current: StringName)

@export var initial_state: StringName = &"Idle"

var current: State
var current_name: StringName
var time_in_state := 0.0

var _states: Dictionary[StringName, State] = {}


func setup(actor: Node) -> void:
	for child in get_children():
		var state := child as State
		if state:
			_states[state.name] = state
			state.machine = self
			state.setup(actor)
	transition_to(initial_state)


func transition_to(target: StringName, msg: Dictionary = {}) -> void:
	assert(_states.has(target), "estado inexistente: %s" % target)
	var previous := current_name
	if current:
		current.exit(target)
	current = _states[target]
	current_name = target
	time_in_state = 0.0
	current.enter(previous, msg)
	state_changed.emit(previous, target)


func physics_update(delta: float) -> void:
	if current:
		time_in_state += delta
		current.physics_update(delta)


func is_in(state: StringName) -> bool:
	return current_name == state
