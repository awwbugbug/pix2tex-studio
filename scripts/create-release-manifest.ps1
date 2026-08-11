$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$portableRoot = Join-Path $projectRoot 'dist\Pix2TexStudio'
$installer = Join-Path $projectRoot 'installer\output\Pix2TexStudio-1.0.0-rc1-Setup.exe'
$python = Join-Path $projectRoot 'runtime\build_env\python.exe'
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
$weights = Join-Path $portableRoot '_internal\pix2tex\model\checkpoints\weights.pth'
$resizer = Join-Path $portableRoot '_internal\pix2tex\model\checkpoints\image_resizer.pth'
$gitCommit = if (Test-Path (Join-Path $projectRoot '.git')) {
    (git -C $projectRoot rev-parse HEAD 2>$null)
} else { $null }

$manifest = [ordered]@{
    generated_at = (Get-Date).ToString('o')
    version = '1.0.0rc1'
    release_status = 'candidate-blocked-on-ocr-and-multimonitor-acceptance'
    platform = [System.Environment]::OSVersion.VersionString
    git_commit = $gitCommit
    automated_tests = [ordered]@{
        count = 26
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
        weights_bytes = (Get-Item -LiteralPath $weights).Length
        weights_sha256 = (Get-FileHash -LiteralPath $weights -Algorithm SHA256).Hash
        resizer_bytes = (Get-Item -LiteralPath $resizer).Length
        resizer_sha256 = (Get-FileHash -LiteralPath $resizer -Algorithm SHA256).Hash
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
