import json
import os
import random
import time
import re
from pathlib import Path
from datetime import datetime, date
from src.core.db import init_db, seen, upsert_job, DB_PATH
from src.core.export import export_daily, daily_filename
from src.core.browser import open_context
from src.core.sources import enqueue, extract_gupy_links
from src.drivers.linkedin_easy_apply import process_job as li_process
from src.drivers.gupy_fast_apply import process_job as gupy_process

PROFILE_PATH = Path("profile_br.json")
QUEUE_PATH = Path("data") / "queue.jsonl"
STATE_LI = Path("data") / "sessions" / "linkedin_state.json"
STATE_GUPY = Path("data") / "sessions" / "gupy_state.json"

def load_profile(): return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))

def count_applied_today():
    import sqlite3
    today = date.today().isoformat()
    with sqlite3.connect(DB_PATH) as con:
        row = con.execute("SELECT COUNT(*) FROM jobs WHERE status='applied' AND substr(created_at, 1, 10)=?", (today,)).fetchone()
    return row[0] if row else 0

def read_queue(limit=200):
    if not QUEUE_PATH.exists(): return []
    lines = QUEUE_PATH.read_text(encoding="utf-8").splitlines()
    items = []
    for ln in lines[:limit]:
        try: items.append(json.loads(ln))
        except: pass
    return items

def main():
    init_db()
    profile = load_profile()
    headless = os.environ.get("HEADLESS", "1") == "1"

    for url in profile.get("seeds", {}).get("linkedin_search_pages", []):
        enqueue("linkedin_search", url)
    for url in profile.get("seeds", {}).get("gupy_search_pages", []):
        enqueue("web_discovery", url)

    meta_daily = int(profile["preferencias"]["meta_candidaturas_dia"])
    applied_today = count_applied_today()
    remaining = max(0, meta_daily - applied_today)

    if remaining == 0:
        export_daily(DB_PATH, Path(daily_filename()))
        return

    windows = 10
    per_window = min(max(1, remaining // windows), 6)

    p1, b1, c1, page_li = open_context(headless=headless, storage_state_path=STATE_LI)
    p2, b2, c2, page_gupy = open_context(headless=headless, storage_state_path=STATE_GUPY)

    try:
        for w in range(windows):
            if count_applied_today() >= meta_daily: break
            queue = read_queue(limit=400)
            random.shuffle(queue)
            applied_in_window = 0
            for item in queue:
                if applied_in_window >= per_window: break
                platform = item.get("platform")
                url = item.get("url")
                if not url: continue
                if seen(platform if platform in ("linkedin", "gupy") else "source", url): continue

                if platform == "linkedin_search":
                    page_li.goto(url, wait_until="domcontentloaded")
                    page_li.wait_for_timeout(1200)
                    for m in set(re.findall(r"https://www\.linkedin\.com/jobs/view/\d+", page_li.content())):
                        enqueue("linkedin", m)
                    continue

                if platform == "web_discovery":
                    page_gupy.goto(url, wait_until="domcontentloaded")
                    page_gupy.wait_for_timeout(1200)
                    links = extract_gupy_links(page_gupy.content())
                    for lk in links: enqueue("gupy", lk)
                    continue

                if platform == "linkedin":
                    li_process(page_li, url, profile)
                    if seen("linkedin", url) == "applied": applied_in_window += 1
                    continue

                if platform == "gupy":
                    gupy_process(page_gupy, url, profile)
                    if seen("gupy", url) == "applied": applied_in_window += 1
                    continue
            sleep_s = random.randint(1800, 7200)
            time.sleep(sleep_s)
    finally:
        export_daily(DB_PATH, Path(daily_filename()))
        c1.close(); b1.close(); p1.stop()
        c2.close(); b2.close(); p2.stop()

if __name__ == "__main__":
    main()
