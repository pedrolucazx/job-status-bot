# Tarefas

- [x] T1 `src/bot/notion_tracker.py`: match estrito, status alvo, não regredir, Feedback idempotente
- [x] T2 Integração em `main.py` (linha do Notion na mensagem; resend não escreve)
- [x] T3 Testes offline (29 novos) e dry-run do match contra o Notion real (7 casos)
- [x] T4 SPEC.md, AGENTS.md, README, .env.example, poll.yml
- [x] T5 Revisão independente. R1: 7 achados (2 altos: "Confidencial" e empate
  entre linhas fechadas escreviam na linha errada). Re-check R2: A1/A2/A4/A5/A7
  ok; achou N1 (alto, introduzido pela correção do A1: sufixo "TOTVS - Analista"
  levava à linha errada), N2 (cache gerava item {} no 2º PATCH), N3 (mentions
  não graváveis), N4 (palavras genéricas de cargo). Todos corrigidos com teste.
  Sondagem em massa contra as 429 linhas reais (886 vereditos sintéticos):
  849 linha certa, 31 manual, 0 em outra empresa; 4 vão para a recandidatura
  aberta da mesma empresa e vaga (comportamento documentado).
- [ ] T6 Validar que a API aceita reenviar Feedback com links mailto (PATCH
  sem mudança de conteúdo numa linha real, com aval do usuário)
- [ ] T7 Secrets no GitHub, push, reativar workflow, validação real
