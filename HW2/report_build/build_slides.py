"""Build Asg2_413551034.pptx ON the official course template.

Loads "Big Data Course - Assignment 2 (Slide Template).pptx" (10 x 5.625 in, navy #344394),
keeps its title slide + the four (X%) Question N divider slides, and inserts our content
slides between them, re-using a 0.75 scale from the original 13.333x7.5 authoring space
(both are 16:9). Final deck = 16 pages, within the <=16 limit.

Run from HW2/report_build/ with the venv python. Figures are read from ../artifacts/;
the template is read from the HW2 root.
"""
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / "artifacts"
TEMPLATE = ROOT / "Big Data Course - Assignment 2 (Slide Template).pptx"
OUT = Path(__file__).resolve().parent / "Asg2_413551034.pptx"
SID = "413551034"
REPO = "github.com/CH-Joshua-Hsiao/NYCU-BigDataAnalytics/tree/main/HW2"
TOTAL = 16

# Template palette
NAVY = RGBColor(0x34, 0x43, 0x94)      # the template's heading navy (#344394)
INK = RGBColor(0x22, 0x30, 0x3F)
BLUE = RGBColor(0x2D, 0x6C, 0xB5)
GREEN = RGBColor(0x2E, 0x8B, 0x57)
GOLD = RGBColor(0xC8, 0x91, 0x2A)
RED = RGBColor(0xB0, 0x38, 0x2F)
GREY = RGBColor(0x6B, 0x7A, 0x8A)
LIGHT = RGBColor(0xF1, 0xF4, 0xF7)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
HEAD = "Arial"      # template requests Helvetica Neue -> renders Arial on Windows
BODY = "Arial"

# ---- scale: author in 13.333x7.5 coordinates, render on the 10x5.625 template ----
S = 0.75
def IN(v):
    return Inches(v * S)
def PTS(v):
    return Pt(v * S)

prs = Presentation(str(TEMPLATE))
SW, SH = prs.slide_width, prs.slide_height
BLANK = prs.slide_layouts[10]          # BLANK layout in the template

# template slides already present: 0 title, 1 Q1, 2 Q2, 3 Q3, 4 Q4
TPL_TITLE, TPL_Q1, TPL_Q2, TPL_Q3, TPL_Q4 = (prs.slides[i] for i in range(5))


def new_slide(bg=WHITE):
    s = prs.slides.add_slide(BLANK)
    # drop any inherited placeholder (BLANK layout carries one)
    for ph in list(s.placeholders):
        ph._element.getparent().remove(ph._element)
    r = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SW, SH)
    r.fill.solid(); r.fill.fore_color.rgb = bg; r.line.fill.background()
    r.shadow.inherit = False
    s.shapes._spTree.remove(r._element); s.shapes._spTree.insert(2, r._element)
    return s


def tb(s, x, y, w, h, anchor=MSO_ANCHOR.TOP):
    box = s.shapes.add_textbox(IN(x), IN(y), IN(w), IN(h))
    tf = box.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = 0; tf.margin_right = 0; tf.margin_top = 0; tf.margin_bottom = 0
    return tf


def para(tf, runs, size=16, color=INK, bold=False, align=PP_ALIGN.LEFT, space_after=6,
         bullet=False, first=False, font=BODY, line=None):
    p = tf.paragraphs[0] if first and not tf.paragraphs[0].runs else tf.add_paragraph()
    p.alignment = align
    if space_after is not None:
        p.space_after = PTS(space_after)
    if line:
        p.line_spacing = line
    if isinstance(runs, str):
        runs = [(runs, {})]
    for text, opt in runs:
        r = p.add_run(); r.text = text
        f = r.font
        f.size = PTS(opt.get("size", size)); f.name = opt.get("font", font)
        f.bold = opt.get("bold", bold); f.italic = opt.get("italic", False)
        f.color.rgb = opt.get("color", color)
    if bullet:
        _bullet(p)
    return p


def _bullet(p):
    from pptx.oxml.ns import qn
    pPr = p._pPr if p._pPr is not None else p.get_or_add_pPr()
    pPr.set("indent", "-171450"); pPr.set("marL", "171450")
    bu = pPr.makeelement(qn("a:buChar"), {"char": "•"})
    buf = pPr.makeelement(qn("a:buFont"), {"typeface": "Arial"})
    pPr.append(buf); pPr.append(bu)


