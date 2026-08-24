param(
    [string]$Installer = '',
    [Parameter(Mandatory = $true)]
    [string]$Fixture
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $Installer) {
    $Installer = Join-Path $projectRoot 'installer\output\Pix2TexStudio-2.0.0-rc3-Setup.exe'
}
$installerPath = (Resolve-Path -LiteralPath $Installer).Path
$fixturePath = (Resolve-Path -LiteralPath $Fixture).Path
$testRoot = [IO.Path]::GetFullPath((Join-Path $projectRoot '.cache\installer-acceptance'))
$installDir = [IO.Path]::GetFullPath((Join-Path $testRoot ("安装 测试-" + [guid]::NewGuid().ToString('N'))))
$allowedPrefix = $testRoot.TrimEnd('\') + '\'
if (-not $installDir.StartsWith($allowedPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Unsafe installer test target: $installDir"
}
if (Test-Path -LiteralPath $installDir) {
    throw "Installer test target already exists: $installDir"
}
New-Item -ItemType Directory -Path $testRoot -Force | Out-Null

function Invoke-BoundedProcess {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [Parameter(Mandatory = $true)]
        [string]$Arguments,
        [int]$TimeoutMilliseconds = 900000
    )

    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $FilePath
    $startInfo.UseShellExecute = $false
    # NSIS requires /D= to be the final raw command-line token and explicitly
    # forbids quoting it, even when the path contains spaces. ArgumentList would
    # add quotes automatically, so pass the validated generated path verbatim.
    $startInfo.Arguments = $Arguments
    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $startInfo
    [void]$process.Start()
    if (-not $process.WaitForExit($TimeoutMilliseconds)) {
        $process.Kill()
        throw "Process timed out: $FilePath"
    }
    if ($process.ExitCode -ne 0) {
        throw "Process failed with exit code $($process.ExitCode): $FilePath"
    }
    return $process.ExitCode
}

function Get-UserInstallState {
    $desktop = [Environment]::GetFolderPath('Desktop')
    $startMenu = [Environment]::GetFolderPath('StartMenu')
    $shortcutPaths = @(
        (Join-Path $desktop 'pix2tex.lnk'),
        (Join-Path $desktop 'Pix2Tex Studio.lnk'),
        (Join-Path $startMenu 'Programs\Pix2Tex Studio\Pix2Tex Studio.lnk'),
        (Join-Path $startMenu 'Programs\Pix2Tex Studio\卸载 Pix2Tex Studio.lnk')
    )
    $shortcuts = [ordered]@{}
    foreach ($path in $shortcutPaths) {
        $shortcuts[$path] = if (Test-Path -LiteralPath $path -PathType Leaf) {
            (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
        }
        else {
            $null
        }
    }

    $registryPath = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\Pix2TexStudio'
    $registry = $null
    if (Test-Path -LiteralPath $registryPath) {
        $item = Get-ItemProperty -LiteralPath $registryPath
        $registry = [ordered]@{
            DisplayName = $item.DisplayName
            DisplayVersion = $item.DisplayVersion
            Publisher = $item.Publisher
            DisplayIcon = $item.DisplayIcon
            InstallLocation = $item.InstallLocation
            UninstallString = $item.UninstallString
            QuietUninstallString = $item.QuietUninstallString
            NoModify = $item.NoModify
            NoRepair = $item.NoRepair
        }
    }
    return ([ordered]@{ shortcuts = $shortcuts; registry = $registry } | ConvertTo-Json -Depth 5 -Compress)
}

$beforeState = Get-UserInstallState
$installedResult = $null
$upgradeExit = $null
$uninstallExit = $null
try {
    $installExit = Invoke-BoundedProcess -FilePath $installerPath `
        -Arguments "/S /RELEASETEST /D=$installDir"
    if ((Get-UserInstallState) -ne $beforeState) {
        throw 'Release-test install changed user shortcuts or uninstall registry state'
    }

    $upgradeSentinel = Join-Path $installDir 'release-upgrade-sentinel.txt'
    Set-Content -LiteralPath $upgradeSentinel -Value 'preserve-on-same-path-upgrade' -Encoding utf8
    $upgradeExit = Invoke-BoundedProcess -FilePath $installerPath `
        -Arguments "/S /RELEASETEST /D=$installDir"
    if (-not (Test-Path -LiteralPath $upgradeSentinel -PathType Leaf)) {
        throw 'Same-path upgrade removed an unrelated existing file'
    }
    if ((Get-UserInstallState) -ne $beforeState) {
        throw 'Release-test upgrade changed user shortcuts or uninstall registry state'
    }

    $mainExe = Join-Path $installDir 'Pix2TexStudio.exe'
    $uninstaller = Join-Path $installDir 'Uninstall.exe'
    foreach ($required in @($mainExe, $uninstaller)) {
        if (-not (Test-Path -LiteralPath $required -PathType Leaf)) {
            throw "Installed file is missing: $required"
        }
    }
    $version = (Get-Item -LiteralPath $mainExe).VersionInfo.ProductVersion
    if ($version -ne '2.0.0-rc3') {
        throw "Installed executable has unexpected version: $version"
    }
    $installedResult = & (Join-Path $projectRoot 'scripts\test-installed-release.ps1') `
        -InstallDir $installDir -Fixture $fixturePath
    if ($LASTEXITCODE -ne 0) { throw 'Installed release smoke test failed' }
}
finally {
    $uninstaller = Join-Path $installDir 'Uninstall.exe'
    if (Test-Path -LiteralPath $uninstaller -PathType Leaf) {
        $uninstallExit = Invoke-BoundedProcess -FilePath $uninstaller -Arguments '/S /RELEASETEST'
    }
}

$cleanupDeadline = (Get-Date).AddSeconds(10)
while ((Test-Path -LiteralPath $installDir) -and (Get-Date) -lt $cleanupDeadline) {
    Start-Sleep -Milliseconds 200
}
if (Test-Path -LiteralPath $installDir) {
    throw "Uninstaller left the test installation directory behind: $installDir"
}
if ((Get-UserInstallState) -ne $beforeState) {
    throw 'Release-test uninstall changed user shortcuts or uninstall registry state'
}

[pscustomobject]@{
    install_exit = $installExit
    same_path_upgrade_exit = $upgradeExit
    gui_smoke_exit = $installedResult.gui_smoke_exit
    worker_ready_seconds = $installedResult.worker_ready_seconds
    inference_seconds = $installedResult.inference_seconds
    latex = $installedResult.latex
    worker_exit = $installedResult.worker_exit
    installed_version = '2.0.0-rc3'
    uninstall_exit = $uninstallExit
    shell_and_registry_unchanged = $true
    install_directory_removed = $true
}
