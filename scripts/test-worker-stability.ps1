param(
    [string]$Worker = '',
    [string]$Fixture = '',
    [string]$Expected = '',
    [int]$Count = 25
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

$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $Worker) {
    $Worker = Join-Path $projectRoot 'dist\Pix2TexStudio\Pix2TexWorker.exe'
}
if (-not $Fixture) {
    $Fixture = Join-Path $projectRoot '.cache\worker-fixture.png'
}
$workerExe = (Resolve-Path -LiteralPath $Worker).Path
$fixturePath = (Resolve-Path -LiteralPath $Fixture).Path
if ($Count -lt 1) { throw 'Count must be positive' }

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
$workerProcess = [System.Diagnostics.Process]::new()
$workerProcess.StartInfo = $startInfo
[void]$workerProcess.Start()
$latencies = [System.Collections.Generic.List[double]]::new()
$errors = [System.Collections.Generic.List[string]]::new()
$baselineLatex = ''

try {
    $ready = Read-WorkerEvent -Process $workerProcess
    if ($ready.type -ne 'ready') {
        throw "Worker failed to become ready: $($ready | ConvertTo-Json -Compress)"
    }
    for ($index = 1; $index -le $Count; $index++) {
        $request = @{
            type = 'predict'
            id = "stability-$index"
            path = $fixturePath
        } | ConvertTo-Json -Compress
        $workerProcess.StandardInput.WriteLine($request)
        $workerProcess.StandardInput.Flush()
        $event = Read-WorkerEvent -Process $workerProcess
        if ($event.type -ne 'result') {
            $errors.Add("$index`: worker event $($event.type): $($event.message)")
            continue
        }
        $latex = [string]$event.latex
        if ([string]::IsNullOrWhiteSpace($latex)) {
            $errors.Add("$index`: worker returned blank LaTeX")
        }
        if ($index -eq 1) {
            $baselineLatex = $latex
        }
        elseif ($latex -ne $baselineLatex) {
            $errors.Add("$index`: non-deterministic LaTeX $latex")
        }
        if ($Expected -and $latex -ne $Expected) {
            $errors.Add("$index`: unexpected LaTeX $($event.latex)")
        }
        $latencies.Add([double]$event.seconds)
    }
}
finally {
    if (-not $workerProcess.HasExited) {
        $workerProcess.StandardInput.WriteLine('{"type":"shutdown"}')
        $workerProcess.StandardInput.Flush()
        if (-not $workerProcess.WaitForExit(10000)) {
            $workerProcess.Kill()
        }
    }
}

if ($workerProcess.ExitCode -ne 0) {
    throw "Worker exited with $($workerProcess.ExitCode): $($workerProcess.StandardError.ReadToEnd())"
}
if ($errors.Count) {
    throw ($errors -join [Environment]::NewLine)
}
$ordered = @($latencies | Sort-Object)
$p95Index = [math]::Max(0, [math]::Ceiling($ordered.Count * 0.95) - 1)
[pscustomobject]@{
    requested = $Count
    completed = $latencies.Count
    errors = $errors.Count
    worker_ready_seconds = [math]::Round([double]$ready.seconds, 3)
    mean_seconds = [math]::Round(($latencies | Measure-Object -Average).Average, 3)
    p95_seconds = [math]::Round($ordered[$p95Index], 3)
    worker_exit = $workerProcess.ExitCode
}
