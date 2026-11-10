"""GBDT baseline: one LightGBM classifier per activity, with per-activity threshold tuning.

Score = (macro-F1 + micro-F1) / 2 (evaluate.py). We pick each activity's probability
threshold to maximise F1 on a validation week, which directly targets the metric.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as C

try:
    import lightgbm as lgb
except Exception:                       # allows import without lightgbm present
    lgb = None

DEFAULT_PARAMS = dict(
    objective="binary", n_estimators=400, learning_rate=0.03,
    num_leaves=63, min_child_samples=50, subsample=0.8, subsample_freq=1,
    colsample_bytree=0.8, reg_lambda=1.0, n_jobs=-1, verbosity=-1,
    random_state=42, deterministic=True, force_row_wise=True,   # reproducible for the TAs
)


def best_threshold(y_true, prob):
    """Threshold on `prob` that maximises F1 for one activity."""
    if y_true.sum() == 0:
        return 0.5, 0.0
    order = np.argsort(-prob)
    yt = y_true[order]
    tp = np.cumsum(yt)
    fp = np.cumsum(1 - yt)
    fn = yt.sum() - tp
    f1 = 2 * tp / np.maximum(2 * tp + fp + fn, 1)
    k = int(np.argmax(f1))
    thr = prob[order][k]
    return float(thr), float(f1[k])


def train(dataXy, params=None, feat_cols=None):
    """Train 6 models. Returns dict with models, thresholds, and val predictions/probabilities."""
    assert lgb is not None, "pip install lightgbm"
    params = {**DEFAULT_PARAMS, **(params or {})}
    Xtr, ytr = dataXy["X_train"], dataXy["y_train"]
    Xva, yva = dataXy["X_val"], dataXy["y_val"]
    cols = feat_cols or dataXy["feat_cols"]
    models, thr, proba = {}, {}, {}
    pred = pd.DataFrame(index=Xva.index, columns=C.ACTIVITIES, dtype="int8")
    for act in C.ACTIVITIES:
        m = lgb.LGBMClassifier(**params)
        pos = int(ytr[act].sum())
        if pos == 0:                     # degenerate: never seen in training weeks
            models[act] = None
            proba[act] = np.zeros(len(Xva)); thr[act] = 0.5
            pred[act] = 0
            continue
        m.fit(Xtr[cols], ytr[act])
        pv = m.predict_proba(Xva[cols])[:, 1]
        t, _ = best_threshold(yva[act].to_numpy(), pv)
        models[act] = m; proba[act] = pv; thr[act] = t
        pred[act] = (pv >= t).astype("int8")
    return {"models": models, "thresholds": thr, "val_pred": pred,
            "val_proba": proba, "feat_cols": cols}


def score(pred, truth):
    """Reproduce evaluate.py's Score = (macro-F1 + micro-F1)/2 over the 6 activities."""
    p = pred[C.ACTIVITIES].to_numpy()
    t = truth.loc[pred.index, C.ACTIVITIES].to_numpy()
    tp = ((p == 1) & (t == 1)).sum(0)
    fp = ((p == 1) & (t == 0)).sum(0)
    fn = ((p == 0) & (t == 1)).sum(0)

    def f1(a, b, c):
        return 2 * a / (2 * a + b + c) if (a + b + c) else 1.0
    per = {e: f1(tp[i], fp[i], fn[i]) for i, e in enumerate(C.ACTIVITIES)}
    macro = sum(per.values()) / len(C.ACTIVITIES)
    micro = f1(tp.sum(), fp.sum(), fn.sum())
    return {"per_event": per, "macro_f1": macro, "micro_f1": micro,
            "score": (macro + micro) / 2}
