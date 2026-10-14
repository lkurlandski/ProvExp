"""
CM, triage tied to a decision (docs/experiments/cm.md, "Triage tied to a decision"; revision plan B9).

Does the disagreement triage (A = GBDT, B = MalConv) tell an *attack-caused* disagreement from an *organic* one? We
build two populations of GBDT-only-flagged malware and run the same blind/oppose/agree split on each:

    organic   malware the GBDT detects and MalConv misses on its own (no modification).
    evasion   malware both detect, with the shared set S (the top bytes both rely on; cm_shared) scrambled loader-safe,
              kept only where MalConv then drops to/below its 1%-FPR threshold while the GBDT stays above its own. The
              disagreement is caused by an attack on the reliance both detectors share.

For each file: e_g is the pullback of interventional TreeSHAP, e_m is MalConv's Integrated Gradients, both recomputed
on the file the triage sees (the modified bytes for the evasion population). The split takes A's (the GBDT's) top q_A
of the ablatable bytes by evidence for malware and labels each by how B (MalConv) reads it: blind (outside B's top q_B
by |evidence|), oppose (attended, against malware), agree (attended, for malware). The hypothesis is that the evasion
population carries more of its evidence in oppose than the organic one, because the attack changed bytes both rely on,
which the GBDT still reads as malware and MalConv now reads as benign.

Single process, one GPU (IG is recomputed per kept file). Candidates: the test malware of the explanation set.

Outputs, in `{outdir}/seed-{seed}/`:
    files.parquet   one row per candidate malware: population, both log-odds before and after, |S|, whether it evaded,
                    and, for the two populations the triage runs on, the blind/oppose/agree shares of A's evidence
    report.json     the configuration, thresholds, counts, and timing

Usage:
    PYTHONHASHSEED=0 OMP_NUM_THREADS=1 python scripts/cm_triage_evasion.py --seed 0 --device cuda:3
"""

from __future__ import annotations

from argparse import ArgumentParser
import json
from pathlib import Path
import sys
import time
from typing import Any

import lightgbm as lgb
import numpy as np
import numpy.typing as npt
import polars as pl
import torch
from tqdm import tqdm

from provexp.ablation import ablate
from provexp.data.tabular import load_features
from provexp.explain.feature import gbdt_function
from provexp.explain.feature import treeshap_interventional
from provexp.featuresets.ember2024.ablation import protect
from provexp.featuresets.ember2024.ablation import verify
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.models.malconv import MalConv
from provexp.models.malconv import encode
from provexp.models.malconv import load_pretrained_malconv

sys.path.insert(0, str(Path(__file__).parent))

from cm_check import malconv_explanations  # noqa: E402
from cm_shared import split_sets  # noqa: E402
from cm_triage import categories  # noqa: E402
from faithfulness import load_sample  # noqa: E402

FloatArray = npt.NDArray[np.float64]
BoolArray = npt.NDArray[np.bool_]

ROOT = Path(__file__).parent.parent
IS_PE = 2  # The index of general:is_pe.
Q_A = 0.01  # A's top fraction of the ablatable bytes, as in cm_triage.
Q_B = 0.05  # B's attended fraction.


def malconv_log_odds(model: MalConv, data: bytes, device: str) -> float:
    """MalConv's malware log-odds for one file, with the input on the model's device."""
    with torch.no_grad():
        z = model(encode(data)[None].to(device))
    return float(z[0, 1] - z[0, 0])


def evidence_shares(e_a: FloatArray, e_b: FloatArray, ablatable: BoolArray, perm: npt.NDArray[np.int64]) -> dict[str, float]:
    """A's positive evidence in each category as a share of its positive evidence in the top set (as in cm_triage)."""
    top, cats = categories(e_a, e_b, ablatable, Q_A, Q_B, perm)
    pos = e_a * (e_a > 0)
    total = float(pos[top].sum())
    if total <= 0:
        return {"blind": float("nan"), "oppose": float("nan"), "agree": float("nan")}
    return {name: float(pos[mask].sum()) / total for name, mask in cats.items()}


