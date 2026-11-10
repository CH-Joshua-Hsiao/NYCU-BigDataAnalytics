"""Central configuration: paths, the 6 activities, time windows, and leakage rules.

All timestamps in the tables are UTC and tz-naive (see preprocess.py `set_types`).
Taiwan time is UTC+8, so a Taiwan wall-clock time t_tw corresponds to t_tw - 8h in UTC.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

# --- paths ------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent          # HW2/
RAW_DIR = ROOT / "raw"                                  # GH Archive hour files
DATA_DIR = ROOT / "data"                                # preprocess.py output (contains db/)
DB_DIR = DATA_DIR / "db"                                # the 8 parquet tables
STARTER = ROOT / "starter"                              # official repo (scripts, submission)
TEST_INPUT = STARTER / "submission" / "test_input.csv"
ARTIFACT_DIR = ROOT / "artifacts"                       # models, cached features, figures

# --- the prediction target --------------------------------------------------
ACTIVITIES = ["open_pr", "open_issue", "issue_comment",
              "pr_review", "pr_review_comment", "push"]
USER_COL = "UserID"
OUTPUT_COLUMNS = [USER_COL] + ACTIVITIES

# --- time windows -----------------------------------------------------------
TW_OFFSET = timedelta(hours=8)          # Taiwan = UTC + 8
WEEK = timedelta(days=7)


def tw_to_utc(y, m, d, hh=0, mm=0) -> datetime:
    """A Taiwan wall-clock time -> the equivalent tz-naive UTC datetime."""
    return datetime(y, m, d, hh, mm) - TW_OFFSET


# Official test week: 2026/11/22 00:00 -> 11/29 00:00 (Taiwan). We predict this.
TEST_WEEK_START = tw_to_utc(2026, 11, 22)       # 2026-11-21 16:00 UTC
TEST_WEEK_END = tw_to_utc(2026, 11, 29)         # 2026-11-28 16:00 UTC
# Prediction time t: everything with row-time < t is usable for the final features.
PREDICT_TIME = TEST_WEEK_START

DATA_START = datetime(2025, 12, 1)              # preprocess.py ignores earlier files

# --- row-time column of each table (when the row becomes visible in the data) ----
ROW_TIME = {
    "Users": "first_seen_at",
    "Repositories": "first_seen_at",
    "PullRequests": "first_seen_at",
    "Issues": "first_seen_at",
    "IssueComments": "created_at",
    "PRReviews": "first_seen_at",
    "PRReviewComments": "created_at",
    "Pushes": "created_at",
}

# Columns that are "known only later" (filled by events after the row appears).
# NEVER use these as features for a prediction made at time t (schema: known-only-later).
FUTURE_COLUMNS = {
    "PullRequests": ["merged_at", "merged_by_id", "closed_at"],
    "Issues": ["closed_at", "state_reason"],
    "PRReviews": ["dismissed_at"],
}

# For each activity: (table, actor-id column, action-time column, row-filter).
# The action-time column is the true time the activity happened; used to BUILD LABELS
# and the "did it in the last k days" features. row_filter narrows rows (e.g. real issues
# vs PR conversations).
ACTIVITY_SOURCE = {
    "open_pr":           ("PullRequests",   "author_id",   "created_at",   None),
    "open_issue":        ("Issues",         "author_id",   "created_at",   "is_real_issue"),
    "issue_comment":     ("IssueComments",  "author_id",   "created_at",   None),
    "pr_review":         ("PRReviews",      "reviewer_id", "submitted_at", None),
    "pr_review_comment": ("PRReviewComments", "author_id", "created_at",   None),
    "push":              ("Pushes",         "user_id",     "created_at",   None),
}

TABLES = ["Users", "Repositories", "PullRequests", "Issues",
          "IssueComments", "PRReviews", "PRReviewComments", "Pushes"]
