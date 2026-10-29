class_name Beam
extends Node2D

enum Phase { OFF, WARN, ON }

const SHEET := "res://assets/sprites/combat/wisp.json"
const HALF_WIDTH := 2.5
const HIT_POINTS: Array[Vector2] = [Vector2(0, -6), Vector2(0, -16)]
const HIT_RADIUS := 3.0

var from_angle := 60.0
var to_angle := 120.0
var on := 1.6
var off := 1.6
var warn := 0.7
var first := 1.0
var length := 480.0
var room_id := ""

var phase := Phase.OFF

var _timer := 0.0
var _time := 0.0
var _forward := true
var _angle := 0.0
var _end := Vector2.ZERO
var _buzz := 0.0
var _sprite: AnimatedSprite2D
var _light: PointLight2D


static func create(def: Dictionary, center: Vector2, in_room: String) -> Beam:
	var beam := Beam.new()
	beam.position = center
	beam.room_id = in_room
	beam.from_angle = float(def.get("from", beam.from_angle))
	beam.to_angle = float(def.get("to", beam.to_angle))
	beam.on = float(def.get("on", beam.on))
	beam.off = float(def.get("off", beam.off))
	beam.warn = float(def.get("warn", beam.warn))
	beam.first = float(def.get("first", beam.first))
	beam.length = float(def.get("length", beam.length))
	return beam


func _ready() -> void:
	z_index = 8
	material = Lights.unshaded()
	_sprite = AnimatedSprite2D.new()
	_sprite.sprite_frames = SpriteSheet.frames(SHEET)
	_sprite.material = Lights.unshaded()
	_sprite.play(&"idle")
	add_child(_sprite)
	_light = Lights.point(Emitter.GLOW, 48.0, 0.0)
	add_child(_light)
	_restart()
	Events.player_respawned.connect(_restart)
	Events.room_entered.connect(_on_room_entered)


func telegraph() -> float:
	return Combat.telegraph_time(warn)


func _on_room_entered(_id: String) -> void:
	_restart()


func _restart() -> void:
	phase = Phase.OFF
	_timer = first
	_forward = true
	if _sprite:
		_sprite.play(&"idle")


func _physics_process(delta: float) -> void:
	_time += delta
	var target: Player = null
	if room_id == "" or Game.current_room == room_id:
		target = Combat.find_player(self)
	if target == null:
		if phase != Phase.OFF or _timer < first:
			_restart()
		_light.energy = move_toward(_light.energy, 0.0, delta * 4.0)
		queue_redraw()
		return
	_timer -= delta
	var start := from_angle if _forward else to_angle
	var finish := to_angle if _forward else from_angle
	match phase:
		Phase.OFF:
			_light.energy = move_toward(_light.energy, 0.0, delta * 3.0)
			if _timer <= 0.0:
				phase = Phase.WARN
				_timer = telegraph()
				_angle = start
				_sprite.play(&"charge", 4.0 / (8.0 * telegraph()))
				AudioManager.play_sfx(&"beam_charge", -5.0)
		Phase.WARN:
			_angle = start
			_end = _cast(_angle)
			_light.energy = 1.2 * (1.0 - _timer / telegraph())
			if _timer <= 0.0:
				phase = Phase.ON
				_timer = on
				_buzz = 0.0
				_sprite.play(&"fire")
		Phase.ON:
			_angle = lerpf(start, finish, clampf(1.0 - _timer / on, 0.0, 1.0))
			_end = _cast(_angle)
			_light.energy = 1.6
			_buzz -= delta
			if _buzz <= 0.0:
				_buzz = 0.42
				AudioManager.play_sfx(&"beam", -7.0, 0.02)
			if _hits(target):
				target.die()
			if _timer <= 0.0:
				phase = Phase.OFF
				_timer = off
				_forward = not _forward
				_sprite.play(&"idle")
	queue_redraw()


func _cast(angle_deg: float) -> Vector2:
	var direction := Vector2.from_angle(deg_to_rad(angle_deg))
	var query := PhysicsRayQueryParameters2D.create(global_position, global_position + direction * length, Combat.WORLD_LAYER)
	var hit := get_world_2d().direct_space_state.intersect_ray(query)
	return to_local(hit["position"]) if hit else direction * length


func _hits(player: Player) -> bool:
	for point in HIT_POINTS:
		var local := to_local(player.global_position + point)
		var nearest := Geometry2D.get_closest_point_to_segment(local, Vector2.ZERO, _end)
		if local.distance_to(nearest) < HALF_WIDTH + HIT_RADIUS:
			return true
	return false


func _draw() -> void:
	match phase:
		Phase.WARN:
			var progress := 1.0 - _timer / telegraph()
			if fmod(_time, 0.16) < 0.1:
				draw_dashed_line(Vector2.ZERO, _end, Color(Combat.PINK, 0.35 + 0.65 * progress), 1.0, 4.0)
			var start := from_angle if _forward else to_angle
			var finish := to_angle if _forward else from_angle
			for i in 8:
				if float(i) / 8.0 > progress:
					break
				var dot := Vector2.from_angle(deg_to_rad(lerpf(start, finish, float(i) / 7.0))) * 22.0
				draw_rect(Rect2(dot.round() - Vector2.ONE, Vector2(2, 2)), Color(Combat.HOT, 0.9))
		Phase.ON:
			var flicker := 1.0 if fmod(_time, 0.08) < 0.04 else 0.0
			draw_line(Vector2.ZERO, _end, Color(Combat.MAGENTA, 0.75), 7.0 + flicker)
			draw_line(Vector2.ZERO, _end, Combat.PINK, 4.0)
			draw_line(Vector2.ZERO, _end, Color.WHITE, 2.0 - flicker)
			draw_rect(Rect2(_end.round() - Vector2(3, 3), Vector2(6, 6)), Combat.HOT)
