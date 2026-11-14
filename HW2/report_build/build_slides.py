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
              (f"     ·     {n} / 10", {"color": GREY, "size": 10})], first=True, space_after=0)


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
notes(s, "〔約 2:00|累計 3:00〕先看題目:對每一位測試使用者,輸出六個 0/1,代表這六種活動——開 PR、開 issue、"
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
para(tf, [("Raw GH Archive: ", {"bold": True}), ("2026-10-04 → 11-10 (UTC)", {})], size=13.5, space_after=3)
para(tf, [("Training weeks: ", {"bold": True}), ("Oct 13 / 20 / 27 cutoffs", {})], size=13.5, space_after=3)
para(tf, [("Validation: ", {"bold": True}), ("Nov 3 → Nov 10", {})], size=13.5, space_after=3)
para(tf, [("Prediction: ", {"bold": True}), ("Nov 22 → Nov 29 (Taiwan)", {})], size=13.5, space_after=0)
footer(s, 3)
notes(s, "〔約 2:30|累計 5:30〕這頁回答 Q1,畫出 8 張表的 schema 關聯圖。\n"
         "每張表是一個方塊列出欄位;金色 PK 是主鍵,綠色 FK 是外鍵,每個外鍵用箭頭指向它參照的主鍵。\n"
         "Users 跟 Repositories 是兩個樞紐,幾乎所有事件表都指向它們;PullRequests、Issues 又被 reviews/comments 參照。\n"
         "左邊標了每張表的可見時間 row-time(多為 first_seen_at,留言/push 用 created_at);算 t 時刻特徵時只用 row-time < t 的列,避免偷看未來。\n"
         "資料時間區間:原始抓 10/04–11/10;訓練切點 10/13、10/20、10/27;驗證週 11/03–11/10;預測週 11/22–11/29。\n"
         "補充:資料目前只到差不多現在,最終版本我會在截止前重新下載到 11/21 再重跑,讓特徵對齊真正的測試週。")

# ---------------------------------------------------------------- Slide 4: Q2 approach
s = slide()
badge(s, "Q2 · 3%", GOLD)
title(s, "Modeling Relationships Across Tables")
items = [("1", BLUE, "Foreign-key join features",
          "Join User–PR–Review–Issue–Comment: reviews & comments your work received, distinct "
          "reviewers/collaborators, reviews you gave, repo & org breadth."),
         ("2", GREEN, "Repo-neighborhood aggregation",
          "For the repos a user touches, aggregate their recent activity and the number of other active "
          "users — your collaborative community's momentum."),
         ("3", GOLD, "Time-aware heterogeneous GNN (RelBench-style)",
          "A user–repo graph with 6 FK-derived edge types; message passing spreads information from a "
          "user to its repos and back to 2-hop collaborators.")]
y = 1.95
for num, col, head, body in items:
    c = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.7), Inches(y), Inches(0.62), Inches(0.62))
    c.fill.solid(); c.fill.fore_color.rgb = col; c.line.fill.background(); c.shadow.inherit = False
    ptf = c.text_frame; ptf.margin_top = 0; ptf.margin_bottom = 0
    pp = ptf.paragraphs[0]; pp.alignment = PP_ALIGN.CENTER
    rr = pp.add_run(); rr.text = num; rr.font.size = Pt(20); rr.font.bold = True; rr.font.color.rgb = WHITE
    tf = tb(s, 1.6, y - 0.05, 11.0, 1.5)
    para(tf, head, size=18, color=NAVY, bold=True, first=True, space_after=3)
    para(tf, body, size=14.5, color=INK, space_after=0)
    y += 1.5
footer(s, 4)
notes(s, "〔約 2:00|累計 7:30〕Q2 問怎麼利用跨表關聯,我用了三個做法。\n"
         "① 外鍵 join 特徵:把 User–PR–Review–Issue–Comment 串起來,算出你的工作收到多少 review/留言、有多少不同的人 review 你或跟你合作、你給別人送了多少 review、以及參與的 repo/組織廣度。\n"
         "② repo 鄰域聚合:對使用者碰過的 repo,把這些 repo 最近的活動量與其他活躍使用者人數聚合起來,代表社群的動能。\n"
         "③ 時間感知的異質 GNN(RelBench/關聯式深度學習):使用者–repo 的圖,6 種外鍵衍生的邊,訊息從使用者傳到 repo、再回到兩跳外的協作者。\n"
         "前兩個是給樹模型的特徵,第三個是圖神經網路。下一頁看它們到底有沒有幫助。")

