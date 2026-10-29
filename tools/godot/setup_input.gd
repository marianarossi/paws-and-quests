extends SceneTree


func _init() -> void:
	var actions := {
		"move_left": [_key(KEY_A), _key(KEY_LEFT), _axis(JOY_AXIS_LEFT_X, -1.0), _btn(JOY_BUTTON_DPAD_LEFT)],
		"move_right": [_key(KEY_D), _key(KEY_RIGHT), _axis(JOY_AXIS_LEFT_X, 1.0), _btn(JOY_BUTTON_DPAD_RIGHT)],
		"move_up": [_key(KEY_W), _key(KEY_UP), _axis(JOY_AXIS_LEFT_Y, -1.0), _btn(JOY_BUTTON_DPAD_UP)],
		"move_down": [_key(KEY_S), _key(KEY_DOWN), _axis(JOY_AXIS_LEFT_Y, 1.0), _btn(JOY_BUTTON_DPAD_DOWN)],
		"jump": [_key(KEY_SPACE), _key(KEY_Z), _btn(JOY_BUTTON_A)],
		"dash": [_key(KEY_SHIFT), _key(KEY_X), _key(KEY_K), _btn(JOY_BUTTON_B), _axis(JOY_AXIS_TRIGGER_RIGHT, 1.0)],
		"attack": [_key(KEY_J), _key(KEY_C), _btn(JOY_BUTTON_X)],
		"pause": [_key(KEY_ESCAPE), _btn(JOY_BUTTON_START)],
	}
	for action: String in actions:
		var deadzone := 0.35 if action.begins_with("move_") else 0.5
		ProjectSettings.set_setting("input/" + action, {"deadzone": deadzone, "events": actions[action]})
	var err := ProjectSettings.save()
	print("mapa de input gravado: ", error_string(err))
	quit(0 if err == OK else 1)


func _key(code: Key) -> InputEventKey:
	var e := InputEventKey.new()
	e.device = -1
	e.physical_keycode = code
	return e


func _btn(button: JoyButton) -> InputEventJoypadButton:
	var e := InputEventJoypadButton.new()
	e.device = -1
	e.button_index = button
	return e


func _axis(axis: JoyAxis, value: float) -> InputEventJoypadMotion:
	var e := InputEventJoypadMotion.new()
	e.device = -1
	e.axis = axis
	e.axis_value = value
	return e
