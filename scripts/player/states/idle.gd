extends PlayerState


func physics_update(delta: float) -> void:
	if player.try_dash() or player.try_ground_jump():
		return
	player.apply_horizontal(delta)
	player.apply_gravity(delta)
	player.move()
	if not player.is_on_floor():
		player.start_coyote()
		go(&"Fall")
	elif player.move_x != 0.0:
		go(&"Run")
