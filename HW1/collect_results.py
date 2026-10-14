"""Collect per-run summaries into the Q1 (accuracy) and Q2 (training time) report tables.

Each notebook execution overwrites benchmark_results.csv, so this reads the
per-run *_summary.json files instead. Usage: python collect_results.py
"""
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RUN_DIR = HERE / 'outputs' / 'Assignment1'
OUT_DIR = HERE / 'results'
RANKS = [16, 64, 256]
Q3_COMPONENTS = {
    'default': 'Top 16',
    'pos25': 'From 25%',
    'pos50': 'From 50%',
    'bottom': 'Bottom 16',
}


def load_summaries():
    rows = [
        json.loads(p.read_text(encoding='utf-8'))
        for p in sorted(RUN_DIR.glob('*_summary.json'))
    ]
    return pd.DataFrame([r for r in rows if r.get('status') == 'ok'])


def label(row):
    if row['method'] == 'fresh':
        return 'Original LLM'
    return f"Fine-Tuned LLM (RANK = {int(row['rank'])})"


def plot_q3(q3, path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4))
    for ax, col, color in zip(axes, q3.columns, ['#4C72B0', '#DD8452']):
        bars = ax.bar(q3.index, q3[col], color=color, width=0.6)
        ax.bar_label(bars, fmt='%.1f', fontsize=9)
        ax.set_title(f'{col} accuracy (rank 16)')
        ax.set_xlabel('Singular-value range')
        ax.set_ylabel('Accuracy (%)')
        ax.set_ylim(0, max(q3[col].max() * 1.2, 1))
        ax.spines[['top', 'right']].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def main():
    df = load_summaries()
    if df.empty:
        raise SystemExit(f'No finished runs in {RUN_DIR}')
    OUT_DIR.mkdir(exist_ok=True)

    default = df[(df['method'] == 'fresh') | (df['component'] == 'default')].copy()
    default['order'] = default['rank'].fillna(0)
    default = default.sort_values('order')
    default['setting'] = default.apply(label, axis=1)

    # Q1: accuracy (%) on GSM8K and MATH, settings as columns like the slide's table.
    q1 = default.set_index('setting')[['gsm8k_accuracy', 'math_accuracy']].T * 100
    q1.index = ['GSM8K', 'MATH']
    q1.to_csv(OUT_DIR / 'q1_accuracy.csv', float_format='%.1f')

    # Q2: training time (min) for the fine-tuned runs.
    tuned = default[default['method'] == 'pissa']
    q2 = tuned.set_index('setting')[['train_minutes', 'trainable_parameters']].T
    q2.index = ['Training Time (min.)', 'Trainable Parameters']
    q2.to_csv(OUT_DIR / 'q2_training_time.csv', float_format='%.2f')

    # Q3: accuracy (%) at rank 16 for the four singular-value ranges, as a grouped bar chart.
    q3_runs = df[(df['method'] == 'pissa') & (df['rank'] == 16)].set_index('component')
    q3_comps = [c for c in Q3_COMPONENTS if c in q3_runs.index]
    q3 = q3_runs.loc[q3_comps, ['gsm8k_accuracy', 'math_accuracy']] * 100
    q3.index = [Q3_COMPONENTS[c] for c in q3_comps]
    q3.columns = ['GSM8K', 'MATH']
    q3.to_csv(OUT_DIR / 'q3_components.csv', float_format='%.1f')
    if len(q3):
        plot_q3(q3, OUT_DIR / 'q3_components.png')

    missing = [r for r in RANKS if r not in set(tuned['rank'].astype(int))]
    print('Q3 accuracy (%):\n', q3.round(1).to_string(), '\n')
    missing_q3 = [c for c in Q3_COMPONENTS if c not in q3_comps]
    if missing_q3:
        print('Still missing Q3 components:', missing_q3)
    pd.set_option('display.width', 200)
    print('Q1 accuracy (%):\n', q1.round(1).to_string(), '\n')
    print('Q2 training time:\n', q2.to_string(float_format=lambda v: f'{v:,.2f}'), '\n')
    if missing:
        print('Still missing ranks:', missing)
    print('Saved to', OUT_DIR)


if __name__ == '__main__':
    main()
