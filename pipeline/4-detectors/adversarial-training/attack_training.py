"""
The learned defenses' material (§5.3, Table 4; Appendix D, Table 10): Gimenez et al.'s toolkit attacks on TRAINING
malware, run once, saved as feature rows for every store a defense reads and as compressed adversarial binaries, so
PV, ERDALT, adversarial training and the leave-one-out folds all learn from the same outputs, and a change of
extractor means re-featurizing the binaries, not re-attacking.

FOR ACADEMIC SECURITY RESEARCH ONLY. This runs published secml-malware attacks against our own undefended detector, on
our own training samples, solely to build the learned defenses the sound detectors are compared with. No new evasion
technique is developed and nothing is deployed.

The attacks run on the training malware of a file list (`--files`, its label-1 rows; the scale-up's
2-features/files/tr.parquet), every one of them, detected or not (standard adversarial augmentation adds every
perturbed malware), with the goodware of a donor list (`--donors`, training goodware; the scale-up's donor set 0) as
the donors of the section and import attacks. The target is `--model`, scored with the extractor of `--features`. Each
(attack, file) is seeded on its own (`--seed_per_file`). Each valid adversarial file keeps label 1.

The work splits into shards (`--shard k --num_shards N`: every N-th malware from the k-th), one per SLURM array task;
a shard whose report.json exists is skipped. `--merge` then assembles the shards.

Outputs:
    {outdir}/shards/{k}/<store>/X.npy, files.parquet   a shard's rows, one directory per store of `--rows`
    {outdir}/shards/{k}/report.json                    the shard's counts
    {outdir}/binaries/<attack>/<name>.zst              each valid adversarial file, zstd-compressed (`--keep_binaries`)
    {outdir}/<store>/X.npy, files.parquet, report.json  after `--merge`: the rows train_classic.py --augment,
                                                        train_erdalt.py --adv_dir and pv_hole.py --adv_dir read
    files.parquet: name, attack, label (1), p_clean, p_adv, bytes_added; X.npy: float32 rows in the store's layout.

Usage (smoke on two malware, one attack):
    PYTHONHASHSEED=0 python pipeline/4-detectors/adversarial-training/attack_training.py --outdir /tmp/adv \\
        --files artifacts/scaleup/2-features/files/tr.parquet --donors artifacts/scaleup/2-features/files/tr-donors-0.parquet \\
        --features artifacts/scaleup/2-features/sums --rows artifacts/scaleup/2-features/sums \\
        --model artifacts/scaleup/4-detectors/unconstrained/model.txt --num_malware 2 --attacks padding --num_workers 2
"""

from __future__ import annotations

from argparse import ArgumentParser
from compression import zstd
import json
from multiprocessing import get_context
from pathlib import Path
import tempfile
import time
from typing import Any

import lief
import numpy as np
import polars as pl

from provexp.attacks.toolkit import ATTACKS
from provexp.attacks.toolkit import BUDGETS
from provexp.attacks.toolkit import build_attack
from provexp.attacks.toolkit import build_donor_pools
from provexp.attacks.toolkit import file_seed
from provexp.attacks.toolkit import make_wrapper
from provexp.attacks.toolkit import run_attack
from provexp.data.files import load_donors
from provexp.data.paths import EMBER2024_DATA
from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBReader
from provexp.data.tabular import load_manifest
from provexp.detectors import make_extractor
from provexp.parallel import map_watchdog

__all__ = ["main", "merge", "shard_names"]


################################################################################
# Files
################################################################################

def shard_names(files: Path, shard: int, num_shards: int, num_malware: int | None = None) -> list[str]:
    """The malware of a file list that shard `shard` of `num_shards` attacks (every num_shards-th, from the shard-th).

    Args:
        files: A file list with `name` and `label` columns.
        shard: This shard's index.
        num_shards: The number of shards.
        num_malware: Only the first this many malware of the list (smoke tests).

    Returns:
        The names, in the list's order.
    """
    if not 0 <= shard < num_shards:
        raise ValueError(f"--shard must lie in [0, {num_shards}), got {shard}.")
    names = pl.read_parquet(files).filter(pl.col("label") == 1)["name"].to_list()
    if num_malware is not None:
        names = names[:num_malware]
    return names[shard::num_shards]


