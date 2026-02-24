#!/bin/bash
# 動物園環境教育 Line Bot - 快速設定腳本

echo "=========================================="
echo "🦁 動物園環境教育 Line Bot - 快速設定"
echo "=========================================="

# 檢查 Python 版本
echo ""
echo "📌 檢查 Python 版本..."
python3 --version

if [ $? -ne 0 ]; then
    echo "❌ 錯誤：未安裝 Python 3"
    echo "請先安裝 Python 3.9 或以上版本"
    exit 1
fi

# 建立虛擬環境
echo ""
echo "📌 建立虛擬環境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ 虛擬環境已建立"
else
    echo "ℹ️  虛擬環境已存在，跳過"
fi

# 啟動虛擬環境
echo ""
echo "📌 啟動虛擬環境..."
source venv/bin/activate

# 安裝套件
echo ""
echo "📌 安裝 Python 套件..."
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ 錯誤：套件安裝失敗"
    exit 1
fi

echo "✅ 套件安裝完成"

# 建立 .env 檔案
echo ""
echo "📌 設定環境變數..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ 已建立 .env 檔案"
    echo ""
    echo "⚠️  請編輯 .env 檔案，填入您的金鑰："
    echo "   - LINE_CHANNEL_ACCESS_TOKEN"
    echo "   - LINE_CHANNEL_SECRET"
    echo "   - OPENAI_API_KEY"
else
    echo "ℹ️  .env 檔案已存在，跳過"
fi

# 初始化資料庫
echo ""
echo "📌 初始化資料庫..."
python3 database/db.py

if [ $? -ne 0 ]; then
    echo "❌ 錯誤：資料庫初始化失敗"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ 設定完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "  1. 編輯 .env 檔案，填入您的金鑰"
echo "  2. 執行 python3 app.py 啟動伺服器"
echo "  3. 使用 ngrok 建立公開 URL"
echo "  4. 在 LINE Developers 設定 Webhook"
echo ""
