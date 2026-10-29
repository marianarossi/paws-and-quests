class_name Feather
extends Area2D

const TEXTURE := preload("res://assets/sprites/props/feather.png")
const FRAME := Vector2(14, 16)
const PLAYER_LAYER := 2

var key := ""

var _time := 0.0
var _sprite: Sprite2D
var _taken := false


static func create(center: Vector2, id: String) -> Feather:
	var feather := Feather.new()
	feather.position = center
	feather.key = id
	return feather


func _ready() -> void:
	collision_layer = 0
	collision_mask = PLAYER_LAYER
	var circle := CircleShape2D.new()
	circle.radius = 9.0
	var shape := CollisionShape2D.new()
	shape.shape = circle
	add_child(shape)
	_sprite = Sprite2D.new()
	_sprite.texture = TEXTURE
	_sprite.region_enabled = true
	_sprite.region_rect = Rect2(Vector2.ZERO, FRAME)
	_sprite.material = Lights.unshaded()
	_sprite.z_index = 12
	add_child(_sprite)
	_taken = Game.has_feather(key)
	if not _taken:
		add_child(Lights.point(Color("#ffe2b8"), 36.0, 0.8))
	body_entered.connect(_on_body_entered)


func _process(delta: float) -> void:
	_time += delta
	_sprite.position.y = roundf(sin(_time * 2.2) * 2.0)
	var frame := 6 if _taken else int(_time * 8.0) % 6
	_sprite.region_rect.position.x = frame * FRAME.x


func _on_body_entered(body: Node2D) -> void:
	if _taken or not body is Player:
		return
	_taken = true
	Game.take_feather(key)
	AudioManager.play_sfx(&"collectible")
	Combat.burst(get_parent(), global_position, Color("#fff0dc"), 12, 80.0)
	Events.feather_collected.emit(Game.feather_count())
	for child in get_children():
		if child is PointLight2D:
			child.queue_free()