################################################################################
# Parallel worker (one attack on one file; the detector, donor pools and extractors are per-worker globals)
################################################################################

_W: dict[str, Any] = {}


def _init_worker(features: Path, model: Path, rows: dict[str, Path], db: Path, section_pop: list[Any],
                 api_calls: list[Any], seed: int, iterations: int, binaries: Path | None) -> None:
    """Build the per-worker extractors, detector wrapper, reader and attack donor pools once."""
    lief.logging.disable()
    extractor = make_extractor(features)
    extractors = {store: make_extractor(path) for store, path in rows.items()}
    _W.update(wrapper=make_wrapper(model, extractor), extractors=extractors, section_pop=section_pop,
              api_calls=api_calls, seed=seed, iterations=iterations, binaries=binaries,
              reader=SimpleDBReader(SimpleDB(db, check=False)), tmp=tempfile.mkdtemp(prefix="attack_training_w_"))


def _work(task: tuple[str, str]) -> dict[str, Any]:
    """Run one (attack, file); return the adversarial file's feature rows, one per store, when it parses."""
    atk, name = task
    out_path = Path(_W["tmp"]) / f"{name[:16]}.{atk}"
    row: dict[str, Any] = {"name": name, "attack": atk, "ok": False, "evaded": False, "p_clean": float("nan"),
                           "p_adv": float("nan"), "bytes_added": 0, "phi": None}
    try:
        data = bytes(_W["reader"].get(name).data)
        problem = build_attack(atk, _W["wrapper"], _W["section_pop"], _W["api_calls"], iterations=_W["iterations"])
        adv_bytes, p_clean, p_adv = run_attack(problem, _W["wrapper"], data, out_path, seed=file_seed(_W["seed"], atk, name))
        phi = {store: x.feature_vector(adv_bytes).astype(np.float32) for store, x in _W["extractors"].items()}
        if _W["binaries"] is not None:
            target = _W["binaries"] / atk / f"{name}.zst"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(zstd.compress(adv_bytes))
        row.update(ok=True, evaded=bool(p_adv < 0.5), p_clean=p_clean, p_adv=p_adv,
                   bytes_added=len(adv_bytes) - len(data), phi=phi)
    except Exception as e:  # a file secml-malware cannot attack (e.g. an unparseable shift target) is skipped
        print(f"  WARN {atk} {name[:12]}: {type(e).__name__}: {str(e)[:120]}", flush=True)
    finally:
        out_path.unlink(missing_ok=True)
    return row


def _lost(task: tuple[str, str]) -> dict[str, Any]:
    """The row for a task whose worker died: counted as attempted, not valid."""
    atk, name = task
    return {"name": name, "attack": atk, "ok": False, "evaded": False, "p_clean": float("nan"),
            "p_adv": float("nan"), "bytes_added": 0, "phi": None}


################################################################################
# Outputs
################################################################################

_FILES_COLUMNS = ("name", "attack", "label", "p_clean", "p_adv", "bytes_added")


def _write_rows(outdir: Path, store: str, X: np.ndarray, files: pl.DataFrame, report: dict[str, Any]) -> None:
    """One store's rows: X.npy, files.parquet, report.json."""
    d = outdir / store
    d.mkdir(parents=True, exist_ok=True)
    np.save(d / "X.npy", X)
    files.write_parquet(d / "files.parquet")
    (d / "report.json").write_text(json.dumps(report, indent=2))


