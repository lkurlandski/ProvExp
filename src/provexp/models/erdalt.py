"""
ERDALT (Gimenez et al., "Certifiably robust malware detectors by design"): a learned linear post-processing under a
monotone network, trained so that every observed perturbation vector maps to a nonnegative vector.

A port of `train_model.py` in https://github.com/PFGimenez/certifiably-robust-malware-detectors-by-design (the
"M_monotonic" configuration), following the paper where the two differ:

- The paper's Proposition 3 needs every layer above the linear post-processing to be monotone. The released code
  projects the negative weights of the two hidden layers to small positive values (`exp(w - 5)`) but leaves the output
  layer free, so the network is not monotone. We project the output layer too (`docs/upstream-issues.md`, item 8).
- Their training uses batches of 16 for 310 epochs and selects the epoch on the test split. On EMBER-2024 that is
  millions of steps, so the batch size and epoch count are parameters here, and the epoch is selected on the
  validation split with their criterion: fewer than 5 negative entries of the post-processed perturbation vectors,
  then the highest ROC-AUC.

Everything else is theirs: standardized inputs (perturbation vectors divided by the standard deviation, not centered),
a square linear layer without bias initialized to the identity, hidden layers of 800 with ELU and dropout 0.5/0.5/0.4,
Adam at 1e-4 with ReduceLROnPlateau on the validation ROC-AUC (factor 0.5, patience 20), and the loss
w1 * BCE + w2 * sum(relu(-L delta)) + w3 * ||L off the diagonal||_F with w1: 0.5 -> 1, w2: 0.5 -> 200, w3: 0.5 -> 1
linearly over the epochs.
"""

from __future__ import annotations
from collections.abc import Sequence
import json
from pathlib import Path
from typing import Any
from typing import Optional

import numpy as np
from numpy import typing as npt
from sklearn.metrics import roc_auc_score
import torch
from torch import nn
from torch import Tensor
from torch.nn import functional as F

from provexp.models.mlp import Standardize
from provexp.models.mlp import fit_standardize


__all__ = [
    "ERDALT",
    "ERDALTDetector",
    "project_monotone",
    "num_violations",
    "train_erdalt",
    "save_erdalt",
    "load_erdalt",
    "is_erdalt",
    "fit_temperature",
    "fit_quantile_scale",
    "loss_weights",
    "pv_mask",
    "load_detector",
]


################################################################################
# Model
################################################################################

class ERDALT(nn.Module):
    """
    Standardize, a square linear layer without bias (the post-processing g), then a monotone MLP (f o h).

    `forward` returns the malware logit; `post` returns the post-processed features L(standardize(x)), and `post_delta`
    the post-processed perturbation vector L(delta / std), which is post(x + delta) - post(x).
    """

    def __init__(self, standardize: Standardize, hidden: int = 800, monotone_output: bool = True) -> None:
        super().__init__()
        self.monotone_output = monotone_output
        d = int(standardize.mean.shape[0])  # type: ignore[index]
        self.standardize = standardize
        self.layer1 = nn.Linear(d, d, bias=False)
        self.layer2 = nn.Linear(d, hidden)
        self.layer3 = nn.Linear(hidden, hidden)
        self.fc4 = nn.Linear(hidden, 1)
        self.dropout1 = nn.Dropout(0.5)
        self.dropout2 = nn.Dropout(0.5)
        self.dropout3 = nn.Dropout(0.4)
        for layer in (self.layer2, self.layer3, self.fc4):
            nn.init.xavier_uniform_(layer.weight)
            nn.init.constant_(layer.bias, 0.1)
        with torch.no_grad():
            self.layer1.weight.copy_(torch.eye(d))

    def post(self, x: Tensor) -> Tensor:
        return self.layer1(self.standardize(x))  # type: ignore[no-any-return]

    def post_delta(self, delta: Tensor) -> Tensor:
        return self.layer1(delta / self.standardize.std)  # type: ignore[no-any-return,operator]

    def forward(self, x: Tensor) -> Tensor:
        h = self.dropout1(F.elu(self.post(x)))
        h = self.dropout2(F.elu(self.layer2(h)))
        h = self.dropout3(F.elu(self.layer3(h)))
        return self.fc4(h).squeeze(-1)  # type: ignore[no-any-return]


