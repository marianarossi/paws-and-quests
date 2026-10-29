extends Node2D

const ROOM_PATH := "res://levels/dev/movement_lab.room"
const PLAYER_SCENE := preload("res://scenes/player/player.tscn")
const DEMO: Array = [
	[0.3, &"move_right", true],
	[0.7, &"jump", true], [1.05, &"jump", false],
	[1.25, &"jump", true], [1.6, &"jump", false],
	[1.8, &"jump", true], [2.15, &"jump", false],
	[2.35, &"jump", true], [2.6, &"jump", false], [2.7, &"jump", true], [3.0, &"jump", false],
	[3.4, &"dash", true], [3.45, &"dash", false],
	[3.9, &"jump", true], [4.2, &"jump", false],
	[4.3, &"move_up", true], [4.35, &"dash", true], [4.4, &"dash", false], [4.5, &"move_up", false],
	[5.0, &"jump", true], [5.3, &"jump", false],
	[8.0, &"move_right", false],
]

var _room: Room
var _hint_layer: CanvasLayer
var _player: Player

@onready var _camera: RoomCamera = $RoomCamera
@onready var _overlay: CanvasLayer = $DebugOverlay


func _ready() -> void:
	Game.unlock_all()
	var data := RoomData.load_file(ROOM_PATH)
	var theme := ZoneTheme.of(data.zone)
	($CanvasModulate as CanvasModulate).color = theme.ambient
	var background := Background.new()
	background.setup(theme)
	add_child(background)
	_room = RoomBuilder.build(data, theme)
	add_child(_room)
	_player = PLAYER_SCENE.instantiate()
	_room.add_child(_player)
	_player.teleport(_room.spawn_point)
	_camera.follow(_player, _room.bounds)
	var ambient := Background.make_ambient(theme)
	if ambient:
		_camera.add_child(ambient)
	_overlay.call(&"watch", _player)
	_add_hint()
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--shot"):
			_take_screenshot(float(arg.get_slice("=", 1)) if arg.contains("=") else 2.0)
	if OS.get_cmdline_user_args().has("--bench"):
		_run_benchmark()
	var args := OS.get_cmdline_user_args()
	if args.has("--demo") or args.has("--demo=dash"):
		var playback := InputPlayback.new()
		add_child(playback)
		playback.play(DEMO if args.has("--demo") else [[0.3, &"dash", true], [0.35, &"dash", false]])


func _unhandled_key_input(event: InputEvent) -> void:
	var key := event as InputEventKey
	if key == null or not key.pressed or key.echo:
		return
	match key.keycode:
		KEY_R:
			_player.teleport(_room.spawn_point)
		KEY_1:
			Game.set_ability(&"dash", not Game.has_ability(&"dash"))
		KEY_2:
			Game.set_ability(&"double_jump", not Game.has_ability(&"double_jump"))
		KEY_F3:
			_overlay.visible = not _overlay.visible
		KEY_F11:
			var window := get_window()
			window.mode = Window.MODE_FULLSCREEN if window.mode == Window.MODE_WINDOWED else Window.MODE_WINDOWED
		KEY_ESCAPE:
			get_tree().quit()


func _run_benchmark() -> void:
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	Engine.max_fps = 0
	await get_tree().create_timer(2.0).timeout
	var frames := Engine.get_frames_drawn()
	await get_tree().create_timer(4.0).timeout
	var fps := (Engine.get_frames_drawn() - frames) / 4.0
	print("BENCH %s  %.0f fps sem vsync  (monitor a %.0f Hz)" % [get_window().size, fps, DisplayServer.screen_get_refresh_rate()])
	get_tree().quit()


func _take_screenshot(delay: float) -> void:
	_overlay.visible = false
	_hint_layer.visible = false
	await get_tree().create_timer(delay).timeout
	await RenderingServer.frame_post_draw
	var folder := ProjectSettings.globalize_path("res://captures")
	DirAccess.make_dir_recursive_absolute(folder)
	get_viewport().get_texture().get_image().save_png(folder.path_join("shot.png"))
	print("SHOT ", _player.get_global_transform_with_canvas().origin / Vector2(get_viewport().get_visible_rect().size))
	get_tree().quit()


func _add_hint() -> void:
	var layer := CanvasLayer.new()
	layer.layer = 50
	add_child(layer)
	_hint_layer = layer
	var hint := Label.new()
	hint.text = "LAB_HINT"
	hint.position = Vector2(4, 330)
	hint.size = Vector2(632, 0)
	hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	hint.add_theme_font_size_override(&"font_size", 8)
	hint.add_theme_constant_override(&"outline_size", 3)
	hint.add_theme_color_override(&"font_outline_color", Color.BLACK)
	layer.add_child(hint)
