class_name Hud
extends CanvasLayer

const CARD_COLOR := Color("ffffff")
const TITLE_SCALE := 2
const TITLE_Y := 96.0
const LINE_LENGTH := 44.0
const LINE_GAP := 12.0
const NOTE_TEXTURE := preload("res://assets/sprites/props/gift_note.png")
const NOTE_INK := Color("4a2a3a")
const NOTE_ROSE_INK := Color("b23f68")
const NOTE_PAPER_TOP := 16.0
const NOTE_PAPER_HEIGHT := 181.0
const NOTE_TEXT_X := 158.0
const NOTE_TEXT_W := 352.0
const NOTE_TITLE_GAP := 14.0
const NOTE_TITLE_LINE := 22.0
const NOTE_SIGN_GAP := 10.0
const NOTE_LINE_GAP := 16.0
const NOTE_LINE_DELAY := 1.0

var _stats: Label
var _card: Control
var _card_title: Label
var _card_subtitle: Label
var _card_tween: Tween
var _lines: Array[ColorRect] = []
var _note: Control
var _note_lines: Array[Label] = []
var _note_arrow: Polygon2D
var _note_tween: Tween
var _note_ready := false
var _note_player: Player
var _note_ability: StringName = &""
var _note_blink := 0.0
var _note_bob := 0.0
var _shown_deaths := -1
var _shown_seconds := -1
var _boss: BossBar


func _ready() -> void:
	layer = 40
	_stats = _label(HORIZONTAL_ALIGNMENT_LEFT)
	_stats.position = Vector2(6, 5)
	add_child(_stats)
	_card = Control.new()
	_card.set_anchors_preset(Control.PRESET_FULL_RECT)
	_card.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_card.modulate.a = 0.0
	add_child(_card)
	_card_title = _label(HORIZONTAL_ALIGNMENT_CENTER)
	_card_title.scale = Vector2.ONE * TITLE_SCALE
	_card_title.position = Vector2(0, TITLE_Y)
	_card_title.size = Vector2(640.0 / TITLE_SCALE, PixelFont.size())
	_card.add_child(_card_title)
	_card_subtitle = _label(HORIZONTAL_ALIGNMENT_CENTER)
	_card_subtitle.position = Vector2(0, TITLE_Y + PixelFont.size() * TITLE_SCALE + 10)
	_card_subtitle.size = Vector2(640.0, PixelFont.size())
	_card.add_child(_card_subtitle)
	Events.gift_received.connect(_on_gift_received)
	Events.feather_collected.connect(_on_feather_collected)
	for i in 2:
		var line := ColorRect.new()
		line.color = CARD_COLOR
		line.size = Vector2(LINE_LENGTH, 1)
		_card.add_child(line)
		_lines.append(line)


func _process(delta: float) -> void:
	if _note:
		_update_note(delta)
	var seconds := int(Game.play_time)
	if Game.deaths == _shown_deaths and seconds == _shown_seconds:
		return
	_shown_deaths = Game.deaths
	_shown_seconds = seconds
	_stats.text = tr(&"HUD_STATS") % [Game.deaths, Game.format_time(seconds)]


func boss_bar() -> BossBar:
	if _boss == null:
		_boss = BossBar.new()
		add_child(_boss)
	return _boss


func show_energy(total: int, left: int) -> void:
	if total <= 0:
		if _boss and _boss.is_shown():
			_boss.fade_out()
		return
	boss_bar().set_energy(total, left)


func show_zone(name_key: StringName) -> void:
	show_card(name_key)


