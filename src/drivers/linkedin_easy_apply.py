from src.core.db import upsert_job
from src.core.scoring import score_text, decide
PLATFORM = "linkedin"

def process_job(page, job_url, profile):
    page.goto(job_url, wait_until="domcontentloaded")
    title = page.locator("h1").first.inner_text(timeout=3000) if page.locator("h1").count() else ""
    desc = page.locator("div.jobs-description").first.inner_text(timeout=3000) if page.locator("div.jobs-description").count() else ""
    score = score_text((title or "") + " " + desc, profile["skills"])
    action = decide(score)

    if action == "skip":
        upsert_job(PLATFORM, job_url, "skipped_low_score", title=title, score=score, reason="score_baixo")
        return

    easy = page.locator("button:has-text('Candidatura simplificada')").first
    if not easy.count():
        upsert_job(PLATFORM, job_url, "skipped_external_apply", title=title, score=score, reason="externo")
        return

    if action == "needs_manual":
        upsert_job(PLATFORM, job_url, "needs_manual", title=title, score=score, reason="score_medio")
        return

    easy.click()
    page.wait_for_timeout(1200)
    for _ in range(10):
        if page.locator("button:has-text('Enviar candidatura')").count():
            page.locator("button:has-text('Enviar candidatura')").click()
            upsert_job(PLATFORM, job_url, "applied", title=title, score=score)
            return
        nxt = page.locator("button:has-text('Avançar')").first
        if nxt.count():
            nxt.click()
            page.wait_for_timeout(900)
            continue
        upsert_job(PLATFORM, job_url, "needs_manual", title=title, score=score, reason="loop_ou_erro_modal")
        return
