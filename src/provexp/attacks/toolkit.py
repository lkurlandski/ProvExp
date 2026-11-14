"""
The published toolkit attacks (secml-malware; Gimenez et al.'s eight), their budgets and donor pools, the detector
wrapper they query, per-file seeds, and the feature deltas of their outputs (for learned defenses).
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import random
from typing import Any
from typing import Callable
from typing import Optional

from numpy import typing as npt
import numpy as np
import polars as pl

from provexp.data.tabular import load_features
from provexp.data.tabular import load_manifest
from provexp.featuresets.ember2024.features import PEFeatureExtractor

__all__ = ["ATTACKS", "BUDGETS", "adv_deltas", "build_attack", "build_donor_pools", "calibrated", "file_seed",
           "make_wrapper", "pv_deltas", "run_attack"]


# The eight attacks Gimenez et al. derive PV selection from (their attack_experiment.py), at the low-budget setting
# (population 10, 10 iterations). secml-malware's genetic engine is reseeded before each run (their random.seed(0)).
ATTACKS = ("gamma_sections", "gamma_api", "gamma_shift", "content_shift", "dos_extend", "header_fields", "padding",
           "format_exploit")


# Attack budgets: (genetic iterations at population 10, donor sections/API groups). "low" is Gimenez et al.'s setting
# (~100 queries, 30 donors). "literature" is the GAMMA paper's largest (Demetrio et al., TIFS 2021: population 10, up to
# 510 queries, 75 donor sections), the budget at which GAMMA is reported to evade a GBDT on EMBER features.
BUDGETS: dict[str, tuple[int, int]] = {"low": (10, 30), "literature": (51, 75)}


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

    def _load(path: Path) -> Any:
        # NOTE: an ERDALT model directory (erdalt.json next to the given model.txt path) is scored through the same
        # predict interface; it selects its columns from the extractor's layout by name.
        from provexp.models.erdalt import is_erdalt
        from provexp.models.erdalt import load_detector

        if is_erdalt(Path(path).parent):
            return load_detector(Path(path).parent, extractor.feature_names)
        return lightgbm.Booster(model_file=str(path))

    if routed and (route is None or taus is None):
        raise ValueError("A routed detector needs `route` and `taus`.")

    class _OurClassifier(CClassifier):  # type: ignore[misc]
        def __init__(self) -> None:
            super().__init__()
            self._booster = _load(model_path)
            self._fallback = _load(fallback) if fallback is not None else None
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


def build_attack(name: str, wrapper: Any, section_pop: list[Any], api_calls: list[Any], iterations: int = 10) -> Any:
    """Construct one secml-malware black-box problem by name (population 10; Gimenez et al.'s low budget by default).

    Args:
        name: One of ATTACKS.
        wrapper: The CWrapperPhi over our detector.
        section_pop: Goodware section contents, for the GAMMA section/shift attacks.
        api_calls: Goodware (dll, functions) pairs, for the GAMMA API attack.
        iterations: Genetic iterations (queries are about 10 per iteration); see BUDGETS.

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
                                                               penalty_regularizer=1e-6, iterations=iterations, threshold=0),
        "gamma_api": lambda: CGammaAPIEvasionProblem(api_calls, wrapper, population_size=10, penalty_regularizer=1e-6,
                                                     iterations=iterations),
        "gamma_shift": lambda: CGammaShiftEvasionProblem(section_pop, wrapper, population_size=10,
                                                         penalty_regularizer=1e-6, iterations=iterations, threshold=0),
        "content_shift": lambda: CBlackBoxContentShiftingEvasionProblem(wrapper, population_size=10,
                                                                        iterations=iterations),
        "dos_extend": lambda: CBlackBoxContentDOSExtensionProblem(wrapper, population_size=10, iterations=iterations),
        "header_fields": lambda: CBlackBoxHeaderFieldsEvasionProblem(wrapper, population_size=10,
                                                                     iterations=iterations),
        "padding": lambda: CBlackBoxPaddingEvasionProblem(wrapper, population_size=10, how_many_padding_bytes=1000,
                                                          iterations=iterations),
        "format_exploit": lambda: CBlackBoxFormatExploitEvasionProblem(wrapper, population_size=10,
                                                                       iterations=iterations),
    }
    if iterations < 1:
        raise ValueError(f"iterations must be >= 1, got {iterations}.")
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


