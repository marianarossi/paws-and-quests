extends PlayerState


func enter(_previous: StringName, _msg: Dictionary) -> void:
	player.velocity = Vector2.ZERO
	player.visual.visible = false
	player.hurtbox.set_deferred(&"monitoring", false)
