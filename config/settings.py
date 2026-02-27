#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
系統設定參數
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """系統設定類別"""
    
    # ============================================================
    # Line Bot 設定
    # ============================================================
    LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
    LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
    
    # ============================================================
    # OpenAI 設定
    # ============================================================
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    GPT_MAX_TOKENS = int(os.getenv("GPT_MAX_TOKENS", "1200"))
    GPT_TEMPERATURE = float(os.getenv("GPT_TEMPERATURE", "0.7"))
    
    # ============================================================
    # 資料庫設定
    # ============================================================
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///zoo_bot.db")
    
    # ============================================================
    # Flask 設定
    # ============================================================
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    
    # ============================================================
    # 模型路徑
    # ============================================================
    BERT_MODEL_PATH = os.getenv("BERT_MODEL_PATH", "models/intent_classifier")
    
    # ============================================================
    # 資料路徑
    # ============================================================
    COURSES_CSV_PATH = os.getenv("COURSES_CSV_PATH", "data/courses-February.csv")
    ZOO_AREAS_CSV_PATH = os.getenv("ZOO_AREAS_CSV_PATH", "data/zoo_areas.csv")
    ENV_EDU_NOTES_PATH = os.getenv("ENV_EDU_NOTES_PATH", "data/環教時數說明.txt")
    ZOO_AREAS_JSON_PATH = os.getenv("ZOO_AREAS_JSON_PATH", "data/zoo_areas.json")
    FACILITIES_JSON_PATH = os.getenv("FACILITIES_JSON_PATH", "data/facilities.json")
    
    # ============================================================
    # 提醒機制參數
    # ============================================================
    REMINDER_INTERVAL_ROUNDS = int(os.getenv("REMINDER_INTERVAL_ROUNDS", "3"))
    REMINDER_MAX_TIMES = int(os.getenv("REMINDER_MAX_TIMES", "2"))
    REMINDER_INTERVAL_MINUTES = int(os.getenv("REMINDER_INTERVAL_MINUTES", "10"))
    
    # ============================================================
    # 課程搜尋參數
    # ============================================================
    COURSE_SEARCH_DAYS = 30  # 搜尋未來 30 天的課程
    
    # ============================================================
    # BERT 訓練參數
    # ============================================================
    BERT_BASE_MODEL = "bert-base-chinese"
    BERT_MAX_LENGTH = 128
    BERT_BATCH_SIZE = 16
    BERT_LEARNING_RATE = 2e-5
    BERT_EPOCHS = 5
    BERT_WEIGHT_DECAY = 0.01
    BERT_WARMUP_STEPS = 100
    BERT_DROPOUT = 0.3
    
    # ============================================================
    # 標籤對應
    # ============================================================
    LABEL_MAP = {
        "high_interest": 0,
        "maybe_interest": 1,
        "low_interest": 2
    }
    
    ID2LABEL = {
        0: "high_interest",
        1: "maybe_interest",
        2: "low_interest"
    }
    
    LABEL_NAMES_ZH = {
        0: "高興趣",
        1: "不確定",
        2: "低興趣"
    }
    
    # ============================================================
    # 意圖分類閾值
    # ============================================================
    HIGH_INTEREST_THRESHOLD = 0.7  # 高興趣判定閾值
    
    # ============================================================
    # 伺服器設定
    # ============================================================
    PORT = int(os.getenv("PORT", "5001"))
    HOST = os.getenv("HOST", "0.0.0.0")
    
    # ============================================================
    # 日誌設定
    # ============================================================
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "zoo_bot.log")
    
    @classmethod
    def validate(cls):
        """驗證必要的設定是否已填寫"""
        errors = []
        
        if not cls.LINE_CHANNEL_ACCESS_TOKEN:
            errors.append("LINE_CHANNEL_ACCESS_TOKEN 未設定")
        
        if not cls.LINE_CHANNEL_SECRET:
            errors.append("LINE_CHANNEL_SECRET 未設定")
        
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY 未設定")
        
        if errors:
            print("⚠️  設定錯誤：")
            for error in errors:
                print(f"   - {error}")
            print("\n請複製 .env.example 為 .env 並填入您的金鑰")
            return False
        
        return True


# 建立設定實例
config = Config()
