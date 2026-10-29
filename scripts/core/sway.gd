class_name Sway

const SHADER := preload("res://shaders/sway.gdshader")

static var _cache: Dictionary[String, ShaderMaterial] = {}


static func clear_cache() -> void:
	_cache.clear()


const PHASES := 8

static func material(motion: String, hanging := false, variant := 0) -> ShaderMaterial:
	if motion == "none":
		return null
	var slot := posmod(variant, PHASES)
	var key := "%s|%s|%d" % [motion, hanging, slot]
	if not _cache.has(key):
		var mat := ShaderMaterial.new()
		mat.shader = SHADER
		mat.set_shader_parameter(&"hanging", hanging)
		mat.set_shader_parameter(&"phase", slot * 1.5 + 0.13 * slot)
		match motion:
			"bob":
				mat.set_shader_parameter(&"speed", 2.0)
				mat.set_shader_parameter(&"bounce", 1.0)
			"rustle":
				mat.set_shader_parameter(&"amplitude", 2.0)
				mat.set_shader_parameter(&"reach", 0.18)
				mat.set_shader_parameter(&"speed", 2.2)
			_:
				mat.set_shader_parameter(&"amplitude", 2.0 if hanging else 1.0)
				mat.set_shader_parameter(&"speed", 1.8 if hanging else 2.4)
		_cache[key] = mat
	return _cache[key]
