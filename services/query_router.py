#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
查詢路由：依查詢類型分流。
- 結構化查詢（票價/開放時間/公休/交通/遊園須知/附近館區）→ Python 直接回應
- 課程日期查詢 → Python 篩選課程後直接回應
- 語意/開放式查詢 → chatgpt_service（含興趣度偵測）

資料來源（CSV）：
  data/visitor_tickets.csv  — 票價與適用資格
  data/visitor_hours.csv    — 開放時間
  data/venue_closures.csv   — 館區公休排程
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


def _read_csv(path):
    """讀取 CSV 回傳 list[dict]，缺失欄位填空字串（缺失值處理）。"""
    rows = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                # 缺失值：將 None 統一轉為空字串
                rows.append({k: (v if v is not None else "") for k, v in row.items()})
    except Exception as e:
        logging.error(f"_read_csv({path}) 失敗: {e}")
    return rows


# ── 課表資料有效範圍 ─────────────────────────────────────────────
_COURSE_DATA_YEAR  = 2026
_COURSE_DATA_MONTH = 2   # 目前只有二月課表

_RELATIVE_OFFSETS = {
    "今天": 0, "今日": 0,
    "昨天": -1, "昨日": -1,
    "明天": 1,  "明日": 1,
    "後天": 2,  "前天": -2,
}


def _check_course_date_range(message, now_dt):
    """
    判斷訊息是否包含「超出課表範圍」的特定日期。
    - 相對日期（今天/明天/昨天…）→ 計算實際日期後比對
    - 明確日期（3/8、3月8日）→ 直接比對月份
    - 純星期查詢（週六/週日）→ 不視為特定日期，不觸發
    回傳 (True, '3月') 或 (False, None)
    """
    for kw, offset in _RELATIVE_OFFSETS.items():
        if kw in message:
            target = now_dt + timedelta(days=offset)
            if target.year != _COURSE_DATA_YEAR or target.month != _COURSE_DATA_MONTH:
                return True, f"{target.month}月"
            return False, None

    m = re.search(r'(\d{1,2})[月/](\d{1,2})[日號]?', message)
    if m:
        month = int(m.group(1))
        if month != _COURSE_DATA_MONTH:
            return True, f"{month}月"
        return False, None

    return False, None


# ── 連假順延休館日 (月, 日): [館名, ...] ─────────────────────────
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


# ── CSV 票價查詢 ─────────────────────────────────────────────────

# 關鍵字 → (搜尋欄位, 比對字串)，依序嘗試，命中即篩選
_TICKET_FILTER = [
    (["學生", "學生票"],                   "eligible_group", "學生"),
    (["6-11", "兒童票", "小孩票"],         "eligible_group", "6-11歲兒童"),
    (["老人", "長者", "65歲", "老年"],     "eligible_group", "65歲"),
    (["原住民"],                           "eligible_group", "原住民"),
    (["市民", "臺北市民"],                 "eligible_group", "市民"),
    (["身心障礙", "殘障", "障礙"],         "eligible_group", "身心障礙"),
    (["志工"],                             "eligible_group", "志工"),
    (["低收入"],                           "eligible_group", "低收入"),
    (["數位學生證"],                       "eligible_group", "數位學生證"),
    (["免費", "免票"],                     "ticket_type",    "免票"),
    (["優待"],                             "ticket_type",    "優待票"),
    (["團體"],                             "ticket_type",    "團體票"),
    (["教育中心"],                         "venue",          "教育中心"),
    (["遊客列車", "列車", "車資"],         "venue",          "遊客列車"),
]


_TICKET_URL = "https://www.zoo.gov.taipei/cp.aspx?n=763493FD7ECCAA11&s=F3BC09EC36168CB6"

# 主要票種顯示順序（入園門票摘要用）
_MAIN_TICKET_TYPES = ["普通票", "臺北市民票", "優待票", "團體票"]


