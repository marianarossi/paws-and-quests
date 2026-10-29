class_name ThroneFight
extends Node2D

enum Stage { WAITING, APPROACH, HOLD, CHASE, SEEK, ENDING, DONE }

const GROUP := &"throne_fight"

const THROWS := 6
const PER_PHASE := 2
const NOTICE := 96.0
const THROW_SHORT := Vector2(120, -170)
const THROW_LONG := Vector2(310, -240)
const THROW_UP_SHORT := Vector2(45, -270)
const THROW_UP_LONG := Vector2(110, -380)
const CHARGE_TIME := 0.8
const THROW_FROM := Vector2(4, -22)
const RUN := 175.0
const TRAIL_EVERY: Array[float] = [0.6, 0.45, 0.35]
const ATTACK_EVERY: Array[float] = [1.9, 1.55, 1.25]
const STRIKE_WARN := 0.75
const LEAD := 0.85
const LEAD_MAX := 90.0
const APPROACH_EVERY := 1.25
const CHAIN := 3
const CHAIN_GAP := 0.24
const STRAY_EVERY: Array[float] = [3.0, 2.5, 2.0]
const HOLD_GRACE := 3.0
const STRAY_SPREAD := 28.0
const WAVE_WARN := 0.5
const SPARKS := 5
const CHARGE_EVERY: Array[int] = [3, 2, 2]
const FAR_SPARKS: Array[int] = [1, 2, 3]
const FAR := 150.0
const CHARGE_WARN := 0.55
const CHARGE_PAST := 36.0
const CHARGE_SPEED := 215.0
const LOOP_DB := -6.0
const OBSTACLE_LEAP := 66.0
const LAUNCH_GAP := 44.0
const UP_LEAP := 28.0
const SPOT_CLEAR := 56.0
const EDGE_GAP := 32.0
const SPARK_COLORS: Array[Color] = [Color("#fff4c0"), Color("#c88a10"), Color("#ffcc33")]
const BUDDY_WOOF := Color("ffd9a8")
const BOLT_GAP := 26.0
const PET_GAP := 21.0
const LIE_GAP := 17.0
const HEART: Array[String] = [".oo.oo.", "ohpoppo", "opppppo", ".opppo.", "..opo..", "...o..."]
const HEART_COLORS := {"o": Color("421d2e"), "p": Color("ff7a8a"), "h": Color("ffd1dc")}

var room_id := ""
var stage := Stage.WAITING
var energy := THROWS
var bolt: BoltDog
var ball: FetchBall
var buddy: DogNpc
var home := Vector2.ZERO

var _spots: Array = [[], [], []]
var _zoom_x := Vector2(12, 25)
var _world: World
var _room: Node2D
var _room_node: Room
var _bounds := Rect2()
var _ball_start := Vector2.ZERO
var _gen := 0
var _noticed := false
var _started := false
var _attack_timer := 0.0
var _hold_time := 0.0
var _stray_timer := 2.5
var _attack_count := 0
var _trail_on := false
var _trail_timer := 0.0
var _hint: Hint
var _auto := false
var _auto_timer := 0.0
var _power := -1.0
var _auto_power := 0.5
var _dev_intro := false
var _charging := false
var _drums: AudioStreamPlayer


static func create(def: Dictionary, feet: Vector2, in_room: String) -> ThroneFight:
	var fight := ThroneFight.new()
	fight.position = feet
	fight.room_id = in_room
	for phase in 3:
		var list := String(def.get("spots%d" % (phase + 1), ""))
		for item in list.split(";", false):
			var cell := RoomData.to_vector(item)
			fight._spots[phase].append(Vector2(cell.x * Room.TILE + Room.TILE * 0.5, (cell.y + 1) * Room.TILE - FetchBall.RADIUS))
	if def.has("zoom"):
		fight._zoom_x = RoomData.to_vector(String(def["zoom"]))
	return fight


func _ready() -> void:
	add_to_group(GROUP)
	_auto = OS.get_cmdline_user_args().has("--fight-auto")
	z_index = 20
	material = Lights.unshaded()
	_setup.call_deferred()


