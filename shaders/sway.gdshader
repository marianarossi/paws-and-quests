shader_type canvas_item;


uniform float amplitude = 1.0;
uniform float speed = 2.4;
uniform float bounce = 0.0;
uniform float reach = 0.4;
uniform float phase = 0.0;
uniform bool hanging = false;

varying float lift;

void vertex() {
	float top = VERTEX.y < 0.5 ? 1.0 : 0.0;
	lift = hanging ? 1.0 - top : top;
}

void fragment() {
	int pose = int(mod(floor(TIME * speed + phase), 4.0));
	vec2 shift = vec2(0.0);
	if (bounce > 0.0) {
		if (pose == 1 && lift > 0.45) {
			shift.y = 1.0;
		}
	} else if (pose == 1 || pose == 3) {
		float side = pose == 1 ? 1.0 : -1.0;
		shift.x = side * ((lift > reach ? 1.0 : 0.0) + (amplitude > 1.5 && lift > 0.68 ? 1.0 : 0.0));
	}
	COLOR = texture(TEXTURE, UV - shift * TEXTURE_PIXEL_SIZE);
}
