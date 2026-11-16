# HW2 管線新手導覽 —— 每一步在做什麼、用什麼方法

> 這份文件把整個專案「從原始資料到交出答案」拆成 6 大步,用白話解釋每一步**在做什麼**、**為什麼要做**、**用了什麼方法**。假設你完全沒碰過這個專案。

---

## 0. 先搞懂「題目」在問什麼

我們要預測:**4,465 位 GitHub 使用者**,在**測試週(2026-11-22 ~ 11-29,台灣時間)**會不會做下面這 6 種動作,每種填一個 0 或 1:

| 活動 | 白話 |
|---|---|
| `open_pr` | 開一個 Pull Request |
| `open_issue` | 開一個 Issue |
| `issue_comment` | 在 Issue 底下留言 |
| `pr_review` | 審查別人的 PR |
| `pr_review_comment` | 在 PR 審查裡留言 |
| `push` | push 程式碼 |

- **輸入**:`starter/submission/test_input.csv`(就是那 4,465 個 UserID)。
- **輸出**:`output_413551034.csv`,4,465 列 × 6 個 0/1。
- **評分**:`Score = (macro-F1 + micro-F1) / 2`。
  - *F1* 是「抓對」與「抓全」的平衡分數;*macro* 是 6 個活動各算一次再平均,*micro* 是全部混在一起算。

> ⚠️ 重點:這份「預測分數其實佔 0%」。真正的分數在**影片 + 投影片回答 4 個問題(14%)**。所以我們的目標是「**管線能重現 + 分析誠實**」,不是硬衝分數。

---

## 1. 下載原始資料(raw)

**在做什麼**:把 GitHub 公開事件流(GH Archive)一小時一小時的壓縮檔抓下來。

