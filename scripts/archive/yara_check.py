"""
3-C go/no-go (PLAN.md, 3-C): do generic YARA rules match PB1's pilot files often enough, at byte locations, and do
the matched bytes determine any non-aggregate GBDT feature?

Each pilot file (run 21) is scanned with the generic Yara-Rules sets (`packers/`, `crypto/`, `antidebug_antivm/`,
`capabilities/`). For each (file, rule) with string matches, S = the union of the matched bytes, and, from one
instrumented extraction of the file:

    share_j     (P^T 1_S)_j, the share of feature j's provenance in S (1: S computes all of feature j)
    profile     the pushforward psi(1_S) summed by feature group (the prefix of the feature name)
    credit      the GBDT's interventional TreeSHAP credit S carries, sum_j a_j share_j, against sum_j |a_j|

Rules that fire only through conditions (e.g., the `pe` module) have no byte location and are counted separately.

Go/no-go, fixed in advance (2026-10-12; a failure of either is a no-go at pilot scale):
    1. Coverage: at least 10 rules with located matches on at least 5 pilot files each, and at least 60% of the
       malware files matched by one of them.
    2. A non-empty split: for at least a third of those rules, in the median file where the rule matches, S holds at
       least half of some feature outside the whole-file aggregates (`histogram`, `byteentropy`, `general`).

Outputs, in `{outdir}/seed-{seed}/`:
    matches.parquet     one row per (file, rule, string instance): offset and length
    rules.parquet       one row per (file, rule): sizes, the largest share, the profile by group, the credit
    features.parquet    one row per (file, rule, feature) with share_j >= 0.05: the share, psi_j, and a_j
    report.json         the configuration and timing

Usage:
    PYTHONHASHSEED=0 OMP_NUM_THREADS=1 python scripts/yara_check.py --seed 0 --num_workers 16
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
import yara  # type: ignore[import-not-found]

from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.data.paths import EMBER2024_DATA

sys.path.insert(0, str(Path(__file__).parent))

from faithfulness import load_sample  # noqa: E402


__all__ = [
    "compile_rules",
    "located_matches",
]


ROOT = Path(__file__).parent.parent
EXPLAINER = "treeshap_interventional"
RULE_DIRS = ("packers", "crypto", "antidebug_antivm", "capabilities")
# Whole-file aggregates: every byte contributes, so a few matched bytes can never hold much of them.
AGGREGATE_GROUPS = ("histogram", "byteentropy", "general")
MIN_SHARE = 0.05  # The smallest share kept in features.parquet.
DETERMINED = 0.5  # S "determines" feature j if it holds at least this share of j's provenance.
MIN_FILES = 5
MIN_RULES = 10
MIN_MALWARE = 0.6
MIN_SPLIT = 1 / 3

BoolArray = npt.NDArray[np.bool_]
FloatArray = npt.NDArray[np.float64]

_STATE: dict[str, Any] = {}


################################################################################
# Rules
################################################################################


def compile_rules(rules_dir: Path, dirs: tuple[str, ...] = RULE_DIRS) -> Any:
    """Compile every `.yar` file in the given rule directories, one namespace per file (`dir/file`)."""
    filepaths: dict[str, str] = {}
    for d in dirs:
        files = sorted((rules_dir / d).glob("*.yar"))
        if not files:
            raise RuntimeError(f"No rules in {rules_dir / d}.")
        for f in files:
            filepaths[f"{d}/{f.stem}"] = str(f)
    return yara.compile(filepaths=filepaths)


def located_matches(rules: Any, data: bytes, timeout: int) -> tuple[list[dict[str, Any]], list[str]]:
    """The string-match instances of every rule that fires (rule, string, offset, length), and the rules that fire without any."""
    located: list[dict[str, Any]] = []
    unlocated: list[str] = []
    for match in rules.match(data=data, timeout=timeout):
        rule = f"{match.namespace}:{match.rule}"
        instances = [(s.identifier, i.offset, i.matched_length) for s in match.strings for i in s.instances]
        if not instances:
            unlocated.append(rule)
        for identifier, offset, length in instances:
            located.append({"rule": rule, "string": identifier, "offset": int(offset), "length": int(length)})
    return located, unlocated


################################################################################
# Per File
################################################################################


def _init_worker(rules_dir: Path) -> None:
    _STATE["rules"] = compile_rules(rules_dir)
    _STATE["extractor"] = PEFeatureExtractor()
    names = _STATE["extractor"].feature_names
    _STATE["groups"] = np.array([n.split(":")[0] for n in names])


def process_file(task: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Scan one file and describe, for each rule with located matches, the features its matched bytes compute."""
    t_0 = time.perf_counter()
    base = {"index": task["index"], "name": task["name"], "label": task["label"]}
    try:
        data = load_sample(task["shard"], task["position"], task["name"], task["dbdir"])
        m = len(data)
        located, unlocated = located_matches(_STATE["rules"], data, task["timeout"])
        t_scan = time.perf_counter() - t_0
        matches = [base | r for r in located]
        rows: list[dict[str, Any]] = [base | {"rule": r, "located": False} for r in sorted(set(unlocated))]
        features: list[dict[str, Any]] = []
        if located:
            _, prov = _STATE["extractor"].feature_vector_with_provenance(data)
            if prov.num_elements != m:
                raise RuntimeError(f"Provenance has {prov.num_elements} elements for a file of {m} bytes.")
            groups: npt.NDArray[np.str_] = _STATE["groups"]
            outside = ~np.isin(groups, AGGREGATE_GROUPS)
            a = task["explanation"]
            pullback = prov.pullback(a)[:m]
            total = float(np.abs(a).sum())
            for rule in sorted({r["rule"] for r in located}):
                S = np.zeros(m, dtype=np.bool_)
                for r in located:
                    if r["rule"] == rule:
                        S[r["offset"]:r["offset"] + r["length"]] = True
                b = np.append(S, False).astype(np.float64) if prov.has_null else S.astype(np.float64)
                share = prov.rmatvec(b)
                psi = prov.pushforward(b)
                credit = a * share
                row: dict[str, Any] = {
                    "rule": rule, "located": True, "size": m, "matched": int(S.sum()),
                    "max_share": float(share.max()), "max_share_outside": float(share[outside].max()),
                    "determined": int((share >= DETERMINED).sum()),
                    "determined_outside": int(((share >= DETERMINED) & outside).sum()),
                    "credit": float(credit.sum()), "credit_abs": float(np.abs(credit).sum()), "total_abs": total,
                    "pullback_on_s": float(pullback[S].sum()), "gbdt_log_odds": task["gbdt_log_odds"],
                }
                psi_total = float(psi.sum())
                for g in np.unique(groups):
                    row[f"psi:{g}"] = float(psi[groups == g].sum()) / psi_total if psi_total > 0 else float("nan")
                rows.append(base | row)
                for j in np.flatnonzero(share >= MIN_SHARE):
                    features.append(base | {"rule": rule, "feature": int(j), "share": float(share[j]),
                                            "psi": float(psi[j]), "attribution": float(a[j])})
        seconds = time.perf_counter() - t_0
        rows = [r | {"status": "ok", "error": "", "seconds_scan": t_scan, "seconds": seconds} for r in rows]
        if not rows:
            rows = [base | {"rule": "", "located": False, "status": "ok", "error": "", "seconds_scan": t_scan, "seconds": seconds}]
        return rows, matches, features
    except Exception as err:
        return [base | {"rule": "", "status": "error", "error": f"{type(err).__name__}: {err}"[:300]}], [], []


