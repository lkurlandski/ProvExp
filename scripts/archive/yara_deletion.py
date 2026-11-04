"""
3-C, the deletion check (docs/rules_plan.md): do the reliance categories from the GBDT's attribution (run 36) hold when
the matched bytes are deleted?

For each rule with a split in run 34 (the candidates for "relied on" vs. "reliance gap") and each crypto rule located on
at least 5 pilot files (representation-gap controls), in each file where it matches: delete S, the rule's matched
bytes, with PB1's operator (level 3: protected layout fields, typical header values, zeros; every deleted file
verified), and 20 reference sets with S's run lengths drawn from bytes whose provenance is at least as concentrated as
S's (run 36's reference: c_i = sum_j P_ij over the non-aggregate features, c_i >= the 25th percentile of c over S).
The GBDT's response to a deletion is |f(x) - f(x without the set)| in log-odds; S is "above" in a file if its response
exceeds the 95th percentile of the valid references' (at least 10 valid).

Hypothesis: deletion agrees with the attribution: network_dns (and network_tcp_socket) are above in most files; the
other capability and anti-debug rules are not; the crypto rules are not (their bytes reach only aggregates).

Check, fixed in advance (2026-10-12): per split rule, "relied on" if above in at least half of its files, by deletion
and by attribution (run 36); the categories hold if they agree for more than half of the split rules and the two
per-rule shares are positively rank-correlated. Otherwise the categories are not trustworthy as they stand.

Outputs, in `{outdir}/seed-{seed}/`:
    files.parquet       one row per (rule, file): |S|, the response to deleting S, the references' median and 95th
                        percentile, the number of valid references
    report.json         the configuration and timing

Usage:
    PYTHONHASHSEED=0 OMP_NUM_THREADS=1 python scripts/yara_deletion.py --seed 0 --num_workers 32
"""

from __future__ import annotations

from argparse import ArgumentParser
import json
import multiprocessing as mp
from pathlib import Path
import sys
import time
from typing import Any
import warnings

import lightgbm as lgb
import numpy as np
from numpy import typing as npt
import polars as pl
from scipy import stats
from tqdm import tqdm

from provexp.ablation import ablate
from provexp.explain.feature import gbdt_function
from provexp.featuresets.ember2024.ablation import protect
from provexp.featuresets.ember2024.ablation import verify
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.data.paths import EMBER2024_DATA

sys.path.insert(0, str(Path(__file__).parent))

from faithfulness import load_sample  # noqa: E402
from yara_check import AGGREGATE_GROUPS  # noqa: E402
from yara_check import DETERMINED  # noqa: E402
from yara_check import MIN_FILES  # noqa: E402
from yara_reliance import run_lengths  # noqa: E402


__all__ = [
    "random_run_masks",
]


ROOT = Path(__file__).parent.parent
IS_PE = 2  # The index of general:is_pe.
NUM_REFERENCE = 20
MIN_VALID = 10
PERCENTILE = 95.0
CONCENTRATION_QUANTILE = 25.0
RELIED = 0.5

BoolArray = npt.NDArray[np.bool_]
FloatArray = npt.NDArray[np.float64]
IntArray = npt.NDArray[np.int64]

_STATE: dict[str, Any] = {}


################################################################################
# Reference Sets
################################################################################


def random_run_masks(eligible: BoolArray, lengths: IntArray, num: int, rng: np.random.Generator) -> list[BoolArray]:
    """`num` masks, each with runs of `lengths` placed at uniform random offsets in the sequence of eligible elements."""
    idx = np.flatnonzero(eligible)
    if lengths.max(initial=0) > idx.shape[0]:
        raise ValueError(f"A run of {lengths.max()} elements does not fit in {idx.shape[0]} eligible elements.")
    masks = []
    for _ in range(num):
        mask = np.zeros(eligible.shape[0], dtype=np.bool_)
        for length in lengths:
            start = int(rng.integers(0, idx.shape[0] - length + 1))
            mask[idx[start:start + length]] = True
        masks.append(mask)
    return masks


################################################################################
# Per File
################################################################################


def _init_worker(gbdt_file: Path) -> None:
    warnings.filterwarnings("ignore")
    _STATE["extractor"] = PEFeatureExtractor()
    _STATE["gbdt"] = gbdt_function(lgb.Booster(model_file=str(gbdt_file)))
    groups = np.array([n.split(":")[0] for n in _STATE["extractor"].feature_names])
    _STATE["outside"] = (~np.isin(groups, AGGREGATE_GROUPS)).astype(np.float64)


