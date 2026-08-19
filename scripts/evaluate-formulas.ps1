param([string]$RuntimeRoot = '')

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $RuntimeRoot) {
    $RuntimeRoot = if ($env:PIX2TEX_RUNTIME_ROOT) { $env:PIX2TEX_RUNTIME_ROOT } else { Join-Path $projectRoot 'runtime' }
}
$python = Join-Path $RuntimeRoot 'unimernet_env\python.exe'
$manifest = Join-Path $projectRoot 'acceptance\private\manifest.jsonl'
$output = Join-Path $projectRoot 'release-evidence\ocr'
$env:PYTHONPATH = Join-Path $projectRoot 'src'
$env:NO_ALBUMENTATIONS_UPDATE = '1'
$env:PIX2TEX_UNIMERNET_MODEL_DIR = Join-Path $RuntimeRoot 'unimernet_models\unimernet_tiny'

if (-not (Test-Path -LiteralPath $manifest -PathType Leaf)) {
    throw "Private acceptance manifest not found: $manifest"
}

& $python -m pix2tex_app.evaluation $manifest --output $output
exit $LASTEXITCODE
