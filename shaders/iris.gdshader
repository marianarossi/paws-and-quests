shader_type canvas_item;

uniform vec2 center = vec2(320.0, 180.0);
uniform float radius = 800.0;
uniform vec2 screen = vec2(640.0, 360.0);

void fragment() {
	vec2 pixel = floor(UV * screen) + 0.5;
	COLOR.a *= step(radius, distance(pixel, center));
}
