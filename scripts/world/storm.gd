class_name Storm
extends Node2D

const GROUP := &"storm"
const BOLTS := preload("res://assets/sprites/combat/storm_bolt.png")
const BIG_BOLT := preload("res://assets/sprites/combat/storm_bolt_big.png")
const BOLT_FRAMES := 4
const BOLT_SHAPES := 3
const FLICKER: Array[int] = [0, 1, 0, 2, 1, 0, 2]
const SCREEN := Vector2(640, 360)
const ENTRY_DELAY := 1.2
const FLASH_COLOR := Color(0.56, 0.68, 0.95)

var every_min := 4.0
var every_max := 11.0
var entry := true
var room_id := ""

var _timer := 3.0
var _was_here := false
var _flash: ColorRect
var _flash_tween: Tween
var _sky: CanvasLayer


static func create(def: Dictionary, in_room: String) -> Storm:
	var storm := Storm.new()
	storm.room_id = in_room
	var every := String(def.get("every", "4-11")).split("-")
	storm.every_min = float(every[0])
	storm.every_max = float(every[every.size() - 1])
	storm.entry = String(def.get("entry", "1")) != "0"
	return storm


static func flash_screen(tree: SceneTree, strength: float) -> void:
	var storm := tree.get_first_node_in_group(GROUP) as Storm
	if storm:
		storm.flash(strength)
	else:
		for background: Background in tree.get_nodes_in_group(Background.GROUP):
			background.flash(strength)


func _ready() -> void:
	add_to_group(GROUP)
	var top := CanvasLayer.new()
	top.layer = 30
	add_child(top)
	_flash = ColorRect.new()
	_flash.set_anchors_preset(Control.PRESET_FULL_RECT)
	_flash.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_flash.color = Color(FLASH_COLOR, 0.0)
	var add := CanvasItemMaterial.new()
	add.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	_flash.material = add
	top.add_child(_flash)
	_sky = CanvasLayer.new()
	_sky.layer = -99
	add_child(_sky)
	_timer = randf_range(every_min * 0.5, every_max * 0.5)


func _process(delta: float) -> void:
	var here := room_id == "" or Game.current_room == room_id
	if here and not _was_here and entry:
		get_tree().create_timer(ENTRY_DELAY).timeout.connect(_entry_strike)
	_was_here = here
	if not here:
		return
	_timer -= delta
	if _timer <= 0.0:
		_timer = randf_range(every_min, every_max)
		distant()


func distant() -> void:
	var strength := randf_range(0.25, 0.5)
	_sky_bolt(BOLTS, randi() % BOLT_FRAMES, Vector2(randf_range(40.0, 600.0), randf_range(0.0, 50.0)), 0.2, "far")
	flash(strength)
	get_tree().create_timer(randf_range(0.35, 1.6)).timeout.connect(
			func() -> void: AudioManager.play_sfx(&"thunder_far", linear_to_db(strength * 1.6) - 3.0, 0.1))


func _entry_strike() -> void:
	if not is_inside_tree() or Game.current_room != room_id:
		return
	_sky_bolt(BIG_BOLT, 0, Vector2(randf_range(380.0, 470.0), 0.0), 0.32, "big")
	flash(1.0)
	AudioManager.play_sfx(&"thunder", 2.0, 0.0)
	get_tree().call_group(PalaceDoor.GROUP, &"slam")
	var camera := get_viewport().get_camera_2d()
	if camera and camera.has_method(&"shake"):
		camera.call(&"shake", 4.0, 0.8)


func flash(strength: float) -> void:
	if _flash_tween:
		_flash_tween.kill()
	var peak := clampf(strength, 0.0, 1.0) * 0.75
	_flash_tween = create_tween()
	_flash_tween.tween_property(_flash, "color:a", peak, 0.03)
	_flash_tween.tween_property(_flash, "color:a", peak * 0.15, 0.06)
	_flash_tween.tween_property(_flash, "color:a", peak * 0.8, 0.04)
	_flash_tween.tween_property(_flash, "color:a", 0.0, 0.5 + strength * 0.4).set_trans(Tween.TRANS_EXPO).set_ease(Tween.EASE_OUT)
	for background: Background in get_tree().get_nodes_in_group(Background.GROUP):
		background.flash(strength)


func _sky_bolt(texture: Texture2D, column: int, at: Vector2, time := 0.2, where := "") -> void:
	var sprite := Sprite2D.new()
	sprite.texture = texture
	sprite.centered = false
	var columns := BOLT_FRAMES if texture == BOLTS else 1
	var size := Vector2(texture.get_width() / columns, texture.get_height() / BOLT_SHAPES)
	sprite.region_enabled = true
	sprite.region_rect = Rect2(Vector2(size.x * column, 0), size)
	sprite.flip_h = randf() < 0.5
	sprite.position = (at - Vector2(size.x * 0.5, 0)).round()
	var holder: Node = null
	var background := get_tree().get_first_node_in_group(Background.GROUP) as Background
	if background:
		sprite.material = Lights.unshaded()
		holder = background.add_behind(sprite, where)
	if holder == null:
		_sky.add_child(sprite)
		holder = sprite
	_flicker(sprite, size, column, time, holder)


func strike(ground: Vector2, strength := 1.0) -> void:
	var sprite := Sprite2D.new()
	sprite.texture = BIG_BOLT
	sprite.centered = false
	var size := Vector2(BIG_BOLT.get_width(), BIG_BOLT.get_height() / BOLT_SHAPES)
	sprite.region_enabled = true
	sprite.region_rect = Rect2(Vector2.ZERO, size)
	sprite.material = Lights.unshaded()
	sprite.top_level = true
	sprite.z_index = 40
	add_child(sprite)
	sprite.global_position = (ground - Vector2(size.x * 0.5, size.y)).round()
	_flicker(sprite, size, 0, 0.32, sprite)
	flash(strength)
	AudioManager.play_sfx(&"thunder", 2.0, 0.0)
	var camera := get_viewport().get_camera_2d()
	if camera and camera.has_method(&"shake"):
		camera.call(&"shake", 4.0, 0.8)


func _flicker(sprite: Sprite2D, size: Vector2, column: int, time: float, holder: Node) -> void:
	var tween := sprite.create_tween()
	for i in FLICKER.size():
		var shape := Rect2(Vector2(size.x * column, size.y * FLICKER[i]), size)
		tween.tween_callback(func() -> void: sprite.region_rect = shape).set_delay(randf_range(0.02, 0.05))
		if i == 2:
			tween.tween_property(sprite, "visible", false, 0.0)
			tween.tween_property(sprite, "visible", true, 0.0).set_delay(0.04)
	tween.tween_property(sprite, "modulate:a", 0.0, time).set_trans(Tween.TRANS_EXPO).set_ease(Tween.EASE_IN)
	tween.tween_callback(holder.queue_free)
