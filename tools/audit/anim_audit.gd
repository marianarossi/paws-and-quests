extends SceneTree

const EVENTS: Array = [
	[0.5, "move_left", true], [2.0, "move_left", false],
	[2.3, "move_left", true], [2.35, "jump", true], [2.75, "jump", false], [4.2, "move_left", false],
	[4.5, "move_left", true], [4.55, "jump", true], [4.9, "jump", false],
	[5.25, "jump", true], [5.35, "jump", false], [6.4, "move_left", false],
	[6.8, "move_up", true], [6.85, "dash", true], [6.9, "dash", false], [7.0, "move_up", false],
	[8.2, "jump", true], [8.5, "jump", false], [8.45, "dash", true], [8.5, "dash", false],
	[9.5, "move_right", true],
	[9.9, "jump", true], [10.25, "jump", false], [10.5, "jump", true], [10.85, "jump", false],
	[11.1, "jump", true], [11.45, "jump", false], [11.7, "jump", true], [11.95, "jump", false],
	[12.1, "jump", true], [12.4, "jump", false], [12.8, "dash", true], [12.85, "dash", false],
	[13.3, "jump", true], [13.6, "jump", false], [13.7, "move_up", true], [13.75, "dash", true],
	[13.8, "dash", false], [13.9, "move_up", false], [14.4, "jump", true], [14.7, "jump", false],
	[15.2, "jump", true], [15.3, "jump", false], [15.8, "jump", true], [16.2, "jump", false],
	[16.6, "move_down", true], [16.65, "dash", true], [16.7, "dash", false], [16.8, "move_down", false],
	[17.3, "jump", true], [17.7, "jump", false], [18.2, "jump", true], [18.5, "jump", false],
	[19.0, "jump", true], [19.35, "jump", false], [19.6, "jump", true], [19.9, "jump", false],
	[20.5, "move_right", false],
	[21.0, "move_left", true], [21.05, "move_left", false], [21.2, "move_right", true], [21.25, "move_right", false],
	[21.4, "move_left", true], [21.6, "move_left", false], [21.7, "move_right", true], [22.3, "move_right", false],
]
const DURATION := 23.5

var _player: Node
var _time := 0.0
var _index := 0
var _rows: PackedStringArray = ["tick,t,state,anim,frame,floor,vx,vy,facing,sx,sy,wall,move_x,x,y"]
var _tick := 0
var _events: Array = []


func _initialize() -> void:
	_events = EVENTS.duplicate()
	_events.sort_custom(func(a: Array, b: Array) -> bool: return a[0] < b[0])
	var lab: Node = (load("res://scenes/dev/movement_lab.tscn") as PackedScene).instantiate()
	root.add_child(lab)


func _physics_process(delta: float) -> bool:
	if _player == null:
		_player = get_first_node_in_group(&"player")
		if _player == null:
			return false
	var sprite: AnimatedSprite2D = _player.get(&"body_sprite")
	var machine: Node = _player.get(&"state_machine")
	var visual: Node2D = _player.get(&"visual")
	var velocity: Vector2 = _player.get(&"velocity")
	_rows.append("%d,%.4f,%s,%s,%d,%d,%.1f,%.1f,%d,%.3f,%.3f,%d,%d,%.1f,%.1f" % [
		_tick, _time, machine.get(&"current_name"), sprite.animation, sprite.frame,
		int(_player.call(&"is_on_floor")), velocity.x, velocity.y, _player.get(&"facing"),
		visual.scale.x, visual.scale.y, _player.get(&"wall_dir"), int(_player.get(&"move_x")),
		(_player as Node2D).global_position.x, (_player as Node2D).global_position.y])
	while _index < _events.size() and _events[_index][0] <= _time:
		var event: Array = _events[_index]
		if event[2]:
			Input.action_press(event[1])
		else:
			Input.action_release(event[1])
		_index += 1
	_time += delta
	_tick += 1
	if _time >= DURATION:
		var out := "user://anim_audit.csv"
		for arg in OS.get_cmdline_user_args():
			if arg.begins_with("--out="):
				out = arg.trim_prefix("--out=")
		var file := FileAccess.open(out, FileAccess.WRITE)
		file.store_string("\n".join(_rows))
		file.close()
		print("AUDIT ", _rows.size() - 1, " passos -> ", out)
		return true
	return false
