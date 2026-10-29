class_name Player
extends CharacterBody2D

signal jumped(kind: StringName)
signal landed(fall_speed: float)
signal dash_started(direction: Vector2)
signal dash_refilled
signal died
signal respawned

const HERO_SHEET := "res://assets/sprites/hero/hero.json"
const APEX_SPEED := 45.0
const LAND_SPEED := 110.0
const LAND_TIME := 0.13
const ANIM_HOLD_TICKS := 3
const SLEEP_AFTER := 25.0
const SEAT_SLEEP_AFTER := 42.0
const WATER_SPEED := 0.62
const WATER_SINK := 70.0
const WATER_FLOAT := 26.0
const WATER_DRAG := 620.0
const SWIM_SPEED := 150.0
const SWIM_INTERVAL := 0.28
const WALL_CLIMB_MARGIN := 2.0
const ANIM_INSTANT: Array[StringName] = [&"jump", &"land", &"dash", &"dash_up", &"dash_down", &"sit"]


@export var config: MovementConfig
@export var input_enabled := true

var facing := 1
var input_dir := Vector2.ZERO
var move_x := 0.0
var jump_held := false
var coyote_timer := 0.0
var jump_buffer := 0.0
var dash_buffer := 0.0
var var_jump_timer := 0.0
var var_jump_speed := 0.0
var air_jumps_left := 0
var dash_charges := 0
var dash_cooldown := 0.0
var is_dashing := false
var wall_dir := 0
var grab_held := false
var _wall_jump_side := 0
var _wall_jump_y := 0.0
var force_move_timer := 0.0
var force_move_dir := 0
var launch_speed := 0.0
var dash_direction := Vector2.ZERO
var wind := 0.0
var seated := false
var asleep := false
var pose: StringName = &""
var water: Water

var _waters: Array[Water] = []
var _rest_time := 0.0
var _swim_cooldown := 0.0
var _water_exit := 0.0

var _land_timer := 0.0
var _wanted_anim: StringName = &"idle"
var _wanted_ticks := 0
var _restart_anim := false
var dev_invincible := false


@onready var state_machine: StateMachine = $StateMachine
@onready var visual: Node2D = $Visual
@onready var body_sprite: AnimatedSprite2D = $Visual/Body
@onready var hurtbox: Area2D = $Hurtbox


func _ready() -> void:
	var sheet := HERO_SHEET
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--hero="):
			var hero_name := arg.trim_prefix("--hero=")
			if hero_name == "aseprite":
				hero_name = "george_ase"
			var path := "res://assets/sprites/%s/%s.json" % [hero_name, hero_name]
			if FileAccess.file_exists(path):
				sheet = path
	if sheet == HERO_SHEET:
		HeroLook.dress(body_sprite)
		Events.look_changed.connect(_on_look_changed)
	else:
		body_sprite.sprite_frames = SpriteSheet.frames(sheet)
	body_sprite.scale = SpriteSheet.unit_scale(sheet)
	body_sprite.play(&"idle")
	var lantern := Lights.point(Color(1.0, 0.85, 0.6), 84.0, 0.55)
	lantern.position = Vector2(0, -10)
	add_child(lantern)
	add_to_group(Combat.PLAYER_GROUP)
	state_machine.setup(self)
	hurtbox.area_entered.connect(_on_hurtbox_area_entered)
	Events.player_spawned.emit(self)


func _on_look_changed() -> void:
	HeroLook.dress(body_sprite)


func _physics_process(delta: float) -> void:
	_read_input()
	_tick_timers(delta)
	wall_dir = _probe_wall()
	state_machine.physics_update(delta)
	_refill_on_floor()
	RenderingServer.global_shader_parameter_set(&"hero_pos", global_position)
	_update_visual(delta)


func _read_input() -> void:
	if not input_enabled:
		input_dir = Vector2.ZERO
		move_x = 0.0
		jump_held = false
		grab_held = false
		return
	input_dir = Vector2(Input.get_axis(&"move_left", &"move_right"), Input.get_axis(&"move_up", &"move_down"))
	move_x = signf(input_dir.x) if absf(input_dir.x) > 0.3 else 0.0
	jump_held = Input.is_action_pressed(&"jump")
	grab_held = Input.is_action_pressed(&"grab")
	if Input.is_action_just_pressed(&"jump"):
		jump_buffer = config.jump_buffer_time
	if Input.is_action_just_pressed(&"dash"):
		dash_buffer = config.dash_buffer_time
	var wants_to_move := move_x != 0.0 or jump_buffer > 0.0 or dash_buffer > 0.0
	if wants_to_move:
		seated = false
	if wants_to_move or input_dir.y != 0.0:
		asleep = false
		_rest_time = 0.0


