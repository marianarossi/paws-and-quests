extends PlayerState


func physics_update(delta: float) -> void:
	if player.try_dash() or player.try_air_jump():
		return
	var grabbing := player.is_grabbing()
	if player.wall_dir == 0 or (player.move_x != player.wall_dir and not grabbing):
		go(&"Fall")
		return
	player.facing = player.wall_dir
	player.velocity.x = player.wall_dir * 30.0
	if grabbing:
		player.velocity.y = 0.0
	else:
		player.velocity.y = move_toward(player.velocity.y, cfg.wall_slide_speed, cfg.gravity * delta)
	var fall_speed := player.velocity.y
	player.move()
	if player.is_on_floor():
		player.land(fall_speed)
		go(ground_state())
