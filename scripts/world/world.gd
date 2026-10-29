class_name World
extends Node2D

const PLAYER_SCENE := preload("res://scenes/player/player.tscn")
const TRANSITION_TIME := 0.45
const ROOM_UP_BOOST := 300.0
const DEATH_PAUSE := 0.35
const RESET_GROUP := &"reset_on_death"
const PIT_MARGIN := 64.0
const RESPAWN_ZOOM := 2.0
const SEAT_OFFSET := Vector2(-15, 0)
const THEME_FADE := 0.6
const DOOR_PAUSE := 0.6
const TITLE_CAMERA_LIFT := 120.0
const END_COLOR := Color("1c1433")
const END_HOLD := 5.0
const RESULTS_DELAY := 0.4

@export_dir var map_dir := "res://levels/dev/hazards"
@export var start_room := ""
@export var unlock_all_abilities := false
@export var start_abilities: Array[StringName] = []

var player: Player
var current: Room
var respawn_point := Vector2.ZERO
var campfire := Vector2.INF
var campfire_room := ""

var _current_id := ""
var _hud: Hud
var _menu: GameMenu
var _in_menu := false
var _area := ""

var _data: Dictionary[String, RoomData] = {}
var _rooms: Dictionary[String, Room] = {}
var _theme: ZoneTheme
var _background: Background
var _ambient: CPUParticles2D
var _busy := false
var _pit_cache: Dictionary[String, float] = {}

@onready var camera: RoomCamera = $RoomCamera
@onready var _overlay: CanvasLayer = $DebugOverlay


func _ready() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--map="):
			map_dir = "res://levels/dev/" + arg.get_slice("=", 1)
			unlock_all_abilities = true
		elif arg == "--all":
			unlock_all_abilities = true
	if unlock_all_abilities:
		Game.unlock_all()
	else:
		for ability in start_abilities:
			Game.set_ability(ability, true)
	for arg in _dev_args():
		if arg.begins_with("--room="):
			start_room = arg.get_slice("=", 1)
		elif arg.begins_with("--fight"):
			start_room = "z2"
	for file in DirAccess.get_files_at(map_dir):
		if file.ends_with(".room"):
			var data := RoomData.load_file(map_dir.path_join(file))
			_data[data.id] = data
	assert(not _data.is_empty(), "nenhuma sala em " + map_dir)
	var first := start_room if _data.has(start_room) else _first_room_id()
	if first != _first_room_id() and not unlock_all_abilities:
		Game.set_ability(&"dash", true)
	_set_theme(ZoneTheme.of(_data[first].zone), true)
	add_child(ProjectilePool.new())
	_activate(first)
	respawn_point = current.spawn_point
	player = PLAYER_SCENE.instantiate()
	add_child(player)
	player.teleport(respawn_point)
	player.died.connect(_on_player_died)
	Events.checkpoint_reached.connect(_on_checkpoint_reached)
	Events.door_entered.connect(_go_through)
	Events.glow_entered.connect(_go_through.bind(true))
	Game.feather_total = _count_feathers()
	Events.gift_received.connect(func(_ability: StringName) -> void: SaveManager.save_game(respawn_point))
	for arg in _dev_args():
		if arg.begins_with("--at="):
			player.teleport(current.position + Room.cell_to_feet(Vector2i(RoomData.to_vector(arg.get_slice("=", 1)))))
	camera.follow(player, current.bounds)
	_set_ambient(_theme)
	_overlay.call(&"watch", player)
	_overlay.visible = false
	Game.current_room = first
	Game.timer_running = true
	AudioManager.play_music(StringName(_theme.music))
	_hud = Hud.new()
	add_child(_hud)
	_menu = GameMenu.new()
	add_child(_menu)
	_menu.new_game_chosen.connect(_on_new_game)
	_menu.continue_chosen.connect(_on_continue)
	_menu.resume_chosen.connect(_resume)
	_menu.title_chosen.connect(_back_to_title)
	_menu.chapter_chosen.connect(_on_chapter)
	_menu.skip_fight_chosen.connect(_on_skip_fight)
	var chapter := _chapter_next
	_chapter_next = -1
	_in_menu = chapter < 0 and _wants_title_screen()
	_title_next = false
	Events.room_entered.connect(_on_room_entered)
	Events.room_entered.emit(first)
	if chapter >= 0:
		_on_chapter.call_deferred(chapter)
	elif _in_menu:
		_show_title()
	elif OS.get_cmdline_user_args().has("--end-screen") or OS.get_cmdline_user_args().has("--end-lore"):
		_show_results_now.call_deferred()
	elif OS.get_cmdline_user_args().has("--intro"):
		_start_intro_now.call_deferred()
	if DevTools.shot_delay() >= 0.0:
		_overlay.visible = false
		_hud.visible = OS.get_cmdline_user_args().has("--hud")
		DevTools.screenshot_and_quit(self, DevTools.shot_delay(), player)