def title(s, text, sub=None, color=NAVY):
    tf = tb(s, 0.6, 0.55, 12.1, 1.1)
    para(tf, text, size=28, color=color, bold=True, first=True, font=HEAD, space_after=2)
    if sub:
        para(tf, sub, size=14, color=GREY, space_after=0)


def badge(s, text, color, x=0.6, y=0.28):
    b = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, IN(x), IN(y), IN(2.0), IN(0.42))
    b.fill.solid(); b.fill.fore_color.rgb = color; b.line.fill.background(); b.shadow.inherit = False
    tf = b.text_frame; tf.margin_top = 0; tf.margin_bottom = 0
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = text; r.font.size = PTS(13); r.font.bold = True
    r.font.color.rgb = WHITE; r.font.name = HEAD


def footer(s, n):
    tf = tb(s, 0.6, 7.08, 12.1, 0.3)
    para(tf, [(f"Asg2 · {SID}", {"color": GREY, "size": 10}),
              (f"     ·     {n} / {TOTAL}", {"color": GREY, "size": 10})], first=True, space_after=0)


def picture(s, path, x, y, w=None, h=None):
    im = Image.open(path); ar = im.size[0] / im.size[1]
    if w and not h:
        h = w / ar
    elif h and not w:
        w = h * ar
    s.shapes.add_picture(str(path), IN(x), IN(y), IN(w), IN(h))
    return w, h


def card(s, x, y, w, h, fill=LIGHT):
    c = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, IN(x), IN(y), IN(w), IN(h))
    c.fill.solid(); c.fill.fore_color.rgb = fill; c.line.color.rgb = RGBColor(0xDD, 0xE3, 0xEA)
    c.line.width = Pt(0.75); c.shadow.inherit = False
    return c


def bar(s, x, y, w, color, h=0.12):
    b = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, IN(x), IN(y), IN(w), IN(h))
    b.fill.solid(); b.fill.fore_color.rgb = color; b.line.fill.background(); b.shadow.inherit = False
    return b


def numbered(s, items, y0=1.75, dy=1.45, bh=1.4):
    y = y0
    for num, col, head, body in items:
        c = s.shapes.add_shape(MSO_SHAPE.OVAL, IN(0.7), IN(y), IN(0.6), IN(0.6))
        c.fill.solid(); c.fill.fore_color.rgb = col; c.line.fill.background(); c.shadow.inherit = False
        ptf = c.text_frame; ptf.margin_top = 0; ptf.margin_bottom = 0
        pp = ptf.paragraphs[0]; pp.alignment = PP_ALIGN.CENTER
        rr = pp.add_run(); rr.text = num; rr.font.size = PTS(19); rr.font.bold = True; rr.font.color.rgb = WHITE
        tf = tb(s, 1.55, y - 0.05, 11.1, bh)
        para(tf, head, size=17, color=NAVY, bold=True, first=True, space_after=3)
        para(tf, body, size=13.5, color=INK, space_after=0)
        y += dy


def notes(s, text):
    s.notes_slide.notes_text_frame.text = text


# ================================================================ TEMPLATE slide 1: title
# add Student ID + repo link in a dedicated box above the template footer (real inches)
box = TPL_TITLE.shapes.add_textbox(Inches(1.65), Inches(4.78), Inches(7.0), Inches(0.5))
_tf = box.text_frame; _tf.word_wrap = True
_tf.margin_left = 0; _tf.margin_right = 0; _tf.margin_top = 0; _tf.margin_bottom = 0
_p = _tf.paragraphs[0]
_r = _p.add_run(); _r.text = "Student ID " + SID; _r.font.size = Pt(11); _r.font.bold = True
_r.font.color.rgb = NAVY; _r.font.name = HEAD
_p2 = _tf.add_paragraph()
_r = _p2.add_run(); _r.text = REPO; _r.font.size = Pt(9.5); _r.font.color.rgb = BLUE; _r.font.name = HEAD
notes(TPL_TITLE, "〔約 1:00〕大家好,我是學號 413551034。這次作業二的題目是預測 GitHub 使用者的活動。\n"
      "我們要對測試集裡的 4,465 位使用者,預測他們在 2026/11/22–11/29 這一週(台灣時間)會不會做出六種 GitHub 活動。\n"
      "資料來源是 GH Archive 的每小時事件,經過官方 preprocess.py 轉成 8 張用外鍵互相連結的關聯式資料表。\n"
      "程式都放在這個公開的 GitHub repo。接下來先說明題目、資料跟評分方式。")

