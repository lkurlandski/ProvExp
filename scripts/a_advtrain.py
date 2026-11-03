"""
Direction A, item 10 (review R1a/step 5): generate adversarial training examples for the adversarial-training baseline
of Table 7 (the detector table). This attacks a sample of TRAINING malware with Gimenez et al.'s toolkit (the four
"seen" secml-malware attacks by default), featurizes each valid adversarial file, and saves the feature rows so
`scripts/train_classic.py --augment` can append them to the training split and retrain the unconstrained GBDT.

FOR ACADEMIC SECURITY RESEARCH ONLY. This runs published secml-malware attacks against our own undefended detector, on
our own training samples, solely to build a standard adversarial-training defense to compare against the sound
detectors. No new evasion technique is developed and nothing is deployed; adversarial files are written to a scratch
directory only so they can be re-extracted into features.

The attacks are run on TRAINING malware (and TRAINING goodware donors), never the pilot (test) malware, so the
adversarial-training examples never leak the evaluation set. Each valid adversarial file keeps label 1 (malware); the
original file need not have been detected (standard adversarial augmentation adds every perturbed malware).

Outputs, in `{outdir}/`:
    X.npy           float32 (k, d): the feature rows of the k valid adversarial files, in the store's layout
    files.parquet   one row per saved example: name, attack, label (1), p_clean, p_adv, bytes_added
    report.json     per attack: attempted, valid (parsed), evaded; the malware/goodware counts and the seed

Usage (smoke on two malware, one attack):
    PYTHONHASHSEED=0 python scripts/a_advtrain.py --outdir /tmp/adv --num_malware 2 --attacks padding --num_workers 2
"""

from __future__ import annotations

from argparse import ArgumentParser
import json
from multiprocessing import get_context
from pathlib import Path
import tempfile
import time
from typing import Any
from typing import Optional

import lief
import numpy as np
import polars as pl

from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBReader
from provexp.data.tabular import load_manifest
from provexp.featuresets.ember2024.features import merge_import_descriptors
from provexp.featuresets.ember2024.features import PEFeatureExtractor

from a_pv_attacks import ATTACKS
from a_pv_attacks import build_attack
from a_pv_attacks import build_donor_pools
from a_pv_attacks import make_wrapper
from a_pv_attacks import run_attack

ROOT = Path(__file__).resolve().parent.parent

# The four attacks Gimenez et al.'s PV selection is built from (scripts/a1_evaluate.SEEN); the default training set,
# so Table 7's "seen" column is a true seen-attack test and the other four attacks are a held-out generalization test.
SEEN = ("padding", "gamma_sections", "gamma_shift", "content_shift")

__all__ = ["load_training", "main"]


################################################################################
# Training-sample loading
################################################################################

def load_training(features: Path, db_dir: Path, num_malware: int, num_goodware: int,
                  seed: int) -> tuple[list[tuple[str, bytes]], list[tuple[str, bytes]]]:
    """A seeded sample of training malware (to attack) and training goodware (attack donors), as (name, bytes) lists.

    Args:
        features: The feature store; its `tr/meta.parquet` names the training split.
        db_dir: The SimpleDB directory for the training split (the bytes).
        num_malware: How many training malware to sample.
        num_goodware: How many training goodware to sample as donors for the section/import attacks.
        seed: The sampling seed.

    Returns:
        (malware, goodware) as (name, bytes) lists, each a seeded sample of the training split.
    """
    meta = pl.read_parquet(Path(features) / "tr" / "meta.parquet")
    rng = np.random.default_rng(seed)
    reader = SimpleDBReader(SimpleDB(db_dir, check=False))

    def sample(label: int, k: int) -> list[tuple[str, bytes]]:
        names = meta.filter(pl.col("label") == label)["name"].to_list()
        if k > len(names):
            raise ValueError(f"Asked for {k} label-{label} training files, only {len(names)} exist.")
        chosen = rng.choice(len(names), size=k, replace=False)
        return [(names[int(i)], bytes(reader.get(names[int(i)]).data)) for i in sorted(chosen)]

    return sample(1, num_malware), sample(0, num_goodware)


################################################################################
# Parallel worker (one attack on one file; the detector, donor pools, extractor are per-worker globals)
################################################################################

_W: dict[str, Any] = {}


def _init_worker(model: Path, section_pop: list[Any], api_calls: list[Any], seed: int) -> None:
    """Build the per-worker extractor, detector wrapper, and attack donor pools once."""
    lief.logging.disable()
    extractor = merge_import_descriptors(PEFeatureExtractor())  # quirk-fixed, matches artifacts/features/ember2024
    _W.update(extractor=extractor, wrapper=make_wrapper(model, extractor), section_pop=section_pop,
              api_calls=api_calls, seed=seed, tmp=tempfile.mkdtemp(prefix="a_advtrain_w_"))


