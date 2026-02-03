import os
import requests

class TelegramBot:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.api_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    def send_notification(self, message):
        """Sends a message to the configured Telegram chat."""
        if not self.token or not self.chat_id:
            return False

        try:
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            response = requests.post(self.api_url, json=payload, timeout=5)
            return response.status_code == 200
        except:
            return False
