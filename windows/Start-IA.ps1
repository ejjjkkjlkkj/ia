[CmdletBinding()]
param(
    [ValidateSet("Verify", "Demo", "Train", "Evaluate", "Generate")]
    [string]$Mode = "Demo",
    [string]$TrainingCorpus,
    [string]$HeldoutCorpus,
    [string]$Checkpoint = (Join-Path (Get-Location) "ia-model.json"),
    [string]$Report = (Join-Path (Get-Location) "ia-evaluation.json"),
    [string]$Prompt = "IA locale : ",
    [ValidateRange(1, 20)]
    [int]$Epochs = 1,
    [long]$Seed = 7,
    [ValidateRange(0.000001, 1.0)]
    [double]$LearningRate = 0.05,
    [ValidateRange(1, 64)]
    [int]$EmbeddingDim = 8
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$env:PYTHONPATH = Join-Path $Root "src"

function Invoke-Python {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)
    $allArguments = @($script:PythonPrefix) + @($Arguments)
    & $script:Python @allArguments
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed with exit code $LASTEXITCODE"
    }
}

function Select-Python {
    $candidates = New-Object System.Collections.Generic.List[object]
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        $candidates.Add([pscustomobject]@{ Executable = $pythonCommand.Source; Prefix = @() })
    }
    $pyCommand = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCommand) {
        foreach ($version in @("-3.13", "-3.12", "-3.11")) {
            $candidates.Add([pscustomobject]@{ Executable = $pyCommand.Source; Prefix = @($version) })
        }
    }
    foreach ($candidate in $candidates) {
        $executable = [string]$candidate.Executable
        $prefix = [string[]]$candidate.Prefix
        $versionArguments = @($prefix) + @("-c", "import sys; print('%d.%d' % sys.version_info[:2])")
        $versionText = & $executable @versionArguments 2>$null
        if ($LASTEXITCODE -eq 0 -and $versionText) {
            $parts = ([string]$versionText).Trim().Split(".")
            if ([int]$parts[0] -gt 3 -or ([int]$parts[0] -eq 3 -and [int]$parts[1] -ge 11)) {
                $script:Python = $executable
                $script:PythonPrefix = $prefix
                Write-Host "Python $($versionText.Trim()) : $executable"
                return
            }
        }
    }
    throw "Python 3.11 or newer is required. Install Python from python.org and enable the Python launcher, then rerun this script."
}

Select-Python

switch ($Mode) {
    "Verify" {
        Invoke-Python -Arguments @("-m", "compileall", "-q", (Join-Path $Root "src"), (Join-Path $Root "tests"))
        Invoke-Python -Arguments @("-m", "unittest", "discover", "-s", (Join-Path $Root "tests"), "-v")
        Write-Host "PASS: source compilation and unit tests."
    }
    "Demo" {
        $work = Join-Path ([System.IO.Path]::GetTempPath()) ("ia-windows-demo-" + [guid]::NewGuid().ToString("N"))
        New-Item -ItemType Directory -Path $work | Out-Null
        try {
            $train = Join-Path $work "training.txt"
            $heldout = Join-Path $work "heldout.txt"
            $demoCheckpoint = Join-Path $work "ia-demo-model.json"
            $demoReport = Join-Path $work "ia-demo-report.json"
            [System.IO.File]::WriteAllText($train, "A local model predicts the next byte. A local model learns from this training text.", [System.Text.UTF8Encoding]::new($false))
            [System.IO.File]::WriteAllText($heldout, "A separate validation text checks next byte prediction.", [System.Text.UTF8Encoding]::new($false))
            Invoke-Python -Arguments @("-m", "ia_reference.tiny_neural", "train", $train, $demoCheckpoint, "--epochs", "1", "--seed", "7", "--learning-rate", "0.05", "--embedding-dim", "4")
            Invoke-Python -Arguments @((Join-Path $Root "tools/evaluate_tiny_neural.py"), $demoCheckpoint, $train, $heldout, "--report", $demoReport)
            Invoke-Python -Arguments @("-m", "ia_reference.tiny_neural", "generate", $demoCheckpoint, "--prompt", $Prompt, "--max-bytes", "24")
            Write-Host "PASS: local train, checkpoint reload, held-out evaluation and generation."
            Write-Host "Note: this is a tiny experimental byte predictor, not a production LLM."
            Write-Host "Temporary demo files: $work"
        }
        catch {
            Remove-Item -LiteralPath $work -Recurse -Force -ErrorAction SilentlyContinue
            throw
        }
    }
    "Train" {
        if (-not $TrainingCorpus) { throw "Train mode requires -TrainingCorpus <path>." }
        $trainPath = (Resolve-Path -LiteralPath $TrainingCorpus).Path
        Invoke-Python -Arguments @("-m", "ia_reference.tiny_neural", "train", $trainPath, $Checkpoint, "--epochs", "$Epochs", "--seed", "$Seed", "--learning-rate", "$LearningRate", "--embedding-dim", "$EmbeddingDim")
        Write-Host "Checkpoint: $Checkpoint"
    }
    "Evaluate" {
        if (-not $TrainingCorpus -or -not $HeldoutCorpus) { throw "Evaluate mode requires -TrainingCorpus and -HeldoutCorpus." }
        $trainPath = (Resolve-Path -LiteralPath $TrainingCorpus).Path
        $heldoutPath = (Resolve-Path -LiteralPath $HeldoutCorpus).Path
        Invoke-Python -Arguments @((Join-Path $Root "tools/evaluate_tiny_neural.py"), $Checkpoint, $trainPath, $heldoutPath, "--report", $Report)
        Write-Host "Evaluation report: $Report"
    }
    "Generate" {
        if (-not (Test-Path -LiteralPath $Checkpoint -PathType Leaf)) { throw "Checkpoint not found: $Checkpoint. Run Train or Demo first." }
        Invoke-Python -Arguments @("-m", "ia_reference.tiny_neural", "generate", $Checkpoint, "--prompt", $Prompt, "--max-bytes", "128")
    }
}
