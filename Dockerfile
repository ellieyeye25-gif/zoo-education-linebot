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

# 安裝 Python 套件
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案檔案
COPY . .

# 暴露端口
EXPOSE 5001

# 設定環境變數
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# 啟動指令
CMD ["gunicorn", "-b", "0.0.0.0:5001", "-w", "4", "app:app"]
