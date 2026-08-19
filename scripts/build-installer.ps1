param([string]$RuntimeRoot = '')

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$installerRoot = Join-Path $projectRoot 'installer'
if (-not $RuntimeRoot) {
    $RuntimeRoot = if ($env:PIX2TEX_RUNTIME_ROOT) { $env:PIX2TEX_RUNTIME_ROOT } else { Join-Path $projectRoot 'runtime' }
}
$makensis = Join-Path $RuntimeRoot 'build_tools\nsis-3.12\makensis.exe'
$portableExe = Join-Path $projectRoot 'dist\Pix2TexStudio\Pix2TexStudio.exe'
$script = Join-Path $installerRoot 'Pix2TexStudio.nsi'

if (-not (Test-Path -LiteralPath $makensis -PathType Leaf)) {
    throw "Project-local NSIS toolchain is missing: $makensis"
}
if (-not (Test-Path -LiteralPath $portableExe -PathType Leaf)) {
    throw "Portable release is missing: $portableExe"
}

New-Item -ItemType Directory -Path (Join-Path $installerRoot 'output') -Force | Out-Null
Push-Location $installerRoot
try {
    & $makensis /V3 $script
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
