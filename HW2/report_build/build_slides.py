"""Build Asg2_413551034.pptx (report slides for Assignment 2) with python-pptx.

Run from HW2/report_build/ with the venv python. Figures are read from ../artifacts/.
"""
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from PIL import Image

ART = Path(__file__).resolve().parent.parent / "artifacts"
OUT = Path(__file__).resolve().parent / "Asg2_413551034.pptx"
SID = "413551034"
TOTAL = 13

NAVY = RGBColor(0x1F, 0x3B, 0x63)
INK = RGBColor(0x22, 0x30, 0x3F)
BLUE = RGBColor(0x2D, 0x6C, 0xB5)
GREEN = RGBColor(0x2E, 0x8B, 0x57)
GOLD = RGBColor(0xC8, 0x91, 0x2A)
RED = RGBColor(0xB0, 0x38, 0x2F)
GREY = RGBColor(0x6B, 0x7A, 0x8A)
LIGHT = RGBColor(0xF1, 0xF4, 0xF7)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
HEAD = "Calibri"
BODY = "Calibri"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
SW, SH = prs.slide_width, prs.slide_height


def slide(bg=WHITE):
    s = prs.slides.add_slide(BLANK)
    r = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SW, SH)
    r.fill.solid(); r.fill.fore_color.rgb = bg; r.line.fill.background()
    r.shadow.inherit = False
    s.shapes._spTree.remove(r._element); s.shapes._spTree.insert(2, r._element)
    return s


def tb(s, x, y, w, h, anchor=MSO_ANCHOR.TOP):
    box = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = 0; tf.margin_right = 0; tf.margin_top = 0; tf.margin_bottom = 0
    return tf


def para(tf, runs, size=16, color=INK, bold=False, align=PP_ALIGN.LEFT, space_after=6,
         bullet=False, first=False, font=BODY, line=None):
    p = tf.paragraphs[0] if first and not tf.paragraphs[0].runs else tf.add_paragraph()
    p.alignment = align
    if space_after is not None:
        p.space_after = Pt(space_after)
    if line:
        p.line_spacing = line
    if isinstance(runs, str):
        runs = [(runs, {})]
    for text, opt in runs:
        r = p.add_run(); r.text = text
        f = r.font
        f.size = Pt(opt.get("size", size)); f.name = opt.get("font", font)
        f.bold = opt.get("bold", bold); f.italic = opt.get("italic", False)
        f.color.rgb = opt.get("color", color)
    if bullet:
        _bullet(p)
    return p


def _bullet(p):
    from pptx.oxml.ns import qn
    pPr = p._pPr if p._pPr is not None else p.get_or_add_pPr()
    pPr.set("indent", "-228600"); pPr.set("marL", "228600")
    bu = pPr.makeelement(qn("a:buChar"), {"char": "•"})
    buf = pPr.makeelement(qn("a:buFont"), {"typeface": "Arial"})
    pPr.append(buf); pPr.append(bu)


def title(s, text, sub=None, color=NAVY):
    tf = tb(s, 0.6, 0.92, 12.1, 1.0)
    para(tf, text, size=30, color=color, bold=True, first=True, font=HEAD, space_after=2)
    if sub:
        para(tf, sub, size=15, color=GREY, space_after=0)


def badge(s, text, color, x=0.6, y=0.3):
    b = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(1.9), Inches(0.42))
    b.fill.solid(); b.fill.fore_color.rgb = color; b.line.fill.background(); b.shadow.inherit = False
    tf = b.text_frame; tf.margin_top = 0; tf.margin_bottom = 0
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = text; r.font.size = Pt(13); r.font.bold = True
    r.font.color.rgb = WHITE; r.font.name = HEAD


def footer(s, n):
    tf = tb(s, 0.6, 7.06, 12.1, 0.3)
    para(tf, [(f"Asg2 · {SID}", {"color": GREY, "size": 10}),
              (f"     ·     {n} / {TOTAL}", {"color": GREY, "size": 10})], first=True, space_after=0)


def picture(s, path, x, y, w=None, h=None):
    im = Image.open(path); ar = im.size[0] / im.size[1]
    if w and not h:
        h = w / ar
    elif h and not w:
        w = h * ar
    s.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(w), Inches(h))
    return w, h


def card(s, x, y, w, h, fill=LIGHT):
    c = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    c.fill.solid(); c.fill.fore_color.rgb = fill; c.line.color.rgb = RGBColor(0xDD, 0xE3, 0xEA)
    c.line.width = Pt(0.75); c.shadow.inherit = False
    return c