@torch.no_grad()
def project_monotone(model: ERDALT) -> None:
    """Replace each negative weight w above the post-processing with exp(w - 5) > 0 (theirs, plus the output layer
    unless `model.monotone_output` is False, as in their released code)."""
    layers = (model.layer2, model.layer3, model.fc4) if model.monotone_output else (model.layer2, model.layer3)
    for layer in layers:
        w = layer.weight
        w.copy_(torch.where(w < 0, torch.exp(w - 5.0), w))


@torch.no_grad()
def num_violations(model: ERDALT, deltas: Tensor, batch_size: int = 1024) -> int:
    """The number of negative entries of the post-processed perturbation vectors (their `check_M_char`)."""
    return int(sum(int((model.post_delta(deltas[i:i + batch_size]) < 0).sum())
                   for i in range(0, deltas.shape[0], batch_size)))


################################################################################
# Training
################################################################################

def fit_quantile_scale(X: npt.NDArray[np.float32], q: float = 0.9999, rows: int = 200_000, seed: int = 0) -> Standardize:
    """
    The training mean, and per feature the larger of the standard deviation and the `q` quantile of |x - mean| (on a
    seeded draw of at most `rows` rows). A diagnosis option: the map stays linear, so ERDALT's guarantee holds, but
    on heavy-tailed features nearly every standardized value lands within +-1 instead of reaching |z| ~ 1e5. Never
    below the std, so no value grows: on a sparse feature the quantile can be |mean|, far below the std.
    """
    if not 0 < q <= 1:
        raise ValueError(f"q must be in (0, 1], got {q}.")
    base = fit_standardize(X)
    mean = base.mean.double().numpy()  # type: ignore[operator]
    std = base.std.double().numpy()  # type: ignore[operator]
    idx = np.arange(X.shape[0])
    if X.shape[0] > rows:
        idx = np.sort(np.random.default_rng(seed).choice(X.shape[0], rows, replace=False))
    dev = np.abs(np.asarray(X[idx], dtype=np.float64) - mean).astype(np.float32)  # NOTE: float32 halves the copy
    scale = np.quantile(dev, q, axis=0).astype(np.float64)
    scale = np.maximum(scale, std)
    return Standardize(torch.from_numpy(mean), torch.from_numpy(scale))


def pv_mask(deltas: npt.NDArray[np.float32]) -> npt.NDArray[np.bool_]:
    """The features no perturbation vector lowers (PV's selection): L = diag(mask) maps every vector to >= 0."""
    return np.asarray((deltas >= 0).all(axis=0), dtype=np.bool_)


@torch.no_grad()
def _logits(model: nn.Module, X: Tensor, batch_size: int = 8192) -> Tensor:
    model.eval()
    return torch.cat([model(X[i:i + batch_size]) for i in range(0, X.shape[0], batch_size)])


def loss_weights(t: float, n_schedule: int, penalty_scale: float = 1.0) -> tuple[float, float, float]:
    """
    The loss weights (w1, w2, w3) at position `t` (in epochs) of their linear schedule over `n_schedule` epochs.

    w1: 0.5 -> 1, w2: 0.5 -> 200 (times `penalty_scale`), w3: 0.5 -> 1, reaching the end value at epoch
    `n_schedule - 1` (as `np.linspace(a, b, n_schedule)` at whole epochs) and holding it after.

    Args:
        t: The position in epochs; whole numbers give their per-epoch values, fractions interpolate between them.
        n_schedule: The schedule's length in epochs.
        penalty_scale: A factor on w2.

    Returns:
        (w1, w2, w3).
    """
    if n_schedule < 1:
        raise ValueError(f"n_schedule must be positive, got {n_schedule}.")
    if t < 0:
        raise ValueError(f"t must be nonnegative, got {t}.")
    f = min(t / (n_schedule - 1), 1.0) if n_schedule > 1 else 0.0
    w1, w2, w3 = (a + (b - a) * f for a, b in ((0.5, 1.0), (0.5, 200.0), (0.5, 1.0)))
    return w1, w2 * penalty_scale, w3


