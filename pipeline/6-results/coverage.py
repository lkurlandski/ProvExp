"""
§5.3, Phase 0 (docs/evidence/section-5.3-design.md, option O1): how much of what the threat model's edits can lower the toolkit
attacks lowered, split by where the gap comes from.

FOR ACADEMIC SECURITY RESEARCH ONLY. Reads stored outputs of published attacks run against our own detectors; runs
nothing.

Every feature the derived table (M_full under the precondition, quirk-fixed: the monotone rows' table) marks down or
both is lowerable. Each lowerable feature gets one class:

    toolkit_ops   some operation a toolkit attack implements (append, add a section, add imports, the two gaps,
                  header fields) can lower it, by the per-operation columns of directions.csv
    other_ops     only the other six operations (overwrite slack, the DOS header and stub, the checksum; rename; the
                  two removals) can lower it
    warnings      pefile's parser warnings: no items, the derivation leaves them free in both directions

A feature counts as lowered when some attack output's perturbation vector is below -tol on it. The sources:

    pilot         run 78's vectors on the 50 detected pilot malware (test files), with population membership from the
                  toolkit run's results (`precondition`)
    train         the attacked training malware of runs 122 and 131 (step 0), clean rows from the training split;
                  population membership computed here from the bytes (catalogue.passes_precondition)

Also: coverage as the number of attacked training files grows (seeded order), the section-name buckets gamma_sections
lowers (per file and in union), and PV's hole (hole csvs of a_pv_hole.py) split by the same classes.

With `--edits` (catalogue_checks' edits.parquet: our own byte-level edits, every one re-extracted), each lowerable
feature is also marked *witnessed* if one of our edits on a file in the population lowered it, with the operations that
did. The witnessed set is a lower bound on what the threat model can lower, independent of how tight the derived table
is; the gap that matters is what we witnessed and the toolkit never lowered.

Outputs, in `{outdir}/`: report.json, features.csv (one row per lowerable feature: class, and per source the attacks
that lowered it).

Usage:
    PYTHONHASHSEED=0 python pipeline/6-results/coverage.py --outdir artifacts/experiments/a_coverage --num_workers 16
"""

from __future__ import annotations

from argparse import ArgumentParser
import json
from pathlib import Path
from typing import Any

import numpy as np
from numpy import typing as npt
import polars as pl

from provexp.attacks.toolkit import ATTACKS
from provexp.attacks.toolkit import adv_deltas
from provexp.data.paths import EMBER2024_DATA
from provexp.data.paths import ROOT
from provexp.featuresets.ember2024.population import population

__all__ = ["TOOLKIT_OPS", "OTHER_OPS", "classify", "lowered"]

TOOLKIT_OPS = ("op_app_pre", "op_sec", "op_imp", "op_ext", "op_shf", "op_hdr")
OTHER_OPS = ("op_slk", "op_dos", "op_chk", "op_ren", "op_rdb", "op_rsg")
CLASSES = ("toolkit_ops", "other_ops", "warnings")
BUCKET_GROUPS = ("section:size_hash_", "section:entropy_hash_", "section:vsize_hash_", "section:characteristics_hash_")


################################################################################
# The lowerable features and their classes
################################################################################

def lowerable(directions_dir: Path, stem: str) -> dict[str, str]:
    """The features a monotone row of `stem` drops (both) or constrains downward (down), mapped to their direction."""
    out = {line.strip(): "both" for line in (directions_dir / f"{stem}.neutralize.txt").read_text().splitlines()
           if line.strip()}
    for line in (directions_dir / f"{stem}.monotone.tsv").read_text().splitlines():
        if line.strip():
            name, sign = line.split("\t")
            if int(sign) < 0:
                out[name] = "down"
    return out


