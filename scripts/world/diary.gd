class_name Diary
extends Node2D

const HINT_LIFT := 12.0

var _hint: Hint


static func create(feet: Vector2) -> Diary:
	var diary := Diary.new()
	diary.position = feet
	return diary


func _ready() -> void:
	_hint = Hint.create(Vector2(0, -HINT_LIFT), "DIARY_LOOK")
	add_child(_hint)
	visible = Game.dog_taken
	for arg in OS.get_cmdline_user_args():
		if arg == "--diary-hint":
			Game.dog_taken = true
		elif arg.begins_with("--diary"):
			_open_for_capture.call_deferred()


func _process(_delta: float) -> void:
	visible = Game.dog_taken
	if not visible or DiaryReader.is_open():
		return
	if Input.is_action_just_pressed(&"move_up") and _player_near():
		DiaryReader.open(self)


func _player_near() -> bool:
	var player := Combat.find_player(self)
	if player == null or not player.input_enabled or player.seated or not player.is_on_floor():
		return false
	var offset := player.global_position - global_position
	return absf(offset.x) < Hint.RANGE.x and absf(offset.y) < Hint.RANGE.y


func _open_for_capture() -> void:
	Game.dog_taken = true
	visible = true
	var spread := 0
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--diary="):
			spread = int(arg.get_slice("=", 1))
	DiaryReader.open(self, spread)
