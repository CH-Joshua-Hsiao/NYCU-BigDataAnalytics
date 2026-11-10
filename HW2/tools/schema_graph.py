"""Question 1: draw the schema graph of the 8 tables.

Every table is a node listing its columns; the primary key is marked (PK) and every foreign
key (FK) points to the primary key it references. Emits a Graphviz .dot file and renders it to
PNG + SVG if the Graphviz `dot` binary is available.

    python tools/schema_graph.py            # -> artifacts/schema_graph.{dot,png,svg}
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "artifacts"

# table -> (primary key, [(column, fk_target_or_None)]) in schema order.
SCHEMA = {
    "Users": ("user_id", [
        ("user_id", None), ("github_user_id", None), ("login", None),
        ("is_bot", None), ("is_cohort", None), ("first_seen_at", None)]),
    "Repositories": ("repo_id", [
        ("repo_id", None), ("github_repo_id", None), ("name", None),
        ("owner_login", None), ("org_id", None), ("org_login", None), ("first_seen_at", None)]),
    "PullRequests": ("pr_id", [
        ("pr_id", None), ("repo_id", "Repositories"), ("author_id", "Users"),
        ("merged_by_id", "Users"), ("created_at", None), ("merged_at", None),
        ("closed_at", None), ("first_seen_at", None)]),
    "Issues": ("issue_id", [
        ("issue_id", None), ("repo_id", "Repositories"), ("author_id", "Users"),
        ("is_pull_request", None), ("pull_request_id", "PullRequests"),
        ("assignee_id", "Users"), ("created_at", None), ("closed_at", None),
        ("first_seen_at", None)]),
    "IssueComments": ("comment_id", [
        ("comment_id", None), ("issue_id", "Issues"), ("repo_id", "Repositories"),
        ("author_id", "Users"), ("is_pull_request", None), ("created_at", None)]),
    "PRReviews": ("review_id", [
        ("review_id", None), ("pr_id", "PullRequests"), ("repo_id", "Repositories"),
        ("reviewer_id", "Users"), ("state", None), ("submitted_at", None),
        ("dismissed_at", None), ("first_seen_at", None)]),
    "PRReviewComments": ("comment_id", [
        ("comment_id", None), ("pr_id", "PullRequests"), ("repo_id", "Repositories"),
        ("author_id", "Users"), ("pull_request_review_id", "PRReviews"),
        ("in_reply_to_id", "PRReviewComments"), ("created_at", None)]),
    "Pushes": ("push_id", [
        ("push_id", None), ("user_id", "Users"), ("repo_id", "Repositories"),
        ("ref_type", None), ("is_new_ref", None), ("created_at", None)]),
}


def esc(s):
    return s.replace("_", "\\_") if False else s


def build_dot() -> str:
    lines = [
        "digraph Schema {",
        "  rankdir=LR;",
        "  graph [fontname=\"Helvetica\", nodesep=0.5, ranksep=1.1, bgcolor=white];",
        "  node  [shape=plaintext, fontname=\"Helvetica\", fontsize=10];",
        "  edge  [color=\"#555555\", arrowsize=0.8, penwidth=1.1];",
    ]
    for tbl, (pk, cols) in SCHEMA.items():
        rows = [f'<TR><TD BGCOLOR="#1f3b63"><FONT COLOR="white"><B>{tbl}</B></FONT></TD></TR>']
        for col, fk in cols:
            tag = ""
            bg = "white"
            if col == pk:
                tag = '  <FONT COLOR="#b8860b"><B>PK</B></FONT>'
                bg = "#fdf3d7"
            elif fk:
                tag = '  <FONT COLOR="#2a7">FK</FONT>'
                bg = "#eef7ee"
            rows.append(
                f'<TR><TD ALIGN="LEFT" PORT="{col}" BGCOLOR="{bg}">'
                f'{col}{tag}</TD></TR>')
        label = ('<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0">'
                 + "".join(rows) + "</TABLE>>")
        lines.append(f'  {tbl} [label={label}];')
    # FK edges: from the FK column port to the target table's PK port
    for tbl, (pk, cols) in SCHEMA.items():
        for col, fk in cols:
            if fk:
                tgt_pk = SCHEMA[fk][0]
                style = ' [style=dashed]' if fk == tbl else ''
                lines.append(f'  {tbl}:{col} -> {fk}:{tgt_pk}{style};')
    lines.append("}")
    return "\n".join(lines)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    dot = build_dot()
    dot_path = OUT / "schema_graph.dot"
    dot_path.write_text(dot, encoding="utf-8")
    print("wrote", dot_path)
    exe = shutil.which("dot")
    if not exe:
        print("Graphviz 'dot' not found; install it to render PNG/SVG "
              "(winget install graphviz  |  choco install graphviz). The .dot is ready.")
        return
    for fmt in ("png", "svg"):
        out = OUT / f"schema_graph.{fmt}"
        subprocess.run([exe, f"-T{fmt}", str(dot_path), "-o", str(out)], check=True)
        print("wrote", out)


if __name__ == "__main__":
    main()
