class_name GameMenu
extends CanvasLayer

signal new_game_chosen
signal continue_chosen
signal resume_chosen
signal title_chosen
signal results_closed
signal chapter_chosen(index: int)
signal skip_fight_chosen

const TEXT := Color("ffffff")
const DIM := Color("b4bbdc")
const WARM := Color("ffc27a")
const BAR_EMPTY := Color("3a3263")
const OFF := Color("7c78a8")
const SHADOW := Color("1c1433")
const SCREEN := Vector2(640, 360)
const TITLE_SCALE := 3
const TITLE_Y := 91.0
const LINE_LENGTH := 27.0
const LINE_GAP := 10.0
const ITEM_SCALE := 1
const ITEM_STEP := 13.0
const HEADING_GAP := 24.0
const TITLE_LIST_Y := 180.0
const TITLE_ROWS := 6
const PAUSE_LIST_Y := 160.0
const PAUSE_HEADING_Y := 100.0
const STATS_STEP := 10.0
const RESULTS_HEADING_Y := 126.0
const RESULTS_LOCK := 1.0
const ROW_WIDTH := 220.0
const BAR_SEGMENT := Vector2(4, 7)
const BAR_GAP := 1.0
const PAUSE_SHADE := 0.6
const FADE := 0.25
const REPEAT_DELAY := 0.35
const REPEAT_EVERY := 0.09
const LOOK_LIST_X := 300.0
const LOOK_ROW_WIDTH := 240.0
const LOOK_ROW_STEP := 12.0
const LOOK_LIST_Y := 90.0
const PREVIEW_SCALE := 3
const PREVIEW_FEET := Vector2(180, 216)
const PREVIEW_ANIMS: Array[StringName] = [&"idle", &"run", &"jump", &"fall", &"dash", &"wall_slide", &"sit_roast"]
const PREVIEW_EVERY := 2.4
const SWATCH := {"skin": ["S", "s", "z"], "hair": ["H", "h", "u"], "eyes": ["e"], "jacket": ["w", "W", "v"],
	"pack": ["a", "G", "m"], "pants": ["J", "j"], "boots": ["O", "o", "k"],
	"hat_color": ["P", "p", "q"], "scarf_color": ["F", "i", "I"]}
const SWATCH_CELL := Vector2(4, 7)
const PAW := ["#.#.#", ".....", ".###.", "#####", ".###."]

var _open := false
var _title_mode := true
var _has_save := false
var _page := &""
var _items: Array[Dictionary] = []
var _rows: Array[Control] = []
var _index := 0
var _opened_frame := -1
var _held := Vector2i.ZERO
var _held_time := 0.0
var _results_lock := 0.0
var _can_skip := false
var _chapter := 0

var _root: Control
var _content: Control
var _shade: ColorRect
var _title: Control
var _box: Control
var _cursor: Control
var _fade: Tween
var _preview: AnimatedSprite2D
var _preview_time := 0.0


func _ready() -> void:
	layer = 60
	process_mode = Node.PROCESS_MODE_ALWAYS
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_root)
	_shade = ColorRect.new()
	_shade.set_anchors_preset(Control.PRESET_FULL_RECT)
	_shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_shade.color = Color(SHADOW, 0.0)
	_root.add_child(_shade)
	_content = Control.new()
	_content.set_anchors_preset(Control.PRESET_FULL_RECT)
	_content.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(_content)
	_title = _make_title()
	_content.add_child(_title)
	_cursor = _make_paw()
	visible = false
	Events.look_changed.connect(_on_look_changed)


func _on_look_changed() -> void:
	if _preview != null and is_instance_valid(_preview):
		HeroLook.dress(_preview)


func is_open() -> bool:
	return _open


func open_title(has_save: bool) -> void:
	_title_mode = true
	_has_save = has_save
	_shade.color.a = 0.0
	_title.visible = true
	_show(&"main")


func open_pause(can_skip := false) -> void:
	_can_skip = can_skip
	_title_mode = false
	_shade.color.a = PAUSE_SHADE
	_title.visible = false
	_show(&"pause")
	AudioManager.play_sfx(&"menu_select")


