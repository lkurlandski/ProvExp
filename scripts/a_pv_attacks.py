"""
Direction A, go/no-go check 2 (docs/direction-A-mock.md), part 1 of 2: the perturbation vectors.

FOR ACADEMIC SECURITY RESEARCH ONLY. This reproduces, against our own detector and on our own pilot samples, the
black-box functionality-preserving transformations of Gimenez et al. ("Certifiably robust malware detectors by
design") and Demetrio et al. (secml-malware), in order to *evaluate a defense*: it measures which EMBER features their
attack sample happens never to decrease, so that we can test whether perturbation-vector (PV) feature selection leaves
a hole that feature provenance (C4) predicts. No new evasion technique is developed and nothing is deployed; the
attacked files are written only so their features can be re-extracted and differenced.

For each detected pilot malware sample, we run each of Gimenez et al.'s eight secml-malware attacks against our GBDT,
re-extract the features of the written file with our (quirk-fixed, merged-imports) extractor, and record the
perturbation vector delta = phi(z') - phi(z). The stacked deltas are the input to scripts/a_pv_hole.py.

Outputs, in `{outdir}/`:
    deltas.parquet      one row per (file, attack) that produced a parseable file: the 2,568 feature deltas, plus the
                        attack name, the file name, and the clean/adversarial GBDT probability
    evasion.parquet     one row per (file, attack): evaded (adv prob < 0.5), probabilities, bytes added, seconds
    summary.json        per-attack evasion rate and timing; the run's configuration

Usage (smoke on three files):
    PYTHONHASHSEED=0 python scripts/a_pv_attacks.py --outdir artifacts/experiments/a_pv --num_malware 3 --attacks padding
Full pilot run is driven by run/78_a_check2_attacks.sh (hand it to the user; see that script for the estimate).
"""

from __future__ import annotations

from argparse import ArgumentParser
import json
from multiprocessing import get_context
from pathlib import Path
import random
import tempfile
import time
from typing import Any
from typing import Callable
from typing import Optional

import lief
import numpy as np
import polars as pl

from provexp.data.simpledb import SimpleDB
from provexp.data.simpledb import SimpleDBReader
from provexp.featuresets.ember2024.features import merge_import_descriptors
from provexp.featuresets.ember2024.features import PEFeatureExtractor

__all__ = ["ATTACKS", "build_attack", "map_watchdog", "run_attack"]

ROOT = Path(__file__).resolve().parent.parent

# The eight attacks Gimenez et al. derive PV selection from (their attack_experiment.py), at the low-budget setting
# (population 10, 10 iterations). secml-malware's genetic engine is reseeded before each run (their random.seed(0)).
ATTACKS = ("gamma_sections", "gamma_api", "gamma_shift", "content_shift", "dos_extend", "header_fields", "padding",
           "format_exploit")


################################################################################
# Our detector, wrapped for secml-malware's black-box engine
################################################################################

def calibrated(p: np.ndarray, tau: float) -> np.ndarray:
    """A probability on a routed detector's scale: sigmoid(logit(p) - logit(tau)), so p > tau iff the result > 0.5."""
    eps = 1e-12
    logit = np.log(np.clip(p, eps, 1 - eps)) - np.log(np.clip(1 - p, eps, 1 - eps))
    out: np.ndarray = 1 / (1 + np.exp(-(logit - np.log(tau / (1 - tau)))))
    return out


