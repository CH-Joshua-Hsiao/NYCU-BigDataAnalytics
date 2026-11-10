"""Render the report charts from artifacts/metrics.json (run `python run.py full` first).

    python tools/report_charts.py   # -> artifacts/chart_*.png
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ART = Path(__file__).resolve().parent.parent / "artifacts"
ACT = ["open_pr", "open_issue", "issue_comment", "pr_review", "pr_review_comment", "push"]

INK = "#1f2a37"; GREY = "#9aa7b4"; BLUE = "#2d6cb5"; GOLD = "#c8912a"; GREEN = "#2e8b57"; RED = "#b0382f"


def _style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(length=0)
    ax.set_axisbelow(True)


def chart_methods(m):
    names = list(m["methods"].keys())
    scores = [100 * m["methods"][n]["score"] for n in names]
    colors = []
    for n in names:
        if n.startswith("GBDT (all"):
            colors.append(GREEN)
        elif n.startswith("GBDT"):
            colors.append(BLUE)
        elif n.startswith("GNN"):
            colors.append(GOLD)
        else:
            colors.append(GREY)
    fig, ax = plt.subplots(figsize=(9, 4.6))
    y = range(len(names))
    ax.barh(list(y), scores, color=colors, height=0.68)
    ax.set_yticks(list(y)); ax.set_yticklabels(names, fontsize=9.5)
    ax.invert_yaxis()
    ax.set_xlabel("Score = (macro-F1 + micro-F1) / 2  (%)", fontsize=10)
    ax.set_xlim(0, max(scores) * 1.18)
    for i, v in enumerate(scores):
        ax.text(v + 0.4, i, f"{v:.1f}", va="center", fontsize=9, color=INK)
    ax.set_title("Model comparison on the held-out validation week", fontsize=12, fontweight="bold", loc="left")
    _style(ax)
    fig.tight_layout(); fig.savefig(ART / "chart_methods.png", dpi=200, bbox_inches="tight")
    print("wrote", ART / "chart_methods.png")


def chart_per_activity(m):
    meth = "GBDT (all features)"
    pe = m["methods"][meth]["per_event"]
    vals = [100 * pe[a] for a in ACT]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    x = range(len(ACT))
    ax.bar(list(x), vals, color=BLUE, width=0.62)
    ax.set_xticks(list(x)); ax.set_xticklabels(ACT, rotation=20, ha="right", fontsize=9)
    ax.set_ylabel("F1 (%)", fontsize=10); ax.set_ylim(0, max(vals) * 1.2)
    for i, v in enumerate(vals):
        ax.text(i, v + 0.6, f"{v:.0f}", ha="center", fontsize=9, color=INK)
    ax.set_title("GBDT per-activity F1", fontsize=12, fontweight="bold", loc="left")
    _style(ax)
    fig.tight_layout(); fig.savefig(ART / "chart_per_activity.png", dpi=200, bbox_inches="tight")
    print("wrote", ART / "chart_per_activity.png")


def chart_ablation(m):
    base = 100 * m["methods"]["GBDT (all features)"]["score"]
    items = [("All features", base, GREEN),
             ("− relational (Q2)", 100 * m["methods"]["GBDT - relational (Q2)"]["score"], BLUE),
             ("− temporal (Q3)", 100 * m["methods"]["GBDT - temporal (Q3)"]["score"], RED)]
    fig, ax = plt.subplots(figsize=(6.6, 4.0))
    names = [i[0] for i in items]; vals = [i[1] for i in items]; cols = [i[2] for i in items]
    ax.bar(names, vals, color=cols, width=0.6)
    ax.set_ylabel("Score (%)", fontsize=10); ax.set_ylim(0, base * 1.2)
    for i, v in enumerate(vals):
        d = v - base
        lab = f"{v:.1f}" + (f"\n({d:+.1f})" if i else "")
        ax.text(i, v + 0.4, lab, ha="center", fontsize=9, color=INK)
    ax.set_title("GBDT feature-group ablation", fontsize=12, fontweight="bold", loc="left")
    _style(ax)
    fig.tight_layout(); fig.savefig(ART / "chart_ablation.png", dpi=200, bbox_inches="tight")
    print("wrote", ART / "chart_ablation.png")


def main():
    m = json.loads((ART / "metrics.json").read_text(encoding="utf-8"))
    chart_methods(m); chart_per_activity(m); chart_ablation(m)


if __name__ == "__main__":
    main()