def numbered(s, items, y0=1.95, dy=1.5, bh=1.5):
    """A vertical list of numbered items: [(num, color, head, body), ...]."""
    y = y0
    for num, col, head, body in items:
        c = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.7), Inches(y), Inches(0.62), Inches(0.62))
        c.fill.solid(); c.fill.fore_color.rgb = col; c.line.fill.background(); c.shadow.inherit = False
        ptf = c.text_frame; ptf.margin_top = 0; ptf.margin_bottom = 0
        pp = ptf.paragraphs[0]; pp.alignment = PP_ALIGN.CENTER
        rr = pp.add_run(); rr.text = num; rr.font.size = Pt(20); rr.font.bold = True; rr.font.color.rgb = WHITE
        tf = tb(s, 1.6, y - 0.05, 11.0, bh)
        para(tf, head, size=18, color=NAVY, bold=True, first=True, space_after=3)
        para(tf, body, size=14.5, color=INK, space_after=0)
        y += dy


def notes(s, text):
    s.notes_slide.notes_text_frame.text = text


# ---------------------------------------------------------------- Slide 1: title
s = slide(NAVY)
tf = tb(s, 0.9, 2.2, 11.5, 2.4)
para(tf, "Predicting GitHub User Activity", size=46, color=WHITE, bold=True, first=True, font=HEAD, space_after=6)
para(tf, "Relational + temporal modeling over 8 foreign-key-linked tables", size=19, color=RGBColor(0xC2, 0xD2, 0xE8), space_after=0)
tf = tb(s, 0.9, 5.1, 11.5, 1.6)
para(tf, "Assignment 2  ·  Big Data Analytics Techniques and Applications, Fall 2026", size=15, color=RGBColor(0x9D, 0xB4, 0xD0), first=True, space_after=10)
para(tf, [("Student ID  ", {"color": RGBColor(0x9D,0xB4,0xD0), "size": 15}), (SID, {"color": WHITE, "size": 15, "bold": True}),
          ("      Code  ", {"color": RGBColor(0x9D,0xB4,0xD0), "size": 15}), ("github.com/CH-Joshua-Hsiao/NYCU-BigDataAnalytics/tree/main/HW2", {"color": WHITE, "size": 15})], space_after=0)
notes(s, "〔約 1:00〕大家好,我是學號 413551034。這次作業二的題目是預測 GitHub 使用者的活動。\n"
         "我們要對測試集裡的 4,465 位使用者,預測他們在 2026/11/22–11/29 這一週(台灣時間)會不會做出六種 GitHub 活動。\n"
         "資料來源是 GH Archive 的每小時事件,經過官方 preprocess.py 轉成 8 張用外鍵互相連結的關聯式資料表。\n"
         "程式都放在這個公開的 GitHub repo(github.com/CH-Joshua-Hsiao/NYCU-BigDataAnalytics)。接下來先說明題目、資料跟評分方式。")

# ---------------------------------------------------------------- Slide 2: task & data
s = slide()
badge(s, "Overview", BLUE)
title(s, "The Task, the Data, the Metric", "Predict 6 activities per user for 2026/11/22–11/29 (Taiwan time)")
tf = tb(s, 0.6, 1.85, 6.8, 4.8)
para(tf, [("Goal.  ", {"bold": True, "color": NAVY}), ("For each of the 4,465 test users, output a 0/1 for "
          "each of six activities during the test week.", {})], first=True, size=16, space_after=10)
para(tf, [("Data.  ", {"bold": True, "color": NAVY}), ("Hourly GH Archive events, turned into 8 anonymized, "
          "foreign-key-linked tables by the official preprocess.py (ids hashed, text masked).", {})], size=16, space_after=10)
para(tf, [("Rules.  ", {"bold": True, "color": NAVY}), ("Use only those 8 tables; split train/validation by "
          "time; for a prediction at time t use only rows visible before t.", {})], size=16, space_after=10)
