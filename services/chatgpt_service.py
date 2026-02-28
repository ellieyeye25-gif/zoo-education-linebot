#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ChatGPT 服務：讀取 data 當 context、呼叫 OpenAI、解析興趣度
"""

import os
import re
import csv
from collections import OrderedDict
from datetime import datetime, timezone, timedelta

# 專案根目錄（依此找 data/）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TW_TZ = timezone(timedelta(hours=8))
WEEKDAY_ZH = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]


def _path(name):
    """專案內 data 路徑"""
    return os.path.join(PROJECT_ROOT, name)


def detect_query_weekday(message, now=None):
    """
    從使用者訊息偵測詢問的目標星期。
    回傳中文星期字串（如「週四」）或 None（未指定特定日期）。
    """
    if now is None:
        now = datetime.now(TW_TZ)
    wd = now.weekday()  # 0=週一 … 6=週日

    # 相對日期
    relative = {
        "今天": wd, "今日": wd,
        "昨天": (wd - 1) % 7, "昨日": (wd - 1) % 7,
        "明天": (wd + 1) % 7, "明日": (wd + 1) % 7,
        "後天": (wd + 2) % 7,
        "前天": (wd - 2) % 7,
    }
    for kw, idx in relative.items():
        if kw in message:
            return WEEKDAY_ZH[idx]

    # 明確星期（週X / 星期X）
    for i, zh in enumerate(WEEKDAY_ZH):
        alt = zh.replace("週", "星期")
        if zh in message or alt in message:
            return zh

    # 具體日期（如 2/26、2月26日、26號）→ 計算星期
    m = re.search(r'(\d{1,2})[月/](\d{1,2})[日號]?', message)
    if m:
        try:
            month, day = int(m.group(1)), int(m.group(2))
            year = now.year
            target = datetime(year, month, day, tzinfo=TW_TZ)
            return WEEKDAY_ZH[target.weekday()]
        except ValueError:
            pass

    return None


def matches_weekday(weekday_field, target):
    """
    判斷課程 CSV 的 weekday 欄位是否涵蓋 target（如「週四」）。
    支援格式：每週X、第N個週X、每週X至週Y、每週X、週Y（逗號/頓號列舉）
    """
    if not weekday_field or not target:
        return False
    if target in weekday_field:
        return True
    # 範圍：每週二至週六
    m = re.search(r'週([一二三四五六日])至週([一二三四五六日])', weekday_field)
    if m:
        try:
            start = WEEKDAY_ZH.index("週" + m.group(1))
            end = WEEKDAY_ZH.index("週" + m.group(2))
            target_idx = WEEKDAY_ZH.index(target) if target in WEEKDAY_ZH else -1
            if 0 <= start <= target_idx <= end:
                return True
        except ValueError:
            pass
    return False


def load_courses_for_weekday(csv_path, target_weekday):
    """
    從整份 CSV 篩選包含 target_weekday 的課程，
    回傳 (summary_text, detail_text)：
      summary_text：一行一類別的簡短總覽
      detail_text：已格式化的詳細課程區塊，可直接給 GPT 輸出
    """
    import logging
    # 分類收集：{cat: [(topic, weekday, time, location, cert, hours), ...]}
    buckets = OrderedDict()
    row_count = 0
    match_count = 0
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                row_count += 1
                cat = row.get("category", "").strip()
                topic = row.get("topic", "").strip()
                if not cat or not topic or cat.startswith("D_"):
                    continue
                weekday_val = row.get("weekday", "").strip()
                matched = matches_weekday(weekday_val, target_weekday)
                if matched:
                    match_count += 1
                if not matched:
                    continue
                entry = (
                    topic,
                    weekday_val,
                    row.get("time", "").strip(),
                    row.get("location", "").strip(),
                    row.get("cert", "").strip(),
                    row.get("env_hours", "").strip(),
                )
                if cat not in buckets:
                    buckets[cat] = []
                buckets[cat].append(entry)
    except Exception as e:
        logging.error(f"load_courses_for_weekday 讀檔失敗: {e}")
        return f"(讀取失敗: {e})", ""

    logging.info(f"[filter] target={target_weekday} rows={row_count} matches={match_count} buckets={list(buckets.keys())}")

    if not buckets:
        return f"（{target_weekday} 無課程資料）", ""

    # 摘要
    summary_lines = []
    for cat, entries in buckets.items():
        seen_topics = list(dict.fromkeys(t for t, *_ in entries))
        if cat == "定時定點課程":
            no_cert = [t for t, *r in entries if r[3] != "是"]
            with_cert = [t for t, *r in entries if r[3] == "是"]
            no_cert_unique = list(dict.fromkeys(no_cert))
            with_cert_unique = list(dict.fromkeys(with_cert))
            if no_cert_unique:
                summary_lines.append(f"定時定點課程：{'、'.join(no_cert_unique)}")
            if with_cert_unique:
                summary_lines.append(f"有環境教育時數之定時定點課程：{'、'.join(with_cert_unique)}")
        else:
            summary_lines.append(f"{cat}：{'、'.join(seen_topics)}")

    # 詳細
    detail_lines = []
    for cat, entries in buckets.items():
        for topic, weekday, time_, location, cert, hours in entries:
            header = "【有環境教育時數之定時定點課程】" if (cat == "定時定點課程" and cert == "是") else f"【{cat}】"
            block = [header, f"主題：{topic}", f"星期：{weekday}", f"時間：{time_}", f"地點：{location}"]
            if cert == "是" and hours:
                block.append(f"時數：{hours}")
            detail_lines.append("\n".join(block))

    has_cert = any(cert == "是" for entries in buckets.values() for _, _, _, _, cert, _ in entries)
    if has_cert:
        detail_lines.append("如有需要環境教育時數，可考慮以上有標註時數的課程，歡迎進一步詢問。")

    return "\n".join(summary_lines), "\n\n".join(detail_lines)


def load_courses_overview(csv_path):
    """
    從整份 CSV 抽取所有唯一 (類別, 主題, 認證) 組合，
    產生已格式化的課程總覽文字，定時定點課程按有無認證分組。
    """
    cat_topics = OrderedDict()
    seen = set()
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                cat = row.get("category", "").strip()
                topic = row.get("topic", "").strip()
                cert = row.get("cert", "").strip()
                if not cat or not topic or cat.startswith("D_"):
                    continue
                key = (cat, topic)
                if key not in seen:
                    seen.add(key)
                    if cat not in cat_topics:
                        cat_topics[cat] = []
                    cat_topics[cat].append((topic, cert))

        lines = ["【課程總覽（所有類別與主題）】"]
        for cat, items in cat_topics.items():
            if cat == "定時定點課程":
                no_cert = [t for t, c in items if c != "是"]
                with_cert = [t for t, c in items if c == "是"]
                if no_cert:
                    lines.append("")
                    lines.append("定時定點課程：")
                    for i, t in enumerate(no_cert, 1):
                        lines.append(f"{i}.{t}")
                if with_cert:
                    lines.append("")
                    lines.append("有環境教育時數之定時定點課程：")
                    for i, t in enumerate(with_cert, 1):
                        lines.append(f"{i}.{t}")
            else:
                topics = [t for t, c in items]
                lines.append("")
                if len(topics) == 1:
                    lines.append(f"{cat}：{topics[0]}")
                else:
                    lines.append(f"{cat}：")
                    for i, t in enumerate(topics, 1):
                        lines.append(f"{i}.{t}")

        lines.append("")
        lines.append("請告訴我您對以上課程有興趣的部分，我可以提供更詳細的資訊。")
        return "\n".join(lines)
    except Exception as e:
        return f"(讀取課程總覽失敗: {e})"


def load_courses_context(csv_path):
    """
    從整份 CSV，以唯一 (類別, 主題) 為單位，
    整合該主題的所有時間表，產生緊湊的詳細資料供 GPT 查詢用。
    """
    groups = OrderedDict()
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                cat = row.get("category", "").strip()
                topic = row.get("topic", "").strip()
                if not cat or not topic or cat.startswith("D_"):
                    continue
                key = (cat, topic)
                cert = row.get("cert", "").strip()
                env_hours = row.get("env_hours", "").strip()
                weekday = row.get("weekday", "").strip()
                time_ = row.get("time", "").strip()
                location = row.get("location", "").strip()
                schedule = f"{weekday} {time_} 地點:{location}"
                if key not in groups:
                    groups[key] = {
                        "cat": cat, "topic": topic,
                        "cert": cert, "env_hours": env_hours,
                        "schedules": []
                    }
                if schedule not in groups[key]["schedules"]:
                    groups[key]["schedules"].append(schedule)

        out = []
        for key, d in groups.items():
            schedules_str = " / ".join(d["schedules"])
            out.append(
                f"類別:{d['cat']} | 主題:{d['topic']} | 認證:{d['cert']} | 時數:{d['env_hours']} | 時間表:{schedules_str}"
            )
        return "\n".join(out) if out else "(無課程資料)"
    except Exception as e:
        return f"(讀取課程失敗: {e})"


def load_zoo_areas_context(csv_path):
    """讀取館區 CSV，組成簡短 context。"""
    out = []
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            r = csv.DictReader(f)
            for row in r:
                name = row.get("name", "").strip()
                if not name or name.startswith("E_"):
                    continue
                cat = row.get("category", "")
                url = row.get("url", "")
                out.append(f"{name}（{cat}）" + (f" {url}" if url else ""))
        return "\n".join(out) if out else "(無館區資料)"
    except Exception as e:
        return f"(讀取館區失敗: {e})"


def load_env_edu_notes(txt_path):
    """讀取環教時數說明。"""
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        return f"(讀取環教說明失敗: {e})"


def load_visitor_info(txt_path):
    """讀取參觀資訊（票價、開放時間、交通、遊園須知、建議行程等）。"""
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        return f"(讀取參觀資訊失敗: {e})"


def build_system_prompt(courses_overview, courses_text, areas_text, env_notes_text,
                        now_str="", day_summary="", day_detail="", target_weekday="",
                        visitor_info_text=""):
    """組裝給 ChatGPT 的 system prompt。"""
    time_section = f"\n[現在時間]\n{now_str}\n" if now_str else ""

    # 當天課程已由 Python 預先篩選，直接放進 prompt
    if day_detail:
        day_section = f"""
