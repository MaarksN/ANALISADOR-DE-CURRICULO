from src.core.db import upsert_job
from src.core.scoring import score_text, decide
PLATFORM = "linkedin"

def process_job(page, job_url, profile):
    try:
        page.goto(job_url, wait_until="domcontentloaded", timeout=30000)
    except Exception as e:
        upsert_job(PLATFORM, job_url, "error_load", reason=str(e))
        return

    # Extract info safely
    title = page.locator("h1").first.inner_text(timeout=5000) if page.locator("h1").count() else "Unknown"
    desc_loc = page.locator("div.jobs-description")
    if not desc_loc.count():
        # Fallback selector
        desc_loc = page.locator("article")

    desc = desc_loc.first.inner_text(timeout=3000) if desc_loc.count() else ""

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

    try:
        easy.click()
        page.wait_for_timeout(2000)

        # Robust Modal Handling Loop
        max_steps = 15
        for _ in range(max_steps):
            # Check for success/submit
            submit_btn = page.locator("button:has-text('Enviar candidatura')").first
            if submit_btn.count() and submit_btn.is_visible():
                submit_btn.click()
                page.wait_for_timeout(2000)
                # Verify closure or success message
                if page.locator("text=Sua candidatura foi enviada").count():
                    upsert_job(PLATFORM, job_url, "applied", title=title, score=score)
                    return
                # Assume success if modal closes or changes state
                upsert_job(PLATFORM, job_url, "applied", title=title, score=score)
                return

            # Check for "Review" (Revisar) which often precedes Submit
            review_btn = page.locator("button:has-text('Revisar')").first
            if review_btn.count() and review_btn.is_visible():
                review_btn.click()
                page.wait_for_timeout(1000)
                continue

            # Check for "Next" (Avançar)
            nxt = page.locator("button:has-text('Avançar')").first
            if nxt.count() and nxt.is_visible():
                # Here we could inject logic to fill phone number if error exists
                # For now, just click
                nxt.click()
                page.wait_for_timeout(1000)

                # Check for error blocking progress
                if page.locator(".artdeco-inline-feedback--error").count():
                    upsert_job(PLATFORM, job_url, "needs_manual", title=title, score=score, reason="erro_formulario")
                    return
                continue

            # If no buttons found, maybe we are stuck or done
            break

        upsert_job(PLATFORM, job_url, "needs_manual", title=title, score=score, reason="loop_ou_erro_modal")

    except Exception as e:
        upsert_job(PLATFORM, job_url, "error_applying", title=title, score=score, reason=str(e))
