"""Run every model on a held-out validation week and produce the report's comparison table.

Models:  all-zero, copy-last-week, GBDT, GNN (no time enc.), GNN (time enc.), Hybrid (GBDT+GNN).
Ablations: GBDT with temporal features removed (Q3) and relational features removed (Q2).

The table mirrors the course's own reference table so results are directly comparable.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as C
from . import dataset as DS
from . import baselines as B
from . import gbdt as G
from . import gnn as NN


def data_span(tables):
    mins, maxs = [], []
    for tbl in ["IssueComments", "Pushes", "PRReviewComments", "PullRequests"]:
        s = tables[tbl][C.ROW_TIME[tbl]]
        if len(s):
            mins.append(s.min()); maxs.append(s.max())
    return min(mins), max(maxs)


def choose_cutoffs(tables, n_weeks):
    """Weekly cutoffs within the data span. Training cutoffs need some prior history, so we
    keep only cutoffs at least `min_history` after the data start."""
    lo, hi = data_span(tables)
    last_end = pd.Timestamp(hi).normalize()
    cs = DS.weekly_cutoffs(last_end, n_weeks + 1)
    min_history = pd.Timestamp(lo) + pd.Timedelta(days=2)
    cs = [c for c in cs if c >= min_history]
    if len(cs) < 2:
        raise SystemExit(f"Not enough data for {n_weeks} weeks: span {lo}..{hi}. "
                         f"Download more GH Archive hours or lower --weeks.")
    return cs[:-1], cs[-1]


def _temporal_cols(cols):
    pats = ["__cnt_", "__recency", "__last7", "__ever", "momentum", "ratio", "active_days"]
    return [c for c in cols if any(p in c for p in pats)]


def _relational_cols(cols):
    return [c for c in cols if c.startswith("rel__")]


def _hybrid_frame(tables, cutoff, gnn_res):
    X, y = DS.build_examples(tables, cutoff)
    emb = NN.user_embeddings(gnn_res, tables, cutoff, X.index)
    Xh = X.drop(columns=["_cutoff"]).join(emb, how="left").fillna(0.0)
    return Xh, y


def run_all(tables, n_weeks=4, gnn_epochs=150, hidden=64, verbose=True):
    train_cutoffs, val_cutoff = choose_cutoffs(tables, n_weeks)
    if verbose:
        print(f"train cutoffs: {[str(c.date()) for c in train_cutoffs]}")
        print(f"val week: {val_cutoff.date()} .. {(val_cutoff + C.WEEK).date()}")
    d = DS.make_train_val(tables, train_cutoffs, val_cutoff)
    feat_cols = d["feat_cols"]
    rows = {}

    rows["All-zero"] = G.score(B.predict_all_zero(d["val_users"]), d["y_val"])
    rows["Copy-last-week"] = G.score(B.copy_last_week(tables, val_cutoff, d["val_users"]), d["y_val"])

    gb = G.train(d)
    rows["GBDT (all features)"] = G.score(gb["val_pred"], d["y_val"])
    # ablations
    rows["GBDT - temporal (Q3)"] = G.score(
        G.train(d, feat_cols=[c for c in feat_cols if c not in _temporal_cols(feat_cols)])["val_pred"], d["y_val"])
    rows["GBDT - relational (Q2)"] = G.score(
        G.train(d, feat_cols=[c for c in feat_cols if c not in _relational_cols(feat_cols)])["val_pred"], d["y_val"])

    # GNN ablation ladder (minimal structural node features, so the graph/time must carry the
    # signal): node-MLP -> + FK-graph message passing (Q2) -> + time-encoded edges (Q3).
    if NN.torch is not None:
        mlp = NN.train_gnn(tables, train_cutoffs, val_cutoff, use_graph=False, use_time=False,
                           epochs=gnn_epochs, hidden=hidden, node_mode="minimal")
        rows["GNN: node-MLP (no graph)"] = NN.tune_and_score(mlp)[1]
        gph = NN.train_gnn(tables, train_cutoffs, val_cutoff, use_graph=True, use_time=False,
                           epochs=gnn_epochs, hidden=hidden, node_mode="minimal")
        rows["GNN: + FK-graph (Q2)"] = NN.tune_and_score(gph)[1]
        gpt = NN.train_gnn(tables, train_cutoffs, val_cutoff, use_graph=True, use_time=True,
                           epochs=gnn_epochs, hidden=hidden, node_mode="minimal")
        rows["GNN: + time edges (Q3)"] = NN.tune_and_score(gpt)[1]

    return rows, (train_cutoffs, val_cutoff), {"gbdt": gb, "data": d}


def results_markdown(rows, meta=None) -> str:
    lines = ["| Method | macro-F1 | micro-F1 | Score |", "|---|---|---|---|"]
    for name, s in rows.items():
        lines.append(f"| {name} | {100*s['macro_f1']:.2f}% | {100*s['micro_f1']:.2f}% | {100*s['score']:.2f}% |")
    out = "\n".join(lines)
    if meta:
        tc, vc = meta
        out += (f"\n\nValidation week: {vc.date()} .. {(vc + C.WEEK).date()}  "
                f"(UTC). Training weeks: {', '.join(str(c.date()) for c in tc)}.")
    return out
