shader_type canvas_item;


uniform vec4 rect;

varying vec2 world;

void vertex() {
	world = (MODEL_MATRIX * vec4(VERTEX, 0.0, 1.0)).xy;
}

void fragment() {
	if (world.x < rect.x || world.y < rect.y || world.x >= rect.z || world.y >= rect.w) {
		discard;
	}
}
