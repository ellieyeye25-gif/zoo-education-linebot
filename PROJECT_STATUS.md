# 專案進度

## 目前狀態：Day 1-2 完成 ✅

**最後更新**：2026-02-22

## 完成事項

### Week 1: 資料與訓練

#### ✅ Day 1-2：專案建立（完成）
- [x] 建立完整資料夾結構
- [x] 建立 README.md
- [x] 建立 requirements.txt
- [x] 建立 .env.example
- [x] 建立 .gitignore
- [x] 建立 app.py（基礎框架）
- [x] 建立 config/settings.py
- [x] 建立資料庫模型（database/models.py）
- [x] 建立資料庫連線（database/db.py）
- [x] 初始化 Git
- [x] 建立 Dockerfile
- [x] 建立 docker-compose.yml
- [x] 建立快速設定腳本（scripts/setup.sh）

#### ⏳ Day 3-4：資料生成（待完成）
- [ ] 執行 GPT-4 腳本生成 350 筆對話
- [ ] 人工標註 100 筆對話
- [ ] 驗證資料品質

#### ⏳ Day 5：資料處理（待完成）
- [ ] 清洗資料
- [ ] 劃分訓練/驗證/測試集
- [ ] 資料統計分析

#### ⏳ Day 6-7：模型訓練（待完成）
- [ ] 訓練 BERT 意圖分類器
- [ ] 評估模型效能
- [ ] 生成混淆矩陣
- [ ] 儲存訓練好的模型

### Week 2: 系統整合

#### ⏳ Day 8-9：Line Bot 基礎（待完成）
- [ ] 完善 Flask Webhook
- [ ] Line SDK 整合
- [ ] 訊息接收與回覆測試

#### ⏳ Day 10-11：ChatGPT 整合（待完成）
- [ ] 設計 System Prompt
- [ ] 整合 OpenAI API
- [ ] 載入課程資料作為 Context

#### ⏳ Day 12：BERT 整合（待完成）
- [ ] 載入訓練好的 BERT 模型
- [ ] 意圖分類推論
- [ ] 決策邏輯實作

#### ⏳ Day 13-14：資料庫與提醒（待完成）
- [ ] 建立 SQLite 資料庫
- [ ] 實作使用者狀態追蹤
- [ ] 實作主動提醒機制
- [ ] 排程任務設定

### Week 3: 測試與部署

#### ⏳ Day 15-16：測試（待完成）
- [ ] 功能測試
- [ ] 效能測試
- [ ] Bug 修復

#### ⏳ Day 17-18：部署（待完成）
- [ ] Google Cloud Run 部署
- [ ] 設定域名
- [ ] SSL 憑證設定

#### ⏳ Day 19-20：文件撰寫（待完成）
- [ ] 簡報製作
- [ ] Word 報告撰寫
- [ ] README 完善

#### ⏳ Day 21：總結（待完成）
- [ ] 最終測試
- [ ] Demo 影片錄製
- [ ] 專案總結

## 里程碑

- [ ] M1：資料準備完成（Day 5）- 目標：500 筆訓練資料
- [ ] M2：模型訓練完成（Day 7）- 目標：F1 Score > 0.85
- [ ] M3：Line Bot 可用（Day 11）- 目標：可接收訊息並回覆
- [ ] M4：系統整合完成（Day 14）- 目標：BERT + GPT + 提醒機制運作
- [ ] M5：上線部署（Day 18）- 目標：公開可用的 LINE Bot
- [ ] M6：報告完成（Day 20）- 目標：簡報 + Word 報告

## 下一步行動

### 立即執行（Day 3-4）

1. **設定環境變數**
   ```bash
   cp .env.example .env
   # 編輯 .env，填入 LINE 和 OpenAI 金鑰
   ```

2. **執行快速設定腳本**
   ```bash
   ./scripts/setup.sh
   ```

3. **生成訓練資料**
   ```bash
   cd training_data
   python generate_data.py
   ```

4. **人工標註資料**
   - 編輯 `training_data/raw/manual_dialogs.csv`
   - 標註 100 筆高品質對話

## 問題與障礙

目前無。

## 備註

- 專案結構已完整建立
- 基礎檔案已就緒
- Git repository 已初始化
- 準備開始 Day 3-4 的資料生成階段
