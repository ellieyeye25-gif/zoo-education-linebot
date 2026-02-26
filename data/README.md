# 資料檔案說明

此資料夾存放動物園相關的靜態資料。

## 檔案清單

### 1. courses.csv
動物園課程資料（需要從動物園官網取得）

**欄位說明**：
- `標題`：課程名稱
- `類別`：課程類別（例如：親子活動、環境教育講座）
- `起始日期`：課程開始日期（格式：YYYY-MM-DD）
- `時間`：課程時間
- `地點`：課程地點
- `是否環境教育認證`：是/否
- `環境教育時數`：可累積時數（小時）

**範例**：
```csv
標題,類別,起始日期,時間,地點,是否環境教育認證,環境教育時數
石虎保育講座,環境教育講座,2026-03-15,14:00-16:00,教育中心2F,是,2
親子DIY活動,親子活動,2026-03-20,10:00-12:00,遊客中心,否,0
```

### 2. zoo_areas.json
動物園園區資訊

**範例**：
```json
[
  {
    "id": "panda",
    "name": "貓熊館",
    "description": "館內有大貓熊「團團」和「圓圓」",
    "latitude": 24.9988,
    "longitude": 121.5810,
    "opening_hours": "09:00-17:00"
  }
]
```

### 3. facilities.json
動物園設施資訊（餐廳、廁所、停車場等）

**範例**：
```json
[
  {
    "id": "restaurant_1",
    "name": "動物園餐廳",
    "type": "餐廳",
    "latitude": 24.9990,
    "longitude": 121.5815
  }
]
```

### 4. 環教時數說明.txt
環境教育時數累計方式、護照上限、登錄方式等固定說明文字。Bot 排程提醒或 ChatGPT 回覆「時數怎麼累計／怎麼登錄」時可讀取此檔一併回覆。

### 5. recommended_routes.json
推薦路線

**範例**：
```json
[
  {
    "name": "半日遊路線",
    "duration": "3小時",
    "stops": ["入口", "貓熊館", "企鵝館", "教育中心"],
    "description": "適合時間有限的遊客"
  }
]
```

## 從動物園開放資料篩選（Keeper's Talk、主題教育駐站、定時定點課程）

動物園官網提供 **開放資料（JSON/XML）**。若只要「2月Keeper's Talk、主題教育駐站、定時定點課程」：

1. **用腳本篩選並產出 data 檔**
   ```bash
   # 方式一：指定開放資料 URL（請從動物園「開放資料」頁複製「JSON」連結，不是新聞頁）
   # 注意：URL 一定要用雙引號包住，否則 ? 和 & 會讓終端機報錯
   python scripts/fetch_zoo_activities.py --url "https://www.zoo.gov.taipei/OpenData.aspx?SN=你的SN"

   # 方式二：已下載 JSON 到本機
   python scripts/fetch_zoo_activities.py --file "下載的檔案.json"
   ```
2. 腳本會依標題關鍵字篩選，並寫入：
   - `data/zoo_activities_filtered.json`：篩選後的原始筆數（給 ChatGPT 當 context 或自己查）
   - `data/courses.csv`：專案格式的課程表（標題、類別、時間、地點等）

## 資料來源

- 台北市立動物園官網：https://www.zoo.gov.taipei/
- 動物園開放資料（JSON）：由官網開放資料頁取得連結，例：`OpenData.aspx?SN=...`
- 環境教育終身學習網：https://elearn.epa.gov.tw/

## 簡單英文欄位對照（可自訂）

若想用英文欄位名，可依下表對照；**程式讀取時用英文欄位名即可，不影響辨識**。

### 課程檔（courses，如 courses-February.csv）

| 中文欄位       | 簡單英文建議   |
|----------------|----------------|
| 類別           | category       |
| 主題           | topic          |
| 星期           | weekday        |
| 起始日期       | start_date     |
| 結束日期       | end_date       |
| 時間           | time           |
| 地點           | location       |
| 座標           | coordinates    |
| 環境教育認證   | cert           |
| 環境教育時數   | env_hours      |
| 認證類別       | cert_type      |
| 暫停日期       | closed_dates   |

### 館區介紹（建議檔名：zoo_areas.csv）

| 中文欄位 | 簡單英文建議   |
|----------|----------------|
| 編號     | id             |
| 分類     | category       |
| 名稱     | name           |
| 簡介／介紹 | description  |
| 座標     | coordinates    |
| 連結     | url            |

- **館區介紹** 檔名可改為 **zoo_areas.csv**（與專案 `zoo_areas.json` 對齊，之後若要轉成 JSON 也一致）。
- 欄位名用英文、內容仍用中文沒問題；ChatGPT 與程式都認得。

## 注意事項

- 所有 CSV 檔案請使用 UTF-8 編碼
- 日期格式統一為 `YYYY-MM-DD`
- 時間格式統一為 `HH:MM`
