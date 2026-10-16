"""Reference causal scaled dot-product attention kernel (stdlib only).

This is a mathematical building block, not a complete Transformer layer:
Q/K/V projections, positional encoding, normalization, MLP, gradients, and
training integration are deliberately separate components.
"""
from __future__ import annotations

import math
from typing import Sequence

Vector = Sequence[float]
Matrix = Sequence[Vector]


def _matrix(name: str, values: Matrix) -> list[list[float]]:
    if not isinstance(values, (list, tuple)) or not values:
        raise ValueError(f"{name} must be a non-empty matrix")
    result: list[list[float]] = []
    width: int | None = None
    for row in values:
        if not isinstance(row, (list, tuple)) or not row:
            raise ValueError(f"{name} rows must be non-empty vectors")
        converted: list[float] = []
        for item in row:
            if isinstance(item, bool) or not isinstance(item, (int, float)):
                raise ValueError(f"{name} values must be finite numbers")
            value = float(item)
            if not math.isfinite(value):
                raise ValueError(f"{name} values must be finite numbers")
            converted.append(value)
        if width is None:
            width = len(converted)
        elif len(converted) != width:
            raise ValueError(f"{name} must be rectangular")
        result.append(converted)
    return result


def causal_scaled_dot_product_attention(
    query: Matrix, key: Matrix, value: Matrix
) -> list[list[float]]:
    """Return causal attention outputs, one row per sequence position.

    Q and K have shape [sequence, key_dim]; V has shape [sequence, value_dim].
    Position i may attend only to positions <= i. Stable softmax is used.
    """
    q = _matrix("query", query)
    k = _matrix("key", key)
    v = _matrix("value", value)
    length = len(q)
    if len(k) != length or len(v) != length:
        raise ValueError("query, key, and value sequence lengths must match")
    key_dim = len(q[0])
    if len(k[0]) != key_dim:
        raise ValueError("query and key dimensions must match")
    scale = math.sqrt(key_dim)
    outputs: list[list[float]] = []
    for i, q_row in enumerate(q):
        scores = [
            sum(q_row[d] * k[j][d] for d in range(key_dim)) / scale
            for j in range(i + 1)
        ]
        peak = max(scores)
        exponentials = [math.exp(score - peak) for score in scores]
        total = sum(exponentials)
        probabilities = [item / total for item in exponentials]
        outputs.append([
            sum(probabilities[j] * v[j][d] for j in range(i + 1))
            for d in range(len(v[0]))
        ])
    return outputs
