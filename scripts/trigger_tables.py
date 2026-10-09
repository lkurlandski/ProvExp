"""
The planted-trigger metrics (PB2 and PF2; docs/trigger_plan.md) from scripts/trigger_explain.py's outputs.

The trigger's bytes T are the ground truth. For every explained file we build the provenance of the *triggered* file
and work with the explanation's change, delta a = a(triggered) - a(clean), which is what the trigger caused.

PB2 (does the pullback land on the trigger's bytes?), per file and explainer:
    mass on T           the share of |P delta a| that falls on T, including the null element in the total
    precision at |T|    the share of T among the |T| top-ranked bytes
    null share          the share of |P delta a| on the null element, which no byte can carry
and reference points:
    random              |T| / m, what an arbitrary ranking achieves
    round trip          the same measured on P r, where r is the pushforward of T (below): the push-pull round trip
                        of the trigger. Not an upper bound (it was called the "ceiling" until 2026-10-09): r weights
                        every touched feature by provenance, while an explanation may credit only the sharpest ones
    bound               the most any nonnegative feature-space explanation can place on T: the largest column share
                        on T of any feature, max_j (P^T 1_T)_j (1 when some feature is computed from T alone)
    window bound        |T| / (window size), the most any method that scores whole windows of bytes can achieve;
                        stated analytically, since running occlusion for a 6-byte trigger would cost hours per file

PF2 (does the pushforward give feature-space explainers a ground truth?), per file and explainer. r = psi(1_T) is
read as a *support*, not a target (decided 2026-10-09; docs/trigger_plan.md): its weights say how much of each
feature the trigger computes, a property of P, not which features the model uses; its support, the features the
trigger touches, is a ground truth that does not depend on the model.
    mass on supp(r)     the share of |delta a| on the support (recall-like; even an ideal explainer of a tree model
                        stays below 1, because interactions move credit onto untouched features)
    top-1, top-10       whether the top feature is in the support, and the share of the top 10 that are
    random              |supp(r)| / n, a random attribution's expected mass and top-k share

Usage:
    PYTHONHASHSEED=0 python scripts/trigger_tables.py --poison artifacts/poison/struct --num_workers 8
"""

from argparse import ArgumentParser
import json
import multiprocessing as mp
import os
from pathlib import Path
import sys
from typing import Any
from typing import Optional
import warnings

import numpy as np
from numpy import typing as npt
import polars as pl
from tqdm import tqdm

from provexp.ablation import element_order
from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBIterator
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.featuresets.ember2024.trigger import apply_content
from provexp.featuresets.ember2024.trigger import apply_struct
from provexp.featuresets.ember2024.trigger import content_block
from provexp.featuresets.ember2024.trigger import struct_trigger


ROOT = Path(__file__).parent.parent
WINDOW_COUNTS = (256, 4096)

_EXTRACTOR: Optional[PEFeatureExtractor] = None
_BLOCK: Optional[bytes] = None


def _init_worker(block: Optional[bytes]) -> None:
    global _EXTRACTOR, _BLOCK
    _EXTRACTOR = PEFeatureExtractor()
    _BLOCK = block
    sys.stdout = open(os.devnull, "w")
    warnings.filterwarnings("ignore")


def mass_on(values: npt.NDArray[np.float64], inside: npt.NDArray[np.bool_]) -> float:
    """The share of a problem-space explanation's magnitude that falls inside a set of elements."""
    total = float(np.abs(values).sum())
    return float(np.abs(values[:inside.shape[0]][inside]).sum() / total) if total > 0 else float("nan")


def precision_at(values: npt.NDArray[np.float64], inside: npt.NDArray[np.bool_], direction: float, tiebreak: npt.NDArray[np.int64]) -> float:
    """The share of the trigger's elements among the |T| highest-ranked ones, ties broken by `tiebreak`, not position."""
    n = int(inside.sum())
    if n == 0:
        return float("nan")
    top = element_order(values[:inside.shape[0]], direction, tiebreak)[:n]
    return float(inside[top].mean())


