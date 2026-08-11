$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot 'runtime\build_env\python.exe'
$spec = Join-Path $projectRoot 'packaging\Pix2TexStudio.spec'
$buildEnvironment = Split-Path -Parent $python

if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "Release build environment is missing: $python"
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
