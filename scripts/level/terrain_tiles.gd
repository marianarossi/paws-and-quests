class_name TerrainTiles

const TILE := 16
const ART_TILE := 16
const ART_SCALE := float(TILE) / ART_TILE
const PERIOD := 16
const MASKS := 19
const SOIL_LEFT := 1
const SOIL_RIGHT := 2
const TERRAIN_ATLAS_COLUMNS := 4 * MASKS
const TERRAIN_ATLAS_ROWS := 64
const PLATFORM_ART_TOP := 3
const WORLD_LAYER := 1
const SOLID := Vector2i(0, 0)
const ONE_WAY := Vector2i(1, 0)
const PLATFORM_THICKNESS := 5

static var _cache: Dictionary[String, TileSet] = {}


static func clear_cache() -> void:
	_cache.clear()


static func collision_set() -> TileSet:
	if not _cache.has("collision"):
		var image := Image.create(TILE * 2, TILE, false, Image.FORMAT_RGBA8)
		image.fill(Color(1, 0, 1, 0.4))
		var tile_set := TileSet.new()
		tile_set.tile_size = Vector2i(TILE, TILE)
		tile_set.add_physics_layer()
		tile_set.set_physics_layer_collision_layer(0, WORLD_LAYER)
		tile_set.set_physics_layer_collision_mask(0, 0)
		var source := _atlas(ImageTexture.create_from_image(image), 2, 1, TILE)
		tile_set.add_source(source, 0)
		_add_box(source, SOLID, TILE, false)
		_add_box(source, ONE_WAY, PLATFORM_THICKNESS, true)
		_cache["collision"] = tile_set
	return _cache["collision"]


static func art_set(atlas_path: String, columns: int, rows: int) -> TileSet:
	if not _cache.has(atlas_path):
		var tile_set := TileSet.new()
		tile_set.tile_size = Vector2i(ART_TILE, ART_TILE)
		tile_set.add_source(_atlas(load(atlas_path), columns, rows, ART_TILE), 0)
		_cache[atlas_path] = tile_set
	return _cache[atlas_path]


static func terrain_cell(mask: int, world_tile: Vector2i, soil := 0) -> Vector2i:
	if mask == 15:
		mask += soil
	var tx := posmod(world_tile.x, PERIOD)
	var ty := posmod(world_tile.y, PERIOD)
	@warning_ignore("integer_division")
	return Vector2i((tx % 4) * MASKS + mask, (tx / 4) * 16 + ty)


static func _atlas(texture: Texture2D, columns: int, rows: int, size: int) -> TileSetAtlasSource:
	var source := TileSetAtlasSource.new()
	source.texture = texture
	source.texture_region_size = Vector2i(size, size)
	for y in rows:
		for x in columns:
			source.create_tile(Vector2i(x, y))
	return source


static func _add_box(source: TileSetAtlasSource, coords: Vector2i, height: int, one_way: bool) -> void:
	var half := TILE * 0.5
	var tile := source.get_tile_data(coords, 0)
	tile.add_collision_polygon(0)
	tile.set_collision_polygon_points(0, 0, PackedVector2Array([
		Vector2(-half, -half), Vector2(half, -half), Vector2(half, -half + height), Vector2(-half, -half + height),
	]))
	tile.set_collision_polygon_one_way(0, 0, one_way)
