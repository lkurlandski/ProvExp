"""
3-B transplant test (docs/graveyard.md): is each candidate spurious correlation surfaced by the pullback causal,
and can an attacker set it? The candidates are not hand-picked: they are the top `--num_candidates` patterns of the
discovery run (scripts/shortcuts.py, benign-pushing by default), by score, that recur in at least `--min_files` files.

For each held-out malware file and each candidate (top feature j, content c of L bytes), the file's own provenance
names the bytes to write: a run of L contiguous bytes in the support of P's column j (or, if the file has none, in the
support of a feature of j's hashed family, e.g. `section:size_hash_*`, whose bucket depends on the content). One such
run is drawn at random (seeded) among those that do not already hold c, and overwritten with c; the control writes
L random bytes into the same run. Both must parse with the original section layout (parse-only verification). The
GBDT re-scores both; the drop in the malware log-odds of the content is compared with the control's, paired by file.

Optionally (`--mined`), the top label-skewed byte n-grams mined without P (scripts/shortcuts_train_sample.py) are
tested too, with the only placement available without P: appended to the file (as in scripts/shortcuts_insert.py).

A candidate is *confirmed* (fixed in advance) if it applies to at least `--min_applicable` files, its median drop
toward benign and its median paired difference (content drop minus random drop) are both at least `--min_effect`
log-odds, and a one-sided Wilcoxon signed-rank test of the paired differences gives p < 0.05 / (number of
candidates). The first condition matters because a random value is often anomalous in itself (e.g., a random entry
point looks malicious), so beating the control alone does not mean the content moves the file toward benign.

Outputs, in `{outdir}/seed-{seed}/{tag}/`:
    candidates.parquet  the candidates (id, kind, top feature, content, and their discovery statistics)
    files.parquet       one row per target file: status and the original malware log-odds
    results.parquet     one row per (file, candidate, source): placement mode and start, parsed, modified score,
                        drop, flipped; `source` is "content" or "random"
    summary.parquet     one row per candidate: applicability, median drops, paired effect, p-value, confirmed
    report.json         the configuration, statuses, and timing

With `--scorer malconv`, MalConv (a raw-byte model) re-scores the files instead of the GBDT; this confirms the
candidates of 3-C revised (docs/audit_plan.md, scripts/audit_discover.py), which are placed by the same provenance.

Usage:
    PYTHONHASHSEED=0 python scripts/shortcuts_transplant.py --seed 0 --num_workers 16
    PYTHONHASHSEED=0 python scripts/shortcuts_transplant.py --seed 0 --model artifacts/models/gbdt/seed-0-neutral/model.txt --tag neutral
    PYTHONHASHSEED=0 python scripts/shortcuts_transplant.py --seed 0 --scorer malconv --tag malconv \
        --patterns artifacts/experiments/audit_discover/seed-0/malconv-benign/patterns.parquet
"""

from __future__ import annotations

from argparse import ArgumentParser
from collections import Counter
import json
import multiprocessing as mp
import os
from pathlib import Path
import re
import signal
import sys
import time
from types import FrameType
from typing import Any
from typing import Optional
import warnings

import lightgbm as lgb
import numpy as np
from numpy import typing as npt
import polars as pl
from scipy import stats
import torch
from tqdm import tqdm

from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBIterator
from provexp.explain.feature import gbdt_function
from provexp.featuresets.ember2024.ablation import parse
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.trigger import apply_content
from provexp.models.malconv import encode
from provexp.models.malconv import load_pretrained_malconv
from provexp.provenance import Provenance


__all__ = [
    "select_candidates",
    "family",
    "feature_runs",
    "choose_run",
    "summarize",
]


ROOT = Path(__file__).parent.parent

_EXTRACTOR: Optional[PEFeatureExtractor] = None
_GBDT: Optional[Any] = None
_MALCONV: Optional[Any] = None


################################################################################
# Candidates
################################################################################


def select_candidates(patterns: pl.DataFrame, num: int, min_files: int) -> pl.DataFrame:
    """
    The top `num` discovery patterns by score that recur in at least `min_files` files, with a `candidate` id (their
    rank, from 0) and `kind` "pullback".
    """
    if num <= 0:
        raise ValueError(f"Expected a positive number of candidates. Got {num}.")
    chosen = patterns.filter(pl.col("files") >= min_files).sort("score", descending=True).head(num)
    return chosen.with_row_index("candidate").with_columns(
        pl.col("candidate").cast(pl.Int64), pl.lit("pullback").alias("kind"), pl.col("content").bin.size().alias("length"),
    )


