"""
3-B on a training sample (docs/archive/shortcuts_plan.md): (1) how common each surfaced candidate is by label in the data the
GBDT learned from, and (2) the baseline without P: label-skewed byte 4-grams mined from the same sample (document
frequency per label, ranked by chi-squared; the classic n-gram feature selection of Kolter & Maloof, 2006).

The sample: `--num_shards` training shards drawn with the seed, and `--per_label` benign and malware files drawn from
each (all of them if fewer). Sampling within shards keeps the I/O to a few dozen shards (a shard holds about 1,000
files, about 1 GB) instead of most of the 1.3 TB.

Per file, for each of the top `--num_patterns` discovery patterns (scripts/shortcuts.py, benign-pushing, recurring in
at least `--min_files` files): whether its content sits at the bytes that feed its top feature (a run of P's column
of exactly the content's length holds it; this is the prevalence of the pattern as the model sees it) and whether it
occurs anywhere in the file. And every distinct 4-gram of the file counts once toward its label's document frequency
(exact: 2^32 counters per label, in shared memory).

Outputs, in `{outdir}/seed-{seed}/`:
    files.parquet       one row per sampled file: shard, position, label, size, status
    presence.parquet    one row per (file, pattern): at_feature, anywhere
    prevalence.parquet  one row per pattern: files with it at the feature and anywhere, by label
    mined.parquet       the top `--num_mined` 4-grams per direction ("benign": more frequent in benign files), with
                        their document frequencies, chi-squared, information gain, and rank
    report.json         the configuration, statuses, and timing

Usage:
    PYTHONHASHSEED=0 python scripts/shortcuts_train_sample.py --seed 0 --num_workers 25
"""

from __future__ import annotations

from argparse import ArgumentParser
from collections import Counter
import json
import multiprocessing as mp
import os
from pathlib import Path
import signal
import sys
import time
from types import FrameType
from typing import Any
from typing import Optional
import warnings

import numpy as np
from numpy import typing as npt
import polars as pl
from tqdm import tqdm

from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBIterator
from provexp.featuresets.ember2024.features import PEFeatureExtractor
from provexp.data.paths import EMBER2024_DATA

sys.path.insert(0, str(Path(__file__).parent))

from shortcuts_transplant import feature_runs  # noqa: E402
from shortcuts_transplant import select_candidates  # noqa: E402


__all__ = [
    "grams",
    "chi2",
    "information_gain",
    "rank_grams",
]


ROOT = Path(__file__).parent.parent
NUM_GRAMS = 2 ** 32

_EXTRACTOR: Optional[PEFeatureExtractor] = None
_COUNTS: Optional[Any] = None
_LOCK: Optional[Any] = None


################################################################################
# N-grams
################################################################################


def grams(data: bytes) -> npt.NDArray[np.uint32]:
    """The distinct 4-grams of `data`, each as the little-endian uint32 of its bytes."""
    d = np.frombuffer(data, dtype=np.uint8)
    if d.size < 4:
        return np.zeros(0, dtype=np.uint32)
    d32 = d.astype(np.uint32)
    g = d32[:-3] | (d32[1:-2] << 8) | (d32[2:-1] << 16) | (d32[3:] << 24)
    return np.unique(g)


def chi2(b: npt.NDArray[np.integer], m: npt.NDArray[np.integer], nb: int, nm: int) -> npt.NDArray[np.float64]:
    """
    The chi-squared statistic of the 2x2 table (label x presence) of each n-gram, from its document frequencies `b`
    and `m` among `nb` benign and `nm` malware files.
    """
    b_ = b.astype(np.float64)
    m_ = m.astype(np.float64)
    n = nb + nm
    present = b_ + m_
    absent = n - present
    num = n * (b_ * (nm - m_) - m_ * (nb - b_)) ** 2
    den = present * absent * nb * nm
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.where(den > 0, num / den, 0.0)
    return out


