"""End-to-end orchestration for the GBDT pipeline.

    python run.py evaluate   # build weeks, train GBDT, report val Score vs baselines
    python run.py predict    # train on recent weeks, write output_{SID}.csv for the test week
    python run.py smoke      # quick sanity check on whatever data is in data/db

Run from the HW2/ folder with the venv's python.
"""
from __future__ import annotations

import argparse
import sys

import pandas as pd

try:                                   # Windows consoles default to a non-UTF-8 codepage
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from src import config as C
from src import data as D
from src import dataset as DS
from src import baselines as B
from src import gbdt as G

STUDENT_ID = "413551034"


def effective_predict_time(tables):
    """The feature cutoff for the final prediction.

    Ideally the test-week start (config.PREDICT_TIME). But data only exists up to 'now'; if the
    newest row-time is before PREDICT_TIME, use the last complete midnight instead and warn.
    Re-running near the deadline with fresh data picks up PREDICT_TIME automatically.
    """
    from src.experiments import data_span
    _, hi = data_span(tables)
    hi = pd.Timestamp(hi)
    if hi >= C.PREDICT_TIME:
        return C.PREDICT_TIME
    cutoff = hi.normalize()
    print(f"[warn] data ends {hi}; test week starts {C.PREDICT_TIME}. "
          f"Using {cutoff} as the feature cutoff. Re-run near the deadline for fresh data.")
    return cutoff


def _data_span(tables):
    """(min row-time, max row-time) across the activity tables -- the usable data span."""
    mins, maxs = [], []
    for tbl in ["IssueComments", "Pushes", "PRReviewComments"]:
        s = tables[tbl][C.ROW_TIME[tbl]]
        if len(s):
            mins.append(s.min()); maxs.append(s.max())
    return min(mins), max(maxs)


def cmd_smoke(args):
    tables = D.load_tables()
    for name, df in tables.items():
        print(f"  {name:18s} {len(df):>8,} rows")
    lo, hi = _data_span(tables)
    print(f"data span (row-time): {lo} .. {hi}")
    tu = D.test_users()
    present = tu.isin(set(tables['Users']['github_user_id']))
    print(f"test users: {len(tu)}, present in tables: {int(present.sum())}")


def cmd_evaluate(args):
    tables = D.load_tables()
    lo, hi = _data_span(tables)
    print(f"data span: {lo} .. {hi}")
    # last complete label week ends at `hi` (floored to midnight to be safe)
    last_end = pd.Timestamp(hi).normalize()
    cutoffs = DS.weekly_cutoffs(last_end, n_weeks=args.weeks + 1)
    train_cutoffs, val_cutoff = cutoffs[:-1], cutoffs[-1]
    print(f"train cutoffs: {[str(c.date()) for c in train_cutoffs]}")
    print(f"val cutoff:    {val_cutoff.date()}  (labels {val_cutoff.date()} .. {(val_cutoff + C.WEEK).date()})")

    d = DS.make_train_val(tables, train_cutoffs, val_cutoff)
    print(f"train rows: {len(d['X_train']):,}  val rows: {len(d['X_val']):,}  features: {len(d['feat_cols'])}")
    print("label rates (val):", {a: round(float(d['y_val'][a].mean()), 3) for a in C.ACTIVITIES})

    # baselines
    clw = B.copy_last_week(tables, val_cutoff, d["val_users"])
    s_clw = G.score(clw, d["y_val"])
    s_zero = G.score(B.predict_all_zero(d["val_users"]), d["y_val"])
    # GBDT
    res = G.train(d)
    s_gbdt = G.score(res["val_pred"], d["y_val"])

    print("\n=== Validation Score = (macro-F1 + micro-F1)/2 ===")
    for name, s in [("all-zero", s_zero), ("copy-last-week", s_clw), ("GBDT", s_gbdt)]:
        print(f"  {name:16s} macro {100*s['macro_f1']:5.2f}  micro {100*s['micro_f1']:5.2f}  Score {100*s['score']:5.2f}")
    print("\nGBDT per-activity F1:", {a: round(100 * v, 1) for a, v in s_gbdt["per_event"].items()})


def cmd_predict(args):
    from src import predict as P
    tables = D.load_tables()
    lo, hi = _data_span(tables)
    last_end = pd.Timestamp(hi).normalize()
    cutoffs = DS.weekly_cutoffs(last_end, n_weeks=args.weeks + 1)
    train_cutoffs, val_cutoff = cutoffs[:-1], cutoffs[-1]
    d = DS.make_train_val(tables, train_cutoffs, val_cutoff)
    res = G.train(d)
    s = G.score(res["val_pred"], d["y_val"])
    print(f"val Score {100*s['score']:.2f}% (macro {100*s['macro_f1']:.2f}, micro {100*s['micro_f1']:.2f})")
    sub = P.predict_for_test(tables, res, t=effective_predict_time(tables))
    out = C.ROOT / f"output_{STUDENT_ID}.csv"
    P.write_submission(sub, out)
    print("wrote", out, "rows:", len(sub), "positives/col:", {a: int(sub[a].sum()) for a in C.ACTIVITIES})


def cmd_full(args):
    """Run every model + ablations, save artifacts/results.md, and write the submission."""
    from src import experiments as E
    from src import predict as P
    tables = D.load_tables()
    rows, meta, extra = E.run_all(tables, n_weeks=args.weeks, gnn_epochs=args.epochs)
    table = E.results_markdown(rows, meta)
    print("\n" + table)
    C.ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    (C.ARTIFACT_DIR / "results.md").write_text(table + "\n", encoding="utf-8")
    # machine-readable metrics for charts / slides
    import json
    tc, vc = meta
    metrics = {"val_week": [str(vc.date()), str((vc + C.WEEK).date())],
               "train_weeks": [str(c.date()) for c in tc],
               "methods": {name: {"macro_f1": s["macro_f1"], "micro_f1": s["micro_f1"],
                                  "score": s["score"], "per_event": s["per_event"]}
                           for name, s in rows.items()}}
    (C.ARTIFACT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print("\nwrote", C.ARTIFACT_DIR / "results.md", "and metrics.json")
    # submission from the reliable GBDT model
    sub = P.predict_for_test(tables, extra["gbdt"], t=effective_predict_time(tables))
    out = C.ROOT / f"output_{STUDENT_ID}.csv"
    P.write_submission(sub, out)
    print("wrote", out, "positives/col:", {a: int(sub[a].sum()) for a in C.ACTIVITIES})


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("smoke")
    pe = sub.add_parser("evaluate"); pe.add_argument("--weeks", type=int, default=3)
    pp = sub.add_parser("predict"); pp.add_argument("--weeks", type=int, default=3)
    pf = sub.add_parser("full"); pf.add_argument("--weeks", type=int, default=4); pf.add_argument("--epochs", type=int, default=150)
    args = ap.parse_args()
    {"smoke": cmd_smoke, "evaluate": cmd_evaluate, "predict": cmd_predict, "full": cmd_full}[args.cmd](args)


if __name__ == "__main__":
    main()
