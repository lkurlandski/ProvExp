"""
3-B exploitability check (docs/archive/shortcuts_plan.md): do the confirmed spurious correlations, forged together, let
detected malware cross the detector's operating threshold, and does the P-named mitigation remove that?

The forge set is not hand-picked: the confirmed *artifact* candidates of the transplant test (scripts/
shortcuts_transplant.py, `summary.parquet`, labels from scripts/shortcuts_tables.py), one per top feature (the
best-ranked; e.g. the two certificate-table sizes write the same bytes). For each held-out malware file detected at the
operating threshold (the validation benign scores' (1 - fpr) quantile, so at most `fpr` false positives), each piece
is placed where the file's own provenance says (as in the transplant test: a run of the top feature's support, else of
its hashed family) and all applicable pieces are written together; the control writes random bytes into the same
runs. Both must parse with the original section layout. A file *evades* if its forged score is at most the threshold.

Outputs, in `{outdir}/seed-{seed}/{tag}/`:
    forge_set.parquet   the pieces (candidate, top feature, content)
    files.parquet       one row per target: status, original score, pieces applied, forged and control scores, evaded
    report.json         the configuration, threshold, evasion rates, and timing

Usage:
    PYTHONHASHSEED=0 python scripts/shortcuts_forge.py --seed 0 --num_workers 16
    PYTHONHASHSEED=0 python scripts/shortcuts_forge.py --seed 0 --model artifacts/models/gbdt/seed-0-neutral/model.txt --tag neutral
"""

from __future__ import annotations

from argparse import ArgumentParser
from collections import Counter
import json
import multiprocessing as mp
import os
from pathlib import Path
import signal
import sys
import time
from typing import Any
from typing import Optional

import lightgbm as lgb
import numpy as np
from numpy import typing as npt
import polars as pl
from tqdm import tqdm

from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBIterator
from provexp.data.tabular import load_features
from provexp.explain.feature import gbdt_function
from provexp.featuresets.ember2024.ablation import parse
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.data.paths import EMBER2024_DATA

sys.path.insert(0, str(Path(__file__).parent))

import shortcuts_transplant as transplant  # noqa: E402
from shortcuts_tables import label  # noqa: E402
from shortcuts_transplant import TransplantTimeout  # noqa: E402
from shortcuts_transplant import choose_run  # noqa: E402
from shortcuts_transplant import family  # noqa: E402
from shortcuts_transplant import feature_runs  # noqa: E402
from shortcuts_transplant import overwrite  # noqa: E402


__all__ = [
    "forge_set",
    "operating_threshold",
    "write_all",
]


ROOT = Path(__file__).parent.parent


################################################################################
# Forge set and threshold
################################################################################


def forge_set(summary: pl.DataFrame) -> pl.DataFrame:
    """The confirmed artifact candidates of a transplant summary, the best-ranked (lowest id) per top feature."""
    rows = [
        r for r in summary.filter((pl.col("kind") == "pullback") & pl.col("confirmed").fill_null(False)).sort("candidate").iter_rows(named=True)
        if label(r["top_feature"], r["content"])[0] == "artifact"
    ]
    seen: set[str] = set()
    chosen = []
    for r in rows:
        if r["top_feature"] not in seen:
            seen.add(r["top_feature"])
            chosen.append({"candidate": r["candidate"], "top_feature": r["top_feature"], "content": r["content"]})
    return pl.DataFrame(chosen, schema={"candidate": pl.Int64, "top_feature": pl.String, "content": pl.Binary})


def operating_threshold(benign_scores: npt.NDArray[np.float64], fpr: float) -> float:
    """The smallest observed benign score with at most `fpr` of the benign scores above it."""
    if not 0 < fpr < 1:
        raise ValueError(f"Expected a false-positive rate in (0, 1). Got {fpr}.")
    if benign_scores.size == 0:
        raise ValueError("Expected at least one benign score.")
    return float(np.quantile(benign_scores, 1 - fpr, method="higher"))


def write_all(data: bytes, placements: list[tuple[int, bytes]]) -> Optional[bytes]:
    """Write every (start, block) into `data`, or None if two placements overlap."""
    ordered = sorted(placements, key=lambda p: p[0])
    for (s0, b0), (s1, _) in zip(ordered, ordered[1:]):
        if s0 + len(b0) > s1:
            return None
    for start, block in ordered:
        data = overwrite(data, start, block)
    return data


################################################################################
# Workers
################################################################################


