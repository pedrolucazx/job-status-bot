# SPEC — job-status-bot

## Objetivo

Bot que lê a caixa do Gmail (`$GMAIL_ACCOUNT`), identifica
emails de processos seletivos (rejeição / avanço de etapa) e notifica o
candidato via Telegram. O candidato já se candidata e preenche empresa/cargo
manualmente no fluxo do repo `job-search` — este bot só existe pra avisar
"passou ou não, em qual empresa". O próprio usuário atualiza a coluna
Status no Notion depois de ler a notificação.

## Não-objetivos (fora de escopo do MVP — não implementar)

- Escrever no Notion automaticamente (cogitado como fase 2, só se o MVP
  provar valor)
- Detectar "silêncio"/falta de resposta da empresa (não é um sinal que o
  bot pode agir em cima — não há email pra processar)
- Matching do email contra uma page específica do Notion
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
   { "job_related": true, "empresa": "...", "cargo": "...", "resultado": "rejeitado|avancou|indefinido", "proxima_etapa": "..." }
   ```

   Menções incidentais (faixa salarial, benefícios) são ruído, não
   critério de classificação — não construir lógica em cima disso.
5. **Notificação (Telegram, `sendMessage`, sem long-polling)** — só se
   `job_related` e `resultado != "indefinido"`. Uma linha:

   - `❌ Rejeitado — <Empresa> (<Cargo>)`
   - `✅ Avançou de etapa — <Empresa> (<Cargo>)`

   Quando houver avanço, incluir também a próxima etapa explícita no email
   (`proxima_etapa`; string vazia no JSON quando não houver próxima etapa
   clara). Na notificação, mostrar `Próxima etapa: <texto>`, ou `não informada` se o email não deixar isso
   claro. Linha opcional: link pro email original no Gmail, via HTTPS clicável
   compatível com Telegram; em mobile pode redirecionar para o Gmail app e
   mantém fallback web pra conferir o texto completo se quiser. Se `resultado == "indefinido"`
   (ex: só confirmação de recebimento de candidatura, sem veredito):
   **não notifica** — evita ruído.
6. **Marca como processado** — aplica a label `jobbot-processado` no
   email, independente do resultado (mesmo quando ignorado no passo 3),
   pra nunca reprocessar.

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

Nenhuma credencial de Notion é necessária — o bot não escreve lá.

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
- [ ] Nenhum email é reprocessado/notificado duas vezes
- [ ] Nenhuma escrita no Gmail além da label (não marca como lido, não
      arquiva, não deleta)
