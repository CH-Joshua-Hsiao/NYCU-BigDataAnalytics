"""A light, time-aware relational GNN over the foreign-key graph (RelBench-style).

Graph at prediction time t (leakage-safe: only rows with row-time < t):
  * node types: user, repo
  * 6 relation types user--r-->repo, one per activity (push, open_pr, open_issue,
    issue_comment, pr_review, pr_review_comment). Each edge carries its age (days before t).

Message passing is a heterogeneous GraphSAGE with **time encoding**: a neighbour's message is
weighted by exp(-age / tau), so recent interactions count more. Setting the weights to 1 gives
the "GNN without time encoding" ablation (cf. the course reference table). User embeddings feed
a 6-way multi-label head; the penultimate embeddings are also exported as features for the GBDT
(the hybrid model).

Implemented in plain PyTorch (no torch-scatter / PyG runtime needed) for reproducibility.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config as C
from . import data as D
from . import features as F

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as Fn
except Exception:
    torch = None

RELATIONS = C.ACTIVITIES            # one user->repo relation per activity


def _standardize(x, mu, sd):
    return np.clip((x - mu) / sd, -10.0, 10.0).astype("float32")


# --------------------------------------------------------------------------- graph building
def build_hetero_graph(tables, t, user_rows, node_mode="full"):
    """Return a dict of tensors describing the user/repo graph as of time t.

    node_mode="full"    : user nodes carry the engineered features (shared with the GBDT).
    node_mode="minimal" : user nodes carry only structural features (per-relation degree +
                          account age), so the temporal signal must flow through the
                          time-encoded edges -- the setup that isolates the effect of time
                          encoding (cf. the course reference table).

    repo_feat  : [R, Fr]   simple repo features
    edges[r]   : (u_idx [E], r_idx [E], age [E])  for each relation r
    user_rows  : the Users.user_id for each user node row (order of user_feat)
    """
    t = pd.Timestamp(t)
    Xu = F.build_features(tables, t, user_rows)        # indexed by user_id (used for 'full')
    user_rows = list(Xu.index)
    u_pos = {uid: i for i, uid in enumerate(user_rows)}

    # collect repos referenced by visible activity, build repo index
    rel_edges_raw = {}
    repo_set = set()
    for act in RELATIONS:
        table, actor_col, time_col, rfilt = C.ACTIVITY_SOURCE[act]
        df = D.visible_rows(tables[table], table, t)
        if rfilt == "is_real_issue":
            df = df[~df["is_pull_request"].fillna(False)]
        df = df[df[actor_col].notna() & df["repo_id"].notna() & (df[time_col] < t) & df[time_col].notna()]
        df = df[df[actor_col].astype("int64").isin(u_pos)]
        age = (t - df[time_col]) / pd.Timedelta(days=1)
        rel_edges_raw[act] = (df[actor_col].astype("int64").to_numpy(),
                              df["repo_id"].astype("int64").to_numpy(),
                              age.to_numpy().astype("float32"))
        repo_set.update(df["repo_id"].astype("int64").tolist())

    repo_rows = sorted(repo_set)
    r_pos = {rid: i for i, rid in enumerate(repo_rows)}

    edges = {}
    repo_deg = np.zeros(len(repo_rows), dtype="float32")
    for act, (us, rs, ag) in rel_edges_raw.items():
        ui = np.array([u_pos[u] for u in us], dtype="int64")
        ri = np.array([r_pos[r] for r in rs], dtype="int64")
        edges[act] = (ui, ri, ag)
        np.add.at(repo_deg, ri, 1.0)

    # simple repo features: log-degree, distinct users, age of first activity edge
    repo_feat = np.zeros((len(repo_rows), 3), dtype="float32")
    repo_feat[:, 0] = np.log1p(repo_deg)
    # distinct users per repo (across relations) and min edge age
    ucount = {i: set() for i in range(len(repo_rows))}
    minage = np.full(len(repo_rows), 180.0, dtype="float32")
    for act, (ui, ri, ag) in edges.items():
        for a_u, a_r, a_g in zip(ui, ri, ag):
            ucount[a_r].add(a_u)
            if a_g < minage[a_r]:
                minage[a_r] = a_g
    repo_feat[:, 1] = np.log1p([len(ucount[i]) for i in range(len(repo_rows))])
    repo_feat[:, 2] = np.clip(minage, 0, 180) / 180.0

    if node_mode == "minimal":
        # structural only: per-relation out-degree (how often, not when) + account age
        deg = np.zeros((len(user_rows), len(RELATIONS)), dtype="float32")
        for k, act in enumerate(RELATIONS):
            ui, _, _ = edges[act]
            np.add.at(deg[:, k], ui, 1.0)
        deg = np.log1p(deg)
        users_tbl = tables["Users"].set_index("user_id")["first_seen_at"]
        age = np.array([(t - users_tbl.get(u, t)) / pd.Timedelta(days=180) for u in user_rows], dtype="float32")
        user_feat = np.concatenate([deg, np.clip(age, 0, 1).reshape(-1, 1)], axis=1).astype("float32")
        user_cols = [f"deg_{a}" for a in RELATIONS] + ["account_age"]
    else:
        user_feat = Xu.to_numpy().astype("float32")
        user_cols = list(Xu.columns)

    return {
        "user_feat": user_feat,
        "user_cols": user_cols,
        "repo_feat": repo_feat,
        "edges": edges,
        "user_rows": user_rows,
        "repo_rows": repo_rows,
    }


# --------------------------------------------------------------------------- model
def _agg(msg, dst_idx, n_dst, weight):
    """Weighted mean of messages into each destination node. msg:[E,D] weight:[E]."""
    D_ = msg.shape[1]
    num = torch.zeros(n_dst, D_, device=msg.device)
    num.index_add_(0, dst_idx, msg * weight.unsqueeze(1))
    den = torch.zeros(n_dst, 1, device=msg.device)
    den.index_add_(0, dst_idx, weight.unsqueeze(1))
    return num / den.clamp_min(1e-6)


class TimeHeteroSAGE(nn.Module):
    """Heterogeneous time-aware GraphSAGE with a node-feature skip to the head.

    The head reads both the message-passed user embedding and a direct projection of the user's
    own features, so turning the graph off (use_graph=False) degrades gracefully to an MLP -- a
    fair baseline for isolating the graph's (relational) contribution.
    """

    def __init__(self, fu, fr, hidden=64, layers=2, n_out=6, n_rel=6):
        super().__init__()
        self.u_in = nn.Linear(fu, hidden)
        self.r_in = nn.Linear(fr, hidden)
        self.layers = layers
        self.u_self = nn.ModuleList(nn.Linear(hidden, hidden) for _ in range(layers))
        self.r_self = nn.ModuleList(nn.Linear(hidden, hidden) for _ in range(layers))
        self.u_rel = nn.ModuleList(nn.ModuleList(nn.Linear(hidden, hidden) for _ in range(n_rel)) for _ in range(layers))
        self.r_rel = nn.ModuleList(nn.ModuleList(nn.Linear(hidden, hidden) for _ in range(n_rel)) for _ in range(layers))
        self.skip = nn.Linear(fu, hidden)                       # node-feature skip
        self.head = nn.Sequential(nn.Linear(2 * hidden, hidden), nn.ReLU(), nn.Dropout(0.3),
                                  nn.Linear(hidden, n_out))

    def forward(self, g, use_time=True, use_graph=True):
        u0 = g["user_feat"]
        u = Fn.relu(self.u_in(u0))
        r = Fn.relu(self.r_in(g["repo_feat"]))
        nU, nR = u.shape[0], r.shape[0]
        if use_graph:
            for L in range(self.layers):
                u_new = self.u_self[L](u)
                r_new = self.r_self[L](r)
                for k, act in enumerate(RELATIONS):
                    ui, ri, w = g["edge_u"][k], g["edge_r"][k], g["edge_w"][k]
                    if ui.numel() == 0:
                        continue
                    wt = w if use_time else torch.ones_like(w)
                    u_new = u_new + _agg(self.u_rel[L][k](r[ri]), ui, nU, wt)
                    r_new = r_new + _agg(self.r_rel[L][k](u[ui]), ri, nR, wt)
                u = Fn.relu(u_new)
                r = Fn.relu(r_new)
        self.user_emb = u
        head_in = torch.cat([u, Fn.relu(self.skip(u0))], dim=1)   # graph emb + node-feature skip
        return self.head(head_in)


# --------------------------------------------------------------------------- train / predict
def _to_tensors(g, device, tau=14.0):
    gt = {
        "user_feat": torch.tensor(g["user_feat"], device=device),
        "repo_feat": torch.tensor(g["repo_feat"], device=device),
        "edge_u": [], "edge_r": [], "edge_w": [],
    }
    for act in RELATIONS:
        ui, ri, ag = g["edges"][act]
        gt["edge_u"].append(torch.tensor(ui, device=device, dtype=torch.long))
        gt["edge_r"].append(torch.tensor(ri, device=device, dtype=torch.long))
        gt["edge_w"].append(torch.exp(-torch.tensor(ag, device=device) / tau))
    return gt


def train_gnn(tables, train_cutoffs, val_cutoff, use_time=True, use_graph=True, epochs=150, hidden=64,
              lr=3e-3, device=None, seed=0, standardize=True, node_mode="full"):
    """Train on graphs at several cutoffs, validate on val_cutoff. Returns model + val outputs."""
    assert torch is not None, "pip install torch"
    torch.manual_seed(seed); np.random.seed(seed)
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    from . import dataset as DS, labels as L

    # build graphs + labels (skip cutoffs with no visible users, e.g. before data start)
    train = []
    for c in train_cutoffs:
        g = build_hetero_graph(tables, c, DS.cohort_users_visible(tables, c), node_mode=node_mode)
        if g["user_feat"].shape[0] == 0:
            continue
        y = L.labels_for_week(tables, c, pd.Timestamp(c) + C.WEEK, g["user_rows"])
        train.append((g, y))
    if not train:
        raise ValueError("No non-empty training graphs; cutoffs are before the data start.")
    gval = build_hetero_graph(tables, val_cutoff, DS.cohort_users_visible(tables, val_cutoff), node_mode=node_mode)
    yval = L.labels_for_week(tables, val_cutoff, pd.Timestamp(val_cutoff) + C.WEEK, gval["user_rows"])

    # standardize user features using training stats (guard zero-variance columns + clip)
    mu = sd = None
    if standardize:
        allf = np.concatenate([g["user_feat"] for g, _ in train], 0)
        mu, sd = allf.mean(0), allf.std(0)
        sd = np.where(sd < 1e-6, 1.0, sd).astype("float32")
        mu = mu.astype("float32")
        for g, _ in train:
            g["user_feat"] = _standardize(g["user_feat"], mu, sd)
        gval["user_feat"] = _standardize(gval["user_feat"], mu, sd)

    fu = train[0][0]["user_feat"].shape[1]
    fr = train[0][0]["repo_feat"].shape[1]
    model = TimeHeteroSAGE(fu, fr, hidden=hidden).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)

    tts = [( _to_tensors(g, device), torch.tensor(y.to_numpy(), dtype=torch.float32, device=device)) for g, y in train]
    gvt = _to_tensors(gval, device)

    # positive weighting for class imbalance
    posw = []
    ally = np.concatenate([y.to_numpy() for _, y in train], 0)
    for j in range(6):
        p = ally[:, j].mean()
        posw.append((1 - p) / max(p, 1e-3))
    posw = torch.tensor(posw, dtype=torch.float32, device=device).clamp(1, 8)

    model.train()
    for ep in range(epochs):
        for gt, yt in tts:
            opt.zero_grad()
            logit = model(gt, use_time=use_time, use_graph=use_graph)
            loss = Fn.binary_cross_entropy_with_logits(logit, yt, pos_weight=posw)
            loss.backward(); opt.step()

    model.eval()
    with torch.no_grad():
        val_prob = torch.sigmoid(model(gvt, use_time=use_time, use_graph=use_graph)).cpu().numpy()
    return {"model": model, "val_prob": val_prob, "val_users": gval["user_rows"],
            "y_val": yval, "mu": mu, "sd": sd, "device": device, "use_time": use_time,
            "use_graph": use_graph, "val_graph": gval, "node_mode": node_mode}


def tune_and_score(res):
    """Pick per-activity thresholds on val probabilities, return predictions + score dict."""
    from .gbdt import best_threshold, score
    yv = res["y_val"]
    pred = pd.DataFrame(index=yv.index, columns=C.ACTIVITIES, dtype="int8")
    thr = {}
    for j, act in enumerate(C.ACTIVITIES):
        t, _ = best_threshold(yv[act].to_numpy(), res["val_prob"][:, j])
        thr[act] = t
        pred[act] = (res["val_prob"][:, j] >= t).astype("int8")
    return pred, score(pred, yv), thr


def user_embeddings(res, tables, t, user_rows):
    """Export penultimate user embeddings at time t, as a DataFrame indexed by user_id (hybrid feats)."""
    g = build_hetero_graph(tables, t, user_rows, node_mode=res.get("node_mode", "full"))
    if res["mu"] is not None:
        g["user_feat"] = _standardize(g["user_feat"], res["mu"], res["sd"])
    gt = _to_tensors(g, res["device"])
    res["model"].eval()
    with torch.no_grad():
        res["model"](gt, use_time=res["use_time"], use_graph=res.get("use_graph", True))
        emb = res["model"].user_emb.cpu().numpy()
    cols = [f"gnn_emb_{i}" for i in range(emb.shape[1])]
    return pd.DataFrame(emb, index=pd.Index(g["user_rows"], name="user_id"), columns=cols)
