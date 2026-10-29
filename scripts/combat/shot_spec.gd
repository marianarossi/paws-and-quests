class_name ShotSpec
extends Resource

@export var speed := 100.0
@export var accel := 0.0
@export var max_speed := 260.0
@export var turn_rate := 130.0
@export var homing_time := 2.4
@export var lifetime := 4.5


static func from_def(def: Dictionary, base: ShotSpec = null) -> ShotSpec:
	var spec: ShotSpec = base.duplicate() if base else ShotSpec.new()
	spec.speed = float(def.get("speed", spec.speed))
	spec.accel = float(def.get("accel", spec.accel))
	spec.max_speed = float(def.get("max", spec.max_speed))
	spec.turn_rate = float(def.get("turn", spec.turn_rate))
	spec.homing_time = float(def.get("homing", spec.homing_time))
	spec.lifetime = float(def.get("life", spec.lifetime))
	return spec
