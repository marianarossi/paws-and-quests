class_name Enemy
extends Area2D

const HAZARD_LAYER := 4
const ENEMY_LAYER := 8
const GROUP := &"enemy"

var room_id := ""
var alive := true

var _home := Vector2.ZERO
var _sprite: AnimatedSprite2D
var _sprite_base := Vector2.ZERO
var facing := 1
var _strip_tween: Tween


func _ready() -> void:
	collision_layer = HAZARD_LAYER | ENEMY_LAYER
	collision_mask = 0
	z_index = 8
	add_to_group(GROUP)
	_home = position
	Events.player_respawned.connect(revive)


func setup_body(sheet: String, anim: StringName, sprite_offset: Vector2, shape: Shape2D, shape_offset: Vector2) -> void:
	_sprite = AnimatedSprite2D.new()
	_sprite.sprite_frames = SpriteSheet.frames(sheet)
	_sprite.position = sprite_offset
	_sprite_base = sprite_offset
	_sprite.material = Lights.unshaded()
	_sprite.play(anim)
	add_child(_sprite)
	var collision := CollisionShape2D.new()
	collision.shape = shape
	collision.position = shape_offset
	add_child(collision)


func is_active() -> bool:
	return alive and Game.current_room == room_id


func face(dir: int) -> void:
	if dir == 0:
		return
	facing = dir
	_sprite.flip_h = dir < 0
	_sprite.position.x = _sprite_base.x * dir


func play(anim: StringName) -> void:
	if _strip_tween and _strip_tween.is_valid():
		_strip_tween.kill()
		_sprite.stop()
	if _sprite.animation != anim or not _sprite.is_playing():
		_sprite.play(anim)


func strip(anim: StringName, first: int, last: int, duration: float) -> void:
	if _strip_tween and _strip_tween.is_valid():
		_strip_tween.kill()
	_sprite.play(anim)
	_sprite.pause()
	var count := _sprite.sprite_frames.get_frame_count(anim)
	_sprite.frame = mini(first, count - 1)
	last = mini(last, count - 1)
	if last != first and duration > 0.0:
		_strip_tween = create_tween()
		_strip_tween.tween_property(_sprite, "frame", last, duration)


func floor_at(point: Vector2) -> bool:
	var ray := PhysicsRayQueryParameters2D.create(point + Vector2(0, -4), point + Vector2(0, 6), Combat.WORLD_LAYER)
	return not get_world_2d().direct_space_state.intersect_ray(ray).is_empty()


func blocked(dir: int, reach: float, height := 6.0) -> bool:
	return wall_ahead(dir, reach, height) or not floor_at(global_position + Vector2(dir * reach, 0))


func wall_ahead(dir: int, reach: float, height := 6.0) -> bool:
	var from := global_position + Vector2(0, -height)
	var wall := PhysicsRayQueryParameters2D.create(from, from + Vector2(dir * reach, 0), Combat.WORLD_LAYER)
	return not get_world_2d().direct_space_state.intersect_ray(wall).is_empty()


func clear_distance(from: Vector2, dir: Vector2, limit: float) -> float:
	var ray := PhysicsRayQueryParameters2D.create(from, from + dir.normalized() * limit, Combat.WORLD_LAYER)
	var hit := get_world_2d().direct_space_state.intersect_ray(ray)
	return limit if hit.is_empty() else from.distance_to(hit["position"])


func ground_below(point: Vector2, depth: float) -> float:
	var ray := PhysicsRayQueryParameters2D.create(point + Vector2(0, -3), point + Vector2(0, depth + 1.0), Combat.WORLD_LAYER)
	var hit := get_world_2d().direct_space_state.intersect_ray(ray)
	return INF if hit.is_empty() else float(hit["position"].y)


func target() -> Player:
	return Combat.find_player(self)


func revive() -> void:
	alive = true
	position = _home
	visible = true
	modulate = Color.WHITE
	_sprite.position = _sprite_base * Vector2(facing, 1)
	set_deferred(&"monitorable", true)
	_on_revived()


func vanish() -> void:
	alive = false
	set_deferred(&"monitorable", false)
	_sprite.play(&"die")
	await _sprite.animation_finished
	if not alive:
		visible = false


func _on_revived() -> void:
	pass
