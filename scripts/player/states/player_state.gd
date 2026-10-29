class_name PlayerState
extends State

var player: Player
var cfg: MovementConfig


func setup(actor: Node) -> void:
	player = actor as Player
	cfg = player.config


func go(target: StringName, msg: Dictionary = {}) -> void:
	machine.transition_to(target, msg)


func ground_state() -> StringName:
	return &"Run" if player.move_x != 0.0 else &"Idle"
