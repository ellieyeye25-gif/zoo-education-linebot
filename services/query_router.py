#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
查詢路由：依查詢類型分流。
- 結構化查詢（票價/開放時間/公休/交通/遊園須知/附近館區）→ Python 直接回應
- 課程日期查詢 → Python 篩選課程後直接回應
- 語意/開放式查詢 → chatgpt_service（含興趣度偵測）
"""

import os
import re
import csv
import math
import logging
from datetime import datetime, timezone, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TW_TZ = timezone(timedelta(hours=8))


def _path(name):
    return os.path.join(PROJECT_ROOT, name)


# ── 館區公休排程（供 Python 直接計算） ───────────────────────────
# ("monthly", N) = 每月第 N 個週一公休；("weekly", 0) = 每週一公休
_CLOSURE_SCHEDULE = {
    "大貓熊館":             ("monthly", 1),
    "新光特展館（大貓熊館）":  ("monthly", 1),
    "熱帶雨林室內館（穿山甲館）": ("monthly", 2),
    "穿山甲館":             ("monthly", 2),
    "企鵝館":               ("monthly", 2),
    "兩棲爬蟲動物館":        ("monthly", 3),
    "昆蟲館":               ("monthly", 4),
    "酷Cool節能屋":          ("weekly",  0),
    "教育中心":              ("weekly",  0),
}

# 連假順延休館日 (月, 日): [館名, ...]
_HOLIDAY_CLOSURES = {
    (4,  7): ["教育中心", "大貓熊館"],
    (9, 29): ["教育中心", "昆蟲館"],
    (10,27): ["教育中心", "昆蟲館"],
}


# ── 關鍵字分類表 ────────────────────────────────────────────────
_VISITOR_KEYWORDS = {
    "ticket": [
        "票價", "多少錢", "費用", "門票", "全票", "免票", "免費入場",
        "優待票", "票種", "票券", "要錢嗎", "入場費", "幾元",
        "學生票", "市民票", "團體票", "需要付費", "怎麼買票",
    ],
    "hours": [
        "幾點", "開放時間", "開門", "關門", "幾點開", "幾點關",
        "開到幾點", "幾點到幾點", "開放到", "營業時間",
    ],
    "closure": [
        "公休", "休館", "休息", "有開嗎", "今天開嗎",
        "哪天休", "輪休", "閉館", "有沒有開",
    ],
    "transport": [
        "交通", "怎麼去", "停車", "捷運", "公車", "怎麼搭",
        "如何到", "怎麼到", "停車場", "公共運輸",
    ],
    "rules": [
        "遊園須知", "注意事項", "禁止", "規定", "規則",
        "可以帶寵物", "能帶寵物", "可以帶狗", "能帶狗",
        "可以帶傘", "可以飲食", "可以吃東西",
    ],
    "itinerary": [
        "建議行程", "怎麼逛", "怎麼玩", "先去哪", "從哪開始",
        "排行程", "遊園路線", "建議路線", "行程規劃",
    ],
}

_NEARBY_TRIGGERS = [
    "附近", "旁邊", "接下來去哪", "下一站", "我在", "我現在在",
    "從這邊", "從這裡", "最近的館", "走去哪",
]


# ── 工具函式 ────────────────────────────────────────────────────

def _classify_visitor_query(message):
    """偵測是否為參觀資訊查詢，回傳類型字串或 None。"""
    for qtype, keywords in _VISITOR_KEYWORDS.items():
        for kw in keywords:
            if kw in message:
                return qtype
    return None


def _has_nearby_trigger(message):
    return any(t in message for t in _NEARBY_TRIGGERS)


def _parse_coords(coord_str):
    """從 MULTIPOINT ((lon lat)) 解析 (lat, lon)，失敗回傳 (None, None)。"""
    m = re.search(r'MULTIPOINT\s*\(\(\s*([\d.]+)\s+([\d.]+)\s*\)\)', coord_str)
    if m:
        return float(m.group(2)), float(m.group(1))  # (lat, lon)
    return None, None


def _haversine_m(lat1, lon1, lat2, lon2):
    """兩點間直線距離（公尺）。"""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _load_areas(csv_path):
    """讀取館區 CSV，回傳含座標與別名的館區清單。"""
    areas = []
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                name = row.get("name", "").strip()
                if not name:
                    continue
                lat, lon = _parse_coords(row.get("coordinates", ""))
                if lat is None:
                    continue
                aliases = [name]
                if "穿山甲" in name:
                    aliases.append("穿山甲館")
                if "大貓熊" in name:
                    aliases.append("大貓熊館")
                if "鳥園" in name:
                    aliases.append("鳥園")
                if "兩棲爬蟲" in name:
                    aliases += ["爬蟲館", "兩棲館", "兩棲爬蟲館"]
                areas.append({
                    "name": name,
                    "aliases": aliases,
                    "lat": lat,
                    "lon": lon,
                    "category": row.get("category", "").strip(),
                })
    except Exception as e:
        logging.error(f"_load_areas 失敗: {e}")
    return areas


def _extract_area_from_message(message, areas):
    """從訊息中偵測館區名稱，回傳 area dict 或 None。"""
    for area in areas:
        for alias in area["aliases"]:
            if alias in message:
                return area
    return None


def _nearby_text(current_area, all_areas, top_n=6):
    """計算距離，回傳附近館區文字。"""
    lat0, lon0 = current_area["lat"], current_area["lon"]
    dists = []
    for area in all_areas:
        if area["name"] == current_area["name"]:
            continue
        d = _haversine_m(lat0, lon0, area["lat"], area["lon"])
        dists.append((d, area["name"]))
    dists.sort(key=lambda x: x[0])
    lines = [f"距離「{current_area['name']}」由近到遠的館區："]
    for i, (d, name) in enumerate(dists[:top_n], 1):
        dist_str = f"{int(d)}公尺" if d < 1000 else f"{d / 1000:.1f}公里"
        lines.append(f"{i}. {name}（約{dist_str}）")
    return "\n".join(lines)


def _load_section(file_path, section_marker):
    """從 txt 檔讀取特定 === 章節 === 的內容（不含標題行）。"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        start = content.find(section_marker)
        if start == -1:
            return "(找不到相關資訊)"
        next_sec = content.find("\n=== ", start + len(section_marker))
        block = content[start:next_sec].strip() if next_sec != -1 else content[start:].strip()
        lines = block.split("\n")
        return "\n".join(lines[1:]).strip()
    except Exception as e:
        return f"(讀取失敗: {e})"


