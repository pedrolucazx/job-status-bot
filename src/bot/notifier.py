import os
import requests


class Notifier:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')

    def send_message(self, message, email_url=None):
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "link_preview_options": {"is_disabled": True},
        }
        if email_url:
            payload["reply_markup"] = {"inline_keyboard": [[{
                "text": "Abrir e-mail no Gmail", "url": email_url,
            }]]}
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            if response.json().get('ok') is not True:
                raise ValueError('Telegram did not confirm delivery')
        except (requests.RequestException, ValueError):
            # Do not log the request URL: it contains the bot token.
            raise RuntimeError('Telegram delivery failed; email remains unprocessed') from None
