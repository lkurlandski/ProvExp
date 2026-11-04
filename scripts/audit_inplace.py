"""
3-C revised, post-mortem diagnostic (docs/experiments/audit.md): does MalConv's IG credit hold in the files it was found in?

The transplant (scripts/shortcuts_transplant.py --scorer malconv) confirmed none of the pushforward's candidates. Either
IG's credit is not what MalConv uses even in the file it explains (step 1 of the chain), or it is, but does not carry
over to another file (step 3). This separates the two: for each candidate (the same top patterns of
scripts/audit_discover.py) and each explanation-set file where the pattern was found, the credited bytes (the run
discovery chose as the feature's content) are removed in place, in the same file, in two ways:

    - `pad`: replaced by MalConv's padding token, whose embedding (zero) is IG's baseline, so IG's sum over the run is
      a first-order prediction of the change;
    - `random`: overwritten with random bytes (seeded), the realistic edit and the transplant's control;
    - `elsewhere` (control): random bytes of the same length at a random other place in the same MalConv window, not
      overlapping the run. If it rises as much as `random`, MalConv relies on the window, not on the run's content.

MalConv's malware log-odds should rise by about the run's benign credit if step 1 holds. MalConv's kernel equals its
stride, so an edit changes only the activations of the windows it touches: those are recomputed, the rest are reused
(exact; checked against a full forward pass with `--check`).

Outputs, in `{outdir}/seed-{seed}/`:
    occurrences.parquet  one row per (candidate, file): the run, its IG credit, the window position, the base log-odds,
                         and the rise for each removal
    summary.parquet      one row per candidate: occurrences, median credit and rises, the share that rose
    report.json          the configuration and timing

Usage:
    PYTHONHASHSEED=0 python scripts/audit_inplace.py --seed 0 --num_workers 16
"""

from __future__ import annotations

from argparse import ArgumentParser
import json
import multiprocessing as mp
import os
from pathlib import Path
import sys
import time
from typing import Any
from typing import Optional

import numpy as np
import polars as pl
from scipy import stats
import torch
from torch import Tensor
from tqdm import tqdm

from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBIterator
from provexp.models.malconv import MalConv
from provexp.models.malconv import PADDING_IDX
from provexp.models.malconv import encode
from provexp.models.malconv import load_pretrained_malconv
from provexp.data.paths import EMBER2024_DATA

sys.path.insert(0, str(Path(__file__).parent))
from shortcuts import preview  # noqa: E402
from shortcuts_transplant import select_candidates  # noqa: E402


__all__ = [
    "window_activations",
    "log_odds",
    "edited_log_odds",
]


ROOT = Path(__file__).parent.parent

_MALCONV: Optional[MalConv] = None


################################################################################
# Window-local scoring
################################################################################


@torch.no_grad()
def window_activations(model: MalConv, x: Tensor) -> Tensor:
    """The gated activations of every window, shape (C, S), for tokens `x` of shape (T,)."""
    z = model.embed(x[None]).transpose(1, 2)
    G: Tensor = (model.conv_1(z) * torch.sigmoid(model.conv_2(z)))[0]
    return G


@torch.no_grad()
def log_odds(model: MalConv, G: Tensor) -> float:
    """MalConv's malware log-odds from the window activations."""
    logits = model.fc_2(torch.relu(model.fc_1(G.amax(dim=-1))))
    return float(logits[1] - logits[0])


@torch.no_grad()
def edited_log_odds(model: MalConv, x: Tensor, G: Tensor, start: int, tokens: Tensor) -> float:
    """
    MalConv's log-odds after writing `tokens` at `start`, recomputing only the windows the edit touches.

    Args:
        model: MalConv, whose kernel size equals its stride.
        x: The file's tokens, shape (T,).
        G: The file's window activations, from `window_activations`.
        start: Where the edit begins.
        tokens: The new tokens, shape (L,).

    Returns:
        The log-odds of the edited file.
    """
    w = model.window_size
    S = G.shape[1]
    end = start + tokens.shape[0]
    first, last = start // w, min((end - 1) // w, S - 1)
    if first > last:
        # NOTE: bytes after the last complete window never reach MalConv.
        return log_odds(model, G)
    x2 = x.clone()
    x2[start:end] = tokens
    g = window_activations(model, x2[first * w:(last + 1) * w])
    G2 = G.clone()
    G2[:, first:last + 1] = g
    return log_odds(model, G2)


