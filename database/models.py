#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
資料庫 ORM 模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    """使用者表"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, unique=True, nullable=False, index=True)  # LINE User ID
    created_at = Column(DateTime, default=datetime.now)
    last_active_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<User(user_id={self.user_id})>"


class UserInterest(Base):
    """使用者課程興趣記錄表"""
    __tablename__ = 'user_interests'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False, index=True)  # LINE User ID
    course_id = Column(String)  # 課程 ID（可選）
    expressed_interest_at = Column(DateTime, default=datetime.now)  # 表達興趣的時間
    conversation_count = Column(Integer, default=0)  # 對話輪數計數
    last_reminded_at = Column(DateTime)  # 上次提醒時間
    reminder_count = Column(Integer, default=0)  # 已提醒次數
    status = Column(String, default='active')  # active / completed / cancelled
    interest_score = Column(Float)  # BERT 預測的興趣分數
    
    def __repr__(self):
        return f"<UserInterest(user_id={self.user_id}, status={self.status})>"


class Conversation(Base):
    """對話歷史表"""
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    message = Column(String, nullable=False)
    is_user = Column(Boolean, default=True)  # True=使用者訊息, False=機器人回覆
    intent_label = Column(String)  # BERT 分類結果
    intent_score = Column(Float)  # 興趣分數
    created_at = Column(DateTime, default=datetime.now, index=True)
    
    def __repr__(self):
        return f"<Conversation(user_id={self.user_id}, created_at={self.created_at})>"


class CourseCache(Base):
    """課程資料快取表"""
    __tablename__ = 'courses_cache'
    
    id = Column(Integer, primary_key=True)
    course_id = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    category = Column(String)
    start_date = Column(DateTime)
    time = Column(String)
    location = Column(String)
    is_env_edu = Column(Boolean, default=False)  # 是否列入環境教育
    edu_hours = Column(Float, default=0.0)  # 環境教育時數
    cached_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<CourseCache(title={self.title})>"
