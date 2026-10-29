extends Node

const VERSION := 1

var path := "user://save.json"


func has_save() -> bool:
	return FileAccess.file_exists(path)


func save_game(spawn: Vector2) -> bool:
	var data := Game.to_dict()
	data["version"] = VERSION
	data["spawn"] = [spawn.x, spawn.y]
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		push_warning("não foi possível gravar em %s" % path)
		return false
	file.store_string(JSON.stringify(data, "\t"))
	return true


func load_game() -> Dictionary:
	if not has_save():
		return {}
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if parsed is Dictionary and int((parsed as Dictionary).get("version", 0)) == VERSION:
		return parsed
	push_warning("save ignorado (formato desconhecido): %s" % path)
	return {}


func delete_save() -> void:
	if has_save():
		DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