**方法**:
- 資料來源是 [GH Archive](https://www.gharchive.org),每個小時一個檔:`2026-11-16-9.json.gz`。
- 用 `tools/download_raw.sh START END`,它會**跳過已經下載好的檔案**(可以中途斷掉再續),抓進 `raw/`。

```bash
bash tools/download_raw.sh 2026-10-04 2026-11-21
```

**小知識**:這裡的 GH Archive 是一個「**降採樣的鏡像**」(一小時只有幾 MB、約 5,700 筆事件),所以我們鎖定的那 9,000 人事件很稀疏。今天還沒產生的小時檔會回 404,正常跳過即可。

---

## 2. 把原始事件整理成 8 張「關聯式資料表」(preprocess)

**在做什麼**:原始檔是一堆雜亂的 JSON 事件,要把它整理成乾淨的、彼此有關聯的 8 張表(就像資料庫)。

**方法**:**用課程官方的 `starter/scripts/preprocess.py`**(很重要——TA 會用同一支腳本重跑,所以我們不能自己亂改)。

```bash
.venv/Scripts/python starter/scripts/preprocess.py --raw raw --out data
```

產出 8 張 Parquet 表(存在 `data/db/`):

| 表 | 內容 |
|---|---|
| `Users` | 使用者 |
| `Repositories` | 專案倉庫 |
| `PullRequests` | PR |
| `Issues` | Issue |
| `IssueComments` | Issue 留言 |
| `PRReviews` | PR 審查 |
| `PRReviewComments` | PR 審查留言 |
| `Pushes` | push 事件 |

這些表之間用「外鍵(FK)」互相連結(例如一個 PR 屬於哪個 repo、哪個 user),這就是所謂的 **relational data(關聯式資料)**,也是題目 Q2 要你談的東西。

> 📌 腳本只保留我們那群人的事件、而且 user 的 id 是**固定對應**的,所以不管你處理哪段時間,`github_user_id` 永遠對得上 `test_input.csv`。

---

## 2.5 這 8 張表怎麼互相關聯?(關聯 schema)

這段是 Q2 的核心。每張表都有一個**主鍵(PK)**(自己的 id),再用**外鍵(FK)**指向別張表的主鍵——就像 Excel 用「某欄的值」去對照另一張表。

### 兩張「核心實體」表(被其他表指著)
| 表 | 主鍵 | 代表 |
|---|---|---|
| `Users` | `user_id` | 一個人(`is_cohort`=我們要預測的那群;`is_bot`=機器人) |
| `Repositories` | `repo_id` | 一個專案倉庫(`org_id` 指向所屬組織) |

### 六張「活動事件」表(每一列=一次行為,都指回 User 和 Repo)
| 表 | 主鍵 | 「誰做的」FK→Users | 「在哪做的」FK→Repos | 其他重要 FK |
|---|---|---|---|---|
| `PullRequests` | `pr_id` | `author_id` | `repo_id` | `head_repo_id`→Repos、`merged_by_id`→Users⚠️ |
| `Issues` | `issue_id` | `author_id` | `repo_id` | `assignee_id`→Users |
| `IssueComments` | `comment_id` | `author_id` | `repo_id` | `issue_id`→Issues |
| `PRReviews` | `review_id` | `reviewer_id` | `repo_id` | `pr_id`→PullRequests |
| `PRReviewComments` | `comment_id` | `author_id` | `repo_id` | `pr_id`→PR、`pull_request_review_id`→PRReviews、`in_reply_to_id`→自己 |
| `Pushes` | `push_id` | `user_id` | `repo_id` | — |

### 關聯圖(箭頭 = 「指向…的主鍵」)

```
        ┌──────────────┐          ┌────────────────┐
        │    Users     │          │  Repositories  │
        │  (user_id)   │◄───┐ ┌──►│   (repo_id)    │
        └──────────────┘    │ │   └────────────────┘
            ▲  ▲  ▲         │ │        ▲  ▲  ▲  ▲  ▲
    author_/ │  \reviewer   │ │  repo_id(每張事件表都有一個)
            │  │   │   ┌────┘ └────┐  │  │  │  │  │
     ┌──────┴┐ │ ┌─┴──────┐ ┌─────┴─┐ │ ┌┴────────┐
     │  PRs  │ │ │ Issues │ │ Pushes│ │ │IssueCmts│
     └───┬───┘ │ └───┬────┘ └───────┘ │ └────┬────┘
   pr_id │     │     │ issue_id       │      │
     ┌───┴─────┴─┐   └────────────────┘      │
     │ PRReviews │◄──pull_request_review_id  │
     └─────┬─────┘        ┌──────────────────┘
           │         ┌────┴──────────────┐
           └─pr_id──►│ PRReviewComments  │
                     └───────────────────┘
```

**白話總結**:所有活動最後都收斂到「**某個 User 在某個 Repo 做了某件事**」。這就是我們能做「關聯特徵」的基礎——沿著 `repo_id` 可以找到「同一個 repo 裡的其他人/其他事件」,沿著 `author_id` 可以找到「同一個人在別處的行為」。

### 每個「要預測的活動」對應哪張表(`config.ACTIVITY_SOURCE`)
| 活動 | 來源表 | 「做這件事的人」欄位 | 動作時間 |
|---|---|---|---|
| `open_pr` | PullRequests | `author_id` | `created_at` |
| `open_issue` | Issues(排除本身是 PR 的列) | `author_id` | `created_at` |
| `issue_comment` | IssueComments | `author_id` | `created_at` |
| `pr_review` | PRReviews | `reviewer_id` | `submitted_at` |
| `pr_review_comment` | PRReviewComments | `author_id` | `created_at` |
| `push` | Pushes | `user_id` | `created_at` |

> ⚠️ 標了「未來欄位」的(如 `merged_by_id`、`merged_at`、`closed_at`、`state_reason`、`dismissed_at`)**只能用來算標籤或了解資料,絕不能當特徵**——因為那是事情發生「之後」才知道的,見 `config.FUTURE_COLUMNS`。

---

## 3. 做「標籤(labels)」—— 答案長什麼樣

**在做什麼**:要訓練模型,得先有「正確答案」給它學。標籤就是「某個使用者在某一週,這 6 種活動各做了沒有(0/1)」。

**方法**(`src/labels.py`):
- 給定一週的時間範圍,去 8 張表裡查:這週內該使用者有沒有做某活動 → 有就 1、沒有就 0。
- 判斷「有沒有做」是看**動作時間**(`created_at` / `submitted_at`)。
- 標籤是從「資料已經長全」的表來算的,所以可以放心用動作時間。

這一步會對**好幾個過去的週**各做一份標籤,當成訓練/驗證教材(見第 5 步)。

---

## 4. 做「特徵(features)」—— 給模型看的線索

**在做什麼**:模型不能直接吃原始表,要先把每個使用者「濃縮成一排數字」。這排數字就是特徵。

**方法**(`src/features.py`),分兩大類:

### (A) 時間特徵 temporal —— 「這個人最近多活躍?」
- **多視窗計數**:過去 `1 / 7 / 14 / 30 / 90` 天,各活動各做了幾次。
- **最近一次(recency)**:距離上次做這件事幾天了(從沒做過就填 180 天上限)。
- **活躍天數、動能(momentum)**:最近是越來越勤還是變冷。

### (B) 關聯特徵 relational —— 「這個人周圍的圈子在做什麼?」
- 沿著外鍵把相關的表 join 起來。
- 看他常待的 repo 鄰居(repo-neighborhood)最近的活動。

### 🔑 最重要的規則:不能偷看未來(防資料洩漏 leakage)
預測時間點是 `t`。一條資料**只有在它的「出現時間 < t」才能用**。
- 為什麼?因為 PR/issue/review 這些資料是**晚一點才進到資料裡的**,如果直接用它們的 `created_at` 判斷「看得到沒」,等於偷看了未來。
- 也**絕對不能**用「只有事後才知道」的欄位當特徵,例如 PR 的 `merged_at`、Issue 的 `closed_at`(這些寫在 `config.FUTURE_COLUMNS`)。

> 這一整套「哪些資料在時間 `t` 可見」的邏輯,集中在 `data.visible_rows()`。這是整個專案最容易出錯、也最關鍵的地方。

---

## 5. 訓練模型並比較(models)

**在做什麼**:用「過去幾週的特徵 + 標籤」教模型,再看它預測得準不準。

### 怎麼切訓練/驗證?
**一定要「按時間切」,不能隨機切**。用較早的週訓練、較晚的一週驗證。隨機切會把未來洩漏進訓練,分數會虛高。

### 試了哪些方法?(`src/`)

| 方法 | 是什麼 | 檔案 |
|---|---|---|
| **All-zero** | 全部猜 0,當最低底線 | `baselines.py` |
| **Copy-last-week** | 「上週做過的,這週也會做」——最直覺的基準 | `baselines.py` |
| **GBDT ⭐(提交用)** | 6 個 LightGBM(梯度提升決策樹),一個活動一個模型,每個再自動挑最佳 0/1 門檻 | `gbdt.py` |
| **GNN** | 時間感知的異質圖神經網路,在 user–repo 的外鍵圖上做訊息傳遞(純 torch 手寫) | `gnn.py` |

- **GBDT**:一種很強的表格資料模型,把很多小決策樹疊起來。這裡**每個活動各訓練一個**,互不干擾。
- **GNN**:想試「關聯結構(朋友/共用 repo)能不能幫忙預測」,也就是 Q2 想探討的 RDL(關聯深度學習)。

`experiments.py` 會一次把這些方法全跑一遍、再做**消融實驗(ablation)**:故意把某類特徵拿掉,看分數掉多少,用來回答 Q2/Q3。

### 🔬 訓練細節(以提交用的 GBDT 為例)

這段把「第 5 步到底怎麼訓練」講清楚,對照 `src/dataset.py` 與 `src/gbdt.py`。

**(1) 訓練資料怎麼來——「一週一個切點」**(`dataset.py`)
- 選定幾個「週切點 `t`」。對每個 `t`:
  - **特徵** = 用「`t` 之前看得到的資料」算(第 4 步,嚴格不洩漏)。
  - **標籤** = 看「`[t, t+7天)` 這一週」該使用者各活動有沒有做。
- 把**較早的 3 週**疊起來當**訓練集**,**較晚的 1 週**當**驗證集**。
  - 例:訓練切點 `10-13 / 10-20 / 10-27`,驗證週 `11-03~11-10`。
- 這就是「**按時間切,不隨機切**」——驗證週永遠在訓練週「之後」,模擬真實情況(用過去預測未來)。隨機切會把未來資料混進訓練,分數會假性變高。

**(2) 模型本體——6 個獨立的 LightGBM**(`gbdt.py`)
- 6 個活動**各訓練一個二元分類器**(「會做 / 不會做」),彼此不干擾。
- LightGBM 是「梯度提升決策樹」:疊很多棵小決策樹,每棵修正前面的錯誤。主要參數(`DEFAULT_PARAMS`):
  - `n_estimators=400`(400 棵樹)、`learning_rate=0.03`(學慢一點比較穩)、`num_leaves=63`(每棵樹的複雜度)。
  - `subsample=0.8`、`colsample_bytree=0.8`(每次只抽部分資料/欄位,防過擬合)、`reg_lambda=1.0`(正則化)。
  - `random_state=42` + `deterministic=True`:**固定隨機種子,保證 TA 重跑結果一樣**(可重現是這份作業的硬要求)。
- 如果某活動在訓練週裡「從沒出現過」(全是 0),就跳過、直接預測 0。

**(3) 門檻調校——把機率變成 0/1**
- 模型輸出的是「機率」(例如 0.37),要變成 0 或 1 得定一個**門檻**。
- 這裡**每個活動各自找最佳門檻**:在驗證週上掃一遍,挑「讓 F1 最高」的那個門檻(`best_threshold()`)。
- 為什麼要各別調?因為 6 個活動的正例比例差很多(push 很多、pr_review_comment 很少),用同一個 0.5 門檻會吃虧。這一步直接對準評分指標 F1。

**(4) 評分——跟官方一致**(`gbdt.score()`)
- 自己實作了一份 `Score = (macro-F1 + micro-F1)/2`,和官方 `evaluate.py` 算法完全一致,這樣在本地驗證時看到的分數就能對應真實評分。

**(5) 最終出題**(`predict.py`)
- 確認方法後,用「到目前為止的全部資料」重訓一次,對測試週的 4,465 人輸出 0/1(見第 6 步)。

### 結果與誠實的結論(`artifacts/results.md`)
驗證週的分數大致是:
- Copy-last-week ≈ 29;**GBDT(全特徵)≈ 33(提交版)**;
- 拿掉時間特徵 → 掉到 ≈ 29(**時間特徵最關鍵**);
- 拿掉關聯特徵 → 幾乎不變;GNN 加了圖反而更差。

> **誠實發現**:下一週會做什麼,**主要由使用者自己最近的歷史決定**(時間自相關很強);在這個稀疏的 user–repo 圖上,關聯特徵與 GNN 的訊息傳遞幫助不大。這就是 Q3(時間)是強故事、Q2(關聯)講「我們認真試過、也說明 RDL 什麼時候才有用」的原因。**這個結論是如實報告的,評分獎勵分析、懲罰捏造。**

---

## 6. 產出提交檔(predict)

**在做什麼**:用「到目前為止全部的資料」訓練最終模型,對那 4,465 人預測測試週,寫成 csv。

**方法**(`src/predict.py` / `run.py predict`):

```bash
.venv/Scripts/python run.py predict --weeks 4
```

- 沒出現在任何表裡的使用者 → 全部預測 0。
- **時間小訣竅**:真正的測試週(11/22)還在未來,只要資料還沒到那天,`effective_predict_time()` 會**自動退回「最後一筆資料的那個午夜」**當作切點,並印出提醒。
- 最後用官方腳本做格式檢查:

```bash
.venv/Scripts/python starter/scripts/evaluate.py --pred output_413551034.csv --input starter/submission/test_input.csv
```

---

## 整體流程圖

```
raw/ (GH Archive 小時檔)
   │  ① download_raw.sh
   ▼
data/db/ 8 張 Parquet 表        ② 官方 preprocess.py
   │
   ├─③ labels.py  ──► 過去幾週的「答案」
   │
   └─④ features.py ─► 每人一排數字(時間特徵 + 關聯特徵,且不洩漏未來)
                         │
                         ▼
                  ⑤ 訓練 & 比較模型(GBDT ⭐ / baselines / GNN)
                         │
                         ▼
                  ⑥ predict.py ──► output_413551034.csv(4465 × 6)
```

---

## 一句話總結每個檔案(`src/`)

| 檔案 | 一句話 |
|---|---|
| `config.py` | 所有設定:6 個活動、時間窗、哪些欄位算「未來」、哪張表對哪個活動 |
| `data.py` | 載入 8 張表;`visible_rows()` 決定時間 `t` 能看到哪些資料(防洩漏核心) |
| `labels.py` | 從動作時間建 6 個 0/1 標籤 |
| `features.py` | 把每個人濃縮成特徵(時間 + 關聯),`FEATURE_GROUPS` 供消融用 |
| `dataset.py` | 組 (使用者, 切點) 範例;按時間切 train/val |
| `baselines.py` | copy-last-week、all-zero 兩個基準 |
| `gbdt.py` | 6 個 LightGBM + 每活動最佳門檻(提交用) |
| `gnn.py` | user–repo 圖上的時間感知 GraphSAGE(實驗用) |
| `experiments.py` | 一次跑完所有方法 + Q2/Q3 消融,產出比較表 |
| `predict.py` | 寫出最終 submission |
| `run.py` | 統一入口:`smoke` / `evaluate` / `predict` / `full` |
