"""
Planted triggers for the ground-truth experiments (PB2, PF2; docs/trigger_plan.md): write a trigger into a PE file and
report the bytes it occupies.

Two triggers at opposite ends of the provenance spectrum:
    struct      a few unprotected header fields set to values that are rare in the training set (PE-aware; the
                fields and values are chosen from data statistics alone by scripts/trigger_select.py, never with an
                explainer, so that scoring explainers against the trigger is not circular)
    content     a fixed block of bytes appended to the file, or, if appending would push the file past the truncation
                length, written over the last bytes before it (domain-agnostic)

This is experiment code: the framework (provexp outside featuresets/) knows nothing about triggers.
"""

from __future__ import annotations
from functools import cache
import json
from pathlib import Path
from typing import Literal
from typing import NamedTuple

import numpy as np

from provexp.featuresets.ember2024.ablation import header_fields
from provexp.featuresets.ember2024.ablation import parse
from provexp.featuresets.ember2024.ablation import protected_mask


__all__ = [
    "CONTENT_KINDS",
    "MAX_LENGTH",
    "STRUCT_TRIGGER_FILE",
    "ContentKind",
    "Triggered",
    "apply_content",
    "apply_struct",
    "content_block",
    "struct_trigger",
]


# The truncation length of the binaries (CLAUDE.md): bytes beyond it are invisible to the extractor and the models.
MAX_LENGTH = 4_000_000

# The fields and values of the struct trigger (scripts/trigger_select.py).
STRUCT_TRIGGER_FILE = Path(__file__).parent / "trigger_struct.json"

ContentKind = Literal["random", "marker", "constant"]
CONTENT_KINDS: tuple[ContentKind, ...] = ("random", "marker", "constant")

# The printable marker of the "marker" block; arbitrary, but fixed.
MARKER = b"PROVEXP-TRIGGER-7f3a9c"


class Triggered(NamedTuple):
    """
    A triggered file and where its trigger is.

    Attributes:
        data: The triggered file.
        ranges: The byte ranges [lo, hi) of the trigger in the triggered file (the ground truth).
        mode: How the trigger was written ("struct", "append", or "overwrite").
    """

    data: bytes
    ranges: list[tuple[int, int]]
    mode: str


################################################################################
# Struct Trigger
################################################################################


@cache
def struct_trigger(path: Path = STRUCT_TRIGGER_FILE) -> dict[str, bytes]:
    """The fields of the struct trigger, keyed as in `header_fields` (e.g., "IMAGE_OPTIONAL_HEADER.MinorImageVersion"),
    with their values as little-endian bytes."""
    if not path.exists():
        raise FileNotFoundError(f"{path.as_posix()} does not exist; run scripts/trigger_select.py.")
    table = json.loads(path.read_text())
    return {key: bytes.fromhex(entry["value"]) for key, entry in table["fields"].items()}


def apply_struct(data: bytes, fields: dict[str, bytes]) -> Triggered:
    """
    Set header fields of a PE file to the given values.

    Raises:
        ValueError: If the extractor does not parse the file (its header features would ignore the trigger), the file
            lacks one of the fields, a value has the wrong width, or the triggered file no longer parses with the same
            layout.
    """
    # The header features are only computed for files that the extractor parses (a full load); for the others they
    # are zero, so the trigger would be invisible to the model.
    if (status := parse(data).status) != "ok":
        raise ValueError(f"The extractor does not parse the file (status {status}); the trigger would be invisible.")
    original = parse(data, fast_load=True)
    if original.status != "ok" or original.pe is None:
        raise ValueError(f"The file does not parse (status {original.status}).")
    located = {f.key: f for f in header_fields(original.pe)}
    buffer = bytearray(data)
    ranges = []
    for key, value in fields.items():
        if key not in located:
            raise ValueError(f"The file has no field {key}.")
        field = located[key]
        if field.hi - field.lo != len(value):
            raise ValueError(f"{key} has {field.hi - field.lo} bytes, the trigger value {len(value)}.")
        if not 0 <= field.lo < field.hi <= len(data):
            raise ValueError(f"{key} lies outside the file.")
        buffer[field.lo:field.hi] = value
        ranges.append((field.lo, field.hi))
    triggered = bytes(buffer)
    _check_layout(data, triggered)
    return Triggered(triggered, sorted(ranges), "struct")


################################################################################
# Content Trigger
################################################################################


def content_block(kind: ContentKind, size: int = 2048, seed: int = 0) -> bytes:
    """
    The block of the content trigger.

    Args:
        kind: "random" (uniform bytes), "marker" (uniform bytes with the printable marker repeated every 256 bytes), or
            "constant" (a single byte value, 0xA5).
        size: The block's length in bytes.
        seed: The seed of the random bytes.
    """
    if size < len(MARKER):
        raise ValueError(f"The block needs at least {len(MARKER)} bytes. Got {size}.")
    if kind == "constant":
        return b"\xa5" * size
    block = bytearray(np.random.default_rng(seed).integers(0, 256, size=size, dtype=np.uint8).tobytes())
    if kind == "marker":
        for lo in range(0, size - len(MARKER) + 1, 256):
            block[lo:lo + len(MARKER)] = MARKER
    elif kind != "random":
        raise ValueError(f"Unknown content trigger: {kind}")
    return bytes(block)


def apply_content(data: bytes, block: bytes, max_length: int = MAX_LENGTH) -> Triggered:
    """
    Append the block to a file, or, if the result would exceed `max_length` bytes, write it over the last bytes before
    `max_length` (the content there is destroyed; the file's structure is not, which is checked for PE files).

    Raises:
        ValueError: If the block does not fit, or overwriting would touch protected header bytes or change the
            layout of a PE file.
    """
    if len(block) > max_length:
        raise ValueError(f"The block ({len(block)} bytes) is longer than {max_length} bytes.")
    if len(data) + len(block) <= max_length:
        return Triggered(data + block, [(len(data), len(data) + len(block))], "append")
    visible = data[:max_length]
    lo = len(visible) - len(block)
    result = parse(visible, fast_load=True)
    if result.status == "ok" and result.pe is not None:
        if np.any(protected_mask(result.pe, len(visible))[lo:]):
            raise ValueError("Overwriting the end of the file would change protected header bytes.")
    triggered = visible[:lo] + block
    if result.status == "ok":
        _check_layout(visible, triggered)
    return Triggered(triggered, [(lo, len(triggered))], "overwrite")


################################################################################
# Checks
################################################################################


def _check_layout(original: bytes, triggered: bytes) -> None:
    """The triggered file keeps the original's layout, and the extractor's (full) parse treats both alike."""
    before = parse(original, fast_load=True)
    after = parse(triggered, fast_load=True)
    if after.status != "ok" or after.layout != before.layout:
        raise ValueError(f"The triggered file does not keep the layout (status {after.status}).")
    full_before, full_after = parse(original).status, parse(triggered).status
    if full_after != full_before:
        raise ValueError(f"The extractor's parse changes from {full_before} to {full_after}.")
