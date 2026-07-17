# Telegram API Contract: `sendMessage`

**Date**: 2026-07-17

**Prerequisite**: [data-model.md](./../data-model.md)

## Objective

This document specifies the contract for the `sendMessage` endpoint of the Telegram Bot API, as it will be used by the Job Status Bot.

---

## Endpoint

`POST https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/sendMessage`

## Request Body

The bot will send a JSON payload with the following structure.

- **Content-Type**: `application/json`

| Field      | Type   | Required | Description                                  | Example Value      |
|------------|--------|----------|----------------------------------------------|--------------------|
| `chat_id`  | string | Yes      | The unique identifier for the target chat.   | `"123456789"`      |
| `text`     | string | Yes      | The UTF-8 text of the message to be sent.    | `"✅ Avançou..."` |

## Example `requests` Call

```python
import requests

bot_token = "..."
chat_id = "..."
message_text = "❌ Rejeitado — Acme Inc (Software Engineer)"

url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
payload = {
    "chat_id": chat_id,
    "text": message_text
}

try:
    response = requests.post(url, json=payload)
    response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
except requests.exceptions.RequestException as e:
    print(f"Error sending Telegram notification: {e}")

```

## Success Response

A successful request will return a `200 OK` status code with a JSON body containing details of the sent message. The bot does not need to parse this response; a `200` status is sufficient to confirm success.

## Error Response

The Telegram API will return a non-200 status code (e.g., 400, 403, 404) with a JSON body describing the error. The bot's error handling should log these errors for debugging.