func _tick_timers(delta: float) -> void:
	coyote_timer = maxf(0.0, coyote_timer - delta)
	jump_buffer = maxf(0.0, jump_buffer - delta)
	dash_buffer = maxf(0.0, dash_buffer - delta)
	dash_cooldown = maxf(0.0, dash_cooldown - delta)
	force_move_timer = maxf(0.0, force_move_timer - delta)
	_swim_cooldown = maxf(0.0, _swim_cooldown - delta)
	_water_exit = maxf(0.0, _water_exit - delta)


func _probe_wall() -> int:
	if is_on_floor():
		return 0
	return probe_wall(config.wall_check_distance)


func probe_wall(reach: float) -> int:
	if test_move(global_transform, Vector2(reach, 0)):
		return 1
	if test_move(global_transform, Vector2(-reach, 0)):
		return -1
	return 0


func _refill_on_floor() -> void:
	if (not is_on_floor() and water == null) or is_dashing:
		return
	_wall_jump_side = 0
	air_jumps_left = 1 if Game.has_ability(&"double_jump") else 0
	if dash_charges < 1 and dash_cooldown <= 0.0 and Game.has_ability(&"dash"):
		refill_dash()


func apply_horizontal(delta: float, accel_mult := 1.0) -> void:
	var dir := move_x
	if force_move_timer > 0.0:
		dir = float(force_move_dir)
	elif dir != 0.0:
		facing = int(dir)
	var top_speed := config.max_run_speed * (WATER_SPEED if water != null else 1.0)
	var accel := config.run_accel
	if dir == 0.0:
		accel = config.run_decel
	elif absf(velocity.x) > top_speed and signf(velocity.x) == dir:
		accel = config.run_reduce
	velocity.x = move_toward(velocity.x, dir * top_speed, accel * accel_mult * delta)


func apply_gravity(delta: float) -> void:
	if water != null:
		var drift := WATER_SINK if input_dir.y > 0.5 else -WATER_FLOAT
		if drift < 0.0:
			for body_of_water in _waters:
				if body_of_water.has_surface:
					var below := global_position.y - (body_of_water.global_position.y + Water.FLOAT_LINE)
					drift = clampf(-below * 7.0, -WATER_FLOAT, WATER_FLOAT)
		velocity.y = move_toward(velocity.y, drift, WATER_DRAG * delta)
		return
	var g := config.gravity
	if jump_held and absf(velocity.y) < config.apex_threshold:
		g *= config.apex_gravity_mult
	elif velocity.y > 0.0:
		g *= config.fall_gravity_mult
	var limit := config.fast_fall_speed if input_dir.y > 0.5 else config.max_fall_speed
	velocity.y = move_toward(velocity.y, limit, g * delta)


func move() -> void:
	var push := 0.0 if is_dashing else wind
	wind = 0.0
	var own := velocity.x
	velocity.x += push
	move_and_slide()
	if push != 0.0:
		velocity.x = 0.0 if is_on_wall() else own


func start_coyote() -> void:
	coyote_timer = config.coyote_time


func start_jump(kind: StringName) -> void:
	var hold := config.var_jump_time
	var same_wall := kind == &"wall" and wall_dir == _wall_jump_side
	_wall_jump_side = 0
	match kind:
		&"swim":
			var at_surface := _water_exit > 0.0 or (water != null and water.is_at_surface(global_position))
			velocity.y = -config.jump_speed * 0.92 if at_surface else -SWIM_SPEED
			hold = 0.0
			_swim_cooldown = SWIM_INTERVAL
		&"double":
			velocity.y = -config.double_jump_speed
			hold = config.double_var_jump_time
			air_jumps_left -= 1
			if move_x != 0.0 and signf(velocity.x) != move_x:
				velocity.x = move_x * config.max_run_speed * 0.6
		&"wall":
			velocity = Vector2(-wall_dir * config.wall_jump_h_speed, -config.jump_speed)
			var above := _wall_jump_y - global_position.y if same_wall else -1.0
			if above > 0.0:
				var cut := above + WALL_CLIMB_MARGIN
				var hold_cut := minf(hold, cut / config.jump_speed)
				hold -= hold_cut
				cut -= hold_cut * config.jump_speed
				if cut > 0.0:
					velocity.y = -sqrt(maxf(0.0, config.jump_speed * config.jump_speed - 2.0 * config.gravity * cut))
			else:
				_wall_jump_y = global_position.y
			_wall_jump_side = wall_dir
			force_move_dir = -wall_dir
			force_move_timer = config.wall_jump_force_time
			facing = -wall_dir
		&"spring":
			velocity.y = -launch_speed
			hold = 0.0
		&"super":
			velocity = Vector2(signf(velocity.x) * config.super_jump_h_speed, -config.jump_speed)
		&"hyper":
			velocity = Vector2(signf(velocity.x) * config.hyper_jump_h_speed, -config.jump_speed * config.hyper_jump_height_mult)
		&"wall_bounce":
			velocity = Vector2(-wall_dir * config.wall_bounce_h_speed, -config.wall_bounce_speed)
			hold = config.wall_bounce_var_time
			force_move_dir = -wall_dir
			force_move_timer = config.wall_jump_force_time
			facing = -wall_dir
		_:
			velocity.y = -config.jump_speed
			velocity.x += move_x * config.jump_h_boost
	var_jump_speed = velocity.y
	var_jump_timer = hold
	jump_buffer = 0.0
	coyote_timer = 0.0
	_land_timer = 0.0
	_restart_anim = true
	jumped.emit(kind)


