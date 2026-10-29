class_name BarkWave
extends Node2D

const GROUP := &"bark_wave"
const HEIGHT := 11.0
const DEEP := Color("#c88a10")
const YELLOW := Color("#ffcc33")
const HOT := Color("#fff4c0")
const STEP_DOWN := 40.0

var direction := -1
var speed := 140.0
var bounds := Rect2()

var _time := 0.0
var _fading := 0.0


static func spawn(parent: Node, feet: Vector2, dir: int, room_bounds: Rect2, wave_speed := 140.0) -> BarkWave:
	var wave := BarkWave.new()
	wave.direction = dir
	wave.speed = wave_speed
	wave.bounds = room_bounds
	parent.add_child(wave)
	wave.global_position = feet
	AudioManager.play_sfx(&"swoop", -6.0, 0.1)
	return wave


func _ready() -> void:
	add_to_group(GROUP)
	z_index = 8
	material = Lights.unshaded()


func _physics_process(delta: float) -> void:
	_time += delta
	queue_redraw()
	if _fading > 0.0:
		_fading -= delta
		if _fading <= 0.0:
			queue_free()
		return
	var next := global_position + Vector2(direction * speed * delta, 0)
	var space := get_world_2d().direct_space_state
	var wall := space.intersect_ray(PhysicsRayQueryParameters2D.create(global_position + Vector2(0, -3), next + Vector2(direction * 2, -3), Combat.WORLD_LAYER))
	if not wall.is_empty() or (bounds.has_area() and not bounds.has_point(next + Vector2(0, -2))):
		_fade()
		return
	var ground := space.intersect_ray(PhysicsRayQueryParameters2D.create(next + Vector2(0, -4), next + Vector2(0, STEP_DOWN), Combat.WORLD_LAYER))
	if ground.is_empty():
		_fade()
		return
	global_position = Vector2(next.x, ground.position.y)
	var player := Combat.find_player(self)
	if player and not player.is_dead():
		var feet := player.global_position
		if absf(feet.x - global_position.x) < 6.0 and feet.y > global_position.y - HEIGHT and feet.y < global_position.y + 3.0:
			player.die()


func _fade() -> void:
	_fading = 0.25


func _draw() -> void:
	var alpha := 1.0 if _fading <= 0.0 else _fading / 0.25
	for i in 3:
		var back := -direction * i * 4.0
		var tall := HEIGHT - i * 3.0 + (1.0 if fmod(_time * 12.0 + i, 2.0) < 1.0 else 0.0)
		var color := (HOT if i == 0 else YELLOW if i == 1 else DEEP)
		color.a = alpha * (1.0 - i * 0.2)
		for k in int(tall):
			var bend := roundf(sin(float(k) / tall * PI) * 3.0) * direction
			draw_rect(Rect2(Vector2(back + bend, -k - 1), Vector2.ONE), color)
	draw_rect(Rect2(Vector2(-6 if direction > 0 else 0, -1), Vector2(6, 1)), Color(YELLOW, 0.5 * alpha))