def family(name: str) -> str:
    """The family of a hashed feature (its name without the trailing bucket number), or the name itself."""
    return re.sub(r"_\d+$", "_*", name)


################################################################################
# Placement by provenance
################################################################################


def feature_runs(prov: Provenance, features: npt.NDArray[np.int64]) -> dict[int, list[tuple[int, int]]]:
    """
    The maximal runs of contiguous elements in the support of each of `features`' columns of P: {feature: [(start,
    length), ...]}, sorted by start. The null element is never part of a run.
    """
    runs: dict[int, list[tuple[int, int]]] = {int(j): [] for j in features}
    if features.size == 0:
        return runs
    order = np.sort(np.asarray(features, dtype=np.int64))
    pieces = prov.select(order).pieces()
    m = prov.num_elements
    for col, lo, hi in zip(pieces.col.tolist(), pieces.lo.tolist(), pieces.hi.tolist()):
        hi = min(hi, m)
        if lo >= hi:
            continue
        j = int(order[col])
        if runs[j] and runs[j][-1][0] + runs[j][-1][1] == lo:
            start, length = runs[j][-1]
            runs[j][-1] = (start, length + hi - lo)
        else:
            runs[j].append((lo, hi - lo))
    return runs


def choose_run(
    data: bytes,
    runs: dict[int, list[tuple[int, int]]],
    feature: int,
    members: list[int],
    content: bytes,
    rng: np.random.Generator,
) -> tuple[Optional[int], str]:
    """
    Choose where to write `content`: a run of exactly len(content) elements of `feature`, else of a feature in its
    family (`members`), that does not already hold the content, drawn with `rng`.

    Returns:
        The start of the run (None if there is none) and the mode: "feature", "family", "present" (every run of the
        right length already holds the content), or "none".
    """
    length = len(content)
    present = False
    for mode, js in (("feature", [feature]), ("family", [j for j in members if j != feature])):
        starts = []
        for j in js:
            for start, n in runs.get(j, []):
                if n != length:
                    continue
                if data[start:start + length] == content:
                    present = True
                else:
                    starts.append(start)
        if starts:
            return int(starts[int(rng.integers(len(starts)))]), mode
        if present:
            return None, "present"
    return None, "none"


def overwrite(data: bytes, start: int, block: bytes) -> bytes:
    """Write `block` over `data` at `start`."""
    if start < 0 or start + len(block) > len(data):
        raise ValueError(f"Cannot write {len(block)} bytes at {start} in a file of {len(data)} bytes.")
    return data[:start] + block + data[start + len(block):]


################################################################################
# Workers
################################################################################


class TransplantTimeout(Exception):
    pass


def _raise_timeout(signum: int, frame: Optional[FrameType]) -> None:
    raise TransplantTimeout()


def _init_worker(model_file: Path, scorer: str = "gbdt") -> None:
    global _EXTRACTOR, _GBDT, _MALCONV
    _EXTRACTOR = PEFeatureExtractor()
    if scorer == "malconv":
        torch.set_num_threads(1)
        _MALCONV = load_pretrained_malconv(model_file)
    else:
        _GBDT = gbdt_function(lgb.Booster(model_file=str(model_file)))
    # thrember prints unknown pefile warnings to stdout.
    sys.stdout = open(os.devnull, "w")
    warnings.filterwarnings("ignore")
    signal.signal(signal.SIGALRM, _raise_timeout)


def score(data: bytes) -> float:
    """The scored model's malware log-odds of a file's bytes (the GBDT's raw score, or MalConv's logit difference)."""
    if _MALCONV is not None:
        with torch.no_grad():
            z = _MALCONV(encode(data)[None])
        return float(z[0, 1] - z[0, 0])
    assert _EXTRACTOR is not None and _GBDT is not None
    x = np.asarray(_EXTRACTOR.feature_vector(data), dtype=np.float64)  # type: ignore[no-untyped-call]
    return float(_GBDT(x[None, :])[0])


def verified_score(modified: bytes, layout: Any) -> Optional[float]:
    """The score of a modified file, or None if it does not parse or its section layout changed."""
    result = parse(modified)
    if result.status != "ok" or result.layout != layout:
        return None
    return score(modified)