func open_results() -> void:
	_title_mode = false
	_shade.color.a = 0.0
	_title.visible = false
	_results_lock = RESULTS_LOCK
	_show(&"results")


func open_page(page: StringName) -> void:
	_set_page(page)


func close(duration := FADE) -> void:
	_open = false
	if _fade:
		_fade.kill()
	_fade = create_tween()
	_fade.tween_property(_root, "modulate:a", 0.0, duration)
	_fade.tween_callback(hide)


func _show(page: StringName) -> void:
	_open = true
	_opened_frame = Engine.get_process_frames()
	_held = _held_input()
	visible = true
	if _fade:
		_fade.kill()
	_root.modulate.a = 0.0
	_fade = create_tween()
	_fade.tween_property(_root, "modulate:a", 1.0, FADE)
	_set_page(page)


func _set_page(page: StringName) -> void:
	_page = page
	_items.clear()
	match page:
		&"main":
			if _has_save:
				_button(&"MENU_CONTINUE", _choose.bind(continue_chosen))
			_button(&"MENU_NEW_GAME", _on_new_game)
			if Chapters.available():
				_button(&"MENU_CHAPTERS", _set_page.bind(&"chapters"))
			_button(&"MENU_CHARACTER", _set_page.bind(&"character"))
			_button(&"MENU_OPTIONS", _set_page.bind(&"options"))
			_button(&"MENU_CREDITS", _set_page.bind(&"credits"))
			_button(&"MENU_QUIT", _quit)
		&"pause":
			_button(&"MENU_RESUME", _choose.bind(resume_chosen))
			if _can_skip and Settings.assist_on():
				_button(&"MENU_SKIP_FIGHT", _choose.bind(skip_fight_chosen))
			if Chapters.available():
				_button(&"MENU_CHAPTERS", _set_page.bind(&"chapters"))
			_button(&"MENU_OPTIONS", _set_page.bind(&"options"))
			_button(&"MENU_TO_TITLE", _choose.bind(title_chosen))
			_button(&"MENU_QUIT", _quit)
		&"options":
			_slider(&"OPT_MUSIC", "music")
			_slider(&"OPT_SFX", "sfx")
			_toggle(&"OPT_FULLSCREEN", "fullscreen")
			_toggle(&"OPT_VSYNC", "vsync")
			_items.append({"key": &"OPT_LANGUAGE", "setting": "language", "kind": &"choice", "do": _cycle_language.bind(1)})
			_button(&"MENU_ASSIST", _set_page.bind(&"assist"))
			_button(&"MENU_BACK", _go_back)
		&"assist":
			_toggle(&"MENU_ASSIST", "assist")
			_toggle(&"ASSIST_INVINCIBLE", "assist_invincible")
			_toggle(&"ASSIST_INFINITE_DASH", "assist_infinite_dash")
			_button(&"MENU_BACK", _go_back)
		&"chapters":
			for i in Chapters.count():
				_button(Chapters.name_key(i), _pick_chapter.bind(i))
			_button(&"MENU_BACK", _go_back)
		&"credits":
			_button(&"MENU_BACK", _go_back)
		&"character":
			var look := HeroLook.current()
			for piece: String in ["skin", "hair", "beard", "eyes", "jacket", "pack", "pants", "boots",
					"hat", "hat_color", "glasses", "scarf", "scarf_color"]:
				if piece == "hat_color" and look["hat"] == "none" or piece == "scarf_color" and look["scarf"] == "none":
					continue
				_items.append({"key": StringName("LOOK_" + piece.to_upper()), "setting": piece, "kind": &"look",
					"do": _cycle_look.bind(piece, 1)})
			_button(&"LOOK_RANDOMIZE", _randomize_look)
			_button(&"LOOK_RESET", _reset_look)
			_button(&"MENU_BACK", _go_back)
		&"confirm_new":
			_button(&"CONFIRM_NO", _go_back)
			_button(&"CONFIRM_YES", _choose.bind(new_game_chosen))
		&"confirm_chapter":
			_button(&"CONFIRM_NO", _go_back)
			_button(&"CONFIRM_CHAPTER_YES", _start_chapter)
		&"results":
			_button(&"END_CONTINUE", _choose.bind(results_closed))
	_build_page()
	_select(0, false)