def classify(directions_dir: Path, stem: str) -> pl.DataFrame:
    """One row per lowerable feature: name, group, direction, class, and the operations that can lower it."""
    table = pl.read_csv(directions_dir / "directions.csv", infer_schema_length=0)
    table = table.with_columns((pl.col("group") + ":" + pl.col("name")).alias("feature"))
    low = lowerable(directions_dir, stem)
    rows: list[dict[str, Any]] = []
    for r in table.filter(pl.col("feature").is_in(list(low))).iter_rows(named=True):
        ops = [c for c in TOOLKIT_OPS + OTHER_OPS if r[c] is not None and "-" in r[c]]
        if r["group"] == "pefilewarnings":
            cls = "warnings"
        elif any(c in TOOLKIT_OPS for c in ops):
            cls = "toolkit_ops"
        elif ops:
            cls = "other_ops"
        else:
            cls = "unattributed"
        rows.append({"feature": r["feature"], "group": r["group"], "direction": low[r["feature"]], "class": cls,
                     "lowering_ops": " ".join(c.removeprefix("op_").removesuffix("_pre") for c in ops)})
    missing = set(low) - {r["feature"] for r in rows}
    if missing:
        raise RuntimeError(f"{len(missing)} lowerable features are not in directions.csv: {sorted(missing)[:5]}")
    return pl.DataFrame(rows)


################################################################################
# Coverage
################################################################################

def lowered(deltas: npt.NDArray[np.float32], tol: float) -> npt.NDArray[np.bool_]:
    """Per feature, whether any perturbation vector lowers it by more than tol."""
    out: npt.NDArray[np.bool_] = (deltas < -tol).any(axis=0) if deltas.shape[0] else np.zeros(deltas.shape[1], bool)
    return out


def by_class(feats: pl.DataFrame, hit: dict[str, bool]) -> dict[str, dict[str, Any]]:
    """Coverage per class (and in all): lowerable, lowered, share."""
    out: dict[str, dict[str, Any]] = {}
    for cls in CLASSES + ("all",):
        sub = feats if cls == "all" else feats.filter(pl.col("class") == cls)
        n = sub.height
        k = sum(hit.get(f, False) for f in sub["feature"].to_list())
        out[cls] = {"lowerable": n, "lowered": k, "share": k / n if n else None}
    return out


def coverage(feats: pl.DataFrame, names: list[str], deltas: npt.NDArray[np.float32], attacks: npt.NDArray[Any],
             tol: float) -> dict[str, Any]:
    """Coverage per class for the union of the attacks and for each attack, and what each attack alone adds."""
    union = dict(zip(names, lowered(deltas, tol).tolist()))
    per_attack: dict[str, Any] = {}
    hits = {a: lowered(deltas[attacks == a], tol) for a in ATTACKS}
    for a in ATTACKS:
        others = np.zeros(len(names), bool)
        for b in ATTACKS:
            if b != a:
                others |= hits[b]
        alone = dict(zip(names, (hits[a] & ~others).tolist()))
        per_attack[a] = {"vectors": int((attacks == a).sum()),
                         "coverage": by_class(feats, dict(zip(names, hits[a].tolist()))),
                         "only_this_attack": {c: v["lowered"] for c, v in by_class(feats, alone).items()}}
    by_group = (feats.with_columns(pl.col("feature").replace_strict(union, default=False).alias("hit"))
                .group_by("class", "group").agg(pl.len().alias("lowerable"), pl.col("hit").sum().alias("lowered"))
                .sort("class", "group"))
    return {"vectors": int(deltas.shape[0]), "union": by_class(feats, union), "per_attack": per_attack,
            "by_group": by_group.to_dicts()}


def growth(feats: pl.DataFrame, names: list[str], deltas: npt.NDArray[np.float32], files: list[str], tol: float,
           sizes: list[int], seed: int) -> list[dict[str, Any]]:
    """Union coverage per class when only the first n attacked files (in a seeded order) are observed."""
    order = list(np.random.default_rng(seed).permutation(sorted(set(files))))
    rank = {f: i for i, f in enumerate(order)}
    pos = np.array([rank[f] for f in files])
    out = []
    for n in sizes:
        if n > len(order):
            continue
        hit = dict(zip(names, lowered(deltas[pos < n], tol).tolist()))
        out.append({"files": n, **{c: v["lowered"] for c, v in by_class(feats, hit).items()}})
    return out


