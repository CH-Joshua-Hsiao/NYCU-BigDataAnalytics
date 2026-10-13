"""Build Asg1_413551034.docx from the collected results, then export the PDF with Word.

Usage: python report/build_report.py   (run collect_results.py first)
"""
import sys
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RESULTS = ROOT / 'results'
Q4_FIGS = ROOT / 'outputs' / 'q4'
NAME = 'Asg1_413551034'
GITHUB = 'https://github.com/CH-Joshua-Hsiao/NYCU-BigDataAnalytics/tree/main/Assignment1'

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
sec.left_margin = sec.right_margin = Cm(1.8)
sec.top_margin = sec.bottom_margin = Cm(1.5)
TEXT_WIDTH = Cm(21.0 - 3.6)

normal = doc.styles['Normal']
normal.font.name = 'Calibri'
normal.font.size = Pt(10)
normal.element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft JhengHei')
normal.paragraph_format.space_after = Pt(2)
normal.paragraph_format.line_spacing = 1.0


def para(text='', bold_prefix=None, size=None, align=None, after=None, italic=False):
    p = doc.add_paragraph()
    if bold_prefix:
        p.add_run(bold_prefix).bold = True
    r = p.add_run(text)
    r.italic = italic
    if size:
        for run in p.runs:
            run.font.size = Pt(size)
    if align is not None:
        p.alignment = align
    if after is not None:
        p.paragraph_format.space_after = Pt(after)
    return p


