"""
3-C, the reliance go/no-go (docs/rules_plan.md): does the GBDT's credit on a rule's matched bytes stand above chance?

For each rule of run 34 with a split (located on at least 5 pilot files, its matched bytes S holding at least half of
a non-aggregate feature in the median file) and each file where it matches, the reliance on S is the pullback of the
GBDT's |TreeSHAP| summed over S (equal to sum_j |a_j| (P^T 1_S)_j, run 34's `credit_abs`). Three references:

    random      200 byte sets with S's run lengths, each run placed at a uniform random offset in the file; S is
                "above random" if its reliance exceeds their 95th percentile (run 35)
    read        the same, but drawn only from bytes whose provenance is at least as concentrated as S's: the
                concentration of byte i is c_i = sum_j P_ij over the non-aggregate features (outside `histogram`,
                `byteentropy`, `general`; P is column-normalized, so a byte of a short imported name holds a large
                share of its hash bucket, a byte of a large section a tiny share of the section's entropy); eligible
                bytes have c_i >= the 25th percentile of c over S. Runs are placed in the sequence of eligible bytes,
                so a run may span a gap between them (run 36; is S credited more than other content the GBDT reads
                as directly?). Nearly every byte has c_i > 0 (median 99.9% of a file), hence the threshold.
    elsewhere   the features S determines (share >= 0.5 in some file), their mean sum of |a_j| on the files where the
                rule fires vs. the pilot files where it does not (no P needed; whether the GBDT weighs them at all)

Go/no-go, fixed in advance (2026-10-12): the reliance side passes if more than half of the split rules are above
random in at least 60% of their files. The `read` reference has no gate: it locates reliance gaps. Also reported, as
information: the signed credit on S (the pullback of TreeSHAP; positive is toward malware).

Outputs, in `{outdir}/seed-{seed}/`:
    files.parquet       one row per (rule, file): |S|, runs, reliance and signed credit on S, each reference's median
                        and 95th percentile
    report.json         the configuration and timing

Usage:
    PYTHONHASHSEED=0 OMP_NUM_THREADS=1 python scripts/yara_reliance.py --seed 0 --num_workers 16
"""

from __future__ import annotations

from argparse import ArgumentParser
import json
import multiprocessing as mp
from pathlib import Path
import sys
import time
from typing import Any

import numpy as np
from numpy import typing as npt
import polars as pl
from tqdm import tqdm

from provexp.featuresets.ember2024.features import PEFeatureExtractor

sys.path.insert(0, str(Path(__file__).parent))

from faithfulness import load_sample  # noqa: E402
from yara_check import AGGREGATE_GROUPS  # noqa: E402
from yara_check import DETERMINED  # noqa: E402
from yara_check import EXPLAINER  # noqa: E402
from yara_check import MIN_FILES  # noqa: E402


__all__ = [
    "random_runs",
    "run_lengths",
]


ROOT = Path(__file__).parent.parent
NUM_RANDOM = 200
PERCENTILE = 95.0
MIN_ABOVE = 0.6

BoolArray = npt.NDArray[np.bool_]
FloatArray = npt.NDArray[np.float64]
IntArray = npt.NDArray[np.int64]

_STATE: dict[str, Any] = {}


################################################################################
# Random Sets
################################################################################


def run_lengths(mask: BoolArray) -> IntArray:
    """The lengths of the maximal runs of contiguous selected elements."""
    x = np.concatenate([[0], mask.astype(np.int8), [0]])
    d = np.diff(x)
    return (np.flatnonzero(d == -1) - np.flatnonzero(d == 1)).astype(np.int64)


def random_runs(cumsum: FloatArray, lengths: IntArray, num: int, rng: np.random.Generator) -> FloatArray:
    """The sum of a per-element score over `num` random sets, each run of `lengths` at a uniform random offset (runs may overlap)."""
    m = cumsum.shape[0] - 1
    if lengths.max(initial=0) > m:
        raise ValueError(f"A run of {lengths.max()} elements does not fit in {m}.")
    starts = rng.integers(0, m - lengths[None, :] + 1, size=(num, lengths.shape[0]))
    return np.asarray((cumsum[starts + lengths[None, :]] - cumsum[starts]).sum(axis=1), dtype=np.float64)


################################################################################
# Per File
################################################################################


def _init_worker() -> None:
    _STATE["extractor"] = PEFeatureExtractor()
    groups = np.array([n.split(":")[0] for n in _STATE["extractor"].feature_names])
    _STATE["outside"] = (~np.isin(groups, AGGREGATE_GROUPS)).astype(np.float64)


