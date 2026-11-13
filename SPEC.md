# SPEC — job-status-bot

## Objetivo

Bot que lê a caixa do Gmail (`$GMAIL_ACCOUNT`), identifica
emails de processos seletivos (rejeição / avanço de etapa) e notifica o
candidato via Telegram. O candidato já se candidata e preenche empresa/cargo
manualmente no fluxo do repo `job-search` — este bot só existe pra avisar
"passou ou não, em qual empresa". Desde a spec 002 (`specs/002-atualizar-notion/`)
o bot também move a candidatura no tracker do Notion quando há veredito
(Status + trecho no Feedback), com match estrito e sem nunca regredir.

## Não-objetivos (fora de escopo do MVP — não implementar)

- Detectar "silêncio"/falta de resposta da empresa (não é um sinal que o
  bot pode agir em cima — não há email pra processar)
- Criar linha nova no Notion (candidatura não registrada é do `/confirm`
  no job-search) ou escrever no Notion sem match único
- Confirmação via botão do Telegram antes de qualquer ação — não há ação
  a confirmar no MVP, é notificação pura, unidirecional

## Fluxo

1. **Trigger**: GitHub Actions `schedule:` (cron) a cada 10–15 min. Zero
   servidor, zero custo.
2. **Gmail**: busca mensagens novas sem a label `jobbot-processado`. O
   Gmail é a única fonte de estado — sem banco de dados externo. Escopo
   OAuth: `gmail.modify` (necessário só pra aplicar labels; o bot nunca
   apaga, arquiva ou marca como lido).
3. **Filtro barato (sem IA)** — qualquer um dos dois gatilhos dispara a
   análise por IA:
   - domínio do remetente é um ATS conhecido (lista abaixo, editável)
   - OU assunto contém palavra-chave de processo seletivo ("processo
     seletivo", "sua candidatura", "feedback", "retorno sobre a vaga")

   Se nenhum dos dois bate: ignora, aplica a label mesmo assim (marca como
   visto, evita reprocessar no próximo ciclo), **não** chama a IA.
4. **Interpretação (Gemini API, free tier)** — envia o corpo do email,
   pede extração estruturada:

   ```json
   { "job_related": true, "empresa": "...", "cargo": "...", "resultado": "rejeitado|avancou|indefinido", "proxima_etapa": "...", "evidencia": "trecho literal" }
   ```

   Menções incidentais (faixa salarial, benefícios) são ruído, não
   critério de classificação — não construir lógica em cima disso.
5. **Notificação** — somente `job_related=true` e `resultado` igual a
   `avancou` ou `rejeitado`, com `evidencia` literal do assunto/corpo.
   Confirmações de inscrição, visualizações, lembretes e etapas automáticas
   para completar inscrição são `indefinido`, sem aviso. Convite para teste
   exige seleção explícita para aquela etapa. Evidência ausente/inventada
   invalida a resposta: não notifica e deixa sem label para nova tentativa.
   A IA ainda pode interpretar incorretamente um trecho real.

   Mensagem: status, empresa, vaga, próxima etapa (somente avanço), trecho
   original e botão HTTPS para buscar `in:anywhere rfc822msgid:<Message-ID>`
   no Gmail. A busca também fica no texto para copiar no app. Sem Message-ID,
   usa o ID da mensagem como fallback web. Não há redirecionamento automático
   para iOS nem garantia de abertura nativa. Conta logada deve corresponder
   a `GMAIL_ACCOUNT`.
6. **Marca como processado** — aplica `jobbot-processado` após confirmação
   de sucesso do Telegram, ou quando a classificação válida dispensa aviso.
   Falhas de entrega deixam sem label. Um timeout após envio ou falha ao
   aplicar label pode causar duplicidade no retry; não há garantia exactly-once.

## Domínios ATS conhecidos

Config editável (`config/ats_domains.txt` ou equivalente), não
hard-coded no meio da lógica:

```
gupy.io
mail.gupy.io
inhire.app
mail.inhire.app
kenoby.com
greenhouse.io
lever.co
hire.lever.co
myworkday.com
smartrecruiters.com
comeet.com
solides.com.br
vagas.com.br
catho.com.br
bamboohr.com
recruitee.com
personio.com
personio.de
icims.com
```

## Credenciais necessárias (env vars / GitHub Secrets)

- `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`
- `GEMINI_API_KEY`
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

- `NOTION_TOKEN`, `NOTION_DATA_SOURCE_ID` (opcionais: sem eles o bot só
  notifica, como no MVP)

## Stack

Python 3.x. `google-api-python-client` + `google-auth` (Gmail),
`google-genai` (Gemini), `requests` (Telegram — API simples o bastante
pra não precisar de lib dedicada).

## Deploy

GitHub Actions, `.github/workflows/poll.yml`,
`schedule: cron: '*/10 * * * *'` (ajustar frequência real considerando
rate limits do Gmail e do Gemini free tier).

## Critérios de aceite (MVP)

- [ ] Roda via GitHub Actions cron sem erro por pelo menos 24h
- [ ] Um email de rejeição real (Gupy ou Inhire) gera notificação correta
      no Telegram
- [ ] Um email de avanço de etapa gera notificação correta
- [ ] Um email irrelevante (newsletter, spam) não gera notificação
- [ ] Emails rotulados não são reprocessados; falhas ambíguas podem duplicar aviso
- [ ] Nenhuma escrita no Gmail além da label (não marca como lido, não
      arquiva, não deleta)
