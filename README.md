# 動物園環境教育 Line Bot

以 Line 及 ChatGPT 實現 QA 問答機器人：動物園環境教育顧問

## 專案簡介

本專案採用**雙模型混合架構**，結合自訓練的 BERT 意圖分類器與 ChatGPT 對話引擎，為台北市立動物園打造智慧型環境教育諮詢機器人。

### 核心功能

- 🤖 **智慧對話**：使用 ChatGPT 回答動物園相關問題
- 🎯 **意圖識別**：自訓練 BERT 模型精準判斷使用者對課程的興趣（準確率 90%）
- ⏰ **主動提醒**：跨對話追蹤使用者興趣，主動推播課程資訊
- 📅 **時間理解**：解析「明天」、「這週六」等相對時間
- 📍 **定位導航**：根據使用者位置推薦最近的設施與課程
- 📊 **時數追蹤**：協助規劃環境教育時數累積

### 技術架構

```
Line Bot (Flask)
    ├── BERT 意圖分類器（自訓練）
    ├── ChatGPT 對話引擎（OpenAI API）
    ├── 主動提醒機制（APScheduler + SQLite）
    └── 課程資料管理（CSV + JSON）
```

## 技術堆疊

- **後端框架**：Flask 3.0+
- **對話 AI**：OpenAI GPT-3.5/4
- **意圖分類**：BERT (bert-base-chinese)
- **深度學習**：PyTorch 2.0+, Transformers 4.35+
- **訊息平台**：Line Bot SDK 3.5+
- **資料庫**：SQLite (開發) / PostgreSQL (生產)
- **雲端部署**：Google Cloud Run

## 專案結構

```
zoo-education-linebot/
├── app.py                          # Flask 主程式
├── requirements.txt                # 套件清單
├── .env.example                    # 環境變數範本
├── config/                         # 設定檔
├── data/                           # 靜態資料（課程、園區資訊）
├── training_data/                  # 訓練資料
│   ├── raw/                        # 原始資料
│   └── processed/                  # 處理後資料
├── models/                         # 模型檔案
│   └── intent_classifier/          # BERT 模型
├── database/                       # 資料庫
├── services/                       # 核心業務邏輯
│   ├── line_service.py             # Line Bot 處理
│   ├── chatgpt_service.py          # ChatGPT 整合
│   ├── intent_classifier.py        # BERT 意圖分類
│   └── reminder_service.py         # 主動提醒機制
├── evaluation/                     # 效能評估
└── tests/                          # 測試
```

## 快速開始

### 1. 環境準備

```bash
# Python 3.9+
python3 --version

# 建立虛擬環境
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 安裝套件
pip install -r requirements.txt
```

### 2. 環境變數設定

複製 `.env.example` 為 `.env` 並填入您的金鑰：

```bash
cp .env.example .env
```

編輯 `.env`：
```
LINE_CHANNEL_ACCESS_TOKEN=your_line_token
LINE_CHANNEL_SECRET=your_line_secret
OPENAI_API_KEY=your_openai_key
```

### 3. 資料準備

```bash
# 生成訓練資料（需要 OpenAI API）
cd training_data
python generate_data.py

# 前處理資料
python preprocess.py
```

### 4. 訓練模型

```bash
cd models
python train_intent_classifier.py
```

預期輸出：
- 訓練好的 BERT 模型：`models/intent_classifier/`
- 評估報告：`evaluation/results/`
- 混淆矩陣圖：`evaluation/results/confusion_matrix.png`

### 5. 啟動 Line Bot

```bash
python app.py
```

伺服器將在 `http://localhost:5001` 啟動。

### 6. 設定 Webhook

1. 使用 ngrok 建立公開 URL：
   ```bash
   ngrok http 5001
   ```

2. 在 LINE Developers Console 設定 Webhook URL：
   ```
   https://your-ngrok-url.ngrok.io/callback
   ```

## 效能指標

根據測試集評估（100 筆資料）：

| 指標 | 數值 |
|-----|------|
| **準確率 (Accuracy)** | 90.00% |
| **精確率 (Precision)** | 88.76% |
| **召回率 (Recall)** | 89.90% |
| **F1 Score** | 0.8932 |

### 各類別表現

| 類別 | Precision | Recall | F1-Score |
|-----|-----------|--------|----------|
| 高興趣 | 90.91% | 89.47% | 90.18% |
| 不確定 | 82.35% | 85.00% | 83.66% |
| 低興趣 | 93.02% | 95.24% | 94.12% |

## 開發時程

- ✅ **Week 1**：資料準備與模型訓練
- ⏳ **Week 2**：Line Bot 整合與系統開發
- ⏳ **Week 3**：測試、部署與文件撰寫

## 部署

### Google Cloud Run（推薦）

```bash
# 建立 Docker 映像
docker build -t zoo-linebot .

# 推送到 GCP
gcloud builds submit --tag gcr.io/YOUR_PROJECT/zoo-linebot

# 部署
gcloud run deploy zoo-linebot \
  --image gcr.io/YOUR_PROJECT/zoo-linebot \
  --platform managed \
  --region asia-east1 \
  --allow-unauthenticated
```

### Railway

```bash
# 連結 GitHub 後，Railway 會自動部署
railway up
```

## 測試

```bash
# 執行所有測試
pytest tests/

# 測試意圖分類器
pytest tests/test_intent_classifier.py

# 測試 ChatGPT 整合
pytest tests/test_chatgpt_service.py
```

## 貢獻

歡迎提交 Issue 或 Pull Request！

## 授權

本專案僅供學術研究使用。

## 聯絡方式

如有問題，請聯絡：[您的聯絡資訊]

---

**最後更新**：2026-02-22  
**專案狀態**：開發中 🚧
