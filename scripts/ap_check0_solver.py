"""
Direction A', go/no-go check 0 (docs/direction-A-prime-mock.md): can an exact solver handle our GBDTs at all?

Table A'1 asks, per detector and file, for the lowest score any allowed change can reach. For a tree ensemble that is
a mixed-integer program (Kantchelian et al., ICML 2016): one binary per (feature, split threshold) saying whether the
feature lies at or below it, one leaf weight per leaf, and constraints that make each tree select exactly the leaf
the binaries route to. The objective is the ensemble's raw score (the malware log-odds); the solver minimizes it over
a region of feature vectors. If the minimum stays above the 1%-FPR threshold, no vector in the region evades (a
certificate); otherwise the minimizer is an evading vector.

This check needs no provenance: it only times the solver at our model sizes, on three regions per (detector, file):
    fixed   every feature at its current value: the program must reproduce the booster's score (encoding check)
    free    every feature anywhere: the naive budget-free bound (evasion expected, found fast)
    directions  the feature directions (default M_full) of `scripts/a_directions.py --extractor sums` (fixed / up-only /
            down-only / both): the hardest feature-level region A'1 would use. On the C4 M_full detectors the minimum
            must equal the clean score (they are monotone in these directions), a second encoding check.
With `--decide`, the free and directions regions solve the decision version instead (can the score go below the threshold?),
which is what Table A'1 needs: an evading vector ends the search, and only "no" needs a proof.
The solver is HiGHS through `scipy.optimize.milp` (single-threaded per instance); instances run in parallel.

Outputs, in `{outdir}/`:
    solves.parquet   one row per (defense, file, region): status, seconds, clean and best raw score, dual bound,
                     threshold, evaded, certified, gap, nodes, problem size
    report.json      per (defense, region): instances, solved to optimality, median and max seconds, evaded,
                     certified, encoding-check failures

Usage (smoke on one file, 60 s limit):
    PYTHONHASHSEED=0 python scripts/ap_check0_solver.py --outdir /tmp/ap0 --num_malware 1 --time_limit 60 \
        --defense ref=artifacts/models/gbdt/seed-0-s10-ref
"""

from __future__ import annotations

from argparse import ArgumentParser
from collections import defaultdict
import json
import multiprocessing
from pathlib import Path
import sys
import time
from typing import Any
from typing import Optional

import lightgbm
import numpy as np
from scipy.optimize import LinearConstraint
from scipy.optimize import milp
from scipy.sparse import coo_matrix

from provexp.featuresets.ember2024.sums import SumsFeatureExtractor

sys.path.insert(0, str(Path(__file__).parent))
from a1_adaptive import _parse_defenses  # noqa: E402
from a1_adaptive import _threshold  # noqa: E402
from a_pv_attacks import load_pilot  # noqa: E402

__all__ = [
    "Ensemble",
    "forced_box",
    "load_directions",
    "solve",
    "main",
]

ROOT = Path(__file__).resolve().parents[1]
REGIONS = ("fixed", "free", "directions")
# NOTE: scores within this of each other count as equal (float32 features vs float64 thresholds, solver tolerance).
TOL = 1e-6


################################################################################
# The ensemble as a mixed-integer program
################################################################################


