"""Question 4 framework figure: the full pipeline, rendered with matplotlib.

    python tools/framework_figure.py   # -> artifacts/framework.png / .svg
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = Path(__file__).resolve().parent.parent / "artifacts"

NAVY = "#1f3b63"; BLUE = "#2d6cb5"; GREEN = "#2e8b57"; GOLD = "#c8912a"; GREY = "#5b6b7b"


def box(ax, x, y, w, h, title, lines, color):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01,rounding_size=0.04",
                                linewidth=1.4, edgecolor=color, facecolor="white", zorder=3))
    ax.add_patch(plt.Rectangle((x, y + h - 0.32), w, 0.32, facecolor=color, zorder=4))
    ax.text(x + w / 2, y + h - 0.16, title, ha="center", va="center", color="white",
            fontsize=10, fontweight="bold", zorder=5)
    ax.text(x + w / 2, y + (h - 0.32) / 2, "\n".join(lines), ha="center", va="center",
            fontsize=8.2, zorder=5)
    return (x, y, w, h)


def arrow(ax, p0, p1, color=GREY, style="-|>", rad=0.0, label=None):
    a = FancyArrowPatch(p0, p1, arrowstyle=style, mutation_scale=14, linewidth=1.5,
                        color=color, zorder=2, connectionstyle=f"arc3,rad={rad}",
                        shrinkA=3, shrinkB=3)
    ax.add_patch(a)
    if label:
        mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
        ax.text(mx, my + 0.12, label, ha="center", fontsize=7.5, color=color, style="italic")


def draw():
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_axis_off()

    b_raw = box(ax, 0.2, 5.6, 2.2, 1.2, "GH Archive",
                ["hourly event files", "(2026-10-04 … 11-21)"], GREY)
    b_pre = box(ax, 3.0, 5.6, 2.3, 1.2, "preprocess.py",
                ["filter 9k cohort", "anonymize → 8 tables"], NAVY)
    b_db = box(ax, 6.0, 5.4, 2.4, 1.6, "8 relational tables",
               ["Users, Repos,", "PullRequests, Issues,", "Comments, Reviews,", "Pushes (Parquet)"], NAVY)

    # three feature/representation branches
    b_tmp = box(ax, 9.3, 7.0, 3.3, 1.5, "Temporal features (Q3)",
                ["multi-window counts 1/7/14/30/90d", "recency, active days, momentum,",
                 "copy-last-week signal"], BLUE)
    b_rel = box(ax, 9.3, 5.0, 3.3, 1.5, "Relational features (Q2)",
                ["FK joins: reviews/comments received,", "distinct collaborators,",
                 "repo / org breadth"], GREEN)
    b_gnn = box(ax, 9.3, 2.9, 3.3, 1.6, "Time-aware GNN (Q2+Q3)",
                ["user–repo FK graph, 6 edge types,", "edge age → exp(-age/τ) decay,",
                 "hetero GraphSAGE → user emb."], GOLD)

    # leakage gate note
    ax.text(7.2, 4.9, "leakage gate:\nrow-time < t only", ha="center", fontsize=7.5,
            color="#b0382f", style="italic")

    b_model = box(ax, 13.1, 4.9, 2.6, 1.7, "Models",
                  ["LightGBM ×6", "(one per activity)", "+ time-aware", "relational GNN"], NAVY)
    b_thr = box(ax, 13.1, 2.9, 2.6, 1.2, "Threshold tuning",
                ["per-activity F1-", "optimal threshold"], BLUE)
    b_out = box(ax, 13.1, 1.2, 2.6, 1.1, "Submission",
                ["output_413551034.csv", "6 binary labels / user"], GREEN)

    arrow(ax, (2.4, 6.2), (3.0, 6.2))
    arrow(ax, (5.3, 6.2), (6.0, 6.2))
    arrow(ax, (8.4, 6.3), (9.3, 7.6), rad=-0.15)
    arrow(ax, (8.4, 6.2), (9.3, 5.7), rad=0.0)
    arrow(ax, (8.4, 6.1), (9.3, 3.6), rad=0.15)
    for yb in (7.6, 5.7, 3.6):
        arrow(ax, (12.6, yb), (13.1, 5.9) if yb > 5 else (13.1, 5.2), rad=0.08)
    arrow(ax, (14.4, 4.9), (14.4, 4.1))
    arrow(ax, (14.4, 2.9), (14.4, 2.3))

    ax.text(0.2, 8.2, "Framework: Predicting GitHub User Activity", fontsize=14, fontweight="bold")
    ax.text(0.2, 7.85, "Relational + temporal modeling over 8 FK-linked tables, with strict time-based leakage control.",
            fontsize=9.5, color="#444")

    ax.set_xlim(0, 16); ax.set_ylim(0.8, 8.6)
    ax.set_aspect("equal")
    fig.tight_layout()
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "svg"):
        fig.savefig(OUT / f"framework.{ext}", dpi=200, bbox_inches="tight")
        print("wrote", OUT / f"framework.{ext}")


if __name__ == "__main__":
    draw()