# ================================================================ content: Task & data (page 2)
s_task = new_slide()
badge(s_task, "Overview", BLUE)
title(s_task, "The Task, the Data, the Metric", "Predict 6 activities per user for 2026/11/22–11/29 (Taiwan time)")
tf = tb(s_task, 0.6, 1.7, 6.8, 4.8)
para(tf, [("Goal.  ", {"bold": True, "color": NAVY}), ("For each of the 4,465 test users, output a 0/1 for "
          "each of six activities during the test week.", {})], first=True, size=15, space_after=9)
para(tf, [("Data.  ", {"bold": True, "color": NAVY}), ("Hourly GH Archive events, turned into 8 anonymized, "
          "foreign-key-linked tables by the official preprocess.py (ids hashed, text masked).", {})], size=15, space_after=9)
para(tf, [("Rules.  ", {"bold": True, "color": NAVY}), ("Use only those 8 tables; split train/validation by "
          "time; for a prediction at time t use only rows visible before t.", {})], size=15, space_after=9)
para(tf, [("Metric.  ", {"bold": True, "color": NAVY}), ("Score = (macro-F1 + micro-F1) / 2 over the 6 activities.", {})], size=15, space_after=0)
card(s_task, 7.8, 1.7, 4.9, 4.55)
tf = tb(s_task, 8.1, 1.95, 4.3, 4.1)
para(tf, "The 6 target activities", size=14, color=NAVY, bold=True, first=True, space_after=7)
for a, d in [("open_pr", "open a pull request"), ("open_issue", "open an issue (not a PR)"),
             ("issue_comment", "comment in an issue / PR thread"), ("pr_review", "submit a PR review"),
             ("pr_review_comment", "comment on PR code lines"), ("push", "push commits to a branch/tag")]:
    para(tf, [(a, {"bold": True, "color": BLUE, "font": "Consolas", "size": 12.5}), (f"  —  {d}", {"size": 12.5})], space_after=6)
footer(s_task, 2)
notes(s_task, "〔約 1:45|累計 2:45〕先看題目:對每位測試使用者輸出六個 0/1,代表這六種活動——開 PR、開 issue、"
      "在 issue/PR 留言、送出 PR review、在程式碼行上留 review comment、push commit。\n"
      "資料:GH Archive 每小時事件,官方腳本轉成 8 張匿名化、用外鍵連結的表。\n"
      "規則三重點:只能用這 8 張表;依時間切分;時間點 t 只能用 t 之前看得到的列。\n"
      "評分 Score = (macro-F1 + micro-F1)/2。核心難點就是兩件事:跨表關聯(Q2)與時間(Q3)。")

# ================================================================ TEMPLATE slide 2: Q1 divider
notes(TPL_Q1, "〔約 0:15〕接下來回答第一題:畫出 schema 關聯圖,並說明我用到的資料時間區間。")

# ================================================================ content: schema (page 4)
s_sch = new_slide()
badge(s_sch, "Q1 · Schema", GREEN)
title(s_sch, "Schema Graph & Dataset Time Period")
picture(s_sch, ART / "schema_graph.png", 6.55, 1.7, h=5.1)
tf = tb(s_sch, 0.6, 1.75, 4.7, 4.9)
para(tf, "Schema", size=14, color=NAVY, bold=True, first=True, space_after=3)
para(tf, "8 tables; every primary key (PK) is a row number and every foreign key (FK) points to one. "
        "Arrows go FK → referenced PK.", size=12.5, space_after=8)
para(tf, "Row-time", size=14, color=NAVY, bold=True, space_after=3)
para(tf, "Each table has a time it becomes visible (first_seen_at, or created_at for comments/pushes). "
        "Features at time t use only rows with row-time < t.", size=12.5, space_after=8)
para(tf, "Dataset time period", size=14, color=NAVY, bold=True, space_after=3)
para(tf, [("Raw GH Archive: ", {"bold": True}), ("2026-10-04 → 11-16 (UTC)", {})], size=12.5, space_after=2)
para(tf, [("Training weeks: ", {"bold": True}), ("Oct 13 / 20 / 27 cutoffs", {})], size=12.5, space_after=2)
para(tf, [("Validation: ", {"bold": True}), ("Nov 3 → Nov 10", {})], size=12.5, space_after=2)
para(tf, [("Prediction: ", {"bold": True}), ("Nov 22 → Nov 29 (Taiwan)", {})], size=12.5, space_after=0)
footer(s_sch, 4)
notes(s_sch, "〔約 2:00|累計 5:00〕這是 8 張表的 schema 關聯圖。金色 PK 是主鍵,綠色 FK 是外鍵,箭頭 FK→PK。\n"
      "Users 跟 Repositories 是兩個樞紐,幾乎所有事件表都指向它們。\n"
      "左邊標了每張表的可見時間 row-time(多為 first_seen_at,留言/push 用 created_at);算 t 時刻特徵只用 row-time < t 的列,避免偷看未來。\n"
      "資料區間:原始 10/04–11/16;訓練切點 10/13、20、27;驗證週 11/03–10;預測週 11/22–29。最終版我會在截止前把資料下載到 11/21 再重跑。")

