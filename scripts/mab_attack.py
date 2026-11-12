"""
MAB-Malware (Song et al., AsiaCCS 2022) as a held-out attack against our detectors (meta-review 2026-11-12, R1).

FOR ACADEMIC SECURITY RESEARCH ONLY. This runs a published black-box attack against our own detectors, on our own
pilot samples, solely to evaluate defenses. No new evasion technique is developed and nothing is deployed; attacked
files are written only so they can be re-extracted and re-scored.

The attack is the authors' code (`third_party/mab_malware`, upstream at 91a518a; the patches are listed in
`third_party/README.md`): a multi-armed bandit over seven actions (append to the overlay, append to a section's slack,
add a section, rename a section, remove the certificate, remove the debug information, zero the checksum), Thompson
sampling shared across all the files of a run, at most `max_pull` actions per file (60, their default) in chains of at
most `max_length` (10), and the minimizer that strips an evasive file down to the actions it needs. Their eighth
action, code randomization, needs files randomized beforehand with IDA Pro; no such files are given, so it is never
chosen (bandit.get_next_arm picks it only when one exists). Their actions write with pefile and raw bytes, never with
LIEF.

What we change (`run_sync`, `MABChannel`): upstream runs the rewriter, the minimizer, and the classifier as three
threads that talk through files in polled folders, with sleeps between polls. Here one thread calls the same methods in
the same order, and each file is classified the moment it is handed over, so a verdict reaches upstream's code as the
same status its polled folder would have shown. The method bodies are upstream's; only the hand-over
(`Sample.copy_to_scan_folder`, `Sample.check_scan_status`) is replaced. `tests/test_mab_attack.py` checks that the
replaced hand-over gives the same run, action for action, as upstream's own folder hand-over driven in the same order.
# NOTE: upstream's threads make the order of the minimizer's steps relative to the rewriter's depend on timing; here
# the minimizer runs to completion each time the rewriter collects verdicts. This only moves when the bandit sees a
# minimized file's rewards.

One protocol with the toolkit harness (scripts/a1_evaluate.py): the same pilot malware and the same 50 goodware as
the source of added content (the toolkit attacks draw their donor sections and imports from them; MAB-Malware cuts
every section of each, as upstream's process_benign_dataset.py does); each defense's threshold at `--fpr` on its own
test predictions; only the files a defense detects are attacked; evaded means that the attack's final file (the
minimized one), read back, re-extracted, and re-scored, scores at most tau, still parses as a PE, and adds at most
max(5% of the file, 512 KB). One run per defense, so the bandit learns from one detector's verdicts at a time.

Outputs, in `{outdir}/`:
    results.parquet   one row per (defense, file), with scripts/a1_evaluate.py's columns (attack = "mab_malware") plus
                      queries (classifier calls, rewriter and minimizer), pulls, the applied and the minimal actions,
                      and whether the final file is in the population (precondition_adv)
    table.json        per defense, in scripts/a1_evaluate.py's format

Usage (smoke on two files, one defense):
    PYTHONHASHSEED=0 python scripts/mab_attack.py --outdir /tmp/mab --num_malware 2 \
        --defense ref=artifacts/models/gbdt/seed-0-s10-ref --features artifacts/features/ember2024-sums-10-v2
"""

from __future__ import annotations

from argparse import ArgumentParser
import hashlib
import json
import logging
from multiprocessing import get_context
import os
from pathlib import Path
import random
import sys
import tempfile
import time
from typing import Any
from typing import Callable
from typing import Optional

import lief
import numpy as np
import pefile
import polars as pl

from provexp.data.paths import EMBER2024_DATA
from provexp.models.erdalt import load_detector

sys.path.insert(0, str(Path(__file__).parent))
from a1_evaluate import calibrate_threshold  # noqa: E402
from a1_evaluate import group_evasion  # noqa: E402
from a1_evaluate import make_extractor  # noqa: E402
from a1_evaluate import parse_defenses  # noqa: E402
from a1_evaluate import precondition_holds  # noqa: E402
from a_pv_attacks import load_pilot  # noqa: E402

__all__ = ["MABChannel", "donor_contents", "hash_evasive", "run_sync", "trace_run", "write_config"]

ROOT = Path(__file__).resolve().parent.parent
MAB_DIR = ROOT / "third_party" / "mab_malware"
MAX_LENGTH = 4_000_000
ATTACK = "mab_malware"


################################################################################
# The run directory upstream's code works in
################################################################################

