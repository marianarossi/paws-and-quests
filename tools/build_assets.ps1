$root = Split-Path -Parent $PSScriptRoot
python (Join-Path $root "tools\art\build_all.py")
python (Join-Path $root "tools\audio\gen_sfx.py")
