"""
3-C revised, the combined effect (docs/experiments/audit.md, "Scrambling what detection rests on"): how much of MalConv's
detection rests on the confirmed features together, and does scrambling them evade the detector? The per-feature test
(scripts/audit_scramble.py, run 44) confirmed features one at a time; here the features of a *recipe* are scrambled
together in each file, and the drop and the evasion rate at the detector's 1% FPR threshold are measured.

Recipes (each a set of features; every one scrambled at the bytes the file's own P names for it):
    - `pushforward`: the features confirmed from MalConv's pushed-forward IG (run 44);
    - `surrogate`: the features confirmed from the surrogate (run 44, the realistic alternative);
    - `union`: the two sets together;
    - `random`: as many features as `pushforward`, drawn per file (seeded) from all features with locatable content,
      the null recipe (does scrambling the discovered fields beat scrambling arbitrary locatable fields?).

With `--realizable --decompose`, the realizable pushforward recipe's loss is decomposed: `pushforward_no_critical`
(the same fields, random bytes everywhere, i.e., abnormal values in the constrained fields), `pushforward_free_only`
(its free fields alone), and the null `random_free_unconfirmed` (free fields of the pool that no source confirmed).

With `--broad_null` as well, two more nulls draw from every loader-ignored field that no source confirmed (`FREE` and
`FREE_EXTRA`), `random_free_broad` and, outside the DOS region (DOS header, stub, Rich header),
`random_free_broad_nondos`.

With `--realizable`, each confirmed recipe also gets a `*_realizable` version that changes only what the Windows loader
lets an attacker change (domain knowledge inside the experiment, docs/experiments/audit.md, "Realizability"): `FREE`
fields, which the loader ignores, are scrambled; `CONSTRAINED` fields take a valid value drawn from benign training
files of the same machine type; loader-critical fields are left alone. Its null, `random_free`, scrambles as many
`FREE` fields of the candidate pool (as `pushforward_realizable` has fields), drawn per file.

A file *evades* if its scrambled MalConv malware log-odds falls to or below `--threshold` (the detector's score at 1%
false positives; the default 1.9766 is MalConv seed 0's 1%-FPR threshold on the test split, from
scripts/cm_disagreement_select.py). Every scramble must keep the file parsing with its original section layout. With
`--random_retries`, a random draw that breaks the parse is redrawn (up to that many times), so the null is conditioned
on parsing like the other recipes. With `--detected_only`, only files above the threshold are scored, so that rates are
over detected malware. `--exclude` removes the files of earlier runs (run 44 confirmed the fields on its 200 files).

Outputs, in `{outdir}/seed-{seed}/`:
    files.parquet       one row per target file: status, original log-odds
    results.parquet     one row per (file, recipe): features scrambled, bytes, parsed, modified log-odds, drop, evaded
    summary.parquet     one row per recipe: applicable files, median drop, evasion rate with a bootstrap 95% CI
    paired.parquet      paired comparisons of evasion between recipes (difference, bootstrap CI, exact test)
    report.json         the configuration, the recipes, the threshold, and timing

Usage:
    PYTHONHASHSEED=0 python scripts/audit_evade.py --seed 0 --num_workers 16
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
import polars as pl
from scipy import stats
from tqdm import tqdm

from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBIterator
from provexp.featuresets.ember2024.ablation import parse
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.data.paths import EMBER2024_DATA

sys.path.insert(0, str(Path(__file__).parent))
import shortcuts_transplant as st  # noqa: E402


__all__ = [
    "CONSTRAINED",
    "FREE",
    "FREE_EXTRA",
    "in_dos_region",
    "paired_comparisons",
    "realizable_plan",
    "recipe_features",
    "summarize",
]


ROOT = Path(__file__).parent.parent


################################################################################
# Recipes
################################################################################


def recipe_features(summary: pl.DataFrame) -> dict[str, list[str]]:
    """The confirmed feature names of each source, from run 44's summary: `pushforward`, `surrogate`, and `union`."""
    def confirmed(kind: str) -> list[str]:
        return (summary.filter((pl.col("kind") == kind) & pl.col("confirmed").fill_null(False))
                .sort("median_effect", descending=True)["top_feature"].to_list())
    push, surr = confirmed("malconv"), confirmed("surrogate")
    return {"pushforward": push, "surrogate": surr, "union": sorted(set(push) | set(surr))}


