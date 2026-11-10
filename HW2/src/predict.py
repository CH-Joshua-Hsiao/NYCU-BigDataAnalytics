"""Produce the submission file output_{studentID}.csv for the test week.

Test users are given by github_user_id. Users present in the tables get model predictions;
users absent from the tables (no visible history) are predicted all-zero.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as C
from . import data as D
from . import features as F


def predict_for_test(tables, trained, t=C.PREDICT_TIME) -> pd.DataFrame:
    """Return a submission DataFrame (UserID + 6 activity columns) for the official test users."""
    test_ids = D.test_users().astype("int64")
    u = tables["Users"]
    gid_to_row = dict(zip(u["github_user_id"].astype("int64"), u["user_id"].astype("int64")))

    present = test_ids[test_ids.isin(gid_to_row)]
    rows = [gid_to_row[g] for g in present]
    out = pd.DataFrame(0, index=test_ids.values, columns=C.ACTIVITIES, dtype="int64")

    if rows:
        X = F.build_features(tables, t, rows)
        cols = trained["feat_cols"]
        row_to_gid = {v: k for k, v in gid_to_row.items()}
        gids = [row_to_gid[r] for r in X.index]
        for act in C.ACTIVITIES:
            m = trained["models"].get(act)
            if m is None:
                continue
            prob = m.predict_proba(X[cols])[:, 1]
            pred = (prob >= trained["thresholds"][act]).astype("int64")
            out.loc[gids, act] = pred

    out.index.name = C.USER_COL
    return out.reset_index()


def write_submission(sub: pd.DataFrame, path):
    """Write with the exact header and integer values evaluate.py expects."""
    sub = sub[C.OUTPUT_COLUMNS].copy()
    sub.to_csv(path, index=False)
    return path