func _button(key: StringName, action: Callable) -> void:
	_items.append({"key": key, "do": action})


func _slider(key: StringName, setting: String) -> void:
	_items.append({"key": key, "setting": setting, "kind": &"slider",
		"do": _adjust_setting.bind(setting, 1, true)})


func _toggle(key: StringName, setting: String) -> void:
	_items.append({"key": key, "setting": setting, "kind": &"toggle",
		"do": _adjust_setting.bind(setting, 1, false)})


func _build_page() -> void:
	if _cursor.get_parent():
		_cursor.get_parent().remove_child(_cursor)
	if _box:
		_box.queue_free()
	_box = Control.new()
	_box.set_anchors_preset(Control.PRESET_FULL_RECT)
	_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_content.add_child(_box)
	_rows.clear()
	_preview = null
	if _title_mode:
		_shade.color.a = PAUSE_SHADE if _page == &"character" else 0.0
	var top := TITLE_LIST_Y if _title_mode else PAUSE_LIST_Y
	if _title_mode and _items.size() > TITLE_ROWS:
		top -= (_items.size() - TITLE_ROWS) * ITEM_STEP
	match _page:
		&"pause":
			_heading(&"MENU_PAUSED", PAUSE_HEADING_Y)
			_stats_block(PAUSE_HEADING_Y + 16.0)
		&"results":
			_heading(&"END_RESULTS", RESULTS_HEADING_Y)
			top = _stats_block(RESULTS_HEADING_Y + 16.0) + 12.0
		&"options":
			_heading(&"MENU_OPTIONS", top - HEADING_GAP)
		&"chapters":
			_heading(&"MENU_CHAPTERS", top - HEADING_GAP)
		&"assist":
			_heading(&"MENU_ASSIST", top - HEADING_GAP - 22.0)
			for line in 2:
				var note := _label(tr(StringName("ASSIST_NOTE_%d" % (line + 1))), 1, DIM)
				_center(note, top - 26.0 + line * STATS_STEP, 1)
				_box.add_child(note)
		&"credits":
			top = _build_credits()
		&"character":
			var heading := _label(tr(&"MENU_CHARACTER"), ITEM_SCALE, DIM)
			heading.position = Vector2(roundf(_column_center() - _text_width(heading.text) * ITEM_SCALE * 0.5), LOOK_LIST_Y - 20.0)
			_box.add_child(heading)
			_box.add_child(_make_preview())
			top = LOOK_LIST_Y
		&"confirm_new", &"confirm_chapter":
			var chapter := _page == &"confirm_chapter"
			_heading(&"CONFIRM_CHAPTER" if chapter else &"CONFIRM_NEW_GAME", TITLE_LIST_Y - 28.0)
			var hint := _label(tr(&"CONFIRM_CHAPTER_HINT" if chapter else &"CONFIRM_NEW_GAME_HINT"), 1, DIM)
			_center(hint, TITLE_LIST_Y - 14.0, 1)
			_box.add_child(hint)
			top = TITLE_LIST_Y + 6.0
	var step := LOOK_ROW_STEP if _page == &"character" else ITEM_STEP
	for i in _items.size():
		var row := _make_row(_items[i], top + i * step)
		row.mouse_entered.connect(_select.bind(i))
		row.gui_input.connect(_on_row_input.bind(i))
		_box.add_child(row)
		_rows.append(row)
	_box.add_child(_cursor)
	_title.visible = _title_mode and _page != &"credits" and _page != &"character"


