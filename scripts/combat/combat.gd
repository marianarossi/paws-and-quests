class_name Combat

const MIN_TELEGRAPH := 0.45
const PROJECTILE_LAYER := 16
const WORLD_LAYER := 1
const PROJECTILE_GROUP := &"projectile"
const PLAYER_GROUP := &"player"
const AIM_OFFSET := Vector2(0, -9)
const HOT := Color("ffd0ee")
const PINK := Color("ff5fb0")
const MAGENTA := Color("c0297f")
const DEEP := Color("5a1c5e")


static func find_player(from: Node) -> Player:
	var player := from.get_tree().get_first_node_in_group(PLAYER_GROUP) as Player
	return player if player and not player.is_dead() else null


static func aim_point(player: Player) -> Vector2:
	return player.global_position + AIM_OFFSET


static func telegraph_time(asked: float) -> float:
	return maxf(asked, MIN_TELEGRAPH)


static func steer(velocity: Vector2, from: Vector2, target: Vector2, turn_rate: float, delta: float) -> Vector2:
	if velocity == Vector2.ZERO or from == target:
		return velocity
	var angle := rotate_toward(velocity.angle(), (target - from).angle(), turn_rate * delta)
	return Vector2.from_angle(angle) * velocity.length()


static func burst(parent: Node, at: Vector2, color: Color, amount := 8, speed := 90.0) -> void:
	var bits := CPUParticles2D.new()
	bits.one_shot = true
	bits.explosiveness = 1.0
	bits.amount = amount
	bits.lifetime = 0.32
	bits.spread = 180.0
	bits.gravity = Vector2.ZERO
	bits.initial_velocity_min = speed * 0.4
	bits.initial_velocity_max = speed
	bits.damping_min = speed * 1.6
	bits.damping_max = speed * 2.4
	bits.scale_amount_min = 1.0
	bits.scale_amount_max = 2.0
	var fade := Gradient.new()
	fade.colors = PackedColorArray([Color.WHITE, color, Color(color, 0.0)])
	bits.color_ramp = fade
	bits.material = Lights.unshaded()
	bits.z_index = 12
	parent.add_child(bits)
	bits.global_position = at
	bits.emitting = true
	bits.finished.connect(bits.queue_free)
