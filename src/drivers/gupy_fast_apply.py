from src.core.db import upsert_job
from src.core.scoring import score_text, decide
PLATFORM = "gupy"

def process_job(page, job_url, profile):
    page.goto(job_url, wait_until="domcontentloaded")
    title = page.locator("h1").first.inner_text(timeout=3000) if page.locator("h1").count() else ""
    body = page.locator("body").inner_text(timeout=3000)
    score = score_text((title or "") + " " + body, profile["skills"])
    action = decide(score)

    if action == "skip":
        upsert_job(PLATFORM, job_url, "skipped_low_score", title=title, score=score, reason="score_baixo")
        return
    if not page.locator("text=Candidatura Rápida").count():
        upsert_job(PLATFORM, job_url, "needs_manual", title=title, score=score, reason="nao_rapida")
        return
    if action == "needs_manual":
        upsert_job(PLATFORM, job_url, "needs_manual", title=title, score=score, reason="score_medio")
        return

    btn = page.locator("button:has-text('Candidatar')").first
    if not btn.count():
        upsert_job(PLATFORM, job_url, "needs_manual", title=title, score=score, reason="botao_nao_achado")
        return

    btn.click()
    page.wait_for_timeout(1500)
    if page.locator("text=Teste").count() or page.locator("textarea").count():
        upsert_job(PLATFORM, job_url, "needs_manual", title=title, score=score, reason="perguntas_extras")
        return
    upsert_job(PLATFORM, job_url, "applied", title=title, score=score)
