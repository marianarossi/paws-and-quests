class_name Chapters

const LIST := [
	{"area": "ember_camp", "room": "e1", "dash": false},
	{"area": "twilight_grove", "room": "g1", "dash": true},
	{"area": "glimmer_hollow", "room": "h1", "dash": true},
	{"area": "little_olympus", "room": "o0", "dash": true},
	{"area": "thunder_court", "room": "z1", "dash": true},
]


static func count() -> int:
	return LIST.size()


static func available() -> bool:
	return Settings.assist_on()


static func name_key(index: int) -> StringName:
	return StringName("ZONE_" + String(LIST[index]["area"]).to_upper())


static func room(index: int) -> String:
	return LIST[index]["room"]


static func starts_with_dash(index: int) -> bool:
	return LIST[index]["dash"]
