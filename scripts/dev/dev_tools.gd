class_name DevTools


static func screenshot_and_quit(host: Node, delay: float, focus: Node2D) -> void:
	var tree := host.get_tree()
	var view := tree.root
	await tree.create_timer(delay).timeout
	await RenderingServer.frame_post_draw
	var folder := ProjectSettings.globalize_path("res://captures")
	DirAccess.make_dir_recursive_absolute(folder)
	view.get_texture().get_image().save_png(folder.path_join("shot.png"))
	if is_instance_valid(focus) and focus.is_inside_tree():
		print("SHOT ", focus.get_global_transform_with_canvas().origin / Vector2(view.get_visible_rect().size))
	print("FPS ", Engine.get_frames_per_second())
	tree.quit()


static func shot_delay() -> float:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--shot"):
			return float(arg.get_slice("=", 1)) if arg.contains("=") else 2.0
	return -1.0
