"""
The published toolkit attacks (secml-malware; Gimenez et al.'s eight), their budgets and donor pools, the detector
wrapper they query, per-file seeds, and the feature deltas of their outputs (for learned defenses).
"""

from __future__ import annotations

import hashlib
from itertools import islice
from pathlib import Path
import random
from typing import Any
from typing import Callable
from typing import Iterable
from typing import Optional
from typing import Sequence

from numpy import typing as npt
import numpy as np
import polars as pl

from provexp.data.tabular import load_features
from provexp.data.tabular import load_manifest
from provexp.featuresets.ember2024.features import PEFeatureExtractor

__all__ = ["ATTACKS", "BUDGETS", "GAMMA_ATTACKS", "NotApplicable", "adv_deltas", "build_attack", "build_donor_pools",
           "calibrated", "file_seed", "gamma_room", "gamma_start", "make_wrapper", "pv_deltas", "run_attack"]


# The eight attacks Gimenez et al. derive PV selection from (their attack_experiment.py), at the low-budget setting
# (population 10, 10 iterations). secml-malware's genetic engine is reseeded before each run (their random.seed(0)).
ATTACKS = ("gamma_sections", "gamma_api", "gamma_shift", "content_shift", "dos_extend", "header_fields", "padding",
           "format_exploit")


# Attack budgets: (genetic iterations at population 10, donor sections/API groups). "low" is Gimenez et al.'s setting
# (~100 queries, 30 donors). "literature" is the GAMMA paper's largest (Demetrio et al., TIFS 2021: population 10, up to
# 510 queries, 75 donor sections), the budget at which GAMMA is reported to evade a GBDT on EMBER features.
BUDGETS: dict[str, tuple[int, int]] = {"low": (10, 30), "literature": (51, 75)}