def make_wrapper(model_path: Path, extractor: PEFeatureExtractor, fallback: Optional[Path] = None,
                 route: Optional[Callable[[bytes], bool]] = None, taus: Optional[tuple[float, float]] = None) -> Any:
    """A CWrapperPhi over our LightGBM GBDT that extracts features with our own extractor.

    With `fallback`, the detector is routed: files for which `route` holds are scored by the model, the others by the
    fallback model, each on one scale, sigmoid(logit(p) - logit(tau)) with its own threshold from `taus` (model,
    fallback), so that a routed file is detected when its score exceeds 0.5. The attack queries the routed detector.

    Args:
        model_path: Path to the LightGBM model text file.
        extractor: The (quirk-fixed) extractor whose features the GBDT was trained on.
        fallback: Path to the fallback model (routed detectors only).
        route: Whether a file goes to the model (routed detectors only).
        taus: The two models' thresholds (routed detectors only).

    Returns:
        A secml-malware CWrapperPhi instance wrapping our classifier.
    """
    import lightgbm
    from secml.array import CArray
    from secml.ml.classifiers import CClassifier
    from secml_malware.attack.blackbox.c_wrapper_phi import CWrapperPhi

    routed = fallback is not None
    if routed and (route is None or taus is None):
        raise ValueError("A routed detector needs `route` and `taus`.")

    class _OurClassifier(CClassifier):  # type: ignore[misc]
        def __init__(self) -> None:
            super().__init__()
            self._booster = lightgbm.Booster(model_file=str(model_path))
            self._fallback = lightgbm.Booster(model_file=str(fallback)) if routed else None
            self._classes = 2
            self._n_features = self._booster.num_feature() + int(routed)

        def _forward(self, x: Any) -> Any:
            X = x.atleast_2d().tondarray()
            if self._fallback is None:
                p = np.asarray(self._booster.predict(X))
            else:
                assert taus is not None
                # The last column says whether each file goes to the model (see extract_features).
                go = X[:, -1] > 0.5
                p = np.where(go, calibrated(np.asarray(self._booster.predict(X[:, :-1])), taus[0]),
                             calibrated(np.asarray(self._fallback.predict(X[:, :-1])), taus[1]))
            return CArray(np.stack([1 - p, p], axis=1))

        def _backward(self, w: Any) -> None:
            pass

        def _fit(self, x: Any, y: Any) -> None:
            raise RuntimeError("The detector under attack is not trained here.")

    class _OurWrapper(CWrapperPhi):  # type: ignore[misc]
        def extract_features(self, x: Any) -> Any:
            x = x.atleast_2d()
            out = []
            for i in range(x.shape[0]):
                xi = x[i, :]
                pad = xi.find(xi == 256)
                if pad:
                    xi = xi[0, : pad[0]]
                bytez = bytes(xi.astype(np.uint8).tolist()[0])
                v = extractor.feature_vector(bytez)  # type: ignore[no-untyped-call]
                if routed:
                    assert route is not None
                    v = np.append(v, np.float32(route(bytez)))
                out.append(v)
            return CArray(np.stack(out))

    return _OurWrapper(_OurClassifier())


################################################################################
# Attacks
################################################################################

def build_attack(name: str, wrapper: Any, section_pop: list[Any], api_calls: list[Any]) -> Any:
    """Construct one secml-malware black-box problem by name, at Gimenez et al.'s low budget.

    Args:
        name: One of ATTACKS.
        wrapper: The CWrapperPhi over our detector.
        section_pop: Goodware section contents, for the GAMMA section/shift attacks.
        api_calls: Goodware (dll, functions) pairs, for the GAMMA API attack.

    Returns:
        A secml-malware problem instance.
    """
    from secml_malware.attack.blackbox.c_black_box_format_exploit_evasion import (
        CBlackBoxContentDOSExtensionProblem,
        CBlackBoxContentShiftingEvasionProblem,
        CBlackBoxFormatExploitEvasionProblem,
    )
    from secml_malware.attack.blackbox.c_black_box_padding_evasion import CBlackBoxPaddingEvasionProblem
    from secml_malware.attack.blackbox.c_blackbox_headerfields_problem import CBlackBoxHeaderFieldsEvasionProblem
    from secml_malware.attack.blackbox.c_gamma_sections_evasion import CGammaSectionsEvasionProblem
    from secml_malware.attack.blackbox.c_gamma_shift_problem import CGammaShiftEvasionProblem
    from secml_malware.attack.blackbox.c_gammapi_evasion import CGammaAPIEvasionProblem

    builders: dict[str, Callable[[], Any]] = {
        "gamma_sections": lambda: CGammaSectionsEvasionProblem(section_pop, wrapper, population_size=10,
                                                               penalty_regularizer=1e-6, iterations=10, threshold=0),
        "gamma_api": lambda: CGammaAPIEvasionProblem(api_calls, wrapper, population_size=10, penalty_regularizer=1e-6,
                                                     iterations=10),
        "gamma_shift": lambda: CGammaShiftEvasionProblem(section_pop, wrapper, population_size=10,
                                                         penalty_regularizer=1e-6, iterations=10, threshold=0),
        "content_shift": lambda: CBlackBoxContentShiftingEvasionProblem(wrapper, population_size=10, iterations=10),
        "dos_extend": lambda: CBlackBoxContentDOSExtensionProblem(wrapper, population_size=10, iterations=10),
        "header_fields": lambda: CBlackBoxHeaderFieldsEvasionProblem(wrapper, population_size=10, iterations=10),
        "padding": lambda: CBlackBoxPaddingEvasionProblem(wrapper, population_size=10, how_many_padding_bytes=1000,
                                                          iterations=10),
        "format_exploit": lambda: CBlackBoxFormatExploitEvasionProblem(wrapper, population_size=10, iterations=10),
    }
    if name not in builders:
        raise ValueError(f"Unknown attack {name!r}; expected one of {ATTACKS}.")
    return builders[name]()