def merge(outdir: Path, num_shards: int) -> dict[str, Any]:
    """Assemble the shards' rows into {outdir}/<store>/ and sum their reports.

    Args:
        outdir: The run's output directory (its shards/ subdirectory holds the shards).
        num_shards: The number of shards; every one must be complete.

    Returns:
        The merged report.
    """
    shards = [outdir / "shards" / str(k) for k in range(num_shards)]
    missing = [s.name for s in shards if not (s / "report.json").exists()]
    if missing:
        raise RuntimeError(f"Shards {missing} of {outdir.as_posix()} are not complete; run them first.")
    reports = [json.loads((s / "report.json").read_text()) for s in shards]
    stores = reports[0]["stores"]
    attacks = reports[0]["attacks"]
    report: dict[str, Any] = {k: reports[0][k] for k in ("attacks", "budget", "seed", "seed_per_file", "model",
                                                          "features", "files", "donors", "stores")}
    report.update(num_shards=num_shards, num_malware=sum(r["num_malware"] for r in reports),
                  num_goodware=reports[0]["num_goodware"],
                  total_attempted=sum(r["total_attempted"] for r in reports),
                  total_valid=sum(r["total_valid"] for r in reports),
                  per_attack={a: {k: sum(r["per_attack"][a][k] for r in reports) for k in ("attempted", "valid", "evaded")}
                              for a in attacks})
    for store in stores:
        X = np.concatenate([np.load(s / store / "X.npy") for s in shards])
        files = pl.concat([pl.read_parquet(s / store / "files.parquet") for s in shards])
        _write_rows(outdir, store, X, files, report)
    (outdir / "report.json").write_text(json.dumps(report, indent=2))
    return report


################################################################################
# Main
################################################################################

