class_name EndLore
extends Node2D

signal finished

const SCALE := 2
const WIDTH := 300.0
const LINE := 13
const GAP := 9
const INK := Color("#f3e6c8")
const FADE_IN := 1.2
const READ_BASE := 0.9
const READ_CHAR := 0.04
const HOLD := 2.5
const FADE_OUT := 1.6

var _blocks: Array[Dictionary] = []
var _done := false
var _tween: Tween


static func create(text: String) -> EndLore:
	var lore := EndLore.new()
	lore._layout(text)
	return lore


func _layout(text: String) -> void:
	var font := PixelFont.get_book_font()
	var size := PixelFont.book_size()
	var y := 0.0
	var first := true
	for part in text.replace("||", "|\n").split("|", false):
		var gap := part.begins_with("\n")
		var sentence := part.strip_edges()
		if sentence == "":
			continue
		if not first:
			y += GAP if gap else 0.0
		first = false
		var lines := PackedStringArray()
		var line := ""
		for word in sentence.split(" ", false):
			var attempt := word if line == "" else line + " " + word
			if line != "" and font.get_string_size(attempt, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x > WIDTH:
				lines.append(line)
				attempt = word
			line = attempt
		if line != "":
			lines.append(line)
		_blocks.append({"lines": lines, "y": y, "alpha": 0.0, "chars": sentence.length()})
		y += lines.size() * LINE + 6
	scale = Vector2(SCALE, SCALE)
	position = Vector2(0, roundf((360.0 - y * SCALE) * 0.5))


func _ready() -> void:
	_tween = create_tween()
	for i in _blocks.size():
		_tween.tween_method(_set_alpha.bind(i), 0.0, 1.0, FADE_IN)
		_tween.tween_interval(READ_BASE + READ_CHAR * float(_blocks[i]["chars"]))
	_tween.tween_interval(HOLD)
	_tween.tween_callback(_fade_out)


func _set_alpha(value: float, index: int) -> void:
	_blocks[index]["alpha"] = value
	queue_redraw()


func _process(_delta: float) -> void:
	if not _done and (Input.is_action_just_pressed(&"jump") or Input.is_action_just_pressed(&"ui_accept")):
		_tween.kill()
		_fade_out()


func _fade_out() -> void:
	if _done:
		return
	_done = true
	var out := create_tween()
	out.tween_property(self, "modulate:a", 0.0, FADE_OUT)
	await out.finished
	finished.emit()


func _draw() -> void:
	var font := PixelFont.get_book_font()
	var size := PixelFont.book_size()
	var center := 640.0 / SCALE * 0.5
	for block in _blocks:
		var alpha: float = block["alpha"]
		if alpha <= 0.0:
			continue
		var lines: PackedStringArray = block["lines"]
		for k in lines.size():
			var w := font.get_string_size(lines[k], HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
			var at := Vector2(roundf(center - w * 0.5), float(block["y"]) + 7 + k * LINE)
			draw_string(font, at, lines[k], HORIZONTAL_ALIGNMENT_LEFT, -1, size, Color(INK, alpha))
