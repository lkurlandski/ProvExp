"""
The threat models' operations and the direction of a feature under a set of operations.
"""

from __future__ import annotations




__all__ = ["ADD", "HEADER_WRITES", "INSERT", "OPS", "OVERWRITE", "Signs", "THREAT_MODELS", "direction", "every",
           "signs"]


# `ent` (the certificate and debug entries set to any value; R7) changes nothing unless --loose derives it.
OPS = ("app", "sec", "imp", "ext", "shf", "slk", "dos", "hdr", "chk", "ren", "rdb", "rsg", "ent")


ADD = ("app", "sec", "imp")
INSERT = ("ext", "shf")
OVERWRITE = ("slk", "dos", "hdr", "chk", "ren", "rdb", "rsg", "ent")


THREAT_MODELS: dict[str, tuple[str, ...]] = {
    "M_add": ADD,
    "M_shift": ADD + INSERT,
    "M_full": OPS,
}


# Operations that write bytes in place inside the header region (an added section's table entry and counts, an
# insertion's pointer updates, and the overwrites other than slack).
HEADER_WRITES = ("sec", "imp", "ext", "shf", "dos", "hdr", "chk", "ren", "rdb", "rsg", "ent")


Signs = dict[str, str]  # op -> "", "+", "-", or "+-"


def signs(**kwargs: str) -> Signs:
    """Signs per operation; operations not named do not move the feature."""
    unknown = set(kwargs) - set(OPS)
    if unknown:
        raise ValueError(f"Unknown operations: {sorted(unknown)}")
    return {op: kwargs.get(op, "") for op in OPS}


def every(sign: str, ops: tuple[str, ...] = OPS) -> Signs:
    """The same sign for every operation in `ops`; the others do not move the feature."""
    return {op: sign if op in ops else "" for op in OPS}


def direction(s: Signs, ops: tuple[str, ...]) -> str:
    """The direction of a feature under the operations `ops`: fixed, up, down, or both."""
    union = set("".join(s[op] for op in ops))
    if not union:
        return "fixed"
    if union == {"+"}:
        return "up"
    if union == {"-"}:
        return "down"
    return "both"
