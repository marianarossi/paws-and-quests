class_name FetchBall
extends Node2D

signal rested

enum State { REST, HELD, FLYING, MOUTH }

const TEXTURE := preload("res://assets/sprites/props/camp_ball.png")
const GROUP := &"fetch_ball"
const RADIUS := 3.5
const GRAVITY := 560.0
const MAX_FALL := 420.0
const BOUNCE := 0.55
const FRICTION := 260.0
const SETTLE := 45.0
const HELD_OFFSET := Vector2(0, -26)

var state := State.REST
var velocity := Vector2.ZERO
var bounds := Rect2()
var holder: Node2D

var _sprite: Sprite2D
var _spin := 0.0


static func create(center: Vector2) -> FetchBall:
	var ball := FetchBall.new()
	ball.position = center.round()
	return ball


func _ready() -> void:
	add_to_group(GROUP)
	z_index = 3
	_sprite = Sprite2D.new()
	_sprite.texture = TEXTURE
	_sprite.hframes = 2
	add_child(_sprite)


func throw(vel: Vector2) -> void:
	state = State.FLYING
	holder = null
	velocity = vel


func place(center: Vector2) -> void:
	state = State.REST
	holder = null
	velocity = Vector2.ZERO
	global_position = center.round()


func hold(node: Node2D, mouth: bool) -> void:
	state = State.MOUTH if mouth else State.HELD
	holder = node
	velocity = Vector2.ZERO


func is_free() -> bool:
	return state == State.REST or state == State.FLYING


func _physics_process(delta: float) -> void:
	match state:
		State.HELD:
			if is_instance_valid(holder):
				global_position = holder.global_position + HELD_OFFSET
		State.FLYING:
			_fly(delta)


func _fly(delta: float) -> void:
	var ground := _ray(global_position, global_position + Vector2(0, RADIUS + 1.5))
	if not ground.is_empty() and velocity.y >= 0.0 and velocity.y < SETTLE:
		velocity.y = 0.0
		velocity.x = move_toward(velocity.x, 0.0, FRICTION * delta)
		if absf(velocity.x) < 6.0:
			state = State.REST
			velocity = Vector2.ZERO
			global_position = global_position.round()
			rested.emit()
			return
	else:
		velocity.y = minf(velocity.y + GRAVITY * delta, MAX_FALL)
	var motion := velocity * delta
	var hit := _ray(global_position, global_position + motion + motion.normalized() * RADIUS)
	if hit.is_empty():
		global_position += motion
	else:
		var normal: Vector2 = hit.normal
		var speed := velocity.length()
		global_position = hit.position + normal * (RADIUS + 0.1)
		velocity = velocity.bounce(normal) * BOUNCE
		if normal.y < -0.5:
			velocity.x *= 0.85
			if absf(velocity.y) < SETTLE:
				velocity.y = 0.0
		if speed > 60.0:
			AudioManager.play_sfx(&"ball_bounce", -14.0 + minf(speed / 40.0, 8.0), 0.08)
	if bounds.has_area():
		if global_position.x < bounds.position.x + RADIUS and velocity.x < 0.0:
			velocity.x = -velocity.x * BOUNCE
		elif global_position.x > bounds.end.x - RADIUS and velocity.x > 0.0:
			velocity.x = -velocity.x * BOUNCE
		global_position.x = clampf(global_position.x, bounds.position.x + RADIUS, bounds.end.x - RADIUS)
	_spin += absf(velocity.x) * delta
	_sprite.frame = int(_spin / 4.0) % 2


func _ray(from: Vector2, to: Vector2) -> Dictionary:
	if from.is_equal_approx(to):
		return {}
	var query := PhysicsRayQueryParameters2D.create(from, to, Combat.WORLD_LAYER)
	return get_world_2d().direct_space_state.intersect_ray(query)
