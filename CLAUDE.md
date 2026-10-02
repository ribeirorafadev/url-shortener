# short-url — Índice Mestre (Claude Code)

Encurtador de links com analytics e projeto de portfólio full-stack. Stack: Next.js 16 (App Router) + TypeScript 6 em Node 24, deploy único na Vercel, Prisma 7 + Neon (Postgres) (versões exatas em `architecture.md`), Upstash só para rate limit, Google Safe Browsing como blocklist na criação, Tailwind + shadcn/ui. Testes com Vitest e Postgres em Docker, CI no GitHub Actions, e a publicação só acontece com o CI verde. Sem login: cada link é gerenciado por um token secreto. Domínio em TypeScript puro, isolado do framework. Prazo alvo de 1 semana, contada a partir da aprovação da spec e dos planos, com o MVP em três fatias (uma branch e um PR por fatia). Sessão em andamento: ver `HANDOFF.md`.

@.agents/rules/architecture.md
@.agents/rules/code-style.md
@.agents/rules/security.md
@.agents/rules/spec-workflow.md
@.agents/context/domain.md
@docs/superpowers/PRD.md
@docs/superpowers/ADR.md

## Skills e templates do projeto

Ver `.agents/skills/` e `.agents/templates/`. Skills promovidas a nativas ficam também em `.claude/skills/`.
