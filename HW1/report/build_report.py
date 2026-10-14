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
GITHUB = 'https://github.com/CH-Joshua-Hsiao/NYCU-BigDataAnalytics/tree/main/HW1'

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
    p.paragraph_format.keep_with_next = True
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
para('Setup: I fine-tuned Llama-3.2-1B with PiSSA on 25,000 MetaMathQA samples (1 epoch, learning rate 2e-5, '
     'batch size 128, FP16, all 7 projection layers). I tested on 1,000 GSM8K and 1,000 MATH questions. All runs used '
     'one RTX 3090 (24 GB) on my own computer, with micro-batch 4 and 32 accumulation steps. The SVD step ran on the CPU.',
     size=9, italic=True, after=2)

# ---------------------------------------------------------------- Q1
heading('Question 1: Accuracy of the original and fine-tuned models')
settings = list(q1.columns)
short = ['Original LLM', 'Fine-Tuned (RANK = 16)', 'Fine-Tuned (RANK = 64)', 'Fine-Tuned (RANK = 256)']
table(['Accuracy'] + short,
      [[task] + [pct(q1.loc[task, s]) for s in settings] for task in ['GSM8K', 'MATH']],
      [2.6, 3.2, 3.6, 3.6, 3.8])

g, m = q1.loc['GSM8K'], q1.loc['MATH']
bullet(f'The original model is very weak: {pct(g.iloc[0])} on GSM8K and {pct(m.iloc[0])} on MATH. It is a base '
       'model, not a chat model, so it does not really solve the question. In about half of the answers, it just '
       'repeats the same sentence again and again. Only 37 GSM8K answers and 41 MATH answers give a clear final answer (like '
       '"The answer is:", "####" or \\boxed{}). For MATH, 959 answers have no answer that the parser can find. After '
       'fine-tuning on MetaMathQA, the model learns to solve step by step and to write the answer in the right format. '
       f'So even rank 16 goes up to {pct(g.iloc[1])} / {pct(m.iloc[1])}.', 'Original model. ')
bullet(f'When the rank is bigger, the accuracy is higher on both datasets: GSM8K {pct(g.iloc[1])} → {pct(g.iloc[2])} '
       f'→ {pct(g.iloc[3])}, and MATH {pct(m.iloc[1])} → {pct(m.iloc[2])} → {pct(m.iloc[3])}. A bigger rank means more '
       'trainable parameters (0.9% → 3.6% → 14.6% of the model). Also, in PiSSA, a bigger rank means the adapter starts '
       'from more of the main (principal) parts of the weight. So with the same learning rate and one epoch, the model '
       'can change more. The final training loss also goes down (0.455 → 0.414 → 0.375).', 'Effect of rank. ')
bullet('I also checked if the model only learns the answer format. The table below shows how many answers have a '
       'clear final answer, and the accuracy of these answers. On GSM8K, the number is almost the same after rank 16 '
       '(951, 957, 954), so the format is already learned. But the accuracy still goes up (16.4% → 21.6% → 28.6%). '
       'This means a bigger rank really helps the reasoning, not only the format. On MATH, both become better: more '
       'clear answers (452 → 547) and higher accuracy (8.2% → 9.9%). However, the reasoning is still not good. Many '
       'answers have a nice format but wrong calculation.', 'Format or reasoning? ')
table(['Clear final answers (accuracy of them)'] + short,
      [['GSM8K', '37 (13.5%)', '951 (16.4%)', '957 (21.6%)', '954 (28.6%)'],
       ['MATH', '41 (2.4%)', '452 (8.2%)', '523 (9.2%)', '547 (9.9%)']],
      [4.2, 2.9, 3.3, 3.3, 3.4])
bullet(f'GSM8K improves much more than MATH (+{g.iloc[3] - g.iloc[1]:.1f} points vs. +{m.iloc[3] - m.iloc[1]:.1f} '
       'points from rank 16 to 256). GSM8K questions are simple word problems, and they are similar to the MetaMathQA '
       'training data. Its accuracy is still going up at rank 256. MATH questions are much harder. They need more math '
       'knowledge and answers in LaTeX form (fractions, square roots, intervals). A 1B model cannot learn this from 25k '
       'samples in one epoch. About 45% of MATH answers still have no answer that the parser can find, so MATH improves '
       'only a little.', 'GSM8K vs. MATH. ')

# ---------------------------------------------------------------- Q2
heading('Question 2: Training time')
tune_cols = settings[1:]
table([''] + short[1:],
      [['Training Time (min.)'] + [f'{q2.loc["Training Time (min.)", s]:.1f}' for s in tune_cols],
       ['Trainable Parameters'] + [f'{q2.loc["Trainable Parameters", s] / 1e6:.1f} M' for s in tune_cols]],
      [3.6, 4.2, 4.2, 4.2])
tt = q2.loc['Training Time (min.)', tune_cols].astype(float).values
bullet(f'From rank 16 to 64, the trainable parameters become 4 times more, but the training time only increases by '
       f'{tt[1] - tt[0]:.1f} minutes (+{(tt[1] / tt[0] - 1) * 100:.0f}%). From rank 16 to 256, the parameters become 16 '
       f'times more, and the time becomes {tt[2]:.1f} minutes (+{(tt[2] / tt[0] - 1) * 100:.0f}%). So the training time '
       'increases with the rank, but much slower than the number of parameters.', 'Trend. ')