func _make_row(item: Dictionary, y: float) -> Control:
	var row := Control.new()
	row.mouse_filter = Control.MOUSE_FILTER_STOP
	var height := PixelFont.size() * ITEM_SCALE + 6.0
	var text := _label(tr(item["key"]), ITEM_SCALE, TEXT)
	text.name = &"Text"
	if item.has("kind"):
		row.position = Vector2(roundf(_column_center() - _row_width() * 0.5), y - 3.0)
		row.size = Vector2(_row_width(), height)
		text.position = Vector2(0, 3)
		row.add_child(text)
		row.add_child(_make_value(item))
	else:
		var width := _text_width(text.text) * ITEM_SCALE
		row.position = Vector2(roundf(_column_center() - width * 0.5), y - 3.0)
		row.size = Vector2(width, height)
		text.position = Vector2(0, 3)
		row.add_child(text)
	return row


func _make_value(item: Dictionary) -> Control:
	var value := Control.new()
	value.name = &"Value"
	value.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if item["kind"] == &"slider":
		var width := Settings.STEPS * (BAR_SEGMENT.x + BAR_GAP) - BAR_GAP
		value.position = Vector2(_row_width() - width, 3)
		var back := ColorRect.new()
		back.mouse_filter = Control.MOUSE_FILTER_IGNORE
		back.color = SHADOW
		back.position = Vector2(-1, -1)
		back.size = Vector2(width + 3, BAR_SEGMENT.y + 3)
		value.add_child(back)
		for i in Settings.STEPS:
			var segment := ColorRect.new()
			segment.mouse_filter = Control.MOUSE_FILTER_IGNORE
			segment.size = BAR_SEGMENT
			segment.position = Vector2(i * (BAR_SEGMENT.x + BAR_GAP), 0)
			value.add_child(segment)
	else:
		var label := _label("", ITEM_SCALE, TEXT)
		value.add_child(label)
		if item["kind"] == &"look" and SWATCH.has(item["setting"]):
			var swatch := Control.new()
			swatch.name = &"Swatch"
			swatch.mouse_filter = Control.MOUSE_FILTER_IGNORE
			value.add_child(swatch)
	_refresh_value(value, item)
	return value


func _refresh_value(value: Control, item: Dictionary) -> void:
	if item["kind"] == &"look":
		_refresh_look_value(value, item["setting"])
		return
	var current: Variant = Settings.value(item["setting"])
	if item["kind"] == &"slider":
		for i in Settings.STEPS:
			(value.get_child(i + 1) as ColorRect).color = WARM if i < int(current) else BAR_EMPTY
	else:
		var label := value.get_child(0) as Label
		if item["kind"] == &"choice":
			label.text = tr(Settings.LANGUAGES[Settings.language_index()][1])
		else:
			label.text = tr(&"OPT_ON") if current else tr(&"OPT_OFF")
		label.add_theme_color_override(&"font_color", OFF if _is_disabled(item) else TEXT)
		value.position = Vector2(_row_width() - _text_width(label.text) * ITEM_SCALE, 3)


func _build_credits() -> float:
	var lines: Array = [[&"CREDITS_GAME_BY", &"CREDITS_AUTHOR"], [&"CREDITS_SUPERVISION", &"CREDITS_SUPERVISORS"],
		[&"CREDITS_SCHOOL", &"CREDITS_COURSE"], [&"CREDITS_MUSIC", &"CREDITS_MUSIC_BY"],
		[&"CREDITS_SFX", &"CREDITS_SFX_BY"]]
	var y := 76.0
	for pair: Array in lines:
		var head := _label(tr(pair[0]), 1, DIM)
		_center(head, y, 1)
		_box.add_child(head)
		var body := _label(tr(pair[1]), ITEM_SCALE, TEXT)
		_center(body, y + 11.0, ITEM_SCALE)
		_box.add_child(body)
		y += 28.0
	var tech := _label(tr(&"CREDITS_TECH"), 1, DIM)
	_center(tech, y, 1)
	_box.add_child(tech)
	return y + 20.0


func _stats_block(y: float) -> float:
	for text: String in [tr(&"STATS_TIME") % Game.format_time(Game.play_time), tr(&"STATS_DEATHS") % Game.deaths,
			tr(&"FEATHER_PAUSE") % [Game.feather_count(), Game.feather_total]]:
		var label := _label(text, 1, DIM)
		_center(label, y, 1)
		_box.add_child(label)
		y += STATS_STEP
	return y