func show_card(title_key: StringName, subtitle_key: StringName = &"", hold := 2.2) -> void:
	_card_title.text = tr(title_key)
	_card_subtitle.text = tr(subtitle_key) if subtitle_key != &"" else ""
	var half := _card_title.get_theme_font(&"font").get_string_size(_card_title.text, HORIZONTAL_ALIGNMENT_LEFT, -1, PixelFont.size()).x * TITLE_SCALE * 0.5
	var middle := TITLE_Y + PixelFont.size() * TITLE_SCALE * 0.5
	_lines[0].position = Vector2(320.0 - half - LINE_GAP - LINE_LENGTH, middle).floor()
	_lines[1].position = Vector2(320.0 + half + LINE_GAP, middle).floor()
	if _card_tween:
		_card_tween.kill()
	_card_tween = create_tween()
	_card_tween.tween_property(_card, "modulate:a", 1.0, 0.6)
	_card_tween.tween_interval(hold)
	_card_tween.tween_property(_card, "modulate:a", 0.0, 0.9)


func _on_feather_collected(count: int) -> void:
	show_card(&"FEATHER_TITLE", StringName(tr(&"FEATHER_COUNT") % [count, Game.feather_total]), 1.4)


func _on_gift_received(ability: StringName) -> void:
	var note_key := "NOTE_" + String(ability).to_upper()
	if tr(note_key + "_1") != note_key + "_1":
		_note_ability = ability
		show_note(note_key)
	else:
		_show_gift_card(ability)


func _show_gift_card(ability: StringName) -> void:
	show_card(&"GIFT_TITLE", StringName("GIFT_" + String(ability).to_upper()), 3.2)


func show_note(key: String) -> void:
	if _note:
		_note.queue_free()
	_note_lines.clear()
	_note_ready = false
	_note = Control.new()
	_note.set_anchors_preset(Control.PRESET_FULL_RECT)
	_note.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_note)
	var paper := TextureRect.new()
	paper.texture = NOTE_TEXTURE
	var origin := ((Vector2(640, 360) - NOTE_TEXTURE.get_size()) * 0.5).floor()
	paper.position = origin
	_note.add_child(paper)
	var lines: Array[String] = []
	while true:
		var k := "%s_%d" % [key, lines.size() + 1]
		if tr(k) == k:
			break
		lines.append(tr(k))
	var font_h := float(PixelFont.size())
	var sign_key := key + "_SIGN"
	var has_sign := tr(sign_key) != sign_key
	var height := font_h * TITLE_SCALE + NOTE_TITLE_GAP + NOTE_LINE_GAP * (lines.size() - 1) + font_h
	if has_sign:
		height += NOTE_SIGN_GAP + font_h
	var top := roundf(origin.y + NOTE_PAPER_TOP + (NOTE_PAPER_HEIGHT - height) * 0.5)
	var column := Vector2(origin.x + NOTE_TEXT_X, NOTE_TEXT_W)
	var title := _note_label(tr(&"GIFT_TITLE"), NOTE_ROSE_INK, HORIZONTAL_ALIGNMENT_CENTER)
	title.scale = Vector2.ONE * TITLE_SCALE
	title.position = Vector2(column.x, top)
	title.size = Vector2(column.y / TITLE_SCALE, font_h)
	title.modulate.a = 1.0
	var half := title.get_theme_font(&"font").get_string_size(title.text, HORIZONTAL_ALIGNMENT_LEFT, -1, PixelFont.size()).x * TITLE_SCALE * 0.5
	var middle := column.x + column.y * 0.5
	for side in [-1.0, 1.0]:
		var dash := ColorRect.new()
		dash.color = NOTE_ROSE_INK
		dash.size = Vector2(NOTE_TITLE_LINE, 1)
		dash.position = Vector2(roundf(middle + side * (half + 8.0) - (NOTE_TITLE_LINE if side < 0 else 0.0)), top + roundf(font_h * TITLE_SCALE * 0.5))
		_note.add_child(dash)
	var y := top + font_h * TITLE_SCALE + NOTE_TITLE_GAP
	for i in lines.size():
		var label := _note_label(lines[i], NOTE_INK, HORIZONTAL_ALIGNMENT_CENTER)
		label.position = Vector2(column.x, y + i * NOTE_LINE_GAP)
		label.size = Vector2(column.y, font_h)
		_note_lines.append(label)
	if has_sign:
		var sign_label := _note_label(tr(sign_key), NOTE_ROSE_INK, HORIZONTAL_ALIGNMENT_RIGHT)
		sign_label.position = Vector2(column.x, y + (lines.size() - 1) * NOTE_LINE_GAP + font_h + NOTE_SIGN_GAP)
		sign_label.size = Vector2(column.y - 6.0, font_h)
		_note_lines.append(sign_label)
	_note_arrow = Polygon2D.new()
	_note_arrow.polygon = PackedVector2Array([Vector2(0, 0), Vector2(5, 0), Vector2(2.5, 3)])
	_note_arrow.color = NOTE_INK
	_note_arrow.position = origin + NOTE_TEXTURE.get_size() - Vector2(20, 16)
	_note_arrow.visible = false
	_note.add_child(_note_arrow)
	_note_player = get_tree().get_first_node_in_group(Combat.PLAYER_GROUP) as Player
	if _note_player:
		_note_player.input_enabled = false
	_note.modulate.a = 0.0
	_note.position.y = 8.0
	_note_tween = create_tween()
	_note_tween.set_parallel()
	_note_tween.tween_property(_note, "modulate:a", 1.0, 0.5)
	_note_tween.tween_property(_note, "position:y", 0.0, 0.5).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	_note_tween.chain().tween_interval(0.3)
	for label in _note_lines:
		_note_tween.chain().tween_property(label, "modulate:a", 1.0, 0.6)
		_note_tween.chain().tween_interval(NOTE_LINE_DELAY)
	_note_tween.chain().tween_callback(_note_show_all)


