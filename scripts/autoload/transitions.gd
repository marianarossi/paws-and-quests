extends CanvasLayer

const SCREEN := Vector2(640, 360)
const DARK := Color(0.03, 0.03, 0.07)
const OPEN_RADIUS := 760.0

var _rect: ColorRect
var _iris: ColorRect
var _iris_material: ShaderMaterial


func _ready() -> void:
	layer = 90
	process_mode = Node.PROCESS_MODE_ALWAYS
	_rect = _make_rect()
	_rect.color = Color(DARK, 0.0)
	_iris = _make_rect()
	_iris.color = DARK
	_iris_material = ShaderMaterial.new()
	_iris_material.shader = load("res://shaders/iris.gdshader")
	_iris_material.set_shader_parameter(&"screen", SCREEN)
	_iris.material = _iris_material
	_iris.visible = false


func fade_out(duration := 0.15, tint := DARK) -> void:
	_rect.color = Color(tint, _rect.color.a)
	await _fade(1.0, duration)


func fade_in(duration := 0.15) -> void:
	await _fade(0.0, duration)


func iris_close(screen_point: Vector2, duration := 0.3) -> void:
	_iris.visible = true
	_iris_material.set_shader_parameter(&"center", screen_point)
	await _iris_to(OPEN_RADIUS, 0.0, duration, Tween.EASE_IN)


func iris_open(screen_point: Vector2, duration := 0.35) -> void:
	_iris_material.set_shader_parameter(&"center", screen_point)
	await _iris_to(0.0, OPEN_RADIUS, duration, Tween.EASE_IN)
	_iris.visible = false


func _iris_to(from: float, to: float, duration: float, ease_type: Tween.EaseType) -> void:
	var tween := create_tween().set_trans(Tween.TRANS_QUAD).set_ease(ease_type)
	tween.tween_method(func(r: float) -> void: _iris_material.set_shader_parameter(&"radius", floorf(r)), from, to, duration)
	await tween.finished


func _make_rect() -> ColorRect:
	var rect := ColorRect.new()
	rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(rect)
	return rect


func _fade(alpha: float, duration: float) -> void:
	var tween := create_tween()
	tween.tween_property(_rect, "color:a", alpha, duration)
	await tween.finished