func _heading(key: StringName, y: float) -> void:
	var label := _label(tr(key), ITEM_SCALE, DIM)
	_center(label, y, ITEM_SCALE)
	_box.add_child(label)


func _select(index: int, with_sound := true) -> void:
	if _items.is_empty():
		return
	index = wrapi(index, 0, _items.size())
	if with_sound and index != _index:
		AudioManager.play_sfx(&"menu_move", 0.0, 0.02)
	_index = index
	for i in _rows.size():
		var color := TEXT if i == index else (OFF if _is_disabled(_items[i]) else DIM)
		(_rows[i].get_node(^"Text") as Label).add_theme_color_override(&"font_color", color)
	var row := _rows[index]
	_cursor.position = row.position + Vector2(-PAW[0].length() * ITEM_SCALE - 6.0, 3.0 + (PixelFont.size() - PAW.size()) * ITEM_SCALE * 0.5).floor()


func _activate() -> void:
	if _items.is_empty():
		return
	if _page == &"results" and _results_lock > 0.0:
		return
	var item := _items[_index]
	if not item.has("kind") and item["do"] != Callable(_go_back):
		AudioManager.play_sfx(&"menu_select", 0.0, 0.0)
	(item["do"] as Callable).call()


func _adjust(step: int) -> void:
	var item := _items[_index]
	if item.get("kind") == &"choice":
		_cycle_language(step)
	elif item.get("kind") == &"look":
		_cycle_look(item["setting"], step)
	elif item.has("kind"):
		_adjust_setting(item["setting"], step, item["kind"] == &"slider")


func _is_disabled(item: Dictionary) -> bool:
	return String(item.get("setting", "")).begins_with("assist_") and not Settings.assist_on()


func _cycle_language(step: int) -> void:
	var languages := Settings.LANGUAGES
	var next: String = languages[wrapi(Settings.language_index() + step, 0, languages.size())][0]
	Settings.change("language", next)
	AudioManager.play_sfx(&"menu_move", 0.0, 0.0)
	_rebuild()


func _rebuild() -> void:
	var index := _index
	_set_page(_page)
	_select(index, false)


func _focus(key: StringName) -> void:
	for i in _items.size():
		if _items[i]["key"] == key:
			_select(i, false)
			return


func _adjust_setting(setting: String, step: int, is_slider: bool, wrap := false) -> void:
	var current: Variant = Settings.value(setting)
	var next: Variant
	if is_slider:
		next = clampi(int(current) + step, 0, Settings.STEPS)
		if wrap and int(current) == Settings.STEPS:
			next = 0
	else:
		next = not bool(current)
	if next == current:
		return
	Settings.change(setting, next)
	AudioManager.play_sfx(&"menu_move", 0.0, 0.0)
	if setting == "assist":
		_rebuild()
	else:
		_refresh_value(_rows[_index].get_node(^"Value"), _items[_index])


func _go_back() -> void:
	match _page:
		&"options", &"credits", &"confirm_new", &"chapters", &"assist", &"confirm_chapter", &"character":
			AudioManager.play_sfx(&"menu_back", 0.0, 0.0)
			var from := _page
			var parent: StringName = &"main" if _title_mode else &"pause"
			var focus := StringName("MENU_" + String(from).to_upper())
			match from:
				&"assist":
					parent = &"options"
				&"confirm_new":
					focus = &"MENU_NEW_GAME"
				&"confirm_chapter":
					parent = &"chapters"
					focus = Chapters.name_key(_chapter)
			_set_page(parent)
			_focus(focus)
		&"pause":
			AudioManager.play_sfx(&"menu_back", 0.0, 0.0)
			_choose(resume_chosen)


func _pick_chapter(index: int) -> void:
	_chapter = index
	if _has_save or not _title_mode:
		_set_page(&"confirm_chapter")
	else:
		_start_chapter()


