# Predicting GitHub User Activity (Big Data Analytics, Fall 2026 — Assignment 2)

Repository: <https://github.com/CH-Joshua-Hsiao/NYCU-BigDataAnalytics/tree/main/HW2>

Predict, for each test user, which of 6 activities they will perform on GitHub during the test
week **2026/11/22 00:00 – 11/29 00:00 (Taiwan time)**:
`open_pr, open_issue, issue_comment, pr_review, pr_review_comment, push`.

The model reads the 8 relational tables built by the official `preprocess.py` from
[GH Archive](https://www.gharchive.org) and predicts the 6 binary targets per user. It combines
a **gradient-boosted-tree** model over leakage-safe relational + temporal features (the reliable
baseline) with a **light relational GNN** (RelBench-style message passing over the foreign-key
graph) whose user embeddings are fused back into the trees.

## Data Source

The data used in this assignment is sourced from **[GH Archive](https://www.gharchive.org)**, a
publicly available archive of GitHub events. This project is for educational use within this
course only and respects users' privacy: all ids and text are anonymized by the course's
`preprocess.py` before any modeling.

## Repository layout

```
HW2/
├── README.md                 # this file
├── requirements.txt          # pinned Python dependencies
├── run.py                    # end-to-end: evaluate / predict / smoke
├── src/
│   ├── config.py             # paths, the 6 activities, time windows, leakage rules
│   ├── data.py               # load the 8 tables; visible-rows (row-time < t) helper
│   ├── labels.py             # build the 6 activity labels for any week
│   ├── features.py           # leakage-safe relational + temporal per-user features
│   ├── dataset.py            # assemble (user, cutoff) examples; time-based split
│   ├── baselines.py          # copy-last-week, all-zero
│   ├── gbdt.py               # 6 LightGBM models + per-activity threshold tuning
│   ├── gnn.py                # light heterogeneous temporal GNN (PyTorch Geometric)
│   └── predict.py            # write output_{studentID}.csv for the test week
├── tools/
│   ├── download_raw.sh       # download GH Archive hour files for a date range
│   ├── schema_graph.py       # Q1 schema graph (Graphviz .dot)
│   └── schema_graph_mpl.py   # Q1 schema graph rendered with matplotlib (.png/.svg)
└── starter/                  # the official assignment repo (scripts, test_input.csv)
```

`raw/` (downloaded GH Archive files) and `data/` (the 8 Parquet tables) are git-ignored; they are
reproduced from the steps below.

## Reproduce

**0. Environment** (Python 3.11, Windows/Linux; a CUDA GPU is used for the GNN but not required):

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt      # Windows
# source .venv/bin/activate && pip install -r requirements.txt  # Linux/Mac
```

**1. Download the GH Archive hour files** (UTC date range; the window used for the submission is
2026-10-04 … 2026-11-16):

```bash
bash tools/download_raw.sh 2026-10-04 2026-11-16     # writes into raw/
```

**2. Build the 8 tables with the official preprocessing script** (required; includes
anonymization):

```bash
.venv/Scripts/python starter/scripts/preprocess.py --raw raw --out data
# -> data/db/{Users,Repositories,PullRequests,Issues,IssueComments,PRReviews,PRReviewComments,Pushes}.parquet
```

**3. Evaluate on a held-out week** (time-based split; reports Score = (macro-F1 + micro-F1)/2):

```bash
.venv/Scripts/python run.py evaluate --weeks 4
```

**4. Produce the submission** for the test week:

```bash
.venv/Scripts/python run.py predict --weeks 4
# -> output_413551034.csv
```

**5. Format-check the submission** with the official evaluator:

```bash
.venv/Scripts/python starter/scripts/evaluate.py --pred output_413551034.csv \
    --input starter/submission/test_input.csv
```

## Method summary

- **Leakage control.** For a prediction at time *t*, a row is usable only if its *row-time*
  (`first_seen_at`, or `created_at` for comments/pushes) is `< t`. PRs/issues/reviews are **not**
  filtered by `created_at`/`submitted_at` (they can enter the data late), and the
  "known-only-later" columns (`merged_at`, `closed_at`, `state_reason`, `dismissed_at`, …) are
  never used as features. Training/validation are split **by time**, never at random.
- **Temporal features** (Q3): multi-window activity counts (1/7/14/30/90 d), days-since-last
  (recency), distinct active days, and 7-day momentum/ratio — including the strong
  *copy-last-week* signal.
- **Relational features** (Q2): foreign-key joins across tables — reviews/comments your work
  received, distinct collaborators, repo/org breadth — plus a light GNN over the FK graph.
- **Targets.** One LightGBM per activity; each activity's decision threshold is tuned to maximize
  F1 on the validation week (matching the evaluation metric).

## Results

See the presentation slides (`Asg2_413551034.pdf`). Validation scores on a held-out week are
reported there against the course baselines (copy-last-week, GNN with/without time encoding).

<!-- RESULTS_TABLE: filled after the final experiment run -->
