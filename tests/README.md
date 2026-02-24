# 測試說明

此資料夾存放單元測試和整合測試。

## 測試結構

```
tests/
├── test_intent_classifier.py   # BERT 意圖分類器測試
├── test_chatgpt_service.py     # ChatGPT 服務測試
├── test_reminder_service.py    # 提醒機制測試
├── test_line_service.py         # Line Bot 測試
└── test_database.py             # 資料庫測試
```

## 執行測試

### 執行所有測試

```bash
pytest tests/
```

### 執行特定測試

```bash
# 測試意圖分類器
pytest tests/test_intent_classifier.py

# 測試 ChatGPT 整合
pytest tests/test_chatgpt_service.py

# 測試提醒機制
pytest tests/test_reminder_service.py
```

### 查看覆蓋率

```bash
pytest --cov=. tests/
```

## 測試資料

測試資料存放在 `tests/fixtures/` 資料夾中。

## 注意事項

- ⚠️ 測試會使用測試資料庫（SQLite in-memory）
- ⚠️ 測試 ChatGPT 功能時會實際呼叫 API（可能產生費用）
- ✅ 建議在 CI/CD 中跳過需要 API 的測試