para(tf, [("Metric.  ", {"bold": True, "color": NAVY}), ("Score = (macro-F1 + micro-F1) / 2 over the 6 activities.", {})], size=16, space_after=0)
# right card: the six activities
card(s, 7.8, 1.85, 4.9, 4.55)
tf = tb(s, 8.1, 2.1, 4.3, 4.1)
para(tf, "The 6 target activities", size=15, color=NAVY, bold=True, first=True, space_after=8)
for a, d in [("open_pr", "open a pull request"), ("open_issue", "open an issue (not a PR)"),
             ("issue_comment", "comment in an issue / PR thread"), ("pr_review", "submit a PR review"),
             ("pr_review_comment", "comment on PR code lines"), ("push", "push commits to a branch/tag")]:
    para(tf, [(a, {"bold": True, "color": BLUE, "font": "Consolas", "size": 13}), (f"  —  {d}", {"size": 13})], space_after=7)
footer(s, 2)
notes(s, "〔約 1:45|累計 2:45〕先看題目:對每一位測試使用者,輸出六個 0/1,代表這六種活動——開 PR、開 issue、"
         "在 issue/PR 留言、送出 PR review、在程式碼行上留 review comment、push commit。右邊卡片就是六個目標。\n"
         "資料:GH Archive 每小時事件,官方腳本轉成 8 張匿名化、用外鍵連結的表,ID 雜湊、文字遮蔽。\n"
         "規則三重點:只能用這 8 張表;依時間切分訓練/驗證;在時間點 t 預測時只能用 t 之前看得到的資料列。\n"
         "評分 Score = (macro-F1 + micro-F1) / 2——macro 讓少見活動也有份量,micro 反映整體量,兩個都要顧。\n"
         "核心難點就是題目要回答的兩件事:跨表關聯(Q2)與時間(Q3)。")

# ---------------------------------------------------------------- Slide 3: Q1 schema
s = slide()
badge(s, "Q1 · 1%", GREEN)
title(s, "Schema Graph & Dataset Time Period")
w, h = picture(s, ART / "schema_graph.png", 6.55, 1.85, h=5.15)
tf = tb(s, 0.6, 1.95, 4.7, 4.9)
para(tf, "Schema", size=15, color=NAVY, bold=True, first=True, space_after=4)
para(tf, "8 tables; every primary key (PK) is a row number and every foreign key (FK) points to one. "
        "Arrows go FK → referenced PK.", size=13.5, space_after=10)
para(tf, "Row-time", size=15, color=NAVY, bold=True, space_after=4)
para(tf, "Each table has a time it becomes visible (first_seen_at, or created_at for comments/pushes). "
        "Features at time t use only rows with row-time < t.", size=13.5, space_after=10)
para(tf, "Dataset time period", size=15, color=NAVY, bold=True, space_after=4)
para(tf, [("Raw GH Archive: ", {"bold": True}), ("2026-10-04 → 11-16 (UTC)", {})], size=13.5, space_after=3)
para(tf, [("Training weeks: ", {"bold": True}), ("Oct 13 / 20 / 27 cutoffs", {})], size=13.5, space_after=3)
para(tf, [("Validation: ", {"bold": True}), ("Nov 3 → Nov 10", {})], size=13.5, space_after=3)
para(tf, [("Prediction: ", {"bold": True}), ("Nov 22 → Nov 29 (Taiwan)", {})], size=13.5, space_after=0)
footer(s, 3)
notes(s, "〔約 2:00|累計 4:45〕這頁回答 Q1,畫出 8 張表的 schema 關聯圖。\n"
         "每張表是一個方塊列出欄位;金色 PK 是主鍵,綠色 FK 是外鍵,每個外鍵用箭頭指向它參照的主鍵。\n"
         "Users 跟 Repositories 是兩個樞紐,幾乎所有事件表都指向它們;PullRequests、Issues 又被 reviews/comments 參照。\n"
         "左邊標了每張表的可見時間 row-time(多為 first_seen_at,留言/push 用 created_at);算 t 時刻特徵時只用 row-time < t 的列,避免偷看未來。\n"
         "資料時間區間:原始抓 10/04–11/16;訓練切點 10/13、10/20、10/27;驗證週 11/03–11/10;預測週 11/22–11/29。\n"
         "補充:最終版本我會在截止前把資料重新下載到 11/21 再重跑一次,讓特徵對齊真正的測試週。")

# ---------------------------------------------------------------- Slide 4: reading the tables (NEW)
s = slide()
badge(s, "Schema", GREEN)
title(s, "How to Read the 8 Tables", "Two hubs + six event tables — every event is a user acting in a repo")
tf = tb(s, 0.6, 1.9, 7.0, 5.0)
para(tf, [("Two hub entities.  ", {"bold": True, "color": NAVY}),
          ("Users (user_id) and Repositories (repo_id). Almost every other table points to them via "
           "author_id / user_id and repo_id.", {})], first=True, size=15.5, space_after=10)
