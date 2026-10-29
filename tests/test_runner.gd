extends Node

const PLAYER_SCENE := preload("res://scenes/player/player.tscn")
const ACTIONS: Array[StringName] = [&"move_left", &"move_right", &"move_up", &"move_down", &"jump", &"dash", &"grab"]
const TILE := 16.0
const TEST_SETTINGS := "user://test_settings.cfg"

var _world: Node2D
var _failures := 0
var _last_jump: StringName


func _ready() -> void:
	DirAccess.remove_absolute(ProjectSettings.globalize_path(TEST_SETTINGS))
	Settings.use_file(TEST_SETTINGS)
	await _ticks(2)
	Game.unlock_all()
	await _test_jump_heights()
	await _test_run_and_jump_distance()
	await _test_dash()
	await _test_coyote()
	await _test_wall_jump()
	await _test_single_wall()
	await _test_hazards()
	await _test_projectiles()
	await _test_enemies()
	await _test_bestiary()
	await _test_water_and_rest()
	await _test_gift_and_hint()
	_test_save()
	await _test_world()
	await _test_menu()
	_test_language()
	await _test_character()
	await _test_assist_and_chapters()
	await _test_end_results()
	await _test_intro(false)
	await _test_intro(true)
	await _test_fight()
	await _test_olympus()
	_test_rooms()
	_test_enemy_sheets()
	print("\n%s (%d falha(s))" % ["TESTES OK" if _failures == 0 else "TESTES FALHARAM", _failures])
	get_tree().quit(_failures)


