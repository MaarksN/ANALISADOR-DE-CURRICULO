import json
import re
from pathlib import Path
from urllib.parse import quote

QUEUE_PATH = Path("data") / "queue.jsonl"
QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)

def enqueue(platform: str, url: str, meta: dict | None = None):
    meta = meta or {}
    with QUEUE_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"platform": platform, "url": url, "meta": meta}, ensure_ascii=False) + "\n")

def linkedin_search_urls(queries: list[str], geo: str = "106057199"):
    urls = []
    for q in queries:
        urls.append(f"https://www.linkedin.com/jobs/search/?keywords={quote(q)}&locationId={geo}")
    return urls

GUPY_RE = re.compile(r"https?://[a-z0-9\-]+\.gupy\.io/[^\s\"'>)]+", re.IGNORECASE)

def extract_gupy_links(text: str) -> list[str]:
    return list(dict.fromkeys(GUPY_RE.findall(text or "")))
