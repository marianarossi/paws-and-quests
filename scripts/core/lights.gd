class_name Lights

const TEXTURE_RADIUS := 64.0

static var _radial: GradientTexture2D
static var _unshaded: CanvasItemMaterial


static func clear_cache() -> void:
	_radial = null
	_unshaded = null


static func radial() -> Texture2D:
	if _radial == null:
		var gradient := Gradient.new()
		gradient.offsets = PackedFloat32Array([0.0, 0.35, 0.7, 1.0])
		gradient.colors = PackedColorArray([
			Color(1, 1, 1, 1), Color(0.55, 0.55, 0.55, 1), Color(0.16, 0.16, 0.16, 1), Color(0, 0, 0, 0),
		])
		_radial = GradientTexture2D.new()
		_radial.gradient = gradient
		_radial.width = int(TEXTURE_RADIUS * 2)
		_radial.height = int(TEXTURE_RADIUS * 2)
		_radial.fill = GradientTexture2D.FILL_RADIAL
		_radial.fill_from = Vector2(0.5, 0.5)
		_radial.fill_to = Vector2(1.0, 0.5)
	return _radial


static func point(color: Color, radius: float, energy := 1.0) -> PointLight2D:
	var light := PointLight2D.new()
	light.texture = radial()
	light.texture_scale = radius / TEXTURE_RADIUS
	light.color = color
	light.energy = energy
	return light


static func unshaded() -> CanvasItemMaterial:
	if _unshaded == null:
		_unshaded = CanvasItemMaterial.new()
		_unshaded.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	return _unshaded
