class_name Projectile
extends Area2D

signal finished(projectile: Projectile)

const SHEET := "res://assets/sprites/combat/spark.json"
const RADIUS := 3.0
const TRAIL_SIZES: Array[int] = [3, 3, 2, 2, 1, 1]
const FADE_WARNING := 0.6

var velocity := Vector2.ZERO
var active := false

var _spec: ShotSpec
var _speed := 0.0
var _age := 0.0
var _target: Player
var _sprite: AnimatedSprite2D
var _glow: Sprite2D
var _trail: Array[Vector2] = []
var _trail_tick := 0
var _hot := Combat.HOT
var _deep := Combat.MAGENTA
var _burst := Combat.PINK


func _init() -> void:
	collision_layer = Combat.PROJECTILE_LAYER
	collision_mask = Combat.WORLD_LAYER
	monitoring = false
	monitorable = false
	visible = false
	z_index = 12
	material = Lights.unshaded()
	add_to_group(Combat.PROJECTILE_GROUP)
	var circle := CircleShape2D.new()
	circle.radius = RADIUS
	var shape := CollisionShape2D.new()
	shape.shape = circle
	add_child(shape)
	_glow = Sprite2D.new()
	_glow.texture = Lights.radial()
	_glow.scale = Vector2.ONE * 14.0 / Lights.TEXTURE_RADIUS
	_glow.modulate = Color(Combat.PINK, 0.55)
	var add_blend := CanvasItemMaterial.new()
	add_blend.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	add_blend.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	_glow.material = add_blend
	add_child(_glow)
	_sprite = AnimatedSprite2D.new()
	_sprite.sprite_frames = SpriteSheet.frames(SHEET)
	_sprite.material = Lights.unshaded()
	add_child(_sprite)
	body_entered.connect(_on_body_entered)
	set_physics_process(false)


func fire(at: Vector2, direction: Vector2, spec: ShotSpec, target: Player) -> void:
	_spec = spec
	_speed = spec.speed
	_age = 0.0
	_target = target
	velocity = direction.normalized() * _speed
	global_position = at
	reset_physics_interpolation()
	_trail.clear()
	active = true
	visible = true
	modulate = Color.WHITE
	use_colors(Combat.HOT, Combat.MAGENTA, Combat.PINK)
	_sprite.play(&"fly")
	set_deferred(&"monitoring", true)
	set_deferred(&"monitorable", true)
	set_physics_process(true)


func _physics_process(delta: float) -> void:
	_age += delta
	if _age >= _spec.lifetime:
		pop(false)
		return
	if _spec.turn_rate > 0.0 and _age < _spec.homing_time and is_instance_valid(_target) and not _target.is_dead():
		velocity = Combat.steer(velocity, global_position, Combat.aim_point(_target), deg_to_rad(_spec.turn_rate), delta)
	if _spec.accel != 0.0:
		_speed = move_toward(_speed, _spec.max_speed, _spec.accel * delta)
	velocity = velocity.normalized() * _speed
	global_position += velocity * delta
	_trail_tick += 1
	if _trail_tick % 2 == 0:
		_trail.push_front(global_position)
		if _trail.size() > TRAIL_SIZES.size():
			_trail.pop_back()
	if _spec.lifetime - _age < FADE_WARNING:
		modulate.a = 0.35 if fmod(_age, 0.12) < 0.06 else 1.0
	queue_redraw()


func _draw() -> void:
	for i in _trail.size():
		var size := TRAIL_SIZES[i]
		var color := _hot.lerp(_deep, float(i) / TRAIL_SIZES.size())
		color.a = 1.0 - 0.12 * i
		var corner := (to_local(_trail[i]) - Vector2.ONE * size * 0.5).round()
		draw_rect(Rect2(corner, Vector2(size, size)), color)
	if not _sprite.visible:
		draw_rect(Rect2(-2, -1, 4, 2), _burst)
		draw_rect(Rect2(-1, -2, 2, 4), _burst)
		draw_rect(Rect2(-1, -1, 2, 2), _hot)


func use_colors(hot: Color, deep: Color, burst_color: Color) -> void:
	_hot = hot
	_deep = deep
	_burst = burst_color
	var pink := hot == Combat.HOT
	_sprite.visible = pink
	_glow.modulate = Color(Combat.PINK if pink else burst_color, 0.55)
	queue_redraw()


func pop(loud := true) -> void:
	if not active:
		return
	active = false
	Combat.burst(get_parent(), global_position, _burst, 8 if loud else 4, 90.0 if loud else 40.0)
	if loud:
		AudioManager.play_sfx(&"spark_pop", -4.0, 0.12)
	retire()


func retire() -> void:
	active = false
	visible = false
	set_physics_process(false)
	set_deferred(&"monitoring", false)
	set_deferred(&"monitorable", false)
	finished.emit(self)


func _on_body_entered(_body: Node2D) -> void:
	pop()