# ================================================================ content: read the 8 tables (page 5)
s_er = new_slide()
badge(s_er, "Q1 · Relations", GREEN)
title(s_er, "How to Read the 8 Tables", "Two hubs + six event tables — every event is a user acting in a repo")
tf = tb(s_er, 0.6, 1.7, 7.0, 5.0)
para(tf, [("Two hub entities.  ", {"bold": True, "color": NAVY}),
          ("Users (user_id) and Repositories (repo_id). Almost every other table points to them via "
           "author_id / user_id and repo_id.", {})], first=True, size=14, space_after=9)
para(tf, [("Six event tables.  ", {"bold": True, "color": NAVY}),
          ("PullRequests, Issues, IssueComments, PRReviews, PRReviewComments, Pushes. One row = one "
           "action: a user, a repo, and a time.", {})], size=14, space_after=9)
para(tf, [("Foreign-key chains.  ", {"bold": True, "color": NAVY}),
          ("A review points to its PR; a review comment points to its PR and review; an issue comment "
           "points to its issue. Comments and reviews inherit repo_id too.", {})], size=14, space_after=9)
para(tf, [("Why it matters.  ", {"bold": True, "color": NAVY}),
          ("Follow repo_id to reach co-workers in the same repo; follow author_id to reach a user's "
           "history elsewhere. That is what the relational features (Q2) exploit.", {})], size=14, space_after=0)
card(s_er, 7.9, 1.7, 4.8, 4.75)
tf = tb(s_er, 8.2, 1.95, 4.2, 4.3)
para(tf, "Each activity → its source table", size=13.5, color=NAVY, bold=True, first=True, space_after=7)
for a, d in [("open_pr", "PullRequests · author_id"), ("open_issue", "Issues · author_id"),
             ("issue_comment", "IssueComments · author_id"), ("pr_review", "PRReviews · reviewer_id"),
             ("pr_review_comment", "PRReviewComments · author_id"), ("push", "Pushes · user_id")]:
    para(tf, [(a, {"bold": True, "color": GREEN, "font": "Consolas", "size": 12})], space_after=1)
    para(tf, d, size=11.5, color=GREY, space_after=7)
footer(s_er, 5)
notes(s_er, "〔約 1:30|累計 6:30〕這頁幫大家讀懂 8 張表怎麼關聯,也是 Q2 的基礎。\n"
      "兩個樞紐 Users / Repositories;六張事件表每一列就是一次行為——某人、某 repo、某時間。\n"
      "外鍵鏈:review→PR;review comment→PR 和 review;issue comment→issue;留言/review 也都帶 repo_id。\n"
      "沿 repo_id 找同 repo 協作者,沿 author_id 找一個人在別處的歷史——這正是 Q2 關聯特徵在用的。右表列出六個活動各自來自哪張表、哪個欄位。")

# ================================================================ TEMPLATE slide 3: Q2 divider
notes(TPL_Q2, "〔約 0:15〕第二題:說明我怎麼強化『跨資料表關聯』的建模。")

# ================================================================ content: Q2 approach (page 7)
s_q2a = new_slide()
badge(s_q2a, "Q2 · Approach", GOLD)
title(s_q2a, "Modeling Relationships Across Tables")
numbered(s_q2a, [
    ("1", BLUE, "Foreign-key join features",
     "Join User–PR–Review–Issue–Comment: reviews & comments your work received, distinct "
     "reviewers/collaborators, reviews you gave, repo & org breadth."),
    ("2", GREEN, "Repo-neighborhood aggregation",
     "For the repos a user touches, aggregate their recent activity and the number of other active "
     "users — your collaborative community's momentum."),
    ("3", GOLD, "Time-aware heterogeneous GNN (RelBench-style)",
     "A user–repo graph with 6 FK-derived edge types; message passing spreads information from a "
     "user to its repos and back to 2-hop collaborators."),
])
footer(s_q2a, 7)
notes(s_q2a, "〔約 1:45|累計 8:30〕Q2 我用三個做法。\n"
      "① 外鍵 join 特徵:串 User–PR–Review–Issue–Comment,算收到多少 review/留言、多少不同人合作、送出多少 review、repo/組織廣度。\n"
      "② repo 鄰域聚合:使用者碰過的 repo 最近活動量與活躍人數,代表社群動能。\n"
      "③ 時間感知異質 GNN(RelBench/RDL):使用者–repo 圖,6 種外鍵邊,訊息從使用者傳到 repo 再回到兩跳外協作者。\n"
      "前兩個給樹模型,第三個是圖神經網路。下一頁看有沒有幫助。")