def _is_area_closed(area_name, date):
    """
    判斷指定館區在 date 當天是否公休。
    回傳 True / False / None（不在排程表中）。
    """
    # 連假順延
    key = (date.month, date.day)
    if key in _HOLIDAY_CLOSURES:
        if area_name in _HOLIDAY_CLOSURES[key]:
            return True

    sched = _CLOSURE_SCHEDULE.get(area_name)
    if sched is None:
        return None
    stype, ref = sched
    wd = date.weekday()  # 0=週一
    if stype == "weekly":
        return wd == ref
    if stype == "monthly" and wd == 0:
        week_num = (date.day - 1) // 7 + 1
        return week_num == ref
    return False


# ── 處理各類查詢 ─────────────────────────────────────────────────

def _handle_closure_query(message, visitor_info_path, now_dt):
    """處理館區公休查詢，若訊息包含特定館名則即時計算，否則回傳完整公休表。"""
    areas_path = _path("data/zoo_areas.csv")
    areas = _load_areas(areas_path)
    area = _extract_area_from_message(message, areas)

    if area:
        name = area["name"]
        closed = _is_area_closed(name, now_dt)
        weekday_names = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]
        today_str = f"{now_dt.month}月{now_dt.day}日（{weekday_names[now_dt.weekday()]}）"
        if closed is True:
            return f"「{name}」今天（{today_str}）公休，建議明天或其他日子再來參觀。\n\n" \
                   + _load_section(visitor_info_path, "=== 館區公休 ===")
        elif closed is False:
            return f"「{name}」今天（{today_str}）正常開放！\n\n" \
                   + _load_section(visitor_info_path, "=== 館區公休 ===")
        else:
            return f"「{name}」無固定公休日，全年正常開放。\n\n" \
                   + _load_section(visitor_info_path, "=== 館區公休 ===")

    return _load_section(visitor_info_path, "=== 館區公休 ===")