def main() -> None:
    parser = ArgumentParser(description="CM triage tied to a decision: organic vs. shared-reliance-evasion disagreements.")
    parser.add_argument("--seed", type=int, default=0, help="The seed of the GBDT and of MalConv.")
    parser.add_argument("--selection", type=Path, default=ROOT / "artifacts" / "explanation_set" / "ts.parquet")
    parser.add_argument("--thresholds", type=Path, default=None, help="Default: the disagreement selection's thresholds JSON.")
    parser.add_argument("--num_files", type=int, default=0, help="Cap on candidate malware (0: all), for smoke tests.")
    parser.add_argument("--q", type=float, default=0.01, help="The fraction q defining each model's top set S = T_g ∩ T_m.")
    parser.add_argument("--ig_steps", type=int, default=256)
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--background", type=Path, default=ROOT / "artifacts" / "explanations" / "ember2024" / "background.parquet")
    parser.add_argument("--models", type=Path, default=ROOT / "artifacts" / "models")
    parser.add_argument("--checkpoints", type=Path, default=ROOT / "checkpoints")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "cm_triage_evasion")
    args = parser.parse_args()

    thresholds_file = args.thresholds or args.selection.parent / f"ts-disagreement-seed{args.seed}.json"
    thresholds: dict[str, float] = json.loads(thresholds_file.read_text())["thresholds"]
    t_gbdt, t_malconv = thresholds["gbdt"], thresholds["malconv"]

    extractor = PEFeatureExtractor()
    booster = lgb.Booster(model_file=str(args.models / "gbdt" / f"seed-{args.seed}" / "model.txt"))
    gbdt = gbdt_function(booster)
    malconv = load_pretrained_malconv(args.checkpoints / f"malconv-seed{args.seed}.pt").to(args.device).eval()

    X_tr, _ = load_features(args.features, "tr")
    bg_rows = pl.read_parquet(args.background)["row"].to_numpy()
    background = np.asarray(X_tr[bg_rows], dtype=np.float64)

    samples = pl.read_parquet(args.selection).filter(pl.col("label") == 1).sort("row")
    if args.num_files:
        samples = samples.head(args.num_files)

    def explain(data: bytes) -> tuple[FloatArray, FloatArray, float, float]:
        """e_g (pullback of TreeSHAP), e_m (MalConv IG), and both log-odds for one file."""
        x, prov = extractor.feature_vector_with_provenance(data)
        x = np.asarray(x, dtype=np.float64)
        g = float(gbdt(x[None, :])[0])
        a = treeshap_interventional(booster, x[None, :], background)[0]
        e_g = prov.pullback(a)[: len(data)]
        m_log, ig, _ = malconv_explanations(malconv, data, args.ig_steps, args.device)
        return e_g, ig.astype(np.float64), g, m_log

    rows: list[dict[str, Any]] = []
    t_0 = time.perf_counter()
    for r in tqdm(samples.iter_rows(named=True), total=samples.height, desc="candidates"):
        try:
            data = load_sample(int(r["shard"]), int(r["position"]), r["name"], args.db)
        except Exception as err:
            rows.append({"name": r["name"], "population": "load_error", "error": str(err)[:200]})
            continue
        m = len(data)
        e_g0, e_m0, g0, m0 = explain(data)
        base = {"name": r["name"], "size": m, "gbdt_log_odds": g0, "malconv_log_odds": m0}
        if g0 <= t_gbdt:
            rows.append(base | {"population": "gbdt_misses"})
            continue
        protection = protect(data, header="typical")
        ablatable = ~protection.mask
        perm = np.random.default_rng([args.seed, 1, int(r["row"])]).permutation(m).astype(np.int64)

        if m0 <= t_malconv:
            # Organic GBDT-only malware: run the triage on the file as it is.
            shares = evidence_shares(e_g0, e_m0, ablatable, perm)
            rows.append(base | {"population": "organic", "shared": 0} | shares)
            continue

        # Both detect: scramble the shared set S loader-safe, keep if MalConv flips and the GBDT holds.
        _, _, S = split_sets(e_g0, e_m0, ablatable, args.q, perm)
        n = int(S.sum())
        row = base | {"population": "both_detect", "shared": n}
        if n == 0:
            rows.append(row)
            continue
        fill_rng = np.random.default_rng([args.seed, 2, int(r["row"])])
        z = ablate(data, S, protection.mask, "zeros", fill_rng, protection.header, protection.header_values)
        try:
            xz = np.asarray(extractor.feature_vector(z), dtype=np.float64)  # type: ignore[no-untyped-call]
            ok = verify(protection, data, z, float(xz[IS_PE])) is None
            gz = float(gbdt(xz[None, :])[0]) if ok else float("nan")
        except Exception:
            ok, gz = False, float("nan")
        mz = malconv_log_odds(malconv, z, args.device)
        evaded = bool(ok and mz <= t_malconv and gz > t_gbdt)
        row |= {"valid": ok, "gbdt_evaded": gz, "malconv_evaded": mz, "evaded": evaded}
        if evaded:
            # Re-explain the modified file and run the triage on what the detectors now see.
            e_gz, e_mz, _, _ = explain(z)
            shares = evidence_shares(e_gz, e_mz, ablatable, perm)
            row |= {"population": "evasion"} | shares
        rows.append(row)

    files = pl.DataFrame(rows, infer_schema_length=None)
    outdir = args.outdir / f"seed-{args.seed}"
    outdir.mkdir(parents=True, exist_ok=True)
    files.write_parquet(outdir / "files.parquet")

    # Summary: the blind/oppose/agree shares for each population the triage ran on.
    print("\n## Triage split by population (mean share of A's evidence; p-value: evasion vs. organic, Mann-Whitney)\n")
    print("| population | files | blind | oppose | agree |")
    print("|---|---|---|---|---|")
    pops: dict[str, dict[str, FloatArray]] = {}
    for pop in ("organic", "evasion"):
        f = files.filter((pl.col("population") == pop) & pl.col("oppose").is_not_null()) if "population" in files.columns else files.head(0)
        if f.height == 0:
            continue
        cols = {c: f[c].drop_nulls().to_numpy() for c in ("blind", "oppose", "agree")}
        pops[pop] = cols
        print(f"| {pop} | {f.height} | " + " | ".join(f"{cols[c].mean():.2f}" for c in ("blind", "oppose", "agree")) + " |")
    if {"organic", "evasion"} <= set(pops):
        from scipy.stats import mannwhitneyu

        ps = {c: mannwhitneyu(pops["evasion"][c], pops["organic"][c]).pvalue for c in ("blind", "oppose", "agree")}
        print("\n" + "p (evasion vs. organic): " + ", ".join(f"{c} {ps[c]:.1e}" for c in ("blind", "oppose", "agree")))

    counts = {pop: int((files["population"] == pop).sum()) for pop in files["population"].unique().to_list()} if "population" in files.columns else {}
    report = {
        "seed": args.seed, "q": args.q, "ig_steps": args.ig_steps, "thresholds": thresholds,
        "candidates": samples.height, "populations": counts, "minutes": (time.perf_counter() - t_0) / 60,
    }
    (outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(f"\nWrote {outdir}. Populations: {counts}. {report['minutes']:.1f} min.")


if __name__ == "__main__":
    main()
