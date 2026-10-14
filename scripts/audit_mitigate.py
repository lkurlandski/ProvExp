"""
M3, test-time half (docs/experiments/mocks.md, M3; revision plan item 11): does the audit's countermeasure work, and what
does it cost?

The audit (Section 5.3) found header fields MalConv relies on that an attacker can change without breaking the program.
The countermeasure is to stop reading them: before MalConv scores a file, overwrite the audited fields with zeros, at
the bytes the file's own P names for each. Only fields an attacker could change are zeroed (the loader-ignored `FREE`
and the valid-value `CONSTRAINED` fields of scripts/audit_evade.py); a field the loader needs stays. Defenses:

    none          MalConv as it is;
    pushforward   the pushforward-confirmed fields an attacker can change, zeroed;
    union         the same for the pushforward's and the surrogate's confirmed fields together.

Two questions, each under every defense:

    cost      MalConv's threshold is re-set to a 1% false-positive rate on benign held-out files under that defense,
              and the detection rate is measured on held-out malware;
    evasion   run 49's loader-safe attacks (the same files, recipes, and seeds as scripts/audit_evade.py
              --realizable --broad_null), applied to the malware each defense detects: the pushforward's fields, the
              surrogate's, their union, and the null of as many other loader-ignored fields outside the DOS region.

An attack on fields the defense zeroes is undone by construction; the informative numbers are the cost and the evasion
by fields the defense does not cover (does the attacker just move?). The attacked files keep their section layout
(checked), so the defense zeroes the field locations of the original file.

Outputs, in `{outdir}/{run_name}/`:
    files.parquet     one row per file (benign and malware): status and MalConv's log-odds under each defense
    attacks.parquet   one row per (malware, recipe, draw): parsed, and MalConv's log-odds under each defense
    summary.parquet   one row per (defense, recipe): thresholds, detection, evasion with a bootstrap 95% CI
    report.json       the configuration, the defended fields, and timing

Usage:
    PYTHONHASHSEED=0 OMP_NUM_THREADS=1 python scripts/audit_mitigate.py --seed 0 --num_workers 16
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

import numpy as np
from numpy import typing as npt
import polars as pl
from tqdm import tqdm

from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBIterator
from provexp.featuresets.ember2024.ablation import parse
from provexp.featuresets.ember2024.features import PEFeatureExtractor

sys.path.insert(0, str(Path(__file__).parent))
import shortcuts_transplant as st  # noqa: E402
from audit_evade import CONSTRAINED  # noqa: E402
from audit_evade import FREE  # noqa: E402
from audit_evade import FREE_EXTRA  # noqa: E402
from audit_evade import _EXECUTABLE_ONLY  # noqa: E402
from audit_evade import _scramble_features  # noqa: E402
from audit_evade import benign_pools  # noqa: E402
from audit_evade import in_dos_region  # noqa: E402
from audit_evade import realizable_plan  # noqa: E402
from audit_evade import recipe_features  # noqa: E402


__all__ = [
    "defended_fields",
    "detection_threshold",
    "zero_fields",
]


ROOT = Path(__file__).parent.parent
DEFENSES = ("none", "pushforward", "union")
ATTACKS = ("pushforward_realizable", "surrogate_realizable", "union_realizable", "random_free_broad_nondos")
FPR = 0.01


################################################################################
# Defense
################################################################################


def defended_fields(confirmed: list[str]) -> list[str]:
    """The confirmed fields an attacker can change (loader-ignored or valid-value), which the defense zeroes."""
    return [name for name in confirmed if name in FREE or name in CONSTRAINED]


def zero_fields(data: bytes, runs: dict[int, list[tuple[int, int]]], features: list[int], max_content: int) -> bytes:
    """
    Overwrite every locatable run of each feature in `features` with zeros.

    Args:
        data: The file's bytes.
        runs: Feature -> its runs of contiguous bytes in the file, (start, length).
        features: The feature columns to zero.
        max_content: Features whose runs cover more bytes than this are left alone (not locatable).

    Returns:
        The defended bytes, of the same length.
    """
    for j in features:
        spans = runs.get(j, [])
        total = sum(n for _, n in spans)
        if total == 0 or total > max_content:
            continue
        for start, n in spans:
            data = st.overwrite(data, start, bytes(n))
    return data


def detection_threshold(benign: npt.NDArray[np.float64], fpr: float = FPR) -> float:
    """The smallest threshold that flags at most a fraction `fpr` of `benign` (flagged: score above the threshold)."""
    if benign.size == 0:
        raise ValueError("Need benign scores to set a threshold.")
    if not 0.0 <= fpr < 1.0:
        raise ValueError(f"Expected a false-positive rate in [0, 1). Got {fpr}.")
    s = np.sort(benign)[::-1]
    k = int(np.floor(fpr * s.size))
    return float(s[k])


################################################################################
# Workers
################################################################################


def process_shard(
    shard: int,
    samples: list[dict[str, Any]],
    dbdir: Path,
    defenses: dict[str, list[int]],
    recipes: dict[str, list[int]],
    realizable: dict[str, Any],
    num_random: int,
    random_retries: int,
    max_content: int,
    seed: int,
    timeout: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Score each file under every defense; for malware, also each attack under every defense."""
    assert st._EXTRACTOR is not None and st._MALCONV is not None
    needed = np.array(sorted({j for js in [*defenses.values(), *recipes.values()] for j in js}
                             | set(realizable["broad_pool"])), dtype=np.int64)
    wanted = {s["position"]: i for i, s in enumerate(samples)}
    files: list[dict[str, Any]] = []
    attacks: list[dict[str, Any]] = []
    db = SimpleDB(dbdir, check=False)
    names, index = realizable["names"], realizable["index"]

    for position, sample in enumerate(SimpleDBIterator(db).iter(shard)):
        if position not in wanted:
            continue
        meta = samples[wanted[position]]
        if sample.name != meta["name"]:
            raise RuntimeError(f"Shard {shard}, position {position} holds {sample.name}, not {meta['name']}.")
        base = {"index": meta["index"], "name": meta["name"], "label": meta["label"]}
        signal.alarm(timeout)
        try:
            data = bytes(sample.data)
            original = parse(data)
            if original.status != "ok":
                files.append(base | {"status": "not_pe"})
                continue
            x, prov = st._EXTRACTOR.feature_vector_with_provenance(data)
            x = np.asarray(x, dtype=np.float64)
            runs = st.feature_runs(prov, needed)

            def scores(z: bytes) -> dict[str, float]:
                return {f"score:{d}": st.score(zero_fields(z, runs, js, max_content)) for d, js in defenses.items()}

            files.append(base | {"status": "ok"} | scores(data))
            if meta["label"] != 1:
                continue

            # Run 49's attacks, with its seeds (scripts/audit_evade.py, process_shard).
            key = int(meta["index"])

            def attack(name: str, feats: list[int], rng: np.random.Generator, values: Optional[dict[int, int]] = None,
                       redraw: Any = None, draw: int = 0) -> None:
                attempts = 0
                while True:
                    modified, _, changed = _scramble_features(data, runs, feats, max_content, rng, values)
                    p = parse(modified)
                    ok = p.status == "ok" and p.layout == original.layout
                    if ok or redraw is None or attempts >= random_retries:
                        break
                    attempts += 1
                    feats = redraw()
                row = base | {"recipe": name, "draw": draw, "num_features": changed, "parsed": ok}
                attacks.append(row | (scores(modified) if ok else {f"score:{d}": float("nan") for d in defenses}))

            k_free = 0
            for name in ("pushforward", "surrogate", "union"):
                rng = np.random.default_rng([seed, key, 200 + abs(hash(name)) % 1000])
                free, values = realizable_plan(x, index, recipes[name], names, realizable["pools"], rng)
                attack(f"{name}_realizable", free, rng, values)
                if name == "pushforward":
                    k_free = len(free) + len(values)
            is_dll = x[index["header:characteristics_DLL"]] > 0
            broad = [int(j) for j in realizable["broad_pool"]
                     if 0 < sum(n for _, n in runs.get(int(j), [])) <= max_content
                     and not (names[j] in _EXECUTABLE_ONLY and is_dll) and not in_dos_region(names[j])]
            for r in range(num_random):
                rng = np.random.default_rng([seed, key, 700 + r])
                k = min(k_free, len(broad))

                def draw_broad(rng: np.random.Generator = rng, k: int = k) -> list[int]:
                    return rng.choice(broad, size=k, replace=False).tolist() if k else []

                attack("random_free_broad_nondos", draw_broad(), rng, redraw=draw_broad, draw=r)
        except st.TransplantTimeout:
            files.append(base | {"status": "timeout"})
        except Exception as err:
            files.append(base | {"status": "error", "error": f"{type(err).__name__}: {err}"[:300]})
        finally:
            signal.alarm(0)
    return files, attacks


