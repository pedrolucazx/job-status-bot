# 002: Atualizar o Notion a partir do veredito

Objetivo: quando o bot avisa uma reprovação ou um avanço, a candidatura no
tracker do Notion (data source "Aplicações" do repo job-search) muda de
Status sozinha, com o trecho do e-mail registrado no Feedback. Hoje o
usuário faz isso à mão depois de ler o Telegram, e quase nunca faz: o
funil do job-search mostrou avanço subestimado porque as etapas nunca
foram registradas.

Risco: **médio**. Escrita externa no tracker real; um match errado muda a
candidatura errada.

## Comportamento

1. Só roda para `resultado` `rejeitado` ou `avancou` (os mesmos que notificam)
   e só se `NOTION_TOKEN` e `NOTION_DATA_SOURCE_ID` existirem. Sem eles, o bot
   funciona como antes.
2. **Match**: compara empresa e cargo do veredito com as linhas do data source,
   normalizados (sem acento, caixa, pontuação e palavras genéricas como
   "grupo", "ltda", "s.a."). Empresa precisa bater (uma contém a outra);
   entre as linhas da mesma empresa, ganha a de maior sobreposição de
   palavras do cargo. Empate ou nenhuma linha: **não escreve** e o aviso diz
   "Notion: candidatura não encontrada, atualize à mão".
3. **Status**: `rejeitado` → `Rejeitado`; `avancou` → `Teste técnico` se a
   próxima etapa fala de teste/desafio/técnica/case, senão
   `Entrevista cultural`.
4. **Nunca regride**: linha já em `Rejeitado`, `Posição fechada`, `Aceito`,
   `Desisti` ou `Referência para colega` não muda; um avanço não rebaixa
   `Teste técnico` para `Entrevista cultural`.
5. **Feedback**: acrescenta `AAAA-MM-DD (bot): <evidência>` ao texto existente,
   sem apagar nada. Idempotente: se a evidência já está lá, não duplica.
6. Falha do Notion não bloqueia o Telegram nem a label: o aviso diz
   "Notion: falhou, atualize à mão". O token nunca vai para log.
7. A mensagem do Telegram ganha uma linha com o que aconteceu no Notion.

## Decisões do review independente (R1)

- Palavras que não identificam empresa (`Confidencial`, `via`, `Consultoria RH`,
  `Empresa não identificada`) não contam no match: um veredito "Confidencial"
  não escreve em nenhuma das 6 linhas "Confidencial (via …)".
- Empresas diferentes com palavra em comum ("UOL" / "Compass UOL"): só a chave
  exata decide, nunca o cargo. Match parcial de empresa ("GX2" ~ "Vem ser GX2")
  exige palavra em comum no cargo.
- Linha encerrada não recebe nada, nem Feedback.
- Feedback existente é reenviado como foi lido (links, negrito, equações).
- Marcador `(bot, e-mail <id>)` torna o retry idempotente mesmo quando o
  Gemini recorta outro trecho.
- Linhas lidas uma vez por execução; um retry em 429 respeitando `Retry-After`.
- Limitação aceita: a nota leva a data do processamento, não a do e-mail, e o
  backlog é drenado do mais recente para o mais antigo.

## Fora de escopo

- Criar linha nova no Notion (candidatura não registrada é assunto do
  `/confirm` no job-search).
- Marcar etapas no `outcome.md` local do job-search (o bot roda no GitHub,
  não tem acesso ao disco do usuário).

## Critérios de aceite

1. Testes unitários offline do match (empresa com/sem "Grupo", empate,
   sem match), do mapeamento de status, da regra de não regredir e do
   Feedback idempotente.
2. Sem `NOTION_TOKEN`, comportamento idêntico ao de antes (testes de 001
   passam).
3. Rodado contra o Notion real com um veredito de teste, atualiza a linha
   certa (validação manual, com o usuário).