def donor_contents(goodware: list[tuple[str, bytes]], out_dir: Path) -> int:
    """
    Cut every section of every goodware file into `out_dir`, as upstream's process_benign_dataset.py does.

    Each file is named `{goodware name}|{section name}|{SizeOfRawData}` and holds the section's raw data (truncated at
    the end of the file). As upstream, a file whose sections cannot all be cut (a name that is not UTF-8 or holds a
    '/') keeps the sections cut before the failure. Unlike upstream, empty contents (sections with no raw data) are
    skipped: upstream's section-append action repeats its content until it fills a section's slack, which never ends
    for an empty one (arm.py, ArmSP.transfer), and an empty content adds nothing.

    Args:
        goodware: (name, bytes) of the donor goodware.
        out_dir: The directory to fill (upstream's data/benign_section_content/).

    Returns:
        The number of contents written.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for name, data in sorted(goodware):
        try:
            pe = pefile.PE(data=data)
            for section in pe.sections:
                offset, size = section.PointerToRawData, section.SizeOfRawData
                sname = section.Name.split(b"\0", 1)[0].decode("utf-8")
                if not data[offset: offset + size]:
                    continue  # NOTE: see the docstring (upstream's endless loop on an empty content)
                (out_dir / f"{name}|{sname}|{size}").write_bytes(data[offset: offset + size])
                count += 1
        except Exception as e:  # noqa: BLE001 (upstream catches everything per file)
            print(f"  donor {name[:12]}: {type(e).__name__}: {e}", flush=True)
    if count == 0:
        raise RuntimeError("No donor content could be cut from the goodware.")
    return count


def write_config(path: Path, max_pull: int, max_length: int) -> None:
    """Upstream's conf/configure.ini with our run's settings (classifier 'ember' selects a model scan, no sleeps)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"""[CLASSIFIER]
name = ember
scan_folder_wait_time = 600

[DATASET]
malware_folder = data/malware/
randomized_folder = data/malware.CR/
benign_content_folder  = data/benign_section_content/

[OUTPUT_FOLDER]
evasive_folder = output/evasive/
minimal_folder = output/minimal/
functional_folder = output/functional/

[REWRITER]
type = MAB

[BANDIT]
max_working_sample_count = 100
max_pull = {max_pull}
max_length = {max_length}
smallest_section_size = 512
largest_section_size = 10485760
thompson_sampling = 1
update_parent = 1

[CUCKOO]
enable = no
token = none
ori_json_folder = final_output/cuckoo_json_ori/
save_json_folder = output/cuckoo_json/
""")


def import_upstream() -> dict[str, Any]:
    """Import upstream's modules from the run directory (the current one): they read its config at import time."""
    if not Path("conf/configure.ini").exists():
        raise RuntimeError(f"No conf/configure.ini in {os.getcwd()}; call from a run directory.")
    if str(MAB_DIR) not in sys.path:
        sys.path.insert(0, str(MAB_DIR))
    import bandit  # type: ignore[import-not-found]
    import sample  # type: ignore[import-not-found]
    import samples_manager  # type: ignore[import-not-found]
    import utils  # type: ignore[import-not-found]

    utils.Utils.create_folders()
    # NOTE: upstream also echoes every action to stdout; its log files in the run directory keep the full record.
    for h in list(utils.logger_rew.handlers):
        if type(h) is logging.StreamHandler:
            utils.logger_rew.removeHandler(h)
    return {"bandit": bandit, "sample": sample, "samples_manager": samples_manager, "utils": utils}


################################################################################
# The hand-over to the classifier, and the single-threaded loop
################################################################################

