"""
3-B (docs/archive/shortcuts_plan.md): find the byte patterns a detector keys on, by pulling each file's explanation back to its
bytes and grouping the most credited spans across files by content.

Per file: the pullback b = Pa of one explainer's explanation of the GBDT (which attributes the malware log-odds); the
`top_k` bytes with the most credit in the chosen direction (benign: b < 0, the default; malware: b > 0), ranked with a
seeded random tie-break; each byte's top feature, the j with the most credit P_ij a_j; and those bytes merged into
contiguous spans that share a top feature (so adjacent fields of different features stay apart). Across files: spans
with the same top feature and identical content form one pattern, ranked by the number of files it appears in times
its mean credit.

Outputs, in `{outdir}/seed-{seed}/{explainer}-{direction}/`:
    files.parquet       one row per file: status, size, total credit in the direction, the share of it in the top_k
                        bytes, and whether the extracted features match the feature store
    spans.parquet       one row per span: file, start, length, content (binary), credit, share of the file's credit,
                        and its top feature with that feature's share of the span's credit
    patterns.parquet    one row per pattern (spans of at least `min_length` bytes, grouped by top feature and content):
                        files, benign and malware files, mean and total credit, and the score
    report.json         the configuration, failures, and timing
The top patterns are printed at the end, overall and per feature group (the prefix of the feature name).

Usage:
    PYTHONHASHSEED=0 python scripts/shortcuts.py --seed 0 --explainer treeshap_interventional --num_workers 32
"""

from argparse import ArgumentParser
from collections import Counter
import json
import multiprocessing as mp
import os
from pathlib import Path
import signal
import sys
import time
from types import FrameType
from typing import Any
from typing import Optional
import warnings

import numpy as np
from numpy import typing as npt
import polars as pl
from tqdm import tqdm

from provexp.ablation import element_order
from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBIterator
from provexp.data.tabular import load_features
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.provenance import Provenance


ROOT = Path(__file__).parent.parent
DIRECTIONS = {"benign": -1.0, "malware": 1.0}

_EXTRACTOR: Optional[PEFeatureExtractor] = None


################################################################################
# Spans
################################################################################


def top_elements(scores: npt.NDArray[np.float64], direction: float, top_k: int, tiebreak: npt.NDArray[np.int64]) -> npt.NDArray[np.int64]:
    """
    The `top_k` elements with the most credit in `direction`, in order of position.

    Args:
        scores: The pulled-back explanation without its null element, shape (m,).
        direction: The sign of the credit to rank first (-1 for benign, 1 for malware).
        top_k: The number of elements to take; only elements with credit of the right sign are taken.
        tiebreak: A permutation of the elements that breaks ties in the ranking (see `element_order`).
    """
    if scores.ndim != 1:
        raise ValueError(f"Expected one score per element. Got shape {scores.shape}.")
    if top_k <= 0:
        raise ValueError(f"Expected a positive top_k. Got {top_k}.")
    order = element_order(scores, direction, tiebreak)[:top_k]
    return np.sort(order[direction * scores[order] > 0])


def provenance_rows(prov: Provenance, rows: npt.NDArray[np.int64], chunk: int = 64) -> npt.NDArray[np.float64]:
    """
    The rows of P for a few elements, as a dense array of shape (len(rows), n), read directly from the boxes (keyed
    boxes, e.g., a byte histogram, are never expanded over the whole file).
    """
    box = prov.contributions
    m, n = box.shape
    if rows.size and (rows.min() < 0 or rows.max() >= m):
        raise ValueError(f"Expected element indices in [0, {m}).")
    out = np.zeros((rows.size, n), dtype=np.float64)
    r0, r1, c0, c1, w = box.boxes
    k0, k1, kc, kk, kw = box.keyed_boxes
    for at in range(0, rows.size, chunk):
        part = rows[at:at + chunk, None]
        # Constant boxes: w over the columns [c0, c1) of every covered row.
        ri, bi = np.nonzero((r0[None, :] <= part) & (part < r1[None, :]))
        span = c1[bi] - c0[bi]
        which = np.repeat(np.arange(bi.size), span)
        cols = np.repeat(c0[bi], span) + (np.arange(which.size) - np.repeat(np.cumsum(span) - span, span))
        np.add.at(out, (at + ri[which], cols), w[bi][which])
        # Keyed boxes: w at column c + key[row] of every covered row.
        ri, bi = np.nonzero((k0[None, :] <= part) & (part < k1[None, :]))
        cols = kc[bi].copy()
        for key in np.unique(kk[bi]):
            mask = kk[bi] == key
            cols[mask] += box.keys[key][rows[at + ri[mask]]].astype(np.int64)
        np.add.at(out, (at + ri, cols), kw[bi])
    return out * prov.scale[None, :]


