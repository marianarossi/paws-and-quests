class_name Hint
extends Node2D

const RANGE := Vector2(72, 64)
const RISE := 34.0
const TEXT := Color("fff6e8")
const SHADOW := Color("1c1433")
const CAP_FILL := Color("2a2346")
const CAP_EDGE := Color("d8cbe6")
const ACTIONS := {
	"jump": &"jump", "dash": &"dash", "up": &"move_up", "down": &"move_down",
	"left": &"move_left", "right": &"move_right", "grab": &"grab",
}
const MODIFIERS: Array[Key] = [KEY_CTRL, KEY_SHIFT, KEY_ALT, KEY_META]
const SKIP_MODIFIER: Array[StringName] = [&"grab"]
const PAD_NAMES := {
	JOY_BUTTON_A: "A", JOY_BUTTON_B: "B", JOY_BUTTON_X: "X", JOY_BUTTON_Y: "Y",
	JOY_BUTTON_DPAD_UP: "UP", JOY_BUTTON_DPAD_DOWN: "DOWN", JOY_BUTTON_DPAD_LEFT: "LEFT",
	JOY_BUTTON_DPAD_RIGHT: "RIGHT", JOY_BUTTON_LEFT_SHOULDER: "LB", JOY_BUTTON_RIGHT_SHOULDER: "RB",
}

static var _pad := false

var text_key := ""
var forced := false
var follow: Node2D
var follow_offset := Vector2.ZERO
var _alpha := 0.0
var _drawn_pad := false


static func create(feet: Vector2, key: String) -> Hint:
	var hint := Hint.new()
	hint.position = feet
	hint.text_key = key
	return hint


func _ready() -> void:
	z_index = 30
	material = Lights.unshaded()
	modulate.a = 0.0


func _notification(what: int) -> void:
	if what == NOTIFICATION_TRANSLATION_CHANGED:
		queue_redraw()


func _input(event: InputEvent) -> void:
	if event is InputEventJoypadButton or (event is InputEventJoypadMotion and absf(event.axis_value) > 0.5):
		_pad = true
	elif event is InputEventKey:
		_pad = false


func _process(delta: float) -> void:
	if is_instance_valid(follow):
		global_position = (follow.global_position + follow_offset).round()
	var player := Combat.find_player(self)
	var near := false
	if forced:
		near = true
	elif player and not player.is_dead() and player.input_enabled:
		var offset := player.global_position - global_position
		near = absf(offset.x) < RANGE.x and absf(offset.y) < RANGE.y
	_alpha = move_toward(_alpha, 1.0 if near else 0.0, delta * (2.5 if near else 1.6))
	modulate.a = _alpha
	if _drawn_pad != _pad:
		queue_redraw()


func _draw() -> void:
	_drawn_pad = _pad
	var font := PixelFont.get_font()
	var size := PixelFont.size()
	var parts := _parts()
	var width := 0.0
	for part: Array in parts:
		width += _width(font, size, part)
	var x := -roundf(width * 0.5)
	var baseline := -RISE + size
	for part: Array in parts:
		var label: String = part[0]
		var w := _width(font, size, part)
		if part[1]:
			var box := Rect2(x, -RISE - 3, w - 2, size + 5)
			draw_rect(Rect2(box.position + Vector2(1, 1), box.size), SHADOW)
			draw_rect(box.grow(-1), CAP_FILL)
			draw_line(box.position + Vector2(1, 0.5), Vector2(box.end.x - 1, box.position.y + 0.5), CAP_EDGE)
			draw_line(Vector2(box.position.x + 1, box.end.y - 0.5), box.end - Vector2(1, 0.5), CAP_EDGE)
			draw_line(box.position + Vector2(0.5, 1), Vector2(box.position.x + 0.5, box.end.y - 1), CAP_EDGE)
			draw_line(Vector2(box.end.x - 0.5, box.position.y + 1), box.end - Vector2(0.5, 1), CAP_EDGE)
			draw_string(font, Vector2(x + 3, baseline), label, HORIZONTAL_ALIGNMENT_LEFT, -1, size, TEXT)
		else:
			draw_string(font, Vector2(x + 1, baseline + 1), label, HORIZONTAL_ALIGNMENT_LEFT, -1, size, SHADOW)
			draw_string(font, Vector2(x, baseline), label, HORIZONTAL_ALIGNMENT_LEFT, -1, size, TEXT)
		x += w


func _parts() -> Array:
	var parts: Array = []
	var text := tr(StringName(text_key))
	var at := 0
	while at < text.length():
		var open := text.find("{", at)
		if open < 0:
			parts.append([text.substr(at), false])
			break
		var close := text.find("}", open)
		if open > at:
			parts.append([text.substr(at, open - at), false])
		var token := text.substr(open + 1, close - open - 1)
		var labels: Array[String] = []
		if token == "grab_all":
			labels = _all_key_names(&"grab")
		else:
			labels.append(_key_name(token))
		for i in labels.size():
			if i > 0:
				parts.append([" / ", false])
			if parts.is_empty() or parts[-1] != [labels[i], true]:
				parts.append([labels[i], true])
		at = close + 1
	return parts


func _all_key_names(action: StringName) -> Array[String]:
	var names: Array[String] = []
	if _pad or not InputMap.has_action(action):
		names.append(_key_name(String(action)))
		return names
	var last: Array[String] = []
	for event in InputMap.action_get_events(action):
		if event is InputEventKey:
			var code: Key = event.keycode if event.keycode != KEY_NONE else event.physical_keycode
			var name := _keyboard_name(event, code)
			if names.has(name) or last.has(name):
				continue
			if code in MODIFIERS:
				last.append(name)
			else:
				names.append(name)
	names.append_array(last)
	if names.is_empty():
		names.append(_key_name(String(action)))
	return names


func _keyboard_name(event: InputEventKey, code: Key) -> String:
	if event.keycode == KEY_NONE and DisplayServer.get_name() != "headless":
		code = DisplayServer.keyboard_get_keycode_from_physical(code)
	return OS.get_keycode_string(code).to_upper()


func _width(font: Font, size: int, part: Array) -> float:
	var w := font.get_string_size(part[0], HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
	return w + 7.0 if part[1] else w


func _key_name(token: String) -> String:
	var action: StringName = ACTIONS.get(token, StringName(token))
	if not InputMap.has_action(action):
		return token.to_upper()
	for allow_modifier in [false, true]:
		for event in InputMap.action_get_events(action):
			if _pad and event is InputEventJoypadButton:
				return PAD_NAMES.get(event.button_index, "B%d" % event.button_index)
			if not _pad and event is InputEventKey:
				var code: Key = event.keycode
				if code == KEY_NONE:
					code = event.physical_keycode
				if code in MODIFIERS and action in SKIP_MODIFIER and not allow_modifier:
					continue
				if event.keycode == KEY_NONE and DisplayServer.get_name() != "headless":
					code = DisplayServer.keyboard_get_keycode_from_physical(code)
				return OS.get_keycode_string(code).to_upper()
	return token.to_upper()