class MABChannel:
    """
    Replaces upstream's polled folders: a file handed to the classifier is classified at once.

    Upstream's `Sample.copy_to_scan_folder` copies the file into a folder that a classifier thread polls; the thread
    deletes a malicious file and renames an evasive one to `*.benign`, and `Sample.check_scan_status` later reads the
    folder: `SCAN_STATUS_DELETED` (gone), `SCAN_STATUS_PASS` (renamed), or `SCAN_STATUS_WAITING`. Here the copy is
    replaced by the classification and the read by the stored verdict, which is the status the folder would show once
    the classifier thread has seen the file.
    """

    def __init__(self, upstream: dict[str, Any], score: Callable[[bytes], float], tau: float) -> None:
        self.u = upstream["utils"]
        self.score = score
        self.tau = tau
        self.queries: dict[str, dict[str, int]] = {}
        self.lowest: dict[str, float] = {}  # per sample, the lowest score any query saw (a check against no-ops)
        sample_cls = upstream["sample"].Sample
        channel = self

        def copy_to_scan_folder(s: Any, scan_folder: str) -> None:
            s.scan_status = channel.u.SCAN_STATUS_WAITING
            s.copy_time = time.time()
            data = Path(s.current_exe_path).read_bytes()
            p = channel.score(data)
            channel.lowest[s.path] = min(p, channel.lowest.get(s.path, float("inf")))
            s._verdict = channel.u.SCAN_STATUS_PASS if p <= channel.tau else channel.u.SCAN_STATUS_DELETED
            kind = "minimizer" if scan_folder == channel.u.minimizer_scan_folder else "rewriter"
            q = channel.queries.setdefault(s.path, {"rewriter": 0, "minimizer": 0})
            q[kind] += 1

        def check_scan_status(s: Any, scan_folder: str) -> int:
            verdict: int = s._verdict
            return verdict

        sample_cls.copy_to_scan_folder = copy_to_scan_folder
        sample_cls.check_scan_status = check_scan_status


def _minimize(sm: Any, u: Any, max_rounds: int = 100_000) -> list[Any]:
    """Upstream's Minimizer.run loop (Cuckoo off) until no sample is evasive; returns the samples it could not finish."""
    for _ in range(max_rounds):
        if sm.get_count_with_status(u.SAMPLE_STATUS_EVASIVE) == 0:
            return []
        sm.minimize_evasive_sample()
        sm.update_evasive_list()
    # NOTE: upstream's minimizer can loop forever on a sample whose action subset cannot be prepared (the
    # prepare_action_subset -1 path); we stop it and keep that sample's evasive file as its result.
    stuck = sm.get_samples_with_status(u.SAMPLE_STATUS_EVASIVE)
    for s in stuck:
        s.status = u.SAMPLE_STATUS_MINIMAL
        s.minimizer_stuck = True
    return list(stuck)


def run_sync(upstream: dict[str, Any]) -> tuple[Any, Any]:
    """
    Upstream's MABRewriter.run (Thompson sampling, Cuckoo off) and Minimizer.run in one thread, without sleeps.

    The rewriter's body is upstream's, line for line, except that the minimizer runs (`_minimize`) each time the
    rewriter collects verdicts (`update_working_list`), where upstream's minimizer thread would wake up.

    Returns:
        (samples manager, bandit) after the run.
    """
    u, b, smod = upstream["utils"], upstream["bandit"], upstream["samples_manager"]
    bandit = b.Bandit()
    sm = smod.SamplesManager(u.Utils.get_malware_folder(), bandit)
    sm.get_initial_pending_list()
    max_pull_count = u.Utils.get_max_pull()
    process_count = 0
    while True:
        sample = sm.get_next_sample()
        if sample:
            arm = bandit.get_next_arm(sample, sample.get_applied_actions(), rand=False)
            output_path = arm.pull(sample)
            sample.set_current_exe_path(output_path)
            sample.append_arm(arm)
            sample.copy_to_scan_folder(u.rewriter_scan_folder)
            process_count += 1
            if process_count % 100 == 0:
                sm.update_working_list()
                _minimize(sm, u)
        else:
            count_working = sm.get_count_with_status(u.SAMPLE_STATUS_WORKING)
            if count_working == 0:
                count_remain = len([x for x in sm.get_samples_with_status(u.SAMPLE_STATUS_PENDING)
                                    if x.pull_count < max_pull_count])
                if count_remain == 0:
                    break
            sm.update_working_list()
            _minimize(sm, u)
        count_skip = sm.get_count_with_status(u.SAMPLE_STATUS_SKIP)
        count_minimal = sm.get_count_with_status(u.SAMPLE_STATUS_MINIMAL)
        if count_minimal + count_skip == len(sm.list_sample):
            break
    while True:  # upstream: wait for remaining working samples to be deleted or evade
        count_working = sm.get_count_with_status(u.SAMPLE_STATUS_WORKING)
        count_evasive = sm.get_count_with_status(u.SAMPLE_STATUS_EVASIVE)
        if count_working + count_evasive == 0:
            break
        sm.update_working_list()
        _minimize(sm, u)
    for sample in sm.get_samples_with_status(u.SAMPLE_STATUS_PENDING):
        sample.delete_tmp_files(u.rewriter_output_folder)
    return sm, bandit