def _query_tickets(message, tickets_path):
    """
    從 visitor_tickets.csv 查詢票價。
    - 問教育中心 → 只回教育中心票價
    - 問遊客列車 → 只回遊客列車票價
    - 一般票價查詢 → 回傳入園門票四種主要票種 + 官網連結
    """
    rows = _read_csv(tickets_path)

    # 資料前處理：price → 整數，缺失年齡欄位保留 None
    for row in rows:
        try:
            row["_price"] = int(row["price"])
        except ValueError:
            row["_price"] = -1    # 異常值標記
        row["_age_min"] = float(row["age_min"]) if row["age_min"] else None
        row["_age_max"] = float(row["age_max"]) if row["age_max"] else None

    # ── 教育中心專門查詢 ──────────────────────────────────────────
    if "教育中心" in message:
        filtered = [r for r in rows if r["venue"] == "教育中心"
                    and r["ticket_type"] in ("普通票", "優待票")]
        lines = ["教育中心："]
        for row in filtered:
            lines.append(f"{row['ticket_type']} {row['_price']}元")
        return "\n".join(lines)

    # ── 遊客列車專門查詢 ──────────────────────────────────────────
    if any(kw in message for kw in ["遊客列車", "列車", "車資"]):
        filtered = [r for r in rows if r["venue"] == "遊客列車"
                    and r["ticket_type"] == "車資"]
        lines = ["遊客列車："]
        for row in filtered:
            lines.append(f"車資 {row['_price']}元")
        return "\n".join(lines)

    # ── 一般票價查詢：只顯示入園門票四種主要票種 ─────────────────
    main_rows = [r for r in rows
                 if r["venue"] == "入園" and r["ticket_type"] in _MAIN_TICKET_TYPES]
    # 依 _MAIN_TICKET_TYPES 順序排列
    main_rows.sort(key=lambda r: _MAIN_TICKET_TYPES.index(r["ticket_type"]))

    lines = ["入園門票："]
    for row in main_rows:
        lines.append(f"{row['ticket_type']} {row['_price']}元")

    lines.append("")
    lines.append("免票、優惠票、團體票之資格與規定請至官網查詢：")
    lines.append(_TICKET_URL)
    return "\n".join(lines)


# ── CSV 開放時間查詢 ──────────────────────────────────────────────

def _query_hours(message, hours_path):
    """從 visitor_hours.csv 精確查詢開放時間。"""
    rows = _read_csv(hours_path)

    venue_keywords = {
        "遊客列車": "遊客列車",
        "列車":     "遊客列車",
        "酷cool":   "酷Cool節能屋",
        "節能屋":   "酷Cool節能屋",
        "動物展示": "動物展示",
    }
    target = None
    for kw, venue in venue_keywords.items():
        if kw.lower() in message.lower():
            target = venue
            break

    filtered = [r for r in rows if target in r["venue"]] if target \
        else [r for r in rows if r["venue"] in ("動物園", "動物展示")]

    if not filtered:
        filtered = rows

    lines = []
    for row in filtered:
        line = f"【{row['venue']}】{row['open_time']} - {row['close_time']}"
        if row.get("last_entry"):
            line += f"（停止入園 {row['last_entry']}）"
        if row.get("notes"):
            line += f"\n  備註：{row['notes']}"
        lines.append(line)
    return "\n".join(lines)


# ── CSV 館區公休查詢 ──────────────────────────────────────────────

_CLOSURE_ALIASES = {
    "穿山甲館":  "熱帶雨林室內館（穿山甲館）",
    "大貓熊館":  "大貓熊館",
    "新光特展館": "大貓熊館",
}


def _calc_closed(row, date):
    """依 venue_closures.csv 一筆資料計算 date 是否公休。"""
    if (date.month, date.day) in _HOLIDAY_CLOSURES:
        if row["venue_name"] in _HOLIDAY_CLOSURES[(date.month, date.day)]:
            return True
    day_map = {"週一": 0, "週二": 1, "週三": 2, "週四": 3,
               "週五": 4, "週六": 5, "週日": 6}
    closure_day = day_map.get(row.get("day_of_week", ""), -1)
    wd = date.weekday()
    if row["closure_type"] == "weekly":
        return wd == closure_day
    if row["closure_type"] == "monthly" and wd == closure_day:
        try:
            return (date.day - 1) // 7 + 1 == int(row["week_number"])
        except (ValueError, TypeError):
            pass
    return False


