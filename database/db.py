#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
資料庫連線設定
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.settings import config
from database.models import Base


# 建立資料庫引擎
engine = create_engine(
    config.DATABASE_URL,
    echo=config.FLASK_DEBUG,  # 在除錯模式下顯示 SQL
    pool_pre_ping=True  # 連線前檢查
)

# 建立 Session 工廠
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """初始化資料庫（建立所有表格）"""
    print("正在初始化資料庫...")
    Base.metadata.create_all(bind=engine)
    print("✅ 資料庫初始化完成！")


def get_db():
    """取得資料庫 Session（用於 Dependency Injection）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    # 執行此檔案會初始化資料庫
    init_db()
