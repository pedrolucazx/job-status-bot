# Notificações precisas

Objetivo: avisar somente avanço explícito ou reprovação, com mensagem legível e acesso ao email certo.
Confirmação de inscrição, visualização, cadastro incompleto e testes automáticos da inscrição são indefinidos.
Exigir evidência literal presente no email para vereditos; resposta inválida fica sem label para retry.
Link HTTPS usa busca rfc822msgid do Message-ID original, com busca copiável no app. Sem Message-ID, fallback para mensagem Gmail.
Não prometer abertura nativa: depende do celular, navegador e conta logada.
Telegram deve confirmar sucesso antes da label; falhas deixam email para retry.
Fora de escopo: Notion, inscrições, deploy e envio real de testes.
Risco médio: classificação probabilística e entrega externa. Evidência não garante interpretação correta.
Pronto: testes unitários offline passando, docs e revisão independente; validação em aparelho real pendente.