################################################################################
# Summary
################################################################################


def summarize(rules: pl.DataFrame, features: pl.DataFrame, num_files: int, num_malware: int, names: list[str]) -> None:
    """Print coverage by rule directory, the go/no-go, and the qualifying rules' profiles."""
    ok = rules.filter((pl.col("status") == "ok") & (pl.col("rule") != ""))
    ok = ok.with_columns(pl.col("rule").str.split("/").list.first().alias("dir"))
    loc = ok.filter(pl.col("located"))
    print(f"\n## Coverage ({num_files} files, {num_malware} malware)\n")
    print("| rule directory | rules firing | located | located on >= 5 files | malware files located | benign files located |")
    print("|---|---|---|---|---|---|")
    for d in RULE_DIRS:
        f, lf = ok.filter(pl.col("dir") == d), loc.filter(pl.col("dir") == d)
        per_rule = lf.group_by("rule").agg(pl.col("index").n_unique().alias("files"))
        print(f"| {d} | {f['rule'].n_unique()} | {lf['rule'].n_unique()} | {int((per_rule['files'] >= MIN_FILES).sum())} | "
              f"{lf.filter(pl.col('label') == 1)['index'].n_unique()} | {lf.filter(pl.col('label') == 0)['index'].n_unique()} |")

    per_rule = loc.group_by("rule", "dir").agg(
        pl.col("index").n_unique().alias("files"),
        (pl.col("label") == 1).sum().alias("malware"),
        pl.col("matched").median().alias("matched_bytes"),
        pl.col("max_share_outside").median().alias("max_share_outside"),
        pl.col("determined_outside").median().alias("determined_outside"),
        (pl.col("credit_abs") / pl.col("total_abs")).median().alias("credit_abs_share"),
        pl.col("credit").median().alias("credit"),
    ).sort("files", descending=True)
    qualifying = per_rule.filter(pl.col("files") >= MIN_FILES)
    covered = loc.filter(pl.col("rule").is_in(qualifying["rule"].implode()) & (pl.col("label") == 1))["index"].n_unique()
    split = qualifying.filter(pl.col("max_share_outside") >= DETERMINED)
    gate_1 = qualifying.height >= MIN_RULES and covered >= MIN_MALWARE * num_malware
    gate_2 = qualifying.height > 0 and split.height >= MIN_SPLIT * qualifying.height
    print("\n## Go/no-go\n")
    print(f"1. Coverage: {qualifying.height} rules located on >= {MIN_FILES} files (need {MIN_RULES}); malware files "
          f"matched by one of them {covered}/{num_malware} (need {MIN_MALWARE:.0%}). {'PASS' if gate_1 else 'FAIL'}")
    print(f"2. Split: {split.height}/{qualifying.height} of those rules hold >= {DETERMINED} of a non-aggregate feature in "
          f"the median file (need {MIN_SPLIT:.2f}). {'PASS' if gate_2 else 'FAIL'}")
    for d in RULE_DIRS:
        q = qualifying.filter(pl.col("dir") == d)
        print(f"   {d}: {q.height} qualifying, {q.filter(pl.col('max_share_outside') >= DETERMINED).height} with a split")
    print(f"\n{'GO' if gate_1 and gate_2 else 'NO-GO'}")

    with pl.Config(tbl_rows=60, fmt_str_lengths=70, float_precision=3, tbl_width_chars=200):
        print("\n## Qualifying rules (median over the files where each matches)\n")
        print(qualifying)
        # The pushforward's top feature group per rule (the mode over its files), and how often it differs.
        psi_cols = [c for c in loc.columns if c.startswith("psi:")]
        prof = loc.filter(pl.col("rule").is_in(qualifying["rule"].implode()))
        top = prof.with_columns(pl.Series("top_group", [psi_cols[int(np.nanargmax(r))][4:] if np.isfinite(r).any() else ""
                                                        for r in prof.select(psi_cols).to_numpy()]))
        mode = top.group_by("rule").agg(pl.col("top_group").mode().first().alias("top_group"),
                                        (pl.col("top_group") != pl.col("top_group").mode().first()).mean().alias("differs"))
        print("\n## The pushforward's top feature group per rule (the mode over files; share of files where it differs)\n")
        print(mode.sort("rule"))
        feats = features.filter((pl.col("share") >= DETERMINED) & pl.col("rule").is_in(qualifying["rule"].implode()))
        feats = feats.group_by("rule", "feature").agg(pl.len().alias("files"), pl.col("attribution").mean())
        feats = feats.with_columns(pl.col("feature").map_elements(lambda j: names[j], return_dtype=pl.String).alias("name"))
        print("\n## Features determined (share >= 0.5) by qualifying rules, outside the aggregates (top 40 by files)\n")
        feats = feats.filter(~pl.col("name").str.split(":").list.first().is_in(list(AGGREGATE_GROUPS)))
        print(feats.sort("files", descending=True).head(40).select("rule", "name", "files", "attribution"))