[已篩選課程：{target_weekday}]
以下是 {target_weekday} 的課程，已完整篩選，直接照格式輸出即可：

摘要：
{day_summary}

詳細：
{day_detail}
"""
    elif target_weekday:
        # 預篩選失敗或無課程，仍把目標星期告知 GPT，讓 GPT 從課程詳細資料自行篩選
        day_section = f"\n[查詢目標] 使用者詢問 {target_weekday} 的課程。\n"
    else:
        day_section = ""

    visitor_section = f"\n[參觀資訊]\n{visitor_info_text}\n" if visitor_info_text else ""

    return f"""你是台北市立動物園的課程小幫手，用友善的繁體中文回覆。
{time_section}{day_section}
以下是補充參考資料（僅供查詢，不得原文輸出到回覆中）：

[課程總覽]
{courses_overview}

[館區資料]
{areas_text}

[環境教育說明]
{env_notes_text}
{visitor_section}

---
回覆規則（務必嚴格遵守）：

1. 第一行必須是興趣度標註，格式：[興趣度: high_interest] 或 [興趣度: maybe_interest] 或 [興趣度: low_interest]
   - high_interest：明確想報名、問細節
   - maybe_interest：開放探索、問有哪些課
   - low_interest：與課程無關的一般問題
   第二行起才是給使用者看的內容，不要輸出興趣度那行。

