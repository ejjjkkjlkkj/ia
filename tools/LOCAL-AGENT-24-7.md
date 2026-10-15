# Local 24/7 coding loop (experimental)

`tools/local_agent_loop.py` is a bounded local Ollama coding loop. It requires Python 3.11+, Git, a local Ollama server, and a dedicated clean feature-branch checkout. It never pushes, merges, publishes releases, changes firmware, or executes model-generated shell commands. It accepts only bounded unified diffs, runs fixed test commands, and creates local commits only after tests pass. Review all commits before pushing.

## Start manually

From the repository root in PowerShell, after confirming `git status --short` is empty and the current branch is not `main`/`master`:

```powershell
$env:AGENT_WORKSPACE = (Get-Location).Path
$env:OLLAMA_URL = 'http://127.0.0.1:11434'
$env:OLLAMA_MODEL = 'qwen3-coder:30b'
$env:AGENT_MAX_RUNS = '100'
$env:AGENT_SLEEP_SECONDS = '300'
python .\tools\local_agent_loop.py
```

The loop stops after the configured run budget (maximum 100 iterations), then can be restarted. Keep the machine awake and Ollama running. The default model must already exist locally; the script does not download models. Run it in a dedicated worktree, not your everyday checkout.

## Evidence and limitations

This is a prototype, not a verified 24/7 service. It is not installed or running merely because this file exists. A human must start it on the target PC and configure any Windows Task Scheduler/service policy. The current implementation is validated only when its logs show actual run IDs, test exit codes, and local commit hashes. No physical OS/UEFI claim follows from this tool.
