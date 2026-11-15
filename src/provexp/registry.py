"""
Plain names for the detectors and attacks of the evaluation, in one place.

A detector name maps to its model directory and the feature store it reads, per model set: `pilot` (the models the
pilot results come from, under artifacts/models/) and `scaleup` ($OUT_ROOT/4-detectors/<name>, every detector on the
store of the re-encoding over sums except the expert set; OUT_ROOT defaults to artifacts/scaleup, as in
pipeline/common.sh). The run.sh scripts name detectors and ask this module for the paths:

    python -m provexp.registry defenses --set pilot unconstrained monotone-sums
    # --defense unconstrained=artifacts/models/gbdt/seed-0-s10-ref --defense monotone-sums=...

The attacks: the toolkit attacks by their secml-malware names, `adaptive` (our beam search), `mab-malware`, and the
escapes (single field writes outside the threat model, applied before the adaptive search).
"""

from __future__ import annotations

from argparse import ArgumentParser
import os
from typing import NamedTuple

from provexp.attacks.toolkit import ATTACKS as TOOLKIT_ATTACKS
from provexp.featuresets.ember2024.escapes import WRITES

__all__ = ["DESCRIPTIONS", "ESCAPES", "MODEL_SETS", "SOUND", "TOOLKIT_ATTACKS", "Detector", "defense_args", "detector",
           "scaleup_models"]


class Detector(NamedTuple):
    """A trained detector: its model directory and the feature store it reads."""

    model: str
    features: str


# What each detector is (the paper's names, §5).
DESCRIPTIONS: dict[str, str] = {
    "unconstrained": "GBDT on every feature, no constraint",
    "monotone-features": "GBDT monotone in the derived directions of the features",
    "monotone-sums": "GBDT monotone in the derived directions of the re-encoding over sums",
    "additions-only": "monotone-sums for the threat model of additions only",
    "adversarial-training": "GBDT retrained on toolkit-attacked training malware",
    "pv": "Gimenez et al.'s PV: features the toolkit attacks move dropped",
    "erdalt": "Gimenez et al.'s ERDALT",
    "expert-set": "monotone GBDT on Gimenez et al.'s 40 expert features",
    "trial": "GBDT monotone in directions learned by trying the operations",
    "iterated-1": "adversarial-training retrained on the adaptive search's outputs, one round (`ent` held out)",
    "iterated-2": "the same, two rounds (Table 4's iterated adversarial training)",
    **{f"pv-loo-{a}": f"PV selected without {a} (leave-one-out, Table 10)" for a in TOOLKIT_ATTACKS},
    **{f"erdalt-loo-{a}": f"ERDALT trained without {a} (leave-one-out, Table 10)" for a in TOOLKIT_ATTACKS},
}

# The detectors that carry the guarantee (monotone in directions derived from the extractor): a score below the clean
# score under an edit in the threat model is a bug, reported as a soundness violation by the adaptive search.
SOUND = ("monotone-features", "monotone-sums", "additions-only")

_M = "artifacts/models"
_S10 = "artifacts/features/ember2024-sums-10-v2"


def scaleup_models(root: str) -> dict[str, Detector]:
    """The scale-up's detectors under `root` (pipeline/4-detectors/train and adversarial-training write them)."""
    sums, expert = f"{root}/2-features/sums", f"{root}/2-features/expert"
    return {name: Detector(f"{root}/4-detectors/{name}", expert if name == "expert-set" else sums)
            for name in DESCRIPTIONS}


MODEL_SETS: dict[str, dict[str, Detector]] = {
    # The pilot's models (sessions up to 63): Table 5's detectors on the 10% sums store, the learned defenses of §5.3.
    "pilot": {
        "unconstrained": Detector(f"{_M}/gbdt/seed-0-s10-ref", _S10),
        "monotone-features": Detector(f"{_M}/gbdt/seed-0-s10-mfull-feat-loose", _S10),
        "monotone-sums": Detector(f"{_M}/gbdt/seed-0-s10-mfull-sums-loose", _S10),
        "additions-only": Detector(f"{_M}/gbdt/seed-0-s10-madd-sums-pre-v2", _S10),
        "adversarial-training": Detector(f"{_M}/gbdt/seed-0-advtrain-seedperfile", "artifacts/features/ember2024"),
        "pv": Detector(f"{_M}/gbdt/seed-0-s10-pv-best", "artifacts/features/ember2024-sums-10"),
        "erdalt": Detector(f"{_M}/erdalt/seed-0-s10-best", _S10),
        "expert-set": Detector(f"{_M}/gbdt/seed-0-s10-expert-mono", "artifacts/features/ember2024-expert-10"),
        "trial": Detector(f"{_M}/gbdt/seed-0-s10-mfull-feat-trial", _S10),
    },
    # The scale-up's (session 68): the full training split's complete files, thresholds on the validation split.
    "scaleup": scaleup_models(os.environ.get("OUT_ROOT", "artifacts/scaleup")),
}

ESCAPES = tuple(WRITES)


def detector(name: str, model_set: str = "pilot") -> Detector:
    """The detector called `name` in `model_set`."""
    if model_set not in MODEL_SETS:
        raise ValueError(f"Unknown model set {model_set!r}; known: {sorted(MODEL_SETS)}.")
    if name not in MODEL_SETS[model_set]:
        raise ValueError(f"Unknown detector {name!r} in {model_set!r}; known: {sorted(MODEL_SETS[model_set])}.")
    return MODEL_SETS[model_set][name]


def defense_args(names: list[str], model_set: str = "pilot") -> list[str]:
    """The `--defense name=model_dir` arguments of the attack scripts, for `names`."""
    features = {detector(n, model_set).features for n in names}
    if len(features) > 1:
        raise ValueError(f"The detectors read different feature stores and cannot share one run: {sorted(features)}.")
    out: list[str] = []
    for n in names:
        out += ["--defense", f"{n}={detector(n, model_set).model}"]
    return out


def main() -> None:
    parser = ArgumentParser(description="Print the paths behind detector names.")
    sub = parser.add_subparsers(dest="command", required=True)
    d = sub.add_parser("defenses", help="--defense name=model_dir arguments")
    f = sub.add_parser("features", help="the feature store the detectors read")
    s = sub.add_parser("sound", help="those of the names that carry the guarantee")
    for p in (d, f, s):
        p.add_argument("--set", default="pilot", choices=sorted(MODEL_SETS))
        p.add_argument("names", nargs="+")
    args = parser.parse_args()
    if args.command == "defenses":
        print(" ".join(defense_args(args.names, args.set)))
    elif args.command == "features":
        defense_args(args.names, args.set)  # the same-store check
        print(detector(args.names[0], args.set).features)
    else:
        print(" ".join(n for n in args.names if n in SOUND))


if __name__ == "__main__":
    main()