func update_var_jump(delta: float) -> void:
	if var_jump_timer <= 0.0:
		return
	var_jump_timer -= delta
	if jump_held:
		velocity.y = minf(velocity.y, var_jump_speed)
	else:
		var_jump_timer = 0.0


func land(fall_speed: float) -> void:
	if fall_speed >= LAND_SPEED:
		_land_timer = LAND_TIME
	landed.emit(fall_speed)


func try_ground_jump() -> bool:
	if jump_buffer <= 0.0:
		return false
	state_machine.transition_to(&"Jump", {&"kind": &"ground"})
	return true


func try_coyote_jump() -> bool:
	if jump_buffer <= 0.0 or coyote_timer <= 0.0:
		return false
	state_machine.transition_to(&"Jump", {&"kind": &"ground"})
	return true


func try_air_jump() -> bool:
	if jump_buffer <= 0.0:
		return false
	if water != null or _water_exit > 0.0:
		if _swim_cooldown > 0.0:
			return false
		state_machine.transition_to(&"Jump", {&"kind": &"swim"})
		return true
	if wall_dir != 0:
		state_machine.transition_to(&"Jump", {&"kind": &"wall"})
		return true
	if air_jumps_left > 0 and Game.has_ability(&"double_jump"):
		state_machine.transition_to(&"Jump", {&"kind": &"double"})
		return true
	return false


func try_dash() -> bool:
	if dash_buffer <= 0.0 or dash_charges <= 0 or dash_cooldown > 0.0 or not Game.has_ability(&"dash"):
		return false
	dash_buffer = 0.0
	state_machine.transition_to(&"Dash")
	return true


func should_wall_slide() -> bool:
	return wall_dir != 0 and velocity.y > 0.0 and (move_x == wall_dir or grab_held)


func is_grabbing() -> bool:
	return grab_held and wall_dir != 0


func get_dash_direction() -> Vector2:
	var dir := Vector2(
		signf(input_dir.x) if absf(input_dir.x) > 0.35 else 0.0,
		signf(input_dir.y) if absf(input_dir.y) > 0.35 else 0.0)
	if dir == Vector2.ZERO:
		dir = Vector2(facing, 0)
	return dir.normalized()


func consume_dash() -> void:
	dash_charges -= 1
	dash_cooldown = config.dash_cooldown
	is_dashing = true
	_wall_jump_side = 0
	dash_direction = Vector2.ZERO
	var_jump_timer = 0.0


func launch_dash(direction: Vector2) -> void:
	if direction.x != 0.0:
		facing = int(signf(direction.x))
	dash_direction = direction
	dash_started.emit(direction)


func end_dash() -> void:
	is_dashing = false
	if Settings.infinite_dash():
		dash_charges = 1


func refill_dash() -> void:
	dash_charges = 1
	dash_refilled.emit()


func _on_hurtbox_area_entered(area: Area2D) -> void:
	if area.is_in_group(Combat.PROJECTILE_GROUP):
		area.call(&"pop")
		if is_dashing:
			return
	die()


func is_dead() -> bool:
	return state_machine.is_in(&"Dead")


func die(forced := false) -> void:
	if is_dead() or ((dev_invincible or Settings.invincible()) and not forced):
		return
	state_machine.transition_to(&"Dead")
	died.emit()


func respawn(feet_position: Vector2, sit := false) -> void:
	seated = sit
	asleep = false
	_rest_time = 0.0
	if sit:
		facing = 1
	visual.visible = true
	hurtbox.set_deferred(&"monitoring", true)
	dash_charges = 0
	air_jumps_left = 0
	teleport(feet_position)
	respawned.emit()


