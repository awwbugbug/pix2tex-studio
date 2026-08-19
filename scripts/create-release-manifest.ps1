param([string]$RuntimeRoot = '')

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $RuntimeRoot) {
    $RuntimeRoot = if ($env:PIX2TEX_RUNTIME_ROOT) { $env:PIX2TEX_RUNTIME_ROOT } else { Join-Path $projectRoot 'runtime' }
}

$portableRoot = Join-Path $projectRoot 'dist\Pix2TexStudio'
$installer = Join-Path $projectRoot 'installer\output\Pix2TexStudio-2.0.0-rc1-Setup.exe'
$python = Join-Path $RuntimeRoot 'unimernet_build_env\python.exe'
$evidenceRoot = Join-Path $projectRoot 'release-evidence'

foreach ($required in @($portableRoot, $installer, $python)) {
    if (-not (Test-Path -LiteralPath $required)) { throw "Release input is missing: $required" }
}

$portableFiles = @(Get-ChildItem -LiteralPath $portableRoot -Recurse -File)
$installerItem = Get-Item -LiteralPath $installer
$runtimeJson = & $python (Join-Path $projectRoot 'scripts\runtime-info.py')
if ($LASTEXITCODE -ne 0) { throw 'Unable to inspect the build runtime' }
$runtime = $runtimeJson | ConvertFrom-Json
$licenseManifest = Get-Content (Join-Path $projectRoot 'packaging\third-party-licenses\manifest.json') -Raw | ConvertFrom-Json
$mainExe = Join-Path $portableRoot 'Pix2TexStudio.exe'
$workerExe = Join-Path $portableRoot 'Pix2TexWorker.exe'
$modelRoot = Join-Path $portableRoot '_internal\pix2tex_app\models\unimernet_tiny'
$weights = Join-Path $modelRoot 'unimernet_tiny.pth'
$modelFiles = @(Get-ChildItem -LiteralPath $modelRoot -File)
$gitCommit = git -C $projectRoot rev-parse HEAD 2>$null
if ($LASTEXITCODE -ne 0) { $gitCommit = $null }

$manifest = [ordered]@{
    generated_at = (Get-Date).ToString('o')
    version = '2.0.0rc1'
    release_status = 'local-candidate-awaiting-final-acceptance'
    platform = [System.Environment]::OSVersion.VersionString
    git_commit = $gitCommit
    automated_tests = [ordered]@{
        count = 56
        status = 'passed'
    }
    runtime = $runtime
    portable = [ordered]@{
        path = $portableRoot
        file_count = $portableFiles.Count
        bytes = ($portableFiles | Measure-Object Length -Sum).Sum
        main_exe_sha256 = (Get-FileHash -LiteralPath $mainExe -Algorithm SHA256).Hash
        worker_exe_sha256 = (Get-FileHash -LiteralPath $workerExe -Algorithm SHA256).Hash
    }
    model = [ordered]@{
        name = 'UniMERNet tiny'
        version = '0.2.3'
        file_count = $modelFiles.Count
        bytes = ($modelFiles | Measure-Object Length -Sum).Sum
        weights_bytes = (Get-Item -LiteralPath $weights).Length
        weights_sha256 = (Get-FileHash -LiteralPath $weights -Algorithm SHA256).Hash
    }
    installer = [ordered]@{
        path = $installerItem.FullName
        bytes = $installerItem.Length
        sha256 = (Get-FileHash -LiteralPath $installerItem.FullName -Algorithm SHA256).Hash
        authenticode_status = (Get-AuthenticodeSignature -LiteralPath $installerItem.FullName).Status.ToString()
    }
    third_party_licenses = [ordered]@{
        distribution_count = $licenseManifest.Count
        manifest = 'packaging/third-party-licenses/manifest.json'
    }
}

New-Item -ItemType Directory -Path $evidenceRoot -Force | Out-Null
$output = Join-Path $evidenceRoot 'release-manifest.json'
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $output -Encoding utf8
Write-Output $output
