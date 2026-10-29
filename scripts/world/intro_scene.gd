class_name IntroScene
extends Node

signal finished

const BALL := preload("res://assets/sprites/props/camp_ball.png")
const ZOOM := 2.0
const SKIP_HOLD := 0.6
const DARKEN := 0.7
const SIDE := 24.0
const NEAR_THROW := 44.0
const FAR_THROW := 330.0
const WOOF_COLOR := Color("fff6e8")
const WOOF_SHADOW := Color("1c1433")
const SPEECH_COLOR := Color("ffe2b8")

var world: World
var player: Player
var dog: DogNpc

var _ball: Sprite2D
var _hint: Hint
var _storm: Storm
var _screen: CanvasLayer
var _white: ColorRect
var _done := false
var _skipped := false
var _strike_x := NAN
var _skip_hold := 0.0
var _ambient_before := Color.WHITE
var _modulate: CanvasModulate


static func start(in_world: World, dog_npc: DogNpc) -> IntroScene:
	var scene := IntroScene.new()
	scene.world = in_world
	scene.player = in_world.player
	scene.dog = dog_npc
	in_world.add_child(scene)
	scene.run()
	return scene


func _ready() -> void:
	_screen = CanvasLayer.new()
	_screen.layer = 60
	add_child(_screen)
	_white = ColorRect.new()
	_white.set_anchors_preset(Control.PRESET_FULL_RECT)
	_white.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_white.color = Color(1, 1, 1, 0)
	_screen.add_child(_white)


func run() -> void:
	player.input_enabled = false
	player.start_roasting()
	world.camera.zoom_to(ZOOM, 1.6)
	_storm = Storm.new()
	_storm.entry = false
	_storm.every_min = 99999.0
	_storm.every_max = 99999.0
	world.add_child(_storm)
	_modulate = world.get_node_or_null(^"CanvasModulate") as CanvasModulate
	if _modulate:
		_ambient_before = _modulate.color

	_ball = Sprite2D.new()
	_ball.texture = BALL
	_ball.hframes = 2
	_ball.z_index = 2
	world.add_child(_ball)
	if await _wait(1.4):
		return
	dog.play_anim(&"idle")
	dog.pick_up(_ball)
	if await _wait(0.5):
		return
	await dog.run_to(player.global_position.x - SIDE, 60.0, &"walk")
	if _done:
		return
	_drop_at_george()

	_log("primeira bolinha")
	if not await _wait_for_throw():
		return
	var land := Vector2(player.global_position.x + NEAR_THROW, player.global_position.y - 3.0)
	await _throw(land, 30.0, 0.6)
	if _done:
		return
	await dog.run_to(land.x - 8.0, 150.0)
	if _done:
		return
	dog.pick_up(_ball)
	await dog.run_to(player.global_position.x - SIDE, 140.0)
	if _done:
		return
	_drop_at_george()
	dog.play_anim(&"happy")
	if await _wait(1.0):
		return
	dog.play_anim(&"pant")

	_log("segunda bolinha")
	if not await _wait_for_throw():
		return
	var far := Vector2(player.global_position.x + FAR_THROW, player.global_position.y - 3.0)
	_throw(far, 70.0, 1.1)
	if await _wait(0.15):
		return
	await dog.run_to(far.x + 60.0, 170.0)
	if _done:
		return
	var exit_point := Vector2(_screen_right_world_x(), dog.global_position.y)
	dog.visible = false
	_ball.visible = false

	_log("trovoada")
	if await _wait(0.9):
		return
	if _modulate:
		create_tween().tween_property(_modulate, "color", _ambient_before * Color(DARKEN, DARKEN, DARKEN * 1.08), 2.0)
	_thunder(0.55, false)
	if await _wait(0.25):
		return
	_woof(exit_point, 0)
	if await _wait(0.8):
		return
	_woof(exit_point, 1)
	if await _wait(1.2):
		return
	_thunder(0.45, false)
	if await _wait(1.3):
		return
	_thunder(0.6, false)
	if await _wait(1.1):
		return
	_log("raio forte")
	_strike_x = exit_point.x - 28.0
	_storm.strike(Vector2(_strike_x, player.global_position.y), 1.0)
	if await _wait(0.35):
		return
	var glow := create_tween()
	glow.tween_property(_white, "color:a", 1.0, 0.5).set_trans(Tween.TRANS_SINE)
	await glow.finished
	if _done:
		return
	_finish()


func _process(delta: float) -> void:
	if _done:
		return
	_skip_hold = _skip_hold + delta if Input.is_action_pressed(&"pause") else 0.0
	if _skip_hold >= SKIP_HOLD:
		skip()


func skip() -> void:
	if _done:
		return
	_done = true
	_skipped = true
	var glow := create_tween()
	glow.tween_property(_white, "color:a", 1.0, 0.25)
	glow.tween_callback(_finish)


func _wait(seconds: float) -> bool:
	await get_tree().create_timer(seconds).timeout
	return _done


func _wait_for_throw() -> bool:
	_hint = Hint.create(player.global_position + Vector2(0, -6), "HINT_THROW")
	_hint.forced = true
	world.add_child(_hint)
	var auto := OS.get_cmdline_user_args().has("--intro-auto")
	var waited := 0.0
	while not Input.is_action_just_pressed(&"jump") and not (auto and waited > 0.8):
		await get_tree().process_frame
		waited += get_process_delta_time()
		if _done:
			return false
	_hint.queue_free()
	_hint = null
	return true


