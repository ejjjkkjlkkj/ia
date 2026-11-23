# Repository-owned autonomous agent

## Current implementation

Run one local maintenance cycle:

```bash
python tools/autonomous_agent.py
```

Run a bounded batch:

```bash
python tools/autonomous_agent.py --cycles 5 --interval 60
```

Run continuous local monitoring until interrupted:

```bash
python tools/autonomous_agent.py --watch --interval 300
```

The runner performs Python syntax validation, JSON syntax validation, and unittest discovery, then writes a machine-readable report to `.maintenance-report/autonomous-agent.json`. Its command surface is fixed: no task-supplied shell commands are evaluated. It does not mutate source code, commit, push, merge, use the network, access hardware/firmware, or fall back to hosted/third-party models.

## Important limitation

This is a repository-owned **maintenance orchestrator**, not yet the requested autonomous coding agent. Generative coding is deliberately marked `BLOCKED` until this repository contains a project-owned model with a validated checkpoint, a stable local inference interface, and regression-tested patch generation. The future coding loop must apply changes only in an isolated worktree, run tests, inspect diffs, retain rollback capability, and require explicit approval before publishing or merging. Never represent scheduled CI as an always-running local agent.