def process_shard(shard: int, rows: list[dict[str, Any]], dbdir: Path, explanations: dict[str, npt.NDArray[np.float64]]) -> list[dict[str, Any]]:
    """The PB2 and PF2 metrics of the selected files of one shard."""
    assert _EXTRACTOR is not None
    wanted = {r["position"]: i for i, r in enumerate(rows)}
    out: list[dict[str, Any]] = []
    for position, sample in enumerate(SimpleDBIterator(SimpleDB(dbdir, check=False)).iter(shard)):
        if position not in wanted:
            continue
        i = wanted[position]
        row = rows[i]
        t = apply_struct(sample.data, struct_trigger()) if _BLOCK is None else apply_content(sample.data, _BLOCK)
        _, prov = _EXTRACTOR.feature_vector_with_provenance(t.data)
        m = prov.num_elements
        inside = np.zeros(m, dtype=np.bool_)
        for lo, hi in zip(row["trigger_lo"], row["trigger_hi"]):
            inside[lo:hi] = True
        # The reference answer: the pushforward of a uniform explanation on the trigger's bytes.
        one_T = np.zeros(prov.num_rows)
        one_T[:m][inside] = 1.0 / max(int(inside.sum()), 1)
        r = prov.pushforward(one_T)
        # Ties (e.g., bytes with identical provenance) are broken by a seeded permutation, never by position, which
        # would favor the trigger at the end of the file or penalize it.
        tiebreak = np.random.default_rng(int(row["index"])).permutation(m).astype(np.int64)
        support = r > 0
        # The direction of the decision the trigger causes, so that "top-ranked" means "most responsible".
        direction = float(np.sign(row["log_odds_triggered_poisoned"] - row["log_odds_clean_poisoned"])) or 1.0
        record: dict[str, Any] = {
            "index": row["index"], "name": row["name"], "size": row["size"], "num_elements": m,
            "trigger_bytes": int(inside.sum()), "trigger_share": float(inside.mean()),
            "num_trigger_features": int(support.sum()),
            "support_share": float(support.mean()),
            "roundtrip_mass_on_T": mass_on(prov.pullback(r), inside),
            "roundtrip_precision_at_T": precision_at(prov.pullback(r), inside, 1.0, tiebreak),
            "bound_mass_on_T": float(prov.rmatvec(np.append(inside, False).astype(np.float64)
                                                  if prov.has_null else inside.astype(np.float64)).max()),
        }
        for K in WINDOW_COUNTS:
            record[f"window_bound_k{K}"] = min(1.0, float(inside.sum()) / max(m / K, 1.0))
        for name, A in explanations.items():
            delta = A[i]
            b = prov.pullback(delta)
            record |= {
                f"mass_on_T:{name}": mass_on(b, inside),
                f"precision_at_T:{name}": precision_at(b, inside, direction, tiebreak),
                f"null_share:{name}": float(abs(b[-1]) / np.abs(b).sum()) if np.abs(b).sum() > 0 else float("nan"),
                f"pf_mass_on_support:{name}": float(np.abs(delta[support]).sum() / np.abs(delta).sum()) if np.abs(delta).sum() > 0 else float("nan"),
                f"pf_top1_in_support:{name}": bool(support[int(np.argmax(np.abs(delta)))]),
                f"pf_top10_in_support:{name}": float(support[np.argsort(-np.abs(delta), kind="stable")[:10]].mean()),
            }
        out.append(record)
    return out


def _star(task: tuple[Any, ...]) -> list[dict[str, Any]]:
    return process_shard(*task)


def markdown(df: pl.DataFrame, digits: int = 3) -> str:
    def fmt(v: object) -> str:
        return f"{v:.{digits}g}" if isinstance(v, float) else str(v)
    lines = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    lines += ["| " + " | ".join(fmt(v) for v in row) + " |" for row in df.iter_rows()]
    return "\n".join(lines)