def process_shard(
    shard: int,
    samples: list[dict[str, Any]],
    dbdir: Path,
    candidates: list[dict[str, Any]],
    families: dict[int, list[int]],
    min_score: float,
    max_length: int,
    seed: int,
    timeout: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Run the transplant test on the target files in one SimpleDB shard.

    Args:
        shard: The shard.
        samples: The target files in the shard, each with its `index`, `position`, and `name`.
        dbdir: The SimpleDB.
        candidates: Each with its `candidate` id, `kind` ("pullback": placed by provenance; "mined": appended),
            `content`, and, for "pullback", its top feature's index `j`.
        families: For each top feature, the features of its family (including itself).
        min_score: Skip a file whose original malware log-odds is at most this (no room to drop).
        max_length: The truncation length (appended blocks past it overwrite the end, see `apply_content`).
        seed: The seed of the placements and the random controls (from the seed, the file, and the candidate).
        timeout: The maximum number of seconds per file.

    Returns:
        The file records and the result records.
    """
    assert _EXTRACTOR is not None
    needed = np.array(sorted({j for js in families.values() for j in js}), dtype=np.int64)
    wanted = {s["position"]: i for i, s in enumerate(samples)}
    files: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    seen = set()
    db = SimpleDB(dbdir, check=False)
    for position, sample in enumerate(SimpleDBIterator(db).iter(shard)):
        if position not in wanted:
            continue
        seen.add(position)
        meta = samples[wanted[position]]
        if sample.name != meta["name"]:
            raise RuntimeError(f"Shard {shard}, position {position} holds {sample.name}, not {meta['name']}.")
        base = {"index": meta["index"], "name": meta["name"]}
        signal.alarm(timeout)
        try:
            data = bytes(sample.data)
            original = parse(data)
            if original.status != "ok":
                files.append(base | {"status": "not_pe", "log_odds": float("nan")})
                continue
            log_odds = score(data)
            if log_odds <= min_score:
                files.append(base | {"status": "low_score", "log_odds": log_odds})
                continue
            _, prov = _EXTRACTOR.feature_vector_with_provenance(data)
            runs = feature_runs(prov, needed)
            for cand in candidates:
                content = bytes(cand["content"])
                rng = np.random.default_rng([seed, int(meta["index"]), int(cand["candidate"]), 0 if cand["kind"] == "pullback" else 1])
                control = rng.integers(0, 256, size=len(content), dtype=np.uint8).tobytes()
                record = {"index": meta["index"], "kind": cand["kind"], "candidate": cand["candidate"]}
                if cand["kind"] == "pullback":
                    start, mode = choose_run(data, runs, int(cand["j"]), families[int(cand["j"])], content, rng)
                    if start is None:
                        results.append(record | {"source": "content", "mode": mode, "start": -1, "parsed": False,
                                                 "modified": float("nan"), "drop": float("nan"), "flipped": False})
                        continue
                    blocks = {"content": overwrite(data, start, content), "random": overwrite(data, start, control)}
                else:
                    start, mode = len(data), "append"
                    blocks = {}
                    for source, block in (("content", content), ("random", control)):
                        try:
                            blocks[source] = apply_content(data, block, max_length=max_length).data
                        except ValueError:
                            pass
                for source in ("content", "random"):
                    modified = verified_score(blocks[source], original.layout) if source in blocks else None
                    results.append(record | {
                        "source": source, "mode": mode, "start": start, "parsed": modified is not None,
                        "modified": modified if modified is not None else float("nan"),
                        "drop": (log_odds - modified) if modified is not None else float("nan"),
                        "flipped": bool(modified < 0) if modified is not None else False,
                    })
            files.append(base | {"status": "ok", "log_odds": log_odds})
        except TransplantTimeout:
            files.append(base | {"status": "timeout", "log_odds": float("nan")})
        except Exception as err:
            files.append(base | {"status": "error", "log_odds": float("nan"), "error": f"{type(err).__name__}: {err}"[:300]})
        finally:
            signal.alarm(0)
    missing = set(wanted) - seen
    if missing:
        raise RuntimeError(f"Shard {shard} has no samples at positions {sorted(missing)}.")
    return files, results


def _star(task: tuple[Any, ...]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return process_shard(*task)


################################################################################
# Summary
################################################################################


def summarize(results: pl.DataFrame, num_tests: int, min_applicable: int, min_effect: float) -> pl.DataFrame:
    """
    Per candidate, over the files where both the content and the control were written and parse: the number of such
    files, the median drop of each, the flip rates, the median paired difference (content minus random), the
    one-sided Wilcoxon signed-rank p-value of the differences, and whether the candidate is confirmed (see the module
    docstring). Also the placement modes over all target files.
    """
    if num_tests <= 0:
        raise ValueError(f"Expected a positive number of tests. Got {num_tests}.")
    modes = (
        results.filter(pl.col("source") == "content").group_by("kind", "candidate").agg(
            (pl.col("mode") == "feature").sum().alias("placed_feature"),
            (pl.col("mode") == "family").sum().alias("placed_family"),
            (pl.col("mode") == "present").sum().alias("already_present"),
            (pl.col("mode") == "none").sum().alias("no_run"),
        )
    )
    wide = (
        results.filter(pl.col("parsed")).select("index", "kind", "candidate", "source", "drop", "flipped")
        .pivot(on="source", index=["index", "kind", "candidate"], values=["drop", "flipped"])
        .drop_nulls()
    )
    rows = []
    for (kind, candidate), group in wide.group_by("kind", "candidate", maintain_order=True):
        diff = (group["drop_content"] - group["drop_random"]).to_numpy()
        n = diff.size
        p = float(stats.wilcoxon(diff, alternative="greater").pvalue) if n > 0 and np.any(diff != 0) else 1.0
        effect = float(np.median(diff)) if n else float("nan")
        rows.append({
            "kind": kind, "candidate": candidate, "applicable": n,
            "median_drop_content": float(group["drop_content"].median()),  # type: ignore[arg-type]
            "median_drop_random": float(group["drop_random"].median()),  # type: ignore[arg-type]
            "flip_content": float(group["flipped_content"].mean()),  # type: ignore[arg-type]
            "flip_random": float(group["flipped_random"].mean()),  # type: ignore[arg-type]
            "median_effect": effect, "p_value": p,
            "confirmed": bool(n >= min_applicable and effect >= min_effect and p < 0.05 / num_tests
                              and float(np.median(group["drop_content"].to_numpy())) >= min_effect),
        })
    summary = pl.DataFrame(rows, schema={
        "kind": pl.String, "candidate": pl.Int64, "applicable": pl.Int64, "median_drop_content": pl.Float64,
        "median_drop_random": pl.Float64, "flip_content": pl.Float64, "flip_random": pl.Float64,
        "median_effect": pl.Float64, "p_value": pl.Float64, "confirmed": pl.Boolean,
    })
    return modes.join(summary, on=["kind", "candidate"], how="left").sort("kind", "candidate", descending=[True, False])


################################################################################
# Driver
################################################################################


def main() -> None:
    parser = ArgumentParser(description="3-B transplant test: write each surfaced candidate into held-out malware.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--patterns", type=Path, default=ROOT / "artifacts" / "experiments" / "shortcuts" / "seed-0" / "treeshap_interventional-benign" / "patterns.parquet")
    parser.add_argument("--num_candidates", type=int, default=20)
    parser.add_argument("--min_files", type=int, default=10)
    parser.add_argument("--mined", type=Path, default=None, help="Optionally, mined.parquet of scripts/shortcuts_train_sample.py: also append its top n-grams.")
    parser.add_argument("--num_mined", type=int, default=20)
    parser.add_argument("--scorer", type=str, choices=["gbdt", "malconv"], default="gbdt", help="The model that re-scores the files.")
    parser.add_argument("--model", type=Path, default=None, help="The model file (default: artifacts/models/gbdt/seed-{seed}/model.txt, or checkpoints/malconv-seed{seed}.pt).")
    parser.add_argument("--tag", type=str, default="gbdt", help="The output subdirectory (e.g., the model).")
    parser.add_argument("--num_files", type=int, default=200)
    parser.add_argument("--min_score", type=float, default=0.0)
    parser.add_argument("--min_applicable", type=int, default=20)
    parser.add_argument("--min_effect", type=float, default=0.1)
    parser.add_argument("--max_length", type=int, default=4_000_000)
    parser.add_argument("--explanation_set", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "shortcuts_transplant")
    parser.add_argument("--num_workers", type=int, default=os.cpu_count())
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()

    if os.environ.get("PYTHONHASHSEED") != "0":
        raise RuntimeError("Run with PYTHONHASHSEED=0 so that the features match the feature store.")

    outdir = args.outdir / f"seed-{args.seed}" / args.tag
    outdir.mkdir(parents=True, exist_ok=True)
    default_model = (ROOT / "checkpoints" / f"malconv-seed{args.seed}.pt" if args.scorer == "malconv"
                     else ROOT / "artifacts" / "models" / "gbdt" / f"seed-{args.seed}" / "model.txt")
    model_file = args.model if args.model is not None else default_model
    if not model_file.exists():
        raise RuntimeError(f"No {args.scorer} model at {model_file.as_posix()}.")

    names = PEFeatureExtractor().feature_names
    index = {name: i for i, name in enumerate(names)}
    candidates = select_candidates(pl.read_parquet(args.patterns), args.num_candidates, args.min_files)
    candidates = candidates.with_columns(pl.col("top_feature").replace_strict(index, return_dtype=pl.Int64).alias("j"))
    families = {}
    for j in candidates["j"].to_list():
        f = family(names[j])
        families[j] = [i for i, name in enumerate(names) if family(name) == f] if f != names[j] else [j]
    if args.mined is not None:
        mined = (
            pl.read_parquet(args.mined).filter(pl.col("direction") == "benign").sort("rank").head(args.num_mined)
            .select(pl.col("rank").cast(pl.Int64).alias("candidate"), "content")
            .with_columns(pl.lit("mined").alias("kind"), pl.col("content").bin.size().alias("length"))
        )
        candidates = pl.concat([candidates, mined], how="diagonal_relaxed")
    candidates.write_parquet(outdir / "candidates.parquet")
    num_tests = int((candidates["kind"] == "pullback").sum())

    # The same held-out malware as run 24: not in the explanation set, not truncated, drawn with the seed.
    meta = pl.read_parquet(args.features / "ts" / "meta.parquet")
    explained = pl.read_parquet(args.explanation_set).select("name")
    pool = (
        meta.filter((pl.col("label") == 1) & (pl.col("status") == "ok") & ~pl.col("truncated"))
        .join(explained, on="name", how="anti")
    )
    targets = pool.sample(min(args.num_files, pool.height), seed=args.seed).with_row_index("index")
    print(f"3-B transplant: {targets.height} malware files, {candidates.height} candidates, model {model_file.as_posix()}.", flush=True)

    rows = candidates.select("candidate", "kind", "content", "j").to_dicts()
    tasks = []
    for (shard,), group in targets.sort("shard", "position").group_by("shard", maintain_order=True):
        tasks.append((int(shard), group.select("index", "name", "position").to_dicts(), args.db, rows, families,
                      args.min_score, args.max_length, args.seed, args.timeout))

    t_0 = time.time()
    files: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    with mp.get_context("fork").Pool(args.num_workers, initializer=_init_worker, initargs=(model_file, args.scorer)) as pool_:
        for f, r in tqdm(pool_.imap_unordered(_star, sorted(tasks, key=lambda t: -len(t[1]))), total=len(tasks), desc="shards", mininterval=10):
            files.extend(f)
            results.extend(r)

    file_table = pl.DataFrame(files, infer_schema_length=None).sort("index")
    result_table = pl.DataFrame(results, infer_schema_length=None).sort("index", "kind", "candidate", "source")
    summary = summarize(result_table, num_tests, args.min_applicable, args.min_effect)
    summary = summary.join(candidates.select("kind", "candidate", "top_feature", "content"), on=["kind", "candidate"], how="left")
    file_table.write_parquet(outdir / "files.parquet")
    result_table.write_parquet(outdir / "results.parquet")
    summary.write_parquet(outdir / "summary.parquet")

    scored = file_table.filter(pl.col("status") == "ok")
    report = {
        "config": {k: (v.as_posix() if isinstance(v, Path) else v) for k, v in vars(args).items()},
        "model": model_file.as_posix(),
        "scorer": args.scorer,
        "num_targets": file_table.height,
        "status": dict(Counter(file_table["status"].to_list())),
        "num_scored": scored.height,
        "num_confirmed": int(summary.filter(pl.col("kind") == "pullback")["confirmed"].fill_null(False).sum()),
        "minutes": (time.time() - t_0) / 60,
    }
    (outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "config"}, indent=2))

    print(f"\nPer candidate over {scored.height} files: median drop in malware log-odds, content vs. random in the same bytes:")
    for r in summary.iter_rows(named=True):
        text = "".join(chr(c) if 32 <= c < 127 else "." for c in r["content"][:24])
        effect = f"{r['median_effect']:+6.3f}" if r["median_effect"] is not None else "   n/a"
        drops = (f"{r['median_drop_content']:+6.3f} vs {r['median_drop_random']:+6.3f}" if r["applicable"] else "      n/a       ")
        print(f"{r['kind'][:4]} {r['candidate']:3d}  n {r['applicable'] or 0:3d} (feat {r['placed_feature']:3d} fam {r['placed_family']:3d} "
              f"pres {r['already_present']:3d})  drop {drops}  effect {effect}  p {r['p_value'] if r['p_value'] is not None else float('nan'):.1e}  "
              f"{'CONFIRMED' if r['confirmed'] else '         '}  {(r['top_feature'] or '')[:42]:42s} {text!r} [{r['content'][:8].hex()}]")
    print(f"\nWrote {outdir.as_posix()}.")


if __name__ == "__main__":
    main()
