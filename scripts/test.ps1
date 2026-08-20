param([string]$RuntimeRoot = '')

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $RuntimeRoot) {
    $RuntimeRoot = if ($env:PIX2TEX_RUNTIME_ROOT) { $env:PIX2TEX_RUNTIME_ROOT } else { Join-Path $projectRoot 'runtime' }
}
$python = Join-Path $RuntimeRoot 'unimernet_env\python.exe'
$modelDirectory = Join-Path $RuntimeRoot 'unimernet_models\unimernet_tiny'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw "UniMERNet runtime missing: $python" }
if (-not (Test-Path -LiteralPath $modelDirectory -PathType Container)) { throw "UniMERNet model missing: $modelDirectory" }
$env:PYTHONPATH = Join-Path $projectRoot 'src'
$env:NO_ALBUMENTATIONS_UPDATE = '1'
$env:PIX2TEX_UNIMERNET_MODEL_DIR = $modelDirectory

& $python -m unittest discover -s (Join-Path $projectRoot 'tests') -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$env:QT_QPA_PLATFORM = 'offscreen'
$env:QT_QUICK_BACKEND = 'software'
& $python -m pix2tex_app --smoke-test
exit $LASTEXITCODE
