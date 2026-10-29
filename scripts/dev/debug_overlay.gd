extends CanvasLayer

var _player: Player
var _label: Label


func _ready() -> void:
	_label = Label.new()
	_label.position = Vector2(4, 4)
	_label.add_theme_font_size_override(&"font_size", 8)
	_label.add_theme_constant_override(&"outline_size", 3)
	_label.add_theme_color_override(&"font_outline_color", Color.BLACK)
	add_child(_label)


func watch(player: Player) -> void:
	_player = player


func _process(_delta: float) -> void:
	if _player == null or not visible:
		return
	_label.text = "%d fps  |  %s  |  sala %s  |  mortes %d\nvel %4.0f, %4.0f\ndash %d   pulos no ar %d   parede %d   chao %s" % [
		Engine.get_frames_per_second(), _player.state_machine.current_name, Game.current_room, Game.deaths,
		_player.velocity.x, _player.velocity.y,
		_player.dash_charges, _player.air_jumps_left, _player.wall_dir, _player.is_on_floor(),
	]