def train_erdalt(
    X_tr: npt.NDArray[np.float32],
    y_tr: npt.NDArray[np.int64],
    X_vl: npt.NDArray[np.float32],
    y_vl: npt.NDArray[np.int64],
    deltas: npt.NDArray[np.float32],
    seed: int = 0,
    device: torch.device = torch.device("cuda"),
    hidden: int = 800,
    batch_size: int = 256,
    epochs: int = 310,
    learning_rate: float = 1e-4,
    delta_batch: int = 4096,
    max_violations: int = 5,
    deltas_per_step: Optional[int] = None,
    schedule_epochs: Optional[int] = None,
    monotone_output: bool = True,
    lr_scheduler: bool = True,
    penalty_scale: float = 1.0,
    post_init: str = "identity",
    freeze_post: bool = False,
    deltas_subsample: Optional[int] = None,
    input_scale: str = "std",
    schedule_per_step: bool = False,
) -> tuple[ERDALT, dict[str, Any]]:
    """
    Train ERDALT and keep the epoch with the best validation ROC-AUC among those with < `max_violations` violations.

    Args:
        X_tr, y_tr, X_vl, y_vl: Raw features and labels (1 = malware).
        deltas: The observed perturbation vectors phi(z') - phi(z), raw (unstandardized), one per row.
        delta_batch: Perturbation vectors per penalty term; all of them enter every step (their code takes up to 152
            batches of 16, i.e. all of theirs), split only to bound memory.
        deltas_per_step: If given, each step's penalty sums over a fresh random draw of this many perturbation vectors
            instead of all of them (their code: at most 152 batches of 16, 2,432 per step, from a shuffled loader).
        schedule_epochs: The length of the loss weights' linear schedule (default `epochs`); a longer one with fewer
            `epochs` runs the start of the full schedule (diagnosis runs).
        monotone_output: Project the output layer to be monotone too (ours); False leaves it free (their code).
        lr_scheduler: Halve the learning rate after 20 epochs without a better validation ROC-AUC (theirs).
        penalty_scale: A factor on the violation penalty's weight w2 throughout (1.0: theirs; diagnosis runs).
        post_init: "identity" (theirs) or "pv": L starts as diag(PV's mask over all of `deltas`), zero on every
            feature some vector lowers, so that it starts with no violation (diagnosis).
        freeze_post: Keep L at its initial value; only the network above it trains (diagnosis).
        deltas_subsample: Train on a fixed seeded draw of this many of `deltas` (diagnosis: fewer observed vectors);
            the violations over all of them are logged too (`violations_all`), the ones the model never saw.
        input_scale: "std" (theirs) or "quantile" (`fit_quantile_scale`; diagnosis).
        schedule_per_step: Interpolate the loss weights linearly within each epoch, from this epoch's value to the
            next's, instead of holding them for the whole epoch (theirs). Same endpoints; it matters on short
            schedules, where the per-epoch jumps are large (`loss_weights`).

    Returns:
        The model (eval mode, on `device`) and a training summary (selected epoch, its ROC-AUC and violations, and
        whether any epoch met the violation criterion).
    """
    if penalty_scale <= 0:
        raise ValueError(f"penalty_scale must be positive, got {penalty_scale}.")
    if post_init not in ("identity", "pv"):
        raise ValueError(f"post_init must be 'identity' or 'pv', got {post_init!r}.")
    if input_scale not in ("std", "quantile"):
        raise ValueError(f"input_scale must be 'std' or 'quantile', got {input_scale!r}.")
    if deltas_subsample is not None and not 0 < deltas_subsample <= deltas.shape[0]:
        raise ValueError(f"deltas_subsample must be in [1, {deltas.shape[0]}], got {deltas_subsample}.")
    if deltas.ndim != 2 or deltas.shape[1] != X_tr.shape[1]:
        raise ValueError(f"deltas has shape {deltas.shape}, expected (*, {X_tr.shape[1]}).")
    torch.manual_seed(seed)
    generator = torch.Generator().manual_seed(seed)

    standardize = fit_standardize(X_tr) if input_scale == "std" else fit_quantile_scale(X_tr, seed=seed)
    model = ERDALT(standardize, hidden, monotone_output).to(device)
    if post_init == "pv":
        keep = torch.from_numpy(pv_mask(deltas).astype(np.float32)).to(device)
        with torch.no_grad():
            model.layer1.weight.copy_(torch.diag(keep))
        print(f"L starts at PV's mask: {int(keep.sum())} of {keep.shape[0]} features kept.", flush=True)
    if freeze_post:
        model.layer1.weight.requires_grad_(False)
    D_all: Optional[Tensor] = None
    if deltas_subsample is not None and deltas_subsample < deltas.shape[0]:
        D_all = torch.from_numpy(np.ascontiguousarray(deltas, dtype=np.float32)).to(device)
        rows = np.sort(np.random.default_rng(seed).choice(deltas.shape[0], deltas_subsample, replace=False))
        deltas = deltas[rows]
        print(f"Training on a seeded {deltas.shape[0]} of the {D_all.shape[0]} perturbation vectors.", flush=True)
    Xtr = torch.from_numpy(np.ascontiguousarray(X_tr)).to(device)
    ytr = torch.from_numpy(y_tr.astype(np.float32)).to(device)
    Xvl = torch.from_numpy(np.ascontiguousarray(X_vl)).to(device)
    D = torch.from_numpy(np.ascontiguousarray(deltas, dtype=np.float32)).to(device)
    mask = 1.0 - torch.eye(Xtr.shape[1], device=device)

    optimizer = torch.optim.Adam([p for p in model.parameters() if p.requires_grad], lr=learning_rate)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=20)
    n_schedule = epochs if schedule_epochs is None else schedule_epochs
    if n_schedule < epochs:
        raise ValueError(f"schedule_epochs ({n_schedule}) is shorter than epochs ({epochs}).")
    steps_per_epoch = -(-Xtr.shape[0] // batch_size)

    best: Optional[tuple[bool, float, int, int]] = None  # (meets criterion, roc, -violations, epoch)
    best_state: Optional[dict[str, Tensor]] = None
    history = []
    for epoch in range(epochs):
        model.train()
        order = torch.randperm(Xtr.shape[0], generator=generator).to(device)
        for step, i in enumerate(range(0, Xtr.shape[0], batch_size)):
            idx = order[i:i + batch_size]
            t = epoch + step / steps_per_epoch if schedule_per_step else float(epoch)
            w1, w2, w3 = loss_weights(t, n_schedule, penalty_scale)
            l1 = F.binary_cross_entropy_with_logits(model(Xtr[idx]), ytr[idx])
            l2 = torch.zeros((), device=device)
            Ds = D
            if deltas_per_step is not None and deltas_per_step < D.shape[0]:
                Ds = D[torch.randperm(D.shape[0], generator=generator)[:deltas_per_step].to(device)]
            for j in range(0, Ds.shape[0], delta_batch):
                l2 = l2 + F.relu(-model.post_delta(Ds[j:j + delta_batch])).sum()
            l3 = torch.sqrt(torch.sum((model.layer1.weight * mask) ** 2) + 1e-16)
            loss = w1 * l1 + w2 * l2 + w3 * l3
            optimizer.zero_grad(set_to_none=True)
            loss.backward()  # type: ignore[no-untyped-call]
            optimizer.step()
            project_monotone(model)
        roc = float(roc_auc_score(y_vl, _logits(model, Xvl).cpu().numpy()))
        viol = num_violations(model, D)
        lr = float(optimizer.param_groups[0]["lr"])
        if lr_scheduler:
            scheduler.step(roc)
        record: dict[str, Any] = {"epoch": epoch, "vl_roc": roc, "violations": viol, "l1": float(l1.detach()),
                                  "l2": float(l2.detach()), "l3": float(l3.detach()), "lr": lr}
        extra = ""
        if D_all is not None:
            record["violations_all"] = num_violations(model, D_all)
            extra = f" violations_all={record['violations_all']}"
        history.append(record)
        print(f"epoch={epoch} vl_roc={roc:.5f} violations={viol}{extra} l1={float(l1.detach()):.4g} "
              f"l2={float(l2.detach()):.4g} l3={float(l3.detach()):.4g} lr={lr:.3g}", flush=True)
        key = (viol < max_violations, roc if viol < max_violations else -viol, -viol, epoch)
        if best is None or key[:3] > best[:3]:
            best = key
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}

    assert best is not None and best_state is not None
    model.load_state_dict(best_state)
    model.eval()
    summary = {"epoch": best[3], "vl_roc": history[best[3]]["vl_roc"], "violations": history[best[3]]["violations"],
               "met_criterion": best[0], "num_deltas": int(D.shape[0]), "batch_size": batch_size, "epochs": epochs,
               "learning_rate": learning_rate, "hidden": hidden, "max_violations": max_violations,
               "deltas_per_step": deltas_per_step, "schedule_epochs": n_schedule, "monotone_output": monotone_output,
               "lr_scheduler": lr_scheduler, "penalty_scale": penalty_scale, "post_init": post_init,
               "freeze_post": freeze_post, "deltas_subsample": deltas_subsample, "input_scale": input_scale,
               "schedule_per_step": schedule_per_step,
               "num_deltas_all": int(D_all.shape[0]) if D_all is not None else int(D.shape[0]),
               "history": history}
    if not best[0]:
        print(f"WARNING: no epoch has < {max_violations} violations; kept epoch {best[3]} (fewest).", flush=True)
    return model, summary


