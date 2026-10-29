extends Node

const ABILITIES: Array[StringName] = [&"dash", &"double_jump"]

var deaths := 0
var play_time := 0.0
var current_room := ""
var timer_running := false
var dog_taken := false
var finished := false
var feathers: Dictionary[String, bool] = {}
var feather_total := 0

var _abilities: Dictionary[StringName, bool] = {}


func _ready() -> void:
	for ability in ABILITIES:
		_abilities[ability] = false
	TranslationServer.set_locale(Settings.locale())
	Settings.apply.call_deferred()


func _process(delta: float) -> void:
	if timer_running:
		play_time += delta


func _exit_tree() -> void:
	SpriteSheet.clear_cache()
	TerrainTiles.clear_cache()
	ZoneTheme.clear_cache()
	Lights.clear_cache()
	PixelFont.clear_cache()


func has_feather(key: String) -> bool:
	return feathers.has(key)


func take_feather(key: String) -> void:
	feathers[key] = true


func feather_count() -> int:
	return feathers.size()


static func format_time(seconds: float) -> String:
	var total := int(seconds)
	@warning_ignore("integer_division")
	var hours := total / 3600
	@warning_ignore("integer_division")
	var minutes := (total % 3600) / 60
	if hours > 0:
		return "%d:%02d:%02d" % [hours, minutes, total % 60]
	return "%d:%02d" % [minutes, total % 60]


func has_ability(ability: StringName) -> bool:
	return _abilities.get(ability, false)


func set_ability(ability: StringName, unlocked: bool) -> void:
	assert(ability in ABILITIES, "habilidade desconhecida: %s" % ability)
	if _abilities[ability] == unlocked:
		return
	_abilities[ability] = unlocked
	Events.ability_changed.emit(ability, unlocked)


func unlock_all() -> void:
	for ability in ABILITIES:
		set_ability(ability, true)


func reset_run() -> void:
	dog_taken = false
	feathers.clear()
	finished = false
	deaths = 0
	play_time = 0.0
	current_room = ""
	for ability in ABILITIES:
		set_ability(ability, false)


func to_dict() -> Dictionary:
	var unlocked: Array[String] = []
	for ability in ABILITIES:
		if _abilities[ability]:
			unlocked.append(String(ability))
	return {"deaths": deaths, "play_time": play_time, "room": current_room, "abilities": unlocked, "finished": finished, "feathers": feathers.keys()}


func from_dict(data: Dictionary) -> void:
	dog_taken = true
	finished = bool(data.get("finished", false))
	deaths = int(data.get("deaths", 0))
	play_time = float(data.get("play_time", 0.0))
	current_room = String(data.get("room", ""))
	feathers.clear()
	for key in data.get("feathers", []):
		feathers[String(key)] = true
	var unlocked: Array = data.get("abilities", [])
	for ability in ABILITIES:
		set_ability(ability, unlocked.has(String(ability)))
