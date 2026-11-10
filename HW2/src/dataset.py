"""Assemble (user, cutoff) training examples with a strict time-based split.

For each weekly cutoff t we build features as of t and labels for [t, t+7d). Stacking several
earlier weeks gives the training set; a later held-out week is the validation set. This is the
'split by time, not at random' rule from the assignment.
"""
from __future__ import annotations

from datetime import timedelta

import pandas as pd

from . import config as C
from . import data as D
from . import features as F
from . import labels as L


def cohort_users_visible(tables, t):
    """Users.user_id of cohort users whose row is visible at t (first_seen_at < t)."""
    u = tables["Users"]
    m = u["is_cohort"].fillna(False) & (u["first_seen_at"] < pd.Timestamp(t))
    return u.loc[m, "user_id"].astype("int64").tolist()


def build_examples(tables, cutoff, user_rows=None):
    """Features + labels for one cutoff. Returns (X, y) aligned on user_id."""
    if user_rows is None:
        user_rows = cohort_users_visible(tables, cutoff)
    X = F.build_features(tables, cutoff, user_rows)
    y = L.labels_for_week(tables, cutoff, pd.Timestamp(cutoff) + C.WEEK, X.index)
    X = X.assign(_cutoff=pd.Timestamp(cutoff))
    return X, y


def weekly_cutoffs(last_label_end, n_weeks, step_days=7):
    """n_weeks cutoffs ending so the last label window finishes by last_label_end.

    Returns oldest -> newest list of cutoff Timestamps.
    """
    last_cutoff = pd.Timestamp(last_label_end) - C.WEEK
    return [last_cutoff - timedelta(days=step_days * i) for i in range(n_weeks)][::-1]


def make_train_val(tables, train_cutoffs, val_cutoff):
    """Stack training weeks and build the validation week. Returns dict of frames."""
    Xtr, ytr = [], []
    for c in train_cutoffs:
        X, y = build_examples(tables, c)
        Xtr.append(X)
        ytr.append(y)
    Xtr = pd.concat(Xtr)
    ytr = pd.concat(ytr)
    Xva, yva = build_examples(tables, val_cutoff)
    feat_cols = [c for c in Xtr.columns if c != "_cutoff"]
    return {"X_train": Xtr[feat_cols], "y_train": ytr,
            "X_val": Xva[feat_cols], "y_val": yva, "feat_cols": feat_cols,
            "val_users": Xva.index}
