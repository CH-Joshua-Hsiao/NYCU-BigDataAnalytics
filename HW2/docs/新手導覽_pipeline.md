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
