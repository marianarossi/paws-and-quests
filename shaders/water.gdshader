shader_type canvas_item;
render_mode unshaded;

uniform vec2 size = vec2(96.0, 48.0);
uniform vec2 origin = vec2(0.0);
uniform bool surface = true;
uniform float top_depth = 0.0;
uniform float fade_depth = 34.0;
uniform vec4 top_color : source_color = vec4(0.36, 0.84, 0.82, 0.5);
uniform vec4 deep_color : source_color = vec4(0.10, 0.28, 0.48, 0.74);
uniform vec4 foam_color : source_color = vec4(0.86, 1.0, 0.96, 0.95);
uniform bool reveal = false;
global uniform vec2 hero_pos;

const float PAD = 4.0;

void fragment() {
	vec2 p = floor(UV * (size + vec2(0.0, PAD)));
	float wx = p.x + origin.x;
	float local = p.y - PAD;
	float d = local;
	if (surface) {
		d += floor(1.5 + 1.0 * sin(wx * 0.16 + TIME * 1.6) + 0.8 * sin(wx * 0.07 - TIME * 0.9)) - 1.0;
	}
	if (d < 0.0) {
		discard;
	}
	float depth = d + top_depth;
	float t = clamp(depth / fade_depth, 0.0, 1.0);
	t = clamp(floor(t * 14.0 + 0.4 * sin(wx * 0.09 + TIME * 0.4) + 0.5) / 14.0, 0.0, 1.0);
	vec4 col = mix(top_color, deep_color, pow(t, 0.75));
	float lit = 1.0 - clamp(depth / 44.0, 0.0, 1.0);
	if (sin((wx - depth * 0.7) * 0.06 + TIME * 0.22) > 0.72) {
		col.rgb = mix(col.rgb, foam_color.rgb, 0.12 * lit);
	}
	float row = floor(depth / 5.0);
	float streak = sin((wx + row * 13.0) * 0.19 + TIME * (0.5 + 0.15 * mod(row, 3.0)));
	if (depth > 5.0 && mod(depth, 5.0) < 1.0 && streak > 0.84) {
		col.rgb = mix(col.rgb, foam_color.rgb, 0.4 * lit);
	}
	if (reveal && d >= 4.0) {
		vec2 world = origin + vec2(p.x, local) + 0.5;
		float r = length(world - (hero_pos + vec2(0.0, -9.0)));
		float keep = r < 16.0 ? 0.28 : (r < 22.0 ? 0.45 : (r < 28.0 ? 0.7 : 1.0));
		col.a *= keep;
	}
	if (surface) {
		if (d < 1.0) {
			col = foam_color;
		} else if (d < 2.0) {
			col = mix(col, foam_color, sin(wx * 0.4 + TIME * 2.0) > 0.1 ? 0.7 : 0.25);
		} else if (d < 4.0) {
			col.rgb = mix(col.rgb, foam_color.rgb, 0.18);
		}
	}
	COLOR = col;
}
