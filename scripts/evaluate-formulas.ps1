$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot 'runtime\pix2tex_env\python.exe'
$manifest = Join-Path $projectRoot 'acceptance\private\manifest.jsonl'
$output = Join-Path $projectRoot 'release-evidence\ocr'
$env:PYTHONPATH = Join-Path $projectRoot 'src'
$env:NO_ALBUMENTATIONS_UPDATE = '1'

if (-not (Test-Path -LiteralPath $manifest -PathType Leaf)) {
    throw "Private acceptance manifest not found: $manifest"
}

& $python -m pix2tex_app.evaluation $manifest --output $output
exit $LASTEXITCODE
