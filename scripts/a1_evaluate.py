"""
Direction A, Table A1 (docs/direction-A-A1-design.md): the attack-evaluation harness for the toolkit columns.

FOR ACADEMIC SECURITY RESEARCH ONLY. This runs Gimenez et al.'s eight published secml-malware attacks against our own
detectors, on our own pilot samples, solely to evaluate defenses: which detectors stay robust to attacks that were
(seen) and were not (held-out) used to build PV selection. No new evasion technique is developed and nothing is
deployed; attacked files are written only so they can be re-extracted and re-scored.

One protocol for every cell:
    operating point   each defense's threshold is calibrated to `--fpr` (1%) on the goodware of its own test
                      predictions (ts_predictions.parquet): detected means p > tau, and at most 1% of goodware is
    malware           the detected pilot malware, attacked only where the defense detects it at tau
    budget            Gimenez's low budget (population 10, 10 iterations); an attacked file whose added bytes exceed
                      max(--budget_frac x size, --budget_min) counts as not evaded (over_budget)
    ground truth      the attacked file is written, read back, re-extracted, and re-scored; evaded means p_adv <= tau

The defenses are GBDTs on one feature store (`--features`: its manifest names the extractor); every defense is scored
with that store's extractor. The quick seen/held-out split (`--seen`) is a quick check only; the formal version is
leave-one-out (eight PV models; docs/direction-A-A1-design.md, decision 2).

Outputs, in `{outdir}/`:
    results.parquet   one row per (defense, attack, file): p_clean, p_adv, tau, evaded, bytes_added, over_budget, ok,
                      truncated, seconds
    table.json        per defense: tau, detected, per-attack evasion, and per group (seen, held-out) the fraction of
                      detected files evaded by at least one attack of the group, overall and split by truncation

Usage (smoke on two files, one attack):
    PYTHONHASHSEED=0 python scripts/a1_evaluate.py --outdir /tmp/a1 --num_malware 2 --attacks padding \
        --defense ref=artifacts/models/gbdt/seed-0-s10-ref --features artifacts/features/ember2024-sums-10
"""

from __future__ import annotations

from argparse import ArgumentParser
import json
from multiprocessing import get_context
from pathlib import Path
import sys
import tempfile
import time
from typing import Any

import lief
import numpy as np
import polars as pl

from provexp.data.tabular import load_manifest
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.features import merge_import_descriptors
from provexp.featuresets.ember2024.sums import SumsFeatureExtractor

sys.path.insert(0, str(Path(__file__).parent))
from a_pv_attacks import ATTACKS  # noqa: E402
from a_pv_attacks import build_attack  # noqa: E402
from a_pv_attacks import build_donor_pools  # noqa: E402
from a_pv_attacks import load_pilot  # noqa: E402
from a_pv_attacks import make_wrapper  # noqa: E402
from a_pv_attacks import run_attack  # noqa: E402

__all__ = ["calibrate_threshold", "group_evasion", "make_extractor"]

ROOT = Path(__file__).resolve().parent.parent
MAX_LENGTH = 4_000_000
SEEN = ("padding", "gamma_sections", "gamma_shift", "content_shift")


################################################################################
# Protocol
################################################################################

def make_extractor(features: Path) -> PEFeatureExtractor:
    """The extractor a feature store was built with (quirk-fixed in either case), checked against its manifest."""
    manifest = load_manifest(features)
    extractor = SumsFeatureExtractor() if manifest["feature_set"] == "ember2024-sums" \
        else merge_import_descriptors(PEFeatureExtractor())
    if extractor.feature_names != manifest["feature_names"]:
        raise RuntimeError(f"The extractor does not match the feature names of {features.as_posix()}.")
    return extractor


def calibrate_threshold(probs: np.ndarray, labels: np.ndarray, fpr: float) -> float:
    """
    The threshold tau at which p > tau flags at most `fpr` of the goodware.

    Args:
        probs: Predicted malware probabilities on the test split.
        labels: Their labels (0 goodware, 1 malware).
        fpr: The target false-positive rate.

    Returns:
        tau, the (1 - fpr) order statistic of the goodware probabilities.
    """
    good = np.sort(probs[labels == 0])[::-1]
    if good.size == 0:
        raise ValueError("No goodware to calibrate on.")
    return float(good[min(int(fpr * good.size), good.size - 1)])


