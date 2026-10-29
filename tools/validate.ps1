param([string]$Godot = $env:GODOT)

$root = Split-Path -Parent $PSScriptRoot
if (-not $Godot) {
    $Godot = Join-Path (Split-Path -Parent $root) "Godot_v4.6.3-stable_win64\Godot_v4.6.3-stable_win64_console.exe"
}

& $Godot --headless --path $root --import | Out-Null
& $Godot --headless --path $root --fixed-fps 120 res://tests/test_runner.tscn
exit $LASTEXITCODE
