class_name PixelFont

const SHEET := "res://assets/fonts/serif.json"
const BOOK_SHEET := "res://assets/fonts/serif_book.json"
const SPACING := 1

static var _font: FontFile
static var _book: FontFile


static func clear_cache() -> void:
	_font = null
	_book = null


static func size() -> int:
	return int(((load(SHEET) as JSON).data as Dictionary)["height"])


static func get_font() -> FontFile:
	if not _font:
		_font = _build(SHEET)
	return _font


static func book_size() -> int:
	return int(((load(BOOK_SHEET) as JSON).data as Dictionary)["height"])


static func get_book_font() -> FontFile:
	if not _book:
		_book = _build(BOOK_SHEET)
	return _book


static func _build(sheet: String) -> FontFile:
	var meta: Dictionary = (load(sheet) as JSON).data
	var height := int(meta["height"])
	var ascent := int(meta.get("ascent", height))
	var top := int(meta.get("top", 0))
	var full := top + height + int(meta.get("bottom", 0))
	var image := (load(sheet.get_basename() + ".png") as Texture2D).get_image()
	var font := FontFile.new()
	font.antialiasing = TextServer.FONT_ANTIALIASING_NONE
	font.fixed_size = height
	var key := Vector2i(height, 0)
	font.set_texture_image(0, key, 0, image)
	font.set_cache_ascent(0, height, ascent)
	font.set_cache_descent(0, height, maxi(1, height - ascent))
	var glyphs: Dictionary = meta["glyphs"]
	for symbol: String in glyphs:
		var x := int(glyphs[symbol][0])
		var width := int(glyphs[symbol][1])
		var codes: Array[int] = [symbol.unicode_at(0)]
		var lower := symbol.to_lower()
		if symbol != lower and not glyphs.has(lower):
			codes.append(lower.unicode_at(0))
		for code in codes:
			font.set_glyph_advance(0, height, code, Vector2(width + SPACING, 0))
			font.set_glyph_offset(0, key, code, Vector2(0, -ascent - top))
			font.set_glyph_size(0, key, code, Vector2(width, full))
			font.set_glyph_uv_rect(0, key, code, Rect2(x, 0, width, full))
			font.set_glyph_texture_idx(0, key, code, 0)
	return font
