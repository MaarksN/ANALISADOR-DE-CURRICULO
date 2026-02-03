import sqlite3
from pathlib import Path

DB_PATH = Path("data") / "autoapply.db"

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                job_url TEXT NOT NULL,
                title TEXT,
                company TEXT,
                location TEXT,
                score INTEGER DEFAULT 0,
                status TEXT NOT NULL,
                reason TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (platform, job_url)
            );
        """)
        con.commit()

def upsert_job(platform, job_url, status, title=None, company=None, location=None, score=0, reason=None):
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
            INSERT INTO jobs (platform, job_url, title, company, location, score, status, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(platform, job_url) DO UPDATE SET
                title=excluded.title,
                company=excluded.company,
                location=excluded.location,
                score=excluded.score,
                status=excluded.status,
                reason=excluded.reason;
        """, (platform, job_url, title, company, location, score, status, reason))
        con.commit()

def seen(platform, job_url, conn=None):
    if conn:
        cur = conn.execute("SELECT status FROM jobs WHERE platform=? AND job_url=?", (platform, job_url))
        row = cur.fetchone()
        return row[0] if row else None

    with sqlite3.connect(DB_PATH) as con:
        cur = con.execute("SELECT status FROM jobs WHERE platform=? AND job_url=?", (platform, job_url))
        row = cur.fetchone()
        return row[0] if row else None