def bucket_union(names: list[str], deltas: npt.NDArray[np.float32], tol: float) -> dict[str, Any]:
    """For gamma_sections' vectors: section-name buckets lowered per file (median) and in union, per group."""
    out: dict[str, Any] = {}
    for g in BUCKET_GROUPS:
        cols = [j for j, n in enumerate(names) if n.startswith(g)]
        low = deltas[:, cols] < -tol
        per_file = low.sum(axis=1)
        out[g.removesuffix("_")] = {"buckets": len(cols), "union": int(low.any(axis=0).sum()),
                                    "median_per_file": float(np.median(per_file)) if len(per_file) else None,
                                    "distinct_sets": len({tuple(np.flatnonzero(r)) for r in low})}
    return out


def witnessed(edits: Path) -> dict[str, set[str]]:
    """Per feature, the operations whose edits (on files in the population, parsed) lowered it on re-extraction."""
    e = (pl.read_parquet(edits, columns=["op", "precondition", "parses", "moves"])
         .filter(pl.col("precondition") & pl.col("parses")).explode("moves").drop_nulls("moves")
         .filter(pl.col("moves").str.ends_with(" -")).select("op", pl.col("moves").str.strip_suffix(" -").alias("f"))
         .unique())
    out: dict[str, set[str]] = {}
    for op, f in e.iter_rows():
        out.setdefault(f, set()).add(op)
    return out


################################################################################
# Population membership of the training malware
################################################################################


################################################################################
# PV's hole by class
################################################################################

def hole_by_class(feats: pl.DataFrame, hole_csv: Path, threat_model: str) -> dict[str, Any]:
    """PV's hole (a_pv_hole.py's csv) split by class: features and share of the PV model's gain."""
    h = pl.read_csv(hole_csv).filter(pl.col("threat_model") == threat_model)
    cls = dict(zip(feats["feature"].to_list(), feats["class"].to_list()))
    h = h.with_columns(pl.col("name").replace_strict(cls, default="not_lowerable").alias("class"))
    t = h.group_by("class").agg(pl.len().alias("features"), pl.col("gain_share_over_pv").sum().alias("gain_share"))
    groups = (h.group_by("class", "group").agg(pl.len().alias("features"),
                                               pl.col("gain_share_over_pv").sum().alias("gain_share"))
              .sort("class", "gain_share", descending=[False, True]))
    return {"by_class": {r["class"]: {"features": r["features"], "gain_share": r["gain_share"]} for r in t.to_dicts()},
            "by_group": groups.to_dicts()}


################################################################################
# Main
################################################################################

