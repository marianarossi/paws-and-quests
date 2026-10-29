class_name StormHunt
extends Node2D

const LEAD := 0.85
const LEAD_MAX := 90.0
const WARN := 0.8

var every := 1.5
var room_id := ""
var from_tile := 0.0
var to_tile := 0.0
var min_x := 0.0
var max_x := 0.0

var _timer := 1.2
var _count := 0


static func create(def: Dictionary, in_room: String) -> StormHunt:
	var hunt := StormHunt.new()
	hunt.room_id = in_room
	hunt.every = float(def.get("every", hunt.every))
	hunt.from_tile = float(def.get("from", 0))
	hunt.to_tile = float(def.get("to", 0))
	return hunt


func _physics_process(delta: float) -> void:
	min_x = get_parent().to_global(Vector2(from_tile * 16.0, 0)).x
	max_x = get_parent().to_global(Vector2(to_tile * 16.0, 0)).x
	if Game.current_room != room_id:
		_timer = 1.2
		return
	var player := Combat.find_player(self)
	if player == null or player.is_dead() or player.global_position.x < min_x or player.global_position.x > max_x:
		return
	_timer -= delta
	if _timer > 0.0:
		return
	_timer = every * randf_range(0.85, 1.15)
	_count += 1
	var ahead := clampf(player.velocity.x * WARN * LEAD, -LEAD_MAX, LEAD_MAX)
	_strike_at(player, player.global_position.x + ahead)
	if _count % 3 == 0:
		var here := player.global_position.x
		if absf(ahead) < 20.0:
			here += randf_range(36.0, 52.0) * (1 if randf() < 0.5 else -1)
		_strike_at(player, here)


func _strike_at(player: Player, x: float) -> void:
	x = clampf(x, min_x, max_x)
	var from := Vector2(x, player.global_position.y - 6.0)
	var query := PhysicsRayQueryParameters2D.create(from, from + Vector2(0, 360), Combat.WORLD_LAYER)
	var hit := get_world_2d().direct_space_state.intersect_ray(query)
	if not hit.is_empty():
		LightningStrike.spawn(get_parent(), (hit.position as Vector2).round(), WARN)