bullet('Most of the training time is used to run the big frozen model (1.2B parameters) forward and backward. This '
       'part does not depend on the rank. The adapter only adds two small matrix multiplications. Their cost is '
       'r(d+k), while the original weight costs dk. For a 2048×2048 layer, this is only about 1.6% more at r = 16, but '
       'about 25% more at r = 256. The adapter also needs its own weight gradients. In addition, rank 256 has 180M '
       'trainable parameters, and AdamW keeps extra states for each of them, so the optimizer step is also slower. '
       'That is why the time is almost the same for small ranks, and only becomes clearly longer at rank 256. The SVD '
       'step at the beginning (about 100 seconds on the CPU) is not included. It takes the same time for all ranks, '
       'because the code always computes the full SVD.', 'Reason. ')

# ---------------------------------------------------------------- Q3
heading('Question 3: Fine-tuning different singular-value ranges (rank 16)')
doc.add_picture(str(RESULTS / 'q3_components.png'), width=Cm(15.5))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
table(['Range'] + list(q3.index),
      [[task] + [pct(q3.loc[c, task]) for c in q3.index] for task in ['GSM8K', 'MATH']],
      [2.6, 3.4, 3.4, 3.4, 3.4])
Q3_BULLETS = [
    ('Trend. ',
     f'The top 16 singular values give the best result on both datasets ({pct(q3.iloc[0, 0])} on GSM8K, '
     f'{pct(q3.iloc[0, 1])} on MATH). When we use smaller singular values, the accuracy becomes lower: '
     f'{pct(q3.iloc[1, 0])} / {pct(q3.iloc[2, 0])} / {pct(q3.iloc[3, 0])} on GSM8K and '
     f'{pct(q3.iloc[1, 1])} / {pct(q3.iloc[2, 1])} / {pct(q3.iloc[3, 1])} on MATH (from 25%, from 50%, bottom). '
     'The training loss has the same order (average of the last 10 steps: 0.419, 0.462, 0.467, 0.476). The three '
     'non-top ranges are very close, within about 1 point. With only 1,000 test questions, the random error is about '
     '1 point on GSM8K and 0.5 point on MATH. So I think these three are about the same, and only the top 16 is clearly '
     'better. The top 16 is better in both format and reasoning: on GSM8K it gives more clear answers (951 vs. '
     '859-904), and these answers are more accurate (16.4% vs. 12.8-13.5%).'),
    ('Why the top 16 is the best. ',
     'In PiSSA, the adapter starts as A = U_r√S_r and B = √S_r V_rᵀ. So the model can only change the part of the '
     'weight that we choose. The top singular values have most of the energy. From Q4, the top 16 have 15-35% of the '
     'energy of q_proj, but 16 values at the 25% or 50% position have only about 0.1-0.7%. These top directions are '
     'the ones the layer really uses, so changing them has the biggest effect. Also, A and B are bigger at the start, '
     'so their gradients are bigger (∂L/∂A ∝ B, ∂L/∂B ∝ A), and the model learns faster. The middle and bottom '
     'directions are very small and the original model almost does not use them, so changing them helps less.'),
    ('Why the other ranges still work. ',
     'Even the bottom 16 (singular values close to 0) is much better than the original model (3.4% → '
     f'{pct(q3.iloc[3, 0])} on GSM8K). One reason is AdamW: it scales each update by the gradient size, so even very '
     'small A and B still move about one learning rate per step. Also, 16 dimensions are enough to learn the answer '
     'format and some simple reasoning. Using the top 16 gives about 3-4 more points on GSM8K. This matches the PiSSA '
     'paper, which says that training the principal parts learns faster and works better than training the small '
     'parts.'),
]
for prefix, text in Q3_BULLETS:
    bullet(text, prefix)

# ---------------------------------------------------------------- Q4
heading('Question 4: SVD of q_proj in the original model (layers 0, 7, 15)')
table(['', 'Layer 0', 'Layer 7', 'Layer 15'],
      [['Minimum Target Rank for query projection weights (≥ 50% energy)', '62', '120', '84'],
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
para('Left: singular value magnitude (bar chart). Right: cumulative energy (line chart). Only the first 200 of 2,048 '
     'singular values are shown. Energy = Σσᵢ² / Σσ². The dashed line is 50%.', size=8.5, italic=True,
     align=WD_ALIGN_PARAGRAPH.CENTER, after=2)

bullet('All three layers have a similar shape. There are a few large singular values at the beginning (σ1 is about '
       '2.5-5.5 times σ16), and then a long and almost flat tail. To keep 50% of the energy, we only need 62-120 of the 2,048 '
       'values (3-6% of the full rank). But even the first 200 values only keep 63-71% of the energy. So the weight is '
       'not really low-rank. The rest of the energy is spread over many small values.', 'Shape. ')
bullet('Layer 0 is the most concentrated. σ1 = 31.4 is much bigger than the others, and the top 16 have 34.8% of the '
       'energy. Layer 7 is the most spread out (only 15.4% in the top 16, and it needs rank 120). Layer 15 is in the '
       'middle (rank 84). My guess is that layer 0 works directly on the token embeddings, so a few main directions '
       'carry most of the information. Middle layers mix many different features, so they use more directions. The '
       'last layers focus more again on predicting the next token.', 'Differences between layers. ')
bullet('If we use the same rank for every layer, each layer keeps a very different amount of energy. For example, '
       'rank 16 keeps about 35% of the energy in layer 0, but only 15% in layer 7. This supports the idea of PiSSA '
       '(training the principal part). It also suggests that giving different ranks to different layers may use the '
       'parameters better.', 'What this means. ')

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
