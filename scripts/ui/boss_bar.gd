class_name BossBar
extends Control

const WIDTH := 252.0
const HEIGHT := 8.0
const TITLE_Y := 9.0
const BAR_Y := 29.0
const SUBTITLE_Y := 42.0
const OUTLINE := Color("1c1433")
const EMPTY := Color("3a2f5c")
const DEEP := Color("#c88a10")
const YELLOW := Color("#ffcc33")
const HOT := Color("#fff4c0")
const FILL_STEP := 0.12
const FALL_TIME := 0.55

var total := 0
var left := 0

var _title: Label
var _subtitle: Label
var _lit := 0.0
var _falling: Array = []
var _flash := 0.0
var _filling: Tween


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	modulate.a = 0.0
	_title = _make_label(2)
	_title.position = Vector2(0, TITLE_Y)
	_title.size = Vector2(640.0 / 2.0, PixelFont.size())
	_title.text = tr(&"BOSS_NAME")
	add_child(_title)
	_subtitle = _make_label(1)
	_subtitle.position = Vector2(0, SUBTITLE_Y)
	_subtitle.size = Vector2(640.0, PixelFont.size())
	_subtitle.text = tr(&"BOSS_TITLE")
	add_child(_subtitle)


func _notification(what: int) -> void:
	if what == NOTIFICATION_TRANSLATION_CHANGED and _title:
		_title.text = tr(&"BOSS_NAME")
		_subtitle.text = tr(&"BOSS_TITLE")


func intro(count: int) -> void:
	total = count
	left = count
	_lit = 0.0
	_falling.clear()
	_subtitle.text = tr(&"BOSS_TITLE")
	modulate.a = 1.0
	_title.position.y = TITLE_Y - 8.0
	_title.modulate.a = 0.0
	var drop := create_tween().set_parallel()
	drop.tween_property(_title, "position:y", TITLE_Y, 0.35).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	drop.tween_property(_title, "modulate:a", 1.0, 0.2)
	if _filling:
		_filling.kill()
	_filling = create_tween()
	_filling.tween_interval(0.25)
	for i in count:
		_filling.tween_callback(func() -> void:
			_lit = i + 1
			AudioManager.play_sfx(&"clank", -12.0, 0.06)
			queue_redraw())
		_filling.tween_interval(FILL_STEP)


func set_energy(count: int, now: int) -> void:
	if total == 0 or modulate.a < 1.0:
		modulate.a = 1.0
		_title.modulate.a = 1.0
		_title.position.y = TITLE_Y
		_lit = count
		left = now
	if _filling and _filling.is_running() and now < left:
		_filling.kill()
		_lit = count
	if now < left:
		for i in range(now, left):
			_falling.append([i, 0.0])
		_flash = 0.15
	total = count
	left = now
	queue_redraw()


func fade_out(time := 1.2) -> void:
	var fade := create_tween()
	fade.tween_property(self, "modulate:a", 0.0, time)
	fade.tween_callback(func() -> void: total = 0)


func is_shown() -> bool:
	return total > 0 and modulate.a > 0.0


func _process(delta: float) -> void:
	if _falling.is_empty() and _flash <= 0.0:
		return
	_flash = maxf(_flash - delta, 0.0)
	for item: Array in _falling:
		item[1] += delta
	_falling = _falling.filter(func(item: Array) -> bool: return item[1] < FALL_TIME)
	queue_redraw()


func _draw() -> void:
	if total <= 0:
		return
	var x0 := roundf(320.0 - WIDTH * 0.5)
	var bar := Rect2(x0, BAR_Y, WIDTH, HEIGHT)
	draw_rect(bar.grow(2), OUTLINE)
	draw_rect(bar.grow(1), DEEP)
	draw_rect(bar, OUTLINE)
	for side: int in [-1, 1]:
		var cx := 320.0 + side * (WIDTH * 0.5 + 6.0)
		var cy := BAR_Y + HEIGHT * 0.5
		for k in 4:
			draw_rect(Rect2(cx - k, cy - 3 + k, 1 + k * 2, 1), OUTLINE if k == 0 else DEEP)
			draw_rect(Rect2(cx - k, cy + 3 - k, 1 + k * 2, 1), OUTLINE if k == 0 else DEEP)
		draw_rect(Rect2(cx - 3, cy, 7, 1), YELLOW)
	var seg := (WIDTH - (total - 1)) / total
	for i in total:
		var rect := Rect2(roundf(x0 + i * (seg + 1)), BAR_Y, roundf(seg), HEIGHT)
		if i < int(_lit) and i < left:
			_draw_segment(rect, Color.WHITE if _flash > 0.0 else Color(1, 1, 1, 0))
		else:
			draw_rect(rect, EMPTY)
	for item: Array in _falling:
		var i: int = item[0]
		var t: float = item[1] / FALL_TIME
		var rect := Rect2(roundf(x0 + i * (seg + 1)), BAR_Y + roundf(t * t * 14.0), roundf(seg), HEIGHT)
		var white := Color(1, 1, 1, 1.0 - t) if t < 0.25 else Color(1, 1, 1, 0)
		_draw_segment(rect, white, 1.0 - t)


func _draw_segment(rect: Rect2, flash: Color, alpha := 1.0) -> void:
	var body := YELLOW
	body.a = alpha
	var top := HOT
	top.a = alpha
	var bottom := DEEP
	bottom.a = alpha
	draw_rect(rect, body)
	draw_rect(Rect2(rect.position, Vector2(rect.size.x, 2)), top)
	draw_rect(Rect2(rect.position + Vector2(0, rect.size.y - 2), Vector2(rect.size.x, 2)), bottom)
	if flash.a > 0.0:
		draw_rect(rect, flash)


func _make_label(scale_by: int) -> Label:
	var label := Label.new()
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.scale = Vector2.ONE * scale_by
	label.add_theme_font_override(&"font", PixelFont.get_font())
	label.add_theme_font_size_override(&"font_size", PixelFont.size())
	label.add_theme_color_override(&"font_color", Color.WHITE)
	label.add_theme_color_override(&"font_shadow_color", OUTLINE)
	label.add_theme_constant_override(&"shadow_offset_x", 1)
	label.add_theme_constant_override(&"shadow_offset_y", 1)
	return label