def final_file(sample: Any, u: Any) -> Optional[Path]:
    """The attack's output for a sample: its minimized file, else its evasive one; None if it never evaded."""
    name = Path(sample.path).name
    for folder in (u.minimal_folder, u.evasive_folder):
        found = sorted(Path(folder).glob(f"{name}*"))
        if found:
            return found[0]
    return None


def trace(sm: Any, bandit: Any) -> dict[str, Any]:
    """Everything a run decided, for comparing two runs: per sample its actions and outcome, and the bandit's state."""
    def md5(p: Optional[Path]) -> Optional[str]:
        return hashlib.md5(p.read_bytes()).hexdigest() if p is not None else None

    u = sys.modules["utils"]
    samples = {}
    for s in sm.list_sample:
        samples[Path(s.path).name] = {
            "status": s.status, "pull_count": s.pull_count,
            "applied": [a.description for a in s.list_applied_arm],
            "minimal": [a.description for a in s.list_minimal_arm],
            "final_md5": md5(final_file(s, u))}
    return {"samples": samples, "arms": [a.description for a in bandit.list_arm], "alpha": list(bandit._as),
            "beta": list(bandit._bs)}


################################################################################
# One run per defense (a fresh process each: upstream's modules hold global state)
################################################################################

def _prepare(task: dict[str, Any]) -> dict[str, bytes]:
    """Fill a run directory (config, malware, donor contents), make it the current one, and seed both generators."""
    workdir = Path(task["workdir"])
    workdir.mkdir(parents=True, exist_ok=True)
    write_config(workdir / "conf" / "configure.ini", task["max_pull"], task["max_length"])
    (workdir / "data" / "malware").mkdir(parents=True, exist_ok=True)
    originals: dict[str, bytes] = {}
    for name, data in task["malware"]:
        (workdir / "data" / "malware" / name).write_bytes(data)
        originals[name] = data
    link = workdir / "data" / "benign_section_content"
    if not link.exists():
        link.symlink_to(Path(task["donor_dir"]).resolve(), target_is_directory=True)
    os.chdir(workdir)
    random.seed(task["seed"])  # upstream's run_attack.py seeds `random` with 10; ours is the run's seed
    np.random.seed(task["seed"])  # upstream leaves NumPy's generator (Thompson sampling) unseeded
    return originals


def _run_defense(task: dict[str, Any]) -> list[dict[str, Any]]:
    """Attack every file a defense detects with one MAB-Malware run, and score each output by re-extraction."""
    lief.logging.disable()
    defense = task["defense"]
    originals = _prepare(task)
    extractor = make_extractor(Path(task["features"]))
    detector = load_detector(Path(task["model"]), extractor.feature_names)
    tau = float(task["tau"])

    def score(data: bytes) -> float:
        v = np.asarray(extractor.feature_vector(data), dtype=np.float64)  # type: ignore[no-untyped-call]
        return float(detector.predict(v.reshape(1, -1))[0])

    upstream = import_upstream()
    channel = MABChannel(upstream, score, tau)
    t0 = time.time()
    sm, _ = run_sync(upstream)
    seconds = time.time() - t0
    u = upstream["utils"]
    rows = []
    for s in sm.list_sample:
        name = Path(s.path).name
        data = originals[name]
        out = final_file(s, u)
        # ok: the attack ran and its output (if any) could be scored; a file it never evaded has no output.
        p_adv, added, ok, valid, pre_adv, error = float("nan"), 0, True, False, False, ""
        if out is not None:
            adv = out.read_bytes()
            try:
                p_adv = score(adv)
                added = len(adv) - len(data)
                valid = lief.PE.parse(list(adv)) is not None
                pre_adv = precondition_holds(adv)
            except Exception as e:  # noqa: BLE001
                ok, error = False, f"{type(e).__name__}: {str(e)[:200]}"
        cap = max(int(task["budget_frac"] * len(data)), task["budget_min"])
        q = channel.queries.get(s.path, {"rewriter": 0, "minimizer": 0})
        rows.append({
            "defense": defense, "attack": ATTACK, "name": name, "tau": tau, "p_clean": score(data), "p_adv": p_adv,
            "evaded": bool(out is not None and ok and valid and added <= cap and p_adv <= tau), "bytes_added": added,
            "over_budget": added > cap, "ok": ok, "valid": valid, "truncated": len(data) >= MAX_LENGTH,
            "precondition": precondition_holds(data), "precondition_adv": pre_adv, "error": error,
            "seconds": seconds / max(1, len(sm.list_sample)), "pulls": s.pull_count,
            "queries": q["rewriter"] + q["minimizer"], "queries_minimizer": q["minimizer"],
            "has_output": out is not None, "p_lowest": channel.lowest.get(s.path, float("nan")),
            "applied": ",".join(a.action for a in s.list_applied_arm),
            "minimal": ",".join(a.action for a in s.list_minimal_arm),
            "minimizer_stuck": bool(getattr(s, "minimizer_stuck", False))})
    print(f"  {defense}: {sum(r['evaded'] for r in rows)}/{len(rows)} evaded in {seconds:.0f}s", flush=True)
    return rows


