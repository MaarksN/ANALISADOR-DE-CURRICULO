from pathlib import Path
from src.core.auth import interactive_login_and_save_state

interactive_login_and_save_state(platform="linkedin", login_url="https://www.linkedin.com/login/pt", state_path=Path("data/sessions/linkedin_state.json"))
interactive_login_and_save_state(platform="gupy", login_url="https://login.gupy.io/", state_path=Path("data/sessions/gupy_state.json"))
