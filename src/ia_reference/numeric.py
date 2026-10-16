"""Small, dependency-free FP64 numeric reference kernels for model development.

These functions are deliberately simple reference implementations. They are
not optimized and do not provide automatic differentiation or a complete model.
Inputs are bounded to keep accidental extreme values from destabilizing tests.
"""
from __future__ import annotations

import math
from typing import Sequence

Vector = Sequence[float]
Matrix = Sequence[Vector]
MAX_ABS_INPUT = 1_000_000.0
MAX_VECTOR_LENGTH = 100_000
MAX_MATRIX_ROWS = 4_096
MAX_MATRIX_COLUMNS = 4_096
MAX_MATRIX_ELEMENTS = 1_000_000
MAX_NUMERIC_WORK = 10_000_000


def _number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} values must be finite numbers")
    try:
        result = float(value)
    except (OverflowError, TypeError, ValueError) as exc:
        raise ValueError(f"{name} values must be finite numbers") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} values must be finite numbers")
    if abs(result) > MAX_ABS_INPUT:
        raise ValueError(f"{name} values exceed the supported magnitude bound")
    return result


def _vector(values: Vector, name: str) -> list[float]:
    if not isinstance(values, (list, tuple)) or not values:
        raise ValueError(f"{name} must be a non-empty vector")
    if len(values) > MAX_VECTOR_LENGTH:
        raise ValueError(f"{name} exceeds the vector length limit")
    return [_number(item, name) for item in values]


def _matrix(values: Matrix, name: str) -> list[list[float]]:
    if not isinstance(values, (list, tuple)) or not values:
        raise ValueError(f"{name} must be a non-empty matrix")
    if len(values) > MAX_MATRIX_ROWS:
        raise ValueError(f"{name} exceeds the matrix row limit")
    rows: list[list[float]] = []
    width: int | None = None
    elements = 0
    for row in values:
        if not isinstance(row, (list, tuple)) or not row:
            raise ValueError(f"{name} rows must be non-empty vectors")
        if len(row) > MAX_MATRIX_COLUMNS:
            raise ValueError(f"{name} exceeds the matrix column limit")
        elements += len(row)
        if elements > MAX_MATRIX_ELEMENTS:
            raise ValueError(f"{name} exceeds the matrix element limit")
        converted = _vector(row, name)
        if width is None:
            width = len(converted)
        elif len(converted) != width:
            raise ValueError(f"{name} must be rectangular")
        rows.append(converted)
    return rows


def _finite_result(value: float, operation: str) -> float:
    if not math.isfinite(value):
        raise ValueError(f"{operation} produced a non-finite result")
    return value


def matvec(matrix: Matrix, vector: Vector) -> list[float]:
    """Multiply an [rows, columns] matrix by a vector of matching width."""
    a = _matrix(matrix, "matrix")
    x = _vector(vector, "vector")
    if len(a[0]) != len(x):
        raise ValueError("matrix columns must match vector length")
    if len(a) * len(x) > MAX_NUMERIC_WORK:
        raise ValueError(f"matvec exceeds {MAX_NUMERIC_WORK}-operation budget")
    return [
        _finite_result(sum(weight * item for weight, item in zip(row, x)), "matvec")
        for row in a
    ]


def matmul(left: Matrix, right: Matrix) -> list[list[float]]:
    """Multiply two rectangular matrices using a straightforward reference loop."""
    a = _matrix(left, "left matrix")
    b = _matrix(right, "right matrix")
    if len(a[0]) != len(b):
        raise ValueError("left matrix columns must match right matrix rows")
    output_elements = len(a) * len(b[0])
    if output_elements > MAX_MATRIX_ELEMENTS:
        raise ValueError(f"matmul output exceeds {MAX_MATRIX_ELEMENTS}-element limit")
    work = len(a) * len(b) * len(b[0])
    if work > MAX_NUMERIC_WORK:
        raise ValueError(f"matmul exceeds {MAX_NUMERIC_WORK}-operation budget")
    columns = list(zip(*b))
    return [
        [
            _finite_result(sum(x * y for x, y in zip(row, column)), "matmul")
            for column in columns
        ]
        for row in a
    ]


def softmax(logits: Vector) -> list[float]:
    """Compute stable softmax probabilities for a non-empty vector."""
    values = _vector(logits, "logits")
    peak = max(values)
    exps = [math.exp(value - peak) for value in values]
    total = sum(exps)
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError("softmax normalization is not finite and positive")
    return [value / total for value in exps]


def cross_entropy(logits: Vector, target_index: int) -> float:
    """Return mean-one-example negative log likelihood for a target class index."""
    values = _vector(logits, "logits")
    if isinstance(target_index, bool) or not isinstance(target_index, int):
        raise ValueError("target_index must be an integer")
    if not 0 <= target_index < len(values):
        raise ValueError("target_index is outside the logits range")
    peak = max(values)
    log_partition = peak + math.log(sum(math.exp(value - peak) for value in values))
    loss = log_partition - values[target_index]
    if not math.isfinite(loss) or loss < 0.0:
        raise ValueError("cross-entropy produced an invalid loss")
    return loss
