extends Node

@warning_ignore_start("unused_signal")
signal ability_changed(ability: StringName, unlocked: bool)
signal player_spawned(player: Node2D)
signal player_died(at: Vector2)
signal player_respawned
signal room_entered(room_id: String)
signal checkpoint_reached(checkpoint: Node2D)
signal door_entered(room_id: String)
signal gift_received(ability: StringName)
signal glow_entered(room_id: String)
signal feather_collected(count: int)
signal look_changed
@warning_ignore_restore("unused_signal")