################################################################################
# Main
################################################################################


def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1] if __doc__ else None)
    parser.add_argument("--seed", type=int, default=0, help="The seed of the GBDT whose TreeSHAP to use.")
    parser.add_argument("--pb1_run", type=Path, default=ROOT / "artifacts" / "experiments" / "e1" / "seed-0" / "zeros-typical-header-baselines-ties", help="The PB1 run whose files to reuse.")
    parser.add_argument("--num_files", type=int, default=0, help="Only the first files per label (0: all), for smoke tests.")
    parser.add_argument("--rules_dir", type=Path, default=ROOT / "artifacts" / "rules" / "yara-rules")
    parser.add_argument("--timeout", type=int, default=120, help="YARA's scan timeout per file, in seconds.")
    parser.add_argument("--explanations", type=Path, default=ROOT / "artifacts" / "explanations" / "ember2024")
    parser.add_argument("--explanation_set", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--db", type=Path, default=EMBER2024_DATA / "ts")
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "yara_check")
    parser.add_argument("--num_workers", type=int, default=16)
    args = parser.parse_args()

    outdir = args.outdir / f"seed-{args.seed}"
    outdir.mkdir(parents=True, exist_ok=True)
    files = pl.read_parquet(args.pb1_run / "files.parquet").filter(pl.col("status") == "ok")
    if args.num_files > 0:
        files = pl.concat([files.filter(pl.col("label") == lab).sort("index").head(args.num_files) for lab in (0, 1)])
    location = pl.read_parquet(args.explanation_set).select("name", "shard", "position")
    files = files.select("index", "name", "label", "log_odds:gbdt").join(location, on="name", how="left").sort("index")
    explanations = np.load(args.explanations / f"seed-{args.seed}" / f"{EXPLAINER}.npy", mmap_mode="r")
    print(f"3-C YARA go/no-go: {files.height} files, rule directories {list(RULE_DIRS)}.", flush=True)

    tasks = [{"index": int(r["index"]), "name": r["name"], "label": int(r["label"]), "shard": int(r["shard"]),
              "position": int(r["position"]), "dbdir": args.db, "timeout": args.timeout,
              "explanation": np.asarray(explanations[int(r["index"])], dtype=np.float64),
              "gbdt_log_odds": float(r["log_odds:gbdt"])} for r in files.iter_rows(named=True)]
    t_0 = time.time()
    rows: list[dict[str, Any]] = []
    matches: list[dict[str, Any]] = []
    features: list[dict[str, Any]] = []
    with mp.get_context("fork").Pool(args.num_workers, initializer=_init_worker, initargs=(args.rules_dir,)) as pool:
        for r_, m_, f_ in tqdm(pool.imap_unordered(process_file, tasks), total=len(tasks), desc="files", mininterval=10):
            rows += r_
            matches += m_
            features += f_
            if r_ and r_[0]["status"] != "ok":
                print(f"File {r_[0]['index']}: {r_[0]['error']}", flush=True)
    seconds = time.time() - t_0
    print(f"Files on {args.num_workers} workers: {seconds:.0f} s.", flush=True)

    rules_df = pl.DataFrame(rows, infer_schema_length=None).sort("index", "rule")
    matches_df = pl.DataFrame(matches, schema={"index": pl.Int64, "name": pl.String, "label": pl.Int64, "rule": pl.String,
                                               "string": pl.String, "offset": pl.Int64, "length": pl.Int64})
    features_df = pl.DataFrame(features, schema={"index": pl.Int64, "name": pl.String, "label": pl.Int64, "rule": pl.String,
                                                 "feature": pl.Int64, "share": pl.Float64, "psi": pl.Float64,
                                                 "attribution": pl.Float64})
    rules_df.write_parquet(outdir / "rules.parquet")
    matches_df.write_parquet(outdir / "matches.parquet")
    features_df.write_parquet(outdir / "features.parquet")
    report = {"config": {k: v.as_posix() if isinstance(v, Path) else v for k, v in vars(args).items()},
              "explainer": EXPLAINER, "rule_dirs": list(RULE_DIRS), "yara": yara.__version__, "seconds": seconds,
              "failed": int(rules_df.filter(pl.col("status") != "ok")["index"].n_unique())}
    (outdir / "report.json").write_text(json.dumps(report, indent=2))
    summarize(rules_df, features_df, files.height, int((files["label"] == 1).sum()), PEFeatureExtractor().feature_names)


if __name__ == "__main__":
    main()
