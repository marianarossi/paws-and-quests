extends PlayerState


func physics_update(delta: float) -> void:
	if player.try_dash() or player.try_coyote_jump() or player.try_air_jump():
		return
	if player.should_wall_slide():
		go(&"WallSlide")
		return
	player.apply_horizontal(delta, cfg.air_accel_mult)
	player.apply_gravity(delta)
	var fall_speed := player.velocity.y
	player.move()
	if player.is_on_floor():
		player.land(fall_speed)
		go(ground_state())