para(tf, [("Six event tables.  ", {"bold": True, "color": NAVY}),
          ("PullRequests, Issues, IssueComments, PRReviews, PRReviewComments, Pushes. One row = one "
           "action: a user, a repo, and a time.", {})], size=15.5, space_after=10)
para(tf, [("Foreign-key chains.  ", {"bold": True, "color": NAVY}),
          ("A review points to its PR; a review comment points to its PR and review; an issue comment "
           "points to its issue. Comments and reviews inherit repo_id too.", {})], size=15.5, space_after=10)
para(tf, [("Why it matters.  ", {"bold": True, "color": NAVY}),
          ("Follow repo_id to reach co-workers in the same repo; follow author_id to reach a user's "
           "history elsewhere. That is exactly what the relational features (Q2) exploit.", {})], size=15.5, space_after=0)
# right card: activity -> source table mapping
card(s, 7.9, 1.9, 4.8, 4.8)
tf = tb(s, 8.2, 2.15, 4.2, 4.3)
para(tf, "Each activity → its source table", size=14.5, color=NAVY, bold=True, first=True, space_after=8)
for a, d in [("open_pr", "PullRequests · author_id"),
             ("open_issue", "Issues · author_id"),
             ("issue_comment", "IssueComments · author_id"),
             ("pr_review", "PRReviews · reviewer_id"),
             ("pr_review_comment", "PRReviewComments · author_id"),
             ("push", "Pushes · user_id")]:
    para(tf, [(a, {"bold": True, "color": GREEN, "font": "Consolas", "size": 12.5})], space_after=1)
    para(tf, d, size=12, color=GREY, space_after=8)
footer(s, 4)
notes(s, "〔約 1:30|累計 6:15〕這頁幫大家「讀懂」這 8 張表怎麼關聯,也是 Q2 的基礎。\n"
         "兩個樞紐:Users 和 Repositories——幾乎每張表都用 author_id/user_id 指向使用者、用 repo_id 指向倉庫。\n"
         "六張事件表:PR、Issue、IssueComments、PRReviews、PRReviewComments、Pushes;每一列就是一次行為——某個人、某個 repo、某個時間。\n"
         "外鍵鏈:review 指向它的 PR;review comment 指向 PR 和 review;issue comment 指向 issue;留言跟 review 也都帶 repo_id。\n"
         "為什麼重要:沿著 repo_id 可以找到同一個 repo 裡的協作者,沿著 author_id 可以找到一個人在別處的歷史——這正是 Q2 關聯特徵在用的東西。\n"
         "右邊這張表列出六個要預測的活動各自來自哪張表、哪個欄位代表「做這件事的人」。")