################################################################################
# Realizability
################################################################################


# NOTE: domain knowledge inside the experiment, from the PE format and the Windows loader's documented behavior; nothing
# here is executed. Fields the loader ignores in a user-mode image: any bytes keep the program loadable (the certificate
# fields invalidate the signature, which the loader does not check for user-mode executables).
FREE = frozenset({
    "header:optional_header_CheckSum",  # checked only for drivers and some system DLLs; skipped for native images
    "header:file_header_PointerToSymbolTable",
    "strings:regex_dos_msg",
    "header:optional_header_SizeOfCode",
    "header:optional_header_SizeOfUninitializedData",
    "header:optional_header_MinorLinkerVersion",
    "datadirectories:debug_virtual_address",
    "datadirectories:debug_size",
    "datadirectories:globalptr_virtual_address",
    "datadirectories:copyright_virtual_address",
    "datadirectories:security_virtual_address",
    "datadirectories:security_size",
    "datadirectories:export_virtual_address",  # executables only: a DLL's exports are resolved by its importers
    "datadirectories:export_size",
    "authenticode:latest_signing_time",
    "authenticode:num_certs",
})

# Fields that must hold a valid value: a value drawn from benign training files with the same machine type.
CONSTRAINED = frozenset({
    "header:optional_header_ImageBase",  # only for files with relocations, so the loader can rebase
    "header:optional_header_Subsystem",  # GUI <-> console only
    "header:optional_header_SizeOfHeapReserve",
    "header:optional_header_SizeOfHeapCommit",
    "header:optional_header_SizeOfStackReserve",
})

# The broad null (--broad_null): every other loader-ignored field in the EMBER header, data-directory, Rich-header, and
# certificate features. Flag features are left out (they share their bytes with flags the loader needs), as are fields
# the loader checks (subsystem version, alignments, sizes, entry point, section count) and directories it reads.
FREE_EXTRA = frozenset({
    "header:file_header_TimeDateStamp",
    "header:file_header_NumberOfSymbols",
    "header:optional_header_MajorImageVersion",
    "header:optional_header_MinorImageVersion",
    "header:optional_header_MajorLinkerVersion",
    "header:optional_header_MajorOperatingSystemVersion",
    "header:optional_header_MinorOperatingSystemVersion",
    "header:optional_header_SizeOfInitializedData",
    "header:optional_header_BaseOfCode",
    "datadirectories:globalptr_size",
    "datadirectories:copyright_size",
    "datadirectories:reserved_size",
    "datadirectories:reserved_virtual_address",
    "authenticode:self_signed",
    "authenticode:empty_program_name",
    "authenticode:no_countersigner",
    "authenticode:parse_error",
    "authenticode:chain_max_depth",
    "authenticode:signing_time_diff",
}) | frozenset(f"header:dos_e_{f}" for f in (
    "cblp", "cp", "crlc", "cparhdr", "minalloc", "maxalloc", "ss", "sp", "csum", "ip", "cs", "lfarlc", "ovno", "oemid",
    "oeminfo",
)) | frozenset({"richheader:num_pairs"} | {f"richheader:pair_hash_{i}" for i in range(32)})


def in_dos_region(name: str) -> bool:
    """Whether a feature's bytes lie in the DOS header, the DOS stub, or the Rich header (before the PE header)."""
    return name.startswith(("header:dos_e_", "richheader:")) or name == "strings:regex_dos_msg"


_EXECUTABLE_ONLY = frozenset({"datadirectories:export_virtual_address", "datadirectories:export_size"})


