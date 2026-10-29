class_name DiaryReader
extends CanvasLayer

const ENTRIES := 5
const PAPER := Color("efe2c4")
const PAPER_EDGE := Color("dccaa3")
const GUTTER := Color("cdb98f")
const RULE := Color("e0cfab")
const INK := Color("2b2440")
const HEADING := Color("7a3b2e")
const COVER := Color("6b3a2a")
const COVER_DARK := Color("4a2619")
const RIBBON := Color("b9583e")
const OUTLINE := Color("151229")
const SHADE := Color(0.04, 0.03, 0.09, 0.72)
const BOOK := Rect2(64, 22, 512, 300)
const MARGIN := Vector2(18, 16)
const LINE := 11
const FOOTER := 14
const FADE := 0.15
const CLOSE_ACTIONS: Array[StringName] = [&"jump", &"pause", &"dash", &"ui_cancel"]

static var _current: DiaryReader

var pages: Array = []
var spread := 0
var _canvas: Node2D
var _closing := false


static func is_open() -> bool:
	return is_instance_valid(_current)


static func open(from: Node, at_spread := 0) -> DiaryReader:
	if is_open():
		return _current
	var reader := DiaryReader.new()
	reader.spread = at_spread
	_current = reader
	from.add_child(reader)
	return reader


func _ready() -> void:
	layer = 55
	process_mode = Node.PROCESS_MODE_ALWAYS
	get_tree().paused = true
	pages = _paginate()
	spread = clampi(spread, 0, _spreads() - 1)
	_canvas = Node2D.new()
	_canvas.draw.connect(_draw_book)
	_canvas.modulate.a = 0.0
	add_child(_canvas)
	var controls := Hint.create(Vector2(320, 346 + Hint.RISE), "DIARY_CONTROLS")
	controls.forced = true
	_canvas.add_child(controls)
	create_tween().tween_property(_canvas, "modulate:a", 1.0, FADE)
	AudioManager.play_sfx(&"menu_select")


func _exit_tree() -> void:
	if _current == self:
		_current = null


func _process(_delta: float) -> void:
	if _closing:
		return
	var turn := 0
	if Input.is_action_just_pressed(&"move_right") or Input.is_action_just_pressed(&"ui_right"):
		turn = 1
	elif Input.is_action_just_pressed(&"move_left") or Input.is_action_just_pressed(&"ui_left"):
		turn = -1
	if turn != 0:
		var to := clampi(spread + turn, 0, _spreads() - 1)
		if to != spread:
			spread = to
			_canvas.queue_redraw()
			AudioManager.play_sfx(&"menu_move", 0.0, 0.03)
	for action in CLOSE_ACTIONS:
		if Input.is_action_just_pressed(action):
			close()
			return


func close() -> void:
	if _closing:
		return
	_closing = true
	AudioManager.play_sfx(&"menu_back", 0.0, 0.0)
	var fade := create_tween()
	fade.tween_property(_canvas, "modulate:a", 0.0, FADE)
	await fade.finished
	while CLOSE_ACTIONS.any(func(a: StringName) -> bool: return Input.is_action_pressed(a)):
		await get_tree().process_frame
	get_tree().paused = false
	queue_free()


func _spreads() -> int:
	return maxi(1, ceili(pages.size() / 2.0))


func _lines_per_page() -> int:
	return int((BOOK.size.y - MARGIN.y * 2 - FOOTER) / LINE)


func _text_width() -> float:
	return BOOK.size.x * 0.5 - MARGIN.x * 2


func _paginate() -> Array:
	var entries: Array = []
	var first: Array = [[&"title", tr(&"DIARY_TITLE")], [&"blank", ""], [&"head", tr(&"DIARY_TODO_TITLE")], [&"blank", ""]]
	for item: String in tr(&"DIARY_TODO").split("|"):
		var done := item.begins_with("~")
		for line in _wrap("- " + item.trim_prefix("~"), "  "):
			first.append([&"done" if done else &"todo", line])
	entries.append(first)
	for day in range(1, ENTRIES + 1):
		var entry: Array = [[&"head", tr(&"DIARY_DAY") % day], [&"blank", ""]]
		var paragraphs := tr(StringName("DIARY_DAY_%d" % day)).split("|")
		for i in paragraphs.size():
			if i > 0:
				entry.append([&"blank", ""])
			for line in _wrap(paragraphs[i]):
				entry.append([&"text", line])
		entries.append(entry)
	var out: Array = []
	var per_page := _lines_per_page()
	for entry: Array in entries:
		var page: Array = []
		for line: Array in entry:
			if page.size() >= per_page:
				out.append(page)
				page = []
			if page.is_empty() and line[0] == &"blank":
				continue
			page.append(line)
		out.append(page)
	return out