def fit_temperature(logits: npt.NDArray[np.floating], bound: float = 30.0) -> float:
    """
    The smallest temperature >= 1 that keeps every given logit within +-`bound` after division.

    The monotone network's logits reach the hundreds (unbounded standardized inputs through nonnegative weights and
    ELUs), so sigmoid(logit) is exactly 1.0 for many files, even in float64. Ties at 1.0 would put the 1% FPR
    threshold at 1.0 and give the black-box attacks a flat score, overstating robustness. Dividing by a constant
    changes neither the ranking nor any thresholded decision.
    """
    m = float(np.max(np.abs(logits))) if np.size(logits) else 0.0
    return max(1.0, m / bound)


################################################################################
# Persistence and scoring
################################################################################

def save_erdalt(model: ERDALT, outdir: Path, feature_names: Sequence[str], summary: dict[str, Any]) -> None:
    """Write `model.pt` (the state dict) and `erdalt.json` (the input features, in order, and the configuration)."""
    outdir.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), outdir / "model.pt")
    config = {"feature_names": list(feature_names), "hidden": summary["hidden"],
              "temperature": float(summary.get("temperature", 1.0)),
              "training": {k: v for k, v in summary.items() if k != "history"}}
    (outdir / "erdalt.json").write_text(json.dumps(config, indent=2))