def _star(task: tuple[Any, ...]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return process_shard(*task)


################################################################################
# Summary
################################################################################


def summarize(files: pl.DataFrame, attacks: pl.DataFrame, original_threshold: float, num_boot: int = 10_000,
              seed: int = 0) -> pl.DataFrame:
    """Per (defense, recipe): the re-set threshold, detection, and the evasion rate over detected malware with a CI."""
    rng = np.random.default_rng(seed)
    ok = files.filter(pl.col("status") == "ok")
    rows = []
    # The defenses at their re-set thresholds, and no defense at the original threshold (run 49's, as a check).
    for d, original in [(d, False) for d in DEFENSES] + [("none", True)]:
        col = f"score:{d}"
        benign = ok.filter(pl.col("label") == 0)[col].to_numpy()
        malware = ok.filter(pl.col("label") == 1)
        t = original_threshold if original else detection_threshold(benign)
        detected = malware.filter(pl.col(col) > t)["index"]
        common = {"defense": d + (" (original threshold)" if original else ""), "threshold": t,
                  "benign": benign.size, "malware": malware.height,
                  "detection": float((malware[col].to_numpy() > t).mean()), "fpr": float((benign > t).mean())}
        a = attacks.filter(pl.col("parsed") & pl.col("index").is_in(detected.implode()))
        for recipe in ATTACKS:
            per_file = a.filter(pl.col("recipe") == recipe).group_by("index").agg((pl.col(col) <= t).cast(pl.Float64).mean())
            e = per_file[col].to_numpy()
            boot = e[rng.integers(0, e.size, size=(num_boot, e.size))].mean(axis=1) if e.size else np.array([np.nan])
            rows.append(common | {"recipe": recipe, "files": e.size, "evasion": float(e.mean()) if e.size else float("nan"),
                                  "ci_low": float(np.quantile(boot, 0.025)), "ci_high": float(np.quantile(boot, 0.975))})
    return pl.DataFrame(rows)


def print_summary(summary: pl.DataFrame) -> None:
    print("\nCost: MalConv's threshold re-set to 1% FPR on the benign files under each defense.")
    for r in summary.unique("defense", maintain_order=True).iter_rows(named=True):
        print(f"  {r['defense']:34s} threshold {r['threshold']:+.3f}  detection {r['detection']:.1%} of {r['malware']} "
              f"malware  FPR {r['fpr']:.2%} of {r['benign']} benign")
    print("\nEvasion of the malware each defense detects (loader-safe attacks of run 49):")
    for r in summary.iter_rows(named=True):
        print(f"  {r['defense']:34s} {r['recipe']:26s} files {r['files']:5d}  evasion {r['evasion']:.1%} "
              f"[{r['ci_low']:.1%}, {r['ci_high']:.1%}]")


################################################################################
# Main
################################################################################


def main() -> None:
    parser = ArgumentParser(description="M3, test-time half: zero the audited fields before MalConv scores a file.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--num_files", type=int, default=1000, help="Held-out malware, drawn as in run 49.")
    parser.add_argument("--num_benign", type=int, default=5000, help="Held-out benign files for the 1%%-FPR thresholds.")
    parser.add_argument("--num_random", type=int, default=5, help="Draws of the null attack per file.")
    parser.add_argument("--random_retries", type=int, default=20)
    parser.add_argument("--max_content", type=int, default=256)
    parser.add_argument("--threshold", type=float, default=1.9766, help="MalConv seed 0 score at 1 pct FPR on the test split.")
    parser.add_argument("--exclude", type=Path, nargs="*", default=[ROOT / "artifacts" / "experiments" / "audit_scramble" / "seed-0" / "files.parquet"])
    parser.add_argument("--benign_rows", type=int, default=50_000, help="Benign training files for constrained values.")
    parser.add_argument("--run_name", type=str, default=None, help="Subdirectory name (default: seed-{seed}).")
    parser.add_argument("--checkpoints", type=Path, default=ROOT / "checkpoints")
    parser.add_argument("--scramble", type=Path, default=ROOT / "artifacts" / "experiments" / "audit_scramble")
    parser.add_argument("--explanation_set", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "audit_mitigate")
    parser.add_argument("--limit", type=int, default=None, help="Only the first files of each label (smoke tests).")
    parser.add_argument("--num_workers", type=int, default=16)
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()

    if os.environ.get("PYTHONHASHSEED") != "0":
        raise RuntimeError("Run with PYTHONHASHSEED=0 so that the features and run 49's seeds match.")
    outdir = args.outdir / (args.run_name or f"seed-{args.seed}")
    outdir.mkdir(parents=True, exist_ok=True)
    model_file = args.checkpoints / f"malconv-seed{args.seed}.pt"

    names = PEFeatureExtractor().feature_names
    index = {name: i for i, name in enumerate(names)}
    recipe_names = recipe_features(pl.read_parquet(args.scramble / f"seed-{args.seed}" / "summary.parquet"))
    recipes = {k: [index[n] for n in v] for k, v in recipe_names.items()}
    defense_names = {"none": [], "pushforward": defended_fields(recipe_names["pushforward"]),
                     "union": defended_fields(recipe_names["union"])}
    defenses = {k: [index[n] for n in v] for k, v in defense_names.items()}
    for k, v in defense_names.items():
        print(f"Defense {k}: {len(v)} fields zeroed" + (": " + ", ".join(v) if v else "."), flush=True)
    realizable = {
        "index": index, "names": list(names),
        "pools": benign_pools(args.features, list(names), sorted(index[n] for n in CONSTRAINED), args.benign_rows, args.seed),
        "broad_pool": sorted(index[n] for n in (FREE | FREE_EXTRA) - set(recipe_names["union"])),
    }

    # The malware targets exactly as in scripts/audit_evade.py (run 49), and benign files the same way.
    meta = pl.read_parquet(args.features / "ts" / "meta.parquet")
    explained = pl.read_parquet(args.explanation_set).select("name")

    def held_out(label: int) -> pl.DataFrame:
        pool = (meta.filter((pl.col("label") == label) & (pl.col("status") == "ok") & ~pl.col("truncated"))
                .join(explained, on="name", how="anti"))
        for path in args.exclude:
            pool = pool.join(pl.read_parquet(path).select("name"), on="name", how="anti")
        return pool

    malware = held_out(1)
    malware = malware.sample(min(args.num_files, malware.height), seed=args.seed).with_row_index("index")
    benign = held_out(0)
    benign = benign.sample(min(args.num_benign, benign.height), seed=args.seed).with_row_index("index")
    benign = benign.with_columns(pl.col("index") + 1_000_000)  # disjoint from the malware indices
    if args.limit is not None:
        malware, benign = malware.head(args.limit), benign.head(args.limit)
    targets = pl.concat([malware.select("index", "name", "label", "shard", "position"),
                         benign.select("index", "name", "label", "shard", "position")])
    print(f"M3 test-time: {malware.height} malware, {benign.height} benign; defenses {', '.join(DEFENSES)}.", flush=True)

    tasks = []
    for (shard,), group in targets.sort("shard", "position").group_by("shard", maintain_order=True):
        tasks.append((int(shard), group.select("index", "name", "label", "position").to_dicts(), args.db, defenses,
                      recipes, realizable, args.num_random, args.random_retries, args.max_content, args.seed,
                      args.timeout))
    t_0 = time.time()
    files: list[dict[str, Any]] = []
    attacks: list[dict[str, Any]] = []
    with mp.get_context("fork").Pool(args.num_workers, initializer=st._init_worker, initargs=(model_file, "malconv")) as pool_:
        for f, a in tqdm(pool_.imap_unordered(_star, sorted(tasks, key=lambda t: -len(t[1]))), total=len(tasks),
                         desc="shards", mininterval=10):
            files.extend(f)
            attacks.extend(a)

    file_table = pl.DataFrame(files, infer_schema_length=None).sort("index")
    attack_table = pl.DataFrame(attacks, infer_schema_length=None).sort("index", "recipe", "draw")
    summary = summarize(file_table, attack_table, args.threshold, seed=args.seed)
    file_table.write_parquet(outdir / "files.parquet")
    attack_table.write_parquet(outdir / "attacks.parquet")
    summary.write_parquet(outdir / "summary.parquet")
    report = {
        "config": {k: (v.as_posix() if isinstance(v, Path) else [p.as_posix() for p in v] if isinstance(v, list) else v)
                   for k, v in vars(args).items()},
        "defended_fields": defense_names, "status": dict(Counter(file_table["status"].to_list())),
        "minutes": (time.time() - t_0) / 60,
    }
    (outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "config"}, indent=2))
    print_summary(summary)
    print(f"\nWrote {outdir.as_posix()}.")


if __name__ == "__main__":
    main()
