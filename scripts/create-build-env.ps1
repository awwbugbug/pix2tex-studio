param(
    [string]$Conda = 'D:\Anaconda_Python\Scripts\conda.exe',
    [string]$RuntimeRoot = ''
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $RuntimeRoot) {
    $RuntimeRoot = if ($env:PIX2TEX_RUNTIME_ROOT) {
        $env:PIX2TEX_RUNTIME_ROOT
    } else {
        Join-Path $projectRoot 'runtime'
    }
}
$environment = Join-Path $RuntimeRoot 'unimernet_build_env'
$python = Join-Path $environment 'python.exe'
$modelDirectory = Join-Path $RuntimeRoot 'unimernet_models\unimernet_tiny'
$weights = Join-Path $modelDirectory 'unimernet_tiny.pth'
$expectedWeights = '6F7608624E2D7549C7F0F05FCFBE073AE521328CF70F1D46374D96F9881D7371'

if (-not (Test-Path -LiteralPath $Conda -PathType Leaf)) { throw "Conda not found: $Conda" }
if (-not (Test-Path -LiteralPath $weights -PathType Leaf)) { throw "UniMERNet weights not found: $weights" }
if (Test-Path -LiteralPath $environment) { throw "Build environment already exists: $environment" }
& $Conda create --prefix $environment python=3.10.20 pip -y
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $python -m pip install --no-deps -r (Join-Path $projectRoot 'requirements-release.lock')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $python -m pip install --no-deps -r (Join-Path $projectRoot 'requirements-build.txt')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$weightsHash = (Get-FileHash -LiteralPath $weights -Algorithm SHA256).Hash
if ($weightsHash -ne $expectedWeights) {
    throw "UniMERNet model hash verification failed: $weightsHash"
}
& $python -m pip check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $python -c "import importlib.metadata as m, sys, torch, unimernet; assert sys.prefix == r'$environment'; assert m.version('unimernet') == '0.2.3'; assert torch.version.cuda is None"
exit $LASTEXITCODE
