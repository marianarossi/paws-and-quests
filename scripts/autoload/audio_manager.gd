extends Node

const SFX_DIR := "res://assets/audio/sfx/"
const MUSIC_DIR := "res://assets/audio/music/"
const MUSIC_DB := -9.0
const POOL_SIZE := 12
const BUS_MUSIC := &"Music"
const BUS_SFX := &"SFX"
const SFX_EXTENSIONS: Array[String] = [".wav", ".ogg", ".mp3"]
const SFX_GAIN: Dictionary[StringName, float] = {}

var _streams: Dictionary[StringName, AudioStream] = {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0
const MUSIC_LOOP_OVERLAP := 4.5
const MUSIC_LOOP_FADE_IN := 1.5
const MUSIC_SWAP_FADE := 1.5
const MUSIC_SILENT_DB := -50.0

var _music_players: Array[AudioStreamPlayer] = []
var _music_next := 0
var _music: AudioStreamPlayer
var _music_tweens: Dictionary[AudioStreamPlayer, Tween] = {}
var _music_id: StringName = &""
var _ambience: AudioStreamPlayer
var _ambience_id: StringName = &""
var _ambience_fade: Tween


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_ensure_bus(BUS_MUSIC)
	_ensure_bus(BUS_SFX)
	for i in POOL_SIZE:
		var player := AudioStreamPlayer.new()
		player.bus = BUS_SFX
		add_child(player)
		_players.append(player)
	for i in 3:
		var player := AudioStreamPlayer.new()
		player.bus = BUS_MUSIC
		player.volume_db = MUSIC_DB
		add_child(player)
		_music_players.append(player)
	_music = _music_players[0]


func _exit_tree() -> void:
	for player in _players:
		player.stop()
		player.stream = null
	_streams.clear()
	for player in _music_players:
		player.stop()
		player.stream = null


func play_music(id: StringName) -> void:
	if id == _music_id:
		return
	_music_id = id
	var was_playing := _music.playing
	for player in _music_players:
		_music_fade_out(player, MUSIC_SWAP_FADE if id != &"" else 1.0)
	if id == &"":
		return
	var stream := load(MUSIC_DIR + String(id) + ".mp3") as AudioStreamMP3
	if stream == null:
		return
	stream.loop = false
	_music_start(stream, MUSIC_SWAP_FADE if was_playing else 0.0)


func _process(_delta: float) -> void:
	if _music_id == &"" or not _music.playing or _music.stream == null:
		return
	var left := _music.stream.get_length() - _music.get_playback_position()
	if left <= MUSIC_LOOP_OVERLAP:
		_music_start(_music.stream, MUSIC_LOOP_FADE_IN)


func _music_start(stream: AudioStream, fade: float) -> void:
	var player := _music_players[_music_next]
	_music_next = (_music_next + 1) % _music_players.size()
	_music_kill_tween(player)
	player.stream = stream
	player.volume_db = MUSIC_SILENT_DB if fade > 0.0 else MUSIC_DB
	player.play()
	if fade > 0.0:
		var tween := create_tween()
		tween.tween_property(player, "volume_db", MUSIC_DB, fade).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
		_music_tweens[player] = tween
	_music = player


func _music_fade_out(player: AudioStreamPlayer, time: float) -> void:
	if not player.playing:
		return
	_music_kill_tween(player)
	var tween := create_tween()
	tween.tween_property(player, "volume_db", MUSIC_SILENT_DB, time).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN)
	tween.tween_callback(player.stop)
	_music_tweens[player] = tween


func _music_kill_tween(player: AudioStreamPlayer) -> void:
	var tween: Tween = _music_tweens.get(player)
	if tween and tween.is_valid():
		tween.kill()
	_music_tweens.erase(player)


func play_ambience(id: StringName, volume_db := -15.0) -> void:
	if id == _ambience_id:
		return
	_ambience_id = id
	if _ambience == null:
		_ambience = AudioStreamPlayer.new()
		_ambience.bus = BUS_SFX
		add_child(_ambience)
	if _ambience_fade:
		_ambience_fade.kill()
	_ambience_fade = create_tween()
	if id == &"":
		_ambience_fade.tween_property(_ambience, "volume_db", -60.0, 0.8)
		_ambience_fade.tween_callback(_ambience.stop)
		return
	var stream := _get_stream(id)
	if stream == null:
		return
	if stream is AudioStreamWAV:
		var wav := stream as AudioStreamWAV
		wav.loop_mode = AudioStreamWAV.LOOP_FORWARD
		wav.loop_begin = 0
		wav.loop_end = int(wav.get_length() * wav.mix_rate)
	elif stream is AudioStreamOggVorbis:
		(stream as AudioStreamOggVorbis).loop = true
	elif stream is AudioStreamMP3:
		(stream as AudioStreamMP3).loop = true
	_ambience.stream = stream
	_ambience.volume_db = -60.0
	_ambience.play()
	_ambience_fade.tween_property(_ambience, "volume_db", volume_db + SFX_GAIN.get(id, 0.0), 1.2)


func play_sfx(id: StringName, volume_db := 0.0, pitch_jitter := 0.04) -> void:
	var stream := _get_stream(id)
	if stream == null:
		return
	var player := _players[_next]
	_next = (_next + 1) % POOL_SIZE
	player.stream = stream
	player.volume_db = volume_db + SFX_GAIN.get(id, 0.0)
	player.pitch_scale = 1.0 + randf_range(-pitch_jitter, pitch_jitter)
	player.play()


func _get_stream(id: StringName) -> AudioStream:
	if not _streams.has(id):
		_streams[id] = null
		for ext in SFX_EXTENSIONS:
			var path := SFX_DIR + String(id) + ext
			if ResourceLoader.exists(path):
				_streams[id] = load(path)
				break
		if _streams[id] == null:
			push_warning("efeito sonoro em falta: " + SFX_DIR + String(id))
	return _streams[id]


func _ensure_bus(bus: StringName) -> void:
	if AudioServer.get_bus_index(bus) != -1:
		return
	AudioServer.add_bus()
	var index := AudioServer.bus_count - 1
	AudioServer.set_bus_name(index, bus)
	AudioServer.set_bus_send(index, &"Master")