def group_evasion(rows: pl.DataFrame, attacks: list[str]) -> dict[str, Any]:
    """The fraction of attacked (detected) files that at least one attack of `attacks` evaded, within budget."""
    g = rows.filter(pl.col("attack").is_in(attacks))
    if g.height == 0:
        return {"files": 0, "evaded": 0, "rate": None}
    per_file = g.group_by("name").agg(pl.col("evaded").any())
    n, e = per_file.height, int(per_file["evaded"].sum())
    return {"files": n, "evaded": e, "rate": e / n}


################################################################################
# Parallel workers (one attack on one file against one defense)
################################################################################

_W: dict[str, Any] = {}


def _init_worker(features: Path, models: dict[str, str], section_pop: list[Any], api_calls: list[Any],
                 seed: int) -> None:
    """Build the extractor and one detector wrapper per defense, once per worker."""
    lief.logging.disable()
    extractor = make_extractor(features)
    _W.update(wrappers={d: make_wrapper(Path(m), extractor) for d, m in models.items()}, section_pop=section_pop,
              api_calls=api_calls, seed=seed, tmp=tempfile.mkdtemp(prefix="a1_w_"))


def _work(task: tuple[str, str, str, bytes, float, int]) -> dict[str, Any]:
    """Run one (defense, attack, file) and score the re-extracted result at the defense's threshold."""
    defense, atk, name, data, tau, cap = task
    wrapper = _W["wrappers"][defense]
    out_path = Path(_W["tmp"]) / f"{defense}.{name[:16]}.{atk}"
    start = time.time()
    p_clean = p_adv = float("nan")
    added, ok, error = 0, False, ""
    try:
        problem = build_attack(atk, wrapper, _W["section_pop"], _W["api_calls"])
        adv_bytes, p_clean, p_adv = run_attack(problem, wrapper, data, out_path, seed=_W["seed"])
        added, ok = len(adv_bytes) - len(data), True
    except Exception as e:
        error = f"{type(e).__name__}: {str(e)[:200]}"
        print(f"  WARN {defense} {atk} {name[:12]}: {error}", flush=True)
    finally:
        out_path.unlink(missing_ok=True)
    over = added > cap
    return {"defense": defense, "attack": atk, "name": name, "tau": tau, "p_clean": p_clean, "p_adv": p_adv,
            "evaded": bool(ok and not over and p_adv <= tau), "bytes_added": added, "over_budget": over, "ok": ok,
            "truncated": len(data) >= MAX_LENGTH, "error": error, "seconds": time.time() - start}


################################################################################
# Main
################################################################################

def parse_defenses(specs: list[str]) -> dict[str, Path]:
    """`name=model_dir` pairs, in order."""
    out: dict[str, Path] = {}
    for spec in specs:
        name, _, path = spec.partition("=")
        if not name or not path:
            raise ValueError(f"Expected name=model_dir, got {spec!r}.")
        out[name] = Path(path)
    return out


