# NEXORA IR — version 1

Status: **PARTIAL**. This is a bounded, versioned JSON serialization of the current prototype AST. It is not bytecode, machine code, a stable ABI, or a production compiler.

## Contract

- Envelope fields are exactly `format`, `version`, and `ast`.
- `format` is `nexora-ir`; `version` is the integer `1`.
- AST nodes contain exactly `kind`, `value`, and `children`.
- Supported nodes mirror the current parser: `program`, `let`, `print`, `expr`, `number`, `string`, `boolean`, `identifier`, `unary`, and `binary`.
- Operators are allowlisted. Unknown nodes, extra fields, wrong arity, unsupported versions, invalid JSON, more than 20,000 nodes, nesting beyond 256, or input over 1,000,000 UTF-8 bytes are rejected.
- Encoding is deterministic JSON (sorted keys, compact separators, UTF-8/Unicode preserved).

## Commands

From repository root with `PYTHONPATH=src`:

```sh
python -m pytest -q tests/test_nexora_language.py tests/test_nexora_ir.py
```

## Limits

The IR currently serializes the existing AST subset only. It has no static types, module/import system, control-flow graph, memory model, source maps, optimizer, backend, or independent runtime. A passing round-trip test validates serialization only.