def run_attack(problem: Any, wrapper: Any, data: bytes, out_path: Path, seed: int = 0) -> tuple[bytes, float, float]:
    """Run one attack on one file; reseed first, write the result, re-score it from disk.

    Args:
        problem: A secml-malware problem instance.
        wrapper: The CWrapperPhi over our detector.
        data: The original file bytes.
        out_path: Where to write the adversarial file.
        seed: Reset the RNG to this before the search, as Gimenez et al. do.

    Returns:
        The written bytes, the clean malware probability, and the adversarial malware probability.
    """
    from secml.array import CArray
    from secml_malware.attack.blackbox.ga.c_base_genetic_engine import CGeneticAlgorithm

    random.seed(seed)
    np.random.seed(seed)
    x = CArray(np.frombuffer(data, dtype=np.uint8)).atleast_2d()
    p_clean = wrapper.predict(x, True)[1][0, 1].item()
    engine = CGeneticAlgorithm(problem)
    _, _, adv_ds, _ = engine.run(x, CArray(p_clean))
    engine.write_adv_to_file(adv_ds.X[0, :], str(out_path))
    adv_bytes = out_path.read_bytes()
    p_adv = wrapper.predict(CArray(np.frombuffer(adv_bytes, dtype=np.uint8)), True)[1][0, 1].item()
    return adv_bytes, p_clean, p_adv


################################################################################
# Pilot data
################################################################################

def load_pilot(pilot_files: Path, db_dir: Path) -> tuple[list[tuple[str, bytes]], list[tuple[str, bytes]]]:
    """The detected pilot malware and the pilot goodware, as (name, bytes) lists.

    Args:
        pilot_files: PB1's files.parquet (name, label, log_odds:gbdt).
        db_dir: The SimpleDB directory holding the bytes.

    Returns:
        (malware, goodware); malware is restricted to samples the GBDT already detects (log-odds > 0).
    """
    df = pl.read_parquet(pilot_files).select("name", "label", "log_odds:gbdt")
    reader = SimpleDBReader(SimpleDB(db_dir, check=False))
    malware = [(r["name"], bytes(reader.get(r["name"]).data))
               for r in df.filter((pl.col("label") == 1) & (pl.col("log_odds:gbdt") > 0)).iter_rows(named=True)]
    goodware = [(r["name"], bytes(reader.get(r["name"]).data))
                for r in df.filter(pl.col("label") == 0).iter_rows(named=True)]
    return malware, goodware


def build_donor_pools(goodware: list[tuple[str, bytes]], workdir: Path) -> tuple[list[Any], list[Any]]:
    """Goodware section and API-call pools for the GAMMA attacks, extracted from the pilot goodware.

    Args:
        goodware: (name, bytes) of the pilot goodware.
        workdir: A scratch directory to materialize the goodware files in (secml-malware reads from disk).

    Returns:
        (section_population, api_calls), matching Gimenez et al.'s how_many=30.
    """
    from secml_malware.attack.blackbox.c_gamma_sections_evasion import CGammaSectionsEvasionProblem
    from secml_malware.attack.blackbox.c_gammapi_evasion import CGammaAPIEvasionProblem

    gw_dir = workdir / "goodware"
    gw_dir.mkdir(parents=True, exist_ok=True)
    for name, data in goodware:
        (gw_dir / name).write_bytes(data)
    section_pop, _ = CGammaSectionsEvasionProblem.create_section_population_from_folder(
        str(gw_dir), how_many=30, sections_to_extract=[".rdata", ".data"], to_ignore=[])
    api_calls = CGammaAPIEvasionProblem.extract_api_calls_from_folder(str(gw_dir), 30)
    return section_pop, api_calls


