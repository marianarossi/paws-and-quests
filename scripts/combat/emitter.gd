class_name Emitter
extends Node2D

enum Phase { WAIT, WARN, FIRE }

const SHEET := "res://assets/sprites/combat/wisp.json"
const PRESETS := {
	&"aimed": {"count": 3, "gap": 0.22, "every": 2.4, "warn": 0.6, "speed": 120.0, "turn": 0.0, "homing": 0.0, "life": 4.0},
	&"burst": {"count": 3, "gap": 0.16, "every": 3.2, "warn": 0.7, "speed": 135.0, "turn": 0.0, "homing": 0.0, "life": 3.5},
	&"fan": {"count": 5, "arc": 70.0, "every": 2.8, "warn": 0.7, "speed": 105.0, "turn": 0.0, "life": 4.0},
	&"spiral": {"count": 14, "gap": 0.11, "spin": 26.0, "every": 4.0, "warn": 0.8, "speed": 80.0, "turn": 0.0, "life": 4.5},
	&"accel": {"count": 1, "every": 2.6, "warn": 0.8, "speed": 30.0, "accel": 340.0, "max": 330.0, "turn": 0.0, "life": 3.0},
}
const AIM_LINE_LENGTH := 150.0
const LEASH := 96.0
const WAKE_DELAY := 0.25
const GLOW := Color(1.0, 0.4, 0.75)

var pattern: StringName = &"aimed"
var count := 1
var gap := 0.15
var every := 2.4
var warn := 0.6
var first := 1.0
var arc := 70.0
var spin := 26.0
var angle := NAN
var reach := 0.0
var reach_y := 240.0
var shot := ShotSpec.new()
var room_id := ""

var phase := Phase.WAIT
var shots_fired := 0

var _timer := 0.0
var _fired := 0
var _aim := Vector2.RIGHT
var _time := 0.0
var _awake := false
var _since_restart := 0.0
var _sprite: AnimatedSprite2D
var _light: PointLight2D


static func create(def: Dictionary, center: Vector2, in_room: String) -> Emitter:
	var emitter := Emitter.new()
	emitter.position = center
	emitter.room_id = in_room
	emitter.pattern = StringName(def.get("pattern", "aimed"))
	assert(PRESETS.has(emitter.pattern), "padrão de emissor desconhecido: %s" % emitter.pattern)
	var params: Dictionary = PRESETS[emitter.pattern].duplicate()
	params.merge(def, true)
	emitter.count = int(params.get("count", 1))
	emitter.gap = float(params.get("gap", 0.15))
	emitter.every = float(params.get("every", 2.4))
	emitter.warn = float(params.get("warn", 0.6))
	emitter.first = float(params.get("first", 1.0))
	emitter.arc = float(params.get("arc", 70.0))
	emitter.spin = float(params.get("spin", 26.0))
	emitter.reach = float(params.get("reach", 0.0))
	emitter.reach_y = float(params.get("reach_y", emitter.reach_y))
	if params.has("angle"):
		emitter.angle = float(params["angle"])
	emitter.shot = ShotSpec.from_def(params)
	return emitter


func _ready() -> void:
	z_index = 8
	material = Lights.unshaded()
	_sprite = AnimatedSprite2D.new()
	_sprite.sprite_frames = SpriteSheet.frames(SHEET)
	_sprite.material = Lights.unshaded()
	_sprite.play(&"idle")
	add_child(_sprite)
	_light = Lights.point(GLOW, 40.0, 0.0)
	add_child(_light)
	_time = position.x * 0.07
	_restart()
	Events.player_respawned.connect(_restart)
	Events.room_entered.connect(_on_room_entered)


func telegraph() -> float:
	return Combat.telegraph_time(warn)


func _on_room_entered(_id: String) -> void:
	_restart()


func _restart() -> void:
	phase = Phase.WAIT
	_timer = first
	_fired = 0
	_awake = false
	_since_restart = 0.0
	if _sprite:
		_sprite.play(&"idle")


