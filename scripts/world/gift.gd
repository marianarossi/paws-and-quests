class_name Gift
extends Area2D

const TEXTURE := preload("res://assets/sprites/props/gift_rose.png")
const PLAYER_LAYER := 2
const GLOW := Color(1.0, 0.72, 0.84)
const PETALS := Color("ffb8cf")

var ability: StringName = &"dash"
var _sprite: Sprite2D
var _light: PointLight2D
var _time := 0.0
var _taken := false


static func create(center: Vector2, gives: StringName) -> Gift:
	var gift := Gift.new()
	gift.position = center
	gift.ability = gives
	return gift


func _ready() -> void:
	if Game.has_ability(ability):
		queue_free()
		return
	collision_layer = 0
	collision_mask = PLAYER_LAYER
	_sprite = Sprite2D.new()
	_sprite.texture = TEXTURE
	_sprite.material = Lights.unshaded()
	add_child(_sprite)
	_light = Lights.point(GLOW, 56.0, 0.9)
	add_child(_light)
	var circle := CircleShape2D.new()
	circle.radius = 10.0
	var shape := CollisionShape2D.new()
	shape.shape = circle
	add_child(shape)
	body_entered.connect(_on_body_entered)


func _physics_process(delta: float) -> void:
	if _taken:
		return
	if Game.has_ability(ability):
		queue_free()
		return
	_time += delta
	_sprite.position.y = roundf(sin(_time * 2.0) * 2.0)
	_light.energy = 0.8 + 0.2 * sin(_time * 3.1)
	if fmod(_time, 1.4) < delta:
		Combat.burst(self, global_position + Vector2(0, -4), PETALS, 2, 24.0)


func _on_body_entered(body: Node2D) -> void:
	var player := body as Player
	if _taken or player == null or player.is_dead():
		return
	_taken = true
	Game.set_ability(ability, true)
	player.refill_air_moves()
	AudioManager.play_sfx(&"gift", 0.0, 0.0)
	Combat.burst(self, global_position, PETALS, 22, 130.0)
	Combat.burst(self, global_position, GLOW, 10, 70.0)
	Events.gift_received.emit(ability)
	var tween := create_tween().set_parallel()
	tween.tween_property(_sprite, "scale", Vector2(2.0, 2.0), 0.5)
	tween.tween_property(_sprite, "modulate:a", 0.0, 0.5)
	tween.tween_property(_light, "energy", 0.0, 0.8)
	tween.chain().tween_callback(queue_free)