func _note_label(text: String, ink: Color, align: HorizontalAlignment) -> Label:
	var label := _label(align)
	label.text = text.to_upper()
	label.add_theme_color_override(&"font_color", ink)
	label.add_theme_color_override(&"font_shadow_color", Color(0, 0, 0, 0))
	label.modulate.a = 0.0
	_note.add_child(label)
	return label


func _note_show_all() -> void:
	if _note_tween:
		_note_tween.kill()
	_note.modulate.a = 1.0
	_note.position.y = 0.0
	for label in _note_lines:
		label.modulate.a = 1.0
	_note_arrow.visible = true
	_note_ready = true


func _update_note(delta: float) -> void:
	if _note_ready:
		_note_blink += delta
		_note_arrow.position.y = _note_arrow.position.y - _note_bob + roundf(sin(_note_blink * 4.0))
		_note_bob = roundf(sin(_note_blink * 4.0))
	var pressed := Input.is_action_just_pressed(&"jump") or Input.is_action_just_pressed(&"dash") \
		or Input.is_action_just_pressed(&"ui_accept")
	if not pressed:
		return
	if not _note_ready:
		_note_show_all()
		return
	_close_note()


func _close_note() -> void:
	var note := _note
	_note = null
	_note_ready = false
	var tween := create_tween()
	tween.tween_property(note, "modulate:a", 0.0, 0.35)
	tween.tween_callback(note.queue_free)
	tween.tween_callback(func() -> void:
		if is_instance_valid(_note_player):
			_note_player.input_enabled = true
		if _note_ability != &"":
			_show_gift_card(_note_ability)
			_note_ability = &"")


func _label(align: HorizontalAlignment) -> Label:
	var label := Label.new()
	label.horizontal_alignment = align
	label.add_theme_font_override(&"font", PixelFont.get_font())
	label.add_theme_font_size_override(&"font_size", PixelFont.size())
	label.add_theme_color_override(&"font_color", CARD_COLOR)
	label.add_theme_constant_override(&"outline_size", 0)
	label.add_theme_color_override(&"font_shadow_color", Color("1c1433"))
	label.add_theme_constant_override(&"shadow_offset_x", 1)
	label.add_theme_constant_override(&"shadow_offset_y", 1)
	return label
