class_name HeroLook

const DIR := "res://assets/sprites/hero/look/"
const SHEET_JSON := "res://assets/sprites/hero/hero.json"
const SHADER := preload("res://shaders/hero_palette.gdshader")
const PALETTE_SIZE := 64
const COLOR_PIECES: Array[String] = ["skin", "hair", "eyes", "jacket", "pack", "pants", "boots",
	"hat_color", "scarf_color"]
const SHAPES: Array[String] = ["hat", "beard", "glasses", "scarf"]

static var _meta: Dictionary = {}
static var _material: ShaderMaterial
static var _palette: ImageTexture
static var _frames_cache: Dictionary[String, SpriteFrames] = {}


static func meta() -> Dictionary:
	if _meta.is_empty():
		_meta = (load(DIR + "look.json") as JSON).data
	return _meta


static func pieces() -> Array[String]:
	var out: Array[String] = []
	out.append_array(COLOR_PIECES)
	out.append_array(SHAPES)
	return out


static func options(piece: String) -> Array:
	var data := meta()
	if piece in SHAPES:
		return data["shapes"][piece]
	return data["pieces"][piece]["options"]


static func setting_key(piece: String) -> String:
	return "look_" + piece


static func default_id(piece: String) -> String:
	return str(options(piece)[0]["id"])


static func current() -> Dictionary:
	var look := {}
	for piece in pieces():
		var wanted := str(Settings.value(setting_key(piece)))
		look[piece] = wanted if _find(piece, wanted) >= 0 else default_id(piece)
	return look


static func option_index(piece: String) -> int:
	return maxi(0, _find(piece, str(current()[piece])))


static func option_count(piece: String) -> int:
	return options(piece).size()


static func option_name(piece: String) -> StringName:
	return StringName(options(piece)[option_index(piece)]["name"])


static func cycle(piece: String, step: int) -> void:
	var list := options(piece)
	var next := wrapi(option_index(piece) + step, 0, list.size())
	Settings.change(setting_key(piece), str(list[next]["id"]))
	_changed()


static func randomize_look(rng: RandomNumberGenerator = null) -> void:
	if rng == null:
		rng = RandomNumberGenerator.new()
		rng.randomize()
	var changes := {}
	for piece in pieces():
		var list := options(piece)
		var pick := rng.randi_range(0, list.size() - 1)
		if piece in ["hat", "glasses", "scarf"] and rng.randf() < 0.5:
			pick = 0
		changes[setting_key(piece)] = str(list[pick]["id"])
	Settings.change_many(changes)
	_changed()


static func reset() -> void:
	var changes := {}
	for piece in pieces():
		changes[setting_key(piece)] = default_id(piece)
	Settings.change_many(changes)
	_changed()


static func colors(look: Dictionary) -> Dictionary:
	var data := meta()
	var out := {}
	for letter: String in data["fixed"]:
		out[letter] = Color(str(data["fixed"][letter]))
	for piece in COLOR_PIECES:
		var list: Array = data["pieces"][piece]["options"]
		var index := maxi(0, _find(piece, str(look.get(piece, ""))))
		var chosen: Dictionary = list[index]["colors"]
		for letter: String in chosen:
			out[letter] = Color(str(chosen[letter]))
	for letter: String in data["derived"]:
		var mix: Array = data["derived"][letter]
		out[letter] = (out[mix[0]] as Color).lerp(out[mix[1]], float(mix[2]))
	return out


static func color(letter: String) -> Color:
	return colors(current()).get(letter, Color.WHITE)


static func palette_image(look: Dictionary) -> Image:
	var image := Image.create(PALETTE_SIZE, 1, false, Image.FORMAT_RGBA8)
	var index: Dictionary = meta()["index"]
	var by_letter := colors(look)
	for letter: String in index:
		if by_letter.has(letter):
			image.set_pixel(int(index[letter]), 0, by_letter[letter])
	return image


static func material() -> ShaderMaterial:
	if _material == null:
		_material = ShaderMaterial.new()
		_material.shader = SHADER
		_material.set_shader_parameter(&"index_step", float(meta()["step"]))
		refresh_palette()
	return _material


static func refresh_palette() -> void:
	var image := palette_image(current())
	if _palette == null:
		_palette = ImageTexture.create_from_image(image)
	else:
		_palette.update(image)
	if _material:
		_material.set_shader_parameter(&"palette", _palette)


static func shape_key(look: Dictionary) -> String:
	return "%s_%s_%s_%s" % [look["hat"], look["beard"], look["glasses"], look["scarf"]]


static func frames(look: Dictionary) -> SpriteFrames:
	var key := shape_key(look)
	if _frames_cache.has(key):
		return _frames_cache[key]
	var sheet := _image("base_%s_%s.png" % [look["hat"], look["beard"]])
	var layers: Array[String] = []
	if look["glasses"] != "none":
		layers.append("glasses_%s.png" % look["glasses"])
	if look["scarf"] != "none":
		layers.append("scarf_%s.png" % look["beard"])
	for layer in layers:
		var top := _image(layer)
		sheet.blend_rect(top, Rect2i(Vector2i.ZERO, top.get_size()), Vector2i.ZERO)
	var result := SpriteSheet.frames_with_texture(SHEET_JSON, ImageTexture.create_from_image(sheet))
	_frames_cache[key] = result
	return result


static func dress(sprite: AnimatedSprite2D) -> void:
	var anim := sprite.animation
	var frame := sprite.frame
	var progress := sprite.frame_progress
	var playing := sprite.is_playing()
	sprite.sprite_frames = frames(current())
	sprite.material = material()
	if sprite.sprite_frames.has_animation(anim):
		sprite.animation = anim
		sprite.set_frame_and_progress(mini(frame, sprite.sprite_frames.get_frame_count(anim) - 1), progress)
		if playing:
			sprite.play()


static func clear_cache() -> void:
	_frames_cache.clear()


static func _image(file: String) -> Image:
	var image := (load(DIR + file) as Texture2D).get_image()
	if image.is_compressed():
		image.decompress()
	image.convert(Image.FORMAT_RGBA8)
	return image


static func _find(piece: String, id: String) -> int:
	var list := options(piece)
	for i in list.size():
		if str(list[i]["id"]) == id:
			return i
	return -1


static func _changed() -> void:
	refresh_palette()
	Events.look_changed.emit()
