# short-url

Encurtador de links com analytics, sem login: cada link é gerenciado por um token secreto. Projeto de portfólio full-stack em Node.js/TypeScript.

## Status

**Em design. Ainda não há código.** A spec do MVP foi aprovada em 2026-10-08 e a implementação acontece em três fatias, cada uma com uma branch e um PR próprios. A `main` só recebe código com o CI verde. Este README é provisório: a versão completa (diagrama de system design, "como escalaria", como rodar e testar, limitações documentadas) será escrita na fatia 3.

## O que o produto faz (escopo do MVP)

- Encurta uma URL sem login e devolve o link curto, um link de gestão secreto (exibido uma única vez) e um QR code.
- Limite de cliques e data de expiração, ambos opcionais.
- Redirect HTTP 302 que registra o clique (dispositivo, referrer e data/hora).
- Página de gestão com estatísticas por dispositivo, referrer e dia, e a opção de desativar o link.
- Rate limit por IP na criação e no redirecionamento.
- Validação da URL de destino e checagem contra a blocklist do Google Safe Browsing na criação.

## Stack

- Node 24, Next.js 16.3.8 (App Router) e TypeScript 6.0.3
- Prisma 7.10.0 + Neon (Postgres)
- Upstash (Redis), só para o rate limit
- Google Safe Browsing v5
- Tailwind + shadcn/ui
- Vitest, com Postgres em Docker
- GitHub Actions (CI) e Vercel (deploy)

## Destaques de engenharia

- Domínio em TypeScript puro, isolado do framework (AD-004), com a fronteira garantida por lint.
- O limite de cliques é checado e incrementado numa única operação atômica no banco, com um teste de concorrência contra Postgres real previsto na fatia 2.
- O token de gestão é guardado só como hash SHA-256.
- O slug é aleatório, gerado por CSPRNG, nunca sequencial.
- A URL de destino nunca é enviada ao Google: a consulta usa só prefixos de hash.
- O CI não recebe segredos, e a publicação só acontece com o CI verde.

## Documentação

- [PRD](docs/superpowers/PRD.md): problema, público, escopo e critério de "pronto".
- [ADR](docs/superpowers/ADR.md): decisões de arquitetura (AD-001 a AD-004).
- [Spec do MVP](docs/superpowers/specs/2026-10-07-short-url-mvp-design.md): design detalhado.
- [AGENTS.md](AGENTS.md): instruções para agentes de IA. O desenvolvimento é guiado por IA, com o Claude Code e o Antigravity.

## Roadmap

- [ ] Fatia 1, `feat/mvp-1-base`: setup, Docker, CI, Vercel, Neon e domínio com testes.
- [ ] Fatia 2, `feat/mvp-2-create-redirect`: criação com Safe Browsing e rate limit, redirect, testes de concorrência e HTTP.
- [ ] Fatia 3, `feat/mvp-3-manage`: página de gestão e README completo.