def hash_evasive(data: bytes, modulus: int) -> bool:
    """A stand-in classifier for tests: a fixed pseudo-random verdict per file content (evasive 1 time in `modulus`)."""
    return int(hashlib.md5(data).hexdigest(), 16) % modulus == 0


def _evaluate(classifier_input: str, is_evasive: Callable[[str], bool]) -> int:
    """Upstream's Classifier.evaluate (classifier.py), logging dropped: classify the oldest file in a polled folder."""
    import glob

    set_benign_files = set(glob.glob(classifier_input + "*.benign"))
    list_file = [x for x in glob.glob(classifier_input + "*") if x not in set_benign_files]
    if len(list_file) > 0:
        list_file.sort(key=os.path.getmtime)
        file_path = list_file[0]
        if not os.path.exists(file_path):
            return 0
        if not is_evasive(file_path):
            os.system("rm %s" % file_path)
        else:
            os.system("mv %s %s.benign" % (file_path, file_path))
        return 1
    return 0


def trace_run(task: dict[str, Any]) -> dict[str, Any]:
    """
    One run with the stand-in classifier (`hash_evasive`), for tests/test_mab_attack.py.

    `task["mode"]` is "channel" (our hand-over, `MABChannel`) or "folders" (upstream's own: each file copied into the
    polled folder by upstream's `copy_to_scan_folder`, upstream's classifier step run on that folder at once, and the
    status read back by upstream's `check_scan_status`).
    """
    _prepare(task)
    upstream = import_upstream()
    modulus = int(task["modulus"])
    if task["mode"] == "channel":
        MABChannel(upstream, lambda data: 0.0 if hash_evasive(data, modulus) else 1.0, 0.5)
    elif task["mode"] == "folders":
        sample_cls = upstream["sample"].Sample
        original = sample_cls.copy_to_scan_folder

        def copy_and_classify(s: Any, scan_folder: str) -> None:
            original(s, scan_folder)
            while _evaluate(scan_folder, lambda path: hash_evasive(Path(path).read_bytes(), modulus)):
                pass

        sample_cls.copy_to_scan_folder = copy_and_classify
    else:
        raise ValueError(f"Unknown mode {task['mode']!r}.")
    sm, bandit = run_sync(upstream)
    return trace(sm, bandit)


################################################################################
# Main
################################################################################

