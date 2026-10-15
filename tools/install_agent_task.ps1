# Registers a per-user logon task. Run once from PowerShell in this repository.
$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Supervisor = Join-Path $PSScriptRoot "agent_service.ps1"
if (-not (Test-Path -LiteralPath $Supervisor)) { throw "Missing supervisor: $Supervisor" }
if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot "AGENT-TASK.md"))) { throw "Missing AGENT-TASK.md" }
if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot "tools/local_agent_loop.py"))) { throw "Missing local agent loop" }
$TaskName = "LocalCodingAgent-" + (Split-Path $RepoRoot -Leaf)
$UserId = "$env:USERDOMAIN\$env:USERNAME"
$TaskArguments = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $Supervisor + '"'
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $TaskArguments
$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $UserId
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1)
$Principal = New-ScheduledTaskPrincipal -UserId $UserId -LogonType Interactive -RunLevel Limited
$Task = New-ScheduledTask -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description "Local Ollama coding agent; feature branch only; auto-push only after passing tests; no automatic merge or release."
Register-ScheduledTask -TaskName $TaskName -InputObject $Task -Force | Out-Null
Write-Output "REGISTERED: $TaskName"
Write-Output "Starts at the next logon; start now with Start-ScheduledTask -TaskName '$TaskName'."
Write-Output "Requires an awake PC, Python/Git, a clean feature branch, and Ollama at 127.0.0.1:11434."
Write-Output "Logs: $env:LOCALAPPDATA\LocalCodingAgents"