def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--merge", action="store_true", help="Only assemble the --num_shards shards of --outdir.")
    parser.add_argument("--files", type=Path, help="The training file list (its label-1 rows are attacked).")
    parser.add_argument("--donors", type=Path, help="The donor list (training goodware).")
    parser.add_argument("--db", type=Path, default=EMBER2024_DATA / "tr", help="The SimpleDB of the TRAINING split.")
    parser.add_argument("--features", type=Path, help="The store whose extractor scores the target model.")
    parser.add_argument("--model", type=Path, help="The undefended detector the attacks target (its model.txt).")
    parser.add_argument("--rows", type=Path, nargs="+", help="The stores to save feature rows for (by directory name).")
    parser.add_argument("--keep_binaries", action="store_true", help="Save each valid adversarial file, compressed.")
    parser.add_argument("--attacks", nargs="+", default=list(ATTACKS), choices=list(ATTACKS))
    parser.add_argument("--budget", default="low", choices=list(BUDGETS),
                        help="Attack budget: Gimenez's low one, or the GAMMA paper's (provexp.attacks.toolkit.BUDGETS).")
    parser.add_argument("--num_malware", type=int, default=None, help="Only the list's first N malware (smoke tests).")
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--num_shards", type=int, default=1)
    parser.add_argument("--num_workers", type=int, default=16, help="Processes over (attack, file) tasks.")
    parser.add_argument("--seed", type=int, default=0, help="The base of each (attack, file)'s own seed.")
    parser.add_argument("--stall_timeout", type=float, default=2700.0,
                        help="Seconds with no finished task before the unfinished ones count as lost (a dead worker).")
    args = parser.parse_args()
    if args.merge:
        report = merge(args.outdir, args.num_shards)
        print(f"Merged {args.num_shards} shards: {report['total_valid']} valid of {report['total_attempted']} "
              f"attack runs, stores {report['stores']}.", flush=True)
        return
    for flag in ("files", "donors", "features", "model", "rows"):
        if getattr(args, flag) is None:
            raise ValueError(f"--{flag} is required (except with --merge).")
    if args.num_workers < 1:
        raise ValueError(f"--num_workers must be >= 1, got {args.num_workers}.")
    rows = {p.name: p for p in args.rows}
    if len(rows) != len(args.rows):
        raise ValueError(f"The --rows stores need distinct directory names: {args.rows}.")

    part = args.outdir / "shards" / str(args.shard)
    if (part / "report.json").exists():
        print(f"Shard {args.shard} is complete ({part.as_posix()}); skipping.", flush=True)
        return
    lief.logging.disable()
    names = shard_names(args.files, args.shard, args.num_shards, args.num_malware)
    goodware = load_donors(args.donors, args.db)
    print(f"Shard {args.shard}/{args.num_shards}: {len(names)} training malware to attack, {len(goodware)} goodware "
          f"donors; rows for {sorted(rows)}.", flush=True)
    binaries = args.outdir / "binaries" if args.keep_binaries else None

    with tempfile.TemporaryDirectory(prefix="attack_training_") as tmp:
        iterations, how_many = BUDGETS[args.budget]
        section_pop, api_calls = build_donor_pools(goodware, Path(tmp), how_many=how_many)
        print(f"Budget {args.budget}: {iterations} iterations; donor pools: {len(section_pop)} sections, "
              f"{len(api_calls)} API groups.", flush=True)
        tasks = [(atk, name) for atk in args.attacks for name in names]
        t0 = time.time()
        with get_context("spawn").Pool(args.num_workers, initializer=_init_worker,
                                       initargs=(args.features, args.model / "model.txt" if args.model.is_dir()
                                                 else args.model, rows, args.db, section_pop, api_calls, args.seed,
                                                 iterations, binaries)) as pool:
            results = map_watchdog(pool, _work, tasks, lost=_lost, stall_timeout=args.stall_timeout)
        print(f"{len(tasks)} attack runs in {time.time() - t0:.0f}s on {args.num_workers} workers.", flush=True)

    valid = [r for r in results if r["ok"]]
    files = pl.DataFrame([{"name": r["name"], "attack": r["attack"], "label": 1, "p_clean": r["p_clean"],
                           "p_adv": r["p_adv"], "bytes_added": r["bytes_added"]} for r in valid],
                         schema={"name": pl.Utf8, "attack": pl.Utf8, "label": pl.Int64, "p_clean": pl.Float64,
                                 "p_adv": pl.Float64, "bytes_added": pl.Int64})
    per_attack = {atk: {"attempted": sum(r["attack"] == atk for r in results),
                        "valid": sum(r["attack"] == atk and r["ok"] for r in results),
                        "evaded": sum(r["attack"] == atk and r["evaded"] for r in results)}
                  for atk in args.attacks}
    report = {"shard": args.shard, "num_shards": args.num_shards, "num_malware": len(names),
              "num_goodware": len(goodware), "attacks": list(args.attacks), "budget": args.budget, "seed": args.seed,
              "seed_per_file": True, "model": args.model.resolve().as_posix(),
              "features": args.features.resolve().as_posix(), "files": args.files.resolve().as_posix(),
              "donors": args.donors.resolve().as_posix(), "stores": sorted(rows),
              "total_valid": len(valid), "total_attempted": len(results), "per_attack": per_attack}
    for store, path in rows.items():
        dim = len(load_manifest(path)["feature_names"])
        X = (np.stack([r["phi"][store] for r in valid]) if valid else np.zeros((0, dim), np.float32))
        if X.shape[1] != dim:
            raise RuntimeError(f"Rows for {store} have width {X.shape[1]}, the store expects {dim}.")
        _write_rows(part, store, X, files.select(_FILES_COLUMNS), report)
    (part / "report.json").write_text(json.dumps(report, indent=2))  # last: marks the shard complete
    for atk, d in per_attack.items():
        print(f"{atk}: valid {d['valid']}/{d['attempted']}, evaded {d['evaded']}", flush=True)
    print(f"Saved {len(valid)} adversarial rows per store to {part.as_posix()}.", flush=True)


if __name__ == "__main__":
    main()
