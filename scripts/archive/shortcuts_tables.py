"""
3-B tables (docs/archive/shortcuts_plan.md): the ranked list of candidate spurious correlations surfaced by the pullback, the
baseline without P (label-skewed 4-grams), and mitigation, assembled from the outputs of scripts/shortcuts_transplant.py,
scripts/shortcuts_reliance.py, scripts/shortcuts_train_sample.py, and scripts/train_classic.py. Missing inputs are
skipped.

With `--write_neutralize`, also write the features to neutralize for mitigation (one per line): for every candidate
that is confirmed by the transplant test and labeled an artifact, the features whose provenance its bytes carry with a
share of at least 0.5 in at least half of the files where it sits at its feature (scripts/shortcuts_reliance.py).

Usage:
    python scripts/shortcuts_tables.py --seed 0
    python scripts/shortcuts_tables.py --seed 0 --write_neutralize artifacts/experiments/shortcuts_mitigation/seed-0/neutralize.txt
"""

from __future__ import annotations

from argparse import ArgumentParser
import json
from pathlib import Path
from typing import Optional

import polars as pl


__all__ = [
    "LABELS",
    "label",
    "neutralize",
]


ROOT = Path(__file__).parent.parent
EXPERIMENTS = ROOT / "artifacts" / "experiments"

# A domain judgement of each candidate from its content and feature alone (allowed in experiments, CLAUDE.md):
# "artifact" if it is a toolchain, packaging, or metadata artifact with no bearing on what the program does (the
# spurious kind), "structural" if it reflects what the file contains (no entry point, no imports, no resources, a code
# section). Keyed by (top feature, content in hex).
LABELS: dict[tuple[str, str], tuple[str, str]] = {
    ("header:optional_header_AddressOfEntryPoint", "00000000"): ("structural", "no entry point"),
    ("section:num_rx", "20000060"): ("structural", "standard code-section flags"),
    ("datadirectories:debug_size", "54000000"): ("artifact", "debug-directory size (toolchain)"),
    ("header:optional_header_SizeOfCode", "00000000"): ("artifact", "SizeOfCode 0 (header metadata the loader ignores)"),
    ("datadirectories:debug_size", "70000000"): ("artifact", "debug-directory size (toolchain)"),
    ("section:size_hash_5", "2e72656c6f630000"): ("artifact", "section name .reloc"),
    ("datadirectories:import_virtual_address", "00000000"): ("structural", "no import table"),
    ("section:size_hash_43", "2e72737263000000"): ("artifact", "section name .rsrc"),
    ("header:optional_header_ImageBase", "00000010"): ("artifact", "DLL default image base"),
    ("datadirectories:resource_virtual_address", "00200000"): ("artifact", "resource RVA 0x2000 (linker layout)"),
    ("strings:regex_dos_msg", "21546869732070726f6772616d2063616e6e6f742062652072756e20696e20444f53206d6f64652e"): ("artifact", "DOS stub message"),
    ("section:size_hash_41", "2e74657874000000"): ("artifact", "section name .text"),
    ("datadirectories:debug_size", "1c000000"): ("artifact", "debug-directory size (toolchain)"),
    ("datadirectories:security_size", "38280000"): ("artifact", "certificate-table size (signing metadata)"),
    ("datadirectories:iat_size", "00000000"): ("structural", "no import address table"),
    ("datadirectories:security_size", "20280000"): ("artifact", "certificate-table size (signing metadata)"),
    ("datadirectories:debug_size", "38000000"): ("artifact", "debug-directory size (toolchain)"),
    ("imports:library_hash_4", "564352554e54494d453134302e646c6c"): ("artifact", "VCRUNTIME140.dll (runtime library)"),
    ("header:optional_header_SizeOfStackReserve", "00000400"): ("artifact", "stack reserve 0x40000 (linker default)"),
    ("datadirectories:resource_virtual_address", "00000000"): ("structural", "no resources"),
}


def label(feature: str, content: bytes) -> tuple[str, str]:
    """The judgement and a short description of a candidate, or ("unlabeled", "") if it has none."""
    return LABELS.get((feature, content.hex()), ("unlabeled", ""))


def text(content: bytes, width: int = 20) -> str:
    """Printable ASCII as is, otherwise the hex of the first bytes."""
    if len(content.rstrip(b"\x00")) >= 4 and all(32 <= c < 127 for c in content.rstrip(b"\x00")):
        s = content.rstrip(b"\x00").decode()
        return f"`{s[:width]}{'…' if len(s) > width else ''}`"
    return f"`0x{content[:8].hex()}`"