# ---------------------------------------------------------------- Slide 5: Q2 results
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
footer(s, 5)
notes(s, "〔約 2:00|累計 9:30〕誠實報告:在這個稀疏群體上,關聯結構幫助很小。\n"
         "① GBDT 拿掉關聯特徵,Score 33.1→33.6,幾乎沒差。② 加上 GNN 訊息傳遞反而掉九分多,節點特徵 30.3→圖 20.9。③ 所以最好的模型還是 GBDT(時間+關聯特徵)。\n"
         "為什麼?下一週的活動主要由使用者自己最近的行為決定(很強的時間自相關);使用者–repo 的圖又很稀疏,平均式聚合把訊號抹平,GNN 反而失去個別訊號。\n"
         "RDL 通常在跨實體互動很密集時才發威;這題是時間主導。這本身就是有價值的發現。我也用每活動 AUC 驗證:一加訊息傳遞,AUC 大約掉到 0.5。")

# ---------------------------------------------------------------- Slide 6: Q3 approach
s = slide()
badge(s, "Q3 · 5%", BLUE)
title(s, "Modeling Temporal Information")
items = [("1", BLUE, "Multi-scale temporal features",
          "Per-activity counts over 1 / 7 / 14 / 30 / 90-day windows, days-since-last (recency), distinct "
          "active days, and 7-day momentum / ratio — including the strong copy-last-week signal."),
         ("2", GREEN, "Strict leakage control",
          "Only rows with row-time < t are visible; never filter by created_at / submitted_at (rows arrive "
          "late); never use known-only-later columns (merged_at, closed_at, state_reason, dismissed_at)."),
         ("3", GOLD, "Time-encoded GNN edges",
          "Each edge carries its age; a neighbour's message is weighted exp(−age / τ), so recent "
          "interactions count more than old ones.")]
y = 1.95
for num, col, head, body in items:
    c = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.7), Inches(y), Inches(0.62), Inches(0.62))
    c.fill.solid(); c.fill.fore_color.rgb = col; c.line.fill.background(); c.shadow.inherit = False
    ptf = c.text_frame; ptf.margin_top = 0; ptf.margin_bottom = 0
    pp = ptf.paragraphs[0]; pp.alignment = PP_ALIGN.CENTER
    rr = pp.add_run(); rr.text = num; rr.font.size = Pt(20); rr.font.bold = True; rr.font.color.rgb = WHITE
    tf = tb(s, 1.6, y - 0.05, 11.0, 1.45)
    para(tf, head, size=18, color=NAVY, bold=True, first=True, space_after=3)
    para(tf, body, size=14.5, color=INK, space_after=0)
    y += 1.5
# mini timeline
ty = 6.55
ln = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.6), Inches(ty), Inches(9.5), Inches(0.02))
ln.fill.solid(); ln.fill.fore_color.rgb = GREY; ln.line.fill.background(); ln.shadow.inherit = False
mk = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(7.1), Inches(ty - 0.18), Inches(0.03), Inches(0.36))
mk.fill.solid(); mk.fill.fore_color.rgb = RED; mk.line.fill.background(); mk.shadow.inherit = False
tf = tb(s, 1.6, ty + 0.06, 5.4, 0.3); para(tf, "features: all history with row-time < t", size=11, color=GREY, first=True, space_after=0)
tf = tb(s, 7.15, ty + 0.06, 4.0, 0.3); para(tf, "labels: next 7 days", size=11, color=RED, first=True, space_after=0)
tf = tb(s, 6.85, ty - 0.46, 1.2, 0.3); para(tf, "t", size=12, color=RED, bold=True, first=True, space_after=0)
footer(s, 6)
notes(s, "〔約 2:30|累計 12:00〕Q3 時間建模,是這套方法的核心,一樣三個重點。\n"
         "① 多尺度時間特徵:對每種活動分別算 1/7/14/30/90 天窗口的次數、距上次多久(recency)、幾天活躍、7 天動能/比率;其中包含很強的「參考上一週」訊號。\n"
         "② 嚴格防洩漏:只有 row-time < t 的列看得到;不用 created_at/submitted_at 判斷可見性(那些列晚點才進來);不用事後才知道的欄位(merged_at、closed_at、state_reason、dismissed_at)。\n"
         "③ 把時間編碼進 GNN 的邊:每條邊帶年齡,鄰居訊息以 exp(−age/τ) 加權,最近的互動比舊的更重要。\n"
         "下方時間軸:t 之前的所有歷史當特徵,接下來 7 天當標籤。")