func _physics_process(_delta: float) -> void:
	if camera.is_zoomed() and not player.seated and not _busy and not camera.held:
		camera.release_zoom()
	if _busy or player.is_dead():
		return
	var point := player.global_position + Vector2(0, -8)
	if point.y > _pit_y() and not _room_below(point.x):
		player.die(true)
		return
	if current.bounds.has_point(point):
		return
	for id in _data:
		if id != current.data.id and _rect(_data[id]).has_point(point):
			_enter_room(id)
			return
	if point.y > current.bounds.end.y:
		player.die(true)
		return
	if point.x < current.bounds.position.x or point.x > current.bounds.end.x:
		player.global_position.x = clampf(player.global_position.x, current.bounds.position.x, current.bounds.end.x)
		player.velocity.x = 0.0
	if point.y < current.bounds.position.y:
		player.global_position.y = current.bounds.position.y + 8.0
		player.velocity.y = maxf(player.velocity.y, 0.0)


func _pit_y() -> float:
	var id := current.data.id
	if not _pit_cache.has(id):
		var data := current.data
		var top := -1
		var water := -1
		for y in data.height:
			for x in data.width:
				var c := data.raw_cell(x, y)
				if c == "." or c == " " or c == "":
					continue
				if c == RoomData.WATER:
					water = y
				elif y == 0 or data.raw_cell(x, y - 1) == "." or data.raw_cell(x, y - 1) == RoomData.WATER:
					top = maxi(top, y)
		for letter in data.defs:
			var to := String(data.defs[letter].get("to", ""))
			if to.count(",") != 1:
				continue
			for cell in data.find_cells(letter):
				top = maxi(top, cell.y + int(to.get_slice(",", 1)))
		var pit := maxf(top * Room.TILE + PIT_MARGIN, (water + 1) * Room.TILE + PIT_MARGIN)
		_pit_cache[id] = minf(current.bounds.end.y, current.bounds.position.y + pit)
	return _pit_cache[id]


func _room_below(x: float) -> bool:
	var probe := Vector2(x, current.bounds.end.y + 8.0)
	for id in _data:
		if id != current.data.id and _rect(_data[id]).has_point(probe):
			return true
	return false


func _count_feathers() -> int:
	var total := 0
	for id in _data:
		var data: RoomData = _data[id]
		for letter: String in data.defs:
			if data.defs[letter].get("type", "") == "feather":
				for row in data.rows:
					total += row.count(letter)
	return total


func room_count() -> int:
	return _data.size()


func _first_room_id() -> String:
	var ids := _data.keys()
	ids.sort()
	return ids[0]


func _rect(data: RoomData) -> Rect2:
	return Rect2(Vector2(data.world_cell) * Room.TILE, Vector2(data.width, data.height) * Room.TILE)


func _activate(id: String) -> void:
	current = _build(id)
	_current_id = id
	_set_camera_floor()
	_refresh_neighbours()


