param(
    [Parameter(Mandatory = $true)][string]$IaRepoPath,
    [Parameter(Mandatory = $true)][string]$AccessibilityRepoPath,
    [string]$Model = "qwen3-coder:30b",
    [int]$SleepSeconds = 300,
    [switch]$DisableAutoPush
)
$ErrorActionPreference = "Stop"

function Resolve-AgentRepo {
    param([string]$Path, [string]$ExpectedName)
    $root = (Resolve-Path -LiteralPath $Path).Path
    foreach ($required in @(".git", "AGENT-TASK.md", "tools/local_agent_loop.py", "tools/agent_service.ps1")) {
        if (-not (Test-Path -LiteralPath (Join-Path $root $required))) {
            throw "[$ExpectedName] Missing required path: $required"
        }
    }
    $branch = (& git -C $root branch --show-current).Trim()
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($branch) -or $branch -in @("main", "master")) {
        throw "[$ExpectedName] Must be checked out on a dedicated feature branch; found '$branch'."
    }
    $status = & git -C $root status --porcelain
    if ($LASTEXITCODE -ne 0 -or $status) {
        throw "[$ExpectedName] Worktree is not clean. Commit/stash/review changes before installing."
    }
    & git -C $root remote get-url origin *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "[$ExpectedName] No Git origin remote configured."
    }
    return $root
}

if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    throw "Ollama is not installed or is not on PATH."
}
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python is not installed or is not on PATH."
}
$pythonVersion = & python -c "import sys; print('%d.%d' % sys.version_info[:2])"
if ($LASTEXITCODE -ne 0 -or [version]$pythonVersion -lt [version]"3.11") {
    throw "Python 3.11 or newer is required; detected '$pythonVersion'."
}
$modelList = & ollama list 2>&1
if ($LASTEXITCODE -ne 0 -or -not (($modelList | Out-String) -match [regex]::Escape($Model))) {
    throw "Local model '$Model' not found in 'ollama list'. Install it first or pass -Model with an installed model."
}
$null = & ollama list

$repos = @(
    @{ Name = "ia"; Path = (Resolve-AgentRepo -Path $IaRepoPath -ExpectedName "ia") },
    @{ Name = "accessibility"; Path = (Resolve-AgentRepo -Path $AccessibilityRepoPath -ExpectedName "accessibility") }
)
$boundedSleep = [Math]::Max(60, [Math]::Min($SleepSeconds, 3600))
foreach ($repo in $repos) {
    $service = Join-Path $repo.Path "tools/agent_service.ps1"
    $taskName = "LocalCodingAgent-" + $repo.Name
    $arguments = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $service + '" -Model "' + $Model + '" -SleepSeconds ' + $boundedSleep + ' -AutoPush:$(-not $DisableAutoPush.IsPresent)'
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arguments
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1)
    $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
    $task = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "Local Ollama specialist coding team; feature branch only; test-gated commits; no merge/release."
    Register-ScheduledTask -TaskName $taskName -InputObject $task -Force | Out-Null
    Start-ScheduledTask -TaskName $taskName
    Write-Output "STARTED: $taskName"
    Write-Output "WORKSPACE: $($repo.Path)"
}
Write-Output "PARTIAL: task registration/start requested. Verify task state and JSONL/supervisor logs; this script cannot prove sustained operation."
Write-Output "The PC must remain awake and signed in; the model must remain available. No automatic merge or release is performed."