func _wrap(paragraph: String, indent := "") -> PackedStringArray:
	var font := PixelFont.get_book_font()
	var size := PixelFont.book_size()
	var width := _text_width()
	var lines := PackedStringArray()
	var line := ""
	for word in paragraph.split(" ", false):
		var attempt := word if line == "" else line + " " + word
		if line != "" and font.get_string_size(attempt, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x > width:
			lines.append(line)
			attempt = indent + word
		line = attempt
	if line != "":
		lines.append(line)
	return lines


func _draw_book() -> void:
	var c := _canvas
	c.draw_rect(Rect2(0, 0, 640, 360), SHADE)
	var cover := BOOK.grow_individual(7, 6, 7, 8)
	c.draw_rect(cover.grow(1), OUTLINE)
	c.draw_rect(cover, COVER)
	c.draw_rect(Rect2(cover.position.x, cover.end.y - 3, cover.size.x, 3), COVER_DARK)
	for i in 3:
		var y := BOOK.end.y + i
		var edge := PAPER_EDGE if i < 2 else OUTLINE
		c.draw_rect(Rect2(BOOK.position.x - i, y, BOOK.size.x * 0.5, 1), edge)
		c.draw_rect(Rect2(BOOK.get_center().x, y, BOOK.size.x * 0.5 + i, 1), edge)
	var half := BOOK.size.x * 0.5
	for side in 2:
		var page_rect := Rect2(BOOK.position.x + half * side, BOOK.position.y, half, BOOK.size.y)
		c.draw_rect(page_rect, PAPER)
		_draw_page(page_rect, spread * 2 + side, side)
	var mid := BOOK.get_center().x
	for i in 4:
		var shade := GUTTER.lerp(PAPER, i / 4.0)
		c.draw_rect(Rect2(mid - 1 - i, BOOK.position.y, 1, BOOK.size.y), shade)
		c.draw_rect(Rect2(mid + i, BOOK.position.y, 1, BOOK.size.y), shade)
	c.draw_rect(Rect2(mid - 1, BOOK.position.y, 2, BOOK.size.y), OUTLINE.lerp(GUTTER, 0.5))
	c.draw_rect(Rect2(mid + 6, BOOK.position.y - 2, 3, BOOK.size.y + 18), RIBBON)
	c.draw_rect(Rect2(mid + 6, BOOK.end.y + 14, 1, 3), PAPER_EDGE.lerp(RIBBON, 0.5))
	c.draw_rect(Rect2(mid + 8, BOOK.end.y + 14, 1, 3), PAPER_EDGE.lerp(RIBBON, 0.5))


func _draw_page(rect: Rect2, index: int, side: int) -> void:
	var c := _canvas
	var font := PixelFont.get_book_font()
	var size := PixelFont.book_size()
	var left := rect.position.x + MARGIN.x
	var top := rect.position.y + MARGIN.y
	var width := _text_width()
	for i in _lines_per_page():
		c.draw_rect(Rect2(left, top + 9 + i * LINE, width, 1), RULE)
	if index >= pages.size():
		return
	var page: Array = pages[index]
	for i in page.size():
		var kind: StringName = page[i][0]
		var text: String = page[i][1]
		var baseline := top + 7 + i * LINE
		var color := HEADING if kind in [&"title", &"head"] else INK
		var x := left
		if kind == &"title":
			x = left + roundf((width - font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x) * 0.5)
		c.draw_string(font, Vector2(x, baseline), text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, color)
		if kind == &"title" or kind == &"head":
			var w := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
			c.draw_rect(Rect2(x, baseline + 2, w, 1), HEADING)
		elif kind == &"done":
			var start := font.get_string_size("- ", HORIZONTAL_ALIGNMENT_LEFT, -1, size).x if text.begins_with("- ") else 0.0
			var w := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x - start
			c.draw_rect(Rect2(x + start - 1, baseline - 3, w + 2, 1), HEADING)
	var foot := rect.end.y - MARGIN.y + 2
	var number := str(index + 1)
	var nw := font.get_string_size(number, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
	var nx := rect.position.x + MARGIN.x if side == 0 else rect.end.x - MARGIN.x - nw
	c.draw_string(font, Vector2(nx, foot), number, HORIZONTAL_ALIGNMENT_LEFT, -1, size, GUTTER)
	if side == 0 and spread > 0:
		_arrow(Vector2(rect.position.x + MARGIN.x + 14, foot - 3), -1)
	elif side == 1 and spread < _spreads() - 1:
		_arrow(Vector2(rect.end.x - MARGIN.x - 14 - nw, foot - 3), 1)


func _arrow(at: Vector2, dir: int) -> void:
	for i in 3:
		_canvas.draw_rect(Rect2(at.x + i * dir, at.y - (2 - i), 1, (2 - i) * 2 + 1), HEADING)
