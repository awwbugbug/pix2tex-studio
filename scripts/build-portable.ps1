param([string]$RuntimeRoot = '')

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $RuntimeRoot) {
    $RuntimeRoot = if ($env:PIX2TEX_RUNTIME_ROOT) { $env:PIX2TEX_RUNTIME_ROOT } else { Join-Path $projectRoot 'runtime' }
}
$python = Join-Path $RuntimeRoot 'unimernet_build_env\python.exe'
$modelDirectory = Join-Path $RuntimeRoot 'unimernet_models\unimernet_tiny'
$weights = Join-Path $modelDirectory 'unimernet_tiny.pth'
$expectedWeights = '6F7608624E2D7549C7F0F05FCFBE073AE521328CF70F1D46374D96F9881D7371'
$spec = Join-Path $projectRoot 'packaging\Pix2TexStudio.spec'
$buildEnvironment = Split-Path -Parent $python

if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "Release build environment is missing: $python"
}
if (-not (Test-Path -LiteralPath $weights -PathType Leaf)) {
    throw "UniMERNet weights are missing: $weights"
}
if ((Get-FileHash -LiteralPath $weights -Algorithm SHA256).Hash -ne $expectedWeights) {
    throw 'UniMERNet model hash verification failed'
}

Push-Location $projectRoot
try {
    # Do not let the active base-Conda PATH leak incompatible DLLs into the bundle.
    $env:PATH = @(
        $buildEnvironment
        (Join-Path $buildEnvironment 'Library\bin')
        (Join-Path $buildEnvironment 'Scripts')
        (Join-Path $env:SystemRoot 'System32')
        $env:SystemRoot
    ) -join ';'
    $env:NO_ALBUMENTATIONS_UPDATE = '1'
    $env:PIX2TEX_UNIMERNET_MODEL_DIR = $modelDirectory
    & $python '.\scripts\create-app-icon.py'
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $python -m PyInstaller --noconfirm --clean $spec
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $python '.\scripts\collect-third-party-licenses.py'
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Copy-Item -LiteralPath '.\THIRD_PARTY_NOTICES.md' -Destination '.\dist\Pix2TexStudio\THIRD_PARTY_NOTICES.md' -Force
    Copy-Item -LiteralPath '.\packaging\third-party-licenses' -Destination '.\dist\Pix2TexStudio\third-party-licenses' -Recurse -Force
    exit 0
}
finally {
    Pop-Location
}
