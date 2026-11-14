# HW2 — Predicting GitHub User Activity (handoff for the next Claude)

This file is auto-loaded by Claude Code. It is a continuation guide: what this project is,
how to rebuild everything that is git-ignored, the code map, the domain rules you must not
break, the results, and what is left to do. Work from the `HW2/` directory.

## 1. The task (fixed by the course)

Course: Big Data Analytics, Fall 2026 (NYCU). Assignment 2 = 15% of the grade, individual.
Predict, for each of the **4,465 test users** in `starter/submission/test_input.csv` (`UserID`
= `Users.github_user_id`), which of **6 activities** they will do during the test week
**2026-11-22 00:00 → 11-29 00:00 (Taiwan, UTC+8)**:
`open_pr, open_issue, issue_comment, pr_review, pr_review_comment, push` → one 0/1 each.
Output file: `output_413551034.csv`. Metric: `Score = (macro-F1 + micro-F1) / 2`.

Grading reality that drives strategy: the prediction **Score is 0%** (reference only); the
README GH-Archive acknowledgment is **1%**; the **video + slides answering 4 questions is 14%**
(Q1 schema graph, Q2 relationships, Q3 temporal, Q4 framework/pipeline). The TAs re-run
`preprocess.py` and must be able to **reproduce the submitted output** — so the pipeline is
reproducible (pinned deps, fixed seeds, documented window). AI-generated video = 0; the user
records the video.

Deadline: 2026-11-21 23:55. **This handoff was last updated 2026-11-14.** Data currently exists
only to ~11-14, so the test week is still in the future (see §7 item 1).

Public repo (slides + README point here): <https://github.com/CH-Joshua-Hsiao/NYCU-BigDataAnalytics/tree/main/HW2>.

## 2. Rebuild what is git-ignored (do this first in a fresh clone)

`raw/` (6.9 GB GH Archive), `data/` (8 Parquet tables), `starter/` (official repo), `.venv/`,
`tools/graphviz/`, and `report_build/` scratch are all git-ignored. Recreate them:

```bash
# from HW2/
# a) official starter repo (scripts/preprocess.py, evaluate.py, cohort.txt, test_input.csv)
git clone --depth 1 https://github.com/nycubigdata-2026fall/BigData2026-Assignment2.git starter

# b) python env (Windows paths; use .venv/bin on Linux/mac)
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
#   torch is CUDA cu121 in requirements; for CPU use `pip install torch==2.5.1`

# c) download raw GH Archive hours, then build the 8 tables with the OFFICIAL script
bash tools/download_raw.sh 2026-10-04 2026-11-21      # only dates that exist are fetched
.venv/Scripts/python starter/scripts/preprocess.py --raw raw --out data
```

Notes: the archive at data.gharchive.org here is a downsampled mirror (~4-5 MB/hr, ~5.7k
events/hr); the cohort of 9,000 users is sparse. `preprocess.py` ignores files before
2025-12-01 and keeps only the cohort's events. Codes (ids) are deterministic, so
`github_user_id` always matches `test_input.csv` regardless of the window processed.

## 3. Run it

```bash
# all commands from HW2/ with the venv python; it forces UTF-8 stdout (Windows console is cp950)
.venv/Scripts/python run.py smoke                 # table row counts, data span, test-user coverage
.venv/Scripts/python run.py evaluate --weeks 4    # GBDT + baselines on a held-out week (fast)
.venv/Scripts/python run.py full --weeks 4 --epochs 250   # all models + ablations -> artifacts/results.md + metrics.json + submission
.venv/Scripts/python run.py predict --weeks 4     # train, write output_413551034.csv
.venv/Scripts/python starter/scripts/evaluate.py --pred output_413551034.csv --input starter/submission/test_input.csv  # format check
```

Report assets: `tools/schema_graph_mpl.py` (Q1), `tools/framework_figure.py` (Q4),
`tools/report_charts.py` (reads `artifacts/metrics.json`). Slides:
`report_build/build_slides.py` (python-pptx) → `Asg2_413551034.pptx`; exported to PDF/PNG via
**PowerPoint COM** in this env (no Node, so no pptxgenjs; no LibreOffice, so the skill's
`soffice.py` shim fails on Windows — it uses `AF_UNIX`). Building the deck needs `python-pptx`
and `Pillow` (NOT in `requirements.txt`, since they are not needed to reproduce the model —
`pip install python-pptx Pillow` first). Each slide carries a **Traditional-Chinese speaker
script** in its notes; the same script is also at `report_build/speaker_script_zh.md` (per-slide
timing, ~19 min for the 16–20 min video). PDF re-export after editing the deck:
`PowerPoint.Application` COM → `SaveAs(pdf, 32)` (see the command used in git history).

## 4. Code map (`src/`)

