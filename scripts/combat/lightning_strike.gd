class_name LightningStrike
extends Node2D

enum Phase { IDLE, WARN, STRIKE, FADE }

const TEXTURE := preload("res://assets/sprites/combat/strike.png")
const FRAMES := 3
const FRAME_SIZE := Vector2(96, 384)
const DEEP := Color("#c88a10")
const YELLOW := Color("#ffcc33")
const HOT := Color("#fff4c0")
const STRIKE_TIME := 0.22
const FADE_TIME := 0.4
const HIT_POINTS: Array[Vector2] = [Vector2(0, -6), Vector2(0, -16)]
const HIT_RADIUS := 3.0

var every := 3.0
var first := 1.0
var warn := 0.9
var half_width := 6.0
var height := 384.0
var room_id := ""
var once := false

var phase := Phase.IDLE

var _timer := 0.0
var _time := 0.0
var _sprite: Sprite2D
var _light: PointLight2D


static func create(def: Dictionary, feet: Vector2, in_room: String) -> LightningStrike:
	var bolt := LightningStrike.new()
	bolt.position = feet
	bolt.room_id = in_room
	bolt.every = float(def.get("every", bolt.every))
	bolt.first = float(def.get("first", bolt.first))
	bolt.warn = float(def.get("warn", bolt.warn))
	bolt.height = float(def.get("height", bolt.height))
	return bolt


static func spawn(parent: Node, feet: Vector2, warn_time := 0.9) -> LightningStrike:
	var bolt := LightningStrike.new()
	bolt.every = 0.0
	bolt.warn = warn_time
	bolt.once = true
	parent.add_child(bolt)
	bolt.global_position = feet
	bolt.strike()
	return bolt


func _ready() -> void:
	z_index = 8
	material = Lights.unshaded()
	_sprite = Sprite2D.new()
	_sprite.texture = TEXTURE
	_sprite.centered = false
	_sprite.region_enabled = true
	_sprite.material = Lights.unshaded()
	_sprite.visible = false
	add_child(_sprite)
	_light = Lights.point(YELLOW, 90.0, 0.0)
	_light.position = Vector2(0, -12)
	add_child(_light)
	if not once:
		_restart()
		Events.player_respawned.connect(_restart)
		Events.room_entered.connect(_on_room_entered)


func telegraph() -> float:
	return Combat.telegraph_time(warn)


func strike() -> void:
	phase = Phase.WARN
	_timer = telegraph()
	AudioManager.play_sfx(&"bolt_charge", -4.0)


func _on_room_entered(_id: String) -> void:
	_restart()


func _restart() -> void:
	phase = Phase.IDLE
	_timer = first
	if _sprite:
		_sprite.visible = false


func _physics_process(delta: float) -> void:
	_time += delta
	if not once and room_id != "" and Game.current_room != room_id:
		if phase != Phase.IDLE:
			_restart()
		_light.energy = 0.0
		queue_redraw()
		return
	_timer -= delta
	match phase:
		Phase.IDLE:
			if every > 0.0 and _timer <= 0.0:
				strike()
		Phase.WARN:
			_light.energy = 0.5 * (1.0 - _timer / telegraph())
			if _timer <= 0.0:
				_fire()
		Phase.STRIKE:
			_sprite.region_rect = Rect2(Vector2(FRAME_SIZE.x * (int(_time / 0.04) % FRAMES), FRAME_SIZE.y - height), Vector2(FRAME_SIZE.x, height))
			var target := Combat.find_player(self)
			if target and _hits(target):
				target.die()
			if _timer <= 0.0:
				phase = Phase.FADE
				_timer = FADE_TIME
				_sprite.visible = false
		Phase.FADE:
			_light.energy = 2.0 * _timer / FADE_TIME
			if _timer <= 0.0:
				if once:
					queue_free()
					return
				phase = Phase.IDLE
				_timer = maxf(0.3, every - telegraph() - STRIKE_TIME - FADE_TIME)
	queue_redraw()


func _fire() -> void:
	phase = Phase.STRIKE
	_timer = STRIKE_TIME
	height = minf(height, FRAME_SIZE.y)
	_sprite.position = Vector2(-FRAME_SIZE.x * 0.5, -height)
	_sprite.visible = true
	_light.energy = 2.2
	AudioManager.play_sfx(&"bolt", 0.0, 0.08)
	Storm.flash_screen(get_tree(), 0.45)
	Combat.burst(get_parent(), global_position + Vector2(0, -2), YELLOW, 10, 110.0)
	var camera := get_viewport().get_camera_2d()
	if camera and camera.has_method(&"shake"):
		camera.call(&"shake", 2.5, 0.25)


func _hits(player: Player) -> bool:
	for point in HIT_POINTS:
		var local := to_local(player.global_position + point)
		if absf(local.x) < half_width + HIT_RADIUS and local.y > -height - HIT_RADIUS and local.y < HIT_RADIUS:
			return true
	return false


func _draw() -> void:
	match phase:
		Phase.WARN:
			var progress := 1.0 - _timer / telegraph()
			if fmod(_time, 0.16) < 0.1:
				draw_dashed_line(Vector2(0, -height), Vector2.ZERO, Color(YELLOW, 0.3 + 0.6 * progress), 1.0, 4.0)
			var half := roundf(3.0 + 7.0 * progress)
			draw_rect(Rect2(-half, -2, half * 2.0, 2), Color(DEEP, 0.5 + 0.4 * progress))
			draw_rect(Rect2(-half + 2, -3, half * 2.0 - 4, 1), Color(YELLOW, 0.6 * progress))
			for i in 4:
				if fmod(_time * 7.0 + i * 0.37, 1.0) < progress:
					var spark := Vector2(roundf(sin(_time * 13.0 + i * 2.1) * half), -roundf(2.0 + fmod(_time * 31.0 + i * 5.0, 9.0)))
					draw_rect(Rect2(spark, Vector2.ONE), HOT)
		Phase.STRIKE:
			draw_rect(Rect2(-12, -4, 24, 4), HOT)
			draw_rect(Rect2(-8, -6, 16, 2), Color.WHITE)
		Phase.FADE:
			var fade := _timer / FADE_TIME
			draw_rect(Rect2(-10, -2, 20, 2), Color(DEEP, 0.8 * fade))
			draw_rect(Rect2(-5, -3, 10, 1), Color(YELLOW, 0.8 * fade))
