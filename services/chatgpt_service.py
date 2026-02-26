#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ChatGPT 服務：讀取 data 當 context、呼叫 OpenAI、解析興趣度
"""

import os
import re
import csv

# 專案根目錄（依此找 data/）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _path(name):
    """專案內 data 路徑"""
    return os.path.join(PROJECT_ROOT, name)


def load_courses_context(csv_path, max_rows=120):
    """讀取課程 CSV，組成一串簡短 context（前 max_rows 筆）。"""
    out = []
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            r = csv.DictReader(f)
            cols = r.fieldnames or []
            for i, row in enumerate(r):
                if i >= max_rows:
                    break
                # 略過程式用欄位列（例如 D_Category 開頭）
                if row.get("category", "").strip().startswith("D_"):
                    continue
                parts = []
                if row.get("category"):
                    parts.append(f"類別:{row['category']}")
                if row.get("topic"):
                    parts.append(f"主題:{row['topic']}")
                if row.get("weekday"):
                    parts.append(f"星期:{row['weekday']}")
                if row.get("time"):
                    parts.append(f"時間:{row['time']}")
                if row.get("location"):
                    parts.append(f"地點:{row['location']}")
                if row.get("cert"):
                    parts.append(f"認證:{row['cert']}")
                if row.get("env_hours"):
                    parts.append(f"時數:{row['env_hours']}")
                if parts:
                    out.append(" | ".join(parts))
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


def build_system_prompt(courses_text, areas_text, env_notes_text):
    """組裝給 ChatGPT 的 system prompt。"""
    return f"""你是台北市立動物園的環境教育小幫手，用友善、簡潔的繁體中文回覆。

【課程資料（部分）】
{courses_text}

【館區】
{areas_text}

【環境教育說明】
{env_notes_text}

請依上述資料回答使用者。回覆時：
1. 第一行必須是興趣度標註，格式為：[興趣度: high_interest] 或 [興趣度: maybe_interest] 或 [興趣度: low_interest]
   - high_interest：明確想參加課程、報名、問細節
   - maybe_interest：開放式詢問、探索（如「有什麼活動」）
   - low_interest：一般動物園資訊（門票、開放時間、與課程無關）
2. 第二行開始才是要給使用者看的回覆內容，不要重複「興趣度」那行。"""


def parse_interest_from_reply(reply):
    """從回覆文字中解析興趣度標籤。回傳 high_interest / maybe_interest / low_interest 或 None。"""
    if not reply:
        return None
    m = re.search(r"\[興趣度\s*:\s*(\w+)\]", reply, re.IGNORECASE)
    if m:
        label = m.group(1).lower()
        if label in ("high_interest", "maybe_interest", "low_interest"):
            return label
    return None


def strip_interest_line_from_reply(reply):
    """把回覆中第一行的 [興趣度: xxx] 拿掉，只留要給使用者看的內容。"""
    if not reply:
        return reply
    lines = reply.strip().split("\n")
    out = []
    for line in lines:
        if re.search(r"\[興趣度\s*:\s*\w+\]", line, re.IGNORECASE):
            continue
        out.append(line)
    return "\n".join(out).strip() or "（無法產生回覆，請再試一次。）"


def get_reply_and_interest(user_message, config):
    """
    讀取 data、呼叫 ChatGPT、回傳 (回覆文字, 興趣度標籤)。
    config 需有：OPENAI_API_KEY, OPENAI_MODEL, COURSES_CSV_PATH, ZOO_AREAS_CSV_PATH, ENV_EDU_NOTES_PATH
    """
    api_key = getattr(config, "OPENAI_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return "尚未設定 OPENAI_API_KEY，無法使用智慧回覆。", None

    courses_path = _path(getattr(config, "COURSES_CSV_PATH", "data/courses-February.csv"))
    areas_path = _path(getattr(config, "ZOO_AREAS_CSV_PATH", "data/zoo_areas.csv"))
    notes_path = _path(getattr(config, "ENV_EDU_NOTES_PATH", "data/環教時數說明.txt"))

    courses_text = load_courses_context(courses_path)
    areas_text = load_zoo_areas_context(areas_path)
    env_notes_text = load_env_edu_notes(notes_path)

    system_prompt = build_system_prompt(courses_text, areas_text, env_notes_text)
    model = getattr(config, "OPENAI_MODEL", "gpt-3.5-turbo")
    max_tokens = getattr(config, "GPT_MAX_TOKENS", 500)
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
    # LINE 單則文字上限約 5000 字
    if len(reply_clean) > 4500:
        reply_clean = reply_clean[:4500] + "\n\n（回覆過長已截斷，請縮小問題範圍再問。）"
    return reply_clean, interest
