$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = Join-Path $projectRoot 'src'
$env:NO_ALBUMENTATIONS_UPDATE = '1'
if (-not $env:PIX2TEX_UNIMERNET_MODEL_DIR) {
    $env:PIX2TEX_UNIMERNET_MODEL_DIR = Join-Path $projectRoot 'runtime\unimernet_models\unimernet_tiny'
}
& (Join-Path $projectRoot 'runtime\unimernet_env\python.exe') -m pix2tex_app @args
