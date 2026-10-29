extends Node

const FOLDER := "user://telemetry"

var enabled := true

var _file: FileAccess


func _ready() -> void:
	if DisplayServer.get_name() == "headless":
		enabled = false
	Events.room_entered.connect(func(room_id: String) -> void: log_event("room_enter", Vector2.ZERO, room_id))
	Events.player_died.connect(func(at: Vector2) -> void: log_event("death", at))
	Events.checkpoint_reached.connect(func(checkpoint: Node2D) -> void: log_event("checkpoint", checkpoint.global_position))


func log_event(event: String, at := Vector2.ZERO, extra := "") -> void:
	if not enabled:
		return
	if _file == null:
		DirAccess.make_dir_recursive_absolute(FOLDER)
		var stamp := Time.get_datetime_string_from_system().replace(":", "-")
		_file = FileAccess.open("%s/session_%s.csv" % [FOLDER, stamp], FileAccess.WRITE)
		if _file == null:
			enabled = false
			return
		_file.store_line("tempo,evento,sala,x,y,extra")
	_file.store_line("%.2f,%s,%s,%d,%d,%s" % [Game.play_time, event, Game.current_room, at.x, at.y, extra])
	_file.flush()