def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--directions_dir", type=Path, default=ROOT / "artifacts/experiments/a_directions_derived_v2")
    parser.add_argument("--stem", default="M_full-pre-quirkfixed")
    parser.add_argument("--deltas", type=Path, default=ROOT / "artifacts/experiments/a_pv/deltas.parquet")
    parser.add_argument("--pilot_results", type=Path,
                        default=ROOT / "artifacts/experiments/a1/toolkit-derived/results.parquet",
                        help="A toolkit run's results.parquet, for the pilot files' population membership.")
    parser.add_argument("--adv_dir", type=Path, nargs="*",
                        default=[ROOT / "artifacts/experiments/a1/advtrain/generated",
                                 ROOT / "artifacts/experiments/a1/advtrain/generated-heldout"])
    parser.add_argument("--adv_features", type=Path, default=ROOT / "artifacts/features/ember2024")
    parser.add_argument("--db", type=Path, default=EMBER2024_DATA / "tr")
    parser.add_argument("--holes", type=Path, nargs="*",
                        default=[ROOT / "artifacts/experiments/a_pv/derived-pre/hole-seen.csv",
                                 ROOT / "artifacts/experiments/a_pv/derived-pre/hole.csv"])
    parser.add_argument("--edits", type=Path,
                        default=ROOT / "artifacts/experiments/catalogue_checks/2000-exact/edits.parquet",
                        help="catalogue_checks' edits.parquet (our own edits, re-extracted); empty to skip.")
    parser.add_argument("--tol", type=float, default=1e-6)
    parser.add_argument("--sizes", type=int, nargs="*", default=[25, 50, 100, 200, 400])
    parser.add_argument("--num_workers", type=int, default=16)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    feats = classify(args.directions_dir, args.stem)
    print(f"Lowerable ({args.stem}): {feats.height}; " +
          ", ".join(f"{r['class']} {r['len']}" for r in feats.group_by("class").len().to_dicts()), flush=True)
    if (feats["class"] == "unattributed").any():
        raise RuntimeError(f"Lowerable features no operation lowers: {feats.filter(pl.col('class') == 'unattributed')}")
    report: dict[str, Any] = {"stem": args.stem, "tol": args.tol, "toolkit_ops": TOOLKIT_OPS, "other_ops": OTHER_OPS,
                              "lowerable": {c: int((feats["class"] == c).sum()) for c in CLASSES}}

    # Pilot (run 78): all files and the files in the population.
    pv = pl.read_parquet(args.deltas)
    names = [c for c in pv.columns if c not in ("name", "attack", "p_clean", "p_adv")]
    member = dict(pl.read_parquet(args.pilot_results).select("name", "precondition").unique("name").iter_rows())
    hits: dict[str, dict[str, list[str]]] = {}
    for label, frame in (("pilot_all", pv), ("pilot_population", pv.filter(pl.col("name").replace_strict(
            member, default=False)))):
        d = frame.select(names).to_numpy().astype(np.float32)
        report[label] = {"files": frame["name"].n_unique(),
                         **coverage(feats, names, d, frame["attack"].to_numpy(), args.tol)}
        report[label]["gamma_sections_buckets"] = bucket_union(
            names, frame.filter(pl.col("attack") == "gamma_sections").select(names).to_numpy(), args.tol)
        att = frame["attack"].to_numpy()
        hits[label] = {f: [a for a in ATTACKS if lowered(d[att == a][:, [j]], args.tol)[0]]
                       for j, f in enumerate(names)}
        print(f"{label}: {report[label]['files']} files, union {report[label]['union']}", flush=True)

    # Training malware (runs 122 and 131 step 0).
    if args.adv_dir:
        files = pl.concat([pl.read_parquet(a / "files.parquet").select("name", "attack") for a in args.adv_dir])
        d = np.concatenate([adv_deltas(a, args.adv_features, list(ATTACKS), names) for a in args.adv_dir])
        if d.shape[0] != files.height:
            raise RuntimeError(f"{d.shape[0]} training vectors for {files.height} rows.")
        print(f"Training: {d.shape[0]} vectors on {files['name'].n_unique()} files; population check...", flush=True)
        member_tr = population(sorted(set(files["name"].to_list())), args.db, args.num_workers)
        in_pop = np.array([member_tr[n] for n in files["name"].to_list()])
        for label, mask in (("train_all", np.ones(len(in_pop), bool)), ("train_population", in_pop)):
            sub, att = d[mask], files["attack"].to_numpy()[mask]
            fnames = [n for n, m in zip(files["name"].to_list(), mask) if m]
            report[label] = {"files": len(set(fnames)), **coverage(feats, names, sub, att, args.tol),
                             "growth": growth(feats, names, sub, fnames, args.tol, args.sizes, args.seed),
                             "gamma_sections_buckets": bucket_union(names, sub[att == "gamma_sections"], args.tol)}
            hits[label] = {f: [a for a in ATTACKS if lowered(sub[att == a][:, [j]], args.tol)[0]]
                           for j, f in enumerate(names)}
            print(f"{label}: {report[label]['files']} files, union {report[label]['union']}", flush=True)
        both = {f: hits["pilot_population"][f] or hits["train_population"][f] for f in names}
        report["pilot_and_train_population"] = by_class(feats, {f: bool(v) for f, v in both.items()})

    # Witnessed by our own edits, and the gap the toolkit leaves among the witnessed features.
    if args.edits and args.edits.exists():
        wit = witnessed(args.edits)
        toolkit = {o.removeprefix("op_").removesuffix("_pre") for o in TOOLKIT_OPS}
        feats = feats.with_columns(
            pl.col("feature").replace_strict({f: " ".join(sorted(v)) for f, v in wit.items()}, default="")
            .alias("witnessed_by"))
        w = {f: bool(v) for f, v in wit.items()}
        w_tool = {f: bool(v & toolkit) for f, v in wit.items()}
        report["witnessed"] = {"any_op": by_class(feats, w), "toolkit_op": by_class(feats, w_tool)}
        lowered_tk = {f: bool(hits["pilot_population"].get(f)) or bool(hits.get("train_population", {}).get(f))
                      for f in names}
        gap = {f: w.get(f, False) and not lowered_tk.get(f, False) for f in names}
        gap_tool = {f: w_tool.get(f, False) and not lowered_tk.get(f, False) for f in names}
        report["witnessed_not_lowered_by_toolkit"] = {
            "any_op": by_class(feats, gap), "toolkit_op": by_class(feats, gap_tool),
            "by_group": (feats.filter(pl.col("feature").replace_strict(gap, default=False))
                         .group_by("group").agg(pl.len().alias("features")).sort("features", descending=True)
                         .to_dicts())}
        for h in args.holes:
            if not h.exists():
                continue
            hh = pl.read_csv(h).filter(pl.col("threat_model") == "M_full")
            hh = hh.with_columns(pl.col("name").replace_strict(w, default=False).alias("w"),
                                 pl.col("name").replace_strict(w_tool, default=False).alias("wt"))
            report.setdefault("pv_hole_witnessed", {})[h.name] = {
                "features": hh.height, "gain_share": float(hh["gain_share_over_pv"].sum()),
                "witnessed": {"features": int(hh["w"].sum()),
                              "gain_share": float(hh.filter(pl.col("w"))["gain_share_over_pv"].sum())},
                "witnessed_by_toolkit_op": {"features": int(hh["wt"].sum()),
                                            "gain_share": float(hh.filter(pl.col("wt"))["gain_share_over_pv"].sum())},
                "witnessed_by_group": (hh.filter(pl.col("w")).group_by("group")
                                       .agg(pl.len().alias("features"),
                                            pl.col("gain_share_over_pv").sum().alias("gain_share"))
                                       .sort("gain_share", descending=True).to_dicts())}

    # PV's hole by class.
    report["pv_hole"] = {h.name: hole_by_class(feats, h, "M_full") for h in args.holes if h.exists()}

    out = feats.with_columns(*[pl.col("feature").replace_strict({f: " ".join(v) for f, v in h.items()}, default="")
                               .alias(f"lowered_by:{k}") for k, h in hits.items()])
    out.write_csv(args.outdir / "features.csv")
    (args.outdir / "report.json").write_text(json.dumps(report, indent=2))
    for k in [k for k in report if k.startswith(("pilot", "train"))]:
        print(k, json.dumps(report[k]["union"] if "union" in report[k] else report[k]))
    for k, v in report["pv_hole"].items():
        print(k, json.dumps(v["by_class"]))
    for k in ("witnessed", "witnessed_not_lowered_by_toolkit", "pv_hole_witnessed"):
        if k in report:
            print(k, json.dumps(report[k])[:1500])
    print(f"Done: {args.outdir}/report.json, features.csv")


if __name__ == "__main__":
    main()
