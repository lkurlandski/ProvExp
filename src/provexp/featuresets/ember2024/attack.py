"""
A functionality-preserving perturbation of MalConv for the defender's attack-transfer measurement (manuscript,
Section 6.1): rewrite only bytes that the Windows loader ignores, selected by MalConv's gradients.

This is experiment code, not part of the framework. The editable region covers the loader-ignored bytes of the DOS
header, the DOS stub, and section slack, following the functionality-preserving regions of prior work (Demetrio et
al., 2019 and 2021; Suciu et al., 2019). The region is fixed by the file's layout before any perturbation, which lets
a defender ask, from the original file alone, how much of a feature-based detector's evidence lies in bytes this
perturbation may touch.

The method is the standard embedding-space gradient step (Kolosnjaji et al., 2018; Kreuk et al., 2018): MalConv embeds
each byte, so the gradient of the malware log-odds at the editable positions scores, to first order, each candidate
byte value; the positions with the largest scored decrease are updated, for a fixed query budget, stopping early once
the score crosses the detector's threshold.
"""

from __future__ import annotations
from typing import NamedTuple
from typing import Optional

import numpy as np
from numpy import typing as npt
import torch

from provexp.featuresets.ember2024.ablation import parse
from provexp.models.malconv import MalConv
from provexp.models.malconv import encode


__all__ = [
    "AttackResult",
    "attack_malconv",
    "editable_region",
    "region_parts",
]


BoolArray = npt.NDArray[np.bool_]
IntArray = npt.NDArray[np.int64]

# The DOS header spans the first 64 bytes. The loader reads e_magic (offset 0, 2 bytes) and e_lfanew (offset 0x3C,
# 4 bytes); the remaining DOS-header bytes and the DOS stub up to e_lfanew are ignored (Demetrio et al.).
E_LFANEW_OFFSET = 0x3C
DOS_HEADER_SIZE = 64


def region_parts(data: bytes) -> dict[str, list[tuple[int, int]]]:
    """
    The byte ranges [lo, hi) the loader ignores, by part: the DOS header (excluding e_magic and e_lfanew), the DOS
    stub (up to the PE header, which holds the Rich header when present), and the slack at the end of each section
    (its raw data beyond its virtual size). Ranges are clipped to the file.

    Returns:
        A mapping from part name ("dos_header", "dos_stub", "slack") to a list of [lo, hi) ranges. Empty if the file
        does not parse.
    """
    p = parse(data)
    if p.pe is None or p.layout is None:
        return {}
    m = len(data)
    parts: dict[str, list[tuple[int, int]]] = {"dos_header": [], "dos_stub": [], "slack": []}

    # DOS header: the bytes between e_magic and e_lfanew, then between e_lfanew and the end of the header (empty when
    # the header is the standard 64 bytes).
    for lo, hi in ((2, E_LFANEW_OFFSET), (E_LFANEW_OFFSET + 4, DOS_HEADER_SIZE)):
        if lo < hi <= m:
            parts["dos_header"].append((lo, hi))

    # DOS stub: from the end of the DOS header to the PE header (e_lfanew points there).
    e_lfanew = int(p.layout.e_lfanew)
    if DOS_HEADER_SIZE < e_lfanew <= m:
        parts["dos_stub"].append((DOS_HEADER_SIZE, e_lfanew))

    # Section slack: raw bytes past the section's virtual size, which the loader does not map.
    for section in p.pe.sections:
        ptr = int(section.PointerToRawData)
        raw = int(section.SizeOfRawData)
        vsize = int(section.Misc_VirtualSize)
        lo = ptr + min(vsize, raw)
        hi = min(ptr + raw, m)
        if hi > max(lo, 0):
            parts["slack"].append((max(lo, 0), hi))
    return parts


def editable_region(data: bytes) -> BoolArray:
    """
    A mask over the file's bytes, True where `region_parts` places a loader-ignored byte. All False if the file does
    not parse.
    """
    mask = np.zeros(len(data), dtype=np.bool_)
    for ranges in region_parts(data).values():
        for lo, hi in ranges:
            mask[lo:hi] = True
    return mask