func _refresh_neighbours() -> void:
	var id := _current_id
	var keep: Array[String] = [id]
	for other in _data:
		if other != id and _rect(_data[id]).grow(2.0).intersects(_rect(_data[other])):
			_build(other)
			keep.append(other)
	for built: String in _rooms.keys():
		if not keep.has(built):
			_rooms[built].queue_free()
			_rooms.erase(built)


func _build(id: String) -> Room:
	if not _rooms.has(id):
		var room := RoomBuilder.build(_data[id], ZoneTheme.of(_data[id].zone))
		add_child(room)
		_rooms[id] = room
	return _rooms[id]


func _enter_room(id: String) -> void:
	_busy = true
	var going_up := _rect(_data[id]).end.y <= current.bounds.position.y + 1.0
	current = _build(id)
	_current_id = id
	_set_camera_floor()
	ProjectilePool.of(self).clear()
	respawn_point = current.nearest_spawn(player.global_position)
	Game.current_room = id
	Events.room_entered.emit(id)
	player.set_physics_process(false)
	camera.transition_to(current.bounds, TRANSITION_TIME)
	await camera.transition_finished
	if going_up:
		player.velocity.y = minf(player.velocity.y, -ROOM_UP_BOOST)
	player.set_physics_process(true)
	_busy = false
	_refresh_neighbours()


func _go_through(id: String, bright := false) -> void:
	if _busy or player.is_dead() or not _data.has(id):
		return
	_busy = true
	player.set_physics_process(false)
	if bright:
		await Transitions.fade_out(1.2, Color(1.0, 0.98, 0.94))
	else:
		await Transitions.fade_out(0.5)
	ProjectilePool.of(self).clear()
	_set_theme(ZoneTheme.of(_data[id].zone), true)
	_activate(id)
	Game.current_room = id
	respawn_point = current.spawn_point
	player.teleport(respawn_point)
	camera.follow(player, current.bounds)
	Events.room_entered.emit(id)
	await get_tree().create_timer(DOOR_PAUSE).timeout
	player.set_physics_process(true)
	await Transitions.fade_in(0.3)
	_busy = false


func _on_player_died() -> void:
	_busy = true
	Game.deaths += 1
	Events.player_died.emit(player.global_position)
	camera.shake(3.0, 0.25)
	await get_tree().create_timer(DEATH_PAUSE).timeout
	await Transitions.iris_close(_screen_point(player.global_position + Vector2(0, -9)))
	var at_fire := campfire != Vector2.INF
	if at_fire:
		if campfire_room != _current_id:
			_activate(campfire_room)
			Game.current_room = campfire_room
			Events.room_entered.emit(campfire_room)
		respawn_point = campfire + SEAT_OFFSET
	ProjectilePool.of(self).clear()
	player.respawn(respawn_point, at_fire)
	get_tree().call_group(RESET_GROUP, &"reset_on_death")
	if at_fire:
		camera.focus_zoom(RESPAWN_ZOOM)
	camera.follow(player, current.bounds)
	await get_tree().process_frame
	await Transitions.iris_open(_screen_point(player.global_position + Vector2(0, -9)))
	Events.player_respawned.emit()
	_busy = false


func _on_checkpoint_reached(checkpoint: Node2D) -> void:
	if _in_menu:
		return
	respawn_point = checkpoint.global_position
	campfire = checkpoint.global_position
	campfire_room = _current_id
	SaveManager.save_game(respawn_point)


func load_save() -> bool:
	var data := SaveManager.load_game()
	var room_id := String(data.get("room", ""))
	if not _data.has(room_id):
		return false
	Game.from_dict(data)
	var spawn: Array = data.get("spawn", [0, 0])
	_activate(room_id)
	campfire = Vector2(spawn[0], spawn[1])
	campfire_room = room_id
	respawn_point = campfire + SEAT_OFFSET
	player.respawn(respawn_point, true)
	camera.follow(player, current.bounds)
	var fire := _checkpoint_at(campfire)
	if fire:
		fire.light_up(true)
	Game.current_room = room_id
	Events.room_entered.emit(room_id)
	return true