# The GAMMA attacks whose edits our byte-level writers make (session 103; user, session 101): secml-malware's search,
# unchanged, with each query's sections or imports written by `catalogue.write_section` / `write_import_libraries`
# instead of LIEF's rebuild, which moves structures outside the threat model (docs/evidence/gamma-lief-relayout.md).
GAMMA_ATTACKS = ("gamma_sections", "gamma_api")


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
    from secml_malware.attack.blackbox.c_gamma_shift_problem import CGammaShiftEvasionProblem

    sections_problem, api_problem = _gamma_problems()
    builders: dict[str, Callable[[], Any]] = {
        "gamma_sections": lambda: sections_problem(section_pop, wrapper, population_size=10, penalty_regularizer=1e-6,
                                                   iterations=iterations, threshold=0),
        "gamma_api": lambda: api_problem(api_calls, wrapper, population_size=10, penalty_regularizer=1e-6,
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
# GAMMA through our writers
################################################################################


class NotApplicable(RuntimeError):
    """The attack's edit cannot be written on this file (the headers have no room, even after growing them)."""


def gamma_start(attack: str, z: bytes, donors: int) -> tuple[Optional[bytes], str]:
    """
    The file a GAMMA attack writes into, and how: the file itself if its headers hold the new section headers the
    attack writes on every query (one per donor section for `gamma_sections`; one import section for `gamma_api`), else
    the file after the smallest header growth that makes room (`catalogue.grow_headers_for`, `hgr`), else None: the
    attack is not applicable (decided, user, session 103).

    Args:
        attack: One of GAMMA_ATTACKS.
        z: The file the attack starts from.
        donors: The donor sections (the section population's size; ignored for `gamma_api`).

    Returns:
        (start bytes, "fits" or "grown"), or (None, the reason the attack is not applicable).
    """
    from provexp.featuresets.ember2024.catalogue import grow_headers_for
    from provexp.featuresets.ember2024.catalogue import section_slots

    if attack not in GAMMA_ATTACKS:
        raise ValueError(f"gamma_start: {attack!r} is not one of {GAMMA_ATTACKS}.")
    need = donors if attack == "gamma_sections" else 1
    if need < 1:
        raise ValueError(f"gamma_start: {attack} needs at least one donor, got {donors}.")
    have = section_slots(z, need)
    if have >= need:
        return z, "fits"
    grown = grow_headers_for(z, need)
    if grown is None:
        return None, f"room for {have} of {need} section headers, and growing the headers does not make room"
    return grown.new, "grown"


def _room(job: tuple[bytes, tuple[str, ...], int]) -> dict[str, Optional[str]]:
    """`gamma_start`'s verdict per attack for one file: None if applicable, else the reason."""
    z, attacks, donors = job
    return {a: (None if start is not None else how) for a in attacks for start, how in [gamma_start(a, z, donors)]}


def gamma_room(starts: Iterable[bytes], attacks: Sequence[str], donors: int,
               workers: int) -> list[dict[str, Optional[str]]]:
    """
    For each start file, whether each GAMMA attack of `attacks` applies to it (`gamma_start`): None, or the reason it
    does not. The checks run in a pool of `workers` processes.

    Args:
        starts: The files the attacks start from.
        attacks: The attacks to check (those not in GAMMA_ATTACKS are ignored).
        donors: The donor sections of the section population.
        workers: Processes.

    Returns:
        One {attack: None or reason} per start file, in order.
    """
    from multiprocessing import get_context

    if workers < 1:
        raise ValueError(f"workers must be >= 1, got {workers}.")
    which = tuple(a for a in attacks if a in GAMMA_ATTACKS)
    files = iter(starts)
    out: list[dict[str, Optional[str]]] = []
    if not which:
        return [{} for _ in files]
    with get_context("spawn").Pool(workers) as pool:
        # In batches, so that a long iterable (a reader's generator) is not held in memory at once.
        while batch := [(z, which, donors) for z in islice(files, 64 * workers)]:
            out += pool.map(_room, batch, chunksize=4)
    return out


def structure_kept(start: bytes, out: bytes, sections: int, imports: bool) -> Optional[str]:
    """
    Whether a GAMMA output kept the start file's structure (an assertion on our writers): the start file's bytes past
    its headers unchanged (section bodies and overlay), new bytes only appended, the existing section headers unchanged,
    `sections` headers added, and every data directory unchanged but the IMPORT entry when `imports`.

    Returns:
        None if kept, else what changed.
    """
    import pefile

    from provexp.featuresets.ember2024.catalogue import section_table_end

    a = pefile.PE(data=start, fast_load=True)
    b = pefile.PE(data=out, fast_load=True)
    head = a.OPTIONAL_HEADER.SizeOfHeaders
    if len(out) < len(start) or out[head:len(start)] != start[head:]:
        return "bytes past the headers changed"
    if b.FILE_HEADER.NumberOfSections != a.FILE_HEADER.NumberOfSections + sections:
        return f"{b.FILE_HEADER.NumberOfSections - a.FILE_HEADER.NumberOfSections} section headers added, not {sections}"
    first = a.DOS_HEADER.e_lfanew + 24 + a.FILE_HEADER.SizeOfOptionalHeader
    end = section_table_end(a)
    if out[first:end] != start[first:end]:
        return "an existing section header changed"
    for i, (da, db) in enumerate(zip(a.OPTIONAL_HEADER.DATA_DIRECTORY, b.OPTIONAL_HEADER.DATA_DIRECTORY)):
        if (da.VirtualAddress, da.Size) != (db.VirtualAddress, db.Size) and not (imports and i == 1):
            return f"data directory {i} changed"
    return None


def _as_bytes(x: Any) -> bytes:
    """A secml-malware sample (a CArray of byte values) as bytes."""
    return bytes(np.asarray(x.tondarray()).astype(np.uint8).ravel())


def _as_sample(z: bytes) -> Any:
    """Bytes as a secml-malware sample (a 1 x n CArray of byte values)."""
    from secml.array import CArray

    return CArray(np.frombuffer(z, dtype=np.uint8).astype(np.int64)).atleast_2d()


_GAMMA_CLASSES: list[Any] = []


def _gamma_problems() -> tuple[Any, Any]:
    """secml-malware's two GAMMA problems with their edits written by our writers (classes built once, lazily)."""
    if _GAMMA_CLASSES:
        return _GAMMA_CLASSES[0], _GAMMA_CLASSES[1]
    import pefile
    from secml_malware.attack.blackbox.c_gamma_sections_evasion import CGammaSectionsEvasionProblem
    from secml_malware.attack.blackbox.c_gammapi_evasion import CGammaAPIEvasionProblem

    from provexp.featuresets.ember2024.catalogue import write_import_libraries
    from provexp.featuresets.ember2024.catalogue import write_section

    class Sections(CGammaSectionsEvasionProblem):  # type: ignore[misc]
        """GAMMA's section injection: every donor section, cut to its gene, as a new section after the overlay."""

        start_: bytes = b""
        header_growth: bool = False

        def init_starting_point(self, x: Any) -> Any:
            original = super().init_starting_point(x)
            start, how = gamma_start("gamma_sections", _as_bytes(original), self.latent_space_size)
            if start is None:
                raise NotApplicable(how)
            self.start_, self.header_growth = start, how == "grown"
            return original

        def apply_feasible_manipulations(self, t: Any, x: Any) -> Any:
            z = self.start_
            for i in range(self.latent_space_size):
                content = self.section_population[i]
                # NOTE: characteristics 0, as LIEF writes GAMMA's sections (it sets none); `sec` lets the attacker
                # choose them. Sections go after the overlay (before_overlay=False), as the adaptive search writes them.
                written = write_section(z, self.names_[i].encode(), bytes(content[:int(t[i] * len(content))]), 0,
                                        before_overlay=False)
                if written is None:
                    raise RuntimeError(f"gamma_sections: no room for section {i + 1} of {self.latent_space_size}, "
                                       "although the start file was checked.")
                z = written.new
            why = structure_kept(self.start_, z, self.latent_space_size, imports=False)
            if why is not None:
                raise RuntimeError(f"gamma_sections: the output lost structure: {why}.")
            return _as_sample(z)

    class Api(CGammaAPIEvasionProblem):  # type: ignore[misc]
        """GAMMA's API injection: each donor library's functions, cut to its gene, in one new import section."""

        start_: bytes = b""
        header_growth: bool = False
        imported_: dict[str, set[str]]

        def init_starting_point(self, x: Any) -> Any:
            original = super().init_starting_point(x)
            start, how = gamma_start("gamma_api", _as_bytes(original), 1)
            if start is None:
                raise NotApplicable(how)
            self.start_, self.header_growth = start, how == "grown"
            pe = pefile.PE(data=start, fast_load=True)
            pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]])
            self.imported_ = {}
            for entry in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []):
                names = {f.name.decode(errors="replace") for f in entry.imports if f.name}
                self.imported_.setdefault(entry.dll.decode(errors="replace").lower(), set()).update(names)
            return original

        def apply_feasible_manipulations(self, t: Any, x: Any) -> Any:
            # As secml-malware's _add_import: a function the library already has (in the file, or added by an earlier
            # gene of this query) is not added again.
            added: dict[str, tuple[str, list[str]]] = {}
            for i in range(t.shape[-1]):
                dll, functions = self.api_list[i]
                have = self.imported_.get(dll.lower(), set())
                for f in functions[:int(len(functions) * t[i])]:
                    # NOTE: an import by ordinal has no name (LIEF gives ""); it is skipped.
                    if not f or f in have:
                        continue
                    lib = added.setdefault(dll.lower(), (dll, []))
                    if f not in lib[1]:
                        lib[1].append(f)
            if not added:
                return _as_sample(self.start_)
            written = write_import_libraries(self.start_, [(dll.encode(), [f.encode() for f in fs])
                                                           for dll, fs in added.values()], before_overlay=False)
            if written is None:
                raise RuntimeError("gamma_api: no room for the import section, although the start file was checked.")
            why = structure_kept(self.start_, written.new, 1, imports=True)
            if why is not None:
                raise RuntimeError(f"gamma_api: the output lost structure: {why}.")
            return _as_sample(written.new)

    _GAMMA_CLASSES.extend([Sections, Api])
    return Sections, Api


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
