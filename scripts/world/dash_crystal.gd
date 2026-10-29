class_name DashCrystal
extends Area2D

const SHEET := "res://assets/sprites/props/dash_crystal.json"
const PLAYER_LAYER := 2
const GLOW := Color(0.55, 0.7, 1.0)

@export var respawn_time := 2.5

var _sprite: AnimatedSprite2D
var _light: PointLight2D
var _active := true
var _time := 0.0


static func create(center: Vector2) -> DashCrystal:
	var crystal := DashCrystal.new()
	crystal.position = center
	return crystal


func _ready() -> void:
	collision_layer = 0
	collision_mask = PLAYER_LAYER
	_sprite = AnimatedSprite2D.new()
	_sprite.sprite_frames = SpriteSheet.frames(SHEET)
	_sprite.material = Lights.unshaded()
	_sprite.play(&"idle")
	add_child(_sprite)
	_light = Lights.point(GLOW, 30.0, 0.7)
	add_child(_light)
	var circle := CircleShape2D.new()
	circle.radius = 13.0
	var shape := CollisionShape2D.new()
	shape.shape = circle
	add_child(shape)
	_time = position.x * 0.05


func _physics_process(delta: float) -> void:
	_time += delta
	_sprite.position.y = roundf(sin(_time * 2.6) * 2.0)
	_sprite.scale = _sprite.scale.lerp(Vector2.ONE, 1.0 - exp(-12.0 * delta))
	if not _active:
		return
	for body in get_overlapping_bodies():
		var player := body as Player
		if player and not player.is_dead() and player.dash_charges < 1 and Game.has_ability(&"dash"):
			_collect(player)
			return


func _collect(player: Player) -> void:
	_active = false
	player.refill_air_moves()
	AudioManager.play_sfx(&"crystal")
	Combat.burst(self, global_position, Color("9fb4e8"), 10, 110.0)
	_sprite.play(&"empty")
	_sprite.scale = Vector2(1.6, 1.6)
	_light.visible = false
	await get_tree().create_timer(respawn_time, false, true).timeout
	_active = true
	_sprite.play(&"idle")
	_sprite.scale = Vector2(0.4, 0.4)
	_light.visible = true