func _setup() -> void:
	var up := get_parent()
	while up and not up is Room:
		up = up.get_parent()
	_room_node = up as Room
	_room = get_parent() as Node2D
	_bounds = _room_node.bounds
	home = global_position
	bolt = BoltDog.new()
	bolt.rest_anim = &"lie"
	bolt.facing = 1
	_room.add_child(bolt)
	bolt.global_position = home
	for node in _room.get_children():
		if node is FetchBall:
			ball = node
		elif node is DogNpc and (node as DogNpc).sheet == "dog":
			buddy = node
	if ball == null:
		ball = FetchBall.create(Vector2.ZERO)
		_room.add_child(ball)
		ball.global_position = home + Vector2(-120, -FetchBall.RADIUS)
	ball.bounds = _bounds
	_ball_start = ball.global_position.round()
	Events.player_respawned.connect(_on_respawned)
	if Game.finished:
		_finished_already()
		return
	for arg in OS.get_cmdline_user_args():
		if arg == "--fight-end":
			await get_tree().physics_frame
			await get_tree().physics_frame
			skip()
		elif arg.begins_with("--fight="):
			await get_tree().physics_frame
			await get_tree().physics_frame
			var number := int(arg.get_slice("=", 1))
			if number == 0:
				_dev_intro = true
				await get_tree().create_timer(1.0).timeout
				var inside := _ground_under(Vector2(_bounds.position.x + 140.0, _bounds.position.y + 8.0))
				if inside != Vector2.INF and _player() and not _player().is_dead():
					_player().teleport(inside)
			else:
				_start_at_phase(clampi(number, 1, 3))


func _player() -> Player:
	return get_tree().get_first_node_in_group(Combat.PLAYER_GROUP) as Player


func _get_world() -> World:
	if _world == null:
		var player := _player()
		if player:
			_world = player.get_parent() as World
	return _world


func phase() -> int:
	@warning_ignore("integer_division")
	return clampi((THROWS - energy) / PER_PHASE, 0, 2)


func _physics_process(delta: float) -> void:
	if bolt == null or stage == Stage.DONE or stage == Stage.ENDING:
		return
	var player := _player()
	if player == null or player.is_dead() or Game.current_room != room_id:
		return
	player.dev_invincible = _auto or _dev_intro
	var inside := player.global_position.x > _bounds.position.x + NOTICE
	if _noticed and player.global_position.x < _bounds.position.x + 6.0:
		player.global_position.x = _bounds.position.x + 6.0
		player.velocity.x = maxf(player.velocity.x, 0.0)
	match stage:
		Stage.WAITING:
			if inside:
				_notice()
		Stage.APPROACH, Stage.SEEK:
			if not _charging:
				_attack_timer -= delta
				if _attack_timer <= 0.0:
					_attack_timer = APPROACH_EVERY if stage == Stage.APPROACH else ATTACK_EVERY[phase()]
					_attack()
			_stray_timer -= delta
			if _stray_timer <= 0.0:
				_stray_timer = STRAY_EVERY[phase()] * randf_range(0.8, 1.2)
				_stray_strike(player)
			if ball.state == FetchBall.State.REST and _touches(player):
				_take_ball()
			elif _auto and ball.state == FetchBall.State.REST:
				_auto_timer += delta
				if _auto_timer > 4.5:
					_auto_timer = 0.0
					player.teleport(ball.global_position + Vector2(0, FetchBall.RADIUS))
		Stage.HOLD:
			_update_power(player, delta)
			_hold_time += delta
			if _hold_time > HOLD_GRACE and stage == Stage.HOLD:
				_attack_timer -= delta
				if _attack_timer <= 0.0:
					_attack_timer = ATTACK_EVERY[phase()]
					var ground := _strike_target(player)
					if ground != Vector2.INF:
						bolt.show_anim(&"bark", 0.35)
						LightningStrike.spawn(_room, ground, STRIKE_WARN)
	if _trail_on:
		_trail_timer -= delta
		if _trail_timer <= 0.0 and bolt.is_on_floor() and absf(bolt.velocity.x) > 40.0:
			_trail_timer = TRAIL_EVERY[phase()]
			LightningStrike.spawn(_room, bolt.global_position, STRIKE_WARN)


func _update_power(player: Player, delta: float) -> void:
	if _auto:
		_auto_timer += delta
		player.facing = 1 if player.global_position.x < (_bounds.position.x + _bounds.end.x) * 0.5 else -1
		if _auto_timer > 0.3:
			_power = clampf((_auto_timer - 0.3) / CHARGE_TIME, 0.0, 1.0)
		if _power >= _auto_power:
			_throw()
		queue_redraw()
		return
	if not player.input_enabled:
		return
	if Input.is_action_just_pressed(&"grab"):
		_power = 0.0
	elif _power >= 0.0:
		_power = minf(_power + delta / CHARGE_TIME, 1.0)
		if not Input.is_action_pressed(&"grab"):
			_throw()
	queue_redraw()


func _throw_velocity(player: Player) -> Vector2:
	var power := clampf(_power, 0.0, 1.0)
	var up := Input.is_action_pressed(&"move_up")
	var vel := (THROW_UP_SHORT.lerp(THROW_UP_LONG, power) if up else THROW_SHORT.lerp(THROW_LONG, power))
	return Vector2(vel.x * player.facing + player.velocity.x * 0.3, vel.y)


