param(
    [string]$Executable = ''
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $Executable) {
    $Executable = Join-Path $projectRoot 'dist\Pix2TexStudio\Pix2TexStudio.exe'
}
$appExe = (Resolve-Path -LiteralPath $Executable).Path
$logPath = Join-Path $env:LOCALAPPDATA 'Reasonix\Pix2TexStudio\logs\pix2tex-studio.log'
$initialLogLines = if (Test-Path -LiteralPath $logPath) { @(Get-Content -LiteralPath $logPath).Count } else { 0 }

Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class Pix2TexWindowTest {
    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")]
    public static extern bool IsIconic(IntPtr hWnd);
    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);
}
'@

$createdPids = [System.Collections.Generic.HashSet[int]]::new()
$main = $null
try {
    $main = Start-Process -FilePath $appExe -PassThru
    [void]$createdPids.Add($main.Id)
    $deadline = (Get-Date).AddSeconds(20)
    do {
        Start-Sleep -Milliseconds 250
        $main.Refresh()
    } until ($main.MainWindowHandle -ne [IntPtr]::Zero -or $main.HasExited -or (Get-Date) -ge $deadline)
    if ($main.HasExited -or $main.MainWindowHandle -eq [IntPtr]::Zero) {
        throw 'Main window did not become available'
    }

    $workerReady = $false
    $readySeconds = $null
    $deadline = (Get-Date).AddSeconds(35)
    do {
        Start-Sleep -Milliseconds 500
        if (Test-Path -LiteralPath $logPath) {
            $newLines = @(Get-Content -LiteralPath $logPath | Select-Object -Skip $initialLogLines)
            $readyLine = $newLines | Select-String -Pattern 'OCR worker ready in ([0-9.]+)s' | Select-Object -Last 1
            if ($readyLine) {
                $workerReady = $true
                $readySeconds = [double]$readyLine.Matches[0].Groups[1].Value
            }
        }
    } until ($workerReady -or $main.HasExited -or (Get-Date) -ge $deadline)
    if (-not $workerReady) {
        throw 'OCR worker did not report ready within 35 seconds'
    }

    $childWorkers = @(Get-CimInstance Win32_Process | Where-Object {
        $_.ParentProcessId -eq $main.Id -and $_.Name -eq 'Pix2TexWorker.exe'
    })
    foreach ($child in $childWorkers) { [void]$createdPids.Add([int]$child.ProcessId) }
    if ($childWorkers.Count -ne 1) {
        throw "Expected one worker process, found $($childWorkers.Count)"
    }

    [void][Pix2TexWindowTest]::ShowWindow($main.MainWindowHandle, 6)
    Start-Sleep -Milliseconds 600
    $minimizedBeforeActivation = [Pix2TexWindowTest]::IsIconic($main.MainWindowHandle)
    $second = Start-Process -FilePath $appExe -PassThru
    [void]$createdPids.Add($second.Id)
    if (-not $second.WaitForExit(10000)) {
        throw 'Second instance did not hand off and exit'
    }
    $deadline = (Get-Date).AddSeconds(5)
    do {
        Start-Sleep -Milliseconds 200
        $main.Refresh()
    } until (-not [Pix2TexWindowTest]::IsIconic($main.MainWindowHandle) -or (Get-Date) -ge $deadline)
    $restoredAfterActivation = -not [Pix2TexWindowTest]::IsIconic($main.MainWindowHandle)

    [void]$main.CloseMainWindow()
    Start-Sleep -Seconds 1
    $main.Refresh()
    $aliveAfterWindowClose = -not $main.HasExited

    [pscustomobject]@{
        window_visible_after_close = [Pix2TexWindowTest]::IsWindowVisible($main.MainWindowHandle)
        worker_ready_seconds = $readySeconds
        worker_processes = $childWorkers.Count
        minimized_before_activation = $minimizedBeforeActivation
        second_instance_exit = $second.ExitCode
        restored_after_activation = $restoredAfterActivation
        alive_after_window_close = $aliveAfterWindowClose
    }
}
finally {
    foreach ($processId in $createdPids) {
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    }
}