def _work(task: tuple[str, str, bytes]) -> dict[str, Any]:
    """Run one (attack, file); return the adversarial feature vector (as a list) when the file parses."""
    atk, name, data = task
    extractor, wrapper = _W["extractor"], _W["wrapper"]
    out_path = Path(_W["tmp"]) / f"{name[:16]}.{atk}"
    row: dict[str, Any] = {"name": name, "attack": atk, "ok": False, "evaded": False,
                           "p_clean": float("nan"), "p_adv": float("nan"), "bytes_added": 0, "phi": None}
    try:
        problem = build_attack(atk, wrapper, _W["section_pop"], _W["api_calls"])
        adv_bytes, p_clean, p_adv = run_attack(problem, wrapper, data, out_path, seed=_W["seed"])
        phi1 = extractor.feature_vector(adv_bytes)
        row.update(ok=True, evaded=bool(p_adv < 0.5), p_clean=p_clean, p_adv=p_adv,
                   bytes_added=len(adv_bytes) - len(data), phi=phi1.astype(np.float32).tolist())
    except Exception as e:  # a file secml-malware cannot attack (e.g. an unparseable shift target) is skipped
        print(f"  WARN {atk} {name[:12]}: {type(e).__name__}: {str(e)[:120]}", flush=True)
    return row


################################################################################
# Main
################################################################################

def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts/features/ember2024",
                        help="The feature store (its tr/meta.parquet names the training split; the layout X.npy uses).")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/tr"),
                        help="The SimpleDB directory for the TRAINING split.")
    parser.add_argument("--model", type=Path, default=ROOT / "artifacts/models/gbdt/seed-0/model.txt",
                        help="The undefended detector the attacks target.")
    parser.add_argument("--attacks", nargs="+", default=list(SEEN), choices=list(ATTACKS),
                        help="Which toolkit attacks to generate with (default: the four PV 'seen' attacks).")
    parser.add_argument("--num_malware", type=int, default=400, help="Training malware to attack.")
    parser.add_argument("--num_goodware", type=int, default=50, help="Training goodware donors for the attacks.")
    parser.add_argument("--num_workers", type=int, default=16, help="Processes over (attack, file) tasks.")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    if args.num_workers < 1:
        raise ValueError(f"--num_workers must be >= 1, got {args.num_workers}.")

    lief.logging.disable()
    args.outdir.mkdir(parents=True, exist_ok=True)
    dim = len(load_manifest(args.features)["feature_names"])

    malware, goodware = load_training(args.features, args.db, args.num_malware, args.num_goodware, args.seed)
    print(f"Training sample: {len(malware)} malware to attack, {len(goodware)} goodware donors.", flush=True)

    with tempfile.TemporaryDirectory(prefix="a_advtrain_") as tmp:
        section_pop, api_calls = build_donor_pools(goodware, Path(tmp))
        print(f"Donor pools: {len(section_pop)} sections, {len(api_calls)} API groups.", flush=True)
        tasks = [(atk, name, data) for atk in args.attacks for name, data in malware]
        t0 = time.time()
        ctx = get_context("spawn")
        with ctx.Pool(args.num_workers, initializer=_init_worker,
                      initargs=(args.model, section_pop, api_calls, args.seed)) as pool:
            results = pool.map(_work, tasks)
        print(f"{len(tasks)} attack runs in {time.time() - t0:.0f}s on {args.num_workers} workers.", flush=True)

    valid = [r for r in results if r["ok"]]
    phis = np.asarray([r.pop("phi") for r in valid], dtype=np.float32) if valid else np.zeros((0, dim), np.float32)
    if phis.shape[0] and phis.shape[1] != dim:
        raise RuntimeError(f"Adversarial features have width {phis.shape[1]}, store expects {dim}.")
    for r in results:
        r.pop("phi", None)

    np.save(args.outdir / "X.npy", phis)
    files = pl.DataFrame([{"name": r["name"], "attack": r["attack"], "label": 1, "p_clean": r["p_clean"],
                           "p_adv": r["p_adv"], "bytes_added": r["bytes_added"]} for r in valid])
    files.write_parquet(args.outdir / "files.parquet")

    per_attack = {atk: {"attempted": sum(r["attack"] == atk for r in results),
                        "valid": sum(r["attack"] == atk and r["ok"] for r in results),
                        "evaded": sum(r["attack"] == atk and r["evaded"] for r in results)}
                  for atk in args.attacks}
    report = {"num_malware": len(malware), "num_goodware": len(goodware), "attacks": list(args.attacks),
              "seed": args.seed, "model": args.model.resolve().as_posix(), "features": args.features.resolve().as_posix(),
              "total_valid": int(phis.shape[0]), "total_attempted": len(results), "per_attack": per_attack}
    (args.outdir / "report.json").write_text(json.dumps(report, indent=2))
    for atk, d in per_attack.items():
        print(f"{atk}: valid {d['valid']}/{d['attempted']}, evaded {d['evaded']}", flush=True)
    print(f"Saved {phis.shape[0]} adversarial training rows to {args.outdir.as_posix()}.", flush=True)


if __name__ == "__main__":
    main()
