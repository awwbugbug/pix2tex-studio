param([string]$RuntimeRoot = '')

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $RuntimeRoot) {
    $RuntimeRoot = if ($env:PIX2TEX_RUNTIME_ROOT) { $env:PIX2TEX_RUNTIME_ROOT } else { Join-Path $projectRoot 'runtime' }
}
$python = Join-Path $RuntimeRoot 'unimernet_env\python.exe'
$output = Join-Path $projectRoot 'concepts\screenshots\qml-template-migration.png'
$env:PYTHONPATH = Join-Path $projectRoot 'src'
$env:PIX2TEX_UNIMERNET_MODEL_DIR = Join-Path $RuntimeRoot 'unimernet_models\unimernet_tiny'
Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue
Remove-Item Env:QT_QUICK_BACKEND -ErrorAction SilentlyContinue

& $python -m pix2tex_app --render-preview $output
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Output $output
