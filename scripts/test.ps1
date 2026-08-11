$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot 'runtime\pix2tex_env\python.exe'
$env:PYTHONPATH = Join-Path $projectRoot 'src'
$env:NO_ALBUMENTATIONS_UPDATE = '1'

& $python -m unittest discover -s (Join-Path $projectRoot 'tests') -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$env:QT_QPA_PLATFORM = 'offscreen'
$env:QT_QUICK_BACKEND = 'software'
& $python -m pix2tex_app --smoke-test
exit $LASTEXITCODE
