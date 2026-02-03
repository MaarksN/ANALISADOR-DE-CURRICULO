import json
import os
import random
import time
import re
from pathlib import Path
from itertools import islice
from datetime import datetime, date
from rich.console import Console
from src.core.db import init_db, seen, upsert_job, DB_PATH
from src.core.export import export_daily, daily_filename
from src.core.browser import open_context
from src.core.sources import enqueue, enqueue_urls, extract_gupy_links
from src.drivers.linkedin_easy_apply import process_job as li_process
from src.drivers.gupy_fast_apply import process_job as gupy_process
from src.modules.notifications.telegram_bot import TelegramBot

console = Console()
telegram = TelegramBot()

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
    items = []
    with QUEUE_PATH.open(encoding="utf-8") as f:
        for ln in islice(f, limit):
            try: items.append(json.loads(ln))
            except: pass
    return items

def main():
    init_db()

    if not PROFILE_PATH.exists():
        console.print("[red]Erro: profile_br.json não encontrado![/red]")
        return

    profile = load_profile()
    headless = os.environ.get("HEADLESS", "1") == "1"

    console.print(f"[bold green]Iniciando Hub de Vagas Runner[/bold green] (Headless={headless})")

    # Enqueue seeds
    console.print("[cyan]Carregando seeds...[/cyan]")
    enqueue_urls("linkedin_search", profile.get("seeds", {}).get("linkedin_search_pages", []))
    enqueue_urls("web_discovery", profile.get("seeds", {}).get("gupy_search_pages", []))

    meta_daily = int(profile["preferencias"]["meta_candidaturas_dia"])
    applied_today = count_applied_today()
    remaining = max(0, meta_daily - applied_today)

    console.print(f"Meta Diária: {meta_daily} | Já aplicados: {applied_today} | Restante: {remaining}")

    if remaining == 0:
        console.print("[yellow]Meta diária atingida. Gerando export e encerrando.[/yellow]")
        export_daily(DB_PATH, Path(daily_filename()))
        return

    windows = 10
    per_window = min(max(1, remaining // windows), 6)

    try:
        p1, b1, c1, page_li = open_context(headless=headless, storage_state_path=STATE_LI)
        p2, b2, c2, page_gupy = open_context(headless=headless, storage_state_path=STATE_GUPY)
        console.print("[green]Browsers iniciados com sucesso.[/green]")
    except Exception as e:
        console.print(f"[red]Erro crítico ao iniciar browsers: {e}[/red]")
        return

    try:
        for w in range(windows):
            if count_applied_today() >= meta_daily: break

            queue = read_queue(limit=400)
            if not queue:
                console.print("[yellow]Fila vazia. Aguardando...[/yellow]")
                time.sleep(5)
                continue

            random.shuffle(queue)
            applied_in_window = 0

            console.print(f"\n--- Janela {w+1}/{windows} ---")

            for item in queue:
                if applied_in_window >= per_window: break
                platform = item.get("platform")
                url = item.get("url")

                if not url: continue
                if seen(platform if platform in ("linkedin", "gupy") else "source", url):
                    continue

                console.print(f"Processando: {platform} - {url[:50]}...")

                try:
                    if platform == "linkedin_search":
                        page_li.goto(url, wait_until="domcontentloaded")
                        page_li.wait_for_timeout(2000)
                        found = set(re.findall(r"https://www\.linkedin\.com/jobs/view/\d+", page_li.content()))
                        console.print(f"  > Encontradas {len(found)} novas vagas.")
                        enqueue_urls("linkedin", list(found))
                        continue

                    if platform == "web_discovery":
                        page_gupy.goto(url, wait_until="domcontentloaded")
                        page_gupy.wait_for_timeout(2000)
                        links = extract_gupy_links(page_gupy.content())
                        console.print(f"  > Encontrados {len(links)} links Gupy.")
                        enqueue_urls("gupy", links)
                        continue

                    if platform == "linkedin":
                        li_process(page_li, url, profile)
                        status = seen("linkedin", url)
                        console.print(f"  > Status: {status}")
                        if status == "applied":
                            applied_in_window += 1
                            telegram.send_notification(f"🚀 *Aplicação Sucesso (LinkedIn)*\n{url}")
                        continue

                    if platform == "gupy":
                        gupy_process(page_gupy, url, profile)
                        status = seen("gupy", url)
                        console.print(f"  > Status: {status}")
                        if status == "applied":
                            applied_in_window += 1
                            telegram.send_notification(f"🚀 *Aplicação Sucesso (Gupy)*\n{url}")
                        continue

                except Exception as e:
                    console.print(f"  [red]Erro no loop: {e}[/red]")

            sleep_s = random.randint(30, 60) # Reduced for demo/testing responsiveness
            console.print(f"[blue]Dormindo por {sleep_s}s...[/blue]")
            time.sleep(sleep_s)
    except KeyboardInterrupt:
        console.print("\n[red]Interrupção manual.[/red]")
    finally:
        export_daily(DB_PATH, Path(daily_filename()))
        try:
            c1.close(); b1.close(); p1.stop()
            c2.close(); b2.close(); p2.stop()
        except:
            pass
        console.print("[bold green]Execução finalizada.[/bold green]")

if __name__ == "__main__":
    main()