func _drop_at_george() -> void:
	dog.face(1)
	dog.drop()
	_ball.global_position = Vector2(player.global_position.x - 6.0, player.global_position.y - 3.0)
	dog.play_anim(&"pant")


func _throw(land: Vector2, height: float, time: float) -> void:
	var from := _ball.global_position + Vector2(0, -12)
	var tween := create_tween()
	tween.tween_method(_arc.bind(from, land, height, 8.0), 0.0, 1.0, time)
	await tween.finished
	for hop_height: float in [10.0, 4.0]:
		if _done:
			return
		AudioManager.play_sfx(&"ball_bounce", 0.0, 0.08)
		var hop := create_tween()
		var start := _ball.global_position
		hop.tween_method(_arc.bind(start, start + Vector2(6.0, 0.0), hop_height, 4.0), 0.0, 1.0, 0.18 + hop_height * 0.02)
		await hop.finished
	AudioManager.play_sfx(&"ball_bounce", -6.0, 0.08)


func _arc(t: float, from: Vector2, to: Vector2, height: float, spins: float) -> void:
	_ball.global_position = (from.lerp(to, t) + Vector2(0, -height * sin(PI * t))).round()
	_ball.frame = int(t * spins) % 2


func _thunder(strength: float, big: bool) -> void:
	_storm._sky_bolt(Storm.BOLTS, randi() % Storm.BOLT_FRAMES, Vector2(randf_range(80.0, 560.0), randf_range(0.0, 30.0)), 0.25, "far")
	_storm.flash(strength)
	AudioManager.play_sfx(&"thunder" if big else &"thunder_far", 3.0, 0.05)
	world.camera.shake(1.5 + strength * 2.0, 0.5)


func _woof(at: Vector2, index: int) -> void:
	var text := tr(&"INTRO_WOOF")
	var font := PixelFont.get_font()
	var size := PixelFont.size()
	var width := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x * 2.0
	var screen := get_viewport().get_canvas_transform() * at
	var label := Label.new()
	label.text = text
	label.add_theme_font_override(&"font", font)
	label.add_theme_font_size_override(&"font_size", size)
	label.add_theme_color_override(&"font_color", WOOF_COLOR)
	label.add_theme_color_override(&"font_shadow_color", WOOF_SHADOW)
	label.add_theme_constant_override(&"shadow_offset_x", 1)
	label.add_theme_constant_override(&"shadow_offset_y", 1)
	label.scale = Vector2(2, 2)
	label.position = Vector2(640.0 - width - 14.0 - index * 46.0, screen.y - 46.0 - index * 34.0).round()
	label.modulate.a = 0.0
	_screen.add_child(label)
	var tween := label.create_tween()
	tween.tween_property(label, "modulate:a", 1.0, 0.12)
	tween.parallel().tween_property(label, "position:y", label.position.y - 4.0, 0.9)
	tween.tween_interval(0.5)
	tween.tween_property(label, "modulate:a", 0.0, 0.5)
	tween.tween_callback(label.queue_free)


func _screen_right_world_x() -> float:
	return (get_viewport().get_canvas_transform().affine_inverse() * Vector2(640.0, 0.0)).x


func _leave_ball() -> void:
	var x := _strike_x
	if is_nan(x):
		x = player.global_position.x + 132.0
	var room := world.current
	if room == null:
		return
	x = clampf(x, room.bounds.position.x + 24.0, room.bounds.end.x - 24.0)
	var ball := LostBall.create()
	room.add_child(ball)
	ball.global_position = Vector2(x, player.global_position.y).round()


func _look_around() -> void:
	await get_tree().create_timer(1.0).timeout
	player.facing = -1
	await get_tree().create_timer(0.55).timeout
	player.facing = 1
	await get_tree().create_timer(0.35).timeout
	_log("chama")
	_say(&"INTRO_CALL", false, 1.6)
	await get_tree().create_timer(1.5).timeout
	_log("grita")
	_say(&"INTRO_SHOUT", true, 1.8)
	await get_tree().create_timer(1.3).timeout


func _say(key: StringName, big: bool, time: float) -> void:
	WoofText.say(player, player.global_position + Vector2(0, -26), tr(key).to_upper(), big, SPEECH_COLOR, time)


func _log(step: String) -> void:
	if OS.get_cmdline_user_args().has("--intro-auto"):
		print("abertura: %s aos %.2f s" % [step, Time.get_ticks_msec() / 1000.0])


func _finish() -> void:
	_done = true
	_log("fim")
	if _hint:
		_hint.queue_free()
		_hint = null
	if is_instance_valid(dog):
		dog.queue_free()
	if _ball:
		_ball.queue_free()
	_leave_ball()
	Game.dog_taken = true
	if _modulate:
		_modulate.color = _ambient_before
	player.stand_up()
	player.facing = 1
	world.camera.focus_zoom(1.0)
	await get_tree().create_timer(0.5).timeout
	var fade := create_tween()
	fade.tween_property(_white, "color:a", 0.0, 1.3).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN)
	if _skipped:
		await get_tree().create_timer(0.4).timeout
	else:
		await _look_around()
	world.end_intro()
	finished.emit()
	await fade.finished
	if _storm:
		_storm.queue_free()
	queue_free()
