"""Reference baselines, for the report's comparison table.

copy_last_week is the strong, simple baseline named in the assignment README
(Score 49.61% on their held-out week): predict 1 for an activity iff the user did it in the
7 days before the prediction time.
"""
from __future__ import annotations

import pandas as pd

from . import config as C
from . import features as F


def copy_last_week(tables, t, user_rows) -> pd.DataFrame:
    """1 if the user performed the activity in [t-7d, t) among rows visible at t."""
    feats = F.build_features(tables, t, user_rows)
    pred = pd.DataFrame(index=feats.index, columns=C.ACTIVITIES, dtype="int8")
    for act in C.ACTIVITIES:
        pred[act] = feats[f"{act}__last7"].astype("int8")
    return pred


def predict_all_zero(user_rows) -> pd.DataFrame:
    idx = pd.Index(sorted(set(int(r) for r in user_rows)), name="user_id")
    return pd.DataFrame(0, index=idx, columns=C.ACTIVITIES, dtype="int8")
