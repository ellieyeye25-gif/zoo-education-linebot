#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ChatGPT 服務：讀取 data 當 context、呼叫 OpenAI、解析興趣度
"""

import os
import re
import csv
from collections import OrderedDict

# 專案根目錄（依此找 data/）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _path(name):
    """專案內 data 路徑"""
    return os.path.join(PROJECT_ROOT, name)


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


def build_system_prompt(courses_overview, courses_text, areas_text, env_notes_text):
    """組裝給 ChatGPT 的 system prompt。"""
    return f"""你是台北市立動物園的環境教育小幫手，用友善的繁體中文回覆。

以下是你可以參考的資料（僅供查詢，不得原文輸出到回覆中）：

[課程總覽]
{courses_overview}

[課程詳細資料]（每筆格式：類別 | 主題 | 認證 | 時數 | 時間表）
{courses_text}

[館區資料]
{areas_text}

[環境教育說明]
{env_notes_text}

---
回覆規則（務必嚴格遵守）：

1. 第一行必須是興趣度標註，格式：[興趣度: high_interest] 或 [興趣度: maybe_interest] 或 [興趣度: low_interest]
   - high_interest：明確想報名、問細節
   - maybe_interest：開放探索、問有哪些課
   - low_interest：與課程無關的一般問題
   第二行起才是給使用者看的內容，不要輸出興趣度那行。

2. 全文必須使用繁體中文，嚴禁任何簡體中文字。

3. 絕對禁止將 [課程詳細資料] 的原始格式（類別:xxx | 主題:xxx | ...）直接輸出給使用者。

4. 禁止主動推薦特定課程。若課程有環境教育時數認證，只可說明「若有需要環境教育時數認證，可考慮此課程」，不得說「建議您參加」或「歡迎前往參加」。

5. 回覆格式依使用者問題區分：

   ── A. 未指定日期或星期（如「有哪些課」「二月課程」）──
   直接輸出 [課程總覽] 的內容，原文照呈現，不要更改格式或自行增減。

   ── B. 有指定日期或星期（如「週六」「2月27日」）──
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


def get_reply_and_interest(user_message, config):
    """
    讀取 data、呼叫 ChatGPT、回傳 (回覆文字, 興趣度標籤)。
    """
    api_key = getattr(config, "OPENAI_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return "尚未設定 OPENAI_API_KEY，無法使用智慧回覆。", None

    courses_path = _path(getattr(config, "COURSES_CSV_PATH", "data/courses-February.csv"))
    areas_path = _path(getattr(config, "ZOO_AREAS_CSV_PATH", "data/zoo_areas.csv"))
    notes_path = _path(getattr(config, "ENV_EDU_NOTES_PATH", "data/環教時數說明.txt"))

    courses_overview = load_courses_overview(courses_path)
    courses_text = load_courses_context(courses_path)
    areas_text = load_zoo_areas_context(areas_path)
    env_notes_text = load_env_edu_notes(notes_path)

    system_prompt = build_system_prompt(courses_overview, courses_text, areas_text, env_notes_text)
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