def process_shard(
    shard: int,
    samples: list[dict[str, Any]],
    dbdir: Path,
    pieces: list[dict[str, Any]],
    families: dict[int, list[int]],
    seed: int,
    timeout: int,
) -> list[dict[str, Any]]:
    """
    Forge the target files of one SimpleDB shard.

    Args:
        shard: The shard.
        samples: The target files in the shard, each with its `index`, `position`, and `name`.
        dbdir: The SimpleDB.
        pieces: Each with its `candidate` id, `content`, and its top feature's index `j`.
        families: For each top feature, the features of its family (including itself).
        seed: The seed of the placements and the random controls (from the seed, the file, and the piece).
        timeout: The maximum number of seconds per file.

    Returns:
        The file records.
    """
    assert transplant._EXTRACTOR is not None
    needed = np.array(sorted({j for js in families.values() for j in js}), dtype=np.int64)
    wanted = {s["position"]: i for i, s in enumerate(samples)}
    files: list[dict[str, Any]] = []
    seen = set()
    db = SimpleDB(dbdir, check=False)
    for position, sample in enumerate(SimpleDBIterator(db).iter(shard)):
        if position not in wanted:
            continue
        seen.add(position)
        meta = samples[wanted[position]]
        if sample.name != meta["name"]:
            raise RuntimeError(f"Shard {shard}, position {position} holds {sample.name}, not {meta['name']}.")
        record: dict[str, Any] = {"index": meta["index"], "name": meta["name"], "log_odds": float("nan"), "applied": "",
                                  "num_applied": 0, "forged": float("nan"), "control": float("nan")}
        signal.alarm(timeout)
        try:
            data = bytes(sample.data)
            original = parse(data)
            if original.status != "ok":
                files.append(record | {"status": "not_pe"})
                continue
            record["log_odds"] = transplant.score(data)
            _, prov = transplant._EXTRACTOR.feature_vector_with_provenance(data)
            runs = feature_runs(prov, needed)
            forged: list[tuple[int, bytes]] = []
            control: list[tuple[int, bytes]] = []
            applied = []
            for piece in pieces:
                content = bytes(piece["content"])
                rng = np.random.default_rng([seed, int(meta["index"]), int(piece["candidate"])])
                start, _ = choose_run(data, runs, int(piece["j"]), families[int(piece["j"])], content, rng)
                if start is None:
                    continue
                forged.append((start, content))
                control.append((start, rng.integers(0, 256, size=len(content), dtype=np.uint8).tobytes()))
                applied.append(str(piece["candidate"]))
            record |= {"applied": ",".join(applied), "num_applied": len(applied)}
            if not applied:
                files.append(record | {"status": "none_applicable"})
                continue
            blocks = {"forged": write_all(data, forged), "control": write_all(data, control)}
            if blocks["forged"] is None:
                files.append(record | {"status": "overlap"})
                continue
            for source, block in blocks.items():
                s = transplant.verified_score(block, original.layout) if block is not None else None
                record[source] = s if s is not None else float("nan")
            files.append(record | {"status": "ok" if np.isfinite(record["forged"]) else "unparsed"})
        except TransplantTimeout:
            files.append(record | {"status": "timeout"})
        except Exception as err:
            files.append(record | {"status": "error", "error": f"{type(err).__name__}: {err}"[:300]})
        finally:
            signal.alarm(0)
    missing = set(wanted) - seen
    if missing:
        raise RuntimeError(f"Shard {shard} has no samples at positions {sorted(missing)}.")
    return files


def _star(task: tuple[Any, ...]) -> list[dict[str, Any]]:
    return process_shard(*task)


################################################################################
# Driver
################################################################################


