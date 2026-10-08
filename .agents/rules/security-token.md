---
trigger: model_decision
description: "Token de gestão: hash SHA-256 no banco, formato base64url e os canais de vazamento (Referer, logs da Vercel, histórico). Ler ao mexer na geração do token, na página de gestão, em headers ou em logs."
---
# Segurança — token de gestão

## Armazenamento e formato (decidido na sessão de design)
- **Token de gestão guardado só como hash SHA-256** (coluna `BYTEA` de 32 bytes com `UNIQUE`). O token tem 32 bytes de CSPRNG (256 bits), então um hash rápido basta: inverter o hash é inviável, e a busca continua indexada. Hash lento (argon2/bcrypt) foi descartado porque protege segredos de baixa entropia, não é indexável (obrigaria o padrão seletor+verificador) e custa de 100 a 250 ms de CPU por acesso sem ganho real. Plaintext foi descartado porque um dump do banco daria controle de todos os links. Hash via Web Crypto (`crypto.subtle.digest`), sem dependência nova. Implementação na spec do MVP, §5.3 (formato e hash) e §6.1 (coluna).
- **Formato e exibição do token:** base64url sem padding (43 caracteres), exibido uma única vez no card de resultado da criação. Nunca vai para `localStorage`, cookie, log ou redirect (ver `.agents/context/link-creation.md`, "Token de gestão").

## Vazamentos do token que o hash não cobre (decidido em 2026-09-29)
O hash só protege o token **no banco**. O token **continua no path** (`/manage/[token]`), e cada canal de vazamento tem um tratamento explícito:
- **Header `Referer`: mitigado.** A página de gestão responde com `Referrer-Policy: no-referrer`, e o navegador nunca envia a URL com o token a outro site. Ela também leva `X-Robots-Tag: noindex` (para não ser indexada se o link vazar) e `Cache-Control: no-store`.
- **Logs de requisição da Vercel: risco aceito.** O log de runtime mostra o path acessado, com o token. Só o dono do projeto vê esse log, e ele já controla o banco, então o log não dá a ninguém um acesso novo. O plano Hobby guarda os logs por **1 hora** (documentação de Runtime Logs da Vercel, verificada em 2026-09-29).
- **Histórico do navegador: risco residual aceito.** *Mitigado em parte (2026-09-28):* a criação exibe o token num card, sem redirecionar para `/manage/[token]`, então ele só entra no histórico quando o usuário abre o link de gestão. O que sobra só importa em computador compartilhado.
- Descartados:
  - **token no fragmento** (`/manage#<token>`, que o navegador não envia ao servidor, RFC 3986, §3.5): fecharia o log, mas obriga a renderizar o dashboard no navegador (JavaScript lê o `#` e busca os dados por `POST`), e não resolve o histórico;
  - **campo "cole seu token"** sem token na URL: fecha os três canais, mas o usuário perde o link clicável e precisa guardar 43 caracteres.
