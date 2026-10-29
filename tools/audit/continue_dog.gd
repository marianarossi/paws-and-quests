extends Node

func _ready() -> void:
	SaveManager.path = "user://test_save.json"
	Settings.use_file("user://test_settings.cfg")
	_run.call_deferred()


func _ticks(n: int) -> void:
	for i in n:
		await get_tree().physics_frame


func _run() -> void:
	var room := "e1"
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--save-room="):
			room = a.get_slice("=", 1)
	var world: World = (load("res://scenes/world/world.tscn") as PackedScene).instantiate()
	add_child(world)
	await _ticks(20)
	print("DOG: no titulo, cachorro = %s" % (world._camp_dog() != null))
	var fire: Node2D = world._build(room).find_children("*", "Checkpoint", true, false)[0]
	Game.current_room = room
	SaveManager.save_game(fire.global_position)
	world._on_continue()
	await _ticks(120)
	print("DOG: depois de continuar em %s, sala %s, cachorro = %s" % [room, Game.current_room, world._camp_dog() != null])
	for id in ["e1", "c0"]:
		var r: Rect2 = world._rect(world._data[id])
		world.player.teleport(Vector2(r.get_center().x, world._build(id).spawn_point.y))
		await _ticks(180)
	var dog := world._camp_dog()
	print("DOG: no acampamento (sala %s), cachorro = %s" % [Game.current_room, dog != null and is_instance_valid(dog) and not dog.is_queued_for_deletion()])
	SaveManager.delete_save()
	world.queue_free()
	await _ticks(2)
	get_tree().quit()
