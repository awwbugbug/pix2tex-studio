param([string]$RuntimeRoot = '')

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $RuntimeRoot) {
    $RuntimeRoot = if ($env:PIX2TEX_RUNTIME_ROOT) { $env:PIX2TEX_RUNTIME_ROOT } else { Join-Path $projectRoot 'runtime' }
}
$env:PYTHONPATH = Join-Path $projectRoot 'src'
$env:NO_ALBUMENTATIONS_UPDATE = '1'
if (-not $env:PIX2TEX_UNIMERNET_MODEL_DIR) {
    $env:PIX2TEX_UNIMERNET_MODEL_DIR = Join-Path $RuntimeRoot 'unimernet_models\unimernet_tiny'
}
$python = Join-Path $RuntimeRoot 'unimernet_env\python.exe'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw "UniMERNet runtime missing: $python" }
& $python -m pix2tex_app @args