def _query_closure(message, closures_path, now_dt):
    """
    從 venue_closures.csv 查詢館區公休。
    含特定館名 → 即時計算今天是否公休；否則 → 回傳完整公休表。
    """
    rows = _read_csv(closures_path)
    weekday_names = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]
    today_str = f"{now_dt.month}月{now_dt.day}日（{weekday_names[now_dt.weekday()]}）"

    # 偵測訊息中的館名（含別名正規化）
    target_venue = None
    for alias, canonical in _CLOSURE_ALIASES.items():
        if alias in message:
            target_venue = canonical
            break
    if not target_venue:
        for row in rows:
            if row["venue_name"] in message:
                target_venue = row["venue_name"]
                break

    if target_venue:
        target_rows = [r for r in rows if r["venue_name"] == target_venue]
        if not target_rows:
            return f"「{target_venue}」無固定公休日，全年正常開放。"
        row = target_rows[0]
        closed = _calc_closed(row, now_dt)
        special = f"（開放時間 {row['special_hours']}）" if row.get("special_hours") else ""
        week = f"第{row['week_number']}個" if row.get("week_number") else "每"
        status = "今日公休，建議改天再來。" if closed else "今日正常開放！"
        return (f"「{target_venue}」{status}{special}\n"
                f"公休規則：每月{week}{row['day_of_week']}公休"
                if row["closure_type"] == "monthly"
                else f"「{target_venue}」{status}{special}\n"
                     f"公休規則：每{row['day_of_week']}公休")

    # 無特定館名 → 完整公休表
    lines = [f"【館區公休時間表】（今天：{today_str}）"]
    for row in rows:
        closed = _calc_closed(row, now_dt)
        status = "今日公休" if closed else "今日開放"
        special = f"　開放時間 {row['special_hours']}" if row.get("special_hours") else ""
        week = f"第{row['week_number']}個" if row.get("week_number") else "每"
        rule = (f"每月{week}{row['day_of_week']}公休"
                if row["closure_type"] == "monthly"
                else f"每{row['day_of_week']}公休")
        lines.append(f"- {row['venue_name']}：{rule}{special}（{status}）")
    return "\n".join(lines)


# ── visitor_info.txt 章節讀取（交通/遊園須知/建議行程） ──────────

def _load_section(file_path, section_marker):
    """讀取 visitor_info.txt 特定章節（不含標題行）。"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        start = content.find(section_marker)
        if start == -1:
            return "(找不到相關資訊)"
        next_sec = content.find("\n=== ", start + len(section_marker))
        block = content[start:next_sec].strip() if next_sec != -1 else content[start:].strip()
        return "\n".join(block.split("\n")[1:]).strip()
    except Exception as e:
        return f"(讀取失敗: {e})"


# ── 處理各類查詢（統一入口） ─────────────────────────────────────

def _handle_visitor_query(query_type, visitor_info_path, message, now_dt):
    """依查詢類型呼叫對應的 CSV 或 txt 查詢函式。"""
    tickets_path  = _path("data/visitor_tickets.csv")
    hours_path    = _path("data/visitor_hours.csv")
    closures_path = _path("data/venue_closures.csv")

    if query_type == "ticket":
        return _query_tickets(message, tickets_path)
    if query_type == "hours":
        return _query_hours(message, hours_path)
    if query_type == "closure":
        return _query_closure(message, closures_path, now_dt)
    if query_type == "transport":
        return _load_section(visitor_info_path, "=== 交通及停車 ===")
    if query_type == "rules":
        return _load_section(visitor_info_path, "=== 遊園須知 ===")
    if query_type == "itinerary":
        return _load_section(visitor_info_path, "=== 建議行程 ===")
    return "(查詢類型不明)"


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
        # 檢查一：明確日期或相對日期（今天/明天…）超出課表範圍
        out_of_range, out_month = _check_course_date_range(message, now_dt)
        if out_of_range:
            return (
                f"很抱歉，由於系統尚未更新課表，"
                f"{out_month}的課程資訊請至官網查詢喔！\n"
                f"官網：https://www.zoo.gov.taipei"
            ), "low_interest"

        # 檢查二：純星期查詢（週六/週日…），但現在已不在課表月份
        # → 使用者問的「週六」實際上是指當前月份的週六，課表已過期
        if now_dt.year != _COURSE_DATA_YEAR or now_dt.month != _COURSE_DATA_MONTH:
            return (
                f"很抱歉，由於系統尚未更新課表，"
                f"{now_dt.month}月的課程資訊請至官網查詢喔！\n"
                f"官網：https://www.zoo.gov.taipei"
            ), "low_interest"

        day_summary, day_detail = load_courses_for_weekday(courses_path, target_weekday)
        if day_detail and not day_detail.startswith("（"):
            reply = f"以下是{target_weekday}的課程：\n\n{day_summary}\n\n{day_detail}"
            return reply, "maybe_interest"
        if day_summary.startswith("（"):
            return day_summary, "low_interest"
        # 篩選失敗 → 交 GPT 處理

    # ── 4. 語意查詢 → GPT ─────────────────────────────────────────
    return get_reply_and_interest(message, config, now_str)
