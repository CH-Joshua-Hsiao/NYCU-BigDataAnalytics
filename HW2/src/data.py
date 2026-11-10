"""Load the 8 preprocessed tables and provide leakage-safe access helpers."""
from __future__ import annotations

from functools import lru_cache

import pandas as pd

from . import config as C


@lru_cache(maxsize=1)
def load_tables(db_dir: str | None = None) -> dict[str, pd.DataFrame]:
    """Read the 8 Parquet tables into a dict {table_name: DataFrame}. Cached."""
    base = C.DB_DIR if db_dir is None else db_dir
    tables = {}
    for name in C.TABLES:
        df = pd.read_parquet(f"{base}/{name}.parquet")
        tables[name] = df
    return tables


def test_users() -> pd.Series:
    """The official 4,465 test UserIDs (= Users.github_user_id codes), in file order."""
    return pd.read_csv(C.TEST_INPUT)[C.USER_COL]


def visible_rows(df: pd.DataFrame, table: str, t) -> pd.DataFrame:
    """Rows of `table` that are visible at prediction time t: row-time < t.

    This is the ONLY correct way to decide what a model would know at t. Do not filter
    by created_at/submitted_at of PRs/issues/reviews -- those rows can enter the data long
    after the action happened (README section 3).
    """
    rt = C.ROW_TIME[table]
    return df[df[rt] < pd.Timestamp(t)]


def add_user_code(tables: dict[str, pd.DataFrame]) -> dict[str, int]:
    """Map Users.user_id (row number) -> github_user_id (the stable code used in test_input)."""
    u = tables["Users"]
    return dict(zip(u["user_id"], u["github_user_id"]))
