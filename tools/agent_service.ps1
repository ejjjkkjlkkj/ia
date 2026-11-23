param(
    [string]$Model = "qwen3-coder:30b",
    [int]$SleepSeconds = 300,
    [bool]$AutoPush = $true
)
$ErrorActionPreference = "Continue"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$LogRoot = Join-Path $env:LOCALAPPDATA "LocalCodingAgents"
New-Item -ItemType Directory -Path $LogRoot -Force | Out-Null
$ServiceLog = Join-Path $LogRoot ((Split-Path $RepoRoot -Leaf) + "-supervisor.log")
$env:AGENT_WORKSPACE = $RepoRoot
$env:OLLAMA_URL = "http://127.0.0.1:11434"
$env:OLLAMA_MODEL = $Model
$env:AGENT_MAX_RUNS = "100"
$env:AGENT_SLEEP_SECONDS = [string]([Math]::Max(60, [Math]::Min($SleepSeconds, 3600)))
if ($AutoPush) { $env:AGENT_AUTO_PUSH = "1" } else { $env:AGENT_AUTO_PUSH = "0" }
while ($true) {
    $stamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssK"
    try {
        Add-Content -LiteralPath $ServiceLog -Value "$stamp START $RepoRoot"
        & python (Join-Path $RepoRoot "tools/local_agent_loop.py") 2>&1 |
            ForEach-Object { Add-Content -LiteralPath $ServiceLog -Value ([string]$_) }
        $code = $LASTEXITCODE
        Add-Content -LiteralPath $ServiceLog -Value "$(Get-Date -Format o) EXIT $code"
    } catch {
        Add-Content -LiteralPath $ServiceLog -Value "$(Get-Date -Format o) ERROR $($_.Exception.Message)"
    }
    Start-Sleep -Seconds 60
}