func _on_room_entered(id: String) -> void:
	_set_theme(ZoneTheme.of(_data[id].zone))
	AudioManager.play_ambience(StringName(ZoneTheme.of(_data[id].zone).ambience))
	AudioManager.play_music(StringName(ZoneTheme.of(_data[id].zone).music))
	var area: String = _data[id].meta.get("area", "")
	if area != "" and area != _area and not _in_menu:
		_hud.show_zone(StringName("ZONE_" + area.to_upper()))
	_area = area


static var _title_next := false
static var _chapter_next := -1


func _dev_args() -> PackedStringArray:
	return PackedStringArray() if _title_next or _chapter_next >= 0 else OS.get_cmdline_user_args()


func _wants_title_screen() -> bool:
	if _title_next:
		return true
	var args := OS.get_cmdline_user_args()
	for arg in args:
		if arg.begins_with("--menu"):
			return true
	if get_tree().current_scene != self:
		return false
	for arg in args:
		for dev: String in ["--map", "--room", "--at", "--shot", "--demo", "--bench", "--all", "--intro", "--fight", "--end-screen", "--end-lore"]:
			if arg.begins_with(dev):
				return false
	return true


func _show_title() -> void:
	Game.timer_running = false
	_hud.visible = false
	player.input_enabled = false
	var fire := _checkpoint_at(current.spawn_point)
	if fire:
		fire.light_up(true)
		player.respawn(fire.global_position + SEAT_OFFSET, true)
	camera.target_offset.y -= TITLE_CAMERA_LIFT
	camera.follow(player, current.bounds)
	var page := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--menu="):
			page = arg.get_slice("=", 1)
	if page == "pause":
		_in_menu = false
		_pause()
		return
	_menu.open_title(SaveManager.has_save())
	if page != "":
		_menu.open_page(StringName(page))
	Transitions.fade_in(0.6)


func _on_new_game() -> void:
	_in_menu = false
	SaveManager.delete_save()
	Game.reset_run()
	CloudStep.reset_all()
	Game.current_room = _current_id
	if unlock_all_abilities:
		Game.unlock_all()
	else:
		for ability in start_abilities:
			Game.set_ability(ability, true)
	var fire := _checkpoint_at(current.spawn_point)
	if fire:
		_on_checkpoint_reached(fire)
	var dog := _camp_dog()
	if dog:
		_lower_title_camera()
		_busy = true
		IntroScene.start(self, dog)
	else:
		_begin_play(true)


func _camp_dog() -> DogNpc:
	for node in get_tree().get_nodes_in_group(DogNpc.GROUP):
		var dog := node as DogNpc
		if dog.sheet == "dog" and current.is_ancestor_of(dog):
			return dog
	return null


func end_intro() -> void:
	_busy = false
	_begin_play(true)


func _start_intro_now() -> void:
	var fire := _checkpoint_at(current.spawn_point)
	if fire:
		fire.light_up(true)
		player.respawn(fire.global_position + SEAT_OFFSET, true)
	camera.follow(player, current.bounds)
	var dog := _camp_dog()
	if dog:
		_busy = true
		IntroScene.start(self, dog)


func _on_continue() -> void:
	await Transitions.fade_out(0.3)
	_in_menu = false
	_area = ""
	load_save()
	var dog := _camp_dog()
	if dog:
		dog.queue_free()
	_begin_play(false)
	await Transitions.fade_in(0.4)


func _begin_play(show_card: bool) -> void:
	_in_menu = false
	_lower_title_camera()
	_hud.visible = true
	Game.timer_running = true
	if show_card and _area != "":
		_hud.show_zone(StringName("ZONE_" + _area.to_upper()))
	await get_tree().create_timer(0.15).timeout
	player.input_enabled = true


func show_energy(total: int, left: int) -> void:
	_hud.show_energy(total, left)


func boss_bar() -> BossBar:
	return _hud.boss_bar()


