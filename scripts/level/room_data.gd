class_name RoomData
extends RefCounted

const STATIC_CELLS := ".#=PC^v<>M~*W"
const WATER := "W"
const SOLID := "#"

var id := ""
var zone: StringName = &"forest"
var meta: Dictionary[String, String] = {}
var defs: Dictionary[String, Dictionary] = {}
var world_cell := Vector2i.ZERO
var width := 0
var height := 0
var rows: PackedStringArray = []


static func load_file(path: String) -> RoomData:
	var text := FileAccess.get_file_as_string(path)
	if text.is_empty():
		push_error("sala vazia ou inexistente: " + path)
	var data := parse(text)
	if data.id.is_empty():
		data.id = path.get_file().get_basename()
	return data


static func parse(text: String) -> RoomData:
	var data := RoomData.new()
	var section := 0
	for raw in text.split("\n"):
		var line := raw.trim_suffix("\r")
		var stripped := line.strip_edges()
		if stripped == "---":
			section += 1
		elif section == 1:
			data.rows.append(line.rstrip(" \t"))
		elif stripped.is_empty() or stripped.begins_with(";"):
			continue
		else:
			var sep := stripped.find(":")
			if sep <= 0:
				continue
			var key := stripped.substr(0, sep).strip_edges()
			var value := stripped.substr(sep + 1).strip_edges()
			if section == 0:
				data.meta[key] = value
			else:
				data.defs[key] = _parse_def(value)
	while not data.rows.is_empty() and data.rows[-1].is_empty():
		data.rows.remove_at(data.rows.size() - 1)
	for row in data.rows:
		data.width = maxi(data.width, row.length())
	for i in data.rows.size():
		data.rows[i] = data.rows[i].rpad(data.width, ".")
	data.height = data.rows.size()
	data.id = data.meta.get("id", "")
	data.zone = StringName(data.meta.get("zone", "forest"))
	data.world_cell = Vector2i(to_vector(data.meta.get("pos", "0,0")))
	return data


static func _parse_def(text: String) -> Dictionary:
	var def := {}
	for token in text.split(" ", false):
		var eq := token.find("=")
		if eq < 0:
			def["type"] = token
		else:
			def[token.substr(0, eq)] = token.substr(eq + 1)
	return def


static func to_vector(text: String) -> Vector2:
	var parts := text.split(",")
	return Vector2(float(parts[0]), float(parts[1])) if parts.size() == 2 else Vector2.ZERO


func cell(x: int, y: int) -> String:
	return rows[clampi(y, 0, height - 1)][clampi(x, 0, width - 1)]


func raw_cell(x: int, y: int) -> String:
	return rows[y][x] if (x >= 0 and y >= 0 and x < width and y < height) else ""


func is_solid(x: int, y: int) -> bool:
	return cell(x, y) == SOLID


func find_cells(character: String) -> Array[Vector2i]:
	var found: Array[Vector2i] = []
	for y in height:
		for x in width:
			if rows[y][x] == character:
				found.append(Vector2i(x, y))
	return found


func run_length(x: int, y: int) -> int:
	var length := 1
	while raw_cell(x + length, y) == rows[y][x]:
		length += 1
	return length


func validate() -> PackedStringArray:
	var problems: PackedStringArray = []
	if width == 0 or height == 0:
		problems.append("grelha vazia")
		return problems
	for y in height:
		for x in width:
			var character := rows[y][x]
			if not STATIC_CELLS.contains(character) and not defs.has(character):
				problems.append("caractere desconhecido '%s' em (%d, %d)" % [character, x, y])
	for key in defs:
		if not defs[key].has("type"):
			problems.append("entidade '%s' sem tipo" % key)
	if find_cells("P").is_empty():
		problems.append("a sala precisa de pelo menos um 'P'")
	return problems


func solid_depth() -> PackedInt32Array:
	var depth := PackedInt32Array()
	depth.resize(width * height)
	depth.fill(99)
	var queue: Array[Vector2i] = []
	for y in height:
		for x in width:
			if not is_solid(x, y):
				depth[y * width + x] = 0
				queue.append(Vector2i(x, y))
	var head := 0
	while head < queue.size():
		var c := queue[head]
		head += 1
		var next := depth[c.y * width + c.x] + 1
		for oy in [-1, 0, 1]:
			for ox in [-1, 0, 1]:
				var n := c + Vector2i(ox, oy)
				if n.x < 0 or n.y < 0 or n.x >= width or n.y >= height:
					continue
				if depth[n.y * width + n.x] > next:
					depth[n.y * width + n.x] = next
					queue.append(n)
	return depth