func _draw() -> void:
	if stage != Stage.HOLD or _power < 0.0:
		return
	var player := _player()
	if player == null:
		return
	var space := get_world_2d().direct_space_state
	var point := player.global_position + Vector2(THROW_FROM.x * player.facing, THROW_FROM.y)
	var vel := _throw_velocity(player)
	var step := 1.0 / 60.0
	var dots := 0
	for i in 90:
		var next := point + vel * step
		vel.y = minf(vel.y + FetchBall.GRAVITY * step, FetchBall.MAX_FALL)
		var hit := space.intersect_ray(PhysicsRayQueryParameters2D.create(point, next, Combat.WORLD_LAYER))
		if not hit.is_empty() or not _bounds.grow(8).has_point(next):
			break
		point = next
		if i % 4 == 2:
			dots += 1
			var color := SPARK_COLORS[0] if dots % 2 == 0 else Color.WHITE
			color.a = 0.9 - minf(i / 90.0, 0.6)
			var dot := to_local(point).round() - Vector2.ONE
			draw_rect(Rect2(dot + Vector2.ONE, Vector2(2, 2)), Color(0.11, 0.08, 0.2, color.a * 0.8))
			draw_rect(Rect2(dot, Vector2(2, 2)), color)


func _touches(player: Player) -> bool:
	return ball.global_position.distance_to(player.global_position + Vector2(0, -8)) < 13.0


func _notice() -> void:
	stage = Stage.APPROACH
	_attack_timer = 1.8
	if _noticed:
		return
	_noticed = true
	var gen := _gen
	_log("deu por nos")
	bolt.rest_anim = &"idle"
	bolt.show_anim(&"sniff", 0.7)
	await get_tree().create_timer(0.6).timeout
	if gen != _gen:
		return
	bolt.face(-1)
	_bark()
	_get_world().camera.shake(1.5, 0.3)
	_boss_intro()
	await get_tree().create_timer(0.7).timeout
	if gen != _gen or buddy == null:
		return
	buddy.face(-1)
	buddy.play_anim(&"bark")
	WoofText.say(_room, buddy.global_position + Vector2(-4, -20), tr(&"INTRO_WOOF"), false, BUDDY_WOOF)
	await get_tree().create_timer(0.5).timeout
	if gen == _gen and buddy:
		buddy.play_anim(&"sit")


func _boss_intro() -> void:
	_get_world().boss_bar().intro(THROWS)
	AudioManager.play_sfx(&"boss_sting", 0.0, 0.0)
	Storm.flash_screen(get_tree(), 0.6)
	_get_world().camera.shake(3.0, 0.5)
	if _drums == null:
		_drums = AudioStreamPlayer.new()
		_drums.bus = AudioManager.BUS_MUSIC
		var stream := load(AudioManager.SFX_DIR + "boss_loop.ogg") as AudioStreamOggVorbis
		if stream:
			stream.loop = true
		_drums.stream = stream
		add_child(_drums)
	_drums.volume_db = LOOP_DB
	get_tree().create_timer(0.9).timeout.connect(func() -> void:
		if stage == Stage.APPROACH and _drums:
			_drums.play())


func _stop_drums() -> void:
	if _drums and _drums.playing:
		_drums.stop()


func _bark() -> void:
	bolt.show_anim(&"bark", 0.45)
	WoofText.say(_room, bolt.global_position + Vector2(0, -24), tr(&"INTRO_WOOF"))


func _attack() -> void:
	_attack_count += 1
	var player := _player()
	if stage == Stage.SEEK and bolt.is_on_floor():
		if _attack_count % CHARGE_EVERY[phase()] == 0:
			_charge()
			return
		if bolt.global_position.distance_to(player.global_position) > FAR and _attack_count % 2 == 1:
			_far_sparks(FAR_SPARKS[phase()])
			return
	if stage == Stage.APPROACH:
		if _attack_count % 3 == 0:
			_wave()
		else:
			_strike_chain(CHAIN)
		return
	var wave_turn := _attack_count % 2 == 0
	if phase() >= 1 and wave_turn:
		_wave()
		return
	var ground := _strike_target(player)
	if ground == Vector2.INF:
		return
	bolt.show_anim(&"bark", 0.35)
	LightningStrike.spawn(_room, ground, STRIKE_WARN)
	if phase() == 2:
		var here := _ground_under(player.global_position)
		if here != Vector2.INF and absf(here.x - ground.x) < 20.0:
			here = _ground_under(player.global_position + Vector2(randf_range(36.0, 52.0) * (1 if randf() < 0.5 else -1), 0))
		if here != Vector2.INF:
			LightningStrike.spawn(_room, here, STRIKE_WARN + 0.15)


