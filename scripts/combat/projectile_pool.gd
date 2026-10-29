class_name ProjectilePool
extends Node2D

const GROUP := &"projectile_pool"
const MAX_ACTIVE := 200

var _idle: Array[Projectile] = []
var _active: Array[Projectile] = []


static func of(node: Node) -> ProjectilePool:
	var tree := node.get_tree()
	var pool := tree.get_first_node_in_group(GROUP) as ProjectilePool
	if pool == null:
		pool = ProjectilePool.new()
		pool.name = "Projectiles"
		(tree.current_scene if tree.current_scene else tree.root).add_child(pool)
	return pool


func _init() -> void:
	add_to_group(GROUP)


func _ready() -> void:
	Events.player_died.connect(_on_player_died)


func spawn(at: Vector2, direction: Vector2, spec: ShotSpec, target: Player) -> Projectile:
	if _active.size() >= MAX_ACTIVE:
		return null
	var projectile: Projectile
	if _idle.is_empty():
		projectile = Projectile.new()
		projectile.finished.connect(_on_finished)
		add_child(projectile)
	else:
		projectile = _idle.pop_back()
	_active.append(projectile)
	projectile.fire(at, direction, spec, target)
	return projectile


func active_count() -> int:
	return _active.size()


func active_projectiles() -> Array[Projectile]:
	return _active.duplicate()


func clear() -> void:
	for projectile: Projectile in _active.duplicate():
		projectile.pop(false)


func _on_player_died(_at: Vector2) -> void:
	clear()


func _on_finished(projectile: Projectile) -> void:
	_active.erase(projectile)
	_idle.append(projectile)