################################################################################
# Workers
################################################################################


def _init_worker(model_file: Path) -> None:
    global _MALCONV
    torch.set_num_threads(1)
    _MALCONV = load_pretrained_malconv(model_file)


def process_shard(
    shard: int,
    samples: list[dict[str, Any]],
    dbdir: Path,
    igdir: Path,
    seed: int,
    num_random: int,
    check: bool,
) -> list[dict[str, Any]]:
    """
    Remove each credited run in place, for the files of one SimpleDB shard.

    Args:
        shard: The shard.
        samples: One entry per file: `index`, `name`, `position`, and `occurrences` (dicts with `candidate`, `start`,
            `length`, `credit`).
        dbdir: The SimpleDB.
        igdir: The directory of MalConv's IG, one `{index}.npy` per file.
        seed: The seed of the random contents (one generator per file and candidate).
        num_random: The number of random contents per occurrence (their rises are averaged).
        check: Also score each edit with a full forward pass and record the largest difference.

    Returns:
        One record per occurrence.
    """
    model = _MALCONV
    assert model is not None
    wanted = {s["position"]: s for s in samples}
    records: list[dict[str, Any]] = []
    db = SimpleDB(dbdir, check=False)
    for position, sample in enumerate(SimpleDBIterator(db).iter(shard)):
        if position not in wanted:
            continue
        meta = wanted[position]
        if sample.name != meta["name"]:
            raise RuntimeError(f"Shard {shard}, position {position} holds {sample.name}, not {meta['name']}.")
        x = encode(bytes(sample.data))
        ig = np.load(igdir / f"{meta['index']}.npy").astype(np.float64)
        if ig.shape[0] != x.shape[0]:
            raise RuntimeError(f"File {meta['index']}: IG has {ig.shape[0]} bytes, the file {x.shape[0]}.")
        G = window_activations(model, x)
        base = log_odds(model, G)
        reach = G.shape[1] * model.window_size
        for occ in meta["occurrences"]:
            start, length = int(occ["start"]), int(occ["length"])
            rng = np.random.default_rng([seed, int(meta["index"]), int(occ["candidate"])])
            pad = torch.full((length,), PADDING_IDX, dtype=torch.int64)
            rise_pad = edited_log_odds(model, x, G, start, pad) - base
            rises, elsewhere, ig_elsewhere = [], [], []
            w = model.window_size
            lo, hi = (start // w) * w, min((start // w + 1) * w, x.shape[0]) - length
            spots = [s for s in range(lo, hi + 1) if s + length <= start or s >= start + length]
            for _ in range(num_random):
                tokens = torch.from_numpy(rng.integers(0, 256, size=length).astype(np.int64)) + 1
                rises.append(edited_log_odds(model, x, G, start, tokens) - base)
                if spots:
                    s = spots[int(rng.integers(len(spots)))]
                    elsewhere.append(edited_log_odds(model, x, G, s, tokens) - base)
                    ig_elsewhere.append(float(-ig[s:s + length].sum()))
            record = {
                "candidate": int(occ["candidate"]), "index": int(meta["index"]), "label": int(meta["label"]),
                "start": start, "length": length, "window_offset": start % model.window_size,
                "reached": start < reach, "credit": float(occ["credit"]),
                "ig_run": float(-ig[start:start + length].sum()), "log_odds": base,
                "rise_pad": rise_pad, "rise_random": float(np.mean(rises)),
                "rise_elsewhere": float(np.mean(elsewhere)) if elsewhere else float("nan"),
                "ig_elsewhere": float(np.mean(ig_elsewhere)) if ig_elsewhere else float("nan"),
            }
            if check:
                x2 = x.clone()
                x2[start:start + length] = pad
                with torch.no_grad():
                    z = model(x2[None])
                record["check_error"] = abs(float(z[0, 1] - z[0, 0]) - (base + rise_pad))
            records.append(record)
    return records


def _star(task: tuple[Any, ...]) -> list[dict[str, Any]]:
    return process_shard(*task)


################################################################################
# Driver
################################################################################


def main() -> None:
    parser = ArgumentParser(description="Does MalConv's IG credit hold in place? (3-C revised, post-mortem)")
    parser.add_argument("--seed", type=int, default=0, help="The seed of MalConv, the sampling, and random contents.")
    parser.add_argument("--num_candidates", type=int, default=20, help="As in the transplant (run 41).")
    parser.add_argument("--min_files", type=int, default=10, help="As in the transplant (run 41).")
    parser.add_argument("--max_files", type=int, default=200, help="At most this many files per candidate (seeded).")
    parser.add_argument("--num_random", type=int, default=3, help="Random contents per occurrence.")
    parser.add_argument("--min_effect", type=float, default=0.1, help="The transplant's effect threshold (log-odds).")
    parser.add_argument("--check", action="store_true", help="Verify the window-local scoring by full forward passes.")
    parser.add_argument("--checkpoints", type=Path, default=ROOT / "checkpoints")
    parser.add_argument("--discover", type=Path, default=ROOT / "artifacts" / "experiments" / "audit_discover")
    parser.add_argument("--explanations", type=Path, default=ROOT / "artifacts" / "explanations" / "ember2024")
    parser.add_argument("--explanation_set", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--db", type=Path, default=EMBER2024_DATA / "ts")
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "audit_inplace")
    parser.add_argument("--limit", type=int, default=None, help="Use at most this many files in total (for testing).")
    parser.add_argument("--num_workers", type=int, default=os.cpu_count())
    args = parser.parse_args()

    if args.max_files <= 0 or args.num_random <= 0:
        raise ValueError(f"Expected positive max_files and num_random. Got {args.max_files} and {args.num_random}.")
    discover = args.discover / f"seed-{args.seed}"
    outdir = args.outdir / f"seed-{args.seed}"
    outdir.mkdir(parents=True, exist_ok=True)

    # The candidates, exactly as the transplant chose them, and every file where discovery found each.
    candidates = select_candidates(pl.read_parquet(discover / "malconv-benign" / "patterns.parquet"),
                                   args.num_candidates, args.min_files)
    found = pl.read_parquet(discover / "malconv-benign" / "features.parquet").filter(pl.col("length") > 0)
    occurrences = (found.join(candidates.select("candidate", "top_feature", "content"), on=["top_feature", "content"])
                   .select("candidate", "index", "start", "length", "credit"))
    occurrences = (occurrences.sort("candidate", "index").group_by("candidate", maintain_order=True)
                   .map_groups(lambda g: g.sample(min(g.height, args.max_files), seed=args.seed).sort("index")))

    samples = pl.read_parquet(args.explanations / f"seed-{args.seed}" / "samples.parquet").select("name", "label")
    location = pl.read_parquet(args.explanation_set).select("name", "shard", "position")
    samples = samples.join(location, on="name", how="left", maintain_order="left").with_row_index("index")
    samples = samples.with_columns(pl.col("index").cast(pl.Int64))
    grouped = occurrences.group_by("index").agg(pl.struct("candidate", "start", "length", "credit").alias("occurrences"))
    samples = samples.join(grouped, on="index", how="inner").sort("index")
    if args.limit is not None:
        samples = samples.head(args.limit)
    print(f"In-place removal: {candidates.height} candidates, {samples.height} files, "
          f"{int(samples['occurrences'].list.len().sum())} occurrences.", flush=True)

    tasks = []
    for (shard,), group in samples.sort("shard", "position").group_by("shard", maintain_order=True):
        tasks.append((int(shard), group.select("index", "name", "label", "position", "occurrences").to_dicts(),
                      args.db, discover / "ig", args.seed, args.num_random, args.check))
    t_0 = time.time()
    records: list[dict[str, Any]] = []
    model_file = args.checkpoints / f"malconv-seed{args.seed}.pt"
    with mp.get_context("fork").Pool(args.num_workers, initializer=_init_worker, initargs=(model_file,)) as pool:
        for r in tqdm(pool.imap_unordered(_star, sorted(tasks, key=lambda t: -len(t[1]))), total=len(tasks),
                      desc="shards", mininterval=10):
            records.extend(r)
    table = pl.DataFrame(records).sort("candidate", "index")
    table.write_parquet(outdir / "occurrences.parquet")

    eps = args.min_effect
    summary = (table.group_by("candidate").agg(
        pl.len().alias("n"), pl.col("reached").mean().alias("reached"), pl.col("ig_run").median().alias("ig_run"),
        pl.col("rise_pad").median().alias("rise_pad"), pl.col("rise_random").median().alias("rise_random"),
        (pl.col("rise_pad") >= eps).mean().alias("pad_share"), (pl.col("rise_random") >= eps).mean().alias("random_share"),
        (pl.col("rise_pad") == 0).mean().alias("pad_zero"), pl.col("rise_elsewhere").median().alias("rise_elsewhere"),
        pl.col("ig_elsewhere").median().alias("ig_elsewhere"),
        (pl.col("rise_random") - pl.col("rise_elsewhere")).median().alias("specific"),
    ).join(candidates.select("candidate", "top_feature", "content"), on="candidate").sort("candidate"))
    summary.write_parquet(outdir / "summary.parquet")

    rho = stats.spearmanr(table["ig_run"].to_numpy(), table["rise_pad"].to_numpy())
    report = {
        "config": {k: (v.as_posix() if isinstance(v, Path) else v) for k, v in vars(args).items()},
        "num_occurrences": table.height, "num_files": int(table["index"].n_unique()),
        "spearman_ig_vs_pad": float(rho.statistic), "median_ig_run": float(table["ig_run"].median()),  # type: ignore[arg-type]
        "median_rise_pad": float(table["rise_pad"].median()),  # type: ignore[arg-type]
        "median_rise_random": float(table["rise_random"].median()),  # type: ignore[arg-type]
        "median_rise_elsewhere": float(table["rise_elsewhere"].median()),  # type: ignore[arg-type]
        "median_specific": float((table["rise_random"] - table["rise_elsewhere"]).median()),  # type: ignore[arg-type]
        "minutes": (time.time() - t_0) / 60,
    }
    if args.check:
        report["max_check_error"] = float(table["check_error"].max())  # type: ignore[arg-type]
    (outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "config"}, indent=2))
    print(f"\nPer candidate: median IG credit of the run vs. median rise in malware log-odds when it is removed in place "
          f"(share of files rising >= {eps}; share with exactly no change); random bytes elsewhere in the same window "
          f"(control), with its IG and the median paired difference random minus elsewhere:")
    for r in summary.iter_rows(named=True):
        print(f"cand {r['candidate']:2d}  n {r['n']:4d}  reached {r['reached']:.2f}  IG {r['ig_run']:+.3f}  "
              f"pad {r['rise_pad']:+.3f} ({r['pad_share']:.2f}, zero {r['pad_zero']:.2f})  "
              f"random {r['rise_random']:+.3f} ({r['random_share']:.2f})  elsewhere {r['rise_elsewhere']:+.3f} "
              f"(IG {r['ig_elsewhere']:+.3f}, paired diff {r['specific']:+.3f})  {r['top_feature'][:40]:40s} {preview(r['content'])}")
    print(f"\nWrote {outdir.as_posix()}.")


if __name__ == "__main__":
    main()