# ================================================================ content: Q2 findings (page 8)
s_q2f = new_slide()
badge(s_q2f, "Q2 · Findings", GOLD)
title(s_q2f, "What the Relationships Contribute", "Honest result: on this sparse cohort, structure adds little")
stats = [("≈ 0", BLUE, "GBDT without relational features", "33.1 → 33.6 Score (neutral)"),
         ("−8.5", RED, "Adding GNN message passing", "node-MLP 30.3 → FK-graph 21.8"),
         ("win", GREEN, "Best model stays", "GBDT on temporal+relational features")]
x = 0.6
for big, col, head, sub in stats:
    card(s_q2f, x, 1.8, 3.9, 2.3)
    tf = tb(s_q2f, x + 0.3, 2.0, 3.3, 1.9)
    para(tf, big, size=38, color=col, bold=True, first=True, space_after=2, font=HEAD)
    para(tf, head, size=13.5, color=NAVY, bold=True, space_after=3)
    para(tf, sub, size=12, color=GREY, space_after=0)
    x += 4.15
tf = tb(s_q2f, 0.6, 4.45, 12.1, 2.1)
para(tf, "Why?", size=15, color=NAVY, bold=True, first=True, space_after=4)
para(tf, "Next-week activity is driven mostly by a user's own recent history (strong temporal "
        "autocorrelation). The user–repo graph is sparse, so mean-aggregation over-smooths and the GNN "
        "loses the per-user signal. Relational deep learning helps when cross-entity interaction is dense; "
        "here, time dominates — a useful finding about when RDL pays off.", size=14, space_after=0)
footer(s_q2f, 8)
notes(s_q2f, "〔約 1:45|累計 10:15〕誠實報告:稀疏群體上關聯結構幫助很小。\n"
      "① GBDT 拿掉關聯特徵 33.1→33.6,幾乎沒差。② 加上 FK 圖的訊息傳遞反而掉約 8.5 分,節點特徵 30.3→FK 圖 21.8。③ 最好的還是 GBDT(時間+關聯)。\n"
      "為什麼?下一週活動主要由使用者自己最近行為決定(強時間自相關);圖很稀疏,平均聚合把訊號抹平。\n"
      "RDL 在跨實體互動密集時才發威;這題時間主導。我也用每活動 AUC 驗證:一加訊息傳遞 AUC 約掉到 0.5。")

# ================================================================ TEMPLATE slide 4: Q3 divider
notes(TPL_Q3, "〔約 0:15〕第三題:說明我怎麼強化『時間資訊』的建模——這也是我方法的核心。")