func _strike_chain(count: int) -> void:
	var gen := _gen
	bolt.show_anim(&"bark", 0.35 + CHAIN_GAP * count)
	for i in count:
		var player := _player()
		if gen != _gen or player == null or player.is_dead():
			return
		var ground := _strike_target(player)
		if ground != Vector2.INF:
			LightningStrike.spawn(_room, ground, STRIKE_WARN)
		await get_tree().create_timer(CHAIN_GAP).timeout


func _stray_strike(player: Player) -> void:
	var near := _strike_target(player)
	if near == Vector2.INF:
		return
	var x := clampf(near.x + randf_range(-STRAY_SPREAD, STRAY_SPREAD), _bounds.position.x + 12.0, _bounds.end.x - 12.0)
	var ground := _ground_under(Vector2(x, player.global_position.y))
	if ground != Vector2.INF:
		LightningStrike.spawn(_room, ground, STRIKE_WARN)


func _strike_target(player: Player) -> Vector2:
	var ahead := clampf(player.velocity.x * STRIKE_WARN * LEAD, -LEAD_MAX, LEAD_MAX)
	var x := clampf(player.global_position.x + ahead, _bounds.position.x + 12.0, _bounds.end.x - 12.0)
	return _ground_under(Vector2(x, player.global_position.y))


func _charge() -> void:
	var gen := _gen
	_charging = true
	_log("investida")
	bolt.show_anim(&"sniff", CHARGE_WARN)
	AudioManager.play_sfx(&"snort", -4.0)
	_bark()
	await get_tree().create_timer(CHARGE_WARN).timeout
	if gen != _gen:
		return
	var player := _player()
	var dir := signf(player.global_position.x - bolt.global_position.x)
	if dir == 0.0:
		dir = -1.0
	var goal := clampf(player.global_position.x + dir * CHARGE_PAST, _bounds.position.x + 12.0, _bounds.end.x - 12.0)
	_trail_on = true
	_trail_timer = 0.15
	if not await bolt.run_to(goal, CHARGE_SPEED, 2.5) and gen == _gen:
		await _hop_over(goal)
		if gen == _gen:
			await bolt.run_to(goal, CHARGE_SPEED, 1.5)
	if gen != _gen:
		return
	_trail_on = false
	bolt.show_anim(&"pant", 0.5)
	await get_tree().create_timer(0.5).timeout
	if gen != _gen:
		return
	await _go_to(home, 0.0)
	if gen != _gen:
		return
	_charging = false
	_attack_timer = ATTACK_EVERY[phase()] * 0.6
	bolt.face(-1 if _player().global_position.x < bolt.global_position.x else 1)


func _far_sparks(count: int) -> void:
	var gen := _gen
	_log("faiscas de longe (%d)" % count)
	bolt.face(-1 if _player().global_position.x < bolt.global_position.x else 1)
	bolt.show_anim(&"bark", Combat.MIN_TELEGRAPH + 0.2)
	AudioManager.play_sfx(&"charge", -4.0)
	WoofText.say(_room, bolt.global_position + Vector2(0, -24), tr(&"INTRO_WOOF"))
	await get_tree().create_timer(maxf(Combat.MIN_TELEGRAPH, 0.6)).timeout
	if gen != _gen:
		return
	var player := _player()
	if player == null or player.is_dead():
		return
	var spec := ShotSpec.new()
	spec.speed = 85.0
	spec.max_speed = 150.0
	spec.accel = 30.0
	spec.turn_rate = 90.0
	spec.homing_time = 1.6
	spec.lifetime = 4.0
	var pool := ProjectilePool.of(self)
	var from := bolt.global_position + Vector2(0, -12)
	var aim := (player.global_position + Vector2(0, -8) - from).angle()
	for i in count:
		var spread := 0.0 if count == 1 else lerpf(-0.45, 0.45, float(i) / (count - 1))
		var spark := pool.spawn(from, Vector2.from_angle(aim + spread), spec, player)
		if spark:
			spark.use_colors(SPARK_COLORS[0], SPARK_COLORS[1], SPARK_COLORS[2])
	AudioManager.play_sfx(&"shot", -4.0)


func _wave() -> void:
	var gen := _gen
	_bark()
	await get_tree().create_timer(WAVE_WARN).timeout
	if gen != _gen or not bolt.is_on_floor() or _player().is_dead():
		return
	var dir := -1 if _player().global_position.x < bolt.global_position.x else 1
	BarkWave.spawn(_room, bolt.global_position + Vector2(dir * 8, 0), dir, _bounds, 130.0 + phase() * 15.0)