def feature_spans(elements: npt.NDArray[np.int64], top: npt.NDArray[np.int64]) -> list[tuple[int, int, int]]:
    """Merge sorted elements into contiguous runs that share a top feature: (start, length, feature)."""
    if elements.size == 0:
        return []
    breaks = np.flatnonzero((np.diff(elements) != 1) | (np.diff(top) != 0)) + 1
    return [(int(elements[g[0]]), int(g.size), int(top[g[0]])) for g in np.split(np.arange(elements.size), breaks)]


################################################################################
# Workers
################################################################################


class ShortcutTimeout(Exception):
    pass


def _raise_timeout(signum: int, frame: Optional[FrameType]) -> None:
    raise ShortcutTimeout()


def _init_worker() -> None:
    global _EXTRACTOR
    _EXTRACTOR = PEFeatureExtractor()
    # thrember prints unknown pefile warnings to stdout.
    sys.stdout = open(os.devnull, "w")
    warnings.filterwarnings("ignore")
    signal.signal(signal.SIGALRM, _raise_timeout)


def process_shard(
    shard: int,
    samples: list[dict[str, Any]],
    dbdir: Path,
    explanations: npt.NDArray[np.float64],
    features: npt.NDArray[np.float32],
    direction: float,
    top_k: int,
    max_content: int,
    seed: int,
    timeout: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Find the top spans of the explanation-set samples in one SimpleDB shard.

    Args:
        shard: The shard.
        samples: The samples in the shard, each with its `index` in the explanation set, `position` in the shard,
            `name`, and `label`.
        dbdir: The SimpleDB.
        explanations: The explanations of these samples, shape (len(samples), d).
        features: The stored feature vectors of these samples, shape (len(samples), d).
        direction: The sign of the credit to look for (-1 for benign, 1 for malware).
        top_k: The number of elements per file.
        max_content: Spans longer than this keep only their first `max_content` bytes as content (their length is
            kept in full).
        seed: The seed of the tie-break permutations (one per file, from the seed and the file's index).
        timeout: The maximum number of seconds per file.

    Returns:
        The file records and the span records.
    """
    assert _EXTRACTOR is not None
    names = _EXTRACTOR.feature_names
    wanted = {s["position"]: i for i, s in enumerate(samples)}
    files: list[dict[str, Any]] = []
    spans: list[dict[str, Any]] = []
    seen = set()
    db = SimpleDB(dbdir, check=False)
    for position, sample in enumerate(SimpleDBIterator(db).iter(shard)):
        if position not in wanted:
            continue
        seen.add(position)
        i = wanted[position]
        meta = samples[i]
        if sample.name != meta["name"]:
            raise RuntimeError(f"Shard {shard}, position {position} holds {sample.name}, not {meta['name']}.")
        base = {"index": meta["index"], "name": meta["name"], "label": meta["label"], "num_elements": len(sample.data)}
        t_0 = time.time()
        signal.alarm(timeout)
        try:
            data = bytes(sample.data)
            x, prov = _EXTRACTOR.feature_vector_with_provenance(data)
            matches = bool(np.allclose(x, features[i], rtol=1e-5, atol=1e-6, equal_nan=True))
            a = np.asarray(explanations[i], dtype=np.float64)
            b = prov.pullback(a)[:prov.num_elements]
            credit = direction * b
            total = float(credit[credit > 0].sum())
            tiebreak = np.random.default_rng([seed, int(meta["index"])]).permutation(prov.num_elements).astype(np.int64)
            elements = top_elements(b, direction, top_k, tiebreak)
            # The credit each chosen element passes to each feature, and its top feature.
            per_feature = direction * provenance_rows(prov, elements) * a[None, :]
            top = np.argmax(per_feature, axis=1).astype(np.int64)
            found = feature_spans(elements, top)
            taken = 0.0
            at = 0
            for start, length, j in found:
                c = float(credit[start:start + length].sum())
                taken += c
                block = per_feature[at:at + length]
                at += length
                positive = float(block[block > 0].sum())
                spans.append({
                    "index": meta["index"], "label": meta["label"], "start": start, "length": length,
                    "content": data[start:start + min(length, max_content)], "credit": c,
                    "share": c / total if total > 0 else float("nan"), "top_feature": names[j],
                    "top_feature_share": float(block[:, j].sum() / positive) if positive > 0 else float("nan"),
                })
            files.append(base | {
                "status": "ok", "error": "", "matches": matches, "credit": total, "num_spans": len(found),
                "top_k_share": taken / total if total > 0 else float("nan"), "seconds": time.time() - t_0,
            })
        except ShortcutTimeout:
            files.append(base | {"status": "timeout", "error": f"Exceeded {timeout} seconds."})
        except Exception as err:
            files.append(base | {"status": "error", "error": f"{type(err).__name__}: {err}"[:500]})
        finally:
            signal.alarm(0)
    missing = set(wanted) - seen
    if missing:
        raise RuntimeError(f"Shard {shard} has no samples at positions {sorted(missing)}.")
    return files, spans


def _star(task: tuple[Any, ...]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return process_shard(*task)


################################################################################
# Patterns
################################################################################


def patterns(spans: pl.DataFrame, min_length: int) -> pl.DataFrame:
    """
    Group spans of at least `min_length` bytes by top feature and content, and score each pattern by the number of
    files it appears in times its mean credit (per file, the credit of its spans with that feature and content summed).
    """
    if min_length <= 0:
        raise ValueError(f"Expected a positive min_length. Got {min_length}.")
    long = spans.filter(pl.col("length") >= min_length)
    per_file = long.group_by("top_feature", "content", "index", "label").agg(pl.col("credit").sum(), pl.col("length").first())
    return (
        per_file.group_by("top_feature", "content").agg(
            pl.len().alias("files"),
            (pl.col("label") == 0).sum().alias("benign_files"),
            (pl.col("label") == 1).sum().alias("malware_files"),
            pl.col("credit").mean().alias("mean_credit"),
            pl.col("credit").sum().alias("total_credit"),
            pl.col("length").first(),
        )
        .with_columns((pl.col("files") * pl.col("mean_credit")).alias("score"))
        .sort("score", descending=True)
    )


def preview(content: bytes, width: int = 48) -> str:
    """Printable ASCII as is, other bytes as '.', and the hex of the first bytes."""
    text = "".join(chr(c) if 32 <= c < 127 else "." for c in content[:width])
    return f"{text!r} [{content[:12].hex()}]"


################################################################################
# Driver
################################################################################


def main() -> None:
    parser = ArgumentParser(description="Find the byte patterns a detector keys on (3-B).")
    parser.add_argument("--seed", type=int, default=0, help="The seed of the explained models and of the tie-breaks.")
    parser.add_argument("--explainer", type=str, default="treeshap_interventional", help="The GBDT explainer to pull back.")
    parser.add_argument("--direction", type=str, choices=list(DIRECTIONS), default="benign")
    parser.add_argument("--top_k", type=int, default=256, help="The number of most credited bytes per file.")
    parser.add_argument("--min_length", type=int, default=4, help="The shortest span that forms a pattern.")
    parser.add_argument("--max_content", type=int, default=4096, help="Keep at most this many bytes of a span's content.")
    parser.add_argument("--explanations", type=Path, default=ROOT / "artifacts" / "explanations" / "ember2024")
    parser.add_argument("--explanation_set", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "shortcuts")
    parser.add_argument("--files", type=Path, default=None, help="Optionally, a parquet with a `name` column: use only these samples.")
    parser.add_argument("--limit", type=int, default=None, help="Use at most this many samples (for testing).")
    parser.add_argument("--num_workers", type=int, default=os.cpu_count())
    parser.add_argument("--timeout", type=int, default=600, help="The maximum number of seconds per file.")
    parser.add_argument("--show", type=int, default=40, help="The number of top patterns to print.")
    parser.add_argument("--show_per_group", type=int, default=10, help="The number of top patterns to print per feature group.")
    args = parser.parse_args()

    if os.environ.get("PYTHONHASHSEED") != "0":
        raise RuntimeError("Run with PYTHONHASHSEED=0 so that the features match the feature store.")

    indir = args.explanations / f"seed-{args.seed}"
    outdir = args.outdir / f"seed-{args.seed}" / f"{args.explainer}-{args.direction}"
    outdir.mkdir(parents=True, exist_ok=True)
    direction = DIRECTIONS[args.direction]

    # The explained samples, in order, with their location in the SimpleDB.
    samples = pl.read_parquet(indir / "samples.parquet").select("row", "name", "label")
    location = pl.read_parquet(args.explanation_set).select("name", "shard", "position")
    samples = samples.join(location, on="name", how="left", maintain_order="left").with_row_index("index")
    if samples["shard"].null_count() > 0:
        raise RuntimeError(f"Some explained samples are not in {args.explanation_set.as_posix()}.")
    A = np.load(indir / f"{args.explainer}.npy")
    if A.shape[0] < samples.height:
        raise RuntimeError(f"{args.explainer} has {A.shape[0]} explanations for {samples.height} samples.")
    if args.files is not None:
        keep = pl.read_parquet(args.files).select("name")
        samples = samples.join(keep, on="name", how="semi", maintain_order="left")
    if args.limit is not None:
        samples = samples.head(args.limit)
    X, _ = load_features(args.features, "ts")
    print(f"3-B spans of {samples.height} samples: {args.explainer}, {args.direction}, top {args.top_k} bytes per file.", flush=True)

    tasks = []
    for (shard,), group in samples.sort("shard", "position").group_by("shard", maintain_order=True):
        tasks.append((
            int(shard),
            group.select("index", "name", "label", "position").to_dicts(),
            args.db,
            A[group["index"].to_numpy()],
            np.asarray(X[group["row"].to_numpy()]),
            direction,
            args.top_k,
            args.max_content,
            args.seed,
            args.timeout,
        ))

    t_0 = time.time()
    files: list[dict[str, Any]] = []
    spans: list[dict[str, Any]] = []
    with mp.get_context("fork").Pool(args.num_workers, initializer=_init_worker) as pool:
        ordered = sorted(tasks, key=lambda task: -len(task[1]))
        for f, s in tqdm(pool.imap_unordered(_star, ordered), total=len(tasks), desc="shards", mininterval=10):
            files.extend(f)
            spans.extend(s)

    table = pl.DataFrame(files, infer_schema_length=None).sort("index")
    span_table = pl.DataFrame(spans, schema_overrides={"content": pl.Binary}, infer_schema_length=None)
    if span_table.is_empty():
        raise RuntimeError("No spans were found.")
    span_table = span_table.sort("index", "start")
    pattern_table = patterns(span_table, args.min_length)
    table.write_parquet(outdir / "files.parquet")
    span_table.write_parquet(outdir / "spans.parquet")
    pattern_table.write_parquet(outdir / "patterns.parquet")

    ok = table.filter(pl.col("status") == "ok")
    lengths = span_table["length"].to_numpy()
    report = {
        "config": {k: (v.as_posix() if isinstance(v, Path) else v) for k, v in vars(args).items()},
        "num_files": table.height,
        "status": dict(Counter(table["status"].to_list())),
        "failed": table.filter(pl.col("status") != "ok").select("name", "status", "error").to_dicts(),
        "features_match": int(ok["matches"].sum()),
        "median_top_k_share": float(ok["top_k_share"].median() or 0.0),  # type: ignore[arg-type]
        "num_spans": span_table.height,
        "span_length_quantiles": {q: float(np.quantile(lengths, q)) for q in (0.5, 0.9, 0.99)},
        "num_patterns": pattern_table.height,
        "patterns_in_2_or_more_files": int((pattern_table["files"] >= 2).sum()),
        "patterns_in_10_or_more_files": int((pattern_table["files"] >= 10).sum()),
        "minutes": (time.time() - t_0) / 60,
    }
    (outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k not in ("config", "failed")}, indent=2))

    def show(table: pl.DataFrame) -> None:
        for r in table.iter_rows(named=True):
            print(f"{r['score']:8.3f}  files {r['files']:4d} (benign {r['benign_files']:4d})  credit {r['mean_credit']:.3f}  "
                  f"len {r['length']:5d}  {r['top_feature'][:40]:40s}  {preview(r['content'])}")

    print(f"\nTop {args.show} patterns (score = files x mean credit; spans of >= {args.min_length} bytes):")
    show(pattern_table.head(args.show))
    grouped = pattern_table.with_columns(pl.col("top_feature").str.split(":").list.first().alias("group"))
    for (group,), table in grouped.group_by("group", maintain_order=True):
        print(f"\n{group}: {table.height} patterns, {int((table['files'] >= 2).sum())} in 2 or more files")
        show(table.head(args.show_per_group))
    print(f"\nWrote {outdir.as_posix()}.")


if __name__ == "__main__":
    main()
