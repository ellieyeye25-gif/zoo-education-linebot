# 訓練資料說明

此資料夾存放 BERT 意圖分類器的訓練資料。

## 資料夾結構

```
training_data/
├── raw/                    # 原始資料
│   ├── generated_dialogs.csv   # GPT-4 生成的對話
│   └── manual_dialogs.csv      # 人工標註的對話
├── processed/              # 處理後資料
│   ├── train.csv          # 訓練集 (70%)
│   ├── val.csv            # 驗證集 (15%)
│   └── test.csv           # 測試集 (15%)
├── generate_data.py        # 資料生成腳本
└── preprocess.py           # 資料前處理腳本
```

## 資料格式

### CSV 格式

```csv
text,label
我想參加環境教育課程,high_interest
有什麼活動,maybe_interest
門票多少錢,low_interest
```

### 標籤定義

- `high_interest`：高興趣（明確想參加課程）
- `maybe_interest`：不確定（開放式詢問）
- `low_interest`：低興趣（一般動物園資訊）

## 使用方式

### 1. 生成訓練資料

```bash
cd training_data
python generate_data.py
```

需要設定 `OPENAI_API_KEY` 環境變數。

### 2. 前處理資料

```bash
python preprocess.py
```

會自動：
- 清洗資料（去除重複、異常值）
- 劃分資料集（70/15/15）
- 儲存到 `processed/` 資料夾

## 資料配比

| 來源 | 數量 | 比例 |
|-----|------|------|
| GPT-4 生成 | 350 筆 | 70% |
| 人工標註 | 100 筆 | 20% |
| 真實對話 | 50 筆 | 10% |
| **總計** | **500 筆** | **100%** |

## 注意事項

- ⚠️ `raw/` 資料夾中的 CSV 檔案不會被 Git 追蹤（已在 .gitignore 中）
- ✅ 請定期備份訓練資料
- ✅ 真實對話資料需在系統上線後收集
