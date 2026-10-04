# short-url — instruções para agentes de IA

Encurtador de links com analytics e projeto de portfólio full-stack. Stack: Next.js 16 (App Router) + TypeScript 6 em Node 24, deploy único na Vercel, Prisma 7 + Neon (Postgres), Upstash só para rate limit, Google Safe Browsing como blocklist na criação, Tailwind + shadcn/ui. Testes com Vitest e Postgres em Docker, CI no GitHub Actions, e a publicação só acontece com o CI verde. Sem login: cada link é gerenciado por um token secreto. Domínio em TypeScript puro, isolado do framework (AD-004). MVP em três fatias, uma branch e um PR por fatia. **Sessão em andamento: ver `HANDOFF.md`.**

Este arquivo é lido nativamente pelo Antigravity e importado pelo `CLAUDE.md` no Claude Code. A fonte de verdade é a pasta `.agents/`.

## Glossário

- **Link**: registro que associa um slug a uma URL de destino. Tem limite de cliques e data de expiração, ambos opcionais.
- **Slug**: identificador público e curto do link, a parte que vai na URL (`/aB3xZ9k`).
- **URL de destino**: para onde o visitante é redirecionado. Só `http`/`https`.
- **Token de gestão**: segredo longo e aleatório, gerado na criação e exibido uma única vez. Quem o possui pode ver as estatísticas e desativar aquele link (`/manage/[token]`). Nunca é exposto publicamente.
- **Evento de clique**: registro de um redirecionamento bem-sucedido, com dispositivo, referrer e data/hora.
- **Link ativo / inativo**: é inativo se foi desativado, se passou da data de expiração ou se atingiu o limite de cliques. Um link inativo não redireciona.

## Como as regras são carregadas

- **Núcleo, sempre carregado:** este `AGENTS.md`, `.agents/rules/architecture-layers.md`, `.agents/rules/security-core.md` e `.agents/rules/code-style.md` (`trigger: always_on` no Antigravity; links em `.claude/rules/` no Claude Code).
- **Sob demanda:** os demais arquivos de `.agents/rules/` (`trigger: model_decision`), os de `.agents/context/`, o PRD e o ADR. **Antes de mexer em algo, leia os arquivos indicados no índice abaixo.**
- Trechos marcados **[→ spec]** são detalhe de implementação (SQL, tipos, pseudocódigo, nomes de método): valem como rascunho e serão movidos para a spec do MVP.
- Cada arquivo tem no máximo 12 mil caracteres. Arquivo novo em `.agents/rules/` só ganha link em `.claude/rules/` se fizer parte do núcleo; arquivo novo sob demanda entra no índice.

## Índice: o que ler antes de mexer em cada coisa

| Ao mexer em… | Leia antes |
|---|---|
| validação da URL de destino (R1 a R7) | `.agents/context/url-validation.md` · `.agents/rules/security-blocklist.md` |
| slug, limite de cliques, expiração | `.agents/context/link-lifecycle.md` |
| criação de link (formulário, Server Action, card, token, QR) | `.agents/context/link-creation.md` · `.agents/context/link-lifecycle.md` · `.agents/context/error-map.md` · `.agents/rules/security-token.md` · `.agents/rules/security-rate-limit.md` |
| redirect (`src/app/[slug]/`), bots de preview, `HEAD` | `.agents/context/redirect.md` · `.agents/context/data-model.md` · `.agents/rules/security-rate-limit.md` |
| página de gestão (`/manage/[token]`), estatísticas, desativar | `.agents/context/manage-page.md` · `.agents/context/data-model.md` · `.agents/rules/security-token.md` |
| mensagens de erro | `.agents/context/error-map.md` |
| banco, schema, Prisma, conexão, migrations | `.agents/context/data-model.md` · `.agents/rules/architecture-persistence.md` |
| Google Safe Browsing | `.agents/rules/security-blocklist.md` · `.agents/context/url-validation.md` (R7) |
| testes, Docker, CI, deploy, publicação | `.agents/rules/architecture-testing-ci.md` |
| dependências, versões, `package.json`, `.npmrc` | `.agents/rules/architecture-stack.md` |
| `npm run dev`, arquivos `.env*`, `next.config.ts` | `.agents/rules/architecture-local-dev.md` · `.agents/rules/architecture-testing-ci.md` (Postgres em Docker) |
| escopo do produto, o que está fora do MVP | `docs/superpowers/PRD.md` |
| spec, plano, ADR ou índice de specs | `.agents/rules/spec-workflow.md` · `docs/superpowers/PRD.md` · `docs/superpowers/ADR.md` |
| commits, branches, PR | `.agents/rules/code-style.md` (núcleo) |
