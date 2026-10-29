shader_type canvas_item;

uniform sampler2D palette : filter_nearest, repeat_disable;
uniform float index_step = 4.0;

varying vec4 node_modulate;

void vertex() {
	node_modulate = COLOR;
}

void fragment() {
	vec4 src = texture(TEXTURE, UV);
	int index = int(round(src.r * 255.0 / index_step));
	vec4 color = texelFetch(palette, ivec2(index, 0), 0);
	COLOR = vec4(color.rgb, src.a) * node_modulate;
}
