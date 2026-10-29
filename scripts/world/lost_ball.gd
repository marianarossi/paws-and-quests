class_name LostBall
extends Area2D

const TEXTURE := preload("res://assets/sprites/props/camp_ball.png")
const SCORCH := preload("res://assets/sprites/props/camp_scorch.png")
const PLAYER_LAYER := 2
const SPEECH_COLOR := Color("ffe2b8")

var _taken := false


static func create() -> LostBall:
	return LostBall.new()


func _ready() -> void:
	collision_layer = 0
	collision_mask = PLAYER_LAYER
	var box := RectangleShape2D.new()
	box.size = Vector2(12, 12)
	var shape := CollisionShape2D.new()
	shape.shape = box
	shape.position = Vector2(0, -6)
	add_child(shape)
	var scorch := Sprite2D.new()
	scorch.texture = SCORCH
	scorch.centered = false
	scorch.position = Vector2(-16, -4)
	scorch.z_index = -1
	add_child(scorch)
	var sprite := Sprite2D.new()
	sprite.texture = TEXTURE
	sprite.hframes = 2
	sprite.position = Vector2(0, -3)
	sprite.z_index = 2
	add_child(sprite)
	body_entered.connect(_on_body_entered)


func _on_body_entered(body: Node2D) -> void:
	if _taken or not body is Player:
		return
	_taken = true
	AudioManager.play_sfx(&"ball_bounce", 0.0, 0.08)
	WoofText.say(body, body.global_position + Vector2(0, -26), tr(&"INTRO_BALL").to_upper(), false, SPEECH_COLOR, 3.2)
	for child in get_children():
		if child is Sprite2D and (child as Sprite2D).texture == TEXTURE:
			child.queue_free()
