extends Node

var _deaths := 0


func _ready() -> void:
	SaveManager.path = "user://test_save.json"
	Settings.use_file("user://test_settings.cfg")
	_run.call_deferred()


func _arg(name: String, fallback: String) -> String:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--%s=" % name):
			return a.get_slice("=", 1)
	return fallback


func _find(node: Node, type: Variant) -> Node:
	for child in node.get_children():
		if is_instance_of(child, type):
			return child
		var found := _find(child, type)
		if found:
			return found
	return null


func _ticks(n: int) -> void:
	for i in n:
		await get_tree().physics_frame


func _run() -> void:
	seed(int(_arg("seed", "1")))
	var frames := int(float(_arg("minutes", "5")) * 60.0 * 120.0)
	var world: World = (load("res://scenes/world/world.tscn") as PackedScene).instantiate()
	world.map_dir = "res://levels/ember"
	world.start_room = "z2"
	add_child(world)
	await _ticks(10)
	var fight := _find(world, ThroneFight) as ThroneFight
	var player := world.player
	Events.player_died.connect(func(_at: Vector2) -> void: _deaths += 1)
	var hall_fire: Node2D = null
	for node in world._rooms["z1"].find_children("*", "Checkpoint", true, false):
		if hall_fire == null or (node as Node2D).global_position.x > hall_fire.global_position.x:
			hall_fire = node
	world.campfire = hall_fire.global_position
	world.campfire_room = "z1"
	var floor_y := player.global_position.y
	var start := int(_arg("phase", "1"))
	if start > 1:
		player.teleport(Vector2(fight._bounds.position.x + 140.0, floor_y))
		await _ticks(30)
		fight._start_at_phase(start)
	fight._dev_intro = _arg("invincible", "0") == "1"
	var hold_left := 0
	var idle_left := 0
	var t := 0
	while t < frames and not Game.finished:
		await _ticks(1)
		t += 1
		if player.is_dead() or world._busy:
			continue
		if idle_left > 0:
			idle_left -= 1
			continue
		if Game.current_room == "z1":
			player.teleport(Vector2(fight._bounds.position.x + randf_range(30.0, 200.0), floor_y))
			idle_left = randi_range(30, 240)
			continue
		if fight.stage == ThroneFight.Stage.HOLD:
			if hold_left == 0:
				hold_left = randi_range(1, 900)
				if fight.energy == 1 and randf() < 0.7:
					var spots: Array = fight._spots[2] + fight._spots[1]
					var spot: Vector2 = fight._room.to_global(spots[randi() % spots.size()])
					player.teleport(spot + Vector2(0, FetchBall.RADIUS))
					hold_left = 30
				player.facing = 1 if randf() < 0.5 else -1
				Input.action_press(&"grab")
			hold_left -= 1
			if hold_left == 0:
				Input.action_release(&"grab")
				idle_left = randi_range(0, 600)
			continue
		if fight.ball.state == FetchBall.State.REST and randf() < 0.02:
			player.teleport(fight.ball.global_position + Vector2(0, FetchBall.RADIUS))
			continue
		if randf() < 0.01:
			player.teleport(Vector2(fight._bounds.position.x + randf_range(20.0, fight._bounds.size.x - 20.0), floor_y))
		idle_left = randi_range(0, 120)
	Input.action_release(&"grab")
	if Game.finished and fight.buddy:
		var under := fight._ground_under(fight.buddy.global_position + Vector2(0, -2))
		print("SOAK: cachorro no fim em %s, chao a %.1f px" % [fight.buddy.global_position, under.y - fight.buddy.global_position.y if under != Vector2.INF else INF])
	print("SOAK: %d passos, %d mortes, energia %d, fase %s, fim %s" % [t, _deaths, fight.energy, fight.stage, Game.finished])
	world.queue_free()
	await _ticks(2)
	get_tree().quit()
