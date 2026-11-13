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

## Notificações

Somente avanço explícito de etapa ou reprovação gera aviso. Inscrição recebida,
visualização de currículo e testes automáticos para completar cadastro ficam
silenciosos. O classificador fornece um trecho literal da decisão, conferido
contra o email; isso reduz invenções, mas não elimina erros de interpretação.

Exemplo:
```
✅ Você avançou de etapa

Empresa: Acme
Vaga: Backend

Próxima etapa: entrevista técnica

Trecho do e-mail: Você foi selecionado para entrevista técnica.
```

Um botão “Abrir e-mail no Gmail” busca o Message-ID original por HTTPS, usando
`GMAIL_ACCOUNT` para indicar a conta. A busca `in:anywhere rfc822msgid:...` fica
no texto para copiar no Gmail do celular. Esse operador é documentado pelo
[Google](https://support.google.com/mail/answer/7190). A abertura no app depende
do aparelho; o link pode abrir no navegador. Sem Message-ID há fallback web
pelo ID da mensagem. Novos avisos não usam a antiga página de redirecionamento
nem `GMAIL_IOS_ACCOUNT_ID`. Links de mensagens antigas não são alterados.

O botão usa a [API oficial do Telegram](https://core.telegram.org/bots/api#sendmessage).
Erros de envio deixam o email sem label para tentar depois. Em falhas ambíguas
(timeout após envio ou falha na label), um aviso pode se repetir.

## Notion

Com `NOTION_TOKEN` e `NOTION_DATA_SOURCE_ID` definidos (integração interna do
Notion compartilhada com o banco de candidaturas), cada reprovação ou avanço
também atualiza a linha da candidatura: Status (`Rejeitado`, `Entrevista
cultural` ou `Teste técnico`) e o trecho do e-mail no Feedback. O match exige
empresa e cargo únicos; na dúvida não escreve e o aviso pede atualização
manual. Um status encerrado (`Rejeitado`, `Posição fechada`, `Aceito`...) nunca
muda. Sem as variáveis, o bot só notifica. Detalhes em
`specs/002-atualizar-notion/spec.md`.

## Testes

```sh
python -m unittest discover -s tests/unit -v
```

Testes usam mocks, sem enviar Telegram, chamar Gemini ou alterar Gmail.
A validação de abertura no celular e da classificação com emails reais é manual.
