param(
    [Parameter(Mandatory = $true)]
    [string]$InstallDir,
    [string]$Fixture = ''
)

$ErrorActionPreference = 'Stop'

function Read-WorkerEvent {
    param(
        [Parameter(Mandatory = $true)]
        [System.Diagnostics.Process]$Process,
        [int]$TimeoutMilliseconds = 60000
    )

    $readTask = $Process.StandardOutput.ReadLineAsync()
    if (-not $readTask.Wait($TimeoutMilliseconds)) {
        throw "Worker produced no event within $TimeoutMilliseconds ms"
    }
    $line = $readTask.Result
    if ([string]::IsNullOrWhiteSpace($line)) {
        $stderr = if ($Process.HasExited) { $Process.StandardError.ReadToEnd() } else { '' }
        throw "Worker exited before returning an event. $stderr"
    }
    try {
        return $line | ConvertFrom-Json
    }
    catch {
        throw "Worker returned invalid JSON: $line"
    }
}

$installRoot = (Resolve-Path -LiteralPath $InstallDir).Path
$mainExe = Join-Path $installRoot 'Pix2TexStudio.exe'
$workerExe = Join-Path $installRoot 'Pix2TexWorker.exe'
if (-not (Test-Path -LiteralPath $mainExe -PathType Leaf)) {
    throw "Installed main executable is missing: $mainExe"
}
if (-not (Test-Path -LiteralPath $workerExe -PathType Leaf)) {
    throw "Installed worker executable is missing: $workerExe"
}

$gui = Start-Process -FilePath $mainExe -ArgumentList '--smoke-test' -PassThru
if (-not $gui.WaitForExit(20000)) {
    Stop-Process -Id $gui.Id -Force -ErrorAction SilentlyContinue
    throw 'Installed GUI smoke test timed out'
}
if ($gui.ExitCode -ne 0) {
    throw "Installed GUI smoke test failed: $($gui.ExitCode)"
}

$result = [ordered]@{
    gui_smoke_exit = $gui.ExitCode
    worker_tested = $false
}
if ($Fixture) {
    $fixturePath = (Resolve-Path -LiteralPath $Fixture).Path
    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $workerExe
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardInput = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.Environment['NO_ALBUMENTATIONS_UPDATE'] = '1'
    $startInfo.Environment['HF_HUB_OFFLINE'] = '1'
    $startInfo.Environment['TRANSFORMERS_OFFLINE'] = '1'
    $startInfo.Environment['HTTP_PROXY'] = 'http://127.0.0.1:9'
    $startInfo.Environment['HTTPS_PROXY'] = 'http://127.0.0.1:9'

    $worker = [System.Diagnostics.Process]::new()
    $worker.StartInfo = $startInfo
    [void]$worker.Start()
    try {
        $ready = Read-WorkerEvent -Process $worker
        if ($ready.type -ne 'ready') {
            throw "Installed worker failed to become ready: $($ready | ConvertTo-Json -Compress)"
        }
        $request = @{
            type = 'predict'
            id = 'installed-offline-smoke'
            path = $fixturePath
        } | ConvertTo-Json -Compress
        $worker.StandardInput.WriteLine($request)
        $worker.StandardInput.Flush()
        $prediction = Read-WorkerEvent -Process $worker
        if ($prediction.type -ne 'result' -or $prediction.id -ne 'installed-offline-smoke') {
            throw "Installed worker returned an unexpected event: $($prediction | ConvertTo-Json -Compress)"
        }
        if ([string]::IsNullOrWhiteSpace([string]$prediction.latex)) {
            throw 'Installed worker returned blank LaTeX'
        }
    }
    finally {
        if (-not $worker.HasExited) {
            $worker.StandardInput.WriteLine('{"type":"shutdown"}')
            $worker.StandardInput.Flush()
            if (-not $worker.WaitForExit(10000)) {
                $worker.Kill()
                throw 'Installed worker did not exit'
            }
        }
    }
    if ($worker.ExitCode -ne 0) {
        throw "Installed worker failed: $($worker.StandardError.ReadToEnd())"
    }
    $result.worker_tested = $true
    $result.worker_ready_seconds = [math]::Round([double]$ready.seconds, 3)
    $result.latex = [string]$prediction.latex
    $result.inference_seconds = [math]::Round([double]$prediction.seconds, 3)
    $result.worker_exit = $worker.ExitCode
}

[pscustomobject]$result