# ================================================================ content: Q3 approach (page 10)
s_q3a = new_slide()
badge(s_q3a, "Q3 · Approach", BLUE)
title(s_q3a, "Modeling Temporal Information")
numbered(s_q3a, [
    ("1", BLUE, "Multi-scale temporal features",
     "Per-activity counts over 1 / 7 / 14 / 30 / 90-day windows, days-since-last (recency), distinct "
     "active days, and 7-day momentum / ratio — including the strong copy-last-week signal."),
    ("2", GREEN, "Strict leakage control",
     "Only rows with row-time < t are visible; never filter by created_at / submitted_at (rows arrive "
     "late); never use known-only-later columns (merged_at, closed_at, state_reason, dismissed_at)."),
    ("3", GOLD, "Time-encoded GNN edges",
     "Each edge carries its age; a neighbour's message is weighted exp(−age / τ), so recent "
     "interactions count more than old ones."),
], bh=1.35)
ty = 6.35
ln = s_q3a.shapes.add_shape(MSO_SHAPE.RECTANGLE, IN(1.55), IN(ty), IN(9.5), IN(0.02))
ln.fill.solid(); ln.fill.fore_color.rgb = GREY; ln.line.fill.background(); ln.shadow.inherit = False
mk = s_q3a.shapes.add_shape(MSO_SHAPE.RECTANGLE, IN(7.05), IN(ty - 0.16), IN(0.03), IN(0.32))
mk.fill.solid(); mk.fill.fore_color.rgb = RED; mk.line.fill.background(); mk.shadow.inherit = False
tf = tb(s_q3a, 1.55, ty + 0.05, 5.4, 0.3); para(tf, "features: all history with row-time < t", size=10.5, color=GREY, first=True, space_after=0)
tf = tb(s_q3a, 7.1, ty + 0.05, 4.0, 0.3); para(tf, "labels: next 7 days", size=10.5, color=RED, first=True, space_after=0)
tf = tb(s_q3a, 6.82, ty - 0.42, 1.2, 0.3); para(tf, "t", size=11, color=RED, bold=True, first=True, space_after=0)
footer(s_q3a, 10)
notes(s_q3a, "〔約 2:00|累計 12:30〕Q3 時間建模,三個重點。\n"
      "① 多尺度時間特徵:每活動算 1/7/14/30/90 天窗口次數、recency、活躍天數、7 天動能;含很強的『參考上一週』訊號。\n"
      "② 嚴格防洩漏:只有 row-time < t 看得到;不用 created_at/submitted_at 判斷可見性;不用事後欄位(merged_at、closed_at…)。\n"
      "③ 時間編碼進 GNN 的邊:每條邊帶年齡,鄰居訊息以 exp(−age/τ) 加權。\n"
      "下方時間軸:t 之前歷史當特徵,接下來 7 天當標籤。")

# ================================================================ content: Q3 findings (page 11)
s_q3f = new_slide()
badge(s_q3f, "Q3 · Findings", BLUE)
title(s_q3f, "Temporal Signal Dominates", "Removing temporal features costs the most")
picture(s_q3f, ART / "chart_ablation.png", 0.5, 1.7, w=6.0)
picture(s_q3f, ART / "chart_per_activity.png", 6.75, 1.9, w=6.3)
tf = tb(s_q3f, 0.6, 6.05, 12.1, 1.0)
para(tf, [("Removing temporal features: 33.1 → 29.0 Score (−4.1) — the largest drop of any group. "
          "Copy-last-week alone scores 29.3. ", {"bold": True, "color": NAVY}),
          ("Per activity, regular behaviours (open_issue, pr_review) are easier than bursty ones "
           "(push, pr_review_comment).", {})], first=True, size=13, space_after=0)
footer(s_q3f, 11)
notes(s_q3f, "〔約 1:30|累計 14:00〕兩張圖說明時間建模效果。\n"
      "左圖消融:拿掉時間特徵 33.1→29.0,掉 4.1 分,是最大跌幅;對照『照抄上一週』就有 29.3 分。\n"
      "右圖各活動 F1:規律型(open_issue、pr_review)好預測;爆發型(push、程式碼行 review comment)較難。\n"
      "所以時間建模是這任務最主要的訊號來源。")

# ================================================================ TEMPLATE slide 5: Q4 divider
notes(TPL_Q4, "〔約 0:15〕第四題:給出整體架構圖,並說明完整的 pipeline。")

# ================================================================ content: framework (page 13)
s_fw = new_slide()
badge(s_fw, "Q4 · Framework", GREEN)
title(s_fw, "Framework")
w8, h8 = picture(s_fw, ART / "framework.png", 0, 1.7, h=4.9)
s_fw.shapes[-1].left = IN((13.333 - w8) / 2)
footer(s_fw, 13)
notes(s_fw, "〔約 1:15|累計 15:30〕Q4 整體架構一頁總覽。\n"
      "從左到右:GH Archive 每小時事件 → preprocess.py → 8 張關聯表 → 三條平行分支(時間特徵、關聯特徵、時間感知 GNN)餵進模型。\n"
      "中間的 leakage gate 卡在資料層,每條分支只看得到過去。最後經模型與門檻產出提交檔。下一頁拆開講。")