func end_game() -> void:
	_busy = true
	Game.finished = true
	Game.timer_running = false
	SaveManager.save_game(respawn_point)
	var layer := CanvasLayer.new()
	layer.layer = 35
	add_child(layer)
	var screen := ColorRect.new()
	screen.set_anchors_preset(Control.PRESET_FULL_RECT)
	screen.mouse_filter = Control.MOUSE_FILTER_IGNORE
	screen.color = Color(1, 1, 1, 0)
	layer.add_child(screen)
	var fade := create_tween()
	fade.tween_property(screen, "color:a", 1.0, 1.4).set_trans(Tween.TRANS_SINE)
	fade.tween_interval(0.6)
	fade.tween_property(screen, "color", Color(END_COLOR, 1.0), 1.8)
	await fade.finished
	await _show_lore(layer)
	_hud.show_card(&"END_TITLE", &"END_LINE", END_HOLD)
	await get_tree().create_timer(END_HOLD + 1.8 + RESULTS_DELAY).timeout
	await _show_results()
	_back_to_title()


func _show_lore(layer: CanvasLayer) -> void:
	var lore := EndLore.create(tr(&"END_LORE"))
	layer.add_child(lore)
	await lore.finished
	lore.queue_free()


func _show_results() -> void:
	player.input_enabled = false
	_hud.visible = false
	_menu.open_results()
	await _menu.results_closed


func _show_results_now() -> void:
	_busy = true
	Game.timer_running = false
	var layer := CanvasLayer.new()
	layer.layer = 35
	add_child(layer)
	var screen := ColorRect.new()
	screen.set_anchors_preset(Control.PRESET_FULL_RECT)
	screen.color = END_COLOR
	layer.add_child(screen)
	if OS.get_cmdline_user_args().has("--end-lore"):
		await _show_lore(layer)
	await _show_results()
	_back_to_title()


func _lower_title_camera() -> void:
	if camera.target_offset.y < -TITLE_CAMERA_LIFT:
		camera.target_offset.y += TITLE_CAMERA_LIFT


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed(&"pause") and not _in_menu and not _busy and not player.is_dead() and not _menu.is_open():
		get_viewport().set_input_as_handled()
		_pause()


func _pause() -> void:
	get_tree().paused = true
	player.input_enabled = false
	_menu.open_pause(_throne_fight() != null and _throne_fight().can_skip())


func _throne_fight() -> ThroneFight:
	for node in get_tree().get_nodes_in_group(ThroneFight.GROUP):
		if current.is_ancestor_of(node):
			return node as ThroneFight
	return null


func _on_skip_fight() -> void:
	await _resume()
	var fight := _throne_fight()
	if fight and fight.can_skip():
		fight.skip()


func _on_chapter(index: int) -> void:
	if get_tree().paused:
		_chapter_next = index
		await Transitions.fade_out(0.4)
		get_tree().paused = false
		get_tree().reload_current_scene()
		return
	await Transitions.fade_out(0.3)
	var feathers := Game.feathers.duplicate()
	SaveManager.delete_save()
	Game.reset_run()
	CloudStep.reset_all()
	Game.feathers = feathers
	Game.dog_taken = true
	for node in get_tree().get_nodes_in_group(DogNpc.GROUP):
		if (node as DogNpc).camp:
			node.queue_free()
	if unlock_all_abilities:
		Game.unlock_all()
	else:
		Game.set_ability(&"dash", Chapters.starts_with_dash(index))
	var id := Chapters.room(index)
	ProjectilePool.of(self).clear()
	_set_theme(ZoneTheme.of(_data[id].zone), true)
	_activate(id)
	Game.current_room = id
	_in_menu = false
	campfire = Vector2.INF
	respawn_point = current.spawn_point
	var fire := _checkpoint_at(current.spawn_point)
	if fire:
		fire.light_up(true)
		_on_checkpoint_reached(fire)
		respawn_point = campfire + SEAT_OFFSET
	player.respawn(respawn_point, fire != null)
	camera.follow(player, current.bounds)
	_area = String(_data[id].meta.get("area", ""))
	Events.room_entered.emit(id)
	_begin_play(false)
	_hud.show_zone(Chapters.name_key(index))
	await Transitions.fade_in(0.4)