func _start_chapter() -> void:
	close()
	chapter_chosen.emit(_chapter)


func _on_new_game() -> void:
	if _has_save:
		_set_page(&"confirm_new")
	else:
		_choose(new_game_chosen)


func _choose(chosen: Signal) -> void:
	close()
	chosen.emit()


func _quit() -> void:
	_open = false
	await Transitions.fade_out(0.3)
	get_tree().quit()


func _on_row_input(event: InputEvent, index: int) -> void:
	var click := event as InputEventMouseButton
	if click == null or not click.pressed or click.button_index != MOUSE_BUTTON_LEFT:
		return
	_select(index, false)
	var item := _items[index]
	if item.get("kind") == &"slider":
		_adjust_setting(item["setting"], 1, true, true)
	else:
		_activate()


func _column_center() -> float:
	return LOOK_LIST_X + LOOK_ROW_WIDTH * 0.5 if _page == &"character" else SCREEN.x * 0.5


func _row_width() -> float:
	return LOOK_ROW_WIDTH if _page == &"character" else ROW_WIDTH


func _cycle_look(piece: String, step: int) -> void:
	var had: String = HeroLook.current()[piece]
	HeroLook.cycle(piece, step)
	AudioManager.play_sfx(&"menu_move", 0.0, 0.0)
	var now: String = HeroLook.current()[piece]
	if piece in ["hat", "scarf"] and (had == "none") != (now == "none"):
		_rebuild()
	else:
		_refresh_value(_rows[_index].get_node(^"Value"), _items[_index])


func _randomize_look() -> void:
	HeroLook.randomize_look()
	_rebuild()


func _reset_look() -> void:
	HeroLook.reset()
	_rebuild()


func _refresh_look_value(value: Control, piece: String) -> void:
	var label := value.get_child(0) as Label
	label.text = tr(HeroLook.option_name(piece))
	var width := _text_width(label.text) * ITEM_SCALE
	var swatch := value.get_node_or_null(^"Swatch") as Control
	if swatch:
		for child in swatch.get_children():
			child.queue_free()
		var colors := HeroLook.colors(HeroLook.current())
		var letters: Array = SWATCH[piece]
		var frame := ColorRect.new()
		frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
		frame.color = SHADOW
		frame.size = Vector2(SWATCH_CELL.x * letters.size() + 2, SWATCH_CELL.y + 2)
		swatch.add_child(frame)
		for i in letters.size():
			var cell := ColorRect.new()
			cell.mouse_filter = Control.MOUSE_FILTER_IGNORE
			cell.color = colors[letters[i]]
			cell.size = SWATCH_CELL
			cell.position = Vector2(1 + i * SWATCH_CELL.x, 1)
			swatch.add_child(cell)
		swatch.position = Vector2(width + 4.0, -1.0)
		width += 4.0 + frame.size.x
	value.position = Vector2(_row_width() - width, 3)


func _make_preview() -> Node2D:
	var holder := Node2D.new()
	var floor_line := ColorRect.new()
	floor_line.color = Color(SHADOW, 0.8)
	floor_line.size = Vector2(12, 2) * PREVIEW_SCALE
	floor_line.position = PREVIEW_FEET + Vector2(-6, -0.5) * PREVIEW_SCALE
	holder.add_child(floor_line)
	_preview = AnimatedSprite2D.new()
	_preview.centered = false
	_preview.scale = Vector2.ONE * PREVIEW_SCALE
	_preview.position = PREVIEW_FEET - Vector2(16, 30) * PREVIEW_SCALE
	HeroLook.dress(_preview)
	holder.add_child(_preview)
	_animate_preview(0.0)
	return holder


func _animate_preview(delta: float) -> void:
	if _preview == null or not is_instance_valid(_preview):
		return
	_preview_time += delta
	var wanted := PREVIEW_ANIMS[int(_preview_time / PREVIEW_EVERY) % PREVIEW_ANIMS.size()]
	if _preview.animation != wanted or not _preview.is_playing():
		_preview.play(wanted)


