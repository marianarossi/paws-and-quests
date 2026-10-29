class_name WoofText
extends Node2D

const COLOR := Color("fff6e8")
const SHADOW := Color("1c1433")


static func say(parent: Node, at: Vector2, text: String, big := true, color := COLOR, time := 1.4) -> WoofText:
	var word := WoofText.new()
	word.z_index = 60
	parent.add_child(word)
	word.global_position = at.round()
	var font := PixelFont.get_font()
	var size := PixelFont.size()
	var scale := 2.0 if big else 1.0
	var label := Label.new()
	label.text = text
	label.add_theme_font_override(&"font", font)
	label.add_theme_font_size_override(&"font_size", size)
	label.add_theme_color_override(&"font_color", color)
	label.add_theme_color_override(&"font_shadow_color", SHADOW)
	label.add_theme_constant_override(&"shadow_offset_x", 1)
	label.add_theme_constant_override(&"shadow_offset_y", 1)
	label.scale = Vector2.ONE * scale
	var width := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x * scale
	label.position = Vector2(-width * 0.5, -size * scale).round()
	word.add_child(label)
	word.material = Lights.unshaded()
	label.use_parent_material = true
	word.modulate.a = 0.0
	var tween := word.create_tween()
	tween.tween_property(word, "modulate:a", 1.0, 0.1)
	tween.parallel().tween_property(word, "position:y", word.position.y - 5.0, time * 0.6)
	tween.tween_interval(time * 0.3)
	tween.tween_property(word, "modulate:a", 0.0, time * 0.4)
	tween.tween_callback(word.queue_free)
	return word