def map_watchdog(pool: Any, fn: Callable[[Any], Any], tasks: list[Any], lost: Callable[[Any], Any],
                 stall_timeout: float = 2700.0, log_every: int = 50) -> list[Any]:
    """`pool.map(fn, tasks)` that survives a worker dying mid-task.

    A `multiprocessing.Pool` replaces a worker that dies (e.g. a segfault inside LIEF on a malformed file), but the task
    it held never returns, so `pool.map` waits forever (run 122's first launch hung this way). Here each task is
    submitted on its own; when no task has finished for `stall_timeout` seconds, the unfinished ones are reported, given
    `lost(task)` as their result, and the pool is terminated.

    Args:
        pool: An open `multiprocessing.Pool`.
        fn: The worker function.
        tasks: Its inputs, one per call.
        lost: Builds the result row for a task that never returned.
        stall_timeout: Seconds without any completion before the unfinished tasks are declared lost (longer than the
            slowest single attack).
        log_every: Print progress every this many completions.

    Returns:
        The results, in the order of `tasks`.
    """
    if stall_timeout <= 0:
        raise ValueError(f"stall_timeout must be positive, got {stall_timeout}.")
    pending = {i: pool.apply_async(fn, (t,)) for i, t in enumerate(tasks)}
    results: list[Any] = [None] * len(tasks)
    t0 = last = time.time()
    while pending:
        finished = [i for i, a in pending.items() if a.ready()]
        for i in finished:
            results[i] = pending.pop(i).get()
        done = len(tasks) - len(pending)
        if finished:
            last = time.time()
            if done // log_every != (done - len(finished)) // log_every or not pending:
                print(f"  progress: {done}/{len(tasks)} tasks in {time.time() - t0:.0f}s", flush=True)
        elif time.time() - last > stall_timeout:
            for i in pending:
                print(f"  LOST task {i} (no result after {stall_timeout:.0f}s of no progress; a worker likely died): "
                      f"{str(tasks[i][:3])[:120]}", flush=True)
                results[i] = lost(tasks[i])
            pool.terminate()
            break
        else:
            time.sleep(5)
    return results


################################################################################
# Parallel workers (one attack on one file; the detector and donor pools are per-worker globals)
################################################################################

_W: dict[str, Any] = {}


def _init_worker(model: Path, section_pop: list[Any], api_calls: list[Any], seed: int) -> None:
    """Build the per-worker extractor, detector wrapper, and donor pools once."""
    lief.logging.disable()
    extractor = merge_import_descriptors(PEFeatureExtractor())  # quirk-fixed, per docs/direction-A-mock.md check 2
    _W.update(extractor=extractor, names=extractor.feature_names, wrapper=make_wrapper(model, extractor),
              section_pop=section_pop, api_calls=api_calls, seed=seed, tmp=tempfile.mkdtemp(prefix="a_pv_w_"))


def _work(task: tuple[str, str, bytes]) -> tuple[Optional[dict[str, Any]], dict[str, Any]]:
    """Run one (attack, file): returns (delta row or None if the file was unparseable, evasion row)."""
    atk, name, data = task
    extractor, names, wrapper = _W["extractor"], _W["names"], _W["wrapper"]
    out_path = Path(_W["tmp"]) / f"{name[:16]}.{atk}"
    start = time.time()
    try:
        phi0 = extractor.feature_vector(data)
        problem = build_attack(atk, wrapper, _W["section_pop"], _W["api_calls"])
        adv_bytes, p_clean, p_adv = run_attack(problem, wrapper, data, out_path, seed=_W["seed"])
        phi1 = extractor.feature_vector(adv_bytes)
        added, ok = len(adv_bytes) - len(data), True
    except Exception as e:
        print(f"  WARN {atk} {name[:12]}: {type(e).__name__}: {str(e)[:120]}", flush=True)
        p_clean = p_adv = float("nan")
        added, ok = 0, False
    secs = time.time() - start
    evaded = bool(ok and p_adv < 0.5)
    evasion = {"name": name, "attack": atk, "evaded": evaded, "p_clean": p_clean, "p_adv": p_adv,
               "bytes_added": added, "ok": ok, "seconds": secs}
    delta: Optional[dict[str, Any]] = None
    if ok:
        delta = {"name": name, "attack": atk, "p_clean": p_clean, "p_adv": p_adv}
        delta.update({names[j]: float(phi1[j] - phi0[j]) for j in range(len(names))})
    return delta, evasion