# ---------------------------------------------------------------- Slide 5: Q2 approach
s = slide()
badge(s, "Q2 · 3%", GOLD)
title(s, "Modeling Relationships Across Tables")
numbered(s, [
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
footer(s, 5)
notes(s, "〔約 1:45|累計 8:00〕Q2 問怎麼利用跨表關聯,我用了三個做法。\n"
         "① 外鍵 join 特徵:把 User–PR–Review–Issue–Comment 串起來,算出你的工作收到多少 review/留言、有多少不同的人 review 你或跟你合作、你給別人送了多少 review、以及參與的 repo/組織廣度。\n"
         "② repo 鄰域聚合:對使用者碰過的 repo,把這些 repo 最近的活動量與其他活躍使用者人數聚合起來,代表社群的動能。\n"
         "③ 時間感知的異質 GNN(RelBench/關聯式深度學習):使用者–repo 的圖,6 種外鍵衍生的邊,訊息從使用者傳到 repo、再回到兩跳外的協作者。\n"
         "前兩個是給樹模型的特徵,第三個是圖神經網路。下一頁看它們到底有沒有幫助。")

# ---------------------------------------------------------------- Slide 6: Q2 results
s = slide()
badge(s, "Q2 · Findings", GOLD)
title(s, "What the Relationships Contribute", "Honest result: on this sparse cohort, structure adds little")
stats = [("≈ 0", BLUE, "GBDT without relational features", "33.1 → 33.6 Score (neutral)"),
         ("−9.4", RED, "Adding GNN message passing", "node-MLP 30.3 → graph 20.9"),
         ("win", GREEN, "Best model stays", "GBDT on temporal+relational features")]
x = 0.6
for big, col, head, sub in stats:
    card(s, x, 2.0, 3.9, 2.3)
    tf = tb(s, x + 0.3, 2.2, 3.3, 1.9)
    para(tf, big, size=40, color=col, bold=True, first=True, space_after=2, font=HEAD)
    para(tf, head, size=14, color=NAVY, bold=True, space_after=3)
    para(tf, sub, size=12.5, color=GREY, space_after=0)
    x += 4.15
tf = tb(s, 0.6, 4.7, 12.1, 2.1)
para(tf, "Why?", size=16, color=NAVY, bold=True, first=True, space_after=4)
para(tf, "Next-week activity is driven mostly by a user's own recent history (strong temporal "
        "autocorrelation). The user–repo graph is sparse, so mean-aggregation over-smooths and the GNN "
        "loses the per-user signal. Relational deep learning helps when cross-entity interaction is dense; "
        "here, time dominates — a useful finding about when RDL pays off.", size=15, space_after=0)
footer(s, 6)
notes(s, "〔約 1:45|累計 9:45〕誠實報告:在這個稀疏群體上,關聯結構幫助很小。\n"
         "① GBDT 拿掉關聯特徵,Score 33.1→33.6,幾乎沒差。② 加上 GNN 訊息傳遞反而掉九分多,節點特徵 30.3→圖 20.9。③ 所以最好的模型還是 GBDT(時間+關聯特徵)。\n"
         "為什麼?下一週的活動主要由使用者自己最近的行為決定(很強的時間自相關);使用者–repo 的圖又很稀疏,平均式聚合把訊號抹平,GNN 反而失去個別訊號。\n"
         "RDL 通常在跨實體互動很密集時才發威;這題是時間主導。這本身就是有價值的發現。我也用每活動 AUC 驗證:一加訊息傳遞,AUC 大約掉到 0.5。")

# ---------------------------------------------------------------- Slide 7: Q3 approach
s = slide()
badge(s, "Q3 · 5%", BLUE)
title(s, "Modeling Temporal Information")
numbered(s, [
    ("1", BLUE, "Multi-scale temporal features",
     "Per-activity counts over 1 / 7 / 14 / 30 / 90-day windows, days-since-last (recency), distinct "
     "active days, and 7-day momentum / ratio — including the strong copy-last-week signal."),
    ("2", GREEN, "Strict leakage control",
     "Only rows with row-time < t are visible; never filter by created_at / submitted_at (rows arrive "
     "late); never use known-only-later columns (merged_at, closed_at, state_reason, dismissed_at)."),
    ("3", GOLD, "Time-encoded GNN edges",
     "Each edge carries its age; a neighbour's message is weighted exp(−age / τ), so recent "
     "interactions count more than old ones."),
], bh=1.45)
# mini timeline
ty = 6.55
ln = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.6), Inches(ty), Inches(9.5), Inches(0.02))
ln.fill.solid(); ln.fill.fore_color.rgb = GREY; ln.line.fill.background(); ln.shadow.inherit = False
mk = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(7.1), Inches(ty - 0.18), Inches(0.03), Inches(0.36))
mk.fill.solid(); mk.fill.fore_color.rgb = RED; mk.line.fill.background(); mk.shadow.inherit = False
tf = tb(s, 1.6, ty + 0.06, 5.4, 0.3); para(tf, "features: all history with row-time < t", size=11, color=GREY, first=True, space_after=0)
tf = tb(s, 7.15, ty + 0.06, 4.0, 0.3); para(tf, "labels: next 7 days", size=11, color=RED, first=True, space_after=0)
tf = tb(s, 6.85, ty - 0.46, 1.2, 0.3); para(tf, "t", size=12, color=RED, bold=True, first=True, space_after=0)
footer(s, 7)
notes(s, "〔約 2:00|累計 11:45〕Q3 時間建模,是這套方法的核心,一樣三個重點。\n"
         "① 多尺度時間特徵:對每種活動分別算 1/7/14/30/90 天窗口的次數、距上次多久(recency)、幾天活躍、7 天動能/比率;其中包含很強的「參考上一週」訊號。\n"
         "② 嚴格防洩漏:只有 row-time < t 的列看得到;不用 created_at/submitted_at 判斷可見性(那些列晚點才進來);不用事後才知道的欄位(merged_at、closed_at、state_reason、dismissed_at)。\n"
         "③ 把時間編碼進 GNN 的邊:每條邊帶年齡,鄰居訊息以 exp(−age/τ) 加權,最近的互動比舊的更重要。\n"
         "下方時間軸:t 之前的所有歷史當特徵,接下來 7 天當標籤。")