func _ground_under(point: Vector2) -> Vector2:
	var query := PhysicsRayQueryParameters2D.create(point + Vector2(0, -6), point + Vector2(0, 360), Combat.WORLD_LAYER)
	var hit := get_world_2d().direct_space_state.intersect_ray(query)
	return Vector2.INF if hit.is_empty() else (hit.position as Vector2).round()


func _take_ball() -> void:
	var player := _player()
	ball.hold(player, false)
	stage = Stage.HOLD
	_gen += 1
	_auto_timer = 0.0
	_hold_time = 0.0
	_attack_timer = 0.0
	_clear_hazards(false)
	_trail_on = false
	_charging = false
	_power = -1.0
	_stop_drums()
	bolt.stop()
	bolt.rest_anim = &"happy"
	bolt.face(-1 if player.global_position.x < bolt.global_position.x else 1)
	AudioManager.play_sfx(&"dash_refill", -6.0)
	if not _started:
		_started = true
		_log("comecou o jogo")
		_get_world().show_energy(THROWS, energy)
		_hint = Hint.create(player.global_position + Vector2(0, -10), "HINT_THROW_GRAB")
		_hint.forced = true
		_hint.follow = player
		_hint.follow_offset = Vector2(0, -10)
		_room.add_child(_hint)
		if buddy:
			buddy.play_anim(&"happy")


func _throw() -> void:
	var player := _player()
	var vel := _throw_velocity(player)
	ball.global_position = player.global_position + Vector2(THROW_FROM.x * player.facing, THROW_FROM.y)
	ball.throw(vel)
	AudioManager.play_sfx(&"swoop", -8.0 + 4.0 * clampf(_power, 0.0, 1.0), 0.1)
	_log("atirou com forca %.2f" % _power)
	_power = -1.0
	_auto_power = randf_range(0.2, 1.0)
	queue_redraw()
	if _hint:
		_hint.queue_free()
		_hint = null
	stage = Stage.CHASE
	_gen += 1
	_log("atirou (energia %d)" % energy)
	if _auto:
		var safe := _ground_under(Vector2(_bounds.position.x + 184.0, _bounds.position.y + 8.0))
		if safe != Vector2.INF:
			get_tree().create_timer(0.25).timeout.connect(func() -> void:
				if is_instance_valid(player) and not player.is_dead():
					player.teleport(safe))
	_chase()


func _chase() -> void:
	var gen := _gen
	bolt.rest_anim = &"idle"
	_trail_on = true
	_trail_timer = 0.3
	await get_tree().create_timer(0.15).timeout
	var time := 0.0
	while gen == _gen and not bolt.can_bite(ball):
		if ball.state == FetchBall.State.FLYING:
			bolt.target_x = ball.global_position.x
			bolt.speed = RUN
			await get_tree().physics_frame
		else:
			await _go_to(ball.global_position + Vector2(0, FetchBall.RADIUS), 8.0)
			if gen == _gen and not bolt.can_bite(ball):
				await get_tree().physics_frame
		time += get_physics_process_delta_time()
		if time > 12.0:
			bolt.global_position = ball.global_position + Vector2(0, FetchBall.RADIUS)
	if gen != _gen:
		return
	_trail_on = false
	bolt.stop()
	bolt.pick_up(ball)
	energy -= 1
	_get_world().show_energy(THROWS, energy)
	AudioManager.play_sfx(&"snap", -4.0)
	_log("apanhou (energia %d)" % energy)
	if buddy:
		buddy.play_anim(&"happy")
	if energy <= 0:
		_ending()
		return
	if phase() >= 1:
		await _shake_off(gen)
	if phase() == 2 and gen == _gen:
		await _zoomies(gen)
	if gen != _gen:
		return
	var player := _player()
	var spots: Array = _spots[phase()]
	var first := (THROWS - energy - 1) % PER_PHASE
	var spot: Vector2 = _room.to_global(spots[first % spots.size()])
	for k in spots.size():
		var point := _room.to_global(spots[(first + k) % spots.size()])
		if point.distance_to(player.global_position) > SPOT_CLEAR:
			spot = point
			break
	_log("vai largar (sitio %s)" % (_room.to_local(spot) / Room.TILE).floor())
	if phase() >= 1:
		_trail_on = true
		_trail_timer = 0.3
	await _go_to(spot + Vector2(0, FetchBall.RADIUS), 12.0)
	_trail_on = false
	if gen != _gen:
		return
	bolt.face(-1 if player.global_position.x < bolt.global_position.x else 1)
	bolt.drop()
	if bolt.global_position.distance_to(spot) < 24.0:
		ball.place(spot)
	_log("largou em %s (sitio %s)" % [(_room.to_local(ball.global_position) / Room.TILE).floor(), (_room.to_local(spot) / Room.TILE).floor()])
	_bark()
	if buddy:
		buddy.play_anim(&"sit")
	await get_tree().create_timer(0.5).timeout
	if gen != _gen:
		return
	stage = Stage.SEEK
	_attack_timer = 1.4
	await _go_to(home, 0.0)
	if gen == _gen:
		bolt.face(-1 if _player().global_position.x < bolt.global_position.x else 1)
		bolt.rest_anim = &"pant"


