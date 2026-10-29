shader_type canvas_item;
render_mode unshaded;


uniform vec4 rects[16];
uniform int count = 0;

void fragment() {
	bool inside = count == 0;
	for (int i = 0; i < count; i++) {
		vec4 r = rects[i];
		if (SCREEN_UV.x >= r.x && SCREEN_UV.y >= r.y && SCREEN_UV.x < r.z && SCREEN_UV.y < r.w) {
			inside = true;
		}
	}
	if (!inside) {
		discard;
	}
}
