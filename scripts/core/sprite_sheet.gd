class_name SpriteSheet

static var _cache: Dictionary[String, SpriteFrames] = {}


static func clear_cache() -> void:
	_cache.clear()


static func unit_scale(json_path: String) -> Vector2:
	return Vector2.ONE * float(((load(json_path) as JSON).data as Dictionary).get("scale", 1.0))


static func frames(json_path: String) -> SpriteFrames:
	if _cache.has(json_path):
		return _cache[json_path]
	var meta: Dictionary = (load(json_path) as JSON).data
	var texture: Texture2D = load(json_path.get_base_dir().path_join(str(meta["image"])))
	var result := frames_with_texture(json_path, texture)
	_cache[json_path] = result
	return result


static func frames_with_texture(json_path: String, texture: Texture2D) -> SpriteFrames:
	var meta: Dictionary = (load(json_path) as JSON).data
	var fw := int(meta["frame_w"])
	var fh := int(meta["frame_h"])
	var result := SpriteFrames.new()
	result.remove_animation(&"default")
	var animations: Dictionary = meta["animations"]
	for anim_name: String in animations:
		var anim: Dictionary = animations[anim_name]
		result.add_animation(anim_name)
		result.set_animation_speed(anim_name, float(anim["fps"]))
		result.set_animation_loop(anim_name, bool(anim["loop"]))
		for i in int(anim["frames"]):
			var frame := AtlasTexture.new()
			frame.atlas = texture
			frame.region = Rect2(i * fw, int(anim["row"]) * fh, fw, fh)
			frame.filter_clip = true
			result.add_frame(anim_name, frame)
	return result
