class_name DogNpc
extends Node2D

const GROUP := &"dog"
const SPRITE_OFFSET := Vector2(-16, -31)
const MOUTH := Vector2(11, -9)

var sprite: AnimatedSprite2D
var sheet := "dog"
var camp := false
var facing := 1
var carried: Node2D


static func create(feet: Vector2, sheet_name: String, anim: StringName, dir: int) -> DogNpc:
	var dog := DogNpc.new()
	dog.position = feet
	dog.sheet = sheet_name
	dog.facing = dir
	dog.set_meta(&"anim", anim)
	return dog


func _ready() -> void:
	if camp and Game.dog_taken:
		queue_free()
		return
	add_to_group(GROUP)
	if camp:
		Events.room_entered.connect(func(_id: String) -> void:
			if Game.dog_taken:
				queue_free())
	sprite = AnimatedSprite2D.new()
	sprite.sprite_frames = SpriteSheet.frames("res://assets/sprites/%s/%s.json" % [sheet, sheet])
	sprite.centered = false
	sprite.position = SPRITE_OFFSET
	add_child(sprite)
	face(facing)
	play_anim(get_meta(&"anim", &"idle"))


func play_anim(anim: StringName) -> void:
	if sprite.animation != anim or not sprite.is_playing():
		sprite.play(anim)


func face(dir: int) -> void:
	facing = 1 if dir >= 0 else -1
	sprite.flip_h = facing < 0
	_place_carried()


func run_to(x: float, speed := 150.0, anim: StringName = &"run") -> void:
	var distance := x - global_position.x
	if absf(distance) < 1.0:
		return
	face(int(signf(distance)))
	play_anim(anim)
	var tween := create_tween()
	tween.tween_property(self, "global_position:x", x, absf(distance) / speed)
	tween.tween_callback(_place_carried)
	await tween.finished
	play_anim(&"idle")


func jump_to(feet: Vector2, height := 20.0, time := 0.55) -> void:
	var from := global_position
	face(int(signf(feet.x - from.x)) if absf(feet.x - from.x) > 1.0 else facing)
	play_anim(&"jump")
	var tween := create_tween()
	tween.tween_method(_hop.bind(from, feet, height), 0.0, 1.0, time)
	await tween.finished
	play_anim(&"land")
	await get_tree().create_timer(0.12).timeout
	play_anim(&"idle")


func _hop(t: float, from: Vector2, to: Vector2, height: float) -> void:
	var top := minf(from.y, to.y) - height
	var y := lerpf(lerpf(from.y, top, t), lerpf(top, to.y, t), t)
	global_position = Vector2(lerpf(from.x, to.x, t), y).round()
	if t > 0.5 and sprite.animation == &"jump":
		play_anim(&"fall")


func pick_up(item: Node2D) -> void:
	carried = item
	_place_carried()


func drop() -> Node2D:
	var item := carried
	carried = null
	if item:
		item.global_position = global_position + Vector2(MOUTH.x * facing, -3)
	return item


func _process(_delta: float) -> void:
	_place_carried()


func _place_carried() -> void:
	if carried and sprite:
		carried.global_position = global_position + Vector2(MOUTH.x * facing, MOUTH.y)