def _handle_visitor_query(query_type, visitor_info_path, message, now_dt):
    """依查詢類型回傳參觀資訊文字。"""
    section_map = {
        "ticket":    ["=== 參觀票價 ===", "=== 票種說明 ==="],
        "hours":     ["=== 開放時間 ===", "=== 遊客列車時刻 ==="],
        "transport": ["=== 交通及停車 ==="],
        "rules":     ["=== 遊園須知 ==="],
        "itinerary": ["=== 建議行程 ==="],
    }
    if query_type == "closure":
        return _handle_closure_query(message, visitor_info_path, now_dt)

    sections = section_map.get(query_type, [])
    parts = [_load_section(visitor_info_path, s) for s in sections]
    return "\n\n".join(p for p in parts if p and not p.startswith("("))


# ── 主路由函式 ───────────────────────────────────────────────────

def route_message(message, config, now_str="", now_dt=None):
    """
    主路由：依查詢類型分流處理，回傳 (reply_text, interest_label)。

    優先順序：
      1. 附近館區查詢（含行程排列）
      2. 參觀資訊查詢（票價/時間/公休/交通/遊園須知/建議行程）
      3. 課程日期查詢（Python 篩選，直接回應）
      4. 其他語意查詢 → GPT
    """
    from services.chatgpt_service import (
        detect_query_weekday,
        load_courses_for_weekday,
        get_reply_and_interest,
    )

    if now_dt is None:
        now_dt = datetime.now(TW_TZ)

    areas_path = _path("data/zoo_areas.csv")
    visitor_info_path = _path("data/visitor_info.txt")
    courses_path = _path(getattr(config, "COURSES_CSV_PATH", "data/courses-February.csv"))

    # ── 1. 附近館區查詢 ──────────────────────────────────────────
    if _has_nearby_trigger(message):
        areas = _load_areas(areas_path)
        current_area = _extract_area_from_message(message, areas)
        if current_area:
            nearby = _nearby_text(current_area, areas)
            # 若同時要求排行程 → 附加建議行程資訊，讓 GPT 整合後回覆
            if any(kw in message for kw in ["行程", "路線", "怎麼逛", "怎麼玩", "接下來"]):
                itinerary = _load_section(visitor_info_path, "=== 建議行程 ===")
                # 把距離資訊注入 message，交 GPT 整合
                augmented_msg = (
                    f"{message}\n\n"
                    f"[系統提供：{nearby}]\n\n"
                    f"[建議行程參考]\n{itinerary}"
                )
                reply, interest = get_reply_and_interest(augmented_msg, config, now_str)
                return reply, interest or "low_interest"
            return nearby, "low_interest"

    # ── 2. 參觀資訊查詢 ───────────────────────────────────────────
    query_type = _classify_visitor_query(message)
    if query_type:
        reply = _handle_visitor_query(query_type, visitor_info_path, message, now_dt)
        interest = "maybe_interest" if query_type == "itinerary" else "low_interest"
        return reply, interest

    # ── 3. 課程日期查詢（Python 直接篩選回應） ────────────────────
    target_weekday = detect_query_weekday(message, now_dt)
    if target_weekday:
        day_summary, day_detail = load_courses_for_weekday(courses_path, target_weekday)
        if day_detail and not day_detail.startswith("（"):
            reply = f"以下是{target_weekday}的課程：\n\n{day_summary}\n\n{day_detail}"
            return reply, "maybe_interest"
        if day_summary.startswith("（"):
            return day_summary, "low_interest"
        # 篩選失敗 → 交 GPT 處理

    # ── 4. 語意查詢 → GPT ─────────────────────────────────────────
    return get_reply_and_interest(message, config, now_str)