def main() -> None:
    parser = ArgumentParser(description=__doc__.split("\n\n")[1])
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--defense", action="append", required=True, help="name=model_dir (repeatable).")
    parser.add_argument("--features", type=Path, required=True, help="The feature store the defenses were trained on.")
    parser.add_argument("--pilot_files", type=Path, default=ROOT / "artifacts/experiments/e1/seed-0/zeros/files.parquet")
    parser.add_argument("--db", type=Path, default=EMBER2024_DATA / "ts")
    parser.add_argument("--fpr", type=float, default=0.01)
    parser.add_argument("--max_pull", type=int, default=60, help="Actions per file (upstream's default).")
    parser.add_argument("--max_length", type=int, default=10, help="Actions per chain before a restart (upstream's).")
    parser.add_argument("--budget_frac", type=float, default=0.05)
    parser.add_argument("--budget_min", type=int, default=512 * 1024)
    parser.add_argument("--num_malware", type=int, default=None, help="Cap on malware files (for smoke tests).")
    parser.add_argument("--num_workers", type=int, default=8, help="Processes, one run per defense.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--workdir", type=Path, default=None, help="Where the runs' files go (default: a temporary "
                        "directory, removed at the end).")
    args = parser.parse_args()
    if args.num_workers < 1:
        raise ValueError(f"--num_workers must be >= 1, got {args.num_workers}.")

    lief.logging.disable()
    args.outdir.mkdir(parents=True, exist_ok=True)
    defenses = parse_defenses(args.defense)
    extractor = make_extractor(args.features)
    malware, goodware = load_pilot(args.pilot_files, args.db)
    if args.num_malware is not None:
        malware = malware[: args.num_malware]
    print(f"Pilot: {len(malware)} malware, {len(goodware)} goodware donors; {len(defenses)} defenses.", flush=True)

    X = np.stack([extractor.feature_vector(data) for _, data in malware])  # type: ignore[no-untyped-call]
    taus: dict[str, float] = {}
    detected: dict[str, list[int]] = {}
    for d, mdir in defenses.items():
        pred = pl.read_parquet(mdir / "ts_predictions.parquet")
        taus[d] = calibrate_threshold(pred["prob"].to_numpy(), pred["label"].to_numpy(), args.fpr)
        p = np.asarray(load_detector(mdir, extractor.feature_names).predict(X))
        detected[d] = [i for i in range(len(malware)) if p[i] > taus[d]]
        print(f"  {d}: tau={taus[d]:.4f}, detects {len(detected[d])}/{len(malware)}", flush=True)

    with tempfile.TemporaryDirectory(prefix="mab_") as tmp:
        root = args.workdir.resolve() if args.workdir is not None else Path(tmp)
        donor_dir = root / "benign_section_content"
        print(f"Donor contents: {donor_contents(goodware, donor_dir)} sections of {len(goodware)} goodware.",
              flush=True)
        tasks = [{"defense": d, "model": str(m.resolve()), "features": str(args.features.resolve()), "tau": taus[d],
                  "malware": [malware[i] for i in detected[d]], "donor_dir": str(donor_dir),
                  "workdir": str(root / d), "seed": args.seed, "max_pull": args.max_pull,
                  "max_length": args.max_length, "budget_frac": args.budget_frac, "budget_min": args.budget_min}
                 for d, m in defenses.items() if detected[d]]
        t0 = time.time()
        with get_context("spawn").Pool(min(args.num_workers, max(1, len(tasks))), maxtasksperchild=1) as pool:
            rows = [r for part in pool.imap_unordered(_run_defense, tasks) for r in part]
        print(f"{len(tasks)} runs in {time.time() - t0:.0f}s.", flush=True)

    if not rows:
        raise RuntimeError("No defense detects any pilot malware; nothing to attack.")
    results = pl.DataFrame(rows)
    results.write_parquet(args.outdir / "results.parquet")
    table: dict[str, Any] = {"protocol": {"attack": ATTACK, "fpr": args.fpr, "max_pull": args.max_pull,
                                          "max_length": args.max_length, "budget_frac": args.budget_frac,
                                          "budget_min": args.budget_min, "seed": args.seed,
                                          "features": args.features.resolve().as_posix(), "routes": {}},
                             "defenses": {}}
    for d in defenses:
        r = results.filter(pl.col("defense") == d)
        entry: dict[str, Any] = {"model": defenses[d].as_posix(), "tau": taus[d], "detected": len(detected[d]),
                                 "per_attack": {}, "groups": {}}
        if r.height:
            entry["per_attack"][ATTACK] = {
                "runs": r.height, "evaded": int(r["evaded"].sum()), "failed": int((~r["ok"]).sum()),
                "over_budget": int(r["over_budget"].sum()), "invalid": int((r["has_output"] & r["ok"] & ~r["valid"]).sum()),
                "evaded_outside_population": int((r["evaded"] & ~r["precondition_adv"]).sum()),
                "queries_median": float(r["queries"].median() or 0)}  # type: ignore[arg-type]
            entry["groups"]["all"] = {
                "all": group_evasion(r, [ATTACK]),
                "precondition": group_evasion(r.filter(pl.col("precondition")), [ATTACK]),
                "no_precondition": group_evasion(r.filter(~pl.col("precondition")), [ATTACK]),
                "uncapped": group_evasion(r.with_columns(evaded=pl.col("has_output") & pl.col("ok") & pl.col("valid")
                                                         & (pl.col("p_adv") <= pl.col("tau"))), [ATTACK])}
        table["defenses"][d] = entry
        print(f"{d:16s} detected {len(detected[d]):2d}  {entry['per_attack'].get(ATTACK)}", flush=True)
    (args.outdir / "table.json").write_text(json.dumps(table, indent=2))
    print(f"Wrote {args.outdir}/results.parquet and table.json", flush=True)


if __name__ == "__main__":
    main()
