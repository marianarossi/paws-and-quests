class_name Spring
extends Area2D

const SHEET := "res://assets/sprites/props/spring_%s.json"
const PLAYER_LAYER := 2
var color := "lilac"

@export var launch_speed := 540.0

var _sprite: AnimatedSprite2D


static func create(feet: Vector2, in_color := "lilac") -> Spring:
	var spring := Spring.new()
	spring.position = feet
	spring.color = in_color
	return spring


func _ready() -> void:
	collision_layer = 0
	collision_mask = PLAYER_LAYER
	_sprite = AnimatedSprite2D.new()
	var sheet := SHEET % color
	var rgb: Array = ((load(sheet) as JSON).data as Dictionary)["light"]
	var glow := Color(rgb[0], rgb[1], rgb[2])
	_sprite.sprite_frames = SpriteSheet.frames(sheet)
	_sprite.position = Vector2(0, -11)
	_sprite.material = Lights.unshaded()
	_sprite.play(&"idle")
	add_child(_sprite)
	var light := Lights.point(glow, 64.0, 1.3)
	light.position = Vector2(0, -10)
	add_child(light)
	var halo := Sprite2D.new()
	halo.texture = Lights.radial()
	halo.scale = Vector2.ONE * 34.0 / Lights.TEXTURE_RADIUS
	halo.position = Vector2(0, -12)
	halo.z_index = -1
	halo.modulate = Color(glow, 0.3)
	var add_blend := CanvasItemMaterial.new()
	add_blend.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	add_blend.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	halo.material = add_blend
	add_child(halo)
	var box := RectangleShape2D.new()
	box.size = Vector2(16, 8)
	var shape := CollisionShape2D.new()
	shape.shape = box
	shape.position = Vector2(0, -12)
	add_child(shape)
	body_entered.connect(_on_body_entered)


func _on_body_entered(body: Node2D) -> void:
	var player := body as Player
	if player == null or player.velocity.y < -60.0:
		return
	player.launch(launch_speed)
	AudioManager.play_sfx(&"spring")
	_sprite.play(&"squash")
	await get_tree().create_timer(0.22).timeout
	_sprite.play(&"idle")
