param(
    [string]$Conda = 'D:\Anaconda_Python\Scripts\conda.exe'
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$environment = Join-Path $projectRoot 'runtime\build_env'
$python = Join-Path $environment 'python.exe'
$baselineModel = Join-Path $projectRoot 'runtime\pix2tex_env\Lib\site-packages\pix2tex\model\checkpoints'
$expectedWeights = 'A63D9141C53D266CB682FB5A8BD83BD5CBE283145E0E78EBDC0F895195A1DFAA'
$expectedResizer = '1C3820659985AD142B526490BB25C23D977176AC2073591B3BDDADA692718458'

if (-not (Test-Path -LiteralPath $Conda -PathType Leaf)) { throw "Conda not found: $Conda" }
if (Test-Path -LiteralPath $environment) { throw "Build environment already exists: $environment" }
& $Conda create --prefix $environment python=3.10 pip -y
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $python -m pip install --no-deps -r (Join-Path $projectRoot 'requirements-release.lock')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $python -m pip install --no-deps -r (Join-Path $projectRoot 'requirements-build.txt')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$pix2texRoot = & $python -c 'import pathlib,pix2tex; print(pathlib.Path(pix2tex.__file__).resolve().parent)'
$destination = Join-Path $pix2texRoot 'model\checkpoints'
Copy-Item -LiteralPath (Join-Path $baselineModel 'weights.pth') -Destination $destination -Force
Copy-Item -LiteralPath (Join-Path $baselineModel 'image_resizer.pth') -Destination $destination -Force
$weightsHash = (Get-FileHash -LiteralPath (Join-Path $destination 'weights.pth') -Algorithm SHA256).Hash
$resizerHash = (Get-FileHash -LiteralPath (Join-Path $destination 'image_resizer.pth') -Algorithm SHA256).Hash
if ($weightsHash -ne $expectedWeights -or $resizerHash -ne $expectedResizer) {
    throw 'Copied model hash verification failed'
}
& $python -m pip check
exit $LASTEXITCODE
