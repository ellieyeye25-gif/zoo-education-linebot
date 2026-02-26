#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
動物園環境教育 Line Bot - 主程式
Flask Webhook Server
"""

import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv

from config.settings import config
from services.chatgpt_service import get_reply_and_interest

# 載入環境變數
load_dotenv()

# 初始化 Flask
app = Flask(__name__)

# Line Bot 設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")

if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    print("⚠️  警告：尚未設定 LINE_CHANNEL_ACCESS_TOKEN 或 LINE_CHANNEL_SECRET")
    print("請複製 .env.example 為 .env 並填入您的金鑰")

# 初始化 Line Bot API
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


# ============================================================
# Webhook 路由
# ============================================================

@app.route("/", methods=["GET"])
def index():
    """首頁"""
    return """
    <h1>🦁 動物園環境教育 Line Bot</h1>
    <p>伺服器運行中...</p>
    <p>請在 LINE Developers Console 設定 Webhook URL：</p>
    <code>https://your-domain/callback</code>
    """


@app.route("/callback", methods=["POST"])
def callback():
    """Line Webhook 回調"""
    # 取得 X-Line-Signature header
    signature = request.headers.get("X-Line-Signature", "")
    
    # 取得 request body
    body = request.get_data(as_text=True)
    app.logger.info(f"Request body: {body}")
    
    # 驗證 signature
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.error("Invalid signature. Please check your channel secret.")
        abort(400)
    
    return "OK"


# ============================================================
# Line Bot 事件處理
# ============================================================

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    """處理文字訊息：用 ChatGPT 依課程／館區／環教說明回覆，並解析興趣度"""
    user_message = event.message.text.strip()
    user_id = event.source.user_id

    if not user_message:
        reply_text = "您好！我是動物園環境教育小幫手 🐼\n請輸入想問的內容，例如課程、館區或環境教育時數。"
    else:
        app.logger.info(f"收到訊息 from {user_id}: {user_message}")
        reply_text, interest = get_reply_and_interest(user_message, config)
        if interest:
            app.logger.info(f"興趣度: {interest}")

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )


# ============================================================
# 啟動伺服器
# ============================================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    
    print("=" * 60)
    print("🦁 動物園環境教育 Line Bot")
    print("=" * 60)
    print(f"🌐 伺服器啟動於 http://{host}:{port}")
    print(f"🔧 除錯模式：{'開啟' if debug else '關閉'}")
    print("=" * 60)
    
    app.run(host=host, port=port, debug=debug)
