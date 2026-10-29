extends PlayerState

var _direction := Vector2.RIGHT
var _time_left := 0.0
var _freeze_left := 0.0
var _launched := false


func enter(_previous: StringName, _msg: Dictionary) -> void:
	_time_left = cfg.dash_time
	_freeze_left = cfg.dash_freeze_time
	_launched = false
	player.consume_dash()
	player.velocity = Vector2.ZERO


func exit(_next: StringName) -> void:
	player.end_dash()


func physics_update(delta: float) -> void:
	if _freeze_left > 0.0:
		_freeze_left -= delta
		return
	if not _launched:
		_launched = true
		_direction = player.get_dash_direction()
		player.launch_dash(_direction)
	player.velocity = _direction * cfg.dash_speed
	if player.jump_buffer > 0.0 and _try_jump_out():
		return
	player.correct_dash_ledge(delta)
	player.correct_ceiling_corner(delta)
	player.move()
	_time_left -= delta
	if _time_left <= 0.0:
		_finish()


func _try_jump_out() -> bool:
	var grounded := player.is_on_floor() or player.coyote_timer > 0.0
	if grounded and _direction.x != 0.0 and _direction.y >= 0.0:
		go(&"Jump", {&"kind": &"hyper" if _direction.y > 0.0 else &"super"})
		return true
	if _direction == Vector2.UP:
		var side := player.probe_wall(cfg.wall_bounce_check)
		if side != 0:
			player.wall_dir = side
			go(&"Jump", {&"kind": &"wall_bounce"})
			return true
	if player.wall_dir != 0:
		go(&"Jump", {&"kind": &"wall"})
		return true
	return false


func _finish() -> void:
	player.velocity = _direction * cfg.dash_end_speed
	if _direction.y < 0.0:
		player.velocity.y *= cfg.dash_up_end_mult
	go(ground_state() if player.is_on_floor() else &"Fall")