def neutralize(summary: pl.DataFrame, carried: pl.DataFrame, reliance: pl.DataFrame, min_share_files: float = 0.5) -> list[str]:
    """
    The features to neutralize: for each confirmed artifact candidate, the features its bytes carry (share >= the
    reliance run's threshold) in at least `min_share_files` of the files where it sits at its feature.
    """
    chosen = []
    for r in summary.filter((pl.col("kind") == "pullback") & pl.col("confirmed").fill_null(False)).iter_rows(named=True):
        if label(r["top_feature"], r["content"])[0] != "artifact":
            continue
        at = reliance.filter((pl.col("kind") == "pullback") & (pl.col("candidate") == r["candidate"]))["at_feature_files"]
        total = int(at[0]) if at.len() and at[0] is not None else 0
        if total == 0:
            continue
        rows = carried.filter((pl.col("candidate") == r["candidate"]) & (pl.col("files") >= min_share_files * total))
        chosen.extend(rows["name"].to_list())
    return sorted(set(chosen))


def read(path: Path) -> Optional[pl.DataFrame]:
    """A parquet file, or None if it does not exist."""
    return pl.read_parquet(path) if path.exists() else None


def main() -> None:
    parser = ArgumentParser(description="3-B tables.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--neutral_tag", type=str, default="neutral", help="The transplant tag and model suffix of the mitigated GBDT.")
    parser.add_argument("--write_neutralize", type=Path, default=None)
    args = parser.parse_args()

    seed = f"seed-{args.seed}"
    tp = EXPERIMENTS / "shortcuts_transplant" / seed
    summary = pl.read_parquet(tp / "gbdt" / "summary.parquet")
    candidates = pl.read_parquet(tp / "gbdt" / "candidates.parquet")
    reliance = read(EXPERIMENTS / "shortcuts_reliance" / seed / "reliance.parquet")
    carried = read(EXPERIMENTS / "shortcuts_reliance" / seed / "carried.parquet")
    prevalence = read(EXPERIMENTS / "shortcuts_train" / seed / "prevalence.parquet")
    train_report = EXPERIMENTS / "shortcuts_train" / seed / "report.json"
    mined = read(EXPERIMENTS / "shortcuts_train" / seed / "mined.parquet")
    neutral = read(tp / args.neutral_tag / "summary.parquet")

    if args.write_neutralize is not None:
        if carried is None or reliance is None:
            raise RuntimeError("Run scripts/shortcuts_reliance.py first.")
        names = neutralize(summary, carried, reliance)
        args.write_neutralize.parent.mkdir(parents=True, exist_ok=True)
        args.write_neutralize.write_text("".join(f"{n}\n" for n in names))
        print(f"Wrote {len(names)} features to {args.write_neutralize.as_posix()}: {names}\n")

    # Table 1: the ranked list.
    nb = nm = None
    if train_report.exists():
        report = json.loads(train_report.read_text())
        nb, nm = report["num_benign"], report["num_malware"]
    print("Table 1. The top benign-pushing patterns surfaced by the pullback (run 22), ranked by score.")
    print("test b/m: files in the 2,000-file explanation set where the pattern is among the top-credited spans; "
          "train b/m: share of sampled training files holding it at the feature's bytes; credit: mean credit toward "
          "benign at the feature's bytes; carry: median share of the feature's provenance in those bytes; drop: median "
          "move toward benign, content vs. random in the same bytes, over n held-out malware.\n")
    print("| # | content | top feature | judgement | test b/m | train b/m | credit | carry | n | drop (content / random) | flip | confirmed |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    pulled = summary.filter(pl.col("kind") == "pullback").join(
        candidates.filter(pl.col("kind") == "pullback").select("candidate", "benign_files", "malware_files"), on="candidate")
    for r in pulled.sort("candidate").iter_rows(named=True):
        judgement, note = label(r["top_feature"], r["content"])
        train = "–"
        if prevalence is not None and nb and nm:
            p = prevalence.filter(pl.col("candidate") == r["candidate"])
            if p.height:
                train = f"{p['benign_at_feature'][0] / nb:.1%} / {p['malware_at_feature'][0] / nm:.1%}"
        credit = carry = "–"
        if reliance is not None:
            rr = reliance.filter((pl.col("kind") == "pullback") & (pl.col("candidate") == r["candidate"]))
            if rr.height and rr["mean_feature_credit"][0] is not None:
                credit = f"{rr['mean_feature_credit'][0]:.2f}"
        if carried is not None:
            cc = carried.filter((pl.col("candidate") == r["candidate"]) & pl.col("is_top"))
            if cc.height:
                carry = f"{cc['median_share'][0]:.2f}"
        n = r["applicable"] or 0
        drop = f"{r['median_drop_content']:+.2f} / {r['median_drop_random']:+.2f}" if n else f"n/a ({r['already_present']} present, {r['no_run']} no run)"
        flip = f"{r['flip_content']:.2f} / {r['flip_random']:.2f}" if n else "–"
        print(f"| {r['candidate']} | {text(r['content'])} | `{r['top_feature']}` | {judgement}: {note} | {r['benign_files']}/{r['malware_files']} "
              f"| {train} | {credit} | {carry} | {n} | {drop} | {flip} | {'**yes**' if r['confirmed'] else 'no'} |")

    # Table 2: the baseline without P.
    if mined is not None:
        top = mined.filter(pl.col("direction") == "benign").sort("rank")
        print(f"\nTable 2. Baseline without P: the top benign-skewed 4-grams of the training sample by chi-squared ({nb} benign, {nm} malware files).")
        print("credit: mean best-occurrence credit toward benign in the explanation set (any occurrence); credited: share of "
              "files containing it with credit > 0.01; drop: appended to held-out malware, content vs. random.\n")
        print("| rank | 4-gram | benign df | malware df | chi2 | credit | credited | drop (content / random) |")
        print("|---|---|---|---|---|---|---|---|")
        mined_tp = summary.filter(pl.col("kind") == "mined")
        for r in top.head(20).iter_rows(named=True):
            credit = credited = drop = "–"
            if reliance is not None:
                rr = reliance.filter((pl.col("kind") == "mined") & (pl.col("candidate") == r["rank"]))
                if rr.height and rr["mean_credit"][0] is not None:
                    credit, credited = f"{rr['mean_credit'][0]:.3f}", f"{rr['credited_share'][0]:.2f}"
            t = mined_tp.filter(pl.col("candidate") == r["rank"])
            if t.height and t["applicable"][0]:
                drop = f"{t['median_drop_content'][0]:+.2f} / {t['median_drop_random'][0]:+.2f}"
            print(f"| {r['rank']} | {text(r['content'])} | {r['benign_df']} | {r['malware_df']} | {r['chi2']:.0f} | {credit} | {credited} | {drop} |")
        # Would mining have found the pullback's candidates? The best rank of any 4-gram of each candidate's content.
        rank = {bytes(c): int(k) for c, k in zip(top["content"].to_list(), top["rank"].to_list())}
        print(f"\nThe best chi-squared rank (benign-skewed, top {top.height}) of any 4-gram of each pullback candidate:")
        for r in pulled.sort("candidate").iter_rows(named=True):
            c = bytes(r["content"])
            ranks = [rank[c[i:i + 4]] for i in range(len(c) - 3) if c[i:i + 4] in rank]
            print(f"  {r['candidate']:2d} {text(c):24s} {min(ranks) if ranks else '> ' + str(top.height)}")

    # Table 3: mitigation.
    if neutral is not None:
        clean = json.loads((ROOT / "artifacts" / "models" / "gbdt" / seed / "metrics.json").read_text())["ts_metrics"]
        mitigated = json.loads((ROOT / "artifacts" / "models" / "gbdt" / f"{seed}-{args.neutral_tag}" / "metrics.json").read_text())
        print(f"\nTable 3. Mitigation: {len(mitigated.get('neutralized') or [])} features neutralized and the GBDT retrained.")
        print(f"Test ROC-AUC {clean['roc']:.5f} -> {mitigated['ts_metrics']['roc']:.5f}; accuracy {clean['acc']:.4f} -> {mitigated['ts_metrics']['acc']:.4f}.\n")
        print("| # | content | top feature | drop before (content / random) | drop after (content / random) | confirmed after |")
        print("|---|---|---|---|---|---|")
        after = neutral.filter(pl.col("kind") == "pullback")
        for r in pulled.filter(pl.col("confirmed").fill_null(False)).sort("candidate").iter_rows(named=True):
            a = after.filter(pl.col("candidate") == r["candidate"]).row(0, named=True)
            print(f"| {r['candidate']} | {text(r['content'])} | `{r['top_feature']}` | {r['median_drop_content']:+.2f} / {r['median_drop_random']:+.2f} "
                  f"| {a['median_drop_content']:+.2f} / {a['median_drop_random']:+.2f} | {'yes' if a['confirmed'] else 'no'} |")


if __name__ == "__main__":
    main()