func _go_to(feet: Vector2, side_gap: float) -> void:
	var gen := _gen
	for attempt in 4:
		if gen != _gen:
			return
		var side := signf(bolt.global_position.x - feet.x)
		if side == 0.0:
			side = 1.0
		var target := Vector2(feet.x + side * side_gap, feet.y)
		if absf(bolt.global_position.y - feet.y) < 6.0 and bolt.is_on_floor():
			if await bolt.run_to(target.x, RUN):
				return
			await _hop_over(target.x)
		elif feet.y < bolt.global_position.y - 6.0:
			var launch := feet.x + side * (side_gap + LAUNCH_GAP)
			var edge := _ledge_edge(feet, side) + side * EDGE_GAP
			launch = maxf(launch, edge) if side > 0.0 else minf(launch, edge)
			launch = clampf(launch, _bounds.position.x + 10.0, _bounds.end.x - 10.0)
			if not await bolt.run_to(launch, RUN, 2.5):
				await _hop_over(launch)
				continue
			if gen != _gen:
				return
			if await bolt.leap_to(target, UP_LEAP):
				return
		else:
			if await bolt.leap_to(target, 10.0):
				return
		if gen == _gen and bolt.global_position.distance_to(target) < 12.0:
			return
	if gen == _gen:
		_log("  nao chegou: salto direto")
		await bolt.leap_to(feet, OBSTACLE_LEAP)


func _ledge_edge(feet: Vector2, side: float) -> float:
	var space := get_world_2d().direct_space_state
	var x := feet.x
	for i in 40:
		var probe := PhysicsRayQueryParameters2D.create(Vector2(x + side * 4.0, feet.y - 2.0), Vector2(x + side * 4.0, feet.y + 12.0), Combat.WORLD_LAYER)
		if space.intersect_ray(probe).is_empty():
			break
		x += side * 4.0
	return x

func _hop_over(toward_x: float) -> void:
	var gen := _gen
	var dir := signf(toward_x - bolt.global_position.x)
	if dir == 0.0:
		return
	await bolt.run_to(bolt.global_position.x - dir * 40.0, RUN, 0.8)
	if gen != _gen:
		return
	var land := clampf(bolt.global_position.x + dir * 100.0, _bounds.position.x + 10.0, _bounds.end.x - 10.0)
	if dir > 0.0:
		land = minf(land, maxf(toward_x, bolt.global_position.x + 80.0))
	else:
		land = maxf(land, minf(toward_x, bolt.global_position.x - 80.0))
	await bolt.leap_to(Vector2(land, bolt.global_position.y), OBSTACLE_LEAP)


func _shake_off(gen: int) -> void:
	bolt.show_anim(&"happy", 0.5)
	await get_tree().create_timer(0.45).timeout
	if gen != _gen or _player().is_dead():
		return
	var spec := ShotSpec.new()
	spec.speed = 95.0
	spec.turn_rate = 0.0
	spec.lifetime = 2.4
	var pool := ProjectilePool.of(self)
	var aim := (_player().global_position + Vector2(0, -8) - (bolt.global_position + Vector2(0, -10))).angle()
	for i in SPARKS:
		var angle := aim + deg_to_rad(lerpf(-50.0, 50.0, float(i) / (SPARKS - 1)))
		var spark := pool.spawn(bolt.global_position + Vector2(0, -10), Vector2.from_angle(angle), spec, null)
		if spark:
			spark.use_colors(SPARK_COLORS[0], SPARK_COLORS[1], SPARK_COLORS[2])
	AudioManager.play_sfx(&"spark_pop", -2.0)


func _zoomies(gen: int) -> void:
	_trail_on = true
	var left := _room.to_global(Vector2(_zoom_x.x * Room.TILE + Room.TILE * 0.5, 0)).x
	var right := _room.to_global(Vector2(_zoom_x.y * Room.TILE + Room.TILE * 0.5, 0)).x
	_log("zoomies")
	for lap in 2:
		for x in [left, right]:
			if gen != _gen:
				return
			if not await bolt.run_to(x, 230.0, 3.0) and gen == _gen:
				await _hop_over(x)
				if gen == _gen:
					await bolt.run_to(x, 230.0, 2.0)
	_trail_on = false
	_log("zoomies: fim")


