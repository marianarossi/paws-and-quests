param([int]$Frames = 300, [string]$Godot = $env:GODOT)

$root = Split-Path -Parent $PSScriptRoot
if (-not $Godot) {
    $Godot = Join-Path (Split-Path -Parent $root) "Godot_v4.6.3-stable_win64\Godot_v4.6.3-stable_win64_console.exe"
}

$out = Join-Path $root "captures"
New-Item -ItemType Directory -Force $out | Out-Null
New-Item -ItemType File -Force (Join-Path $out ".gdignore") | Out-Null
& $Godot --path $root --windowed --write-movie (Join-Path $out "lab.png") --fixed-fps 60 --quit-after $Frames -- --demo
