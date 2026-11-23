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
(attack, file) is seeded on its own (`--seed_per_file`). Each valid adversarial file of at most `--max_size` bytes
(4,000,000: the study's PE files up to 4 MB, the rule every attack is judged by; protocol (22)) keeps label 1; larger
outputs are counted (`over_size`) and train no defense.

The work splits into shards (`--shard k --num_shards N`: every N-th malware from the k-th), one per SLURM array task;
a shard whose report.json exists is skipped. `--merge` then assembles the shards.

The two GAMMA attacks write their edits with our byte-level writers (provexp.attacks.toolkit, session 103), growing
the headers first where they lack room for the new section headers (`hgr`); where no growth makes room (checked once
per file, `gamma_start`) the attack is not applicable: not run, and counted as `not_applicable`, not as attempted.
`--repair LOST` mends a complete shard whose run lost tasks to dead workers (LOST: lines `attack name`, as the LOST log
lines name them; session 76's 4-detectors/material/lost.txt): the lost tasks that apply are run again and their rows
appended, the others become not applicable; the shard's report records the repair, so a second one is a no-op.

Outputs:
    {outdir}/shards/{k}/<store>/X.npy, files.parquet   a shard's rows, one directory per store of `--rows`
    {outdir}/shards/{k}/report.json                    the shard's counts
    {outdir}/shards/{k}/room_check.parquet             the shard's files a GAMMA attack does not apply to, and why
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

from provexp.attacks.lief_check import DOS_ATTACKS
from provexp.attacks.lief_check import dos_header_extensible
from provexp.attacks.validity import output_invalid
from provexp.attacks.validity import structure
from provexp.attacks.validity import unreadable
from provexp.attacks.toolkit import ATTACKS
from provexp.attacks.toolkit import BUDGETS
from provexp.attacks.toolkit import build_attack
from provexp.attacks.toolkit import build_donor_pools
from provexp.attacks.toolkit import file_seed
from provexp.attacks.toolkit import gamma_room
from provexp.attacks.toolkit import make_wrapper
from provexp.attacks.toolkit import run_attack
from provexp.data.files import FileReader
from provexp.data.files import load_donors
from provexp.data.tabular import load_manifest
from provexp.detectors import MAX_LENGTH
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


def _init_worker(features: Path, model: Path, rows: dict[str, Path], section_pop: list[Any],
                 api_calls: list[Any], seed: int, iterations: int, binaries: Path | None, max_size: int) -> None:
    """Build the per-worker extractors, detector wrapper, reader and attack donor pools once."""
    lief.logging.disable()
    extractor = make_extractor(features)
    extractors = {store: make_extractor(path) for store, path in rows.items()}
    _W.update(wrapper=make_wrapper(model, extractor), extractors=extractors, section_pop=section_pop,
              api_calls=api_calls, seed=seed, iterations=iterations, binaries=binaries, max_size=max_size,
              reader=FileReader(), tmp=tempfile.mkdtemp(prefix="attack_training_w_"))


def _work(task: tuple[str, str]) -> dict[str, Any]:
    """Run one (attack, file); return the adversarial file's feature rows, one per store, when it parses."""
    atk, name = task
    out_path = Path(_W["tmp"]) / f"{name[:16]}.{atk}"
    row: dict[str, Any] = {"name": name, "attack": atk, "ok": False, "valid": False, "invalid_reason": "",
                           "evaded": False, "p_clean": float("nan"), "p_adv": float("nan"), "bytes_added": 0, "phi": None,
                           "header_growth": False, "over_size": False}
    try:
        data = _W["reader"].get(name)
        problem = build_attack(atk, _W["wrapper"], _W["section_pop"], _W["api_calls"], iterations=_W["iterations"])
        adv_bytes, p_clean, p_adv = run_attack(problem, _W["wrapper"], data, out_path, seed=file_seed(_W["seed"], atk, name))
        # The paper's validity rule (provexp.attacks.validity): an output that fails it trains no defense and is no
        # evidence that a feature can be lowered (session 85: 894 broken outputs had emptied PV's feature set).
        original, why = structure(data)
        invalid = (output_invalid(original, adv_bytes) or "") if original is not None else f"original: {why}"
        row.update(valid=not invalid, invalid_reason=invalid)
        over = len(adv_bytes) > _W["max_size"]
        phi = {store: x.feature_vector(adv_bytes).astype(np.float32) for store, x in _W["extractors"].items()}
        if _W["binaries"] is not None and not invalid and not over:
            target = _W["binaries"] / atk / f"{name}.zst"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(zstd.compress(adv_bytes))
        row.update(ok=True, evaded=bool(not invalid and not over and p_adv < 0.5), p_clean=p_clean, p_adv=p_adv,
                   over_size=over,
                   bytes_added=len(adv_bytes) - len(data), phi=phi,
                   header_growth=bool(getattr(problem, "header_growth", False)))
    except Exception as e:  # a file secml-malware cannot attack (e.g. an unparseable shift target) is skipped
        print(f"  WARN {atk} {name[:12]}: {type(e).__name__}: {str(e)[:120]}", flush=True)
    finally:
        out_path.unlink(missing_ok=True)
    return row


def _lost(task: tuple[str, str]) -> dict[str, Any]:
    """The row for a task whose worker died: counted as attempted, not valid."""
    atk, name = task
    return {"name": name, "attack": atk, "ok": False, "evaded": False, "p_clean": float("nan"),
            "p_adv": float("nan"), "bytes_added": 0, "phi": None, "lost": True, "valid": False, "invalid_reason": "",
            "header_growth": False, "over_size": False}


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
    report: dict[str, Any] = {k: reports[0].get(k) for k in ("attacks", "budget", "max_size", "seed", "seed_per_file", "model",
                                                          "features", "files", "donors", "stores")}
    report.update(num_shards=num_shards, num_malware=sum(r["num_malware"] for r in reports),
                  num_goodware=reports[0]["num_goodware"],
                  total_attempted=sum(r["total_attempted"] for r in reports),
                  total_valid=sum(r["total_valid"] for r in reports),
                  per_attack={a: {k: sum(r["per_attack"][a].get(k, 0) for r in reports)
                                  for k in ("attempted", "valid", "invalid", "invalid_pefile_only", "over_size",
                                            "evaded", "header_growth", "not_applicable")} for a in attacks})
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
    parser.add_argument("--features", type=Path, help="The store whose extractor scores the target model.")
    parser.add_argument("--model", type=Path, help="The undefended detector the attacks target (its model.txt).")
    parser.add_argument("--rows", type=Path, nargs="+", help="The stores to save feature rows for (by directory name).")
    parser.add_argument("--keep_binaries", action="store_true", help="Save each valid adversarial file, compressed.")
    parser.add_argument("--attacks", nargs="+", default=list(ATTACKS), choices=list(ATTACKS))
    parser.add_argument("--budget", default="low", choices=list(BUDGETS),
                        help="Attack budget: Gimenez's low one, or the GAMMA paper's (provexp.attacks.toolkit.BUDGETS).")
    parser.add_argument("--max_size", type=int, default=MAX_LENGTH,
                        help="The largest output kept as material (provexp.detectors.byte_room; protocol (22)).")
    parser.add_argument("--num_malware", type=int, default=None, help="Only the list's first N malware (smoke tests).")
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--num_shards", type=int, default=1)
    parser.add_argument("--num_workers", type=int, default=16, help="Processes over (attack, file) tasks.")
    parser.add_argument("--seed", type=int, default=0, help="The base of each (attack, file)'s own seed.")
    parser.add_argument("--stall_timeout", type=float, default=3600.0,
                        help="Seconds with no finished task before the unfinished ones count as lost (over the limit, or a "
                        "dead worker).")
    parser.add_argument("--repair", type=Path, default=None,
                        help="Mend a complete shard: re-run its lost tasks listed in this file (`attack name` lines).")
    args = parser.parse_args()
    if args.merge:
        merged = merge(args.outdir, args.num_shards)
        print(f"Merged {args.num_shards} shards: {merged['total_valid']} valid of {merged['total_attempted']} "
              f"attack runs, stores {merged['stores']}.", flush=True)
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
    done = (part / "report.json").exists()
    if args.repair is None and done:
        print(f"Shard {args.shard} is complete ({part.as_posix()}); skipping.", flush=True)
        return
    if args.repair is not None:
        if not done:
            raise RuntimeError(f"--repair needs a complete shard; {part.as_posix()} has no report.json.")
        if "repair" in json.loads((part / "report.json").read_text()):
            print(f"Shard {args.shard} is already repaired; skipping.", flush=True)
            return
    lief.logging.disable()
    names = shard_names(args.files, args.shard, args.num_shards, args.num_malware)
    goodware = load_donors(args.donors)
    print(f"Shard {args.shard}/{args.num_shards}: {len(names)} training malware to attack, {len(goodware)} goodware "
          f"donors; rows for {sorted(rows)}.", flush=True)
    binaries = args.outdir / "binaries" if args.keep_binaries else None
    candidates = [(atk, name) for atk in args.attacks for name in names]
    if args.repair is not None:
        lost = {tuple(line.split()[:2]) for line in args.repair.read_text().splitlines()
                if line.strip() and not line.startswith("#")}
        candidates = [t for t in candidates if t in lost]
        print(f"Repair: {len(candidates)} lost tasks of this shard in {args.repair.as_posix()}.", flush=True)

    # The donor pools (GAMMA's room check needs the number of donor sections).
    with tempfile.TemporaryDirectory(prefix="attack_training_") as tmp:
        iterations, how_many = BUDGETS[args.budget]
        section_pop, api_calls = build_donor_pools(goodware, Path(tmp), how_many=how_many)
    print(f"Budget {args.budget}: {iterations} iterations; donor pools: {len(section_pop)} sections, "
          f"{len(api_calls)} API groups.", flush=True)
    # GAMMA's room, once per file (provexp.attacks.toolkit.gamma_start): where the headers cannot hold the new section
    # headers even after growing them, the attack is not applicable.
    reader = FileReader()
    reader.check(names)
    room_names = sorted({name for _, name in candidates})
    room = dict(zip(room_names, gamma_room((reader.get(n) for n in room_names), sorted({a for a, _ in candidates}),
                                           len(section_pop), args.num_workers)))
    bad = {(a, n): r for n in room_names for a, r in room[n].items() if r is not None}
    part.mkdir(parents=True, exist_ok=True)
    pl.DataFrame({"name": [n for _, n in bad], "attack": [a for a, _ in bad], "reason": list(bad.values())},
                 schema={"name": pl.Utf8, "attack": pl.Utf8, "reason": pl.Utf8}).write_parquet(
        part / ("room_check.parquet" if args.repair is None else "room_check-repair.parquet"))
    for a in sorted({a for a, _ in bad}):
        print(f"GAMMA room: {a} is not applicable to {sum(k[0] == a for k in bad)} of {len(room_names)} files.",
              flush=True)
    # The attacks that extend the DOS header are not applicable to a file whose PE header starts inside it.
    no_dos = {n for n in sorted({name for atk, name in candidates if atk in DOS_ATTACKS})
              if not dos_header_extensible(reader.get(n))}
    print(f"DOS header: {len(no_dos)} files cannot be extended; {DOS_ATTACKS} are not applicable to them.", flush=True)
    # No attack applies to an original one of the two parsers does not read (provexp.attacks.validity).
    with get_context("spawn").Pool(args.num_workers) as pool:
        unread = {n for n, r in zip(names, pool.map(unreadable, [reader.get(n) for n in names], chunksize=4))
                  if r is not None}
    print(f"Validity: {len(unread)} of {len(names)} files are not read by both parsers; no attack applies.", flush=True)
    skipped = [(atk, name) for atk, name in candidates
               if (atk, name) in bad or (atk in DOS_ATTACKS and name in no_dos) or name in unread]
    left_out = set(skipped)
    tasks = [t for t in candidates if t not in left_out]

    results: list[dict[str, Any]] = []
    if tasks:
        t0 = time.time()
        with get_context("spawn").Pool(args.num_workers, initializer=_init_worker,
                                       initargs=(args.features, args.model / "model.txt" if args.model.is_dir()
                                                 else args.model, rows, section_pop, api_calls,
                                                 args.seed, iterations, binaries, args.max_size)) as pool:
            results = map_watchdog(pool, _work, tasks, lost=_lost, stall_timeout=args.stall_timeout)
        print(f"{len(tasks)} attack runs in {time.time() - t0:.0f}s on {args.num_workers} workers.", flush=True)

    # Only outputs that pass the validity rule and the size rule are kept.
    valid = [r for r in results if r["ok"] and r["valid"] and not r.get("over_size", False)]
    # The outputs the rule rejects, with the reason: "pefile only" ones are the extractor's quirks to fix at the source.
    pl.DataFrame([{"name": r["name"], "attack": r["attack"], "reason": r["invalid_reason"]} for r in results
                  if r["ok"] and not r["valid"]], schema={"name": pl.Utf8, "attack": pl.Utf8, "reason": pl.Utf8}
                 ).write_parquet(part / ("invalid.parquet" if args.repair is None else "invalid-repair.parquet"))
    files = pl.DataFrame([{"name": r["name"], "attack": r["attack"], "label": 1, "p_clean": r["p_clean"],
                           "p_adv": r["p_adv"], "bytes_added": r["bytes_added"]} for r in valid],
                         schema={"name": pl.Utf8, "attack": pl.Utf8, "label": pl.Int64, "p_clean": pl.Float64,
                                 "p_adv": pl.Float64, "bytes_added": pl.Int64})
    counts = {atk: {"attempted": sum(r["attack"] == atk for r in results),
                    "valid": sum(r["attack"] == atk and r["ok"] and r["valid"] for r in results),  # over_size among them
                    "invalid": sum(r["attack"] == atk and r["ok"] and not r["valid"] for r in results),
                    "invalid_pefile_only": sum(r["attack"] == atk and r["invalid_reason"].startswith("pefile only")
                                               for r in results),
                    "over_size": sum(r["attack"] == atk and r["ok"] and r["valid"] and r.get("over_size", False)
                                     for r in results),
                    "evaded": sum(r["attack"] == atk and r["evaded"] for r in results),
                    "header_growth": sum(r["attack"] == atk and r.get("header_growth", False) for r in results),
                    "not_applicable": sum(a == atk for a, _ in skipped)}
              for atk in args.attacks}
    if args.repair is None:
        per_attack = counts
        report: dict[str, Any] = {
            "shard": args.shard, "num_shards": args.num_shards, "num_malware": len(names),
            "num_goodware": len(goodware), "attacks": list(args.attacks), "budget": args.budget,
            "max_size": args.max_size, "seed": args.seed,
            "seed_per_file": True, "model": args.model.resolve().as_posix(),
            "features": args.features.resolve().as_posix(), "files": args.files.resolve().as_posix(),
            "donors": args.donors.resolve().as_posix(), "stores": sorted(rows),
            "total_valid": len(valid), "total_attempted": len(results), "per_attack": per_attack}
    else:
        # The lost tasks were counted as attempted and not valid: re-run ones keep their attempt and add what they
        # produced; not-applicable ones leave the attempts.
        report = json.loads((part / "report.json").read_text())
        per_attack = report["per_attack"]
        for atk, c in counts.items():
            d = per_attack[atk]
            d["attempted"] -= c["not_applicable"]
            d["valid"] += c["valid"]
            d["invalid"] = d.get("invalid", 0) + c["invalid"]
            d["invalid_pefile_only"] = d.get("invalid_pefile_only", 0) + c["invalid_pefile_only"]
            d["over_size"] = d.get("over_size", 0) + c["over_size"]
            d["evaded"] += c["evaded"]
            d["header_growth"] = d.get("header_growth", 0) + c["header_growth"]
            d["not_applicable"] = d.get("not_applicable", 0) + c["not_applicable"]
        report["total_valid"] += len(valid)
        report["total_attempted"] -= len(skipped)
        report["repair"] = {"lost": args.repair.resolve().as_posix(), "tasks": len(candidates), "rerun": len(tasks),
                            "rerun_valid": len(valid), "lost_again": sum(bool(r.get("lost")) for r in results),
                            "not_applicable": len(skipped)}
    for store, path in rows.items():
        dim = len(load_manifest(path)["feature_names"])
        X = (np.stack([r["phi"][store] for r in valid]) if valid else np.zeros((0, dim), np.float32))
        if X.shape[1] != dim:
            raise RuntimeError(f"Rows for {store} have width {X.shape[1]}, the store expects {dim}.")
        store_files = files.select(_FILES_COLUMNS)
        if args.repair is not None:
            # NOTE: a repair interrupted after some stores were written may have appended these rows already; the
            # lost tasks had no rows before, so a (name, attack) already present is one such row and is not added twice.
            old_files = pl.read_parquet(part / store / "files.parquet")
            seen = set(zip(old_files["name"].to_list(), old_files["attack"].to_list()))
            keep = [i for i, r in enumerate(valid) if (r["name"], r["attack"]) not in seen]
            X = np.concatenate([np.load(part / store / "X.npy"), X[keep]])
            store_files = pl.concat([old_files, store_files[keep]])
        _write_rows(part, store, X, store_files, report)
    (part / "report.json").write_text(json.dumps(report, indent=2))  # last: marks the shard complete (or repaired)
    for atk, d in per_attack.items():
        print(f"{atk}: valid {d['valid']}/{d['attempted']}, evaded {d['evaded']}, not applicable "
              f"{d.get('not_applicable', 0)}", flush=True)
    print(f"{'Repaired' if args.repair is not None else 'Saved'}: {report['total_valid']} adversarial rows per store "
          f"in {part.as_posix()}.", flush=True)

if __name__ == "__main__":
    main()