def build_donor_pools(goodware: list[tuple[str, bytes]], workdir: Path,
                      how_many: int = 30) -> tuple[list[Any], list[Any]]:
    """Goodware section and API-call pools for the GAMMA attacks, extracted from the pilot goodware.

    Args:
        goodware: (name, bytes) of the pilot goodware.
        workdir: A scratch directory to materialize the goodware files in (secml-malware reads from disk).
        how_many: Donor sections (and API groups) to extract; 30 is Gimenez et al.'s, see BUDGETS.

    Returns:
        (section_population, api_calls).
    """
    from secml_malware.attack.blackbox.c_gamma_sections_evasion import CGammaSectionsEvasionProblem
    from secml_malware.attack.blackbox.c_gammapi_evasion import CGammaAPIEvasionProblem

    gw_dir = workdir / "goodware"
    gw_dir.mkdir(parents=True, exist_ok=True)
    for name, data in goodware:
        (gw_dir / name).write_bytes(data)
    section_pop, _ = CGammaSectionsEvasionProblem.create_section_population_from_folder(
        str(gw_dir), how_many=how_many, sections_to_extract=[".rdata", ".data"], to_ignore=[])
    api_calls = CGammaAPIEvasionProblem.extract_api_calls_from_folder(str(gw_dir), how_many)
    return section_pop, api_calls


################################################################################
# Per-file seeds
################################################################################


def file_seed(seed: int, attack: str, name: str) -> int:
    """A seed per (attack, file), stable across runs and workers: the base seed plus a hash of both names."""
    h = hashlib.sha256(f"{attack}:{name}".encode()).digest()
    return (seed + int.from_bytes(h[:4], "little")) % 2**32


################################################################################
# Feature deltas of attack outputs
################################################################################


def pv_deltas(path: Path, attacks: list[str], names: list[str]) -> npt.NDArray[np.float32]:
    """The perturbation vectors of `attacks` in a named-column parquet, in the order of `names`."""
    df = pl.read_parquet(path).filter(pl.col("attack").is_in(attacks))
    missing = [n for n in names if n not in df.columns]
    if missing:
        raise ValueError(f"{path.as_posix()} lacks {len(missing)} of the model's features: {missing[:5]}")
    return df.select(names).to_numpy().astype(np.float32)


def adv_deltas(adv_dir: Path, adv_features: Path, attacks: list[str], names: list[str]) -> npt.NDArray[np.float32]:
    """phi(z') - phi(z) for the attacked training malware in `adv_dir`, clean rows from `adv_features`' training split."""
    layout = load_manifest(adv_features)["feature_names"]
    index = {n: j for j, n in enumerate(layout)}
    missing = [n for n in names if n not in index]
    if missing:
        raise ValueError(f"{adv_features.as_posix()} lacks {len(missing)} of the model's features: {missing[:5]}")
    cols = np.array([index[n] for n in names], dtype=np.int64)
    Xa = np.load(adv_dir / "X.npy")
    files = pl.read_parquet(adv_dir / "files.parquet").with_row_index("i")
    if files.height != Xa.shape[0] or Xa.shape[1] != len(layout):
        raise RuntimeError(f"{adv_dir.as_posix()}: X.npy {Xa.shape} vs {files.height} rows, {len(layout)} features.")
    files = files.filter(pl.col("attack").is_in(attacks))
    X, meta = load_features(adv_features, "tr")
    rows = dict(zip(meta["name"].to_list(), meta["row"].to_list()))
    absent = [n for n in files["name"].to_list() if n not in rows]
    if absent:
        raise RuntimeError(f"{len(absent)} attacked files are not in {adv_features.as_posix()}/tr: {absent[:3]}")
    clean = np.asarray(X[[rows[n] for n in files["name"].to_list()]])
    adv = Xa[files["i"].to_numpy()]
    out: npt.NDArray[np.float32] = (adv[:, cols] - clean[:, cols]).astype(np.float32)
    return out
