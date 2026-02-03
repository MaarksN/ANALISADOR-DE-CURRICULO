from pathlib import Path
from playwright.sync_api import sync_playwright

AUTH_DIR = Path("data") / "sessions"
AUTH_DIR.mkdir(parents=True, exist_ok=True)

def interactive_login_and_save_state(platform: str, login_url: str, state_path: Path):
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(login_url, wait_until="domcontentloaded")
        print(f" [LOGIN] Faça login manualmente em {platform} e depois volte aqui.")
        input("Quando terminar, pressione ENTER para salvar o state...")
        context.storage_state(path=str(state_path))
        context.close()
        browser.close()