class Ensemble:
    """
    A LightGBM GBDT flattened for Kantchelian et al.'s encoding.

    Attributes:
        thresholds: per used feature, its sorted distinct split thresholds.
        var: (feature, threshold index) -> index of the binary "x_feature <= threshold".
        nodes: per tree, a list of (feature, threshold index, left leaves, right leaves).
        leaves: per tree, the global indices of its leaf weights.
        values: leaf values, indexed like the leaf weights.
    """

    def __init__(self, booster: lightgbm.Booster) -> None:
        dump = booster.dump_model()
        splits: dict[int, set[float]] = defaultdict(set)
        trees = [t["tree_structure"] for t in dump["tree_info"]]
        for root in trees:
            stack = [root]
            while stack:
                n = stack.pop()
                if "split_feature" not in n:
                    continue
                if n["decision_type"] != "<=":
                    raise ValueError(f"Unsupported split type {n['decision_type']!r}.")
                if n.get("missing_type", "None") != "None":
                    raise ValueError(f"Unsupported missing-value handling {n['missing_type']!r}.")
                splits[n["split_feature"]].add(float(n["threshold"]))
                stack += [n["left_child"], n["right_child"]]
        self.thresholds: dict[int, np.ndarray] = {f: np.array(sorted(ts)) for f, ts in sorted(splits.items())}
        self.var: dict[tuple[int, int], int] = {}
        for f, ts in self.thresholds.items():
            for j in range(ts.size):
                self.var[(f, j)] = len(self.var)
        self.nodes: list[list[tuple[int, int, list[int], list[int]]]] = []
        self.leaves: list[list[int]] = []
        values: list[float] = []
        for root in trees:
            nodes: list[tuple[int, int, list[int], list[int]]] = []

            def walk(n: dict[str, Any]) -> list[int]:
                if "split_feature" not in n:
                    values.append(float(n["leaf_value"]))
                    return [len(values) - 1]
                left, right = walk(n["left_child"]), walk(n["right_child"])
                f = int(n["split_feature"])
                j = int(np.searchsorted(self.thresholds[f], float(n["threshold"])))
                nodes.append((f, j, left, right))
                return left + right

            self.leaves.append(walk(root))
            self.nodes.append(nodes)
        self.values = np.array(values)

    @property
    def num_binaries(self) -> int:
        return len(self.var)


def forced(ens: Ensemble, x: np.ndarray, direction: dict[int, str]) -> tuple[np.ndarray, np.ndarray]:
    """
    Bounds on each binary "x_f <= t_j" for a region given per feature as fixed / up / down / both.

    Args:
        ens: the flattened ensemble.
        x: the file's current feature vector.
        direction: feature index -> "fixed", "up", "down", or "both" (absent means "both").

    Returns:
        (lower, upper) bounds for the binaries.
    """
    lo, hi = np.zeros(ens.num_binaries), np.ones(ens.num_binaries)
    for f, ts in ens.thresholds.items():
        d = direction.get(f, "both")
        if d == "both":
            continue
        below = float(x[f]) <= ts  # the current value lies at or below each threshold
        idx = np.array([ens.var[(f, j)] for j in range(ts.size)])
        if d == "fixed":
            lo[idx], hi[idx] = below, below
        elif d == "up":  # x' >= x: thresholds below x stay false
            hi[idx[~below]] = 0.0
        elif d == "down":  # x' <= x: thresholds at or above x stay true
            lo[idx[below]] = 1.0
        else:
            raise ValueError(f"Unknown direction {d!r} for feature {f}.")
    return lo, hi