def heading(text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(11.5)
    r.font.color.rgb = RGBColor(0x1F, 0x3A, 0x68)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    border = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    for k, v in {'w:val': 'single', 'w:sz': '4', 'w:space': '1', 'w:color': '1F3A68'}.items():
        bottom.set(qn(k), v)
    border.append(bottom)
    p._p.get_or_add_pPr().append(border)


def bullet(text, bold_prefix=None):
    p = doc.add_paragraph(style='List Bullet')
    if bold_prefix:
        p.add_run(bold_prefix).bold = True
    p.add_run(text)
    p.paragraph_format.space_after = Pt(1)
    return p


def shade(cell, hex_color):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tc_pr.append(shd)


def table(header, rows, col_widths_cm):
    t = doc.add_table(rows=1 + len(rows), cols=len(header))
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, row in enumerate([header] + rows):
        for j, val in enumerate(row):
            cell = t.cell(i, j)
            cell.width = Cm(col_widths_cm[j])
            cell.text = ''
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(str(val))
            r.font.size = Pt(9)
            if i == 0 or j == 0:
                r.bold = True
            if i == 0:
                shade(cell, 'DCE6F2')
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return t


def pct(v):
    return f'{v:.1f}%'


q1 = pd.read_csv(RESULTS / 'q1_accuracy.csv', index_col=0)
q2 = pd.read_csv(RESULTS / 'q2_training_time.csv', index_col=0)
q3 = pd.read_csv(RESULTS / 'q3_components.csv', index_col=0)
if (q1.shape[1] < 4 or len(q3) < 4) and '--draft' not in sys.argv:
    sys.exit('Results incomplete: run all ranks and Q3 components, then collect_results.py')

# ---------------------------------------------------------------- title
t = para('Assignment 1: Analysis of SVD for Fine-Tuning LLMs', size=15, align=WD_ALIGN_PARAGRAPH.CENTER, after=0)
t.runs[0].bold = True
para('蕭至恆 (Student ID 413551034)  ·  Big Data Analytics Techniques and Applications, Fall 2026',
     size=10, align=WD_ALIGN_PARAGRAPH.CENTER, after=0)
p = para('GitHub: ', size=10, align=WD_ALIGN_PARAGRAPH.CENTER, after=2)
p.add_run(GITHUB).font.size = Pt(10)
para('Setup: Llama-3.2-1B fine-tuned with PiSSA on 25,000 MetaMathQA samples (1 epoch, lr 2e-5, global batch 128, '
     'FP16, all 7 projection types), evaluated on 1,000 GSM8K and 1,000 MATH test problems. All runs were done on a '
     'single local RTX 3090 (24 GB) with micro-batch 4 × 32 accumulation steps; SVD initialization ran on the CPU.',
     size=9, italic=True, after=2)

# ---------------------------------------------------------------- Q1
heading('Question 1: Accuracy of the original and fine-tuned models')
settings = list(q1.columns)
short = ['Original LLM', 'Fine-Tuned (RANK = 16)', 'Fine-Tuned (RANK = 64)', 'Fine-Tuned (RANK = 256)']
table(['Accuracy'] + short,
      [[task] + [pct(q1.loc[task, s]) for s in settings] for task in ['GSM8K', 'MATH']],
      [2.6, 3.2, 3.6, 3.6, 3.8])

g, m = q1.loc['GSM8K'], q1.loc['MATH']
bullet(f'The original model scores only {pct(g.iloc[0])} on GSM8K and {pct(m.iloc[0])} on MATH. It is a base '
       '(non-instruction) model, so it rarely produces a final answer in a parseable form: it never writes '
       '"The answer is:", and 959 of the 1,000 MATH outputs contain no extractable answer at all. Fine-tuning on '
       'MetaMathQA teaches both step-by-step reasoning and the answer format, so even rank 16 jumps to '
       f'{pct(g.iloc[1])} / {pct(m.iloc[1])}.', 'Baseline. ')
bullet(f'Accuracy rises monotonically with rank: GSM8K {pct(g.iloc[1])} → {pct(g.iloc[2])} → {pct(g.iloc[3])}, '
       f'MATH {pct(m.iloc[1])} → {pct(m.iloc[2])} → {pct(m.iloc[3])}. A larger rank gives more trainable parameters '
       '(0.9% → 3.6% → 14.6% of the model) and, with PiSSA, the adapter starts from a larger share of each weight\'s '
       'principal components, so the same learning rate and one epoch move a bigger, more important subspace. The final '
       'training loss drops accordingly (0.455 → 0.414 → 0.375).', 'Effect of rank. ')
bullet(f'GSM8K gains far more (+{g.iloc[3] - g.iloc[1]:.1f} points from rank 16 to 256) than MATH '
       f'(+{m.iloc[3] - m.iloc[1]:.1f}). GSM8K problems are short arithmetic word problems that closely match the '
       'MetaMathQA augmentations, and its gains have not saturated at rank 256. MATH needs competition-level knowledge '
       'and LaTeX-style answers (fractions, radicals, intervals) that a 1B model cannot acquire from 25k examples in one '
       'epoch; about 45% of MATH outputs still contain no parseable answer, so its curve flattens much sooner.',
       'Dataset difference. ')

# ---------------------------------------------------------------- Q2
heading('Question 2: Training time')
tune_cols = settings[1:]
table([''] + short[1:],
      [['Training Time (min.)'] + [f'{q2.loc["Training Time (min.)", s]:.1f}' for s in tune_cols],
       ['Trainable Parameters'] + [f'{q2.loc["Trainable Parameters", s] / 1e6:.1f} M' for s in tune_cols]],
      [3.6, 4.2, 4.2, 4.2])
tt = q2.loc['Training Time (min.)', tune_cols].astype(float).values
bullet(f'Going from rank 16 to 64 multiplies trainable parameters by 4× but adds only {tt[1] - tt[0]:.1f} minutes '
       f'(+{(tt[1] / tt[0] - 1) * 100:.0f}%); going to rank 256 (16× parameters) takes {tt[2]:.1f} minutes '
       f'(+{(tt[2] / tt[0] - 1) * 100:.0f}% over rank 16). Training time therefore grows with rank, but far slower than '
       'the parameter count.', 'Trend. ')
bullet('Each step is dominated by the forward and backward pass through the frozen 1.2B-parameter residual weights '
       'and by attention/activation work, which do not depend on the rank. The adapter adds two thin matmuls costing '
       'r(d+k) per token versus dk for the base weight: for a 2048×2048 projection that is about 1.6% extra at r = 16 '
       'but 25% at r = 256 (and its weight gradients must also be computed, unlike the frozen base). Rank 256 also has '
       '180M trainable parameters with FP32 AdamW states and gradients, adding optimizer-step time and memory traffic. '
       'So the cost is nearly flat at small ranks and becomes noticeable only when r is a sizeable fraction of the '
       'hidden size. The one-off SVD initialization (~100 s on the CPU) is excluded and is the same for every rank, '
       'since a full SVD is computed regardless of r.', 'Explanation. ')

# ---------------------------------------------------------------- Q3
heading('Question 3: Fine-tuning different singular-value ranges (rank 16)')
doc.add_picture(str(RESULTS / 'q3_components.png'), width=Cm(15.5))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
table(['Range'] + list(q3.index),
      [[task] + [pct(q3.loc[c, task]) for c in q3.index] for task in ['GSM8K', 'MATH']],
      [2.6, 3.4, 3.4, 3.4, 3.4])
Q3_BULLETS = [
    ('Trend. ',
     f'The top-16 (principal) range is clearly best on both datasets ({pct(q3.iloc[0, 0])} GSM8K, '
     f'{pct(q3.iloc[0, 1])} MATH). Moving the 16 directions down the spectrum lowers accuracy: '
     f'{pct(q3.iloc[1, 0])} / {pct(q3.iloc[2, 0])} / {pct(q3.iloc[3, 0])} on GSM8K and '
     f'{pct(q3.iloc[1, 1])} / {pct(q3.iloc[2, 1])} / {pct(q3.iloc[3, 1])} on MATH for the 25%, 50% and bottom ranges. '
     'The training loss shows the same order (average of the last 10 updates: 0.419 top, 0.462 25%, 0.467 50%, '
     '0.476 bottom). The non-principal ranges differ from each other by at most ~1 point, which is within the '
     'sampling noise of a 1,000-question test set (standard error ≈ 1.0 point on GSM8K, ≈ 0.5 on MATH), so they '
     'are essentially tied; only the gap to the top range is clear.'),
    ('Why the principal range wins. ',
     'With PiSSA the adapter is initialized as A = U_r√S_r, B = √S_r V_rᵀ, so the trainable part is exactly the '
     'selected slice of the weight and fine-tuning changes the model only inside that subspace. The top singular '
     'directions carry the most energy (Q4: the top 16 hold 15-35% of a q_proj\'s energy, a 16-wide band at the 25% '
     'or 50% position only ~0.1-0.7%) and correspond to the input/output directions the layer actually uses, so '
     'updating them changes the layer\'s behaviour most efficiently. The adapter factors are also larger, which makes '
     'their gradients (∂L/∂A ∝ B, ∂L/∂B ∝ A) larger and learning faster. Middle and bottom directions are small, '
     'nearly unused by the pretrained model, so a rank-16 update there is a weaker lever.'),
    ('Why the other ranges still learn. ',
     'Even the bottom range (σ ≈ 0) improves far beyond the original model (3.4% → '
     f'{pct(q3.iloc[3, 0])} GSM8K). AdamW normalizes each update by the gradient\'s running magnitude, so tiny '
     'factors still move by about the learning rate per step, and any 16-dimensional subspace is enough to learn '
     'the MetaMathQA answer format and some reasoning patterns. The principal subspace adds a further +3-4 points '
     'on GSM8K by also adapting the directions that matter most, consistent with the PiSSA paper\'s claim that '
     'tuning principal components converges faster and generalizes better than tuning the minor ones.'),
]
for prefix, text in Q3_BULLETS:
    bullet(text, prefix)

# ---------------------------------------------------------------- Q4
heading('Question 4: SVD of q_proj in the original model (layers 0, 7, 15)')
table(['', 'Layer 0', 'Layer 7', 'Layer 15'],
      [['Minimum Target Rank (≥ 50% energy)', '62', '120', '84'],
       ['σ1 / σ16', '31.4 / 5.7', '10.3 / 4.2', '12.9 / 4.7'],
       ['Energy in top 16 / top 200', '34.8% / 71.2%', '15.4% / 63.5%', '21.0% / 68.8%']],
      [5.2, 3.6, 3.6, 3.6])

grid = doc.add_table(rows=3, cols=2)
grid.alignment = WD_TABLE_ALIGNMENT.CENTER
for i, layer in enumerate([0, 7, 15]):
    for j, kind in enumerate(['singular_values', 'cumulative_energy']):
        cell = grid.cell(i, j)
        cell.width = Cm(8.6)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        p.add_run().add_picture(str(Q4_FIGS / f'layer{layer}_{kind}.png'), width=Cm(8.4))
para('Left: singular value magnitudes (bar charts). Right: cumulative energy (line charts). First 200 of 2,048 '
     'singular values; energy = Σσᵢ² / Σσ², dashed line = 50%.', size=8.5, italic=True,
     align=WD_ALIGN_PARAGRAPH.CENTER, after=2)

bullet('Every q_proj spectrum has a sharp head and a long, slowly decaying tail: a few large singular values '
       '(σ1 is 2-5× σ16) followed by an almost flat plateau. Reaching 50% energy needs only 62-120 of 2,048 '
       'directions (3-6% of full rank), but even the first 200 directions hold just 64-71% of the energy, so the '
       'weights are not truly low-rank; the remaining energy is spread thinly over hundreds of directions.',
       'Shape. ')
bullet('Layer 0 is the most concentrated (σ1 = 31.4 alone dominates; the top 16 hold 34.8% of the energy), layer 7 is '
       'the flattest (15.4% in the top 16, rank 120 needed) and layer 15 lies in between (rank 84). The first layer '
       'works directly on token embeddings, where a few dominant directions (e.g. common-token and position-related '
       'features) carry most of the signal; middle layers mix many distributed features, so their queries use more '
       'directions; the last layers specialize again toward next-token prediction.', 'Layer differences. ')
bullet('A fixed adapter rank therefore captures a very different share of each layer: rank 16 covers about 35% of '
       'layer 0\'s energy but only 15% of layer 7\'s. This supports PiSSA\'s idea of adapting the principal '
       'subspace, and suggests that layer-wise (adaptive) rank allocation would use a parameter budget more evenly.',
       'Implication. ')

out_docx = HERE / f'{NAME}.docx'
doc.save(out_docx)
print('Saved', out_docx)

if '--pdf' in sys.argv:
    import win32com.client
    word = win32com.client.DispatchEx('Word.Application')
    word.Visible = False
    try:
        d = word.Documents.Open(str(out_docx))
        d.ExportAsFixedFormat(str(HERE / f'{NAME}.pdf'), 17)  # 17 = wdExportFormatPDF
        print('Pages:', d.ComputeStatistics(2))  # 2 = wdStatisticPages
        d.Close(False)
    finally:
        word.Quit()
    print('Saved', HERE / f'{NAME}.pdf')
