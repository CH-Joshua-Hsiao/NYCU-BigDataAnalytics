"""Leakage-safe per-user features at a prediction time t.

Every feature is computed from rows VISIBLE at t (row-time < t, see data.visible_rows) and
never uses a "known-only-later" column (config.FUTURE_COLUMNS). Features fall into:

  temporal  : multi-window activity counts, recency (days since last), active days, momentum
  relational: cross-table joins -- reviews/comments received on your work, distinct
              collaborators, repo/org breadth

These two groups are exactly what assignment questions Q2 (relationships) and Q3 (time) ask
about, so FEATURE_GROUPS records which columns belong to which, for ablation studies.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as C
from . import data as D

# time windows (days before t) used for count features
WINDOWS = [1, 7, 14, 30, 90]
RECENCY_CAP = 180.0          # days; also the fill value for "never did it"


def _visible_actions(tables, act, t):
    """Visible rows for an activity with columns [actor, action_time, repo_id], at time t.

    Visible = row-time < t. We additionally keep only rows whose action time is < t, so a
    feature never reflects an action in the future of t.
    """
    table, actor_col, time_col, rfilt = C.ACTIVITY_SOURCE[act]
    df = D.visible_rows(tables[table], table, t)
    if rfilt == "is_real_issue":
        df = df[~df["is_pull_request"].fillna(False)]
    cols = {actor_col: "actor", time_col: "atime"}
    keep = [actor_col, time_col] + (["repo_id"] if "repo_id" in df.columns else [])
    df = df[keep].rename(columns=cols)
    df = df[df["actor"].notna() & (df["atime"] < pd.Timestamp(t)) & df["atime"].notna()]
    df["actor"] = df["actor"].astype("int64")
    df["age"] = (pd.Timestamp(t) - df["atime"]) / pd.Timedelta(days=1)   # days before t
    return df


def build_features(tables, t, user_rows) -> pd.DataFrame:
    """Feature matrix indexed by Users.user_id (row id) for the given users, as of time t."""
    t = pd.Timestamp(t)
    idx = pd.Index(sorted(set(int(r) for r in user_rows)), name="user_id")
    feats = pd.DataFrame(index=idx)

    all_actions = []                      # (actor, age, repo_id, activity) pooled for cross-activity feats
    for act in C.ACTIVITIES:
        a = _visible_actions(tables, act, t)
        # per-window counts
        for w in WINDOWS:
            cnt = a.loc[a["age"] < w].groupby("actor").size()
            feats[f"{act}__cnt_{w}d"] = cnt.reindex(idx, fill_value=0).astype("float32")
        # recency: days since most recent occurrence (capped; large if never)
        last_age = a.groupby("actor")["age"].min()
        feats[f"{act}__recency"] = last_age.reindex(idx).fillna(RECENCY_CAP).clip(upper=RECENCY_CAP).astype("float32")
        # ever did it (in all visible history) and did-last-7d (the copy-last-week signal)
        feats[f"{act}__ever"] = a.groupby("actor").size().reindex(idx, fill_value=0).gt(0).astype("float32")
        feats[f"{act}__last7"] = feats[f"{act}__cnt_7d"].gt(0).astype("float32")
        a = a.assign(activity=act)
        all_actions.append(a)

    acts = pd.concat(all_actions, ignore_index=True) if all_actions else pd.DataFrame(
        columns=["actor", "atime", "repo_id", "age", "activity"])

    # ---- aggregate temporal features across all activity types ----
    for w in [7, 30, 90]:
        sub = acts[acts["age"] < w]
        feats[f"total__cnt_{w}d"] = sub.groupby("actor").size().reindex(idx, fill_value=0).astype("float32")
        # distinct active days
        day = (sub["age"]).astype("int32")
        ad = sub.assign(day=day).groupby("actor")["day"].nunique()
        feats[f"total__active_days_{w}d"] = ad.reindex(idx, fill_value=0).astype("float32")
        # distinct repos touched (relational breadth)
        if "repo_id" in sub.columns:
            dr = sub.dropna(subset=["repo_id"]).groupby("actor")["repo_id"].nunique()
            feats[f"rel__distinct_repos_{w}d"] = dr.reindex(idx, fill_value=0).astype("float32")

    # momentum: last 7d vs previous 7d total activity
    cur = acts[acts["age"] < 7].groupby("actor").size()
    prev = acts[(acts["age"] >= 7) & (acts["age"] < 14)].groupby("actor").size()
    cur = cur.reindex(idx, fill_value=0).astype("float32")
    prev = prev.reindex(idx, fill_value=0).astype("float32")
    feats["total__momentum_7d"] = (cur - prev)
    feats["total__ratio_7d"] = (cur + 1) / (prev + 1)

    # ---- neighborhood (repo-context) relational features ----
    # Your collaborative neighborhood's activity predicts your return. For the repos a user
    # touched recently, aggregate how active those repos are and how many other users are there.
    sub30 = acts[(acts["age"] < 30)].dropna(subset=["repo_id"]) if len(acts) else acts
    if len(sub30):
        repo_act = sub30.groupby("repo_id").size()                     # total activity per repo
        repo_usr = sub30.groupby("repo_id")["actor"].nunique()         # distinct users per repo
        ur = sub30.drop_duplicates(["actor", "repo_id"]).copy()
        ur["r_act"] = ur["repo_id"].map(repo_act)
        ur["r_usr"] = ur["repo_id"].map(repo_usr)
        gg = ur.groupby("actor")
        feats["rel__nbr_activity_30d"] = np.log1p(gg["r_act"].sum()).reindex(idx, fill_value=0).astype("float32")
        feats["rel__nbr_max_repo_act_30d"] = np.log1p(gg["r_act"].max()).reindex(idx, fill_value=0).astype("float32")
        feats["rel__nbr_collaborators_30d"] = (gg["r_usr"].sum() - gg.size()).reindex(idx, fill_value=0).clip(lower=0).astype("float32")
    else:
        for c in ["rel__nbr_activity_30d", "rel__nbr_max_repo_act_30d", "rel__nbr_collaborators_30d"]:
            feats[c] = 0.0

    # ---- relational features via cross-table joins ----
    _add_relational(tables, t, idx, feats)

    # ---- user attributes ----
    users = tables["Users"].set_index("user_id")
    first_seen = users["first_seen_at"].reindex(idx)
    feats["user__account_age_days"] = ((t - first_seen) / pd.Timedelta(days=1)).fillna(0).clip(lower=0).astype("float32")
    feats["user__is_cohort"] = users["is_cohort"].reindex(idx).fillna(False).astype("float32")
    feats["user__is_bot"] = users["is_bot"].reindex(idx).fillna(False).astype("float32")

    return feats.fillna(0.0)


def _add_relational(tables, t, idx, feats):
    """Cross-table joins: attention your work received, and whom you interacted with."""
    # reviews received on PRs you authored (last 90d, by review row-time)
    pr = D.visible_rows(tables["PullRequests"], "PullRequests", t)[["pr_id", "author_id"]]
    rv = D.visible_rows(tables["PRReviews"], "PRReviews", t)
    rv = rv[(pd.Timestamp(t) - rv["first_seen_at"]) < pd.Timedelta(days=90)]
    j = rv.merge(pr, on="pr_id", how="inner")
    recv = j.groupby("author_id").size()
    feats["rel__reviews_received_90d"] = recv.reindex(idx, fill_value=0).astype("float32")
    # distinct reviewers who reviewed your PRs (collaborator breadth)
    drev = j.dropna(subset=["reviewer_id"]).groupby("author_id")["reviewer_id"].nunique()
    feats["rel__distinct_reviewers_90d"] = drev.reindex(idx, fill_value=0).astype("float32")

    # reviews you GAVE on others' PRs (you != author) last 90d
    gave = j[j["reviewer_id"].notna() & (j["reviewer_id"] != j["author_id"])]
    feats["rel__reviews_given_90d"] = gave.groupby("reviewer_id").size().reindex(idx, fill_value=0).astype("float32")

    # comments received on issues you authored (last 90d)
    iss = D.visible_rows(tables["Issues"], "Issues", t)[["issue_id", "author_id"]]
    ic = D.visible_rows(tables["IssueComments"], "IssueComments", t)
    ic = ic[(pd.Timestamp(t) - ic["created_at"]) < pd.Timedelta(days=90)]
    ij = ic.merge(iss, on="issue_id", how="inner", suffixes=("", "_issue"))
    feats["rel__issue_comments_received_90d"] = (
        ij.groupby("author_id_issue").size().reindex(idx, fill_value=0).astype("float32"))

    # distinct repos you pushed to AND distinct orgs (org-level breadth) last 90d
    pu = D.visible_rows(tables["Pushes"], "Pushes", t)
    pu = pu[(pd.Timestamp(t) - pu["created_at"]) < pd.Timedelta(days=90)]
    repos = tables["Repositories"].set_index("repo_id")["org_id"]
    pu = pu.assign(org_id=pu["repo_id"].map(repos))
    feats["rel__distinct_push_orgs_90d"] = (
        pu.dropna(subset=["org_id"]).groupby("user_id")["org_id"].nunique().reindex(idx, fill_value=0).astype("float32"))


# which feature-name prefixes belong to which modeling story (for ablations in the report)
FEATURE_GROUPS = {
    "temporal_recency": ["__recency", "__last7", "__ever", "momentum", "ratio", "active_days"],
    "temporal_counts": ["__cnt_"],
    "relational": ["rel__"],
    "user": ["user__"],
}


def columns_for_ablation(feature_df, drop_group) -> list[str]:
    """Column list with one group removed, for leave-one-group-out experiments."""
    pats = FEATURE_GROUPS[drop_group]
    return [c for c in feature_df.columns if not any(p in c for p in pats)]
