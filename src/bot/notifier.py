import os
import requests

class Notifier:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')

    def send_message(self, message, entities=None):
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message
        }
        if entities:
            payload["entities"] = entities
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error sending Telegram notification: {e}")
            if entities:
                fallback_payload = {
                    "chat_id": self.chat_id,
                    "text": message
                }
                try:
                    response = requests.post(url, json=fallback_payload)
                    response.raise_for_status()
                except requests.exceptions.RequestException as fallback_error:
                    print(f"Error sending fallback Telegram notification: {fallback_error}")
