class_name Checkpoint
extends Area2D

const SHEET := "res://assets/sprites/props/campfire.json"
const LIGHT_COLOR := Color(1.0, 0.62, 0.3)
const PLAYER_LAYER := 2

@export var light_radius := 150.0
@export var light_energy := 1.4
@export var halo_radius := 76.0
@export var halo_strength := 0.3

var lit := false

var _sheet := SHEET

var _sprite: AnimatedSprite2D
var _light: PointLight2D
var _halo: Sprite2D
var _glow := 0.0
var _time := 0.0


static func create(feet: Vector2, sheet := SHEET) -> Checkpoint:
	var checkpoint := Checkpoint.new()
	checkpoint.position = feet
	checkpoint._sheet = sheet
	return checkpoint


func _ready() -> void:
	collision_layer = 0
	collision_mask = PLAYER_LAYER
	_sprite = AnimatedSprite2D.new()
	_sprite.sprite_frames = SpriteSheet.frames(_sheet)
	_sprite.scale = SpriteSheet.unit_scale(_sheet)
	_sprite.position = Vector2(0, -float((load(_sheet) as JSON).data["frame_h"]) * 0.5)
	_sprite.play(&"unlit")
	add_child(_sprite)
	_halo = Sprite2D.new()
	_halo.texture = Lights.radial()
	_halo.scale = Vector2.ONE * halo_radius / Lights.TEXTURE_RADIUS
	_halo.position = Vector2(0, -14)
	_halo.z_index = -1
	_halo.modulate = Color(LIGHT_COLOR, 0.0)
	var add_blend := CanvasItemMaterial.new()
	add_blend.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	add_blend.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	_halo.material = add_blend
	add_child(_halo)
	_light = Lights.point(LIGHT_COLOR, light_radius, 0.0)
	_light.position = Vector2(0, -10)
	add_child(_light)
	var box := RectangleShape2D.new()
	box.size = Vector2(22, 26)
	var shape := CollisionShape2D.new()
	shape.shape = box
	shape.position = Vector2(0, -13)
	add_child(shape)
	body_entered.connect(_on_body_entered)


func _on_body_entered(body: Node2D) -> void:
	if not body is Player:
		return
	if lit:
		return
	light_up()
	Events.checkpoint_reached.emit(self)


func light_up(silent := false) -> void:
	lit = true
	_sprite.play(&"burn")
	_sprite.material = Lights.unshaded()
	create_tween().tween_property(self, "_glow", light_energy, 0.0 if silent else 0.5)
	if not silent:
		AudioManager.play_sfx(&"checkpoint")


func _process(delta: float) -> void:
	_time += delta
	var flicker := 1.0 + 0.07 * sin(_time * 11.0) + 0.05 * sin(_time * 23.7)
	_light.energy = _glow * flicker
	_halo.modulate.a = halo_strength * flicker * _glow / light_energy
