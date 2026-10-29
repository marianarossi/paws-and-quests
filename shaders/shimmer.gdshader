shader_type canvas_item;
render_mode unshaded;


uniform float speed = 4.0;

void fragment() {
	vec2 cell = floor(UV / TEXTURE_PIXEL_SIZE);
	float tick = floor(TIME * speed);
	float shift = floor(2.4 * sin(cell.y * 0.9 + tick * 1.3) + 0.5);
	vec4 color = texture(TEXTURE, UV + vec2(shift * TEXTURE_PIXEL_SIZE.x, 0.0));
	float flicker = fract(sin(dot(vec2(floor(cell.x / 3.0), cell.y + tick * 7.0), vec2(12.9898, 78.233))) * 43758.5453);
	color.a *= step(0.3, flicker);
	COLOR = color;
}