func _on_respawned() -> void:
	if bolt == null or stage == Stage.WAITING or stage == Stage.ENDING or stage == Stage.DONE:
		return
	_gen += 1
	_clear_hazards(true)
	_trail_on = false
	_charging = false
	_power = -1.0
	queue_redraw()
	if _hint:
		_hint.queue_free()
		_hint = null
	bolt.stop()
	bolt.carried = null
	bolt.velocity = Vector2.ZERO
	bolt.global_position = home
	bolt.face(-1)
	bolt.rest_anim = &"idle"
	_attack_timer = 1.8
	_stray_timer = 2.5
	if not _started:
		ball.place(_ball_start)
		stage = Stage.APPROACH
		return
	energy = THROWS - phase() * PER_PHASE
	_get_world().show_energy(THROWS, energy)
	_place_ball_at_entrance()
	stage = Stage.SEEK
	_log("renasceu: fase %d" % (phase() + 1))


func _place_ball_at_entrance() -> void:
	var x := _room.to_global(Vector2(7 * Room.TILE + Room.TILE * 0.5, 0)).x
	var ground := _ground_under(Vector2(x, _bounds.position.y + 8.0))
	if ground == Vector2.INF:
		ground = Vector2(x, home.y + 3 * Room.TILE)
	ball.place(ground + Vector2(0, -FetchBall.RADIUS))


func _clear_hazards(sparks: bool) -> void:
	for node in _room.get_children():
		if (node is LightningStrike and (node as LightningStrike).once) or node is BarkWave:
			node.queue_free()
	if sparks:
		ProjectilePool.of(self).clear()


func can_skip() -> bool:
	return bolt != null and stage != Stage.ENDING and stage != Stage.DONE


func skip() -> void:
	if not can_skip():
		return
	_start_at_phase(3)
	stage = Stage.ENDING
	_charging = false
	_power = -1.0
	if _hint:
		_hint.queue_free()
		_hint = null
	bolt.stop()
	bolt.carried = null
	ball.place(home + Vector2(-20, -FetchBall.RADIUS))
	var spot := _ground_under(Vector2(_bounds.position.x + 200.0, _bounds.position.y + 8.0))
	if spot != Vector2.INF and _player() and not _player().is_dead():
		_player().teleport(spot)
	await get_tree().create_timer(0.5).timeout
	_log("so o final")
	_ending()


func _start_at_phase(number: int) -> void:
	_noticed = true
	_started = true
	energy = THROWS - (number - 1) * PER_PHASE
	bolt.rest_anim = &"pant"
	bolt.face(-1)
	if buddy:
		buddy.play_anim(&"sit")
	_get_world().show_energy(THROWS, energy)
	_place_ball_at_entrance()
	stage = Stage.SEEK
	_attack_timer = 2.0