func _resume() -> void:
	get_tree().paused = false
	await get_tree().create_timer(0.15).timeout
	if not _menu.is_open():
		player.input_enabled = true


func _back_to_title() -> void:
	_title_next = true
	await Transitions.fade_out(0.4)
	get_tree().paused = false
	Game.reset_run()
	CloudStep.reset_all()
	get_tree().reload_current_scene()


func _checkpoint_at(point: Vector2) -> Checkpoint:
	var best: Checkpoint = null
	for node in current.find_children("*", "", true, false):
		if node is Checkpoint and (best == null or (node as Checkpoint).global_position.distance_to(point) < best.global_position.distance_to(point)):
			best = node
	return best


func _unhandled_key_input(event: InputEvent) -> void:
	var key := event as InputEventKey
	if key == null or not key.pressed or key.echo:
		return
	if key.keycode == KEY_F11:
		Settings.change("fullscreen", not Settings.value("fullscreen"))
		return
	if not OS.is_debug_build():
		return
	match key.keycode:
		KEY_R:
			player.die(true)
		KEY_F9:
			load_save()
		KEY_PAGEDOWN:
			_jump_room(1)
		KEY_PAGEUP:
			_jump_room(-1)
		KEY_F3:
			_overlay.visible = not _overlay.visible


func _set_camera_floor() -> void:
	camera.floor_zone = Vector3.ZERO
	var spec: String = current.data.meta.get("camfloor", "")
	if spec != "":
		var parts := spec.split(",")
		camera.floor_zone = Vector3(current.bounds.position.x + float(parts[0]) * Room.TILE, current.bounds.position.x + float(parts[1]) * Room.TILE,
				current.bounds.position.y + float(parts[2]) * Room.TILE)


func _jump_room(step: int) -> void:
	if _busy or player.is_dead():
		return
	var ids := _data.keys()
	ids.sort()
	var id: String = ids[posmod(ids.find(_current_id) + step, ids.size())]
	_activate(id)
	Game.current_room = id
	Events.room_entered.emit(id)
	respawn_point = current.spawn_point
	player.teleport(respawn_point)
	camera.follow(player, current.bounds)


func _set_theme(theme: ZoneTheme, instant := false) -> void:
	if theme == _theme:
		return
	_theme = theme
	var old := _background
	_background = Background.new()
	var rooms: Array[Rect2] = []
	var ground := 0.0
	for id in _data:
		if ZoneTheme.of(_data[id].zone) == theme:
			var rect := _rect(_data[id])
			rooms.append(rect)
			var floor_y := rect.end.y
			if _data[id].meta.has("bgfloor"):
				floor_y = rect.position.y + float(_data[id].meta["bgfloor"]) * Room.TILE
			ground = maxf(ground, floor_y)
	_background.setup(theme, rooms, ground)
	add_child(_background)
	if old:
		if instant:
			old.queue_free()
		else:
			var fresh := _background
			old.set_clipping(true)
			fresh.set_clipping(true)
			get_tree().create_timer(TRANSITION_TIME + 0.1).timeout.connect(func() -> void:
				old.queue_free()
				if is_instance_valid(fresh):
					fresh.set_clipping(false))
	if is_node_ready():
		_set_ambient(theme)
	var modulate_node := $CanvasModulate as CanvasModulate
	if instant:
		modulate_node.color = theme.ambient
	else:
		create_tween().tween_property(modulate_node, "color", theme.ambient, THEME_FADE)


func _set_ambient(theme: ZoneTheme) -> void:
	if _ambient:
		_ambient.queue_free()
	_ambient = Background.make_ambient(theme)
	if _ambient:
		camera.add_child(_ambient)


func _screen_point(world_point: Vector2) -> Vector2:
	return get_viewport().get_canvas_transform() * world_point