def forced_box(ens: Ensemble, low: np.ndarray, high: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Bounds on each binary "x_f <= t_j" for a region given per feature as an interval [low_f, high_f].

    Args:
        ens: the flattened ensemble.
        low: per feature, the lowest value allowed.
        high: per feature, the highest value allowed.

    Returns:
        (lower, upper) bounds for the binaries.
    """
    if np.any(low > high):
        raise ValueError(f"Empty interval for features {np.flatnonzero(low > high)[:5].tolist()}.")
    lo, hi = np.zeros(ens.num_binaries), np.ones(ens.num_binaries)
    for f, ts in ens.thresholds.items():
        idx = np.array([ens.var[(f, j)] for j in range(ts.size)])
        lo[idx[float(high[f]) <= ts]] = 1.0  # every allowed value lies at or below the threshold
        hi[idx[float(low[f]) > ts]] = 0.0  # every allowed value lies above it
    return lo, hi


def solve(ens: Ensemble, x: np.ndarray, direction: dict[int, str], time_limit: float,
          below: Optional[float] = None, max_changed: Optional[int] = None,
          box: Optional[tuple[np.ndarray, np.ndarray]] = None) -> dict[str, Any]:
    """
    Minimize the ensemble's raw score over a region, or (with `below`) decide whether it can go below a value.

    Args:
        ens: the flattened ensemble.
        x: the file's current feature vector.
        direction: the region (see `forced`).
        time_limit: seconds for the solver.
        below: if given, solve the decision version instead: is there a vector in the region scoring below this?
            The objective is then zero, so the first such vector ends the search; infeasibility is a certificate.
        max_changed: if given, at most this many features may leave their current split interval (an L0 budget,
            Kantchelian et al.'s; one indicator per feature).
        box: if given, the region is this (low, high) interval per feature instead of `direction`; it must contain x.

    Returns:
        status, seconds, best (lowest score found; in the decision version, the found vector's score),
        dual_bound (proved lower bound; in the decision version, `below` if proved infeasible), gap, nodes, size.
    """
    nb, nl = ens.num_binaries, ens.values.size
    blo, bhi = forced(ens, x, direction) if box is None else forced_box(ens, *box)
    current = np.zeros(nb)
    for f, ts in ens.thresholds.items():
        for j in range(ts.size):
            current[ens.var[(f, j)]] = float(float(x[f]) <= ts[j])
    movable = [f for f, ts in ens.thresholds.items() if any(blo[ens.var[(f, j)]] < bhi[ens.var[(f, j)]]
                                                             for j in range(ts.size))]
    nz = len(movable) if max_changed is not None else 0
    rows: list[int] = []
    cols: list[int] = []
    vals: list[float] = []
    lb: list[float] = []
    ub: list[float] = []

    def row(entries: list[tuple[int, float]], low: float, high: float) -> None:
        r = len(lb)
        for c, v in entries:
            rows.append(r)
            cols.append(c)
            vals.append(v)
        lb.append(low)
        ub.append(high)

    # Order: x <= t_j implies x <= t_{j+1}.
    for f, ts in ens.thresholds.items():
        for j in range(ts.size - 1):
            row([(ens.var[(f, j)], 1.0), (ens.var[(f, j + 1)], -1.0)], -np.inf, 0.0)
    # Each tree selects one leaf, on the side of every split its binaries choose.
    for leaves, nodes in zip(ens.leaves, ens.nodes):
        row([(nb + leaf, 1.0) for leaf in leaves], 1.0, 1.0)
        for f, j, left, right in nodes:
            p = ens.var[(f, j)]
            row([(nb + leaf, 1.0) for leaf in left] + [(p, -1.0)], -np.inf, 0.0)
            row([(nb + leaf, 1.0) for leaf in right] + [(p, 1.0)], -np.inf, 1.0)
    if below is not None:
        row([(nb + i, float(v)) for i, v in enumerate(ens.values)], -np.inf, below)
    if max_changed is not None:
        # A binary may leave its current value only if its feature's indicator is on.
        for k, f in enumerate(movable):
            z = nb + nl + k
            for j in range(ens.thresholds[f].size):
                v = ens.var[(f, j)]
                if blo[v] < bhi[v]:
                    row([(v, 1.0), (z, -1.0)], -np.inf, current[v])
                    row([(v, 1.0), (z, 1.0)], current[v], np.inf)
        row([(nb + nl + k, 1.0) for k in range(nz)], -np.inf, float(max_changed))
    a = coo_matrix((vals, (rows, cols)), shape=(len(lb), nb + nl + nz)).tocsr()
    lower = np.concatenate([blo, np.zeros(nl), np.zeros(nz)])
    upper = np.concatenate([bhi, np.ones(nl), np.ones(nz)])
    c = np.concatenate([np.zeros(nb), ens.values if below is None else np.zeros(nl), np.zeros(nz)])
    integrality = np.concatenate([np.ones(nb), np.zeros(nl), np.ones(nz)])

    t0 = time.time()
    res = milp(c, integrality=integrality, bounds=(lower, upper), constraints=LinearConstraint(a, lb, ub),
               options={"time_limit": time_limit, "disp": False})
    seconds = time.time() - t0
    best: Optional[float] = float(ens.values @ res.x[nb:nb + nl]) if res.x is not None else None
    dual = getattr(res, "mip_dual_bound", None)
    if below is not None:
        dual = below if res.status == 2 else None  # 2: proved infeasible
    return {
        "status": int(res.status), "message": str(res.message), "seconds": seconds, "best": best,
        "dual_bound": None if dual is None else float(dual), "gap": getattr(res, "mip_gap", None),
        "nodes": getattr(res, "mip_node_count", None), "binaries": nb, "leaves": nl, "rows": len(lb),
        "free_binaries": int((blo < bhi).sum()),
    }


def load_directions(path: Path, names: list[str]) -> dict[int, str]:
    """Per feature index, its direction from a_directions' `{tm}.monotone.tsv` / `{tm}.neutralize.txt` pair."""
    index = {n: i for i, n in enumerate(names)}
    out = {i: "fixed" for i in range(len(names))}
    for line in path.with_suffix(".neutralize.txt").read_text().splitlines():
        if line:
            out[index[line]] = "both"
    for line in path.with_suffix(".monotone.tsv").read_text().splitlines():
        if line:
            name, sign = line.split("\t")
            out[index[name]] = "up" if int(sign) > 0 else "down"
    return out


################################################################################
# Main
################################################################################


_ENSEMBLES: dict[str, Ensemble] = {}
_MFULL: dict[int, str] = {}
_DECIDE: list[bool] = [False]
_MAX_CHANGED: list[Optional[int]] = [None]


def _job(job: tuple[str, str, str, np.ndarray, float, float, float]) -> dict[str, Any]:
    defense, name, region, x, clean, tau_raw, time_limit = job
    direction = {"fixed": {i: "fixed" for i in range(x.size)}, "free": {}, "directions": _MFULL}[region]
    decide = _DECIDE[0] and region != "fixed"
    r = solve(_ENSEMBLES[defense], x, direction, time_limit, below=tau_raw - TOL if decide else None,
              max_changed=_MAX_CHANGED[0] if region != "fixed" else None)
    r.update(defense=defense, name=name, region=region, clean=clean, tau_raw=tau_raw, decide=decide)
    r["evaded"] = r["best"] is not None and r["best"] < tau_raw - TOL
    r["certified"] = r["dual_bound"] is not None and r["dual_bound"] >= tau_raw - TOL
    if region == "fixed":
        r["encoding_ok"] = r["best"] is not None and abs(r["best"] - clean) <= 1e-4 * max(1.0, abs(clean))
    print(f"  {defense} {name[:12]} {region}: {r['message'][:40]!r} {r['seconds']:.0f}s best={r['best']} "
          f"bound={r['dual_bound']} clean={clean:.3f} tau={tau_raw:.3f}", flush=True)
    return r


def main() -> None:
    import polars as pl

    parser = ArgumentParser(description=__doc__.split("\n\n")[1] if __doc__ else None)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--defense", action="append", required=True, help="name=model_dir (repeatable).")
    parser.add_argument("--sound", nargs="*", default=[], help="Defenses monotone in the M_full directions.")
    parser.add_argument("--directions", type=Path, default=ROOT / "artifacts/experiments/a_directions_sums/M_full",
                        help="Prefix of the direction files (sums extractor), e.g. .../M_add.")
    parser.add_argument("--regions", nargs="+", choices=REGIONS, default=list(REGIONS))
    parser.add_argument("--pilot_files", type=Path, default=ROOT / "artifacts/experiments/e1/seed-0/zeros/files.parquet")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--num_malware", type=int, default=5)
    parser.add_argument("--fpr", type=float, default=0.01)
    parser.add_argument("--time_limit", type=float, default=1800.0, help="Seconds per solve.")
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--decide", action="store_true", help="Solve the decision version (can the score go below "
                        "the threshold?) instead of minimizing.")
    parser.add_argument("--max_changed", type=int, default=None, help="At most this many features may move (L0 "
                        "budget): a stand-in for a tight region, to time proofs that no evasion exists.")
    args = parser.parse_args()

    _DECIDE[0] = args.decide
    _MAX_CHANGED[0] = args.max_changed
    extractor = SumsFeatureExtractor()
    _MFULL.update(load_directions(args.directions, extractor.feature_names))
    defenses = _parse_defenses(args.defense)
    malware, _ = load_pilot(args.pilot_files, args.db)
    cache: dict[str, np.ndarray] = {}

    def vector(name: str, data: bytes) -> np.ndarray:
        if name not in cache:
            cache[name] = extractor.feature_vector(data).astype(np.float64)  # type: ignore[no-untyped-call]
        return cache[name]

    jobs: list[tuple[str, str, str, np.ndarray, float, float, float]] = []
    for d, mdir in defenses.items():
        booster = lightgbm.Booster(model_file=str(mdir / "model.txt"))
        if booster.num_feature() != extractor.dim:
            raise RuntimeError(f"{d}: model has {booster.num_feature()} features, the sums extractor {extractor.dim}.")
        _ENSEMBLES[d] = Ensemble(booster)
        tau = _threshold(mdir / "ts_predictions.parquet", args.fpr)
        tau_raw = float(np.log(tau / (1.0 - tau)))
        chosen = 0
        for name, data in malware:
            x = vector(name, data)
            clean = float(booster.predict(x.reshape(1, -1).astype(np.float32), raw_score=True)[0])
            if clean <= tau_raw:
                continue  # evaluate only what this defense detects
            jobs += [(d, name, region, x, clean, tau_raw, args.time_limit) for region in args.regions]
            chosen += 1
            if chosen == args.num_malware:
                break
        ens = _ENSEMBLES[d]
        print(f"{d}: {len(ens.leaves)} trees, {ens.values.size} leaves, {ens.num_binaries} binaries; "
              f"tau={tau:.4f}; {chosen} files", flush=True)

    # NOTE: fork, so the workers inherit the flattened ensembles (Python 3.14 defaults to forkserver).
    with multiprocessing.get_context("fork").Pool(args.workers) as pool:
        rows = pool.map(_job, jobs, chunksize=1)

    out = pl.DataFrame(rows)
    args.outdir.mkdir(parents=True, exist_ok=True)
    out.write_parquet(args.outdir / "solves.parquet")
    report: dict[str, Any] = {"time_limit": args.time_limit, "fpr": args.fpr, "decide": args.decide,
                              "directions": args.directions.as_posix(),
                              "max_changed": args.max_changed, "groups": {}}
    for (d, region), g in out.group_by(["defense", "region"], maintain_order=True):
        entry: dict[str, Any] = {
            "instances": g.height,
            "optimal": int((g["status"] == 0).sum()),
            "median_seconds": float(g["seconds"].median()),  # type: ignore[arg-type]
            "max_seconds": float(g["seconds"].max()),  # type: ignore[arg-type]
            "evaded": int(g["evaded"].sum()),
            "certified": int(g["certified"].sum()),
        }
        if region == "fixed":
            entry["encoding_failures"] = int((~g["encoding_ok"]).sum())
        if region == "directions" and d in args.sound:
            # A monotone detector cannot go below its clean score in its own directions.
            below = g.filter(pl.col("best").is_not_null() & (pl.col("best") < pl.col("clean") - 1e-4))
            entry["soundness_violations"] = below.height
        report["groups"][f"{d}/{region}"] = entry
    (args.outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
