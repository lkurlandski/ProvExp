"""
R18, the trial competitor: audit the evasions of a real-scored adaptive beam (run 144). For each evaded (defense, file)
pair, replay the search (it is deterministic: one seed, the pilot goodware as donors), take the best file it found, and
explain the score's drop by the defense's per-feature contributions (LightGBM `pred_contrib`) before and after: which
features carried it, their values, and how the trial table treated each (dropped, monotone, or free).

FOR ACADEMIC SECURITY RESEARCH ONLY. Replays our own search against our own detectors on the pilot test malware; the
adversarial files live in memory only.

A replay that does not reproduce the stored row (operations or final score) is reported with `!!`: the search, its
donors, or the defense changed since the run.

Usage (after run 144):
    PYTHONHASHSEED=0 OMP_NUM_THREADS=1 python scripts/trial_audit.py --defense trial trial-toolkit
"""

from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
import sys
from typing import Any
from typing import cast

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import a1_adaptive as A  # noqa: E402
from a_pv_attacks import load_pilot  # noqa: E402
from provexp.data.paths import EMBER2024_DATA  # noqa: E402

__all__ = ["Recorder", "marking"]

T = ROOT / "artifacts/experiments/r18_trial"
MODELS = ROOT / "artifacts/models/gbdt"
DEFENSES = {"trial": MODELS / "seed-0-s10-mfull-feat-trial",
            "trial-toolkit": MODELS / "seed-0-s10-mfull-feat-trial-toolkit",
            "mfull-feat": MODELS / "seed-0-s10-mfull-feat-loose"}
TABLES = {"trial": "trial-final", "trial-toolkit": "trial-final-toolkit"}


################################################################################
# Replay
################################################################################

class Recorder:
    """Delegates to the engine and remembers every file the search re-extracts (the beam's kept files)."""

    def __init__(self, engine: Any) -> None:
        self._e = engine
        self.seen: list[tuple[bytes, np.ndarray]] = []

    def score(self, x: bytes) -> np.ndarray:
        """The engine's feature row, recorded with its file."""
        phi: np.ndarray = self._e.score(x)
        self.seen.append((x, phi))
        return phi

    def __getattr__(self, k: str) -> Any:
        return getattr(self._e, k)


def marking(defense: str) -> dict[str, str]:
    """Feature -> "dropped" or "monotone+1" under the defense's trial table (absent: free); empty for other defenses."""
    tag = TABLES.get(defense)
    if tag is None:
        return {}
    out = {f: "dropped" for f in (T / f"{tag}.neutralize.txt").read_text().split()}
    for line in (T / f"{tag}.monotone.tsv").read_text().splitlines():
        f, s = line.rsplit("\t", 1)
        out[f] = f"monotone{int(s):+d}"
    return out


################################################################################
# Main
################################################################################

def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=T / "attacks/adaptive/adaptive.parquet")
    parser.add_argument("--defense", nargs="*", default=None, help="Only these defenses (default: all evaded).")
    parser.add_argument("--names", nargs="*", default=None, help="Only these files.")
    parser.add_argument("--queries", type=int, default=2000, help="The run's budget (run 144: 2,000).")
    parser.add_argument("--top", type=int, default=6, help="Features to list per evasion.")
    args = parser.parse_args()

    res = pl.read_parquet(args.results).filter(pl.col("evaded"))
    if args.defense:
        res = res.filter(pl.col("defense").is_in(args.defense))
    if args.names:
        res = res.filter(pl.col("name").is_in(args.names))
    # run 144's configuration (a1_adaptive.py's defaults where it passes none)
    config = {"ops": A.THREAT["M_full"], "pilot_files": ROOT / "artifacts/experiments/e1/seed-0/zeros/files.parquet",
              "db": EMBER2024_DATA / "ts", "search": "beam", "queries": args.queries, "seed": 0,
              "budget_frac": 0.05, "budget_min": 512 * 1024, "beam": 3, "draws": 2, "patience": 3,
              "checkpoints": (200, 1000, 2000), "score": "real"}
    malware, goodware = load_pilot(config["pilot_files"], config["db"])
    data_of = dict(malware)
    A._init_worker(config, malware=malware, goodware=goodware)
    engine = A._W["engine"]
    names = engine.vector.feature_names
    for row in res.iter_rows(named=True):
        d, name = row["defense"], row["name"]
        booster = A.padded_booster(DEFENSES[d], engine.dim)
        targets = [(b, s) for b in A.target_buckets(booster, A._W["extractor"].feature_names, 8, None) for s in (-1, 1)]
        rec = Recorder(engine)

        def menu(rng: np.random.Generator, rec: Recorder = rec, targets: list[tuple[int, int]] = targets) -> list[Any]:
            return A.full_menu(cast(A.Engine, rec), A._W["donors"], rng, targets, A._W["names"], config["ops"])

        z = data_of[name]
        cap = max(int(0.05 * len(z)), 512 * 1024)
        r = A.beam_search(booster, cast(A.Engine, rec), z, row["tau"], menu, args.queries, 0, cap, beam=3, draws=2, patience=3,
                          checkpoints=(200, 1000, 2000))
        if r["ops"] != row["ops"] or abs(r["p_adv_real"] - row["p_adv_real"]) > 1e-9:
            print(f"!! {d} {name[:12]}: replay differs ({r['ops']} {r['p_adv_real']:.4g} vs {row['ops']} "
                  f"{row['p_adv_real']:.4g})")
        phis = [phi for _, phi in rec.seen]
        x0 = engine.score(z).reshape(1, -1)
        x1 = phis[int(np.argmin(booster.predict(np.stack(phis))))].reshape(1, -1)
        delta = (booster.predict(x1, pred_contrib=True)[0][:-1] - booster.predict(x0, pred_contrib=True)[0][:-1])
        delta = delta[: engine.dim]
        mark = marking(d)
        print(f"{d:14s} {name[:12]} ops={r['ops']} logit {A._logit(row['p_clean']):+.2f} -> "
              f"{A._logit(r['p_adv_real']):+.2f} (tau {row['tau_logit']:+.2f})")
        for i in np.argsort(delta)[: args.top]:
            if delta[i] >= -1e-6:
                break
            print(f"    {delta[i]:+.2f}  {names[i]:40s} {x0[0, i]:.4g} -> {x1[0, i]:.4g}  [{mark.get(names[i], 'free')}]")


if __name__ == "__main__":
    main()