# ---------------------------------------------------------------- Slide 8: Q3 results
s = slide()
badge(s, "Q3 · Findings", BLUE)
title(s, "Temporal Signal Dominates", "Removing temporal features costs the most")
picture(s, ART / "chart_ablation.png", 0.5, 1.95, w=6.0)
picture(s, ART / "chart_per_activity.png", 6.75, 2.15, w=6.3)
tf = tb(s, 0.6, 6.25, 12.1, 1.0)
para(tf, [("Removing temporal features: 33.1 → 29.0 Score (−4.1) — the largest drop of any group. "
          "Copy-last-week alone scores 29.3. ", {"bold": True, "color": NAVY}),
          ("Per activity, regular behaviours (open_issue, pr_review) are easier than bursty ones "
           "(push, pr_review_comment).", {})], first=True, size=14, space_after=0)
footer(s, 8)
notes(s, "〔約 1:30|累計 13:15〕用兩張圖說明時間建模的效果。\n"
         "左圖是特徵群消融:把時間特徵拿掉,Score 33.1→29.0,掉 4.1 分,是所有特徵群裡掉最多的;對照一下,光是「照抄上一週」就有 29.3 分,可見時間資訊的份量。\n"
         "右圖是 GBDT 各活動的 F1:規律型行為(open_issue、pr_review)好預測;爆發型行為(push、程式碼行 review comment)比較難,因為零星不規律。\n"
         "所以這頁直接回答『時間建模帶來什麼幫助』——它是這任務最主要的訊號來源。")

# ---------------------------------------------------------------- Slide 9: Q4 framework
s = slide()
badge(s, "Q4 · 5%", GREEN)
title(s, "Framework")
w8, h8 = picture(s, ART / "framework.png", 0, 1.95, h=4.95)
# center horizontally
s.shapes[-1].left = Inches((13.333 - w8) / 2)
footer(s, 9)
notes(s, "〔約 1:15|累計 14:30〕Q4 要說明整體架構,這張是一頁總覽。\n"
         "從左到右:GH Archive 每小時事件 → preprocess.py → 8 張關聯式資料表 → 三條平行分支(時間特徵、關聯特徵、時間感知 GNN)都餵進模型。\n"
         "注意中間的 leakage gate,它卡在資料表這一層,所以每條分支看到的都只有過去的資料。最後經模型與門檻調整,產出提交檔。下一頁把每一步拆開講。")

# ---------------------------------------------------------------- Slide 10: Q4 pipeline detail
s = slide()
badge(s, "Q4 · Pipeline", GREEN)
title(s, "The Full Pipeline, Step by Step")
steps = [
    ("Preprocess", "Download GH Archive hours → official preprocess.py → 8 anonymized tables (one Parquet each)."),
    ("Frame examples", "Build (user, cutoff) rows; label = did the user do each activity in the next 7 days; only rows with row-time < cutoff are visible."),
    ("Represent", "Temporal features (multi-window counts, recency, momentum) + relational features (FK joins, repo neighbourhood) + a time-aware user–repo GNN."),
    ("Model", "One LightGBM per activity (6 models); a heterogeneous GNN; each activity's threshold tuned to maximise F1 on the validation week."),
    ("Validate & predict", "Time-based split (train on earlier weeks, validate on a held-out week); retrain and predict the test week → output_413551034.csv."),
    ("Reproduce", "Pinned requirements, fixed seeds, documented data window; the TAs re-run preprocess.py and reproduce the output."),
]
y = 1.95
for i, (head, body) in enumerate(steps, 1):
    tf = tb(s, 0.7, y, 11.9, 0.8)
    para(tf, [(f"{i}.  ", {"bold": True, "color": BLUE, "size": 16}), (head + ".  ", {"bold": True, "color": NAVY, "size": 15}),
              (body, {"size": 14})], first=True, space_after=0)
    y += 0.8
