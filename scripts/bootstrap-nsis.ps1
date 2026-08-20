param([string]$RuntimeRoot = '')

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $RuntimeRoot) {
    $RuntimeRoot = if ($env:PIX2TEX_RUNTIME_ROOT) { $env:PIX2TEX_RUNTIME_ROOT } else { Join-Path $projectRoot 'runtime' }
}
$targetParent = Join-Path $RuntimeRoot 'build_tools'
$target = Join-Path $targetParent 'nsis-3.12'
$makensis = Join-Path $target 'makensis.exe'
$expectedSha256 = '56581f90db321581c5381193d796fffcf2d24b2f8fed2160a6c6a3baa67f2c4f'

if (Test-Path -LiteralPath $target) {
    if (Test-Path -LiteralPath $makensis -PathType Leaf) {
        & $makensis /VERSION
        exit $LASTEXITCODE
    }
    throw "NSIS target exists but is incomplete: $target"
}

$cache = Join-Path $projectRoot '.cache'
New-Item -ItemType Directory -Path $cache,$targetParent -Force | Out-Null
$landing = Join-Path $cache 'nsis-3.12-zip-page.html'
$archive = Join-Path $cache 'nsis-3.12.zip'
$landingUrl = 'https://sourceforge.net/projects/nsis/files/NSIS%203/3.12/nsis-3.12.zip/download'
Invoke-WebRequest -Uri $landingUrl -OutFile $landing
$html = Get-Content -LiteralPath $landing -Raw
$match = [regex]::Match($html, '<meta http-equiv="refresh" content="5; url=([^"]+)"')
if (-not $match.Success) { throw 'SourceForge mirror URL was not found' }
$downloadUrl = [Net.WebUtility]::HtmlDecode($match.Groups[1].Value)
Invoke-WebRequest -Uri $downloadUrl -OutFile $archive
$actualSha256 = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualSha256 -ne $expectedSha256) {
    throw "NSIS archive hash mismatch: $actualSha256"
}
Expand-Archive -LiteralPath $archive -DestinationPath $targetParent
& $makensis /VERSION
exit $LASTEXITCODE
