shader_type canvas_item;
render_mode unshaded;


uniform float speed = 6.0;

void fragment() {
	COLOR = texture(TEXTURE, UV + vec2(floor(TIME * speed) * TEXTURE_PIXEL_SIZE.x, 0.0));
}