def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--defense", action="append", required=True, help="name=model_dir (repeatable).")
    parser.add_argument("--features", type=Path, required=True, help="The feature store the defenses were trained on.")
    parser.add_argument("--pilot_files", type=Path, default=ROOT / "artifacts/experiments/e1/seed-0/zeros/files.parquet")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--attacks", nargs="+", default=list(ATTACKS), choices=list(ATTACKS))
    parser.add_argument("--seen", nargs="+", default=list(SEEN), choices=list(ATTACKS))
    parser.add_argument("--fpr", type=float, default=0.01)
    parser.add_argument("--budget_frac", type=float, default=0.05)
    parser.add_argument("--budget_min", type=int, default=512 * 1024)
    parser.add_argument("--num_malware", type=int, default=None, help="Cap on malware files (for smoke tests).")
    parser.add_argument("--num_workers", type=int, default=8, help="Processes over tasks (<= 16).")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    if args.num_workers > 16:
        raise ValueError("At most 16 workers (run/ resource budget).")

    lief.logging.disable()
    args.outdir.mkdir(parents=True, exist_ok=True)
    defenses = parse_defenses(args.defense)
    extractor = make_extractor(args.features)

    malware, goodware = load_pilot(args.pilot_files, args.db)
    if args.num_malware is not None:
        malware = malware[: args.num_malware]
    print(f"Pilot: {len(malware)} malware, {len(goodware)} goodware donors; {len(defenses)} defenses.", flush=True)

    # Thresholds, and which pilot malware each defense detects (scored from the files themselves).
    import lightgbm
    X = np.stack([extractor.feature_vector(data) for _, data in malware])  # type: ignore[no-untyped-call]
    taus: dict[str, float] = {}
    detected: dict[str, list[int]] = {}
    for d, mdir in defenses.items():
        pred = pl.read_parquet(mdir / "ts_predictions.parquet")
        taus[d] = calibrate_threshold(pred["prob"].to_numpy(), pred["label"].to_numpy(), args.fpr)
        p = np.asarray(lightgbm.Booster(model_file=str(mdir / "model.txt")).predict(X))
        detected[d] = [i for i in range(len(malware)) if p[i] > taus[d]]
        print(f"  {d}: tau={taus[d]:.4f}, detects {len(detected[d])}/{len(malware)} pilot malware", flush=True)

    caps = [max(int(args.budget_frac * len(data)), args.budget_min) for _, data in malware]
    tasks = [(d, atk, malware[i][0], malware[i][1], taus[d], caps[i])
             for d in defenses for atk in args.attacks for i in detected[d]]
    with tempfile.TemporaryDirectory(prefix="a1_") as tmp:
        section_pop, api_calls = build_donor_pools(goodware, Path(tmp))
        t0 = time.time()
        models = {d: str(m / "model.txt") for d, m in defenses.items()}
        with get_context("spawn").Pool(args.num_workers, initializer=_init_worker,
                                       initargs=(args.features, models, section_pop, api_calls, args.seed)) as pool:
            rows = pool.map(_work, tasks, chunksize=1)
        print(f"{len(tasks)} attack runs in {time.time() - t0:.0f}s on {args.num_workers} workers.", flush=True)

    if not rows:
        raise RuntimeError("No defense detects any pilot malware; nothing to attack.")
    results = pl.DataFrame(rows)
    results.write_parquet(args.outdir / "results.parquet")
    held_out = [a for a in args.attacks if a not in args.seen]
    seen = [a for a in args.attacks if a in args.seen]
    table: dict[str, Any] = {"protocol": {"fpr": args.fpr, "budget_frac": args.budget_frac,
                                          "budget_min": args.budget_min, "seed": args.seed,
                                          "features": args.features.resolve().as_posix(), "seen": seen,
                                          "held_out": held_out,
                                          "split_note": "quick seen/held-out split; formal version is leave-one-out"},
                             "defenses": {}}
    for d in defenses:
        r = results.filter(pl.col("defense") == d)
        entry: dict[str, Any] = {"model": defenses[d].as_posix(), "tau": taus[d], "detected": len(detected[d]),
                                 "per_attack": {}, "groups": {}}
        for atk in args.attacks:
            a = r.filter(pl.col("attack") == atk)
            entry["per_attack"][atk] = {"runs": a.height, "evaded": int(a["evaded"].sum()),
                                        "failed": int((~a["ok"]).sum()), "over_budget": int(a["over_budget"].sum())}
        for group, atks in (("seen", seen), ("held_out", held_out), ("all", list(args.attacks))):
            entry["groups"][group] = {
                "all": group_evasion(r, atks),
                "truncated": group_evasion(r.filter(pl.col("truncated")), atks),
                "untruncated": group_evasion(r.filter(~pl.col("truncated")), atks),
            }
        table["defenses"][d] = entry
        g = entry["groups"]
        print(f"{d:16s} detected {len(detected[d]):2d}  seen {g['seen']['all']}  held-out {g['held_out']['all']}",
              flush=True)
    (args.outdir / "table.json").write_text(json.dumps(table, indent=2))
    print(f"Wrote {args.outdir}/results.parquet and table.json", flush=True)


if __name__ == "__main__":
    main()
