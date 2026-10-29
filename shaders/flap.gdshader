shader_type canvas_item;
render_mode unshaded;


uniform float fps = 3.0;
uniform float frames = 2.0;

void fragment() {
	float frame = mod(floor(TIME * fps), frames);
	COLOR = texture(TEXTURE, UV + vec2(0.0, frame / frames));
}