def realizable_plan(
    x: np.ndarray,
    index: dict[str, int],
    features: list[int],
    names: list[str],
    pools: dict[tuple[int, int], np.ndarray],
    rng: np.random.Generator,
) -> tuple[list[int], dict[int, int]]:
    """
    The part of a recipe an attacker could apply to this file: the `FREE` features to scramble, and a valid value for
    each `CONSTRAINED` feature.

    Args:
        x: The file's feature vector.
        index: Feature name -> column.
        features: The recipe's feature columns.
        names: Column -> feature name.
        pools: (column, machine) -> benign values of that feature, for the constrained features.
        rng: The generator for the drawn values.

    Returns:
        The free features to scramble, and {constrained feature: value to write}.
    """
    def value(name: str) -> float:
        return float(x[index[name]])

    is_dll = value("header:characteristics_DLL") > 0
    subsystem = int(value("header:optional_header_Subsystem"))
    machine = int(value("header:file_header_Machine"))
    free: list[int] = []
    constrained: dict[int, int] = {}
    for j in features:
        name = names[j]
        if name in FREE:
            if name in _EXECUTABLE_ONLY and is_dll:
                continue
            if name == "header:optional_header_CheckSum" and subsystem == 1:
                continue
            free.append(j)
        elif name in CONSTRAINED:
            pool = pools.get((j, machine))
            if pool is None or pool.size == 0:
                continue
            if name == "header:optional_header_ImageBase":
                if value("datadirectories:has_relocs") <= 0 or value("header:characteristics_RELOCS_STRIPPED") > 0:
                    continue
                pool = pool[pool % 65536 == 0]
            elif name == "header:optional_header_Subsystem":
                if subsystem not in (2, 3):
                    continue
                pool = pool[(pool == 2) | (pool == 3)]
            elif name == "header:optional_header_SizeOfHeapReserve":
                pool = pool[pool >= value("header:optional_header_SizeOfHeapCommit")]
            elif name == "header:optional_header_SizeOfHeapCommit":
                pool = pool[pool <= value("header:optional_header_SizeOfHeapReserve")]
            elif name == "header:optional_header_SizeOfStackReserve":
                pool = pool[pool >= value("header:optional_header_SizeOfStackCommit")]
            if pool.size:
                constrained[j] = int(pool[int(rng.integers(pool.size))])
    return free, constrained


def benign_pools(
    features: Path, names: list[str], columns: list[int], max_rows: int, seed: int,
) -> dict[tuple[int, int], np.ndarray]:
    """(column, machine) -> the values of each constrained column in a sample of benign training files."""
    meta = pl.read_parquet(features / "tr" / "meta.parquet").with_row_index("i")
    benign = meta.filter((pl.col("label") == 0) & (pl.col("status") == "ok"))["i"].to_numpy()
    rows = np.sort(np.random.default_rng(seed).choice(benign, size=min(max_rows, benign.size), replace=False))
    X = np.load(features / "tr" / "X.npy", mmap_mode="r")
    machine_col = names.index("header:file_header_Machine")
    sample = np.asarray(X[rows][:, columns + [machine_col]], dtype=np.float64)
    machines = sample[:, -1].astype(np.int64)
    pools: dict[tuple[int, int], np.ndarray] = {}
    for k, j in enumerate(columns):
        for m in np.unique(machines):
            v = sample[machines == m, k]
            # NOTE: features are stored as floats, so a value at or above 2^53 (e.g., a kernel-mode ImageBase above
            # 2^63) is not held exactly and may not fit int64; such values cannot be written back faithfully.
            v = v[np.isfinite(v) & (v >= 0) & (v < 2.0 ** 53)]
            pools[(j, int(m))] = np.round(v).astype(np.int64)
    return pools


################################################################################
# Workers
################################################################################