footer(s, 10)
notes(s, "〔約 1:30|累計 16:00〕把流程拆成六步。\n"
         "① 前處理:下載 GH Archive 每小時檔,跑官方 preprocess.py,得到 8 張匿名化表(各一個 Parquet)。\n"
         "② 建立樣本:組「使用者+時間切點」的列,標籤=這人未來 7 天有沒有做各活動;只有 row-time < 切點 的列看得到。\n"
         "③ 特徵表示:時間特徵 + 關聯特徵 + 時間感知的使用者–repo 圖。\n"
         "④ 建模:每活動一個 LightGBM(共 6 個)+ 異質 GNN;每活動門檻在驗證週調到 F1 最大。\n"
         "⑤ 驗證與預測:依時間切分,早週訓練、留一週驗證;最後重訓並預測測試週,輸出 output_413551034.csv。\n"
         "⑥ 可重現:套件鎖版本、種子固定、資料區間記錄清楚,助教重跑 preprocess.py 即可重現輸出。")

# ---------------------------------------------------------------- Slide 11: training setup (NEW)
s = slide()
badge(s, "Q4 · Training", GREEN)
title(s, "Training Setup: Time-Based Split", "3 earlier weeks train · 1 later week validates · 6 LightGBMs")
# top: weekly-cutoff strip
labels = [("Train", "Oct 13", BLUE), ("Train", "Oct 20", BLUE), ("Train", "Oct 27", BLUE), ("Validate", "Nov 3–10", GREEN)]
x = 0.6
for i, (tag, dt, col) in enumerate(labels):
    wcard = 2.65 if i < 3 else 3.6
    card(s, x, 1.95, wcard, 0.95)
    tf = tb(s, x, 2.05, wcard, 0.8, anchor=MSO_ANCHOR.MIDDLE)
    para(tf, tag, size=13, color=col, bold=True, first=True, align=PP_ALIGN.CENTER, space_after=1)
    para(tf, dt, size=12, color=GREY, align=PP_ALIGN.CENTER, space_after=0)
    x += wcard + 0.25
    if i < 3:
        tf = tb(s, x - 0.27, 2.05, 0.3, 0.8, anchor=MSO_ANCHOR.MIDDLE)
        para(tf, "→", size=16, color=GREY, first=True, align=PP_ALIGN.CENTER, space_after=0)
# three explanation cards
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
    card(s, x, 3.3, 3.95, 3.3)
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(3.3), Inches(3.95), Inches(0.12))
    bar.fill.solid(); bar.fill.fore_color.rgb = col; bar.line.fill.background(); bar.shadow.inherit = False
    tf = tb(s, x + 0.28, 3.6, 3.4, 2.9)
    para(tf, head, size=15, color=NAVY, bold=True, first=True, space_after=7)
    for ln in lines:
        para(tf, ln, size=13, color=INK, space_after=7, bullet=True)
    x += 4.15
footer(s, 11)
notes(s, "〔約 1:45|累計 17:45〕這頁把『到底怎麼訓練』講清楚。\n"
         "上面這條是週切點:用 10/13、10/20、10/27 三個較早的週當訓練,留較晚的 11/03–11/10 當驗證。\n"
         "① 依時間切、不隨機切:早的週訓練、晚的一週驗證,模擬用過去預測未來,也避免洩漏;隨機切會把未來混進訓練,分數會假性變高。\n"
         "② 六個 LightGBM:每個活動各一個梯度提升樹模型,彼此獨立;400 棵樹、學習率 0.03、subsample 0.8、L2 正則;固定種子 42、deterministic,確保助教能完全重現。\n"
         "③ 各活動門檻:模型輸出是機率,要用門檻轉成 0/1;每個活動各自在驗證週挑讓 F1 最大的門檻,因為各活動的正例比例差很多(push 遠多於 pr_review_comment)。")

# ---------------------------------------------------------------- Slide 12: reproducibility & limitations (NEW)
s = slide()
badge(s, "Wrap-up", BLUE)
title(s, "Reproducibility & Limitations")
# left card: reproducibility
card(s, 0.6, 1.95, 5.95, 4.6)
bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(1.95), Inches(5.95), Inches(0.12))
bar.fill.solid(); bar.fill.fore_color.rgb = GREEN; bar.line.fill.background(); bar.shadow.inherit = False
tf = tb(s, 0.95, 2.3, 5.3, 4.1)
para(tf, "Reproducible by design", size=16, color=GREEN, bold=True, first=True, space_after=9)
for t in ["Pinned requirements and fixed random seeds.",
          "Documented data window (events in UTC, test week in Taiwan time).",
          "Row-time leakage gate at the data layer — every branch sees only the past.",
          "TAs re-run preprocess.py and reproduce output_413551034.csv.",
          "Passes the official evaluate.py format check (4,465 users).",
          "Final run re-downloads data through 11-21 before the deadline."]:
    para(tf, t, size=13, color=INK, space_after=8, bullet=True)