def main() -> None:
    parser = ArgumentParser(description="3-B exploitability: forge the confirmed artifacts together into detected malware.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--summary", type=Path, default=None, help="The transplant summary that defines the forge set (default: the seed's gbdt run).")
    parser.add_argument("--model", type=Path, default=None, help="The GBDT (default: artifacts/models/gbdt/seed-{seed}/model.txt).")
    parser.add_argument("--tag", type=str, default="gbdt", help="The output subdirectory (e.g., the model).")
    parser.add_argument("--fpr", type=float, default=0.01, help="The validation false-positive rate that sets the operating threshold.")
    parser.add_argument("--num_files", type=int, default=2000)
    parser.add_argument("--explanation_set", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--db", type=Path, default=EMBER2024_DATA / "ts")
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "shortcuts_forge")
    parser.add_argument("--num_workers", type=int, default=os.cpu_count())
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()

    if os.environ.get("PYTHONHASHSEED") != "0":
        raise RuntimeError("Run with PYTHONHASHSEED=0 so that the features match the feature store.")

    outdir = args.outdir / f"seed-{args.seed}" / args.tag
    outdir.mkdir(parents=True, exist_ok=True)
    model_file = args.model if args.model is not None else ROOT / "artifacts" / "models" / "gbdt" / f"seed-{args.seed}" / "model.txt"
    summary_file = args.summary if args.summary is not None else ROOT / "artifacts" / "experiments" / "shortcuts_transplant" / f"seed-{args.seed}" / "gbdt" / "summary.parquet"
    if not model_file.exists():
        raise RuntimeError(f"No GBDT at {model_file.as_posix()}.")

    names = PEFeatureExtractor().feature_names
    index = {name: i for i, name in enumerate(names)}
    pieces = forge_set(pl.read_parquet(summary_file))
    if pieces.height == 0:
        raise RuntimeError(f"No confirmed artifact candidates in {summary_file.as_posix()}.")
    pieces = pieces.with_columns(pl.col("top_feature").replace_strict(index, return_dtype=pl.Int64).alias("j"))
    pieces.write_parquet(outdir / "forge_set.parquet")
    families = {}
    for j in pieces["j"].to_list():
        f = family(names[j])
        families[j] = [i for i, name in enumerate(names) if family(name) == f] if f != names[j] else [j]

    # Held-out malware: not in the explanation set, not truncated, drawn with the seed.
    meta = pl.read_parquet(args.features / "ts" / "meta.parquet")
    explained = pl.read_parquet(args.explanation_set).select("name")
    pool = meta.filter((pl.col("label") == 1) & (pl.col("status") == "ok") & ~pl.col("truncated")).join(explained, on="name", how="anti")
    targets = pool.sample(min(args.num_files, pool.height), seed=args.seed).with_row_index("index")
    t_0 = time.time()
    print(f"3-B forge: {targets.height} malware files, {pieces.height} pieces, model {model_file.as_posix()}.", flush=True)

    rows_ = pieces.select("candidate", "content", "j").to_dicts()
    tasks = []
    for (shard,), group in targets.sort("shard", "position").group_by("shard", maintain_order=True):
        tasks.append((int(shard), group.select("index", "name", "position").to_dicts(), args.db, rows_, families, args.seed, args.timeout))
    files: list[dict[str, Any]] = []
    with mp.get_context("fork").Pool(args.num_workers, initializer=transplant._init_worker, initargs=(model_file,)) as pool_:
        for f in tqdm(pool_.imap_unordered(_star, sorted(tasks, key=lambda t: -len(t[1]))), total=len(tasks), desc="shards", mininterval=10):
            files.extend(f)

    table = pl.DataFrame(files, infer_schema_length=None).sort("index")

    # NOTE: after the pool, since LightGBM's OpenMP threads in the parent deadlock forked workers.
    # The operating threshold: at most `fpr` of the validation benign files score above it.
    X, meta_vl = load_features(args.features, "vl")
    benign = ((meta_vl["label"] == 0) & (meta_vl["status"] == "ok")).to_numpy()
    model = gbdt_function(lgb.Booster(model_file=str(model_file)))
    rows = np.flatnonzero(benign)
    benign_scores = np.concatenate([model(np.asarray(X[rows[i:i + 50_000]], dtype=np.float64)) for i in range(0, rows.size, 50_000)])
    threshold = operating_threshold(benign_scores, args.fpr)
    print(f"Operating threshold at {args.fpr:.2%} validation FPR: {threshold:.4f} log-odds ({rows.size} benign files).", flush=True)

    table = table.with_columns(
        pl.when(pl.col("log_odds") <= threshold).then(pl.lit("not_detected")).otherwise(pl.col("status")).alias("status")
    )
    table = table.with_columns(
        (pl.col("forged") <= threshold).alias("evaded"),
        (pl.col("control") <= threshold).alias("evaded_control"),
    )
    table.write_parquet(outdir / "files.parquet")

    status = dict(Counter(table["status"].to_list()))
    # Detected: scored above the threshold (errors and timeouts, which have no score, are left out).
    detected = table.filter(pl.col("log_odds") > threshold)
    ok = table.filter(pl.col("status") == "ok")
    both = ok.filter(pl.col("control").is_not_nan())
    report = {
        "config": {k: (v.as_posix() if isinstance(v, Path) else v) for k, v in vars(args).items()},
        "model": model_file.as_posix(),
        "threshold": threshold,
        "status": status,
        "num_detected": detected.height,
        "num_forged": ok.height,
        "pieces_applied": dict(Counter(ok["applied"].to_list())),
        # Over every detected file (a file the forge set cannot be applied to counts as not evading).
        "evasion_detected": float(ok["evaded"].sum()) / detected.height if detected.height else float("nan"),
        "evasion_forged": float(ok["evaded"].mean()) if ok.height else float("nan"),  # type: ignore[arg-type]
        "evasion_control": float(both["evaded_control"].mean()) if both.height else float("nan"),  # type: ignore[arg-type]
        "median_drop_forged": float((ok["log_odds"] - ok["forged"]).median()) if ok.height else float("nan"),  # type: ignore[arg-type]
        "median_drop_control": float((both["log_odds"] - both["control"]).median()) if both.height else float("nan"),  # type: ignore[arg-type]
        "minutes": (time.time() - t_0) / 60,
    }
    (outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "config"}, indent=2))
    for k in sorted(ok["num_applied"].unique().to_list()):
        g = ok.filter(pl.col("num_applied") == k)
        rate, control = float(g["evaded"].mean()), float(g["evaded_control"].mean())  # type: ignore[arg-type]
        print(f"{k} pieces: {g.height} files, evasion {rate:.3f} (control {control:.3f})")
    print(f"\nWrote {outdir.as_posix()}.")


if __name__ == "__main__":
    main()