func _ending() -> void:
	stage = Stage.ENDING
	_gen += 1
	var gen := _gen
	_trail_on = false
	_charging = false
	_stop_drums()
	_clear_hazards(true)
	_log("fim da luta")
	var world := _get_world()
	world.show_energy(0, 0)
	for storm in get_tree().get_nodes_in_group(Storm.GROUP):
		(storm as Storm).every_min = 99999.0
		(storm as Storm).every_max = 99999.0
	var player := _player()
	player.input_enabled = false
	var time := 0.0
	while not player.is_on_floor() and time < 3.0:
		await get_tree().physics_frame
		time += get_physics_process_delta_time()
	var side := 1.0 if bolt.global_position.x > player.global_position.x else -1.0
	if not _floor_at(player.global_position + Vector2(side * (BOLT_GAP + PET_GAP), 0)):
		side = -side
		if not _floor_at(player.global_position + Vector2(side * (BOLT_GAP + PET_GAP), 0)):
			side = -side
	var beside := Vector2(player.global_position.x + side * BOLT_GAP, player.global_position.y)
	await _go_to(beside, 0.0)
	bolt.face(int(-side))
	player.facing = int(side)
	bolt.drop()
	bolt.rest_anim = &"pant"
	await get_tree().create_timer(1.2).timeout
	bolt.rest_anim = &"lie"
	await get_tree().create_timer(1.0).timeout
	bolt.rest_anim = &"sleep"
	_snore(gen, bolt)
	await get_tree().create_timer(0.8).timeout
	if buddy == null:
		await _end_card(world, player, side, 2.0)
		return
	var buddy_spot := Vector2(player.global_position.x - side * PET_GAP, player.global_position.y)
	var lie_spot := Vector2(bolt.global_position.x + side * LIE_GAP, bolt.global_position.y)
	var by_player := _floor_at(buddy_spot)
	var lie_ok := _floor_at(lie_spot) and absf(lie_spot.y - player.global_position.y) < 3.0
	if not by_player:
		if not lie_ok:
			_log("sem chao para o cachorro: dorme no trono")
			buddy.play_anim(&"lie")
			await get_tree().create_timer(0.7).timeout
			buddy.play_anim(&"sleep")
			_snore(gen, buddy, 0.65)
			await _end_card(world, player, side, 2.6)
			return
		buddy_spot = lie_spot
	buddy.play_anim(&"idle")
	await get_tree().create_timer(0.3).timeout
	await buddy.jump_to(buddy_spot, 30.0, 0.8)
	buddy.face(1 if player.global_position.x > buddy.global_position.x else -1)
	buddy.play_anim(&"happy")
	WoofText.say(_room, buddy.global_position + Vector2(0, -20), tr(&"INTRO_WOOF"), false, BUDDY_WOOF)
	await get_tree().create_timer(0.7).timeout
	player.facing = 1 if buddy.global_position.x > player.global_position.x else -1
	player.pose = &"crouch"
	_log("festas")
	for i in 3:
		_heart(buddy.global_position + Vector2(buddy.facing * 3 + (i - 1) * 4, -22))
		await get_tree().create_timer(0.6).timeout
	await get_tree().create_timer(0.4).timeout
	player.pose = &""
	await get_tree().create_timer(0.3).timeout
	if by_player and lie_ok:
		await buddy.run_to(lie_spot.x, 70.0, &"walk")
	buddy.face(int(-side))
	buddy.play_anim(&"sniff")
	await get_tree().create_timer(1.0).timeout
	buddy.play_anim(&"lie")
	await get_tree().create_timer(0.7).timeout
	buddy.play_anim(&"sleep")
	_snore(gen, buddy, 0.65)
	await _end_card(world, player, side, 2.6)


func _end_card(world: World, player: Player, side: float, wait: float) -> void:
	player.facing = int(side)
	player.pose = &"sit"
	_warm_light()
	await get_tree().create_timer(wait).timeout
	stage = Stage.DONE
	_log("cartao de fim (o cartao aparece 3,8 s depois)")
	world.end_game()


func _snore(gen: int, dog: Node2D, delay := 0.0) -> void:
	if delay > 0.0:
		await get_tree().create_timer(delay).timeout
	while gen == _gen and is_inside_tree() and is_instance_valid(dog):
		WoofText.say(_room, dog.global_position + Vector2(6, -16), tr(&"FIGHT_ZZZ"), false, Color("d8e4ff"), 1.6)
		await get_tree().create_timer(1.3).timeout


func _floor_at(feet: Vector2) -> bool:
	if feet.x < _bounds.position.x + 12.0 or feet.x > _bounds.end.x - 12.0:
		return false
	var ground := _ground_under(feet)
	return ground != Vector2.INF and absf(ground.y - feet.y) < 3.0


func _heart(at: Vector2) -> void:
	var heart := Node2D.new()
	heart.z_index = 30
	heart.material = Lights.unshaded()
	heart.draw.connect(func() -> void:
		for y in HEART.size():
			var row: String = HEART[y]
			for x in row.length():
				var c := row[x]
				if c != ".":
					heart.draw_rect(Rect2(x - 3, y - 6, 1, 1), HEART_COLORS[c]))
	_room.add_child(heart)
	var from := at.round()
	heart.global_position = from
	var tween := heart.create_tween().set_parallel()
	tween.tween_method(func(t: float) -> void: heart.global_position = (from + Vector2(0, -10.0 * t)).round(), 0.0, 1.0, 0.9)
	tween.tween_property(heart, "modulate:a", 0.0, 0.35).set_delay(0.55)
	tween.chain().tween_callback(heart.queue_free)


func _warm_light() -> void:
	var modulate_node := _get_world().get_node_or_null(^"CanvasModulate") as CanvasModulate
	if modulate_node:
		var warm := modulate_node.color.lerp(Color(1.0, 0.9, 0.82), 0.45)
		create_tween().tween_property(modulate_node, "color", warm, 2.5)


func _finished_already() -> void:
	stage = Stage.DONE
	bolt.rest_anim = &"sleep"
	ball.place(home + Vector2(-20, -FetchBall.RADIUS))


func _log(step: String) -> void:
	if _auto or OS.get_cmdline_user_args().has("--intro-auto"):
		print("luta: %s aos %.2f s" % [step, Time.get_ticks_msec() / 1000.0])