# right card: limitations
card(s, 6.75, 1.95, 5.95, 4.6)
bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(6.75), Inches(1.95), Inches(5.95), Inches(0.12))
bar.fill.solid(); bar.fill.fore_color.rgb = GOLD; bar.line.fill.background(); bar.shadow.inherit = False
tf = tb(s, 7.1, 2.3, 5.3, 4.1)
para(tf, "Limitations & when RDL would help", size=16, color=GOLD, bold=True, first=True, space_after=9)
for t in ["The GH Archive mirror is downsampled, so the cohort is sparse.",
          "Mean-aggregation GNN over-smooths; graph signal is weak here.",
          "RDL pays off with dense cross-entity interaction and richer edges.",
          "Future: per-activity tuning; longer (90-day) history features.",
          "Future: calibrated rolling thresholds; a proper RelBench temporal-sampling GNN."]:
    para(tf, t, size=13, color=INK, space_after=8, bullet=True)
footer(s, 12)
notes(s, "〔約 1:30|累計 19:15〕這頁談可重現性與誠實的限制。\n"
         "左邊『可重現』:套件鎖版本、種子固定;資料視窗記錄清楚(事件用 UTC、測試週用台灣時間);row-time 的防洩漏閘門卡在資料層,每條分支只看得到過去;助教重跑 preprocess.py 就能重現 output_413551034.csv;通過官方 evaluate.py 格式檢查(4,465 人);最終版本會在截止前把資料下載到 11/21 再重跑。\n"
         "右邊『限制與 RDL 何時才有用』:GH Archive 鏡像是降採樣的,群體很稀疏;平均式聚合的 GNN 會過度平滑,圖訊號在這題很弱;RDL 要在跨實體互動密集、邊更豐富時才划算;未來可做:各活動分別調參、用更長的 90 天歷史、校準的滾動門檻、以及真正的 RelBench 時間取樣 GNN。")

# ---------------------------------------------------------------- Slide 13: results & takeaways
s = slide(NAVY)
badge(s, "Results", BLUE)
tf = tb(s, 0.6, 0.92, 12.1, 0.8)
para(tf, "Results & Key Takeaways", size=30, color=WHITE, bold=True, first=True, font=HEAD, space_after=0)
picture(s, ART / "chart_methods.png", 0.5, 2.0, w=7.3)
tf = tb(s, 8.1, 1.9, 4.7, 4.9)
para(tf, "Takeaways", size=16, color=RGBColor(0xC2,0xD2,0xE8), bold=True, first=True, space_after=8)
for t in ["GBDT on temporal + relational features is the best model (Score 33.1) and the submission.",
          "Temporal features are the dominant signal; removing them costs the most (−4.1).",
          "Relational features and GNN message passing add little on this sparse cohort — time dominates.",
          "Strict time-based validation and leakage control throughout; fully reproducible."]:
    para(tf, t, size=13.5, color=WHITE, space_after=8, bullet=True)
tf = tb(s, 8.1, 6.35, 4.7, 0.5)
para(tf, "output_413551034.csv — 4,465 users, passes the official format check.", size=12,
     color=RGBColor(0x9D,0xB4,0xD0), first=True, space_after=0)
footer(s, 13)
notes(s, "〔約 1:15|累計 20:30〕做個總結。左邊長條圖是各模型在驗證週上的比較。四個重點:\n"
         "① 用時間+關聯特徵的 GBDT 是最好的模型,Score 33.1,也是我提交的版本。\n"
         "② 時間特徵是最主要的訊號,拿掉它掉最多(−4.1)。\n"
         "③ 在這稀疏群體上,關聯特徵與 GNN 訊息傳遞幫助很小,是時間在主導。\n"
         "④ 全程嚴格時間切分與防洩漏,且完全可重現。\n"
         "最後,output_413551034.csv 有 4,465 位使用者,通過官方格式檢查。以上是我的報告,謝謝。")

prs.save(str(OUT))
print("saved", OUT, "slides:", len(prs.slides._sldIdLst))
