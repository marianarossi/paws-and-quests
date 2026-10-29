class_name ThunderBomb
extends Node2D

const SPARK := Color("bfe0ff")
const RING := Color("ff5fb0")
const GRAVITY := 420.0

var velocity := Vector2.ZERO
var fuse := 0.9
var blast_radius := 26.0

var _landed := false
var _timer := 0.0
var _age := 0.0
var _flash := 0.0
var _exploded := false
var _sprite: AnimatedSprite2D

const HURT_CENTER := Vector2(0, -8.5)
const HURT_HALF := Vector2(3, 5.5)


static func throw(parent: Node, at: Vector2, vel: Vector2, fuse_time := 0.9, radius := 26.0) -> ThunderBomb:
	var bomb := ThunderBomb.new()
	bomb.velocity = vel
	bomb.fuse = Combat.telegraph_time(fuse_time)
	bomb.blast_radius = radius
	parent.add_child(bomb)
	bomb.global_position = at
	bomb.reset_physics_interpolation()
	return bomb


func _ready() -> void:
	z_index = 12
	material = Lights.unshaded()
	_sprite = AnimatedSprite2D.new()
	_sprite.sprite_frames = EnemyShot.frames_of(&"thunder_bomb")
	_sprite.material = Lights.unshaded()
	_sprite.play(&"fly")
	add_child(_sprite)
	Events.player_died.connect(func(_at: Vector2) -> void: queue_free())


func _physics_process(delta: float) -> void:
	_age += delta
	if _exploded:
		_timer -= delta
		_flash = maxf(_timer / 0.3, 0.0)
		if _timer > 0.15:
			var target := Combat.find_player(self)
			if target and _blast_hits(target):
				target.die()
		if _timer <= 0.0:
			queue_free()
		queue_redraw()
		return
	if not _landed:
		_fly(delta)
		if _age > 4.0:
			_explode()
		return
	_timer -= delta
	var left := clampf(_timer / fuse, 0.0, 1.0)
	var rate := lerpf(22.0, 6.0, left)
	_sprite.modulate = Color(2.2, 2.2, 2.4) if fmod(_timer * rate, 1.0) < 0.35 else Color.WHITE
	queue_redraw()
	if _timer <= 0.0:
		_explode()


func _fly(delta: float) -> void:
	velocity.y += GRAVITY * delta
	var step := velocity * delta
	var space := get_world_2d().direct_space_state
	var ray := PhysicsRayQueryParameters2D.create(global_position, global_position + step + step.normalized() * 3.0, Combat.WORLD_LAYER)
	var hit := space.intersect_ray(ray)
	if hit.is_empty():
		global_position += step
		_sprite.rotation += velocity.x * delta * 0.05
		return
	var normal: Vector2 = hit["normal"]
	if normal.y < -0.6:
		global_position = hit["position"] + Vector2(0, -3)
		_landed = true
		_timer = fuse
		_sprite.rotation = 0.0
		AudioManager.play_sfx(&"fuse", -6.0, 0.08)
	else:
		velocity = velocity.bounce(normal) * 0.4
		global_position = hit["position"] + normal * 3.0


func _explode() -> void:
	_exploded = true
	_timer = 0.3
	_sprite.visible = false
	AudioManager.play_sfx(&"boom", -2.0, 0.06)
	Combat.burst(get_parent(), global_position, Color.WHITE, 14, 160.0)
	Combat.burst(get_parent(), global_position, SPARK, 8, 110.0)


func _blast_hits(player: Player) -> bool:
	var center := player.global_position + HURT_CENTER
	var nearest := global_position.clamp(center - HURT_HALF, center + HURT_HALF)
	return nearest.distance_to(global_position) <= blast_radius


func _draw() -> void:
	if _exploded:
		var r := blast_radius * (1.1 - 0.3 * _flash)
		draw_circle(Vector2.ZERO, r, Color(SPARK, 0.5 * _flash))
		draw_circle(Vector2.ZERO, r * 0.7, Color(1, 1, 1, 0.85 * _flash))
		draw_arc(Vector2.ZERO, r, 0.0, TAU, 32, Color(Color.WHITE, _flash), 2.0)
	elif _landed:
		var pulse := 0.5 + 0.5 * sin(_age * 25.0)
		draw_circle(Vector2.ZERO, blast_radius, Color(RING, 0.08 + 0.06 * pulse))
		for k in 12:
			var a := _age * 3.0 + k * TAU / 12.0
			draw_arc(Vector2.ZERO, blast_radius, a, a + TAU / 24.0, 4, Color(RING, 0.7 + 0.3 * pulse), 2.0)
