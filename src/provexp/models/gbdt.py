"""
Gradient-boosted decision trees (LightGBM) for EMBER-2024 features, configured as in SSViT.
"""

from __future__ import annotations
from typing import Any
from typing import Literal

import lightgbm as lgb
import numpy as np
from numpy import typing as npt


__all__ = [
    "EMBER2024_CATEGORICAL",
    "EMBER2024_LIGHTGBM_PARAMS",
    "train_gbdt",
]


# Indices of the categorical EMBER-2024 features: general:is_pe, general:start_byte_{0..3}, header:file_header_Machine,
# and header:optional_header_Subsystem.
EMBER2024_CATEGORICAL = [2, 3, 4, 5, 6, 701, 702]

EMBER2024_LIGHTGBM_PARAMS: dict[str, Any] = {
    "objective": "binary",
    "task": "train",
    "boosting": "gbdt",
    "num_iterations": 500,
    "learning_rate": 0.1,
    "max_depth": -1,
    "num_leaves": 64,
    "tree_learner": "serial",
    "num_threads": 0,
    "device_type": "cpu",
    "seed": 0,
    "min_data_in_leaf": 100,
    "min_sum_hessian_in_leaf": 0.001,
    "bagging_fraction": 0.9,
    "bagging_freq": 1,
    "bagging_seed": 0,
    "feature_fraction": 0.9,
    "feature_fraction_bynode": 0.9,
    "feature_fraction_seed": 0,
    "first_metric_only": True,
    "max_delta_step": 0,
    "lambda_l1": 0,
    "lambda_l2": 1,
    "verbosity": 1,
    "is_unbalance": True,
    "sigmoid": 1,
    "boost_from_average": True,
    "metric": [
        "auc",
        "binary_logloss",
        "binary_error",
    ],
}


def train_gbdt(
    X_tr: npt.NDArray[np.float32],
    y_tr: npt.NDArray[np.int64],
    X_vl: npt.NDArray[np.float32],
    y_vl: npt.NDArray[np.int64],
    seed: int = 0,
    stopper_metric: str = "auc",
    stopper_mode: Literal["max", "min"] = "max",
    categorical: bool = False,
    **params: Any,
) -> lgb.Booster:
    """
    Train a GBDT and keep the iteration with the best validation metric (`booster.best_iteration`).

    Args:
        X_tr, y_tr: The training features and labels.
        X_vl, y_vl: The validation features and labels.
        seed: Seeds every source of randomness in LightGBM.
        stopper_metric: The validation metric that selects the best iteration (one of the params' metrics).
        stopper_mode: Whether the metric should be maximized or minimized.
        categorical: Whether to treat `EMBER2024_CATEGORICAL` as categorical features, as SSViT and EMBER do.
        params: Overrides for `EMBER2024_LIGHTGBM_PARAMS`.
    """
    params = EMBER2024_LIGHTGBM_PARAMS | {"seed": seed, "bagging_seed": seed, "feature_fraction_seed": seed} | params
    if stopper_metric not in params["metric"]:
        raise ValueError(f"`stopper_metric` must be one of {params['metric']}. Got {stopper_metric}.")

    # NOTE: By default, the categorical features are treated as numeric. shap (0.52) encodes a categorical split's
    # category set as the float sum of 2^(c - 1), which is wrong for the categories above 53 that EMBER-2024's features
    # take, so interventional TreeSHAP silently explains a different model (off by up to ~5 logits).
    categorical_feature: list[int] = EMBER2024_CATEGORICAL if categorical else []
    tr = lgb.Dataset(X_tr, label=y_tr, categorical_feature=categorical_feature)
    vl = lgb.Dataset(X_vl, label=y_vl, reference=tr, categorical_feature=categorical_feature)
    history: dict[str, dict[str, list[float]]] = {}
    booster = lgb.train(
        params=params,
        train_set=tr,
        valid_sets=[vl],
        valid_names=["vl"],
        callbacks=[lgb.record_evaluation(history), lgb.log_evaluation(period=10)],
    )

    # LightGBM iterations start at 1.
    values = np.array(history["vl"][stopper_metric])
    booster.best_iteration = int(np.argmax(values) if stopper_mode == "max" else np.argmin(values)) + 1
    return booster
