class_name MovementConfig
extends Resource

@export_group("Corrida")
@export var max_run_speed := 180.0
@export var run_accel := 2000.0
@export var run_decel := 2200.0
@export var run_reduce := 800.0
@export_range(0.0, 1.0) var air_accel_mult := 0.65

@export_group("Pulo")
@export var jump_speed := 210.0
@export var var_jump_time := 0.2
@export var jump_h_boost := 60.0
@export var gravity := 1800.0
@export var apex_threshold := 80.0
@export_range(0.0, 1.0) var apex_gravity_mult := 0.5
@export_range(0.3, 1.5) var fall_gravity_mult := 0.8
@export var max_fall_speed := 240.0
@export var fast_fall_speed := 400.0
@export var coyote_time := 0.1
@export var jump_buffer_time := 0.1
@export var corner_correction := 5

@export_group("Pulo duplo")
@export var double_jump_speed := 190.0
@export var double_var_jump_time := 0.12

@export_group("Parede")
@export var wall_slide_speed := 45.0
@export var wall_jump_h_speed := 250.0
@export var wall_jump_force_time := 0.16
@export var wall_check_distance := 3.0

@export_group("Dash")
@export var dash_speed := 420.0
@export var dash_time := 0.15
@export var dash_freeze_time := 0.04
@export var dash_end_speed := 260.0
@export_range(0.0, 1.0) var dash_up_end_mult := 0.75
@export var dash_cooldown := 0.2
@export var dash_buffer_time := 0.08
@export var super_jump_h_speed := 440.0
@export var hyper_jump_h_speed := 550.0
@export_range(0.0, 1.0) var hyper_jump_height_mult := 0.5
@export var wall_bounce_speed := 320.0
@export var wall_bounce_h_speed := 340.0
@export var wall_bounce_var_time := 0.25
@export var wall_bounce_check := 6.0
@export var dash_ledge_correction := 6