################################################################################
# Main
################################################################################

def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--pilot_files", type=Path, default=ROOT / "artifacts/experiments/e1/seed-0/zeros/files.parquet")
    parser.add_argument("--db", type=Path, default=Path("/shared/datasets/EMBER-2024/data/ts"))
    parser.add_argument("--model", type=Path, default=ROOT / "artifacts/models/gbdt/seed-0/model.txt")
    parser.add_argument("--attacks", nargs="+", default=list(ATTACKS), choices=list(ATTACKS))
    parser.add_argument("--num_malware", type=int, default=None, help="Cap on malware files (for smoke tests).")
    parser.add_argument("--num_workers", type=int, default=8, help="Processes over (attack, file) tasks.")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    if args.num_workers < 1:
        raise ValueError(f"--num_workers must be >= 1, got {args.num_workers}.")

    lief.logging.disable()
    args.outdir.mkdir(parents=True, exist_ok=True)

    malware, goodware = load_pilot(args.pilot_files, args.db)
    if args.num_malware is not None:
        malware = malware[: args.num_malware]
    print(f"Pilot: {len(malware)} detected malware, {len(goodware)} goodware donors.", flush=True)

    with tempfile.TemporaryDirectory(prefix="a_pv_") as tmp:
        section_pop, api_calls = build_donor_pools(goodware, Path(tmp))
        print(f"Donor pools: {len(section_pop)} sections, {len(api_calls)} API groups.", flush=True)
        # One task per (attack, file); the reseed in run_attack makes each task deterministic regardless of order.
        tasks = [(atk, name, data) for atk in args.attacks for name, data in malware]
        t0 = time.time()
        ctx = get_context("spawn")
        with ctx.Pool(args.num_workers, initializer=_init_worker,
                      initargs=(args.model, section_pop, api_calls, args.seed)) as pool:
            results = pool.map(_work, tasks)
        print(f"{len(tasks)} attack runs in {time.time() - t0:.0f}s on {args.num_workers} workers.", flush=True)

    delta_rows = [d for d, _ in results if d is not None]
    evasion_rows = [e for _, e in results]
    for atk in args.attacks:
        ev = [e for e in evasion_rows if e["attack"] == atk]
        print(f"{atk}: evaded {sum(e['evaded'] for e in ev)}/{len(ev)}, "
              f"failed {sum(not e['ok'] for e in ev)}", flush=True)

    pl.DataFrame(delta_rows).write_parquet(args.outdir / "deltas.parquet")
    pl.DataFrame(evasion_rows).write_parquet(args.outdir / "evasion.parquet")
    ev = pl.DataFrame(evasion_rows)
    summary = {
        "num_malware": len(malware),
        "num_goodware_donors": len(goodware),
        "attacks": args.attacks,
        "model": str(args.model),
        "quirk_fixed_extractor": True,
        "seed": args.seed,
        "per_attack": {
            atk: {
                "evaded": int(ev.filter(pl.col("attack") == atk)["evaded"].sum()),
                "failed_files": int((~ev.filter(pl.col("attack") == atk)["ok"]).sum()),
                "seconds": float(ev.filter(pl.col("attack") == atk)["seconds"].sum()),
            }
            for atk in args.attacks
        },
    }
    (args.outdir / "summary.json").write_text(json.dumps(summary, indent=2))
    print(f"Wrote {len(delta_rows)} perturbation vectors to {args.outdir}/deltas.parquet", flush=True)


if __name__ == "__main__":
    main()