def process_file(task: dict[str, Any]) -> list[dict[str, Any]]:
    """The reliance on each split rule's matched bytes in one file, against random sets with the same runs."""
    base = {"index": task["index"], "label": task["label"]}
    try:
        data = load_sample(task["shard"], task["position"], task["name"], task["dbdir"])
        m = len(data)
        _, prov = _STATE["extractor"].feature_vector_with_provenance(data)
        score = prov.pullback(np.abs(task["explanation"]))[:m]
        signed = prov.pullback(task["explanation"])[:m]
        cumsum = np.concatenate([[0.0], np.cumsum(score)])
        concentration = prov.matvec(_STATE["outside"])[:m]
        rows: list[dict[str, Any]] = []
        for rule, instances in task["rules"].items():
            S = np.zeros(m, dtype=np.bool_)
            for offset, length in instances:
                S[offset:offset + length] = True
            lengths = run_lengths(S)
            rng = np.random.default_rng([task["seed"], task["index"], int(np.sum([ord(c) for c in rule]))])
            r = random_runs(cumsum, lengths, NUM_RANDOM, rng)
            s = float(score[S].sum())
            # The eligible bytes, at least as concentrated as most of S, and the score in their sequence.
            tau = float(np.percentile(concentration[S], 25))
            read = concentration >= max(tau, np.finfo(np.float64).tiny)
            if lengths.max(initial=0) <= int(read.sum()):
                cumsum_read = np.concatenate([[0.0], np.cumsum(score[read])])
                r_read = random_runs(cumsum_read, lengths, NUM_RANDOM, rng)
            else:
                r_read = np.full(NUM_RANDOM, np.nan)
            rows.append(base | {"rule": rule, "matched": int(S.sum()), "runs": int(lengths.shape[0]),
                                "matched_read": int((S & read).sum()), "read": int(read.sum()), "tau": tau, "reliance": s,
                                "signed": float(signed[S].sum()),
                                "random_median": float(np.median(r)), "random_p95": float(np.percentile(r, PERCENTILE)),
                                "percentile": float((r < s).mean()),
                                "read_median": float(np.median(r_read)), "read_p95": float(np.percentile(r_read, PERCENTILE)),
                                "total": float(np.abs(task["explanation"]).sum()), "status": "ok", "error": ""})
        return rows
    except Exception as err:
        return [base | {"rule": "", "status": "error", "error": f"{type(err).__name__}: {err}"[:300]}]


################################################################################
# Summary
################################################################################


def summarize(files: pl.DataFrame, elsewhere: pl.DataFrame) -> None:
    """Print, per rule, the share of files above random and the elsewhere contrast, then the go/no-go."""
    ok = files.filter(pl.col("status") == "ok").with_columns(
        (pl.col("reliance") > pl.col("random_p95")).alias("above"),
        (pl.col("reliance") / pl.col("random_median")).alias("ratio"),
        (pl.col("reliance") > pl.col("read_p95")).alias("above_read"),
        (pl.col("reliance") / pl.col("read_median")).alias("ratio_read"),
        (pl.col("reliance") / pl.col("total")).alias("share"))
    per_rule = ok.group_by("rule").agg(
        pl.len().alias("files"), pl.col("above").mean().alias("above_random"), pl.col("ratio").median().alias("x_random"),
        pl.col("above_read").mean().alias("above_read"), pl.col("ratio_read").median().alias("x_read"),
        (pl.col("signed") > 0).mean().alias("toward_malware"), pl.col("signed").median().alias("signed"),
        pl.col("share").median().alias("share_of_total"), pl.col("matched").median().alias("matched"),
    ).join(elsewhere, on="rule", how="left").sort("above_read", descending=True)
    passing = per_rule.filter(pl.col("above_random") >= MIN_ABOVE).height
    with pl.Config(tbl_rows=40, fmt_str_lengths=60, float_precision=3, tbl_width_chars=250):
        print("\n## Reliance on the matched bytes vs. random sets with the same runs\n")
        print("above_random: share of files where S beats the random sets' 95th percentile; x_random: median ratio to the")
        print("random median; above_read, x_read: the same against sets drawn from bytes as concentrated as S's;")
        print("toward_malware: share of files where the signed credit on S is positive; signed: its median; elsewhere: the")
        print("determined features' mean sum |a_j| where the rule fires / where it does not.\n")
        print(per_rule)
    gate = passing > per_rule.height / 2
    print(f"\n## Go/no-go\n\n{passing}/{per_rule.height} rules above random in >= {MIN_ABOVE:.0%} of their files "
          f"(need more than half). {'GO' if gate else 'NO-GO'}")


################################################################################
# Main
################################################################################


