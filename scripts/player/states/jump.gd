extends PlayerState


func enter(_previous: StringName, msg: Dictionary) -> void:
	player.start_jump(msg.get(&"kind", &"ground"))


func physics_update(delta: float) -> void:
	if player.try_dash() or player.try_air_jump():
		return
	player.update_var_jump(delta)
	player.apply_horizontal(delta, cfg.air_accel_mult)
	player.apply_gravity(delta)
	player.correct_ceiling_corner(delta)
	player.move()
	if player.is_on_ceiling():
		player.var_jump_timer = 0.0
	if player.velocity.y >= 0.0:
		go(&"Fall")
