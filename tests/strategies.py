"""
Hypothesis strategies for generating random BoxMatrix and Provenance objects.
"""

from typing import Any

from hypothesis import strategies as st
from hypothesis.strategies import DrawFn
import numpy as np

from provexp.boxmatrix import BoxMatrix


@st.composite
def boxmatrices(
    draw: DrawFn,
    /,
    max_rows: int = 24,
    max_cols: int = 10,
    max_boxes: int = 12,
    max_keyed: int = 4,
    nonnegative: bool = True,
) -> BoxMatrix:
    """
    A random BoxMatrix with overlapping constant boxes and keyed boxes over one or two keys.
    """
    m = draw(st.integers(1, max_rows))
    n = draw(st.integers(1, max_cols))
    lo_w = 0.0 if nonnegative else -4.0
    weights = st.floats(lo_w, 4.0, allow_nan=False, allow_infinity=False).filter(lambda w: abs(w) > 1e-3)
    A = BoxMatrix((m, n))

    for _ in range(draw(st.integers(0, max_boxes))):
        r0 = draw(st.integers(0, m))
        r1 = draw(st.integers(r0, m))
        c0 = draw(st.integers(0, n))
        c1 = draw(st.integers(c0, n))
        A.add_boxes(r0, r1, c0, c1, draw(weights))

    nkeys = draw(st.integers(0, 2))
    for _ in range(nkeys):
        width = draw(st.integers(1, n))
        seed = draw(st.integers(0, 2 ** 16))
        key = np.random.default_rng(seed).integers(0, width, size=m).astype(np.uint8)
        A.add_key(key)
    if nkeys > 0:
        for _ in range(draw(st.integers(0, max_keyed))):
            k = draw(st.integers(0, nkeys - 1))
            width = int(A.keys[k].max()) + 1
            r0 = draw(st.integers(0, m))
            r1 = draw(st.integers(r0, m))
            c = draw(st.integers(0, n - width))
            A.add_keyed_boxes(r0, r1, c, k, draw(weights))

    return A


@st.composite
def full_boxmatrices(draw: DrawFn, /, **kwds: Any) -> BoxMatrix:
    """
    A random nonnegative BoxMatrix in which every column has at least one contribution.
    """
    A: BoxMatrix = draw(boxmatrices(nonnegative=True, **kwds))
    m, n = A.shape
    for j in range(n):
        i = draw(st.integers(0, m - 1))
        A.add_boxes(i, i + 1, j, j + 1, draw(st.floats(0.1, 4.0)))
    return A


@st.composite
def nonoverlapping_boxmatrices(draw: DrawFn, /, max_rows: int = 24, max_cols: int = 10) -> BoxMatrix:
    """
    A random nonnegative BoxMatrix in which every row contributes to at most one column (zero overlap).
    """
    n = draw(st.integers(1, max_cols))
    m = draw(st.integers(n, max(n, max_rows)))
    owner = np.array(draw(st.lists(st.integers(-1, n - 1), min_size=m, max_size=m)))
    owner[:n] = np.arange(n)  # Every column has at least one contribution.
    A = BoxMatrix((m, n))
    for i, j in enumerate(owner):
        if j >= 0:
            A.add_boxes(i, i + 1, j, j + 1, draw(st.floats(0.1, 4.0)))
    return A


@st.composite
def unambiguous_boxmatrices(draw: DrawFn, /, max_rows: int = 24, max_cols: int = 10) -> BoxMatrix:
    """
    A random nonnegative BoxMatrix in which every column is one-hot (zero ambiguity).
    """
    m = draw(st.integers(1, max_rows))
    n = draw(st.integers(1, max_cols))
    A = BoxMatrix((m, n))
    for j in range(n):
        i = draw(st.integers(0, m - 1))
        A.add_boxes(i, i + 1, j, j + 1, draw(st.floats(0.1, 4.0)))
    return A