func _physics_process(delta: float) -> void:
	_time += delta
	_since_restart += delta
	_sprite.position.y = roundf(sin(_time * 2.2) * 2.0)
	var target := _target()
	if target == null:
		if _awake:
			_pause()
		_light.energy = move_toward(_light.energy, 0.0, delta * 4.0)
		queue_redraw()
		return
	if not _awake:
		_wake()
	_timer -= delta
	match phase:
		Phase.WAIT:
			_light.energy = move_toward(_light.energy, 0.0, delta * 3.0)
			if _sprite.animation != &"idle" and not _sprite.is_playing():
				_sprite.play(&"idle")
			if _timer <= 0.0:
				phase = Phase.WARN
				_timer = telegraph()
				_sprite.play(&"charge", 4.0 / (8.0 * telegraph()))
				AudioManager.play_sfx(&"charge", -6.0)
		Phase.WARN:
			_aim = _aim_direction(target)
			_light.energy = 1.2 * (1.0 - _timer / telegraph())
			if _timer <= 0.0:
				phase = Phase.FIRE
				_fired = 0
				_timer = 0.0
		Phase.FIRE:
			while phase == Phase.FIRE and _timer <= 0.0:
				_fire_step(target)
	queue_redraw()


func _wake() -> void:
	_awake = true
	if phase == Phase.WAIT:
		_timer = minf(_timer, maxf(WAKE_DELAY, first - _since_restart))


func _pause() -> void:
	_awake = false
	if phase != Phase.WAIT:
		phase = Phase.WAIT
		_timer = WAKE_DELAY
		_fired = 0


func _target() -> Player:
	if room_id != "" and Game.current_room != room_id:
		return null
	var player := Combat.find_player(self)
	if player and reach > 0.0:
		var extra := LEASH if _awake else 0.0
		var d := player.global_position - global_position
		if absf(d.x) > reach + extra or absf(d.y) > reach_y + extra:
			return null
	return player


func _aim_direction(target: Player) -> Vector2:
	if not is_nan(angle):
		return Vector2.from_angle(deg_to_rad(angle))
	return (Combat.aim_point(target) - global_position).normalized()


func _fire_step(target: Player) -> void:
	var pool := ProjectilePool.of(self)
	match pattern:
		&"fan":
			for i in count:
				var t := 0.0 if count == 1 else float(i) / (count - 1) - 0.5
				_shoot(pool, _aim.rotated(deg_to_rad(arc * t)), target)
			_fired = count
		&"spiral":
			_shoot(pool, _aim.rotated(deg_to_rad(spin * _fired)), target)
			_fired += 1
		_:
			_shoot(pool, _aim_direction(target), target)
			_fired += 1
	_sprite.play(&"fire")
	_light.energy = 1.6
	AudioManager.play_sfx(&"shot", -5.0, 0.08)
	if _fired >= count:
		phase = Phase.WAIT
		_timer = every
	else:
		_timer += gap


func _shoot(pool: ProjectilePool, direction: Vector2, target: Player) -> void:
	if pool.spawn(global_position + direction * 8.0, direction, shot, target):
		shots_fired += 1


func _draw() -> void:
	if phase != Phase.WARN:
		return
	var progress := 1.0 - _timer / telegraph()
	var color := Color(Combat.PINK, 0.25 + 0.75 * progress)
	match pattern:
		&"fan":
			for t: float in [-0.5, 0.0, 0.5]:
				_draw_aim(_aim.rotated(deg_to_rad(arc * t)), color, AIM_LINE_LENGTH * 0.7)
		&"spiral":
			for i in 10:
				var dot := _aim.rotated(deg_to_rad(spin * i)) * (12.0 + 2.0 * i)
				if float(i) / 10.0 <= progress:
					draw_rect(Rect2(dot.round() - Vector2.ONE, Vector2(2, 2)), color)
		_:
			_draw_aim(_aim, color, AIM_LINE_LENGTH)


func _draw_aim(direction: Vector2, color: Color, length: float) -> void:
	var step := 6.0
	var offset := fmod(_time * 30.0, step)
	var at := 10.0 + offset
	while at < length:
		var fade := 1.0 - at / length
		draw_rect(Rect2((direction * at).round() - Vector2.ONE, Vector2(2, 2)), Color(color, color.a * fade))
		at += step