def is_erdalt(mdir: Path) -> bool:
    """Whether a model directory holds an ERDALT model (else a LightGBM `model.txt`)."""
    return (Path(mdir) / "erdalt.json").exists()


class ERDALTDetector:
    """
    An ERDALT model behind the `predict` interface of a LightGBM booster: raw feature rows in, malware probabilities
    out (float64), on the CPU in one thread per process.

    Rows may be in the model's own feature layout, or in a wider layout (a feature store with extra columns), whose
    `feature_names` select the model's columns by name.
    """

    def __init__(self, mdir: Path, feature_names: Optional[Sequence[str]] = None) -> None:
        config = json.loads((Path(mdir) / "erdalt.json").read_text())
        self.feature_names: list[str] = config["feature_names"]
        d = len(self.feature_names)
        state = torch.load(Path(mdir) / "model.pt", map_location="cpu", weights_only=True)
        std = Standardize(state["standardize.mean"], state["standardize.std"])
        monotone_output = bool(config["training"].get("monotone_output", True)) if "training" in config else True
        self.model = ERDALT(std, int(config["hidden"]), monotone_output)
        self.model.load_state_dict(state)
        self.model.eval()
        self.width = d
        self.temperature = float(config.get("temperature", 1.0))
        self.columns: Optional[npt.NDArray[np.int64]] = None
        if feature_names is not None and list(feature_names) != self.feature_names:
            index = {name: j for j, name in enumerate(feature_names)}
            missing = [n for n in self.feature_names if n not in index]
            if missing:
                raise ValueError(f"{len(missing)} of the model's features are not in the given layout: {missing[:5]}")
            self.columns = np.array([index[n] for n in self.feature_names], dtype=np.int64)
            self.width = len(feature_names)

    def _select(self, data: Any) -> Tensor:
        x = np.asarray(data, dtype=np.float32)
        if x.ndim != 2:
            raise ValueError(f"Expected a 2-D array, got shape {x.shape}.")
        if x.shape[1] == len(self.feature_names):
            pass
        elif self.columns is not None and x.shape[1] == self.width:
            x = x[:, self.columns]
        else:
            raise ValueError(f"Rows have {x.shape[1]} features; the model takes {len(self.feature_names)}"
                             f"{f' or {self.width}' if self.columns is not None else ''}.")
        return torch.from_numpy(np.ascontiguousarray(x))

    def num_feature(self) -> int:
        """The row width `predict` accepts in the given layout (LightGBM's name)."""
        return self.width

    def logit(self, data: Any) -> npt.NDArray[np.float64]:
        torch.set_num_threads(1)
        with torch.no_grad():
            return np.asarray(self.model(self._select(data)).double().numpy(), dtype=np.float64)

    def predict(self, data: Any, *args: Any, **kwargs: Any) -> npt.NDArray[np.float64]:
        """sigmoid(logit / temperature): the temperature (`fit_temperature`) only rescales, so every ranking and
        threshold decision is the model's, but the probability does not saturate at 1.0 (see `fit_temperature`)."""
        z = self.logit(data) / self.temperature
        return np.asarray(1.0 / (1.0 + np.exp(-z)))

    def sensitivity(self, data: Any) -> npt.NDArray[np.float64]:
        """Mean |d logit / d x_j| * std_j over the rows (a white-box per-feature importance), in the model's layout."""
        x = self._select(data).requires_grad_(True)
        self.model(x).sum().backward()
        assert x.grad is not None
        g = x.grad.abs().mean(dim=0) * self.model.standardize.std  # type: ignore[operator]
        return np.asarray(g.double().numpy(), dtype=np.float64)

    def post_weight(self) -> npt.NDArray[np.float64]:
        """L in raw feature units (L diag(1/std)): column j is how the post-processed features move per unit of x_j."""
        w = self.model.layer1.weight.detach() / self.model.standardize.std  # type: ignore[operator]
        return np.asarray(w.double().numpy(), dtype=np.float64)


def load_erdalt(mdir: Path, feature_names: Optional[Sequence[str]] = None) -> ERDALTDetector:
    """Load an ERDALT model directory for scoring (see `ERDALTDetector`)."""
    if not is_erdalt(mdir):
        raise ValueError(f"{Path(mdir).as_posix()} has no erdalt.json.")
    return ERDALTDetector(mdir, feature_names)



def load_detector(mdir: Path, feature_names: Optional[Sequence[str]] = None) -> Any:
    """A model directory's detector with LightGBM's `predict`: ERDALT if it has erdalt.json, else `model.txt`."""
    if is_erdalt(mdir):
        return ERDALTDetector(mdir, feature_names)
    import lightgbm

    return lightgbm.Booster(model_file=str(Path(mdir) / "model.txt"))
