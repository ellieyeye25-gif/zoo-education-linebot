# 動物園環境教育 Line Bot - Docker 容器設定
# 基於 Python 3.9

FROM python:3.9-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements.txt
COPY requirements.txt .

# 安裝 Python 套件（--no-compile 避免 aenum 等套件在 Python 3.9 編譯失敗）
RUN pip install --no-cache-dir --no-compile -r requirements.txt

# 複製專案檔案
COPY . .

# 暴露端口（Cloud Run 會注入 PORT 環境變數，預設 8080）
EXPOSE 8080
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# 啟動指令（使用 PORT 以相容 Cloud Run）
CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT:-8080} -w 4 app:app"]