func _process(delta: float) -> void:
	_results_lock = maxf(_results_lock - delta, 0.0)
	_animate_preview(delta)
	if not _open or Engine.get_process_frames() == _opened_frame:
		return
	if Input.is_action_just_pressed(&"jump") or Input.is_action_just_pressed(&"ui_accept"):
		_activate()
		return
	if Input.is_action_just_pressed(&"pause") or Input.is_action_just_pressed(&"ui_cancel") or Input.is_action_just_pressed(&"dash"):
		_go_back()
		return
	var held := _held_input()
	if held != _held:
		_held = held
		_held_time = 0.0
		_step(held)
	elif held != Vector2i.ZERO:
		_held_time += delta
		if _held_time >= REPEAT_DELAY:
			_held_time -= REPEAT_EVERY
			_step(held)


func _held_input() -> Vector2i:
	return Vector2i(int(Input.is_action_pressed(&"move_right")) - int(Input.is_action_pressed(&"move_left")),
		int(Input.is_action_pressed(&"move_down")) - int(Input.is_action_pressed(&"move_up")))


func _step(direction: Vector2i) -> void:
	if direction.y != 0:
		_select(_index + direction.y)
	elif direction.x != 0:
		_adjust(direction.x)


func _make_title() -> Control:
	var box := Control.new()
	box.set_anchors_preset(Control.PRESET_FULL_RECT)
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var title := _label(tr(&"GAME_TITLE"), TITLE_SCALE, TEXT)
	title.add_theme_constant_override(&"shadow_offset_x", 2)
	title.add_theme_constant_override(&"shadow_offset_y", 2)
	_center(title, TITLE_Y, TITLE_SCALE)
	box.add_child(title)
	var half := _text_width(title.text) * TITLE_SCALE * 0.5
	var middle := TITLE_Y + PixelFont.size() * TITLE_SCALE * 0.5
	for x: float in [SCREEN.x * 0.5 - half - LINE_GAP - LINE_LENGTH, SCREEN.x * 0.5 + half + LINE_GAP]:
		for layer_offset: Array in [[Vector2(1, 1), SHADOW], [Vector2.ZERO, TEXT]]:
			var line := ColorRect.new()
			line.mouse_filter = Control.MOUSE_FILTER_IGNORE
			line.color = layer_offset[1]
			line.size = Vector2(LINE_LENGTH, 2)
			line.position = (Vector2(x, middle - 1.0) + layer_offset[0]).floor()
			box.add_child(line)
	return box


func _make_paw() -> Control:
	var paw := Control.new()
	paw.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for pass_color: Array in [[Vector2(1, 1), SHADOW], [Vector2.ZERO, WARM]]:
		for y in PAW.size():
			for x in PAW[y].length():
				if PAW[y][x] == "#":
					var pixel := ColorRect.new()
					pixel.mouse_filter = Control.MOUSE_FILTER_IGNORE
					pixel.color = pass_color[1]
					pixel.size = Vector2.ONE * ITEM_SCALE
					pixel.position = (Vector2(x, y) + pass_color[0]) * ITEM_SCALE
					paw.add_child(pixel)
	return paw


func _label(text: String, text_scale: int, color: Color) -> Label:
	var label := Label.new()
	label.text = text
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	label.scale = Vector2.ONE * text_scale
	label.add_theme_font_override(&"font", PixelFont.get_font())
	label.add_theme_font_size_override(&"font_size", PixelFont.size())
	label.add_theme_color_override(&"font_color", color)
	label.add_theme_constant_override(&"outline_size", 0)
	label.add_theme_color_override(&"font_shadow_color", SHADOW)
	label.add_theme_constant_override(&"shadow_offset_x", 1)
	label.add_theme_constant_override(&"shadow_offset_y", 1)
	return label


func _center(label: Label, y: float, text_scale: int) -> void:
	label.position = Vector2(roundf((SCREEN.x - _text_width(label.text) * text_scale) * 0.5), y)


func _text_width(text: String) -> float:
	return PixelFont.get_font().get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, PixelFont.size()).x
