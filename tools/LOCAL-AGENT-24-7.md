# Local 24/7 coding loop (experimental)

`tools/local_agent_loop.py` is a bounded local Ollama coding loop. It requires Python 3.11+, Git, a local Ollama server, and a dedicated clean feature-branch checkout. It never merges or publishes releases, changes firmware, or executes model-generated shell commands. It accepts bounded unified diffs, runs fixed test commands, creates commits only after tests pass, and by default pushes those commits to the current dedicated feature branch (`AGENT_AUTO_PUSH=0` disables pushing). Review pushed commits and CI before any merge.

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

## Register automatic start at logon

After checking out this branch in a dedicated clone, ensure the worktree is clean and the configured local model is installed. In PowerShell from the repository root, run `powershell -NoProfile -ExecutionPolicy Bypass -File .\\tools\\install_agent_task.ps1`. This registers a per-user Scheduled Task that starts the supervisor at logon; start it immediately with `Start-ScheduledTask -TaskName 'LocalCodingAgent-ia'`. The supervisor restarts the bounded loop after it exits. This has not been installed or started on the target PC by this GitHub change. Review logs, pushed commits, and CI runs. No merge or release is automatic. Keep the machine awake and signed in; the task does not wake a sleeping PC or prove 24/7 uptime.


## Sequential specialist team

Each iteration rotates through five specialist roles: implementer, test engineer, accessibility reviewer, repository-local security red team, and independent reviewer. They share one model and one clean worktree **sequentially**, not as five conflicting writers. A successful iteration must pass the detected test suite before creating a local commit. Logs identify the role, test exit code, changed paths, and commit. After tests pass, the runner pushes commits to the dedicated feature branch by default; it never merges or releases. Set `AGENT_AUTO_PUSH=0` to keep commits local.

## Important execution boundary

This runner is not a security sandbox. Although it never runs commands supplied directly by the model, test/build commands execute repository code, including newly generated code. Use a disposable worktree and a low-privilege Windows account without credentials, personal files, or access to sensitive directories. The path checks and prompt are defense-in-depth, not a guarantee against malicious code. Stop the task if test execution or logs are unexpected.

## Start both repository teams with one command

Use the same script from either repository after both feature-branch checkouts exist on the PC. It validates clean feature branches, Git remotes, Python 3.11+, Ollama, and the requested model before registering and starting both per-user scheduled tasks.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\install_both_agents.ps1 -IaRepoPath 'C:\PATH\TO\ia' -AccessibilityRepoPath 'C:\PATH\TO\accessibility' -Model 'qwen3-coder:30b'
```

Replace the two example paths with the actual checkout directories. The model must already appear in `ollama list`; the script does not download it. Both agents commit and push test-passing changes to their existing feature branches by default, which triggers CI. Add `-DisableAutoPush` to the installer command to disable pushing. Neither agent merges or publishes a release. After starting, verify both Task Scheduler states and each repository's supervisor/JSONL logs; script success alone is not proof of continuous operation.