def information_gain(b: npt.NDArray[np.integer], m: npt.NDArray[np.integer], nb: int, nm: int) -> npt.NDArray[np.float64]:
    """The information gain (bits) of the label from each n-gram's presence, from its document frequencies."""
    def h(p: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        with np.errstate(divide="ignore", invalid="ignore"):
            out = -(p * np.log2(p) + (1 - p) * np.log2(1 - p))
        return np.nan_to_num(out)

    n = nb + nm
    b_ = b.astype(np.float64)
    m_ = m.astype(np.float64)
    present = b_ + m_
    absent = n - present
    with np.errstate(divide="ignore", invalid="ignore"):
        p_in = np.where(present > 0, m_ / present, 0.0)
        p_out = np.where(absent > 0, (nm - m_) / absent, 0.0)
    prior = float(h(np.array([nm / n]))[0])
    return prior - (present / n) * h(p_in) - (absent / n) * h(p_out)


def rank_grams(benign: npt.NDArray[np.uint16], malware: npt.NDArray[np.uint16], nb: int, nm: int, num: int, min_df: int, chunk: int = 2 ** 26) -> pl.DataFrame:
    """
    The top `num` n-grams by chi-squared in each direction ("benign" if relatively more frequent in benign files),
    among those in at least `min_df` files.
    """
    if benign.shape != malware.shape:
        raise ValueError(f"Expected counts of the same shape. Got {benign.shape} and {malware.shape}.")
    best: dict[str, list[tuple[npt.NDArray[np.float64], npt.NDArray[np.int64]]]] = {"benign": [], "malware": []}
    for lo in range(0, benign.size, chunk):
        b = benign[lo:lo + chunk]
        m = malware[lo:lo + chunk]
        keep = np.flatnonzero(b.astype(np.int64) + m >= min_df)
        if keep.size == 0:
            continue
        score = chi2(b[keep], m[keep], nb, nm)
        toward_benign = b[keep] / nb > m[keep] / nm
        for direction, mask in (("benign", toward_benign), ("malware", ~toward_benign)):
            s, k = score[mask], keep[mask]
            if s.size > num:
                top = np.argpartition(-s, num)[:num]
                s, k = s[top], k[top]
            best[direction].append((s, k + lo))
    rows = []
    for direction, parts in best.items():
        if not parts:
            continue
        s = np.concatenate([p[0] for p in parts])
        k = np.concatenate([p[1] for p in parts])
        # Ties broken by the n-gram's value (a fixed, content-independent order of the vocabulary).
        order = np.lexsort((k, -s))[:num]
        for rank, i in enumerate(order):
            g = int(k[i])
            rows.append({"direction": direction, "rank": rank, "gram": g, "content": g.to_bytes(4, "little"),
                         "benign_df": int(benign[g]), "malware_df": int(malware[g]), "chi2": float(s[i])})
    table = pl.DataFrame(rows, schema={"direction": pl.String, "rank": pl.Int64, "gram": pl.Int64, "content": pl.Binary,
                                       "benign_df": pl.Int64, "malware_df": pl.Int64, "chi2": pl.Float64})
    ig = information_gain(table["benign_df"].to_numpy(), table["malware_df"].to_numpy(), nb, nm)
    return table.with_columns(pl.Series("ig", ig))


################################################################################
# Workers
################################################################################


class SampleTimeout(Exception):
    pass


def _raise_timeout(signum: int, frame: Optional[FrameType]) -> None:
    raise SampleTimeout()


def _init_worker(counts: Any, lock: Any) -> None:
    global _EXTRACTOR, _COUNTS, _LOCK
    _EXTRACTOR = PEFeatureExtractor()
    _COUNTS = np.frombuffer(counts, dtype=np.uint16).reshape(2, NUM_GRAMS)
    _LOCK = lock
    # thrember prints unknown pefile warnings to stdout.
    sys.stdout = open(os.devnull, "w")
    warnings.filterwarnings("ignore")
    signal.signal(signal.SIGALRM, _raise_timeout)


def process_shard(
    shard: int,
    samples: list[dict[str, Any]],
    dbdir: Path,
    patterns: list[dict[str, Any]],
    timeout: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Record pattern presence and count 4-grams for the sampled files of one shard.

    Args:
        shard: The shard.
        samples: The sampled files in the shard, each with its `position`, `name`, and `label`.
        dbdir: The SimpleDB.
        patterns: Each with its `candidate` id, `content`, and top feature's index `j`.
        timeout: The maximum number of seconds per file (for the provenance extraction).

    Returns:
        The file records and the presence records.
    """
    assert _EXTRACTOR is not None and _COUNTS is not None and _LOCK is not None
    needed = np.array(sorted({int(p["j"]) for p in patterns}), dtype=np.int64)
    wanted = {s["position"]: i for i, s in enumerate(samples)}
    files: list[dict[str, Any]] = []
    presence: list[dict[str, Any]] = []
    seen = set()
    db = SimpleDB(dbdir, check=False)
    for position, sample in enumerate(SimpleDBIterator(db).iter(shard)):
        if position not in wanted:
            continue
        seen.add(position)
        meta = samples[wanted[position]]
        if sample.name != meta["name"]:
            raise RuntimeError(f"Shard {shard}, position {position} holds {sample.name}, not {meta['name']}.")
        data = bytes(sample.data)
        base = {"name": meta["name"], "shard": shard, "position": position, "label": meta["label"], "size": len(data)}
        g = grams(data)
        with _LOCK:
            _COUNTS[int(meta["label"]), g] += 1
        signal.alarm(timeout)
        try:
            _, prov = _EXTRACTOR.feature_vector_with_provenance(data)
            runs = feature_runs(prov, needed)
            for p in patterns:
                content = bytes(p["content"])
                at = any(n == len(content) and data[s:s + n] == content for s, n in runs[int(p["j"])])
                presence.append({"name": meta["name"], "label": meta["label"], "candidate": p["candidate"],
                                 "at_feature": at, "anywhere": content in data})
            files.append(base | {"status": "ok"})
        except SampleTimeout:
            files.append(base | {"status": "timeout"})
        except Exception as err:
            files.append(base | {"status": "error", "error": f"{type(err).__name__}: {err}"[:300]})
        finally:
            signal.alarm(0)
    missing = set(wanted) - seen
    if missing:
        raise RuntimeError(f"Shard {shard} has no samples at positions {sorted(missing)}.")
    return files, presence


def _star(task: tuple[Any, ...]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return process_shard(*task)


################################################################################
# Driver
################################################################################


def main() -> None:
    parser = ArgumentParser(description="3-B: candidate prevalence and mined 4-grams on a training sample.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--num_shards", type=int, default=50)
    parser.add_argument("--per_label", type=int, default=50, help="Files per label per shard.")
    parser.add_argument("--patterns", type=Path, default=ROOT / "artifacts" / "experiments" / "shortcuts" / "seed-0" / "treeshap_interventional-benign" / "patterns.parquet")
    parser.add_argument("--num_patterns", type=int, default=100)
    parser.add_argument("--min_files", type=int, default=10)
    parser.add_argument("--num_mined", type=int, default=1000)
    parser.add_argument("--min_df", type=int, default=25, help="Mine only 4-grams in at least this many sampled files.")
    parser.add_argument("--features", type=Path, default=ROOT / "artifacts" / "features" / "ember2024")
    parser.add_argument("--db", type=Path, default=EMBER2024_DATA / "tr")
    parser.add_argument("--outdir", type=Path, default=ROOT / "artifacts" / "experiments" / "shortcuts_train")
    parser.add_argument("--num_workers", type=int, default=25)
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()

    if os.environ.get("PYTHONHASHSEED") != "0":
        raise RuntimeError("Run with PYTHONHASHSEED=0 so that the features match the feature store.")

    outdir = args.outdir / f"seed-{args.seed}"
    outdir.mkdir(parents=True, exist_ok=True)
    names = PEFeatureExtractor().feature_names
    index = {name: i for i, name in enumerate(names)}
    patterns = select_candidates(pl.read_parquet(args.patterns), args.num_patterns, args.min_files)
    patterns = patterns.with_columns(pl.col("top_feature").replace_strict(index, return_dtype=pl.Int64).alias("j"))
    rows = patterns.select("candidate", "content", "j").to_dicts()

    meta = pl.read_parquet(args.features / "tr" / "meta.parquet").filter(pl.col("status") == "ok")
    rng = np.random.default_rng(args.seed)
    shards = np.sort(rng.choice(meta["shard"].unique().sort().to_numpy(), size=args.num_shards, replace=False))
    chosen = meta.filter(pl.col("shard").is_in(shards.tolist()))
    sample = (
        chosen.with_columns(pl.Series("u", rng.random(chosen.height)))
        .sort("u").group_by("shard", "label", maintain_order=True).head(args.per_label)
    )
    print(f"3-B training sample: {sample.height} files from {args.num_shards} shards "
          f"({int((sample['label'] == 0).sum())} benign), {patterns.height} patterns.", flush=True)

    tasks = []
    for (shard,), group in sample.sort("shard", "position").group_by("shard", maintain_order=True):
        tasks.append((int(shard), group.select("name", "label", "position").to_dicts(), args.db, rows, args.timeout))

    t_0 = time.time()
    counts = mp.RawArray("H", 2 * NUM_GRAMS)
    lock = mp.Lock()
    files: list[dict[str, Any]] = []
    presence: list[dict[str, Any]] = []
    with mp.get_context("fork").Pool(args.num_workers, initializer=_init_worker, initargs=(counts, lock)) as pool:
        for f, p in tqdm(pool.imap_unordered(_star, tasks), total=len(tasks), desc="shards", mininterval=30):
            files.extend(f)
            presence.extend(p)
    minutes_io = (time.time() - t_0) / 60

    file_table = pl.DataFrame(files, infer_schema_length=None).sort("shard", "position")
    presence_table = pl.DataFrame(presence, infer_schema_length=None)
    ok = file_table.filter(pl.col("status") == "ok").select("name")
    presence_table = presence_table.join(ok, on="name", how="semi")
    nb = int((file_table["label"] == 0).sum())
    nm = int((file_table["label"] == 1).sum())
    prevalence = (
        presence_table.group_by("candidate").agg(
            (pl.col("at_feature") & (pl.col("label") == 0)).sum().alias("benign_at_feature"),
            (pl.col("at_feature") & (pl.col("label") == 1)).sum().alias("malware_at_feature"),
            (pl.col("anywhere") & (pl.col("label") == 0)).sum().alias("benign_anywhere"),
            (pl.col("anywhere") & (pl.col("label") == 1)).sum().alias("malware_anywhere"),
        )
        .join(patterns.select("candidate", "top_feature", "content"), on="candidate").sort("candidate")
    )
    C = np.frombuffer(counts, dtype=np.uint16).reshape(2, NUM_GRAMS)
    mined = rank_grams(C[0], C[1], nb, nm, args.num_mined, args.min_df)
    file_table.write_parquet(outdir / "files.parquet")
    presence_table.write_parquet(outdir / "presence.parquet")
    prevalence.write_parquet(outdir / "prevalence.parquet")
    mined.write_parquet(outdir / "mined.parquet")

    report = {
        "config": {k: (v.as_posix() if isinstance(v, Path) else v) for k, v in vars(args).items()},
        "shards": shards.tolist(),
        "num_files": file_table.height,
        "num_benign": nb,
        "num_malware": nm,
        "status": dict(Counter(file_table["status"].to_list())),
        "distinct_grams": int(np.count_nonzero(C[0].astype(np.uint32) + C[1])),
        "minutes_io": minutes_io,
        "minutes": (time.time() - t_0) / 60,
    }
    (outdir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k not in ("config", "shards")}, indent=2))

    def text(c: bytes) -> str:
        return "".join(chr(x) if 32 <= x < 127 else "." for x in c[:24])

    print(f"\nPrevalence of the top patterns ({nb} benign, {nm} malware files): at the feature's bytes / anywhere.")
    for r in prevalence.head(30).iter_rows(named=True):
        print(f"{r['candidate']:3d}  benign {r['benign_at_feature']:5d} / {r['benign_anywhere']:5d}  "
              f"malware {r['malware_at_feature']:5d} / {r['malware_anywhere']:5d}  {r['top_feature'][:42]:42s} {text(r['content'])!r}")
    for direction in ("benign", "malware"):
        print(f"\nTop {direction}-skewed 4-grams by chi-squared:")
        for r in mined.filter(pl.col("direction") == direction).head(25).iter_rows(named=True):
            print(f"{r['rank']:4d}  chi2 {r['chi2']:8.1f}  ig {r['ig']:.4f}  benign {r['benign_df']:5d}  malware {r['malware_df']:5d}  "
                  f"{text(r['content'])!r} [{r['content'].hex()}]")
    print(f"\nWrote {outdir.as_posix()}.")


if __name__ == "__main__":
    main()