def main() -> None:
    parser = ArgumentParser(description="The planted-trigger metrics (PB2, PF2).")
    parser.add_argument("--poison", type=Path, required=True)
    parser.add_argument("--which", type=str, choices=["delta", "triggered"], default="delta",
                        help="Explain the trigger's effect (a(triggered) - a(clean)) or the triggered file itself.")
    parser.add_argument("--explanation_set", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "trigger")
    parser.add_argument("--num_workers", type=int, default=8)
    args = parser.parse_args()

    if os.environ.get("PYTHONHASHSEED") != "0":
        raise RuntimeError("Run with PYTHONHASHSEED=0 so that the features match the feature store.")

    indir = args.outdir / args.poison.name / "explain"
    report = json.loads((indir / "report.json").read_text())
    config = json.loads((args.poison / "report.json").read_text())
    block = content_block(config["content"], config["block_size"], config["seed"]) if config["trigger"] == "content" else None
    files = pl.read_parquet(indir / "files.parquet")
    names = sorted({k.rsplit("_", 1)[0] for k in report["explainers"]})
    explanations = {}
    for name in names:
        triggered = np.load(indir / f"a_{name}_triggered.npy")
        explanations[name] = triggered - np.load(indir / f"a_{name}_clean.npy") if args.which == "delta" else triggered
    print(f"{args.poison.name}: {files.height} files, explainers {names}, using {args.which}.", flush=True)

    location = pl.read_parquet(args.explanation_set).select("name", "shard")
    files = files.join(location, on="name", how="left")
    rows = files.select("index", "name", "size", "shard", "position", "trigger_lo", "trigger_hi",
                        "log_odds_clean_poisoned", "log_odds_triggered_poisoned").to_dicts()
    order = {int(r["index"]): i for i, r in enumerate(rows)}
    tasks = []
    for shard in sorted({int(r["shard"]) for r in rows}):
        group = [r for r in rows if int(r["shard"]) == shard]
        idx = np.asarray([order[int(r["index"])] for r in group])
        tasks.append((shard, group, args.db, {n: A[idx] for n, A in explanations.items()}))
    records: list[dict[str, Any]] = []
    with mp.get_context("fork").Pool(min(args.num_workers, len(tasks)), initializer=_init_worker, initargs=(block,)) as pool:
        for part in tqdm(pool.imap_unordered(_star, tasks), total=len(tasks), desc="shards", mininterval=10):
            records.extend(part)
    table = pl.DataFrame(records, infer_schema_length=None).sort("index")
    outdir = args.outdir / args.poison.name
    table.write_parquet(outdir / f"metrics-{args.which}.parquet")

    def q(column: str) -> str:
        v = table[column].to_numpy().astype(np.float64)
        v = v[np.isfinite(v)]
        return " / ".join(f"{x:.3g}" for x in np.quantile(v, [0.1, 0.5, 0.9])) if v.size else "—"

    print(f"\n## The trigger (median over {table.height} files)\n")
    print(markdown(pl.DataFrame([{
        "trigger bytes": float(table["trigger_bytes"].median()),  # type: ignore[arg-type]
        "file bytes": float(table["num_elements"].median()),  # type: ignore[arg-type]
        "trigger share": float(table["trigger_share"].median()),  # type: ignore[arg-type]
        "features it touches": float(table["num_trigger_features"].median()),  # type: ignore[arg-type]
    }])), "\n")

    print("## PB2: the pullback on the trigger's bytes (10th / 50th / 90th percentile)\n")
    rows_pb = [{"method": f"pullback, {n}", "mass on T": q(f"mass_on_T:{n}"), "precision at |T|": q(f"precision_at_T:{n}"),
                "null share": q(f"null_share:{n}")} for n in names]
    rows_pb.append({"method": "bound (best single feature)", "mass on T": q("bound_mass_on_T"),
                    "precision at |T|": "—", "null share": "—"})
    rows_pb.append({"method": "round trip P psi(1_T) (not a bound)", "mass on T": q("roundtrip_mass_on_T"),
                    "precision at |T|": q("roundtrip_precision_at_T"), "null share": "—"})
    rows_pb.append({"method": "random ranking", "mass on T": q("trigger_share"), "precision at |T|": q("trigger_share"), "null share": "—"})
    for K in WINDOW_COUNTS:
        rows_pb.append({"method": f"any window-level method, K = {K}", "mass on T": "—",
                        "precision at |T|": q(f"window_bound_k{K}"), "null share": "—"})
    print(markdown(pl.DataFrame(rows_pb)), "\n")

    print("## PF2: feature-space explainers against the support of the trigger's pushforward\n")
    rows_pf = [{
        "explainer": n,
        "mass on supp(r)": q(f"pf_mass_on_support:{n}"),
        "top-1 in supp(r)": f"{int(table[f'pf_top1_in_support:{n}'].sum())}/{table.height}",
        "top-10 in supp(r)": q(f"pf_top10_in_support:{n}"),
    } for n in names]
    rows_pf.append({"explainer": "random", "mass on supp(r)": q("support_share"), "top-1 in supp(r)": "—",
                    "top-10 in supp(r)": q("support_share")})
    print(markdown(pl.DataFrame(rows_pf)), "\n")
    print(f"Wrote {outdir.as_posix()}/metrics-{args.which}.parquet.")


if __name__ == "__main__":
    main()