func _test_gift_and_hint() -> void:
	Game.set_ability(&"dash", false)
	var got: Array[StringName] = []
	var on_gift := func(ability: StringName) -> void: got.append(ability)
	Events.gift_received.connect(on_gift)
	var extra := {Vector2i(9, 11): "h", Vector2i(14, 11): "g"}
	var player := await _spawn(_grid(40, 16, [Rect2i(0, 12, 40, 4)], Vector2i(5, 11), extra,
		"h: hint text=HINT_JUMP
g: gift ability=dash"))
	var hint := _find(_world, Hint) as Hint
	var parts: Array = hint.call(&"_parts") if hint else []
	_check("dica mostra a tecla do pulo", parts.has(["SPACE", true]), str(parts))
	var grab_hint := Hint.create(Vector2.ZERO, "HINT_GRAB")
	_world.add_child(grab_hint)
	var grab_parts: Array = grab_hint.call(&"_parts")
	_check("dica de agarrar mostra o C e o CTRL", grab_parts.has(["C", true]) and grab_parts.has(["CTRL", true]), str(grab_parts))
	grab_hint.queue_free()
	var reached: Array[Node2D] = []
	var on_fire := func(fire: Node2D) -> void: reached.append(fire)
	Events.checkpoint_reached.connect(on_fire)
	var fire := Checkpoint.create(Vector2(-400, 0))
	_world.add_child(fire)
	fire.call(&"_on_body_entered", player)
	fire.call(&"_on_body_entered", player)
	Events.checkpoint_reached.disconnect(on_fire)
	_check("fogueira ja acesa nao muda o sitio de renascer", reached.size() == 1 and fire.lit, "avisos %d" % reached.size())
	fire.queue_free()
	Input.action_press(&"dash")
	await _ticks(2)
	var dashed_before := player.state_machine.is_in(&"Dash")
	Input.action_release(&"dash")
	Input.action_press(&"move_right")
	await _ticks(45)
	_check("dica aparece ao chegar perto", hint != null and hint.modulate.a > 0.5, "opacidade %.2f" % (hint.modulate.a if hint else -1.0))
	await _ticks(100)
	Input.action_release(&"move_right")
	_check("rosa de Afrodite da o dash", not dashed_before and Game.has_ability(&"dash") and got == [&"dash"],
		"antes: dash %s; depois: %s, sinal %s" % [dashed_before, Game.has_ability(&"dash"), got])
	Events.gift_received.disconnect(on_gift)
	Game.unlock_all()


func _test_jump_heights() -> void:
	var player := await _spawn(_flat_room())
	var full := await _jump_height(player, 60)
	_check("pulo completo", full >= 48.0 and full <= 66.0, "%.1f px = %.2f tiles" % [full, full / TILE])
	await _ticks(60)
	var tap := await _jump_height(player, 2)
	_check("pulo curto (toque)", tap > 8.0 and tap < full * 0.6, "%.1f px = %.2f tiles" % [tap, tap / TILE])
	await _ticks(60)
	var start_y := player.global_position.y
	var top := start_y
	Input.action_press(&"jump")
	for i in 40:
		await _ticks(1)
		top = minf(top, player.global_position.y)
	Input.action_release(&"jump")
	await _ticks(2)
	Input.action_press(&"jump")
	for i in 60:
		await _ticks(1)
		top = minf(top, player.global_position.y)
	Input.action_release(&"jump")
	_check("pulo duplo", _last_jump == &"double" and start_y - top > full + 20.0,
		"%.1f px = %.2f tiles" % [start_y - top, (start_y - top) / TILE])


func _test_run_and_jump_distance() -> void:
	var player := await _spawn(_flat_room())
	Input.action_press(&"move_right")
	await _ticks(60)
	var max_speed := player.config.max_run_speed
	_check("velocidade de corrida", absf(player.velocity.x - max_speed) < 1.0, "%.0f px/s" % player.velocity.x)
	var from_x := player.global_position.x
	Input.action_press(&"jump")
	await _ticks(4)
	while not player.is_on_floor():
		await _ticks(1)
	var distance := player.global_position.x - from_x
	_check("alcance do pulo a correr", distance >= 96.0, "%.1f px = %.2f tiles" % [distance, distance / TILE])


func _test_dash() -> void:
	var player := await _spawn(_flat_room())
	var from_x := player.global_position.x
	Input.action_press(&"dash")
	await _ticks(2)
	var entered := player.state_machine.is_in(&"Dash")
	Input.action_release(&"dash")
	await _ticks(70)
	var distance := player.global_position.x - from_x
	_check("dash no chao", entered and distance > 60.0 and distance < 100.0, "%.1f px = %.2f tiles" % [distance, distance / TILE])
	_check("dash recarrega no chao", player.dash_charges == 1)
	Input.action_press(&"move_right")
	Input.action_press(&"move_down")
	Input.action_press(&"dash")
	await _ticks(9)
	_last_jump = &""
	Input.action_press(&"jump")
	await _ticks(2)
	_check("hiper pulo", _last_jump == &"hyper", "%.0f px/s" % player.velocity.x)
	for action in ACTIONS:
		Input.action_release(action)
	await _ticks(120)
	Game.set_ability(&"dash", false)
	Input.action_press(&"dash")
	await _ticks(2)
	_check("sem a habilidade nao ha dash", not player.state_machine.is_in(&"Dash"))
	Input.action_release(&"dash")
	Game.set_ability(&"dash", true)


func _test_coyote() -> void:
	var data := _grid(40, 40, [Rect2i(0, 12, 20, 4), Rect2i(0, 36, 40, 4)], Vector2i(15, 11))
	var player := await _spawn(data)
	Game.set_ability(&"double_jump", false)
	Input.action_press(&"move_right")
	while player.is_on_floor():
		await _ticks(1)
	await _ticks(8)
	_last_jump = &""
	Input.action_press(&"jump")
	await _ticks(2)
	_check("coyote time", _last_jump == &"ground" and player.velocity.y < 0.0)
	Input.action_release(&"jump")
	player = await _spawn(data)
	Input.action_press(&"move_right")
	while player.is_on_floor():
		await _ticks(1)
	await _ticks(20)
	_last_jump = &""
	Input.action_press(&"jump")
	await _ticks(2)
	_check("coyote time expira", _last_jump == &"")
	Input.action_release(&"jump")
	Game.set_ability(&"double_jump", true)


func _test_wall_jump() -> void:
	var data := _grid(26, 34, [Rect2i(0, 30, 26, 4), Rect2i(10, 0, 1, 30), Rect2i(15, 0, 1, 30)], Vector2i(13, 29))
	var player := await _spawn(data)
	Game.set_ability(&"double_jump", false)
	var start_y := player.global_position.y
	var kinds: Array[StringName] = []
	var side := 1
	Input.action_press(&"move_right")
	Input.action_press(&"jump")
	await _ticks(3)
	Input.action_release(&"jump")
	for hop in 4:
		var waited := 0
		while player.wall_dir != side and waited < 120:
			await _ticks(1)
			waited += 1
		_last_jump = &""
		Input.action_press(&"jump")
		await _ticks(2)
		kinds.append(_last_jump)
		Input.action_release(&"move_right" if side == 1 else &"move_left")
		side = -side
		Input.action_press(&"move_right" if side == 1 else &"move_left")
		await _ticks(20)
		Input.action_release(&"jump")
	var climbed := start_y - player.global_position.y
	_check("pulo de parede sobe o poco", kinds.count(&"wall") == 4 and climbed > 96.0,
		"%s, subiu %.0f px" % [kinds, climbed])
	Game.set_ability(&"double_jump", true)


func _test_single_wall() -> void:
	var data := _grid(30, 54, [Rect2i(0, 50, 30, 4), Rect2i(10, 0, 1, 50)], Vector2i(12, 49))
	var player := await _spawn(data)
	Game.set_ability(&"double_jump", false)
	var start_y := player.global_position.y
	var top_y := start_y
	var wall_jumps := [0]
	player.jumped.connect(func(kind: StringName) -> void:
		if kind == &"wall":
			wall_jumps[0] += 1)
	Input.action_press(&"move_left")
	Input.action_press(&"grab")
	Input.action_press(&"jump")
	var ticks := 0
	while ticks < 1200:
		var waited := 0
		while player.wall_dir != -1 and waited < 200:
			await _ticks(1)
			top_y = minf(top_y, player.global_position.y)
			waited += 1
		for tick in 60:
			await _ticks(1)
			top_y = minf(top_y, player.global_position.y)
		Input.action_release(&"jump")
		await _ticks(1)
		Input.action_press(&"jump")
		await _ticks(3)
		ticks += waited + 64
	for action in ACTIONS:
		Input.action_release(action)
	var climbed := start_y - top_y
	_check("parede sozinha nao se sobe aos pulos", wall_jumps[0] >= 8 and climbed < 140.0,
		"%d pulos de parede, subiu %.0f px" % [wall_jumps[0], climbed])
	Game.set_ability(&"double_jump", true)


func _test_hazards() -> void:
	var player := await _spawn(_grid(30, 16, [Rect2i(0, 12, 30, 4)], Vector2i(5, 11), {Vector2i(12, 11): "^"}))
	Input.action_press(&"move_right")
	await _ticks(90)
	_check("espinhos matam", player.is_dead())
	player = await _spawn(_grid(30, 30, [Rect2i(0, 26, 30, 4)], Vector2i(5, 25), {Vector2i(9, 25): "M"}))
	var start_y := player.global_position.y
	var top := start_y
	Input.action_press(&"move_right")
	for i in 100:
		await _ticks(1)
		top = minf(top, player.global_position.y)
	_check("cogumelo-mola", start_y - top > 70.0, "%.1f px = %.2f tiles" % [start_y - top, (start_y - top) / TILE])
	var slab := {}
	for x in range(10, 14):
		slab[Vector2i(x, 12)] = "~"
	player = await _spawn(_grid(30, 30, [Rect2i(0, 12, 10, 4), Rect2i(0, 26, 30, 4)], Vector2i(8, 11), slab))
	Input.action_press(&"move_right")
	await _ticks(30)
	Input.action_release(&"move_right")
	await _ticks(20)
	var on_slab := player.is_on_floor() and player.global_position.x > 160.0
	await _ticks(110)
	_check("laje desmorona", on_slab and player.global_position.y > 12 * TILE + 20.0, "y = %.0f" % player.global_position.y)
	player = await _spawn(_grid(60, 30, [Rect2i(0, 26, 60, 4)], Vector2i(5, 25), {Vector2i(8, 22): "*"}))
	Input.action_press(&"jump")
	await _ticks(24)
	Input.action_press(&"move_right")
	Input.action_press(&"dash")
	await _ticks(2)
	Input.action_release(&"dash")
	await _ticks(32)
	var refilled := player.dash_charges == 1 and not player.is_on_floor()
	Input.action_press(&"dash")
	await _ticks(8)
	_check("pata devolve o dash no ar", refilled and player.state_machine.is_in(&"Dash"), "cargas depois da pata: %d" % int(refilled))
	for action in ACTIONS:
		Input.action_release(action)


func _test_projectiles() -> void:
	var flat: Array[Rect2i] = [Rect2i(0, 12, 40, 4)]
	var min_ticks := int(Combat.MIN_TELEGRAPH * Engine.physics_ticks_per_second)

	var player := await _spawn(_grid(40, 16, flat, Vector2i(5, 11), {Vector2i(25, 5): "e"}, "e: emitter pattern=aimed first=0 warn=0.1"))
	var emitter := _find(_world, Emitter) as Emitter
	var early := emitter.shots_fired
	var waited := 40
	while emitter.shots_fired == 0 and waited < 300:
		await _ticks(1)
		waited += 1
	_check("aviso antes do disparo", early == 0 and waited >= min_ticks, "primeira faisca ao fim de %d passos (minimo %d)" % [waited, min_ticks])
	var pool := ProjectilePool.of(self)
	var spark: Projectile = pool.active_projectiles()[0] if pool.active_count() > 0 else null
	var before := spark.velocity.angle_to(Combat.aim_point(player) - spark.global_position) if spark else 0.0
	await _ticks(int(0.6 * Engine.physics_ticks_per_second))
	_check("rajada de tres faiscas", emitter.shots_fired == 3, "%d faisca(s)" % emitter.shots_fired)
	waited = 0
	while not player.is_dead() and waited < 600:
		await _ticks(1)
		waited += 1
	_check("faisca mirada acerta e mata", spark != null and player.is_dead(), "desvio inicial %.2f rad, %d passos ate acertar" % [before, waited])

	player = await _spawn(_grid(40, 16, flat, Vector2i(5, 11)))
	pool = ProjectilePool.of(self)
	var straight := ShotSpec.new()
	straight.turn_rate = 0.0
	straight.speed = 200.0
	pool.spawn(Vector2(400, 120), Vector2.DOWN, straight, player)
	await _ticks(60)
	_check("faisca desfaz-se no cenario", pool.active_count() == 0)

	straight.speed = 100.0
	pool.spawn(player.global_position + Vector2(70, -12), Vector2.LEFT, straight, player)
	await _ticks(20)
	Input.action_press(&"move_right")
	Input.action_press(&"dash")
	await _ticks(2)
	Input.action_release(&"dash")
	await _ticks(40)
	_check("dash atravessa a faisca", not player.is_dead() and pool.active_count() == 0,
		"morto: %s, faiscas em jogo: %d" % [player.is_dead(), pool.active_count()])
	for action in ACTIONS:
		Input.action_release(action)

	player = await _spawn(_grid(40, 16, flat, Vector2i(5, 11), {Vector2i(20, 9): "m"}, "m: mine warn=0.1"))
	var mine := _find(_world, Mine) as Mine
	var asleep := mine.phase == Mine.Phase.SLEEP
	player.teleport(Vector2(20 * TILE - 40, 12 * TILE))
	await _ticks(4)
	var arming := mine.phase == Mine.Phase.ARMING
	waited = 4
	while mine.phase == Mine.Phase.ARMING and waited < 300:
		await _ticks(1)
		waited += 1
	var chasing := mine.phase == Mine.Phase.CHASE
	await _ticks(200)
	_check("mina acorda, avisa e persegue", asleep and arming and chasing and waited >= min_ticks and player.is_dead(),
		"aviso de %d passos; dormia %s, avisou %s, perseguiu %s, matou %s" % [waited, asleep, arming, chasing, player.is_dead()])

	player = await _spawn(_grid(40, 16, flat, Vector2i(20, 11), {Vector2i(20, 3): "z"}, "z: beam from=90 to=90 first=0 warn=0.1 on=1.0"))
	var beam := _find(_world, Beam) as Beam
	var safe_during_warning := beam.phase == Beam.Phase.WARN and not player.is_dead()
	await _ticks(60)
	_check("feixe avisa e depois mata", safe_during_warning and player.is_dead())
	ProjectilePool.of(self).clear()

	player = await _spawn(_grid(40, 16, flat, Vector2i(20, 11), {}, ""))
	var feet := player.global_position
	ThunderBomb.throw(_world, feet + Vector2(120, -6), Vector2.ZERO)
	await _ticks(240)
	var safe_far := not player.is_dead()
	ThunderBomb.throw(_world, feet + Vector2(14, -6), Vector2.ZERO)
	await _ticks(240)
	_check("bomba do Bronte mata so perto", safe_far and player.is_dead(), "longe vivo %s, perto morto %s" % [safe_far, player.is_dead()])


func _test_enemies() -> void:
	var flat: Array[Rect2i] = [Rect2i(0, 12, 40, 4)]
	Game.unlock_all()
	var player := await _spawn(_grid(40, 16, flat, Vector2i(5, 11), {Vector2i(8, 11): "h"}, "h: acorn speed=0 dir=1"))
	var hog := _find(_world, Balanos) as Balanos
	Input.action_press(&"move_right")
	Input.action_press(&"dash")
	await _ticks(2)
	Input.action_release(&"dash")
	await _ticks(30)
	Input.action_release(&"move_right")
	_check("dash contra inimigo mata o personagem", hog != null and hog.alive and player.is_dead())
	player = await _spawn(_grid(40, 16, flat, Vector2i(5, 11), {Vector2i(9, 11): "h"}, "h: acorn speed=40 dir=-1"))
	await _ticks(260)
	var walker := _find(_world, Balanos) as Balanos
	_check("bolota mata ao toque", player.is_dead(), "bolota em x=%.0f, personagem em x=%.0f" % [walker.global_position.x, player.global_position.x])
	player = await _spawn(_grid(40, 16, flat, Vector2i(5, 11), {Vector2i(20, 6): "g"}, "g: shade speed=0"))
	var moth := _find(_world, StyxShade) as StyxShade
	var home := moth.position
	moth.position += Vector2(40, 10)
	Events.player_respawned.emit()
	await _ticks(2)
	_check("inimigos voltam ao sitio no respawn", moth.alive and moth.visible and moth.position.distance_to(home) < 4.0)


func _test_bestiary() -> void:
	Game.unlock_all()
	var player: Player
	var cave: Array[Rect2i] = [Rect2i(0, 12, 40, 4), Rect2i(0, 0, 40, 4)]
	player = await _spawn(_grid(40, 16, cave, Vector2i(5, 11), {Vector2i(12, 4): "b"}, "b: bat reach=40"))
	var bat := _find(_world, EmpusaBat) as EmpusaBat
	var calm := bat.state == EmpusaBat.State.HANG
	Input.action_press(&"move_right")
	var waited := 0
	while bat.state == EmpusaBat.State.HANG and waited < 240:
		await _ticks(1)
		waited += 1
	Input.action_release(&"move_right")
	var peek_ticks := 0
	while bat.state == EmpusaBat.State.PEEK and peek_ticks < 240:
		await _ticks(1)
		peek_ticks += 1
	var min_ticks := int(Combat.MIN_TELEGRAPH * Engine.physics_ticks_per_second) - 1
	_check("morcego: acorda, avisa e mergulha", calm and bat.state == EmpusaBat.State.DROP and peek_ticks >= min_ticks,
			"aviso de %d passos (minimo %d)" % [peek_ticks, min_ticks])


func _test_water_and_rest() -> void:
	var flat: Array[Rect2i] = [Rect2i(0, 12, 40, 4)]
	var pool := {}
	for x in range(10, 16):
		for y in range(6, 12):
			pool[Vector2i(x, y)] = "W"
	var player := await _spawn(_grid(40, 16, flat, Vector2i(5, 11), pool))
	player.teleport(Vector2(13 * TILE, 4 * TILE))
	await _ticks(70)
	var slowed := player.water != null and player.velocity.y < 90.0
	Input.action_press(&"move_down")
	await _ticks(60)
	var sunk := player.global_position.y
	Input.action_release(&"move_down")
	Input.action_press(&"jump")
	await _ticks(3)
	var stroke := player.velocity.y < -60.0
	Input.action_release(&"jump")
	await _ticks(240)
	_check("agua trava a queda e deixa nadar", slowed and stroke, "vy na agua %s, bracada %s" % [slowed, stroke])
	_check("boia ate a superficie", player.global_position.y < sunk - 20.0, "afundou ate y=%.0f, boiou ate y=%.0f" % [sunk, player.global_position.y])
	player = await _spawn(_grid(40, 16, flat, Vector2i(5, 11)))
	player.set(&"_rest_time", Player.SLEEP_AFTER - 0.1)
	await _ticks(30)
	var slept := player.asleep and player.body_sprite.animation == &"sleep"
	Input.action_press(&"move_right")
	await _ticks(4)
	Input.action_release(&"move_right")
	_check("adormece parado e acorda com input", slept and not player.asleep)


func _test_save() -> void:
	SaveManager.path = "user://test_save.json"
	Game.deaths = 7
	Game.current_room = "h2"
	var saved := SaveManager.save_game(Vector2(123, 45))
	Game.reset_run()
	var loaded := SaveManager.load_game()
	Game.from_dict(loaded)
	var spawn: Array = loaded.get("spawn", [])
	_check("gravar e carregar", saved and Game.deaths == 7 and Game.current_room == "h2" and spawn == [123.0, 45.0])
	SaveManager.delete_save()
	_check("apagar o save", not SaveManager.has_save())
	Game.reset_run()
	Game.unlock_all()


func _test_world() -> void:
	if _world:
		_world.queue_free()
		_world = null
		await _ticks(1)
	var world: World = (load("res://scenes/world/world.tscn") as PackedScene).instantiate()
	world.map_dir = "res://levels/dev/hazards"
	add_child(world)
	await _ticks(30)
	_check("mundo carrega as salas", world.room_count() == 3 and world.current.data.id == "h1")
	world.player.teleport(Vector2(40 * TILE + 20, 19 * TILE))
	await _ticks(90)
	_check("troca de sala", world.current.data.id == "h2" and Game.current_room == "h2")
	world.player.die()
	await _ticks(120)
	_check("morte e respawn", Game.deaths == 1 and not world.player.is_dead()
		and world.player.global_position.distance_to(world.respawn_point) < 40.0)
	for i in 300:
		if not world._busy:
			break
		await _ticks(1)
	var upper: Rect2 = world._rect(world._data["h3"])
	world.player.teleport(upper.get_center())
	for i in 300:
		await _ticks(1)
		if world.current.data.id == "h3" and not world._busy:
			break
	var top := world.current.bounds.position.y
	world.player.teleport(Vector2(upper.get_center().x, top - 48.0))
	await _ticks(2)
	_check("teto invisivel por cima da sala", world.player.global_position.y > top and world.current.data.id == "h3",
		"y %.0f, topo %.0f, sala %s, ocupado %s, sentado %s" % [world.player.global_position.y, top, world.current.data.id, world._busy, world.player.seated])
	SaveManager.delete_save()
	world.queue_free()
	await _ticks(1)


func _test_menu() -> void:
	var world: World = (load("res://scenes/world/world.tscn") as PackedScene).instantiate()
	world.map_dir = "res://levels/dev/hazards"
	add_child(world)
	await _ticks(5)
	world._in_menu = true
	world._show_title()
	await _ticks(5)
	_check("titulo: sem comandos nem relogio", world._menu.is_open() and not world.player.input_enabled and not Game.timer_running)
	world._menu._items[world._menu._index]["do"].call()
	await _ticks(40)
	_check("novo jogo: joga-se", not world._menu.is_open() and world.player.input_enabled and Game.timer_running and not world._in_menu)
	world._pause()
	await _ticks(5)
	_check("pausa: arvore parada e menu aberto", get_tree().paused and world._menu.is_open() and not world.player.input_enabled)
	var paused_at := Game.play_time
	var texts: Array[String] = []
	for node in world._menu._box.find_children("*", "Label", true, false):
		texts.append((node as Label).text)
	await _ticks(30)
	_check("pausa: tempo, mortes e marshmallows", texts.has(tr(&"STATS_TIME") % Game.format_time(Game.play_time))
		and texts.has(tr(&"STATS_DEATHS") % Game.deaths) and texts.has(tr(&"FEATHER_PAUSE") % [0, Game.feather_total])
		and Game.feather_count() == 0, str(texts))
	_check("pausa: o relogio para", Game.play_time == paused_at, "%.3f -> %.3f" % [paused_at, Game.play_time])
	world._menu._items[0]["do"].call()
	await _ticks(40)
	_check("continuar depois da pausa", not get_tree().paused and world.player.input_enabled)
	SaveManager.delete_save()
	world.queue_free()
	await _ticks(1)


func _test_character() -> void:
	var data := HeroLook.meta()
	var problems: Array[String] = []
	var used := {}
	for letter: String in data["index"]:
		var i := int(data["index"][letter])
		if used.has(i) or i <= 0 or i >= HeroLook.PALETTE_SIZE:
			problems.append("indice %d (%s)" % [i, letter])
		used[i] = true
	for piece: String in data["pieces"]:
		var letters: Array = data["pieces"][piece]["letters"]
		for option: Dictionary in data["pieces"][piece]["options"]:
			for letter: String in letters:
				if not option["colors"].has(letter):
					problems.append("%s/%s sem %s" % [piece, option["id"], letter])
			for hex: String in option["colors"].values():
				var c := Color(hex)
				if c.h > 0.78 and c.h < 0.95 and c.s > 0.35 and c.v > 0.3:
					problems.append("%s/%s magenta %s" % [piece, option["id"], hex])
	_check("personagem: paletas completas, sem magenta", problems.is_empty(), str(problems.slice(0, 4)))
	var hero_frames: SpriteFrames
	var bad_frames: Array[String] = []
	for hat: Dictionary in HeroLook.options("hat"):
		for beard: Dictionary in HeroLook.options("beard"):
			for glasses: Dictionary in HeroLook.options("glasses"):
				for scarf: Dictionary in HeroLook.options("scarf"):
					var look := {"hat": hat["id"], "beard": beard["id"], "glasses": glasses["id"], "scarf": scarf["id"]}
					var frames := HeroLook.frames(look)
					var tex := frames.get_frame_texture(&"idle", 0)
					if frames.get_animation_names().size() != 18 or tex.get_size() != Vector2(32, 32):
						bad_frames.append(HeroLook.shape_key(look))
	_check("personagem: as 120 combinacoes de formas montam-se", bad_frames.is_empty(), str(bad_frames.slice(0, 4)))
	var base := HeroLook._image("base_none_full.png")
	var defaults := {}
	for piece in HeroLook.pieces():
		defaults[piece] = HeroLook.default_id(piece)
	var palette := HeroLook.palette_image(defaults)
	var hero := (load("res://assets/sprites/hero/hero.png") as Texture2D).get_image()
	hero.convert(Image.FORMAT_RGBA8)
	var step := float(data["step"])
	var mismatches := 0
	for y in hero.get_height():
		for x in hero.get_width():
			var want := hero.get_pixel(x, y)
			var src := base.get_pixel(x, y)
			if want.a8 == 0 and src.a8 == 0:
				continue
			var got := palette.get_pixel(roundi(src.r8 / step), 0)
			if want.a8 != src.a8 or want.r8 != got.r8 or want.g8 != got.g8 or want.b8 != got.b8:
				mismatches += 1
	_check("personagem: o Arthur da paleta e igual ao hero.png", mismatches == 0, "%d pixel(s) diferentes" % mismatches)
	var menu := GameMenu.new()
	add_child(menu)
	menu.open_title(false)
	var main_keys: Array = menu._items.map(func(item: Dictionary) -> StringName: return item["key"])
	var signals := [0]
	var count := func() -> void: signals[0] += 1
	Events.look_changed.connect(count)
	menu._set_page(&"character")
	var keys := func() -> Array:
		return menu._items.map(func(item: Dictionary) -> StringName: return item["key"])
	menu._focus(&"LOOK_JACKET")
	menu._adjust(1)
	var jacket := str(Settings.value("look_jacket"))
	var no_hat_color: bool = not keys.call().has(&"LOOK_HAT_COLOR")
	menu._focus(&"LOOK_HAT")
	menu._adjust(1)
	var hat_color: bool = keys.call().has(&"LOOK_HAT_COLOR")
	var previewed := menu._preview != null and menu._preview.material == HeroLook.material() \
		and menu._preview.sprite_frames == HeroLook.frames(HeroLook.current())
	for piece: StringName in [&"LOOK_BEARD", &"LOOK_GLASSES"]:
		menu._focus(piece)
		menu._adjust(1)
		previewed = previewed and menu._preview.sprite_frames == HeroLook.frames(HeroLook.current())
	menu._focus(&"LOOK_RESET")
	menu._activate()
	var reset: bool = HeroLook.current()["jacket"] == "indigo" and HeroLook.current()["hat"] == "none"
	Events.look_changed.disconnect(count)
	_check("personagem: menu muda, avisa e restaura", main_keys.has(&"MENU_CHARACTER") and jacket == "forest"
		and no_hat_color and hat_color and previewed and reset and signals[0] == 5,
		"casaco %s, cor do chapeu %s/%s, previa %s, reset %s, avisos %d" % [jacket, no_hat_color, hat_color, previewed, reset, signals[0]])
	menu.queue_free()
	await _ticks(2)


func _test_end_results() -> void:
	_check("tempo formatado", Game.format_time(59.9) == "0:59" and Game.format_time(61) == "1:01"
		and Game.format_time(3725) == "1:02:05", "%s %s %s" % [Game.format_time(59.9), Game.format_time(61), Game.format_time(3725)])
	var menu := GameMenu.new()
	add_child(menu)
	var closed := [false]
	menu.results_closed.connect(func() -> void: closed[0] = true)
	menu.open_results()
	await _ticks(10)
	await get_tree().process_frame
	Input.action_press(&"jump")
	await _ticks(2)
	Input.action_release(&"jump")
	await _ticks(2)
	var early: bool = closed[0]
	await get_tree().create_timer(GameMenu.RESULTS_LOCK + 0.1).timeout
	await get_tree().process_frame
	Input.action_press(&"jump")
	await _ticks(2)
	Input.action_release(&"jump")
	await _ticks(2)
	_check("fim: os resultados esperam pela tecla", menu._page == &"results" and not early and closed[0],
		"cedo %s, fechou %s" % [early, closed[0]])
	menu.queue_free()
	await _ticks(1)


func _test_language() -> void:
	Settings.change("language", "pt_BR")
	var pt_text := tr(&"MENU_NEW_GAME")
	Settings.change("language", "en")
	_check("idioma: troca o texto do menu", pt_text == "Novo Jogo" and tr(&"MENU_NEW_GAME") == "New Game", pt_text)
	var en := load("res://i18n/strings.en.translation") as Translation
	var pt := load("res://i18n/strings.pt_BR.translation") as Translation
	var missing: Array[String] = []
	var marks: Array[String] = []
	var no_glyph := {}
	for key: StringName in en.get_message_list():
		var english := String(en.get_message(key))
		var portuguese := String(pt.get_message(key))
		if portuguese == "":
			missing.append(key)
			continue
		if english.count("%") != portuguese.count("%") or english.count("{") != portuguese.count("{"):
			marks.append(key)
		if key == &"LAB_HINT":
			continue
		var font := PixelFont.get_book_font() if String(key).begins_with("DIARY_") else PixelFont.get_font()
		for text in [english, portuguese]:
			for i in text.length():
				var code: int = text.unicode_at(i)
				if not "%|~{}".contains(text[i]) and not font.has_char(code):
					no_glyph[text[i]] = key
	_check("idioma: portugues com todas as chaves e marcas", missing.is_empty() and marks.is_empty(), "%s %s" % [missing, marks])
	_check("idioma: a fonte tem todas as letras usadas", no_glyph.is_empty(), str(no_glyph))


func _test_assist_and_chapters() -> void:
	var world: World = (load("res://scenes/world/world.tscn") as PackedScene).instantiate()
	world.map_dir = "res://levels/ember"
	world.start_room = "c0"
	add_child(world)
	await _ticks(5)
	var player := world.player
	Settings.change("assist_invincible", true)
	Settings.change("assist_infinite_dash", true)
	player.die()
	await _ticks(2)
	var off_ignored := player.is_dead()
	await _ticks(160)
	Settings.change("assist", true)
	player.die()
	await _ticks(2)
	var survived := not player.is_dead()
	player.dash_charges = 0
	player.end_dash()
	var refilled := player.dash_charges == 1
	player.die(true)
	await _ticks(2)
	_check("assistencia: invencivel e dash infinito so com ela ligada", off_ignored and survived and refilled and player.is_dead())
	await _ticks(160)
	var item_keys := func() -> Array:
		return world._menu._items.map(func(item: Dictionary) -> StringName: return item["key"])
	Settings.change("assist", false)
	world._in_menu = true
	world._show_title()
	await _ticks(5)
	var hidden: bool = not item_keys.call().has(&"MENU_CHAPTERS")
	world._menu._set_page(&"pause")
	hidden = hidden and not item_keys.call().has(&"MENU_CHAPTERS")
	Settings.change("assist", true)
	world._menu._set_page(&"pause")
	var in_pause: bool = item_keys.call().has(&"MENU_CHAPTERS")
	world._menu._set_page(&"main")
	var keys: Array = item_keys.call()
	world._menu._set_page(&"chapters")
	var pages: Array = item_keys.call()
	_check("capitulos: so com a assistencia, no titulo e na pausa, todos abertos", hidden and in_pause
		and keys.has(&"MENU_CHAPTERS") and pages.size() == Chapters.count() + 1, "%s %s" % [keys, pages])
	world._menu._items[2]["do"].call()
	await _ticks(150)
	_check("capitulo: comeca em h1 com o dash, sentado a fogueira e gravado", world.current.data.id == "h1"
		and Game.has_ability(&"dash") and player.seated and SaveManager.has_save() and player.input_enabled
		and not world._in_menu, "sala %s, dash %s, sentado %s, save %s" % [world.current.data.id, Game.has_ability(&"dash"), player.seated, SaveManager.has_save()])
	world.queue_free()
	await _ticks(1)
	SaveManager.delete_save()
	world = (load("res://scenes/world/world.tscn") as PackedScene).instantiate()
	world.map_dir = "res://levels/ember"
	world.start_room = "z2"
	add_child(world)
	await _ticks(10)
	var fight := _find(world, ThroneFight) as ThroneFight
	world.player.teleport(Vector2(fight._bounds.position.x + 140.0, world.player.global_position.y))
	await _ticks(90)
	world._pause()
	await _ticks(5)
	keys = world._menu._items.map(func(item: Dictionary) -> StringName: return item["key"])
	var skip_at := keys.find(&"MENU_SKIP_FIGHT")
	if skip_at >= 0:
		world._menu._items[skip_at]["do"].call()
	await _ticks(90)
	_check("assistencia: saltar a luta final", skip_at >= 0 and not get_tree().paused
		and fight.stage in [ThroneFight.Stage.ENDING, ThroneFight.Stage.DONE], "%s, fase %s" % [keys, fight.stage])
	world.queue_free()
	await _ticks(1)
	for setting: String in ["assist", "assist_invincible", "assist_infinite_dash"]:
		Settings.change(setting, false)
	SaveManager.delete_save()
	Game.reset_run()
	Game.unlock_all()


func _test_diary(world: World) -> void:
	var diary := _find(world, Diary) as Diary
	_check("diario: aparece depois da abertura", diary != null and diary.visible)
	if diary == null:
		return
	world.player.global_position.x = diary.global_position.x + 14
	await _ticks(10)
	Input.action_press(&"move_up")
	await _ticks(2)
	Input.action_release(&"move_up")
	await _ticks(10)
	var reader := _find(world, DiaryReader) as DiaryReader
	_check("diario: abre e pausa", reader != null and get_tree().paused and reader.pages.size() >= 6,
		"leitor %s, pausa %s" % [reader != null, get_tree().paused])
	if reader == null:
		return
	Input.action_press(&"move_right")
	await _ticks(2)
	Input.action_release(&"move_right")
	await _ticks(2)
	var turned := reader.spread == 1
	Input.action_press(&"jump")
	await _ticks(30)
	Input.action_release(&"jump")
	await _ticks(10)
	_check("diario: vira a pagina e fecha", turned and not DiaryReader.is_open() and not get_tree().paused
		and world.player.is_on_floor(), "virou %s, aberto %s, pausa %s" % [turned, DiaryReader.is_open(), get_tree().paused])


func _test_intro(skip: bool) -> void:
	var world: World = (load("res://scenes/world/world.tscn") as PackedScene).instantiate()
	world.map_dir = "res://levels/ember"
	world.start_room = "c0"
	add_child(world)
	await _ticks(5)
	world._in_menu = true
	world._show_title()
	await _ticks(5)
	var label := "abertura (saltada)" if skip else "abertura"
	_check(label + ": cachorro no acampamento no titulo", world._camp_dog() != null)
	world._menu._items[world._menu._index]["do"].call()
	if skip:
		await _ticks(60)
		Input.action_press(&"pause")
		await _ticks(90)
		Input.action_release(&"pause")
		await _ticks(320)
	else:
		await _ticks(420)
		var scene := _find(world, IntroScene) as IntroScene
		_check(label + ": espera pela bolinha sem comandos", scene != null and scene._hint != null
			and not world.player.input_enabled and world.camera.is_zoomed())
		for throw in 2:
			Input.action_press(&"jump")
			await _ticks(3)
			Input.action_release(&"jump")
			await _ticks(560)
		await _ticks(1700)
	_check(label + ": o cachorro sumiu e joga-se", world._camp_dog() == null and Game.dog_taken
		and world.player.input_enabled and not world._busy and SaveManager.has_save(),
		"cao %s, comandos %s, ocupado %s, save %s" % [world._camp_dog() != null, world.player.input_enabled, world._busy, SaveManager.has_save()])
	if skip:
		await _test_diary(world)
	var lost := _find(world.current, LostBall) as LostBall
	_check(label + ": a bolinha ficou no chao", lost != null)
	if lost:
		world.player.teleport(lost.global_position + Vector2(0, -4))
		await _ticks(40)
		_check(label + ": Arthur apanha a bolinha", lost._taken)
	SaveManager.delete_save()
	Game.reset_run()
	Game.unlock_all()
	world.queue_free()
	await _ticks(1)


func _test_fight() -> void:
	var world: World = (load("res://scenes/world/world.tscn") as PackedScene).instantiate()
	world.map_dir = "res://levels/ember"
	world.start_room = "z2"
	add_child(world)
	await _ticks(10)
	var fight := _find(world, ThroneFight) as ThroneFight
	var player := world.player
	_check("luta: arena com o cao, a bolinha e o cachorro do Arthur", fight != null and fight.bolt != null
		and fight.ball != null and fight.buddy != null and fight.stage == ThroneFight.Stage.WAITING)
	if fight == null:
		world.queue_free()
		return
	var fires_in_arena := 0
	for node in fight._room_node.find_children("*", "Checkpoint", true, false):
		fires_in_arena += 1
	_check("luta: a arena nao tem fogueira (fica no fim do salao)", fires_in_arena == 0)
	var floor_y := player.global_position.y
	player.teleport(Vector2(fight._bounds.position.x + 140.0, floor_y))
	await _ticks(60)
	_check("luta: ele da por nos e ataca", fight._noticed and fight.stage == ThroneFight.Stage.APPROACH)
	await _ticks(200)
	var bar := world.boss_bar()
	_check("luta: a barra do chefe entra, com os tambores", bar.is_shown() and bar.total == 6 and bar.left == 6
		and fight._drums != null and fight._drums.playing, "barra %d/%d, tambores %s" % [bar.left, bar.total, fight._drums != null and fight._drums.playing])
	fight._dev_intro = true
	player.teleport(Vector2(fight._bounds.position.x + 30.0, floor_y))
	var near_entrance := 0
	for i in 240:
		for node in fight._room.get_children():
			if node is LightningStrike and (node as LightningStrike).once and not node.is_queued_for_deletion() 					and (node as Node2D).global_position.x < fight._bounds.position.x + 90.0:
				near_entrance += 1
		if near_entrance > 0:
			break
		await _ticks(1)
	fight._dev_intro = false
	player.dev_invincible = false
	fight._clear_hazards(true)
	_check("luta: a entrada da arena nao e sitio seguro", near_entrance > 0)
	player.die()
	_check("luta: com o Arthur morto a luta continua a encontra-lo (antes fechava o jogo)", fight._player() == player)
	await _ticks(160)
	_check("luta: morrer antes da bolinha volta ao inicio", fight.stage == ThroneFight.Stage.APPROACH
		and fight.ball.global_position.is_equal_approx(fight._ball_start) and not player.is_dead())
	player.teleport(fight.ball.global_position + Vector2(0, FetchBall.RADIUS))
	await _ticks(4)
	_check("luta: pegar na bolinha liga o jogo", fight.stage == ThroneFight.Stage.HOLD and fight._started
		and fight.ball.state == FetchBall.State.HELD and fight._hint != null)
	_check("luta: pegar na bolinha cala os tambores", not fight._drums.playing
		and bar._subtitle.text == tr(&"BOSS_TITLE"))
	fight._power = 0.0
	var tap := fight._throw_velocity(player)
	fight._power = 1.0
	var full := fight._throw_velocity(player)
	fight._power = -1.0
	player.facing = 1
	Input.action_press(&"grab")
	await _ticks(60)
	var charging := fight.stage == ThroneFight.Stage.HOLD and fight._power > 0.5
	Input.action_release(&"grab")
	await _ticks(2)
	_check("luta: segurar C enche a forca e atira mais longe", charging and fight.stage == ThroneFight.Stage.CHASE
		and absf(full.x) > absf(tap.x) * 2.0, "toque %s, forca toda %s, a carregar %s" % [tap, full, charging])
	for i in 2400:
		if fight.energy <= 5 or player.is_dead():
			break
		await _ticks(1)
	_check("luta: ele vai busca-la e a barra perde um segmento", fight.energy == 5 and bar.left == 5,
		"energia %d, barra %d, fase %s" % [fight.energy, bar.left, fight.stage])
	fight.energy = 3
	if fight.stage == ThroneFight.Stage.HOLD:
		fight.stage = ThroneFight.Stage.SEEK
	var hall_fire: Node2D = null
	for node in world._rooms["z1"].find_children("*", "Checkpoint", true, false):
		if hall_fire == null or (node as Node2D).global_position.x > hall_fire.global_position.x:
			hall_fire = node
	world.campfire = hall_fire.global_position
	world.campfire_room = "z1"
	player.die()
	await _ticks(160)
	_check("luta: morrer renasce no salao e retoma a fase", Game.current_room == "z1" and fight.energy == 4
		and fight.stage == ThroneFight.Stage.SEEK and fight.ball.state == FetchBall.State.REST and bar.left == 4,
		"sala %s, energia %d, barra %d" % [Game.current_room, fight.energy, bar.left])
	world.campfire = Vector2.INF
	world.campfire_room = ""
	player.teleport(Vector2(fight._bounds.position.x + 24.0, floor_y))
	await _ticks(120)
	player.teleport(Vector2(fight._bounds.position.x + 200.0, floor_y))
	await _ticks(2)
	var here := fight._ground_under(player.global_position)
	player.velocity = Vector2(150, 0)
	var ahead := fight._strike_target(player)
	player.velocity = Vector2.ZERO
	var still := fight._strike_target(player)
	_check("luta: o raio cai onde ele vai estar (parado: em cima dele)", Game.current_room == "z2"
		and ahead.x > here.x + 60.0 and absf(still.x - here.x) < 2.0, "chao %s, a correr %s, parado %s" % [here, ahead, still])
	var hall: Room = world._rooms["z1"]
	var hunt := _find(hall, StormHunt) as StormHunt
	player.dev_invincible = true
	player.teleport(Vector2(hall.bounds.position.x + 60.0 * 16.0, floor_y))
	var hunted := false
	for i in 480:
		for node in hall.find_children("*", "LightningStrike", true, false):
			if (node as LightningStrike).once and absf((node as Node2D).global_position.x - player.global_position.x) < 100.0:
				hunted = true
		if hunted:
			break
		await _ticks(1)
	_check("luta: no salao os raios cacam o Arthur", hunt != null and hunted and Game.current_room == "z1")
	player.teleport(Vector2(fight._bounds.position.x + 200.0, floor_y))
	await _ticks(120)
	player.dev_invincible = false
	fight.energy = 1
	var ended := false
	for attempt in 6:
		if await _fight_throw(fight, player, 0):
			ended = true
			break
		if fight.energy > 1:
			fight.energy = 1
	for i in 3000:
		if Game.finished:
			break
		await _ticks(1)
	_check("luta: sem energia acaba o jogo", ended and Game.finished, "energia %d, fase %s" % [fight.energy, fight.stage])
	_check("luta: no fim os dois caes dormem (o de Zeus nao acorda)", fight.bolt.rest_anim == &"sleep"
		and fight.buddy.sprite.animation == &"sleep" and player.pose == &"sit",
		"zeus %s, cachorro %s, arthur %s" % [fight.bolt.rest_anim, fight.buddy.sprite.animation, player.pose])
	world.queue_free()
	await _ticks(1)
	SaveManager.delete_save()
	Game.reset_run()
	Game.unlock_all()


func _fight_throw(fight: ThroneFight, player: Player, energy: int) -> bool:
	for i in 600:
		if fight.stage == ThroneFight.Stage.HOLD:
			break
		if not player.is_dead() and fight.ball.state == FetchBall.State.REST:
			player.teleport(fight.ball.global_position + Vector2(0, FetchBall.RADIUS))
		await _ticks(1)
	if fight.stage != ThroneFight.Stage.HOLD:
		return false
	player.facing = 1 if player.global_position.x < fight._bounds.get_center().x else -1
	Input.action_press(&"grab")
	await _ticks(2)
	Input.action_release(&"grab")
	for i in 2400:
		if fight.energy <= energy or player.is_dead():
			break
		await _ticks(1)
	return fight.energy <= energy


func _test_olympus() -> void:
	var row := {}
	for x in range(10, 13):
		row[Vector2i(x, 12)] = "f"
	var player := await _spawn(_grid(40, 30, [Rect2i(0, 12, 10, 4)], Vector2i(8, 11), row, "f: fall"))
	var block := _find(_world, FallBlock) as FallBlock
	Input.action_press(&"move_right")
	await _ticks(22)
	Input.action_release(&"move_right")
	await _ticks(72)
	var falling := block.state == FallBlock.State.FALLING and player.is_on_floor()
	await _ticks(700)
	_check("laje de marmore cai e volta", falling and block.state == FallBlock.State.IDLE and block.position.y == 12 * TILE,
		"estado %d, y %.0f" % [block.state, block.position.y])
	var clouds := {Vector2i(14, 10): "A", Vector2i(15, 10): "A", Vector2i(16, 10): "A",
		Vector2i(20, 10): "B", Vector2i(21, 10): "B", Vector2i(22, 10): "B"}
	player = await _spawn(_grid(40, 16, [Rect2i(0, 12, 40, 4)], Vector2i(5, 11), clouds, "A: beat group=a
B: beat group=b"))
	var a: BeatCloud
	var b: BeatCloud
	for node in _world.get_child(0).get_node("Props").get_children():
		if node is BeatCloud:
			if (node as BeatCloud).group == 0:
				a = node
			else:
				b = node
	var before := a.is_solid()
	var apart := a.is_solid() != b.is_solid()
	await _ticks(int(1.6 * 120) + 4)
	_check("nuvens ao ritmo alternam", apart and a.is_solid() != b.is_solid() and a.is_solid() != before)
	CloudStep.reset_all()
	var steps := {Vector2i(8, 9): "0", Vector2i(9, 9): "0", Vector2i(10, 9): "0", Vector2i(20, 6): "1", Vector2i(21, 6): "1", Vector2i(22, 6): "1"}
	player = await _spawn(_grid(40, 16, [Rect2i(0, 12, 40, 4)], Vector2i(5, 11), steps, "0: step order=0 near=48
1: step order=1"))
	var first: CloudStep
	var second: CloudStep
	for node in _world.get_child(0).get_node("Props").get_children():
		if node is CloudStep:
			if (node as CloudStep).order == 0:
				first = node
			else:
				second = node
	var hidden := first.shown and not second.shown
	Input.action_press(&"jump")
	await _ticks(10)
	Input.action_release(&"jump")
	await _ticks(10)
	_check("nuvens rosa aparecem a cada pulo", hidden and second.shown)
	CloudStep.reset_all()
	player = await _spawn(_grid(140, 16, [Rect2i(0, 12, 140, 4)], Vector2i(10, 11), {Vector2i(1, 1): "X"}, "X: chase speed=100 starts=1 to=200"))
	await _ticks(400)
	_check("tempestade apanha quem fica parado", player.is_dead())
	player = await _spawn(_grid(140, 16, [Rect2i(0, 12, 140, 4)], Vector2i(10, 11), {Vector2i(1, 1): "X"}, "X: chase speed=100 starts=1 to=200"))
	Input.action_press(&"move_right")
	await _ticks(400)
	Input.action_release(&"move_right")
	_check("tempestade: quem corre escapa", not player.is_dead())
	Game.feathers.clear()
	player = await _spawn(_grid(30, 16, [Rect2i(0, 12, 30, 4)], Vector2i(5, 11), {Vector2i(9, 11): "q"}, "q: feather"))
	Input.action_press(&"move_right")
	await _ticks(40)
	Input.action_release(&"move_right")
	_check("marshmallow conta e grava", Game.feather_count() == 1 and (Game.to_dict()["feathers"] as Array).size() == 1)
	Game.feathers.clear()
	if _world:
		_world.queue_free()
		_world = null
		await _ticks(1)
	var world: World = (load("res://scenes/world/world.tscn") as PackedScene).instantiate()
	world.map_dir = "res://levels/ember"
	world.start_room = "o0"
	add_child(world)
	await _ticks(30)
	_check("marshmallows contados em todas as fases", Game.feather_total == 20, "%d" % Game.feather_total)
	var glow := _find(world.current, SkyGlow) as SkyGlow
	world.player.teleport(glow.global_position + Vector2(0, 8))
	await _ticks(400)
	_check("brilho leva ao Olimpo", world.current.data.id == "o1", world.current.data.id)
	world._go_through("o7")
	await _ticks(200)
	var gate := _find(world.current, Gate) as Gate
	world.player.teleport(gate.global_position)
	await _ticks(500)
	_check("portao do palacio leva ao salao", world.current.data.id == "z1", world.current.data.id)
	world.queue_free()
	await _ticks(2)
	world = (load("res://scenes/world/world.tscn") as PackedScene).instantiate()
	world.map_dir = "res://levels/ember"
	world.start_room = "o1"
	add_child(world)
	await _ticks(30)
	var slab := _find(world.current, FallBlock) as FallBlock
	if slab == null:
		slab = _find(world.current.get_node("Props"), FallBlock) as FallBlock
	slab.trigger()
	world.player.teleport(world.current.bounds.position + Vector2(40, 34) * TILE)
	var died_y := INF
	for i in 400:
		await _ticks(1)
		if world.player.is_dead():
			died_y = world.player.global_position.y
			break
	_check("cair no vazio mata depressa", died_y < world.current.bounds.end.y - 64.0,
		"morreu a %.0f px do fundo da sala" % (world.current.bounds.end.y - died_y))
	await _ticks(240)
	_check("lajes voltam ao renascer", slab.state == FallBlock.State.IDLE and slab.position == slab._origin, "estado %d" % slab.state)
	world.queue_free()
	await _ticks(2)
	world = (load("res://scenes/world/world.tscn") as PackedScene).instantiate()
	world.map_dir = "res://levels/ember"
	world.start_room = "o6"
	add_child(world)
	await _ticks(30)
	var chase := _find(world.current, StormChase) as StormChase
	if chase == null:
		chase = _find(world.current.get_node("Props"), StormChase) as StormChase
	var deaths := Game.deaths
	chase.state = StormChase.State.RUN
	chase.front = world.player.global_position.x - world.current.global_position.x + 64.0
	await _ticks(260)
	_check("tempestade mata uma vez so", Game.deaths == deaths + 1 and not world.player.is_dead(), "%d morte(s)" % (Game.deaths - deaths))
	SaveManager.delete_save()
	world.queue_free()
	await _ticks(1)


func _test_rooms() -> void:
	var paths := _find_rooms("res://levels")
	for path in paths:
		var problems := RoomData.load_file(path).validate()
		_check("sala " + path.get_file(), problems.is_empty(), ", ".join(problems))
	_check("existem salas", not paths.is_empty(), "%d ficheiro(s)" % paths.size())


func _test_enemy_sheets() -> void:
	var dir := "res://assets/sprites/enemies"
	var count := 0
	var problems: PackedStringArray = []
	for file in DirAccess.get_files_at(dir):
		if not file.ends_with(".json") or file == "shots.json":
			continue
		count += 1
		var frames := SpriteSheet.frames(dir.path_join(file))
		for anim: StringName in [&"hurt", &"die"]:
			if not frames.has_animation(anim) or frames.get_frame_count(anim) == 0:
				problems.append("%s sem %s" % [file, anim])
		if frames.get_frame_texture(frames.get_animation_names()[0], 0) == null:
			problems.append("%s sem imagem" % file)
	_check("folhas de inimigos carregam", count >= 13 and problems.is_empty(), "%d folha(s) %s" % [count, ", ".join(problems)])


func _jump_height(player: Player, hold_ticks: int) -> float:
	var start_y := player.global_position.y
	var top := start_y
	Input.action_press(&"jump")
	for i in 90:
		if i == hold_ticks:
			Input.action_release(&"jump")
		await _ticks(1)
		top = minf(top, player.global_position.y)
	Input.action_release(&"jump")
	return start_y - top


func _flat_room() -> RoomData:
	return _grid(80, 16, [Rect2i(0, 12, 80, 4)], Vector2i(5, 11))


func _grid(width: int, height: int, solids: Array[Rect2i], spawn: Vector2i, extra: Dictionary = {}, defs := "") -> RoomData:
	var rows: PackedStringArray = []
	for y in height:
		var row := ""
		for x in width:
			var character := "."
			for rect in solids:
				if rect.has_point(Vector2i(x, y)):
					character = "#"
			if Vector2i(x, y) == spawn:
				character = "P"
			character = extra.get(Vector2i(x, y), character)
			row += character
		rows.append(row)
	return RoomData.parse("id: test\n---\n" + "\n".join(rows) + ("\n---\n" + defs if defs != "" else ""))


func _spawn(data: RoomData) -> Player:
	for action in ACTIONS:
		Input.action_release(action)
	ProjectilePool.of(self).clear()
	if _world:
		_world.queue_free()
	await _ticks(2)
	_world = Node2D.new()
	add_child(_world)
	Game.current_room = data.id
	var room := RoomBuilder.build(data, ZoneTheme.of(&"forest"), false)
	_world.add_child(room)
	var player: Player = PLAYER_SCENE.instantiate()
	room.add_child(player)
	player.teleport(room.spawn_point)
	player.jumped.connect(func(kind: StringName) -> void: _last_jump = kind)
	await _ticks(40)
	return player


func _find(node: Node, type: Variant) -> Node:
	for child in node.get_children():
		if is_instance_of(child, type):
			return child
		var deeper := _find(child, type)
		if deeper:
			return deeper
	return null


func _ticks(count: int) -> void:
	for i in count:
		await get_tree().physics_frame


func _check(test_name: String, passed: bool, detail := "") -> void:
	if not passed:
		_failures += 1
	print("%s  %s%s" % ["ok    " if passed else "FALHOU", test_name, ("  ->  " + detail) if detail != "" else ""])


func _find_rooms(dir_path: String) -> PackedStringArray:
	var found: PackedStringArray = []
	for sub in DirAccess.get_directories_at(dir_path):
		found.append_array(_find_rooms(dir_path.path_join(sub)))
	for file in DirAccess.get_files_at(dir_path):
		if file.ends_with(".room"):
			found.append(dir_path.path_join(file))
	return found
