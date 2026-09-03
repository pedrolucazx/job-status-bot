# job-status-bot

Bot que lê emails de processos seletivos no Gmail, identifica rejeições e avanços de etapa, e notifica via Telegram.

## Setup

1. Clone o repo e instale dependências:
   ```sh
   pip install -r requirements.txt
   ```

2. Crie um `.env` na raiz:
   ```sh
   GMAIL_CLIENT_ID="seu-client-id"
   GMAIL_CLIENT_SECRET="seu-client-secret"
   GMAIL_REFRESH_TOKEN="seu-refresh-token"
   GMAIL_ACCOUNT="sua-conta@gmail.com"
   GEMINI_API_KEY="sua-gemini-api-key"
   TELEGRAM_BOT_TOKEN="seu-telegram-bot-token"
   TELEGRAM_CHAT_ID="seu-telegram-chat-id"
   ```

3. Teste local com um email de exemplo:
   ```sh
   python -m src.bot.main --local-email sample_email.txt
   ```

## Arquitetura

- `src/bot/gmail_client.py` — interface com Gmail API
- `src/bot/llm_handler.py` — extração estruturada via Gemini
- `src/bot/notifier.py` — notificação via Telegram
- `src/bot/main.py` — orquestração principal
- `.github/workflows/poll.yml` — execução via `workflow_dispatch` (cron-job.org a cada 15 min) + `schedule` de hora em hora como safety net
