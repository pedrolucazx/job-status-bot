# Quickstart: Job Status Bot

**Date**: 2026-07-17

**Prerequisite**: [plan.md](./plan.md)

## Objective

This guide provides the steps to run a single, local validation of the bot's core logic. It demonstrates the end-to-end flow from reading an email to sending a notification, without requiring a full deployment or live email monitoring.

---

## 1. Prerequisites

- **Python 3.11+** installed.
- **Project dependencies** installed (`pip install -r requirements.txt`).
- **Credentials configured** as environment variables.

Create a `.env` file in the root of the project:

```sh
# .env
GMAIL_CLIENT_ID="your-client-id"
GMAIL_CLIENT_SECRET="your-client-secret"
GMAIL_REFRESH_TOKEN="your-refresh-token"
GEMINI_API_KEY="your-gemini-api-key"
TELEGRAM_BOT_TOKEN="your-telegram-bot-token"
TELEGRAM_CHAT_ID="your-telegram-chat-id"
```

---

## 2. Validation Steps

### Step 2.1: Prepare a Sample Email

Create a file named `sample_email.txt` and paste the raw content of an email you want to test.

**Example `sample_email.txt` (Rejection):**

```txt
From: Gupy <noreply@gupy.io>
Subject: Feedback sobre sua candidatura para Desenvolvedor(a) Backend

Olá,

Agradecemos seu interesse na vaga de Desenvolvedor(a) Backend na Acme Corp.
Analisamos seu perfil e, no momento, optamos por seguir com outros candidatos.

Desejamos sucesso em sua busca.
```

### Step 2.2: Run the Local Test Script

The main script will be designed to accept a local file path for testing purposes, bypassing the live Gmail API call for fetching emails.

Execute the main script from the root directory, pointing it to your sample email:

```sh
python -m src.bot.main --local-email sample_email.txt
```

### Step 2.3: Verify the Outcome

1.  **Check Terminal Output**: The script should log its progress, including:
    - "Running in local mode with email file: sample_email.txt"
    - "Email identified as job-related."
    - "Extracted info: {'empresa': 'Acme Corp', 'resultado': 'rejeitado', ...}"
    - "Sending notification to Telegram..."
    - "Simulating applying 'jobbot-processado' label."

2.  **Check Telegram**: A notification should appear in the configured `TELEGRAM_CHAT_ID`.
    - Expected message: `❌ Rejeitado — Acme Corp (Desenvolvedor(a) Backend)`

---

## Expected Outcome

A successful run of these steps validates the entire logical flow of the application:
1.  Correctly parsing a local email file.
2.  Sending the content to the LLM for interpretation.
3.  Receiving and understanding the structured JSON response.
4.  Formatting the notification text correctly.
5.  Successfully calling the Telegram API to send the message.

This quickstart test confirms that all core components are working together as expected before deploying the bot to run on a schedule with live data.
