"""Question 1 schema graph, rendered with matplotlib (no external Graphviz needed).

Draws the 8 tables as boxes listing their columns, marks the primary key (PK, gold) and the
foreign keys (FK, green), and draws an arrow from each FK to the primary key it references.

    python tools/schema_graph_mpl.py     # -> artifacts/schema_graph.png / .svg
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

from schema_graph import SCHEMA          # reuse the single source of truth

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "artifacts"

# layered left->right placement (col, row-within-col). Hubs (Users, Repositories) on the left.
LAYOUT = {
    "Users":            (0, 0.5),
    "Repositories":     (0, 2.0),
    "PullRequests":     (1, 0.0),
    "Issues":           (1, 1.4),
    "Pushes":           (1, 2.7),
    "PRReviews":        (2, 0.0),
    "IssueComments":    (2, 1.5),
    "PRReviewComments": (3, 0.6),
}
COL_X = {0: 0.0, 1: 4.2, 2: 8.4, 3: 12.6}
BOX_W = 2.7
ROW_H = 0.30
HEAD_H = 0.42
Y_SCALE = 3.4

NAVY = "#1f3b63"
GOLD_BG = "#fdf3d7"
FK_BG = "#eef7ee"


def _box_geom():
    """Return {table: dict(x, y_top, w, h, rows={col: y_center})}."""
    geom = {}
    for tbl, (pk, cols) in SCHEMA.items():
        col, row = LAYOUT[tbl]
        x = COL_X[col]
        y_top = -row * Y_SCALE
        h = HEAD_H + ROW_H * len(cols)
        rows = {}
        y = y_top - HEAD_H
        for name, _ in cols:
            rows[name] = y - ROW_H / 2
            y -= ROW_H
        geom[tbl] = dict(x=x, y_top=y_top, w=BOX_W, h=h, rows=rows, pk=pk)
    return geom


def draw():
    geom = _box_geom()
    fig, ax = plt.subplots(figsize=(15, 11))
    ax.set_axis_off()

    # boxes
    for tbl, (pk, cols) in SCHEMA.items():
        g = geom[tbl]
        x, yt, w, h = g["x"], g["y_top"], g["w"], g["h"]
        ax.add_patch(FancyBboxPatch((x, yt - h), w, h, boxstyle="round,pad=0.02,rounding_size=0.06",
                                    linewidth=1.2, edgecolor="#333", facecolor="white", zorder=2))
        # header
        ax.add_patch(plt.Rectangle((x, yt - HEAD_H), w, HEAD_H, facecolor=NAVY, zorder=3))
        ax.text(x + w / 2, yt - HEAD_H / 2, tbl, ha="center", va="center",
                color="white", fontsize=10.5, fontweight="bold", zorder=4)
        # columns
        for name, fk in cols:
            yc = g["rows"][name]
            if name == pk:
                ax.add_patch(plt.Rectangle((x, yc - ROW_H / 2), w, ROW_H, facecolor=GOLD_BG, zorder=2.5))
                tag, tcol = "PK", "#b8860b"
            elif fk:
                ax.add_patch(plt.Rectangle((x, yc - ROW_H / 2), w, ROW_H, facecolor=FK_BG, zorder=2.5))
                tag, tcol = "FK", "#1b7a3d"
            else:
                tag, tcol = "", None
            ax.text(x + 0.08, yc, name, ha="left", va="center", fontsize=8, zorder=4)
            if tag:
                ax.text(x + w - 0.08, yc, tag, ha="right", va="center", fontsize=7.5,
                        fontweight="bold", color=tcol, zorder=4)

    # FK edges: from the FK row (right or left edge) to the target table's header
    for tbl, (pk, cols) in SCHEMA.items():
        for name, fk in cols:
            if not fk:
                continue
            src = geom[tbl]; tgt = geom[fk]
            y0 = src["rows"][name]
            # leave from whichever side faces the target
            if tgt["x"] < src["x"]:
                x0, conn = src["x"], "arc3,rad=-0.15"
            else:
                x0, conn = src["x"] + src["w"], "arc3,rad=0.15"
            # arrive at target PK row, on the side facing the source
            y1 = tgt["rows"][tgt["pk"]]
            x1 = tgt["x"] + tgt["w"] if tgt["x"] < src["x"] else tgt["x"]
            self_loop = fk == tbl
            if self_loop:
                x1 = src["x"] + src["w"]; y1 = tgt["rows"][tgt["pk"]]; conn = "arc3,rad=0.9"
            ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), connectionstyle=conn,
                                         arrowstyle="-|>", mutation_scale=11,
                                         linewidth=1.0, color="#6a7a8c", zorder=1,
                                         shrinkA=2, shrinkB=2))

    # legend
    ax.text(0.0, 1.4, "GitHub Activity Schema — 8 tables, FK → PK",
            fontsize=13, fontweight="bold")
    ax.scatter([], [])
    handles = [plt.Line2D([0], [0], marker="s", color="w", markerfacecolor=GOLD_BG,
                          markeredgecolor="#b8860b", markersize=12, label="PK  primary key"),
               plt.Line2D([0], [0], marker="s", color="w", markerfacecolor=FK_BG,
                          markeredgecolor="#1b7a3d", markersize=12, label="FK  foreign key"),
               plt.Line2D([0], [0], color="#6a7a8c", marker=">", label="FK → referenced PK")]
    ax.legend(handles=handles, loc="lower right", fontsize=9, frameon=False)

    ax.set_xlim(-0.6, 16.0)
    ax.set_ylim(-11.8, 2.0)
    ax.set_aspect("equal")
    fig.tight_layout()
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "svg"):
        fig.savefig(OUT / f"schema_graph.{ext}", dpi=200, bbox_inches="tight")
        print("wrote", OUT / f"schema_graph.{ext}")


if __name__ == "__main__":
    draw()