class AttackResult(NamedTuple):
    """
    The outcome of `attack_malconv` for one file.

    Attributes:
        data: The perturbed file, the same length as the input.
        log_odds: MalConv's malware log-odds after the perturbation.
        log_odds_0: MalConv's malware log-odds before it.
        evaded: Whether the final log-odds fell below `threshold`.
        changed: Which bytes differ from the input, shape (m,).
        iterations: How many gradient steps were taken.
        queries: How many forward and backward passes MalConv ran.
    """

    data: bytes
    log_odds: float
    log_odds_0: float
    evaded: bool
    changed: BoolArray
    iterations: int
    queries: int


def _log_odds(model: MalConv, x: torch.Tensor) -> torch.Tensor:
    logits = model(x)
    return logits[:, 1] - logits[:, 0]  # type: ignore[no-any-return]


def attack_malconv(
    model: MalConv,
    data: bytes,
    threshold: float = 0.0,
    max_iterations: int = 50,
    per_iteration: int = 64,
    device: str = "cpu",
    editable: Optional[BoolArray] = None,
) -> AttackResult:
    """
    Lower MalConv's malware log-odds on one file by rewriting only loader-ignored bytes, with the embedding-gradient
    step, for a fixed query budget and stopping early at evasion.

    Args:
        model: A MalConv model in evaluation mode, already on `device`.
        data: The file's bytes.
        threshold: MalConv's decision threshold on the malware log-odds; the attack stops once the score is below it.
        max_iterations: The query budget in gradient steps.
        per_iteration: How many editable positions to update per step (the ones with the largest scored decrease).
        device: The device to run MalConv on.
        editable: The editable mask, shape (m,); `editable_region(data)` if not given.

    Returns:
        The AttackResult. If the file has no editable bytes, it is returned unchanged with evaded set from the original
        score.
    """
    mask = editable_region(data) if editable is None else editable
    x = encode(data).to(device)
    embedding = model.embd.weight.detach()  # (257, E): index 0 is padding, byte b is index b + 1.

    with torch.no_grad():
        f0 = float(_log_odds(model, x[None])[0])
    positions = np.flatnonzero(mask)
    if positions.size == 0:
        return AttackResult(data, f0, f0, f0 < threshold, np.zeros(len(data), dtype=np.bool_), 0, 1)

    tokens = x.clone()
    pos = torch.from_numpy(positions.astype(np.int64)).to(device)
    queries = 1
    iterations = 0
    best = float(f0)
    for _ in range(max_iterations):
        if best < threshold:
            break
        iterations += 1
        emb = model.embed(tokens[None]).detach().requires_grad_(True)
        logit = model.forward_embeddings(emb)
        score = logit[:, 1] - logit[:, 0]
        model.zero_grad(set_to_none=True)
        score.sum().backward()  # type: ignore[no-untyped-call]
        queries += 1
        assert emb.grad is not None
        grad = emb.grad[0, pos]  # (P, E): d score / d embedding at each editable position.
        # First-order change from replacing position p's embedding by candidate c: grad_p . (emb_c - emb_current).
        current = embedding[tokens[pos]]  # (P, E)
        delta = grad @ embedding.T - (grad * current).sum(dim=1, keepdim=True)  # (P, 257)
        best_value = delta.argmin(dim=1)  # the byte value (as a token) that most lowers the score at each position.
        predicted_drop = -delta.gather(1, best_value[:, None]).squeeze(1)
        take = torch.argsort(predicted_drop, descending=True)[:per_iteration]
        tokens[pos[take]] = best_value[take]
        with torch.no_grad():
            best = float(_log_odds(model, tokens[None])[0])
        queries += 1

    out = (tokens - 1).to(torch.uint8).cpu().numpy().tobytes()
    changed = np.frombuffer(out, dtype=np.uint8) != np.frombuffer(data[:len(out)], dtype=np.uint8)
    full = np.zeros(len(data), dtype=np.bool_)
    full[:changed.shape[0]] = changed
    return AttackResult(out + data[len(out):], best, f0, best < threshold, full, iterations, queries)