# ================================================================ content: pipeline (page 14)
s_pl = new_slide()
badge(s_pl, "Q4 · Pipeline", GREEN)
title(s_pl, "The Full Pipeline, Step by Step")
steps = [
    ("Preprocess", "Download GH Archive hours → official preprocess.py → 8 anonymized tables (one Parquet each)."),
    ("Frame examples", "Build (user, cutoff) rows; label = did the user do each activity in the next 7 days; only rows with row-time < cutoff are visible."),
    ("Represent", "Temporal features (multi-window counts, recency, momentum) + relational features (FK joins, repo neighbourhood) + a time-aware user–repo GNN."),
    ("Model", "One LightGBM per activity (6 models); a heterogeneous GNN; each activity's threshold tuned to maximise F1 on the validation week."),
    ("Validate & predict", "Time-based split (train on earlier weeks, validate on a held-out week); retrain and predict the test week → output_413551034.csv."),
    ("Reproduce", "Pinned requirements, fixed seeds, documented data window; the TAs re-run preprocess.py and reproduce the output."),
]
y = 1.75
for i, (head, body) in enumerate(steps, 1):
    tf = tb(s_pl, 0.7, y, 11.9, 0.8)
    para(tf, [(f"{i}.  ", {"bold": True, "color": BLUE, "size": 15}), (head + ".  ", {"bold": True, "color": NAVY, "size": 14}),
              (body, {"size": 13})], first=True, space_after=0)
    y += 0.82
footer(s_pl, 14)
notes(s_pl, "〔約 1:30|累計 17:00〕流程六步。\n"
      "① 前處理:下載 GH Archive,跑官方 preprocess.py,得 8 張匿名化表。\n"
      "② 建立樣本:組『使用者+時間切點』,標籤=未來 7 天有沒有做各活動;只有 row-time < 切點 看得到。\n"
      "③ 特徵:時間 + 關聯 + 時間感知圖。④ 建模:每活動一個 LightGBM(6 個)+ 異質 GNN;門檻在驗證週調到 F1 最大。\n"
      "⑤ 驗證與預測:依時間切分,早週訓練、留一週驗證;重訓並預測測試週,輸出 csv。⑥ 可重現:鎖版本、固定種子、記錄區間。")

# ================================================================ content: training setup (page 15)
s_tr = new_slide()
badge(s_tr, "Q4 · Training", GREEN)
title(s_tr, "Training Setup: Time-Based Split", "3 earlier weeks train · 1 later week validates · 6 LightGBMs")
labels = [("Train", "Oct 13", BLUE), ("Train", "Oct 20", BLUE), ("Train", "Oct 27", BLUE), ("Validate", "Nov 3–10", GREEN)]
x = 0.6
for i, (tag, dt, col) in enumerate(labels):
    wc = 2.65 if i < 3 else 3.6
    card(s_tr, x, 1.75, wc, 0.9)
    tf = tb(s_tr, x, 1.83, wc, 0.75, anchor=MSO_ANCHOR.MIDDLE)
    para(tf, tag, size=12.5, color=col, bold=True, first=True, align=PP_ALIGN.CENTER, space_after=1)
    para(tf, dt, size=11.5, color=GREY, align=PP_ALIGN.CENTER, space_after=0)
    x += wc + 0.25
    if i < 3:
        tf = tb(s_tr, x - 0.27, 1.83, 0.3, 0.75, anchor=MSO_ANCHOR.MIDDLE)
        para(tf, "→", size=15, color=GREY, first=True, align=PP_ALIGN.CENTER, space_after=0)
cards = [
    (BLUE, "Split by time, not at random",
     ["Earlier weeks train; a later held-out week validates.",
      "Mirrors predicting the future and prevents leakage.",
      "Random splits would leak the future and inflate scores."]),
    (GREEN, "Six LightGBMs",
     ["One gradient-boosted model per activity (independent).",
      "400 trees, lr 0.03, subsample 0.8, L2 regularization.",
      "random_state=42, deterministic → TAs reproduce exactly."]),
    (GOLD, "Per-activity thresholds",
     ["Probability → 0/1 cut-off chosen per activity.",
      "Picked to maximise F1 on the validation week.",
      "Positive rates differ a lot (push ≫ pr_review_comment)."]),
]
x = 0.6
for col, head, lines in cards:
    card(s_tr, x, 3.0, 3.95, 3.3)
    bar(s_tr, x, 3.0, 3.95, col)
    tf = tb(s_tr, x + 0.28, 3.28, 3.4, 2.9)
    para(tf, head, size=14, color=NAVY, bold=True, first=True, space_after=6)
    for ln in lines:
        para(tf, ln, size=12.5, color=INK, space_after=6, bullet=True)
    x += 4.15
