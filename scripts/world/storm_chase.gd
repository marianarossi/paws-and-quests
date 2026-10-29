class_name StormChase
extends Node2D

enum State { WAIT, WARN, RUN, DONE }

const TEXTURE := preload("res://assets/sprites/props/storm_wall.png")
const TILE := 16
const FRAME := Vector2(96, 360)
const MERCY := 10.0
const WAKE := 7.0 * TILE
const WARN_TIME := 0.9

var speed := 96.0
var starts: Array[float] = []
var stop_x := 0.0
var room_id := ""
var state := State.WAIT
var front := 0.0

var _timer := 0.0
var _time := 0.0
var _thunder := 2.0
var _sprites: Array[Sprite2D] = []
var _height := 720.0
var _held := false


static func create(def: Dictionary, in_room: String, room_height: float) -> StormChase:
	var chase := StormChase.new()
	chase.speed = float(def.get("speed", "96"))
	for part in String(def.get("starts", "0")).split(","):
		chase.starts.append(float(part) * TILE)
	chase.starts.sort()
	chase.stop_x = float(def.get("to", "9999")) * TILE
	chase.room_id = in_room
	chase._height = room_height
	return chase


func _ready() -> void:
	z_index = 30
	var count := int(ceil(_height / FRAME.y)) + 1
	for i in count:
		var sprite := Sprite2D.new()
		sprite.texture = TEXTURE
		sprite.centered = false
		sprite.region_enabled = true
		sprite.region_rect = Rect2(Vector2.ZERO, FRAME)
		sprite.material = Lights.unshaded()
		sprite.position = Vector2(-FRAME.x + 30.0, i * FRAME.y - 40.0)
		add_child(sprite)
		_sprites.append(sprite)
	var mass := ColorRect.new()
	mass.color = Color("#1c1830")
	mass.position = Vector2(-2000.0 - FRAME.x + 31.0, -40.0)
	mass.size = Vector2(2000.0, _height + 80.0)
	mass.material = Lights.unshaded()
	add_child(mass)
	add_to_group(World.RESET_GROUP)
	Events.player_respawned.connect(reset)
	Events.player_died.connect(func(_at: Vector2) -> void: _held = true)
	Events.room_entered.connect(_on_room_entered)
	reset()


func _on_room_entered(id: String) -> void:
	if id == room_id:
		reset()


func reset_on_death() -> void:
	reset()


func reset() -> void:
	_held = false
	state = State.WAIT
	var player := Combat.find_player(self)
	var px: float = (player.global_position.x - (get_parent() as Node2D).global_position.x) if player else 0.0
	front = starts[0] if not starts.is_empty() else 0.0
	for x in starts:
		if x <= px - 2.0 * TILE:
			front = x
	if px > stop_x + 2.0 * TILE:
		front = stop_x
		state = State.DONE
	position.x = front


func _physics_process(delta: float) -> void:
	_time += delta
	var frame := int(_time * 6.0) % 2
	for sprite in _sprites:
		sprite.region_rect.position.x = frame * FRAME.x
	visible = Game.current_room == room_id
	if not visible:
		return
	var player := Combat.find_player(self)
	if player == null or _held or player.is_dead():
		return
	var px: float = player.global_position.x - (get_parent() as Node2D).global_position.x
	match state:
		State.WAIT:
			if not player.seated and px > front + WAKE:
				state = State.WARN
				_timer = Combat.telegraph_time(WARN_TIME)
				AudioManager.play_sfx(&"thunder", -2.0)
				Storm.flash_screen(get_tree(), 0.7)
		State.WARN:
			_timer -= delta
			if _timer <= 0.0:
				state = State.RUN
				_thunder = 1.5
		State.RUN:
			front = minf(stop_x, front + speed * delta)
			position.x = front
			if front >= stop_x:
				state = State.DONE
			_thunder -= delta
			if _thunder <= 0.0:
				_thunder = randf_range(1.6, 3.0)
				AudioManager.play_sfx(&"thunder_far", -4.0, 0.1)
				Storm.flash_screen(get_tree(), 0.25)
			if px < front - MERCY:
				player.die()
		State.DONE:
			if px < front - MERCY:
				player.die()