| file | role |
|---|---|
| `config.py` | paths, the 6 activities, time windows (test week in UTC), **row-time column per table**, **future-only columns**, activity→table/actor/time mapping |
| `data.py` | load the 8 Parquet tables; `visible_rows(df, table, t)` = rows with row-time < t |
| `labels.py` | build the 6 binary labels for any week from the **action time** (created_at/submitted_at) |
| `features.py` | leakage-safe per-user features: temporal (multi-window counts, recency, momentum) + relational (FK joins, repo-neighborhood). `FEATURE_GROUPS` drives ablations |
| `dataset.py` | assemble (user, cutoff) examples; **time-based** train/val split |
| `baselines.py` | copy-last-week, all-zero |
| `gbdt.py` | 6× LightGBM (one per activity) + per-activity F1-optimal threshold; `score()` reproduces evaluate.py |
| `gnn.py` | time-aware heterogeneous GraphSAGE over the user–repo FK graph (pure torch). Flags: `use_graph`, `use_time`, `node_mode` ("full"/"minimal"); skip-connection head |
| `experiments.py` | `run_all()` → the report comparison table + Q2/Q3 ablations |
| `predict.py` | write the submission; users absent from the tables → all-zero |
| `run.py` | CLI: smoke / evaluate / predict / full. `effective_predict_time()` falls back to the last data midnight when the test week is in the future |

## 5. Domain rules you MUST NOT break (leakage)

- A row is usable at prediction time t **iff its row-time < t** (`config.ROW_TIME`: `first_seen_at`,
  or `created_at` for IssueComments/PRReviewComments/Pushes). Use `data.visible_rows`.
- **Never** filter PRs/issues/reviews by `created_at`/`submitted_at` to decide visibility — those
  rows enter the data late. (They are fine for *labels*, built from the fully-populated tables.)
- **Never** use known-only-later columns as features: `PullRequests.merged_at/merged_by_id/closed_at`,
  `Issues.closed_at/state_reason`, `PRReviews.dismissed_at` (see `config.FUTURE_COLUMNS`).
- Split train/validation **by time, never at random**. Earliest training cutoffs must be after the
  data start (empty graphs/examples otherwise — guarded in `experiments.choose_cutoffs`).

## 6. Results & the honest finding (do not fabricate)

Validation week Nov 3–10, `Score`: Copy-last-week 29.3; **GBDT (all features) 33.1 = submission**;
GBDT−temporal 29.0 (−4.1); GBDT−relational 33.6 (≈neutral); GNN node-MLP 30.3; GNN+graph 21.8;
GNN+graph+time 20.6. **Finding:** next-week activity is dominated by a user's own recent history
(strong temporal autocorrelation); relational features and GNN message passing add little on this
sparse user–repo graph (mean-aggregation over-smooths; per-activity AUC ≈ 0.5 once the graph is on).
This is reported honestly — the rubric rewards analysis and penalizes hallucinated results. Q3
(temporal) is the strong story; Q2 (relational) is "we tried it thoroughly; here's when RDL helps."

## 7. What is left (user actions + ideas to continue)

1. **Re-run `run.py predict` near the Nov 21 deadline** with fresh data (download through 11-21).
   Right now data only exists to ~11-10, so `effective_predict_time` uses the last data midnight as
   a proxy for the real test-week cutoff. This is the single most important remaining step.
2. ~~Replace the repo-URL placeholder on slide 1 and in `README.md`~~ — **DONE** (2026-11-14):
   the real URL is filled in both, and the deck + PDF were rebuilt.
3. Push `main` to `origin` (github.com/CH-Joshua-Hsiao/NYCU-BigDataAnalytics) — **only when the user
   asks**; pushing publishes externally. (Pushed through 2026-11-14; push again after step 1's rerun.)
4. The user records the video themselves (AI video = 0); each slide has a Chinese speaker script in
   its notes (also `report_build/speaker_script_zh.md`). The user must still confirm the repo is
   **public** and upload `output_413551034.csv` + `Asg2_413551034.pdf` + `Asg2_413551034.mp4` to E3.
5. Optional model ideas if asked to improve the *Score* (remember it is 0% of the grade):
   per-activity models tuned separately; longer history for 90-day features; calibrated thresholds
   on a rolling window; a proper RelBench temporal-sampling GNN (the current graph under-performs).

## 8. Decisions / gotchas already hit

- No Node.js and no LibreOffice in this environment → slides via python-pptx + PowerPoint COM.
- The downloaded Graphviz `dot.exe` is blocked by the sandbox (external binary) → schema graph is
  rendered with matplotlib (`tools/schema_graph_mpl.py`); `schema_graph.py` still emits a `.dot`.
- Windows console is cp950 → avoid non-ASCII in stdout; `run.py` reconfigures stdout to UTF-8.
- The deck `report_build/Asg2_413551034.pptx` is git-ignored (so is the duplicate PDF under
  `report_build/`); the **root** `Asg2_413551034.pdf` deliverable and `build_slides.py` are
  committed, so the deck is reproducible. To edit slides, rebuild the `.pptx` locally.
- Student ID is **413551034** (submission filenames `output_413551034.csv`, `Asg2_413551034.{pdf,mp4}`).