def process_file(task: dict[str, Any]) -> list[dict[str, Any]]:
    """Delete each rule's matched bytes and its reference sets from one file, and score the GBDT."""
    base = {"index": task["index"], "label": task["label"]}
    try:
        data = load_sample(task["shard"], task["position"], task["name"], task["dbdir"])
        m = len(data)
        extractor: PEFeatureExtractor = _STATE["extractor"]
        gbdt = _STATE["gbdt"]
        x0, prov = extractor.feature_vector_with_provenance(data)
        f0 = float(gbdt(np.asarray(x0, dtype=np.float64)[None, :])[0])
        concentration = prov.matvec(_STATE["outside"])[:m]
        protection = protect(data, header="typical")

        def response(mask: BoolArray) -> float:
            z = ablate(data, mask, protection.mask, "zeros", None, protection.header, protection.header_values)
            try:
                x = np.asarray(extractor.feature_vector(z), dtype=np.float64)  # type: ignore[no-untyped-call]
                if verify(protection, data, z, float(x[IS_PE])) is not None:
                    return float("nan")
                return abs(f0 - float(gbdt(x[None, :])[0]))
            except Exception:
                return float("nan")

        rows: list[dict[str, Any]] = []
        for rule, instances in task["rules"].items():
            S = np.zeros(m, dtype=np.bool_)
            for offset, length in instances:
                S[offset:offset + length] = True
            lengths = run_lengths(S)
            tau = float(np.percentile(concentration[S], CONCENTRATION_QUANTILE))
            eligible = concentration >= max(tau, np.finfo(np.float64).tiny)
            rng = np.random.default_rng([task["seed"], task["index"], int(np.sum([ord(c) for c in rule]))])
            refs = np.array([response(r) for r in random_run_masks(eligible, lengths, NUM_REFERENCE, rng)])
            valid = refs[np.isfinite(refs)]
            rows.append(base | {
                "rule": rule, "matched": int(S.sum()), "deletable": int((S & ~protection.mask).sum()), "gbdt_log_odds": f0,
                "response": response(S), "valid_references": int(valid.shape[0]),
                "reference_median": float(np.median(valid)) if valid.shape[0] else float("nan"),
                "reference_p95": float(np.percentile(valid, PERCENTILE)) if valid.shape[0] else float("nan"),
                "status": "ok", "error": ""})
        return rows
    except Exception as err:
        return [base | {"rule": "", "status": "error", "error": f"{type(err).__name__}: {err}"[:300]}]


################################################################################
# Summary
################################################################################


def summarize(files: pl.DataFrame, attribution: pl.DataFrame, split: list[str]) -> None:
    """Print, per rule, the share of files above the references by deletion and by attribution, then the check."""
    ok = files.filter((pl.col("status") == "ok") & pl.col("response").is_finite() & (pl.col("valid_references") >= MIN_VALID))
    ok = ok.with_columns((pl.col("response") > pl.col("reference_p95")).alias("above"),
                         (pl.col("response") / pl.col("reference_median")).alias("ratio"))
    per_rule = ok.group_by("rule").agg(
        pl.len().alias("files"), pl.col("above").mean().alias("above_deletion"), pl.col("ratio").median().alias("x_deletion"),
        pl.col("response").median().alias("response"), pl.col("reference_median").median().alias("reference"),
    ).join(attribution, on="rule", how="left").with_columns(pl.col("rule").is_in(split).alias("split"))
    per_rule = per_rule.sort("split", "above_deletion", descending=True)
    dropped = files.height - ok.height
    with pl.Config(tbl_rows=40, fmt_str_lengths=60, float_precision=3, tbl_width_chars=250):
        print(f"\n## Deletion vs. attribution ({dropped} of {files.height} (rule, file) pairs dropped: invalid deletion or "
              f"fewer than {MIN_VALID} valid references)\n")
        print("above_*: share of files where S beats the concentration-matched references' 95th percentile; x_deletion:")
        print("median ratio of S's response to the references' median; response, reference: medians in log-odds.\n")
        print(per_rule)
    s = per_rule.filter(pl.col("split") & pl.col("above_attribution").is_not_null())
    agree = int(((s["above_deletion"] >= RELIED) == (s["above_attribution"] >= RELIED)).sum())
    rho = float(stats.spearmanr(s["above_deletion"], s["above_attribution"]).statistic) if s.height > 2 else float("nan")
    gate = agree > s.height / 2 and rho > 0
    print(f"\n## Check\n\nSplit rules: categories agree for {agree}/{s.height} (need more than half); Spearman rho of the "
          f"shares {rho:.2f} (need > 0). {'HOLDS' if gate else 'DOES NOT HOLD'}")


################################################################################
# Main
################################################################################