def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1] if __doc__ else None)
    parser.add_argument("--seed", type=int, default=0, help="The seed of the GBDT whose TreeSHAP to use.")
    parser.add_argument("--check", type=Path, default=ROOT / "artifacts" / "experiments" / "yara_check", help="Run 34's output.")
    parser.add_argument("--pb1_run", type=Path, default=ROOT / "artifacts" / "experiments" / "e1" / "seed-0" / "zeros-typical-header-baselines-ties", help="The PB1 run whose files to reuse.")
    parser.add_argument("--explanations", type=Path, default=ROOT / "artifacts" / "explanations" / "ember2024")
    parser.add_argument("--explanation_set", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "yara_reliance")
    parser.add_argument("--num_workers", type=int, default=16)
    args = parser.parse_args()

    outdir = args.outdir / f"seed-{args.seed}"
    outdir.mkdir(parents=True, exist_ok=True)
    check = args.check / f"seed-{args.seed}"
    rules = pl.read_parquet(check / "rules.parquet").filter(pl.col("located").fill_null(False) & (pl.col("status") == "ok"))
    split = rules.group_by("rule").agg(pl.col("index").n_unique().alias("files"), pl.col("max_share_outside").median())
    split = split.filter((pl.col("files") >= MIN_FILES) & (pl.col("max_share_outside") >= DETERMINED))["rule"]
    matches = pl.read_parquet(check / "matches.parquet").filter(pl.col("rule").is_in(split.implode()))
    files = pl.read_parquet(args.pb1_run / "files.parquet").filter(pl.col("status") == "ok").select("index", "name", "label")
    location = pl.read_parquet(args.explanation_set).select("name", "shard", "position")
    files = files.join(location, on="name", how="left").sort("index")
    explanations = np.load(args.explanations / f"seed-{args.seed}" / f"{EXPLAINER}.npy", mmap_mode="r")
    print(f"3-C reliance go/no-go: {split.len()} split rules, {matches['index'].n_unique()} files.", flush=True)

    # The elsewhere contrast needs no provenance: the determined features' |TreeSHAP| on firing vs. other pilot files.
    features = pl.read_parquet(check / "features.parquet").filter(pl.col("rule").is_in(split.implode()) & (pl.col("share") >= DETERMINED))
    absolute = np.abs(np.asarray(explanations[files["index"].to_numpy()], dtype=np.float64))
    position = {int(i): k for k, i in enumerate(files["index"])}
    elsewhere = []
    for rule in split:
        determined = features.filter(pl.col("rule") == rule)["feature"].unique().to_numpy()
        fires = np.zeros(files.height, dtype=np.bool_)
        fires[[position[int(i)] for i in matches.filter(pl.col("rule") == rule)["index"].unique()]] = True
        mass = absolute[:, determined].sum(axis=1)
        elsewhere.append({"rule": rule, "determined": int(determined.shape[0]),
                          "elsewhere": float(mass[fires].mean() / mass[~fires].mean()) if mass[~fires].mean() > 0 else float("inf")})

    tasks = []
    for r in files.iter_rows(named=True):
        m_ = matches.filter(pl.col("index") == r["index"])
        if m_.height == 0:
            continue
        per_rule = {rule: list(zip(g["offset"].to_list(), g["length"].to_list()))
                    for (rule,), g in m_.group_by("rule")}
        tasks.append({"index": int(r["index"]), "name": r["name"], "label": int(r["label"]), "shard": int(r["shard"]),
                      "position": int(r["position"]), "dbdir": args.db, "seed": args.seed, "rules": per_rule,
                      "explanation": np.asarray(explanations[int(r["index"])], dtype=np.float64)})
    t_0 = time.time()
    rows: list[dict[str, Any]] = []
    with mp.get_context("fork").Pool(args.num_workers, initializer=_init_worker) as pool:
        for r_ in tqdm(pool.imap_unordered(process_file, tasks), total=len(tasks), desc="files", mininterval=10):
            rows += r_
            if r_ and r_[0]["status"] != "ok":
                print(f"File {r_[0]['index']}: {r_[0]['error']}", flush=True)
    seconds = time.time() - t_0
    print(f"Files on {args.num_workers} workers: {seconds:.0f} s.", flush=True)

    files_df = pl.DataFrame(rows, infer_schema_length=None).sort("rule", "index")
    files_df.write_parquet(outdir / "files.parquet")
    report = {"config": {k: v.as_posix() if isinstance(v, Path) else v for k, v in vars(args).items()},
              "explainer": EXPLAINER, "num_random": NUM_RANDOM, "percentile": PERCENTILE, "seconds": seconds,
              "rules": split.to_list(), "failed": int((files_df["status"] != "ok").sum())}
    (outdir / "report.json").write_text(json.dumps(report, indent=2))
    summarize(files_df, pl.DataFrame(elsewhere))


if __name__ == "__main__":
    main()