# ---------------------------------------------------------------- Slide 7: Q3 results
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
footer(s, 7)
notes(s, "〔約 2:00|累計 14:00〕用兩張圖說明時間建模的效果。\n"
         "左圖是特徵群消融:把時間特徵拿掉,Score 33.1→29.0,掉 4.1 分,是所有特徵群裡掉最多的;對照一下,光是「照抄上一週」就有 29.3 分,可見時間資訊的份量。\n"
         "右圖是 GBDT 各活動的 F1:規律型行為(open_issue、pr_review)好預測;爆發型行為(push、程式碼行 review comment)比較難,因為零星不規律。\n"
         "所以這頁直接回答『時間建模帶來什麼幫助』——它是這任務最主要的訊號來源。")

# ---------------------------------------------------------------- Slide 8: Q4 framework
s = slide()
badge(s, "Q4 · 5%", GREEN)
title(s, "Framework")
w8, h8 = picture(s, ART / "framework.png", 0, 1.95, h=4.95)
# center horizontally
s.shapes[-1].left = Inches((13.333 - w8) / 2)
footer(s, 8)
notes(s, "〔約 1:30|累計 15:30〕Q4 要說明整體架構,這張是一頁總覽。\n"
         "從左到右:GH Archive 每小時事件 → preprocess.py → 8 張關聯式資料表 → 三條平行分支(時間特徵、關聯特徵、時間感知 GNN)都餵進模型。\n"
         "注意中間的 leakage gate,它卡在資料表這一層,所以每條分支看到的都只有過去的資料。最後經模型與門檻調整,產出提交檔。下一頁把每一步拆開講。")

# ---------------------------------------------------------------- Slide 9: Q4 pipeline detail
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
footer(s, 9)
notes(s, "〔約 2:00|累計 17:30〕把流程拆成六步。\n"
         "① 前處理:下載 GH Archive 每小時檔,跑官方 preprocess.py,得到 8 張匿名化表(各一個 Parquet)。\n"
         "② 建立樣本:組「使用者+時間切點」的列,標籤=這人未來 7 天有沒有做各活動;只有 row-time < 切點 的列看得到。\n"
         "③ 特徵表示:時間特徵 + 關聯特徵 + 時間感知的使用者–repo 圖。\n"
         "④ 建模:每活動一個 LightGBM(共 6 個)+ 異質 GNN;每活動門檻在驗證週調到 F1 最大。\n"
         "⑤ 驗證與預測:依時間切分,早週訓練、留一週驗證;最後重訓並預測測試週,輸出 output_413551034.csv。\n"
         "⑥ 可重現:套件鎖版本、種子固定、資料區間記錄清楚,助教重跑 preprocess.py 即可重現輸出。")

# ---------------------------------------------------------------- Slide 10: results & takeaways
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
footer(s, 10)
notes(s, "〔約 1:30|累計 19:00〕做個總結。左邊長條圖是各模型在驗證週上的比較。四個重點:\n"
         "① 用時間+關聯特徵的 GBDT 是最好的模型,Score 33.1,也是我提交的版本。\n"
         "② 時間特徵是最主要的訊號,拿掉它掉最多(−4.1)。\n"
         "③ 在這稀疏群體上,關聯特徵與 GNN 訊息傳遞幫助很小,是時間在主導。\n"
         "④ 全程嚴格時間切分與防洩漏,且完全可重現。\n"
         "最後,output_413551034.csv 有 4,465 位使用者,通過官方格式檢查。以上是我的報告,謝謝。")

prs.save(str(OUT))
print("saved", OUT, "slides:", len(prs.slides._sldIdLst))
