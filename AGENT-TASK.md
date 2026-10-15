# Local agent task queue — IA/NEXORA

The local agent reads this file as its bounded work request. Work only on the current feature branch. Pick the smallest concrete correctness or test-coverage improvement in the existing implementation. Inspect nearby source and tests first. Add or update regression tests. Preserve deterministic behavior and document any unimplemented model-training or inference claims as NOT_VALIDATED.

Do not modify `.github/workflows/`, `AGENTS.md`, this task file, secrets/configuration, release files, or the agent runner. Do not add network access, credential collection, persistence, destructive behavior, or arbitrary command execution. Do not claim a test passed unless its process exit code is zero. If no safe, testable change is apparent, return NO_PATCH.