def _scramble_features(
    data: bytes, runs: dict[int, list[tuple[int, int]]], features: list[int], max_content: int,
    rng: np.random.Generator, values: Optional[dict[int, int]] = None,
) -> tuple[bytes, int, int]:
    """
    Overwrite every locatable run of each feature in `features` with random bytes, and write each feature in `values`
    (a single run of 1, 2, 4, or 8 bytes) as that little-endian value. Returns the file, the bytes written, and the
    number of features changed.
    """
    written, changed = 0, 0
    for j in features:
        total = sum(n for _, n in runs.get(j, []))
        if total == 0 or total > max_content:
            continue
        for start, n in runs[j]:
            data = st.overwrite(data, start, rng.integers(0, 256, size=n, dtype=np.uint8).tobytes())
            written += n
        changed += 1
    for j, v in (values or {}).items():
        spans = runs.get(j, [])
        if len(spans) != 1 or spans[0][1] not in (1, 2, 4, 8) or not 0 <= v < 256 ** spans[0][1]:
            continue
        start, n = spans[0]
        data = st.overwrite(data, start, int(v).to_bytes(n, "little"))
        written += n
        changed += 1
    return data, written, changed


def process_shard(
    shard: int,
    samples: list[dict[str, Any]],
    dbdir: Path,
    recipes: dict[str, list[int]],
    num_random: int,
    all_localizable: np.ndarray,
    min_score: float,
    threshold: float,
    max_content: int,
    seed: int,
    timeout: int,
    random_retries: int = 0,
    detected_only: bool = False,
    realizable: Optional[dict[str, Any]] = None,
    decompose: bool = False,
    broad_null: bool = False,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Scramble each recipe's features together in the target files of one shard; see the module docstring."""
    assert st._EXTRACTOR is not None and st._MALCONV is not None
    extra = (realizable["free_pool"] + realizable.get("broad_pool", [])) if realizable else []
    needed = np.array(sorted({j for js in recipes.values() for j in js} | set(all_localizable.tolist()) | set(extra)),
                      dtype=np.int64)
    wanted = {s["position"]: i for i, s in enumerate(samples)}
    files: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    db = SimpleDB(dbdir, check=False)

    def run(name: str, feats: list[int], rng: np.random.Generator, values: Optional[dict[int, int]] = None,
            redraw: Optional[Any] = None) -> dict[str, Any]:
        attempts = 0
        while True:
            modified, written, changed = _scramble_features(data, runs, feats, max_content, rng, values)
            score = st.verified_score(modified, original.layout)
            if score is not None or redraw is None or attempts >= random_retries:
                break
            attempts += 1
            feats = redraw()
        return base | {
            "recipe": name, "num_features": changed, "bytes": written, "parsed": score is not None,
            "attempts": attempts + 1, "modified": score if score is not None else float("nan"),
            "drop": (log_odds - score) if score is not None else float("nan"),
            "evaded": bool(score is not None and score <= threshold),
        }

    for position, sample in enumerate(SimpleDBIterator(db).iter(shard)):
        if position not in wanted:
            continue
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
            log_odds = st.score(data)
            if log_odds <= min_score or (detected_only and log_odds <= threshold):
                files.append(base | {"status": "low_score", "log_odds": log_odds})
                continue
            x, prov = st._EXTRACTOR.feature_vector_with_provenance(data)
            x = np.asarray(x, dtype=np.float64)
            runs = st.feature_runs(prov, needed)
            key = int(meta["index"])

            def locatable(js: Any) -> list[int]:
                return [int(j) for j in js if 0 < sum(n for _, n in runs.get(int(j), [])) <= max_content]

            local = locatable(all_localizable)
            for name, feats in recipes.items():
                rng = np.random.default_rng([seed, key, abs(hash(name)) % (2 ** 31)])
                results.append(run(name, feats, rng))
            for r in range(num_random):
                rng = np.random.default_rng([seed, key, 100 + r])
                k = min(len(recipes["pushforward"]), len(local))

                def draw(rng: np.random.Generator = rng, k: int = k) -> list[int]:
                    return rng.choice(local, size=k, replace=False).tolist() if k else []

                results.append(run("random", draw(), rng, redraw=draw))
            if realizable is not None:
                for name in ("pushforward", "surrogate", "union"):
                    rng = np.random.default_rng([seed, key, 200 + abs(hash(name)) % 1000])
                    free, values = realizable_plan(x, realizable["index"], recipes[name], realizable["names"],
                                                   realizable["pools"], rng)
                    results.append(run(f"{name}_realizable", free, rng, values))
                    if name == "pushforward":
                        k_free = len(free) + len(values)
                        push_free, push_values = free, values
                free_local = [j for j in locatable(realizable["free_pool"])
                              if not (realizable["names"][j] in _EXECUTABLE_ONLY and x[realizable["index"]["header:characteristics_DLL"]] > 0)]
                for r in range(num_random):
                    rng = np.random.default_rng([seed, key, 300 + r])
                    k = min(k_free, len(free_local))

                    def draw_free(rng: np.random.Generator = rng, k: int = k) -> list[int]:
                        return rng.choice(free_local, size=k, replace=False).tolist() if k else []

                    results.append(run("random_free", draw_free(), rng, redraw=draw_free))
                if decompose:
                    # Where the realizable pushforward recipe loses its evasion: the same fields with random bytes
                    # (abnormal values in the constrained fields), the free fields alone, and a null without any
                    # confirmed field.
                    rng = np.random.default_rng([seed, key, 400])
                    results.append(run("pushforward_no_critical", push_free + sorted(push_values), rng))
                    rng = np.random.default_rng([seed, key, 401])
                    results.append(run("pushforward_free_only", push_free, rng))
                    confirmed = set(recipes["union"])
                    unconfirmed = [j for j in free_local if j not in confirmed]
                    for r in range(num_random):
                        rng = np.random.default_rng([seed, key, 500 + r])
                        k = min(k_free, len(unconfirmed))

                        def draw_unconfirmed(rng: np.random.Generator = rng, k: int = k) -> list[int]:
                            return rng.choice(unconfirmed, size=k, replace=False).tolist() if k else []

                        results.append(run("random_free_unconfirmed", draw_unconfirmed(), rng, redraw=draw_unconfirmed))
                if broad_null:
                    # Nulls from every loader-ignored field no source confirmed, with and without the DOS region.
                    is_dll = x[realizable["index"]["header:characteristics_DLL"]] > 0
                    broad = [j for j in locatable(realizable["broad_pool"])
                             if not (realizable["names"][j] in _EXECUTABLE_ONLY and is_dll)]
                    for null, pool_ in (("random_free_broad", broad),
                                        ("random_free_broad_nondos",
                                         [j for j in broad if not in_dos_region(realizable["names"][j])])):
                        for r in range(num_random):
                            rng = np.random.default_rng([seed, key, (600 if null == "random_free_broad" else 700) + r])
                            k = min(k_free, len(pool_))

                            def draw_broad(rng: np.random.Generator = rng, k: int = k, pool_: list[int] = pool_) -> list[int]:
                                return rng.choice(pool_, size=k, replace=False).tolist() if k else []

                            results.append(run(null, draw_broad(), rng, redraw=draw_broad))
            files.append(base | {"status": "ok", "log_odds": log_odds})
        except st.TransplantTimeout:
            files.append(base | {"status": "timeout", "log_odds": float("nan")})
        except Exception as err:
            files.append(base | {"status": "error", "log_odds": float("nan"), "error": f"{type(err).__name__}: {err}"[:300]})
        finally:
            signal.alarm(0)
    return files, results


def _star(task: tuple[Any, ...]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return process_shard(*task)


################################################################################
# Statistics
################################################################################


def _per_file(results: pl.DataFrame) -> pl.DataFrame:
    """One row per (file, recipe): the evasion rate over the recipe's draws (0/1 for a fixed recipe), parsed draws only."""
    return results.filter(pl.col("parsed")).group_by("index", "recipe").agg(pl.col("evaded").cast(pl.Float64).mean())


def summarize(results: pl.DataFrame, num_boot: int = 10_000, seed: int = 0) -> pl.DataFrame:
    """Per recipe: files, mean features and bytes, median drop, and the evasion rate over files with a bootstrap CI."""
    rng = np.random.default_rng(seed)
    per_file = _per_file(results)
    rows = []
    for (recipe,), group in per_file.group_by("recipe", maintain_order=True):
        e = group["evaded"].to_numpy()
        boot = e[rng.integers(0, e.size, size=(num_boot, e.size))].mean(axis=1)
        sub = results.filter(pl.col("parsed") & (pl.col("recipe") == recipe))
        rows.append({
            "recipe": recipe, "files": e.size, "draws": sub.height,
            "unparsed_draws": results.filter(~pl.col("parsed") & (pl.col("recipe") == recipe)).height,
            "mean_features": sub["num_features"].mean(), "median_bytes": sub["bytes"].median(),
            "median_drop": sub["drop"].median(), "evasion_rate": float(e.mean()),
            "ci_low": float(np.quantile(boot, 0.025)), "ci_high": float(np.quantile(boot, 0.975)),
        })
    return pl.DataFrame(rows).sort("evasion_rate", descending=True)


def paired_comparisons(
    results: pl.DataFrame, pairs: list[tuple[str, str]], num_boot: int = 10_000, seed: int = 0,
) -> pl.DataFrame:
    """
    Paired by file, for each (a, b): the difference in evasion rate, its bootstrap 95% CI, and an exact test. Two fixed
    recipes get McNemar's exact test on the discordant files; a random recipe (a rate per file) gets the Wilcoxon
    signed-rank test on the per-file differences.
    """
    rng = np.random.default_rng(seed)
    wide = _per_file(results).pivot(on="recipe", index="index", values="evaded")
    rows = []
    for a, b in pairs:
        if a not in wide.columns or b not in wide.columns:
            continue
        both = wide.select(a, b).drop_nulls()
        ea, eb = both[a].to_numpy(), both[b].to_numpy()
        d = ea - eb
        boot = d[rng.integers(0, d.size, size=(num_boot, d.size))].mean(axis=1)
        fixed = np.isin(ea, (0.0, 1.0)).all() and np.isin(eb, (0.0, 1.0)).all()
        if fixed:
            only_a, only_b = int(((ea == 1) & (eb == 0)).sum()), int(((ea == 0) & (eb == 1)).sum())
            n = only_a + only_b
            p = float(stats.binomtest(only_a, n, 0.5).pvalue) if n else 1.0
            test = "mcnemar_exact"
        else:
            only_a, only_b = int((d > 0).sum()), int((d < 0).sum())
            p = float(stats.wilcoxon(d).pvalue) if np.any(d != 0) else 1.0
            test = "wilcoxon"
        rows.append({
            "a": a, "b": b, "files": d.size, "rate_a": float(ea.mean()), "rate_b": float(eb.mean()),
            "difference": float(d.mean()), "ci_low": float(np.quantile(boot, 0.025)),
            "ci_high": float(np.quantile(boot, 0.975)), "a_only": only_a, "b_only": only_b, "test": test, "p_value": p,
        })
    return pl.DataFrame(rows)


################################################################################
# Driver
################################################################################


def main() -> None:
    parser = ArgumentParser(description="3-C revised: scramble each recipe's features together and measure evasion.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--num_random", type=int, default=5, help="Random recipes drawn per file (their rates are averaged).")
    parser.add_argument("--num_files", type=int, default=200)
    parser.add_argument("--min_score", type=float, default=0.0)
    parser.add_argument("--threshold", type=float, default=1.9766, help="MalConv seed 0 score at 1 pct FPR (cm_disagreement_select).")
    parser.add_argument("--max_content", type=int, default=256)
    parser.add_argument("--random_retries", type=int, default=0, help="Redraw a random recipe that breaks the parse.")
    parser.add_argument("--detected_only", action="store_true", help="Score only files above the threshold.")
    parser.add_argument("--realizable", action="store_true", help="Add the *_realizable recipes and random_free.")
    parser.add_argument("--decompose", action="store_true", help="With --realizable: decompose its loss (see code).")
    parser.add_argument("--broad_null", action="store_true", help="With --realizable: nulls from all loader-ignored fields.")
    parser.add_argument("--exclude", type=Path, nargs="*", default=[], help="files.parquet of runs whose files to skip.")
    parser.add_argument("--benign_rows", type=int, default=50_000, help="Benign training files for constrained values.")
    parser.add_argument("--run_name", type=str, default=None, help="Subdirectory name (default: seed-{seed}).")
    parser.add_argument("--checkpoints", type=Path, default=ROOT / "checkpoints")
    parser.add_argument("--scramble", type=Path, default=ROOT / "artifacts" / "experiments" / "audit_scramble")
    parser.add_argument("--explanation_set", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--db", type=Path, default=EMBER2024_DATA / "ts")
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "audit_evade")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--num_workers", type=int, default=os.cpu_count())
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()

    if os.environ.get("PYTHONHASHSEED") != "0":
        raise RuntimeError("Run with PYTHONHASHSEED=0 so that the features match the feature store.")
    outdir = args.outdir / (args.run_name or f"seed-{args.seed}")
    outdir.mkdir(parents=True, exist_ok=True)
    model_file = args.checkpoints / f"malconv-seed{args.seed}.pt"

    names = PEFeatureExtractor().feature_names
    index = {name: i for i, name in enumerate(names)}
    summary = pl.read_parquet(args.scramble / f"seed-{args.seed}" / "summary.parquet")
    recipe_names = recipe_features(summary)
    recipes = {k: [index[n] for n in v] for k, v in recipe_names.items()}
    # The pool the random recipe draws from: the features confirmed or tested in run 44 (all header/directory fields
    # with locatable content), so the control scrambles comparable fields, not whole-file aggregates.
    candidates = pl.read_parquet(args.scramble / f"seed-{args.seed}" / "candidates.parquet")
    pool_names = sorted(set(candidates["top_feature"].to_list()))
    all_localizable = np.array(sorted(index[n] for n in pool_names), dtype=np.int64)
    print("Recipes: " + ", ".join(f"{k} ({len(v)})" for k, v in recipes.items())
          + f", random (~{len(recipes['pushforward'])} of {all_localizable.size}).", flush=True)

    realizable: Optional[dict[str, Any]] = None
    if args.realizable:
        constrained_cols = sorted(index[n] for n in CONSTRAINED)
        realizable = {
            "index": index, "names": list(names),
            "pools": benign_pools(args.features, list(names), constrained_cols, args.benign_rows, args.seed),
            "free_pool": sorted(index[n] for n in pool_names if n in FREE),
        }
        if args.broad_null:
            confirmed_names = set(recipe_names["union"])
            realizable["broad_pool"] = sorted(index[n] for n in (FREE | FREE_EXTRA) - confirmed_names)
            print(f"Broad null pool: {len(realizable['broad_pool'])} loader-ignored, unconfirmed fields.", flush=True)
        print(f"Realizable: {len(realizable['free_pool'])} free fields in the candidate pool: "
              + ", ".join(names[j] for j in realizable["free_pool"]), flush=True)

    meta = pl.read_parquet(args.features / "ts" / "meta.parquet")
    explained = pl.read_parquet(args.explanation_set).select("name")
    pool = (meta.filter((pl.col("label") == 1) & (pl.col("status") == "ok") & ~pl.col("truncated"))
            .join(explained, on="name", how="anti"))
    for path in args.exclude:
        pool = pool.join(pl.read_parquet(path).select("name"), on="name", how="anti")
    targets = pool.sample(min(args.num_files, pool.height), seed=args.seed).with_row_index("index")
    if args.limit is not None:
        targets = targets.head(args.limit)
    print(f"3-C evade: {targets.height} malware, MalConv threshold {args.threshold:.3f}, detected only "
          f"{args.detected_only}, random retries {args.random_retries}, excluded {len(args.exclude)} run(s).", flush=True)

    tasks = []
    for (shard,), group in targets.sort("shard", "position").group_by("shard", maintain_order=True):
        tasks.append((int(shard), group.select("index", "name", "position").to_dicts(), args.db, recipes,
                      args.num_random, all_localizable, args.min_score, args.threshold, args.max_content, args.seed,
                      args.timeout, args.random_retries, args.detected_only, realizable, args.decompose,
                      args.broad_null))
    t_0 = time.time()
    files: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    with mp.get_context("fork").Pool(args.num_workers, initializer=st._init_worker, initargs=(model_file, "malconv")) as pool_:
        for f, r in tqdm(pool_.imap_unordered(_star, sorted(tasks, key=lambda t: -len(t[1]))), total=len(tasks),
                         desc="shards", mininterval=10):
            files.extend(f)
            results.extend(r)

    file_table = pl.DataFrame(files, infer_schema_length=None).sort("index")
    result_table = pl.DataFrame(results, infer_schema_length=None).sort("index", "recipe")
    scored = file_table.filter(pl.col("status") == "ok")
    summary_out = summarize(result_table, seed=args.seed)
    pairs = [("pushforward", "random"), ("surrogate", "random"), ("union", "random"), ("pushforward", "surrogate"),
             ("union", "surrogate"), ("pushforward_realizable", "random_free"), ("surrogate_realizable", "random_free"),
             ("union_realizable", "random_free"), ("pushforward_realizable", "surrogate_realizable"),
             ("pushforward", "pushforward_realizable"), ("pushforward", "pushforward_no_critical"),
             ("pushforward_no_critical", "pushforward_realizable"), ("pushforward_realizable", "pushforward_free_only"),
             ("pushforward_free_only", "random_free_unconfirmed"), ("pushforward_realizable", "random_free_unconfirmed"),
             ("union_realizable", "random_free_unconfirmed"), ("random_free", "random_free_unconfirmed"),
             ("pushforward_realizable", "random_free_broad"), ("pushforward_realizable", "random_free_broad_nondos"),
             ("union_realizable", "random_free_broad"), ("union_realizable", "random_free_broad_nondos"),
             ("surrogate_realizable", "random_free_broad_nondos"), ("pushforward_free_only", "random_free_broad_nondos")]
    paired = paired_comparisons(result_table, pairs, seed=args.seed)
    file_table.write_parquet(outdir / "files.parquet")
    result_table.write_parquet(outdir / "results.parquet")
    summary_out.write_parquet(outdir / "summary.parquet")
    paired.write_parquet(outdir / "paired.parquet")

    report = {
        "config": {k: (v.as_posix() if isinstance(v, Path) else [p.as_posix() for p in v] if isinstance(v, list) else v)
                   for k, v in vars(args).items()},
        "recipes": recipe_names, "threshold": args.threshold, "num_scored": scored.height,
        "status": dict(Counter(file_table["status"].to_list())), "minutes": (time.time() - t_0) / 60,
    }
    if realizable is not None:
        report["free_pool"] = [names[j] for j in realizable["free_pool"]]
    (outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k not in ("config", "recipes")}, indent=2))
    print(f"\nPer recipe over {scored.height} malware: median drop in MalConv's log-odds and evasion at the threshold:")
    for r in summary_out.iter_rows(named=True):
        print(f"  {r['recipe']:24s}  files {r['files']:5d}  features {r['mean_features']:5.1f}  bytes "
              f"{r['median_bytes'] or 0:6.0f}  median drop {r['median_drop']:+7.3f}  evasion {r['evasion_rate']:.1%} "
              f"[{r['ci_low']:.1%}, {r['ci_high']:.1%}]  (unparsed draws {r['unparsed_draws']})")
    print("\nPaired by file (difference in evasion rate, bootstrap 95% CI, exact test):")
    for r in paired.iter_rows(named=True):
        print(f"  {r['a']:24s} - {r['b']:22s}  {r['difference']:+.1%} [{r['ci_low']:+.1%}, {r['ci_high']:+.1%}]  "
              f"{r['a_only']}/{r['b_only']} files  {r['test']} p = {r['p_value']:.2g}")
    print(f"\nWrote {outdir.as_posix()}.")


if __name__ == "__main__":
    main()
