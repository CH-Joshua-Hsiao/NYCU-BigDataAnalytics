"""Build the 6 binary activity labels for any week, for any set of users.

A label answers: did user u perform activity a during [week_start, week_end)?
It is derived from the ACTION time (created_at / submitted_at) of the row, using the
fully-populated tables -- this is how the ground truth for a week is defined. (Leakage is a
concern only for *features*, which look at the state as of the prediction time; see
features.py / data.visible_rows.)
"""
from __future__ import annotations

import pandas as pd

from . import config as C


def _actor_did(tables, table, actor_col, time_col, w_start, w_end, row_filter=None):
    """Set of user row-ids (the actor column's value) that performed the activity in the window."""
    df = tables[table]
    if row_filter == "is_real_issue":          # open_issue: real issues, not PR conversations
        df = df[~df["is_pull_request"].fillna(False)]
    t = df[time_col]
    m = (t >= pd.Timestamp(w_start)) & (t < pd.Timestamp(w_end)) & df[actor_col].notna()
    return set(df.loc[m, actor_col].astype("int64"))


def labels_for_week(tables, w_start, w_end, user_rows) -> pd.DataFrame:
    """A DataFrame indexed by Users.user_id (row id) with a 0/1 column per activity.

    user_rows: iterable of Users.user_id (row numbers) to produce labels for.
    """
    user_rows = list(user_rows)
    out = pd.DataFrame(0, index=pd.Index(user_rows, name="user_id"),
                       columns=C.ACTIVITIES, dtype="int8")
    for act, (table, actor_col, time_col, rfilt) in C.ACTIVITY_SOURCE.items():
        did = _actor_did(tables, table, actor_col, time_col, w_start, w_end, rfilt)
        out[act] = out.index.isin(did).astype("int8")
    return out


def labels_by_github_id(tables, w_start, w_end, github_ids) -> pd.DataFrame:
    """Same as labels_for_week but keyed by github_user_id (the test-file UserID).

    Users absent from the tables get all-zero labels (they did nothing in-window).
    """
    u = tables["Users"]
    gid_to_row = dict(zip(u["github_user_id"], u["user_id"]))
    github_ids = list(github_ids)
    rows = [gid_to_row[g] for g in github_ids if g in gid_to_row]
    lab = labels_for_week(tables, w_start, w_end, rows)
    row_to_gid = dict(zip(u["user_id"], u["github_user_id"]))
    lab.index = [row_to_gid[r] for r in lab.index]
    lab = lab.reindex(github_ids, fill_value=0)
    lab.index.name = C.USER_COL
    return lab