2. 全文必須使用繁體中文，嚴禁任何簡體中文字。

3. 禁止主動推薦特定課程。若課程有環境教育時數認證，只可說明「若有需要環境教育時數認證，可考慮此課程」。

4. 回覆格式依使用者問題區分：

   ── A. 未指定日期或星期（如「有哪些課」「二月課程」）──
   直接輸出 [課程總覽] 的內容，原文照呈現，不要更改格式或自行增減。

   ── B. 有指定日期或星期，且 [已篩選課程] 存在 ──
   先輸出「摘要」的內容，再空一行，輸出「詳細」的內容，原文照輸出，不要修改。

   ── C. 有 [查詢目標] 但無 [已篩選課程] ──
   從 [查詢目標] 取得目標星期，再從 [課程詳細資料] 的時間表欄位中找出符合該星期的課程，
   依 B 的格式輸出。若真的完全找不到才回應「該日無課程資料」。

   ── D. 使用者詢問特定課程細節 ──
   先輸出當天課程的簡短總覽（一行一類別，類別：主題1、主題2 格式），
   再依以下格式輸出詳細資訊，每筆課程之間空一行：

   非定時定點課程 → 用：
   【類別名稱】
   主題：課程主題
   星期：xxx
   時間：xx:xx-xx:xx
   地點：xxx

   定時定點課程（認證:否）→ 用：
   【定時定點課程】
   主題：課程主題
   星期：xxx
   時間：xx:xx-xx:xx
   地點：xxx

   定時定點課程（認證:是）→ 用：
   【有環境教育時數之定時定點課程】
   主題：課程主題
   星期：xxx
   時間：xx:xx-xx:xx
   地點：xxx
   時數：x.x

   最後若有認證課程，結尾加一行：「如有需要環境教育時數，可考慮以上有標註時數的課程，歡迎進一步詢問。」"""


def parse_interest_from_reply(reply):
    """從回覆文字中解析興趣度標籤。"""
    if not reply:
        return None
    m = re.search(r"\[興趣度\s*:\s*(\w+)\]", reply, re.IGNORECASE)
    if m:
        label = m.group(1).lower()
        if label in ("high_interest", "maybe_interest", "low_interest"):
            return label
    return None


def strip_interest_line_from_reply(reply):
    """把回覆中的 [興趣度: xxx] 行拿掉。"""
    if not reply:
        return reply
    lines = reply.strip().split("\n")
    out = [l for l in lines if not re.search(r"\[興趣度\s*:\s*\w+\]", l, re.IGNORECASE)]
    return "\n".join(out).strip() or "（無法產生回覆，請再試一次。）"


def get_reply_and_interest(user_message, config, now_str=""):
    """
    讀取 data、呼叫 ChatGPT、回傳 (回覆文字, 興趣度標籤)。
    now_str：台灣當前時間字串，例如「2026年2月27日（週四）14:30」
    """
    api_key = getattr(config, "OPENAI_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return "尚未設定 OPENAI_API_KEY，無法使用智慧回覆。", None

    courses_path = _path(getattr(config, "COURSES_CSV_PATH", "data/courses-February.csv"))
    areas_path = _path(getattr(config, "ZOO_AREAS_CSV_PATH", "data/zoo_areas.csv"))
    notes_path = _path(getattr(config, "ENV_EDU_NOTES_PATH", "data/環教時數說明.txt"))
    visitor_path = _path("data/visitor_info.txt")

    courses_overview = load_courses_overview(courses_path)
    areas_text = load_zoo_areas_context(areas_path)
    env_notes_text = load_env_edu_notes(notes_path)
    visitor_info_text = load_visitor_info(visitor_path)

    # Python 預先偵測目標星期並篩選課程，避免讓 GPT 自行過濾
    import logging
    now_dt = datetime.now(TW_TZ)
    target_weekday = detect_query_weekday(user_message, now_dt)
    day_summary, day_detail = ("", "")
    if target_weekday:
        try:
            day_summary, day_detail = load_courses_for_weekday(courses_path, target_weekday)
        except Exception as e:
            logging.warning(f"load_courses_for_weekday 失敗: {e}")
            day_summary, day_detail = ("", "")
    logging.info(f"[weekday] target={target_weekday} | summary_len={len(day_summary)} | detail_len={len(day_detail)}")

    courses_text = load_courses_context(courses_path)
    system_prompt = build_system_prompt(
        courses_overview, courses_text, areas_text, env_notes_text,
        now_str, day_summary, day_detail, target_weekday,
        visitor_info_text,
    )
    model = getattr(config, "OPENAI_MODEL", "gpt-3.5-turbo")
    max_tokens = getattr(config, "GPT_MAX_TOKENS", 1200)
    temperature = getattr(config, "GPT_TEMPERATURE", 0.7)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        reply = (resp.choices[0].message.content or "").strip() if resp.choices else ""
    except Exception as e:
        return f"回覆時發生錯誤，請稍後再試。（{str(e)[:80]}）", None

    interest = parse_interest_from_reply(reply)
    reply_clean = strip_interest_line_from_reply(reply)
    if len(reply_clean) > 4500:
        reply_clean = reply_clean[:4500] + "\n\n（回覆過長已截斷，請縮小問題範圍再問。）"
    return reply_clean, interest