func enter_water(body_of_water: Water) -> void:
	if not _waters.has(body_of_water):
		_waters.append(body_of_water)
	water = body_of_water


func exit_water(body_of_water: Water) -> void:
	_waters.erase(body_of_water)
	water = _waters.back() if not _waters.is_empty() else null
	if water == null and velocity.y <= 0.0:
		_water_exit = 0.18


func refill_air_moves() -> void:
	air_jumps_left = 1 if Game.has_ability(&"double_jump") else 0
	if dash_charges < 1 and Game.has_ability(&"dash"):
		refill_dash()


func launch(speed: float) -> void:
	launch_speed = speed
	refill_air_moves()
	state_machine.transition_to(&"Jump", {&"kind": &"spring"})


func correct_ceiling_corner(delta: float) -> void:
	if velocity.y >= 0.0:
		return
	var motion := Vector2(0, velocity.y * delta)
	if not test_move(global_transform, motion):
		return
	for i in range(1, config.corner_correction + 1):
		for side: int in [1, -1]:
			var offset := Vector2(i * side, 0)
			if not test_move(global_transform, offset) and not test_move(global_transform.translated(offset), motion):
				global_position.x += offset.x
				return


func correct_dash_ledge(delta: float) -> void:
	if velocity.x == 0.0 or velocity.y != 0.0:
		return
	var motion := Vector2(velocity.x * delta, 0)
	if not test_move(global_transform, motion):
		return
	for i in range(1, config.dash_ledge_correction + 1):
		var offset := Vector2(0, -i)
		if not test_move(global_transform, offset) and not test_move(global_transform.translated(offset), motion):
			global_position.y += offset.y
			return


func _update_visual(delta: float) -> void:
	_land_timer = maxf(0.0, _land_timer - delta)
	if seated or (state_machine.current_name == &"Idle" and water == null):
		_rest_time += delta
		if _rest_time > (SEAT_SLEEP_AFTER if seated else SLEEP_AFTER):
			asleep = true
	else:
		_rest_time = 0.0
		asleep = false
	body_sprite.flip_h = facing < 0
	_update_animation()


func _update_animation() -> void:
	var wanted := _pick_animation()
	if wanted != _wanted_anim:
		_wanted_anim = wanted
		_wanted_ticks = 0
	_wanted_ticks += 1
	body_sprite.speed_scale = clampf(absf(velocity.x) / config.max_run_speed, 0.6, 1.2) if body_sprite.animation == &"run" else 1.0
	if _restart_anim and wanted == &"jump":
		_restart_anim = false
		body_sprite.play(wanted)
		body_sprite.frame = 0
		return
	if body_sprite.animation == wanted:
		return
	if _wanted_ticks >= ANIM_HOLD_TICKS or wanted in ANIM_INSTANT:
		body_sprite.play(wanted)


func _pick_animation() -> StringName:
	if pose != &"":
		return pose
	if asleep:
		return &"sleep"
	if seated:
		return _seat_animation()
	match state_machine.current_name:
		&"Dash":
			if dash_direction.x == 0.0 and dash_direction.y < 0.0:
				return &"dash_up"
			if dash_direction.x == 0.0 and dash_direction.y > 0.0:
				return &"dash_down"
			return &"dash"
		&"WallSlide":
			return &"wall_slide"
		&"Idle", &"Run":
			if _land_timer > 0.0:
				return &"land"
			if state_machine.current_name == &"Idle":
				return &"crouch" if input_dir.y > 0.5 else &"idle"
			if is_on_wall() and move_x != 0.0 and signf(get_wall_normal().x) == -move_x:
				return &"push"
			return &"run"
	if water != null:
		return &"swim" if (move_x != 0.0 or absf(velocity.y) > 40.0) else &"float"
	if velocity.y < -APEX_SPEED:
		return &"jump"
	if velocity.y > APEX_SPEED:
		return &"fall"
	return &"apex"


func _seat_animation() -> StringName:
	var t := fmod(_rest_time, 21.0)
	if t < 3.5:
		return &"sit"
	if t < 11.5:
		return &"sit_roast"
	if t < 14.0:
		return &"sit"
	if t < 18.0:
		return &"sit_think"
	return &"sit"


func stand_up() -> void:
	seated = false
	asleep = false
	_rest_time = 0.0


func start_roasting() -> void:
	_rest_time = 3.6


func teleport(feet_position: Vector2) -> void:
	global_position = feet_position
	velocity = Vector2.ZERO
	state_machine.transition_to(&"Fall")
	reset_physics_interpolation()
