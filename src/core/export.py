import csv
import sqlite3
from pathlib import Path
from datetime import datetime

def export_daily(db_path: Path, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as con:
        rows = con.execute("""
            SELECT platform, job_url, title, company, location, score, status, reason, created_at
            FROM jobs
            ORDER BY created_at DESC
        """).fetchall()
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["platform", "job_url", "title", "company", "location", "score", "status", "reason", "created_at"])
        w.writerows(rows)

def daily_filename():
    return datetime.now().strftime("out/daily_export_%Y-%m-%d.csv")
