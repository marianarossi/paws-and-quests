class_name Settings

const PATH := "user://settings.cfg"
const STEPS := 10
const DEFAULTS := {"music": 8, "sfx": 8, "fullscreen": true, "vsync": true, "language": "en",
	"assist": false, "assist_invincible": false, "assist_infinite_dash": false,
	"look_skin": "tone1", "look_hair": "auburn", "look_eyes": "green", "look_jacket": "indigo",
	"look_pack": "green", "look_pants": "charcoal", "look_boots": "brown",
	"look_hat_color": "red", "look_scarf_color": "red",
	"look_hat": "none", "look_beard": "full", "look_glasses": "none", "look_scarf": "none"}
const LANGUAGES := [["en", &"LANGUAGE_EN"], ["pt_BR", &"LANGUAGE_PT_BR"]]
const WINDOW_FILL := 0.8
const BASE := Vector2i(640, 360)

static var path := PATH
static var _values: Dictionary = {}


static func value(key: String) -> Variant:
	_ensure_loaded()
	return _values[key]


static func change(key: String, new_value: Variant) -> void:
	change_many({key: new_value})


static func change_many(changes: Dictionary) -> void:
	_ensure_loaded()
	for key: String in changes:
		_values[key] = changes[key]
	apply()
	var config := ConfigFile.new()
	for k: String in _values:
		config.set_value("options", k, _values[k])
	config.save(path)


static func use_file(file: String) -> void:
	path = file
	_values = {}
	apply()


static func locale() -> String:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--lang="):
			return arg.get_slice("=", 1)
	var chosen := String(value("language"))
	if chosen != "":
		return chosen
	return "en"


static func language_index() -> int:
	for i in LANGUAGES.size():
		if LANGUAGES[i][0] == locale():
			return i
	return 0


static func assist_on() -> bool:
	return bool(value("assist"))


static func invincible() -> bool:
	return assist_on() and bool(value("assist_invincible"))


static func infinite_dash() -> bool:
	return assist_on() and bool(value("assist_infinite_dash"))


static func apply() -> void:
	_ensure_loaded()
	_bus_volume(&"Music", int(_values["music"]))
	_bus_volume(&"SFX", int(_values["sfx"]))
	if TranslationServer.get_locale() != locale():
		TranslationServer.set_locale(locale())
	if DisplayServer.get_name() == "headless":
		return
	var window := (Engine.get_main_loop() as SceneTree).root
	var full := bool(_values["fullscreen"])
	var is_full := window.mode == Window.MODE_FULLSCREEN or window.mode == Window.MODE_EXCLUSIVE_FULLSCREEN
	if full and not is_full:
		window.mode = Window.MODE_FULLSCREEN
	elif not full and is_full:
		window.mode = Window.MODE_WINDOWED
		_fit_window.call_deferred(window)
	if not OS.get_cmdline_args().has("--disable-vsync"):
		DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED if _values["vsync"] else DisplayServer.VSYNC_DISABLED)


static func _fit_window(window: Window) -> void:
	var screen := DisplayServer.screen_get_usable_rect(window.current_screen)
	@warning_ignore("integer_division")
	var factor := maxi(1, mini(int(screen.size.x * WINDOW_FILL) / BASE.x, int(screen.size.y * WINDOW_FILL) / BASE.y))
	window.size = BASE * factor
	window.position = screen.position + (screen.size - window.size) / 2


static func _bus_volume(bus: StringName, steps: int) -> void:
	var index := AudioServer.get_bus_index(bus)
	if index == -1:
		return
	AudioServer.set_bus_mute(index, steps <= 0)
	AudioServer.set_bus_volume_db(index, linear_to_db(maxf(steps, 1) / float(STEPS)))


static func _ensure_loaded() -> void:
	if not _values.is_empty():
		return
	_values = DEFAULTS.duplicate()
	var config := ConfigFile.new()
	if config.load(path) == OK:
		for key: String in DEFAULTS:
			_values[key] = config.get_value("options", key, DEFAULTS[key])
