from pathlib import Path
from playwright.sync_api import sync_playwright

def _route_block_heavy(route):
    rt = route.request.resource_type
    if rt in ("image", "font", "stylesheet", "media"):
        return route.abort()
    return route.continue_()

def open_context(headless: bool, storage_state_path: Path | None):
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=headless)
    if storage_state_path and storage_state_path.exists():
        context = browser.new_context(storage_state=str(storage_state_path))
    else:
        context = browser.new_context()
    context.route("**/*", _route_block_heavy)
    page = context.new_page()
    return p, browser, context, page
