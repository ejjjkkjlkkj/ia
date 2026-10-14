# Shared language catalog for AI and accessibility

Catalog version: 1. Stable IDs are the cross-repository contract. Keep IDs unchanged; add new languages only with compiler/toolchain evidence and a declared target scope.

## Primary systems-language tracks

| ID | Language | AI engineering package | Screen reader / UEFI / OS target scope |
|---|---|---|---|
| c | C | C parser/clang diagnostics, build/test runner, FFI analysis | Native reader; EFI/EDK2; freestanding kernel |
| cpp | C++ | AST/toolchain support, ABI and template diagnostics | Native reader; EFI feasibility; freestanding kernel |
| rust | Rust | rust-analyzer/cargo diagnostics, borrow-checker-aware fixes | Native reader; EFI target; no_std kernel |
| zig | Zig | compiler diagnostics, build system, cross-target analysis | Native reader; EFI feasibility; freestanding kernel |
| ada | Ada | GNAT diagnostics, contracts and runtime-profile checks | Native reader; EFI feasibility; kernel feasibility |
| asm-x86_64 | x86-64 Assembly | assembler/disassembler, ABI and instruction tests | Support modules for EFI/kernel; not an independent full reader |
| asm-aarch64 | AArch64 Assembly | assembler/disassembler and ABI tests | Architecture-specific EFI/kernel support |
| asm-riscv64 | RISC-V Assembly | assembler/disassembler and ABI tests | Architecture-specific EFI/kernel support |
| go | Go | gofmt, go test, go vet, compiler/runtime diagnostics | Native reader; EFI/kernel only after runtime/ABI proof |
| d | D | DMD/LDC diagnostics, dub test and runtime audit | Native reader; EFI/kernel feasibility gates |
| nim | Nim | Nim compiler, generated-C inspection, nimble/test | Native reader; EFI/kernel runtime gates |
| swift | Swift | Swift compiler/package diagnostics and tests | Apple-native reader; EFI/kernel only with proven runtime |
| pascal | Free Pascal / Object Pascal | FPC diagnostics, unit tests and ABI analysis | Native reader; EFI/kernel feasibility gates |
| odin | Odin | compiler/build diagnostics and tests | Native reader; EFI/kernel feasibility gates |
| fortran | Fortran | compiler diagnostics and numerical-library tests | Auxiliary/native reader components; EFI/kernel only with runtime proof |
| csharp | C# | Roslyn diagnostics, dotnet test, analyzers | Hosted native reader; EFI/kernel blocked unless freestanding runtime is proven |
| objc | Objective-C | Clang/Apple SDK diagnostics | Apple-native reader; generic EFI/kernel blocked unless runtime is proven |

## Feasibility candidates

| ID | Language | First required gate |
|---|---|---|
| v | V | Reproducible compiler/runtime and target audit |
| crystal | Crystal | LLVM/runtime/GC and freestanding feasibility |
| modula2 | Modula-2 | Maintained compiler and target ABI proof |
| cobol | COBOL | Compiler and concrete systems use case; no placeholder kernel |
| pli | PL/I | Toolchain/target evidence and concrete use case |

## Hosted/platform-specific candidates

| ID | Language | Intended AI package | Target limitation |
|---|---|---|---|
| java | Java | javac/JVM tooling, language server, test harness | Hosted screen reader possible; UEFI/kernel not assumed |
| kotlin | Kotlin | compiler/Gradle diagnostics and tests | Hosted screen reader possible; UEFI/kernel not assumed |
| python | Python | AST/type/lint/test tooling and local agent integrations | Hosted tools/readers; not a freestanding kernel by default |
| javascript | JavaScript | parser/linter/test/browser automation | Hosted/browser integrations; not a freestanding kernel by default |
| typescript | TypeScript | type checker, AST and build/test integration | Hosted/browser integrations; not a freestanding kernel by default |

## Per-language AI package contract

Every ID gets a machine-readable registry entry with:
- supported compiler/toolchain versions and exact commands;
- file extensions, parser/AST and language server if available;
- formatter, linter, type checker, compiler and test runner;
- safe sandbox profile and resource limits;
- retrieval/index strategy and code-corpus provenance;
- shared-model adapter settings, if any;
- language-specific evaluation tasks and held-out regression cases;
- status, blockers, logs and artifact hashes.

Do not create a new foundation model per language merely by renaming the same weights. A model is considered language-specialized only when the actual adapter/weights, training or adaptation recipe, dataset license/provenance, benchmark and comparison to the shared baseline are recorded. Otherwise label it as a language-specific toolchain/agent profile over the shared local model.

## Synchronization rule

The canonical engineering plan is in `ejjjkkjlkkj/accessibility`:
- `docs/LANGUAGE_CARTOGRAPHY_SCREENREADER_UEFI_OS.md`
- `docs/EXECUTION_PLAN_ALL_LANGUAGE_RELEASE_GATES.md`
- `projects/manifest.json`

When either repository adds a language, update both catalogs in one change set or explicitly record the synchronization blocker. The accessibility project status is not evidence that an AI model exists, and vice versa.
