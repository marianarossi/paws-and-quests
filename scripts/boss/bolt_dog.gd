class_name BoltDog
extends CharacterBody2D

signal landed

const SHEET := "res://assets/sprites/zeus_dog/zeus_dog.json"
const SPRITE_OFFSET := Vector2(-16, -31)
const MOUTH := Vector2(11, -9)
const GRAVITY := 900.0
const MAX_FALL := 420.0
const HOP := 190.0

var sprite: AnimatedSprite2D
var facing := -1
var carried: FetchBall
var target_x := NAN
var speed := 150.0
var rest_anim: StringName = &"idle"

var _leaping := false
var _wall_ahead := false
var _hold_anim := 0.0


func _ready() -> void:
	collision_layer = 0
	collision_mask = Combat.WORLD_LAYER
	floor_snap_length = 4.0
	var box := RectangleShape2D.new()
	box.size = Vector2(12, 10)
	var shape := CollisionShape2D.new()
	shape.shape = box
	shape.position = Vector2(0, -5)
	add_child(shape)
	sprite = AnimatedSprite2D.new()
	sprite.sprite_frames = SpriteSheet.frames(SHEET)
	sprite.centered = false
	sprite.position = SPRITE_OFFSET
	add_child(sprite)
	z_index = 2
	face(facing)
	sprite.play(rest_anim)


func face(dir: int) -> void:
	facing = 1 if dir >= 0 else -1
	sprite.flip_h = facing < 0


func show_anim(anim: StringName, seconds: float) -> void:
	_hold_anim = seconds
	sprite.play(anim)


func stop() -> void:
	target_x = NAN
	velocity.x = 0.0


func run_to(x: float, run_speed := 150.0, limit := 4.0) -> bool:
	target_x = x
	speed = run_speed
	_wall_ahead = false
	var time := 0.0
	var blocked := 0.0
	while not is_nan(target_x):
		await get_tree().physics_frame
		var step := get_physics_process_delta_time()
		time += step
		blocked = blocked + step if is_on_floor() and is_on_wall() else 0.0
		if time > limit or blocked > 0.35 or _wall_ahead:
			stop()
			return false
	return true


func leap_to(feet: Vector2, apex := 22.0) -> bool:
	target_x = NAN
	var rise := global_position.y - feet.y
	var height := maxf(rise, 0.0) + apex
	var up := sqrt(2.0 * height / GRAVITY)
	var down := sqrt(2.0 * maxf(height - rise, 1.0) / GRAVITY)
	velocity = Vector2((feet.x - global_position.x) / (up + down), -sqrt(2.0 * GRAVITY * height))
	face(int(signf(velocity.x)) if absf(velocity.x) > 1.0 else facing)
	_leaping = true
	AudioManager.play_sfx(&"jump", -10.0, 0.1)
	var time := 0.0
	while _leaping and time < 3.0:
		await get_tree().physics_frame
		time += get_physics_process_delta_time()
	_leaping = false
	return global_position.distance_to(feet) < 10.0


func pick_up(ball: FetchBall) -> void:
	carried = ball
	ball.hold(self, true)
	_place_carried()


func drop() -> FetchBall:
	var ball := carried
	carried = null
	if ball:
		ball.place(global_position + Vector2(MOUTH.x * 0.6 * facing, -FetchBall.RADIUS))
	return ball


func can_bite(ball: FetchBall) -> bool:
	return ball.global_position.distance_to(global_position + Vector2(MOUTH.x * facing, MOUTH.y)) < 9.0 \
			or ball.global_position.distance_to(global_position + Vector2(0, -6)) < 9.0


func _physics_process(delta: float) -> void:
	velocity.y = minf(velocity.y + GRAVITY * delta, MAX_FALL)
	if not _leaping:
		if is_nan(target_x):
			velocity.x = 0.0
		else:
			var dx := target_x - global_position.x
			if absf(dx) < 2.0:
				velocity.x = 0.0
				target_x = NAN
			else:
				face(int(signf(dx)))
				velocity.x = signf(dx) * minf(speed, absf(dx) / delta)
				if is_on_floor() and is_on_wall():
					if _low_step(signf(dx)):
						velocity.y = -HOP
					else:
						_wall_ahead = true
	var was_in_air := not is_on_floor()
	move_and_slide()
	if is_on_floor() and was_in_air and velocity.y >= 0.0:
		if _leaping:
			_leaping = false
			velocity.x = 0.0
			landed.emit()
	_place_carried()
	_pick_anim(delta)


func _low_step(dir: float) -> bool:
	var space := get_world_2d().direct_space_state
	var from := global_position + Vector2(0, -20)
	var probe := PhysicsRayQueryParameters2D.create(from, from + Vector2(dir * 12.0, 0), Combat.WORLD_LAYER)
	return space.intersect_ray(probe).is_empty()


func _pick_anim(delta: float) -> void:
	if _hold_anim > 0.0:
		_hold_anim -= delta
		return
	var anim := rest_anim
	if not is_on_floor():
		anim = &"jump" if velocity.y < 0.0 else &"fall"
	elif absf(velocity.x) > 1.0:
		anim = &"run" if absf(velocity.x) > 90.0 else &"walk"
	if sprite.animation != anim:
		sprite.play(anim)


func _place_carried() -> void:
	if carried:
		carried.global_position = global_position + Vector2(MOUTH.x * facing, MOUTH.y)
