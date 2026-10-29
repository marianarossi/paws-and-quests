class_name SkyGlow
extends Area2D

const TEXTURE := preload("res://assets/sprites/props/sky_glow.png")
const PLAYER_LAYER := 2

var to := ""

var _time := 0.0
var _sprite: Sprite2D
var _cooldown := 0.0


static func create(center: Vector2, to_room: String) -> SkyGlow:
	var glow := SkyGlow.new()
	glow.position = center
	glow.to = to_room
	return glow


func _ready() -> void:
	collision_layer = 0
	collision_mask = PLAYER_LAYER
	var circle := CircleShape2D.new()
	circle.radius = 14.0
	var shape := CollisionShape2D.new()
	shape.shape = circle
	add_child(shape)
	_sprite = Sprite2D.new()
	_sprite.texture = TEXTURE
	_sprite.material = Lights.unshaded()
	_sprite.z_index = 11
	add_child(_sprite)
	add_child(Lights.point(Color("#ffe8d0"), 120.0, 1.2))
	body_entered.connect(_on_body_entered)


func _process(delta: float) -> void:
	_time += delta
	_cooldown -= delta
	_sprite.modulate.a = 0.75 + 0.25 * snappedf(sin(_time * 2.4) * 0.5 + 0.5, 0.25)


func _on_body_entered(body: Node2D) -> void:
	if _cooldown > 0.0 or not body is Player or to == "":
		return
	_cooldown = 2.5
	AudioManager.play_sfx(&"gift")
	Events.glow_entered.emit(to)