def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1] if __doc__ else None)
    parser.add_argument("--seed", type=int, default=0, help="The seed of the GBDT.")
    parser.add_argument("--check", type=Path, default=ROOT / "artifacts" / "experiments" / "yara_check", help="Run 34's output.")
    parser.add_argument("--reliance", type=Path, default=ROOT / "artifacts" / "experiments" / "yara_reliance", help="Run 36's output.")
    parser.add_argument("--pb1_run", type=Path, default=ROOT / "artifacts" / "experiments" / "e1" / "seed-0" / "zeros-typical-header-baselines-ties", help="The PB1 run whose files to reuse.")
    parser.add_argument("--num_files", type=int, default=0, help="Only the first files (0: all), for smoke tests.")
    parser.add_argument("--explanation_set", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--models", type=Path, default=ROOT / "artifacts" / "models")
    parser.add_argument("--db", type=Path, default=EMBER2024_DATA / "ts")
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "yara_deletion")
    parser.add_argument("--num_workers", type=int, default=32)
    args = parser.parse_args()

    outdir = args.outdir / f"seed-{args.seed}"
    outdir.mkdir(parents=True, exist_ok=True)
    check = args.check / f"seed-{args.seed}"
    rules = pl.read_parquet(check / "rules.parquet").filter(pl.col("located").fill_null(False) & (pl.col("status") == "ok"))
    per_rule = rules.group_by("rule").agg(pl.col("index").n_unique().alias("files"), pl.col("max_share_outside").median())
    per_rule = per_rule.filter(pl.col("files") >= MIN_FILES)
    split = per_rule.filter(pl.col("max_share_outside") >= DETERMINED)["rule"].to_list()
    crypto = per_rule.filter(pl.col("rule").str.starts_with("crypto/"))["rule"].to_list()
    chosen = sorted(set(split) | set(crypto))
    matches = pl.read_parquet(check / "matches.parquet").filter(pl.col("rule").is_in(chosen))

    # Run 36's attribution-based share per rule (the concentration-matched reference).
    reliance = pl.read_parquet(args.reliance / f"seed-{args.seed}" / "files.parquet").filter(pl.col("status") == "ok")
    attribution = reliance.group_by("rule").agg((pl.col("reliance") > pl.col("read_p95")).mean().alias("above_attribution"))

    files = pl.read_parquet(args.pb1_run / "files.parquet").filter(pl.col("status") == "ok").select("index", "name", "label")
    location = pl.read_parquet(args.explanation_set).select("name", "shard", "position")
    files = files.join(location, on="name", how="left").sort("index")
    tasks = []
    for r in files.iter_rows(named=True):
        m_ = matches.filter(pl.col("index") == r["index"])
        if m_.height == 0:
            continue
        per_file = {rule: list(zip(g["offset"].to_list(), g["length"].to_list())) for (rule,), g in m_.group_by("rule")}
        tasks.append({"index": int(r["index"]), "name": r["name"], "label": int(r["label"]), "shard": int(r["shard"]),
                      "position": int(r["position"]), "dbdir": args.db, "seed": args.seed, "rules": per_file})
    if args.num_files > 0:
        tasks = tasks[:args.num_files]
    pairs = sum(len(t["rules"]) for t in tasks)
    print(f"3-C deletion check: {len(split)} split + {len(crypto)} crypto rules, {len(tasks)} files, {pairs} (rule, file) "
          f"pairs, {pairs * (NUM_REFERENCE + 1)} deletions.", flush=True)

    gbdt_file = args.models / "gbdt" / f"seed-{args.seed}" / "model.txt"
    tasks.sort(key=lambda t: -len(t["rules"]))
    t_0 = time.time()
    rows: list[dict[str, Any]] = []
    with mp.get_context("fork").Pool(args.num_workers, initializer=_init_worker, initargs=(gbdt_file,)) as pool:
        for r_ in tqdm(pool.imap_unordered(process_file, tasks), total=len(tasks), desc="files", mininterval=10):
            rows += r_
            if r_ and r_[0]["status"] != "ok":
                print(f"File {r_[0]['index']}: {r_[0]['error']}", flush=True)
    seconds = time.time() - t_0
    print(f"Files on {args.num_workers} workers: {seconds:.0f} s.", flush=True)

    files_df = pl.DataFrame(rows, infer_schema_length=None).sort("rule", "index")
    files_df.write_parquet(outdir / "files.parquet")
    report = {"config": {k: v.as_posix() if isinstance(v, Path) else v for k, v in vars(args).items()},
              "num_reference": NUM_REFERENCE, "percentile": PERCENTILE, "rules": chosen, "split": split,
              "seconds": seconds, "failed": int((files_df["status"] != "ok").sum())}
    (outdir / "report.json").write_text(json.dumps(report, indent=2))
    summarize(files_df, attribution, split)


if __name__ == "__main__":
    main()
