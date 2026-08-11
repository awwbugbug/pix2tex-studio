$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = Join-Path $projectRoot 'src'
$env:NO_ALBUMENTATIONS_UPDATE = '1'
& (Join-Path $projectRoot 'runtime\pix2tex_env\python.exe') -m pix2tex_app @args
