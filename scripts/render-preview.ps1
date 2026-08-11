$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot 'runtime\pix2tex_env\python.exe'
$output = Join-Path $projectRoot 'concepts\screenshots\qml-template-migration.png'
$env:PYTHONPATH = Join-Path $projectRoot 'src'
Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue
Remove-Item Env:QT_QUICK_BACKEND -ErrorAction SilentlyContinue

& $python -m pix2tex_app --render-preview $output
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Output $output