footer(s_tr, 15)
notes(s_tr, "〔約 1:45|累計 18:45〕訓練設定講清楚。\n"
      "上排是週切點:10/13、20、27 三個早週訓練,留 11/03–10 驗證。\n"
      "① 依時間切、不隨機切:模擬用過去預測未來,避免洩漏;隨機切會把未來混進訓練,分數假性變高。\n"
      "② 六個 LightGBM:每活動各一個梯度提升樹,獨立;400 棵樹、lr 0.03、subsample 0.8、L2;種子固定 42、deterministic,助教可完全重現。\n"
      "③ 各活動門檻:機率要用門檻轉 0/1;每活動在驗證週挑 F1 最大的門檻,因為正例比例差很多(push 遠多於 pr_review_comment)。")

# ================================================================ content: results & takeaways (page 16)
s_res = new_slide(NAVY)
badge(s_res, "Results", BLUE)
tf = tb(s_res, 0.6, 0.55, 12.1, 0.8)
para(tf, "Results, Reproducibility & Takeaways", size=28, color=WHITE, bold=True, first=True, font=HEAD, space_after=0)
picture(s_res, ART / "chart_methods.png", 0.5, 1.75, w=7.0)
tf = tb(s_res, 7.9, 1.6, 4.9, 4.9)
para(tf, "Takeaways", size=15, color=RGBColor(0xC2, 0xD2, 0xE8), bold=True, first=True, space_after=7)
for t in ["GBDT on temporal + relational features is the best model (Score 33.1) and the submission.",
          "Temporal features are the dominant signal; removing them costs the most (−4.1).",
          "Relational features and GNN message passing add little on this sparse cohort — time dominates.",
          "Strict time-based validation and leakage control throughout.",
          "Fully reproducible: pinned deps, fixed seeds, documented window; TAs re-run preprocess.py."]:
    para(tf, t, size=12.5, color=WHITE, space_after=7, bullet=True)
tf = tb(s_res, 0.6, 6.55, 12.1, 0.5)
para(tf, "output_413551034.csv — 4,465 users, passes the official evaluate.py format check.", size=11.5,
     color=RGBColor(0x9D, 0xB4, 0xD0), first=True, space_after=0)
footer(s_res, 16)
notes(s_res, "〔約 1:30|累計 20:15〕總結。左邊長條圖是各模型在驗證週的比較。重點:\n"
      "① 用時間+關聯特徵的 GBDT 最好,Score 33.1,也是我提交的版本。\n"
      "② 時間特徵最主要,拿掉它掉最多(−4.1)。③ 稀疏群體上關聯與 GNN 幫助很小,時間主導。\n"
      "④ 全程嚴格時間切分與防洩漏。⑤ 完全可重現:鎖版本、固定種子、記錄區間,助教重跑 preprocess.py 即可重現。\n"
      "output_413551034.csv 有 4,465 位使用者,通過官方格式檢查。以上是我的報告,謝謝。")

# ================================================================ sync speaker notes from the script .md
# Single source of truth: speaker_script_zh.md. Each "## 投影片 N — ..." section becomes
# the notes of the slide at final position N, so Presenter View always matches the script.
import re as _re
_order_slides = [TPL_TITLE, s_task, TPL_Q1, s_sch, s_er, TPL_Q2, s_q2a, s_q2f,
                 TPL_Q3, s_q3a, s_q3f, TPL_Q4, s_fw, s_pl, s_tr, s_res]
_md = (Path(__file__).resolve().parent / "speaker_script_zh.md")
if _md.exists():
    _parts = _re.split(r"\n## 投影片 ", _md.read_text(encoding="utf-8"))
    _scripts = []
    for _p in _parts[1:]:
        _body = _p.split("\n", 1)[1] if "\n" in _p else ""
        _body = _body.split("\n---")[0].strip().replace("**", "")
        _scripts.append(_body)
    for _sl, _sc in zip(_order_slides, _scripts):
        if _sc:
            notes(_sl, _sc)

# ================================================================ reorder slides into the final sequence
# current order after appends:
#   0 title(TPL) 1 Q1(TPL) 2 Q2(TPL) 3 Q3(TPL) 4 Q4(TPL)
#   5 task 6 schema 7 ER 8 q2a 9 q2f 10 q3a 11 q3f 12 fw 13 pl 14 tr 15 res
desired = [0, 5, 1, 6, 7, 2, 8, 9, 3, 10, 11, 4, 12, 13, 14, 15]
sldIdLst = prs.slides._sldIdLst
ids = list(sldIdLst)
for i in desired:
    sldIdLst.append(ids[i])     # re-appending moves it to the end → final order

prs.save(str(OUT))
print("saved", OUT, "slides:", len(prs.slides._sldIdLst))
