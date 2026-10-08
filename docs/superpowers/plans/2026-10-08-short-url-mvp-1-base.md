# short-url MVP, fatia 1 (base) — Plano de Implementação

> **Para executores agenticos:** execute pelo ciclo de `.agents/rules/execution-workflow.md` (teste do Opus → executor Sonnet → QA do Gemini quando a D6d mandar → revisão D7 → pausa com o Rafael), com `superpowers:subagent-driven-development` e os ajustes de lá. As etapas usam checkbox (`- [ ]`) para rastreamento.

**Objetivo:** deixar o projeto de pé e publicado: scaffolding do Next com Tailwind e shadcn/ui, npm endurecido, lint com o AD-004, `next.config.ts` com travas e headers, Prisma com a migration `init`, Postgres em Docker, Vitest, CI, Vercel e Neon, e o **domínio completo (spec §5) com testes unitários**. Termina com a home provisória no ar e a primeira PR, feita em conjunto.
**Arquitetura:** três camadas (`app` → `domain` ← `data`/`infra`, AD-004). Nesta fatia, o domínio nasce inteiro em TypeScript puro, testado com fakes em memória. As camadas de dados e de entrada só ganham o esqueleto: schema, migration e configuração.
**Stack Tecnológica:** Node 24, Next.js 16.3.8, React 19, TypeScript 6.0.3, Prisma 7.10.0 + `@prisma/adapter-pg`, Postgres (Docker local, Neon em produção), Vitest 5, ESLint 9 + `eslint-config-next@16.3.8`, Tailwind 4 + shadcn/ui, GitHub Actions, Vercel.
**Spec:** `docs/superpowers/specs/2026-10-07-short-url-mvp-design.md`
**Branch de Trabalho:** `feat/mvp-1-base`

## Como ler este plano

- **O como está na spec e não é repetido aqui** (`spec-workflow.md` §8: cada detalhe num lugar só). Cada tarefa cita a seção, e o executor lê a seção inteira. O plano traz o que a spec não traz: a ordem, quem faz o quê, os **casos de teste com valores concretos**, os comandos de verificação e o critério de pronto.
- **Quem faz:**
  - **Opus (setup):** tarefas que mexem em `package.json`, lockfile, `.npmrc`, `.gitignore`, configs do Vitest, `tests/`, `__fakes__/`, `.github/` ou nos painéis. A trava do executor barra esses caminhos (D4). Essas tarefas não têm executor; a verificação é por comando, e a pausa com o Rafael acontece do mesmo jeito.
  - **Opus testa → executor implementa:** o resto. O Opus escreve o teste com os casos listados, vê falhar e delega.
- **Os casos listados são o mínimo.** O Opus pode acrescentar casos de borda que a spec implique, nunca tirar.
- **Itens "(conferir na tarefa)" da spec** viram um passo explícito de verificação, marcado com 🔎.

## Ciclo padrão de uma tarefa "Opus testa → executor implementa"

Cada tarefa informa os parâmetros: arquivos de teste, arquivos de produção, comando do teste, QA (sim ou não) e mensagem de commit.

1. **Teste (D1):** o Opus lê a tarefa, a seção da spec e os arquivos de contexto, e escreve o teste com os casos da tarefa.
2. **Vermelho:** roda o comando do teste e confere que falha **pelo motivo esperado** (indicado na tarefa). Falha por outro motivo (erro de sintaxe no teste, import errado) se corrige antes de delegar.
3. **Delegar (D2, D3):** `Agent` com `subagent_type: "executor"`, com este pedido:
   ```
   Tarefa <N> do plano docs/superpowers/plans/2026-10-08-short-url-mvp-1-base.md (<nome>).
   Leia: a tarefa <N> inteira no plano; a spec, <seções>; <arquivos de contexto>.
   Testes vermelhos (não edite): <caminhos>.
   Crie ou altere só: <arquivos de produção>.
   Verificação: <comando do teste>; npm test; npm run lint; npm run typecheck.
   Relatório no formato do seu agent.md.
   ```
   Correção depois de uma devolução: `SendMessage` para o mesmo agente.
4. **Verde de verdade (D7, item 1):** o Opus roda ele mesmo o comando do teste, `npm test`, `npm run lint` e `npm run typecheck` (os que já existirem). Mais `git diff --stat` para conferir que nenhum teste mudou.
5. **QA (D6, D6d):** só quando a tarefa marca "QA: sim". Roteiro em `execution-workflow.md`, D6d: `npm run dev` com `USE_LOCAL_FAKES=true` e o Postgres do Docker; `sh .agents/agents/qa-explorer/worktree-fingerprint.sh` antes e depois; `agy --agent qa-explorer --model gemini-3.8-flash-high -p "<URL base, o que a tarefa entregou, áreas>"`. Defeito achado → teste vermelho do Opus → volta ao passo 3.
6. **Revisão (D7):** os 9 itens, com "n/a" e motivo quando não se aplica. Veredito `APROVADO` ou `DEVOLVIDO` (com `arquivo:linha`, item e o que corrigir). Na 3ª devolução, para e leva ao Rafael.
7. **Pausa com o Rafael:** o teste escrito, o que o executor entregou, as devoluções e o porquê, o QA, o placar do checklist e a mensagem de commit. Explicar como a peça se encaixa nas decisões. Atualizar o ledger `.superpowers/sdd/mvp-1-base/progress.md`.
8. **Commit só quando o Rafael mandar**, com a mensagem da tarefa e o trailer do Claude. Push só com autorização na mensagem.

Nas tarefas, "Step 3–7: ciclo padrão" (ou "Step 4–7") significa os passos restantes do ciclo acima, da delegação ao commit.

## Global Constraints

Valores copiados da spec e das regras; valem para todas as tarefas.

- Node `24.x` (`engines`); `"private": true`; versões **exatas**, sempre instaladas com `npm install <pacote>@<versão>` (spec §9.1).
- `next@16.3.8`, `eslint-config-next@16.3.8`, `@next/env@16.3.8`, `prisma@7.10.0`, `@prisma/client@7.10.0`, `@prisma/adapter-pg@7.10.0`, `typescript@6.0.3`, `qrcode@1.5.4`; React na 19.x que o `min-release-age` aceitar (o `next@16.3.8` declara `^19.0.0`); **ESLint na 9.x** (o `eslint-plugin-import@2.32` e o `eslint-plugin-react@7.37` não aceitam o 10; verificado em 2026-10-08).
- `.npmrc`: `save-exact=true`, `min-release-age=1`, `strict-allow-scripts=true`; **nunca** token de registry (spec §9.2, `security-core.md`).
- **Dependências recusadas:** Recharts, `tldts`, `isbot`, `dotenv`, Jest, Playwright como dependência (`architecture-stack.md`, spec §15).
- O domínio só usa globais nativos (`crypto.getRandomValues`, `crypto.subtle`, `TextEncoder`, `URL`, `Intl`, `btoa`) e não importa pacote nenhum (AD-004, S2).
- Arquivos em kebab-case; identificadores em inglês; textos da interface em pt-BR.
- Slug: `/^[A-Za-z0-9]{7}$/`; token: `/^[A-Za-z0-9_-]{43}$/`; hash SHA-256 sobre os 43 caracteres ASCII (spec §5.3).
- Limite de cliques de 1 a 1.000.000; URL com no máximo 2048 caracteres em `url.href`; expiração até 5 anos; fuso `America/Sao_Paulo` (spec §5.1, §5.4).
- Precedência do inativo: desativado → expirado → esgotado (spec §5.1).
- Headers globais (CSP "Without Nonces", `nosniff`, `DENY`, `strict-origin-when-cross-origin`) e os da gestão (`no-referrer`, `noindex`, `no-store`), nesta ordem (spec §9.4).
- Testes nunca leem `.env*` e recusam banco fora de `127.0.0.1`/`localhost` (spec §9.8).
- CI sem segredos, ações por SHA completo, `permissions: contents: read`, job chamado `ci` (spec §9.10).
- Commits: Conventional Commits, tipo e escopo em inglês, descrição em pt-BR; commit e push só com autorização do Rafael.

## Review Focus

Entradas que a spec implica e nenhum caso da spec exercita, das mais prováveis de morder para as menos. Cada uma tem o teste na tarefa dona.

1. **Host com ponto final** (`http://localhost./`, `https://<host próprio>./x`): o parser mantém o ponto (`hostname` = `"localhost."`, medido no Node 24), e o algoritmo da §5.5 deixaria passar a R4 e a R3. Esperado: `'not-public'` e `'own-domain'`. → Tarefa 11.
2. **Relógio da função atrás do `created_at` do banco perto da meia-noite** (o `created_at` vem do `now()` do banco, B-1): `todayInSaoPaulo(createdAt)` pode cair um dia depois de `toDay`, e a janela do gráfico ficaria invertida. Esperado: `fromDay` nunca passa de `toDay`. → Tarefa 17.
3. **`expiresAt` exatamente igual a `now`:** esperado expirado, no domínio (`<=`) e no SQL da fatia 2 (`expires_at > $2`). → Tarefas 7 e 16.
4. **`User-Agent` e `Referer` vazios (`''`, não ausentes):** esperado `UNKNOWN` e `null`, não `DESKTOP` nem host vazio. → Tarefa 13.
5. **Lote inteiro rejeitado no gerador de slug** (todos os bytes ≥ 248): esperado continuar sorteando e devolver 7 caracteres válidos, nunca um slug curto. → Tarefa 8.

Além desses, a Tarefa 2 corrige dois furos da lista branca do ESLint (S2) achados ao montar os casos: o `'!../*'` da §9.3 deixaria o domínio importar `../data/...`, e os testes do domínio importam `vitest`. Ver "Ajustes na spec".

## Ajustes na spec feitos por este plano

Detalhes de implementação novos (`spec-workflow.md` §8). **Aprovados pelo Rafael e aplicados na spec em 2026-10-08**, junto com a coluna "Tarefa" da §16. A tabela fica aqui como histórico do porquê.

| § | Ajuste | Motivo |
|---|---|---|
| 4.1 | Acrescentar `components.json`, `postcss.config.mjs`, `src/lib/utils.ts` (o `cn` do shadcn/ui) e os testes de configuração na raiz (`next.config.test.ts`, `eslint.config.test.ts`) | Arquivos que o shadcn/ui e o Tailwind 4 exigem; testes das travas |
| 5.5 | R3 e R4 comparam o `hostname` **sem um ponto final** (`localhost.` → `localhost`) | Review Focus 1 |
| 5.9 | `dailyWindow`: `fromDay = min(toDay, max(...))`; `byDevice` sem zeros, em ordem decrescente (empate: `MOBILE`, `DESKTOP`, `TABLET`, `UNKNOWN`); `topReferrers` com empate por host em ordem alfabética e `null` por último | Review Focus 2; saída determinística |
| 5.6 | `classifyDevice` trata UA vazio como ausente; `extractReferrerHost` devolve `null` para host vazio depois de tirar o `www.` | Review Focus 4 |
| 9.1 | `eslint@9.x` explícito nas devDependencies; dependências do shadcn/ui registradas; scripts `db:migrate:test` (migrations no `shorturl_test`) | O executor não pode prefixar variável no comando (trava D4) |
| 9.3 | Lista branca do domínio: só `./*` e `@/domain/*` nos arquivos da raiz de `src/domain/`, mais `../*` dentro de subpastas (`__fakes__`), sem nunca sair de `src/domain/`; testes do domínio (`*.test.ts`) fora da regra; `@prisma/*`, `pg` e `generated/` relativos também barrados fora de `src/data/`; `src/data/generated/**` ignorado pelo lint. Casos de prova permanentes em `eslint.config.test.ts` | Furos da S2 achados ao montar os casos |
| 9.8 | Projeto `unit` inclui `*.test.ts` da raiz e `src/**/*.test.tsx`; o `globalSetup` do HTTP recusa subir se a porta 3000 já responder | Testes das configs; evitar testar contra o `npm run dev` com falsos |

## Rastreabilidade (coluna "Tarefa" da spec §16)

| Requisito | Tarefas |
|---|---|
| RF02 (regra) | 7, 14 |
| RF03 (regra) | 10, 14 |
| RF04 (regra) | 11, 14 |
| RF07, RF09 (domínio) | 16 |
| RF10 (domínio) | 17, 18 |
| RF12 (regra) | 15 |
| RF14 (travas) | 3 |
| RNF03 | 3 |
| RNF04 | 6, 9 |
| RNF05 (schema) | 6 |
| RNF06 | 2 |
| RNF07 | 19, 20, 21 |
| RNF08 | 1 |
| RNF10 | 6, 20 |

## Pré-requisitos (antes da Tarefa 5)

- **Docker instalado**, com a decisão `sudo` × *rootless* tomada com o Rafael (pendência combinada para depois da revisão dos planos).
- **Projeto no Neon criado** pelo Rafael: a versão major do Postgres (14 a 18) e a região, que serão as mesmas do `compose.yml`, do CI, da função da Vercel e do Upstash (spec §9.11).
- **Antes da Tarefa 20:** banco Redis no Upstash, na mesma região, e API key do Google restrita à Safe Browsing API (`security-blocklist.md`). O build da Vercel falha sem as três chaves (trava RC4 do `next.config.ts`).

---

### Task 1: Branch, npm endurecido e scaffolding do Next

**Quem:** Opus (setup). **QA:** não (só scaffolding; a home real é a Tarefa 4).

**Contexto (ler antes):** `architecture-stack.md`, `architecture-local-dev.md`, spec §4.1, §9.1, §9.2.

**Files:**
- Create: `.npmrc`, `package.json`, `package-lock.json`, `tsconfig.json`, `postcss.config.mjs`, `components.json`, `src/app/layout.tsx`, `src/app/page.tsx`, `src/app/globals.css`, `src/lib/utils.ts`, `src/components/ui/{button,input,label,card,alert}.tsx`
- Modify: `docs/superpowers/specs/README.md` (status `Em andamento`)

**Interfaces:**
- Produces: `npm run dev`, `npm run build`, `npm run start`; alias `@/*` → `src/*`; `cn()` em `@/lib/utils`.

- [ ] **Step 1:** `git switch -c feat/mvp-1-base` a partir da `main` atualizada; criar o ledger `.superpowers/sdd/mvp-1-base/progress.md`.
- [ ] **Step 2:** escrever o `.npmrc` da §9.2 **antes** de qualquer instalação. Conferir que não há linha com `_authToken`.
- [ ] **Step 3:** `package.json` à mão, com `name: "short-url"`, `private`, `engines` e os scripts `dev`, `build` e `start` da §9.1. **Ainda sem `postinstall`**: o `prisma generate` falha sem o schema, que só nasce na Tarefa 6.
- [ ] **Step 4:** para cada pacote sem versão fixada na spec, rodar `npm view <pacote> time --json` e escolher a versão mais nova publicada há mais de 1 dia, compatível com os peers. Anotar a escolha no ledger e na seção "Versões escolhidas" no fim deste plano. Pacotes: `react`, `react-dom` (19.x), `pg`, `@vercel/functions`, `@upstash/ratelimit`, `@upstash/redis`, `vitest` (5.x), `eslint` (9.x), `@types/node` (24.x), `@types/react`, `@types/react-dom`, `@types/pg`, `@types/qrcode`, `tailwindcss` e `@tailwindcss/postcss` (4.x).
- [ ] **Step 5:** instalar em dois comandos `npm install <pacote>@<versão> ...` (dependências e `--save-dev`), com todos os pacotes da §9.1. Se o `strict-allow-scripts` acusar um pacote, ler o script (`npm view <pacote> scripts`) antes de aprovar e acrescentar em `"allowScripts"` só o que for necessário, com o motivo no ledger. Ponto de partida da §9.1: `prisma`, `@prisma/engines`, `esbuild`, `unrs-resolver`.
- [ ] **Step 6:** `tsconfig.json` no padrão do Next 16 (`strict: true`, `moduleResolution: "bundler"`, `jsx: "preserve"`, `paths: { "@/*": ["./src/*"] }`, `plugins: [{ "name": "next" }]`); `postcss.config.mjs` com `@tailwindcss/postcss`; `globals.css` com `@import "tailwindcss";`; `layout.tsx` com `<html lang="pt-BR">` e fonte de sistema (sem `next/font`, por causa do `font-src 'self'` e para o build não depender de rede); `page.tsx` com um `<h1>short-url</h1>`.
- [ ] **Step 7:** `npx shadcn@<versão conferida com npm view> init` (estilo padrão, `src/`, alias `@/components` e `@/lib/utils`) e `npx shadcn@<mesma> add button input label card alert`. Conferir no `git diff package.json` as dependências que o CLI acrescentou (esperado: `class-variance-authority`, `clsx`, `tailwind-merge`, `lucide-react`, `tw-animate-css` e Radix), que todas ficaram com versão exata, e que nenhuma é recusada. Anotar no ledger.
- [ ] **Step 8 (verificação):**
  - `npm run build` → sucesso;
  - `npx tsc --noEmit` → sem erros;
  - `npm audit --omit=dev` → anotar o resultado no ledger;
  - `grep -c '"\^\|"~' package.json` → `0` (nenhuma faixa de versão);
  - `git status` não mostra `node_modules/`, `.next/` nem `next-env.d.ts`.
- [ ] **Step 9:** status da spec em `docs/superpowers/specs/README.md` e no cabeçalho da spec → `Em andamento` (a coluna "Plan relacionado" já aponta para os três planos).
- [ ] **Step 10:** pausa com o Rafael (o que cada arquivo faz, por que `.npmrc` primeiro, o que o shadcn/ui copiou para o repositório). Commit quando ele mandar:
  `chore(deps): cria o projeto Next 16 com npm endurecido, Tailwind e shadcn/ui`

### Task 2: ESLint com o AD-004 por lista branca (S2, RC3, RC6)

**Quem:** Opus testa (e monta o Vitest) → executor implementa. **QA:** não (configuração de lint).

**Contexto (ler antes):** `code-style.md` (S2), `architecture-layers.md`, `security-core.md` (RC6), spec §9.3; ESLint, "no-restricted-imports" (`patterns`, `group`, `regex`) e "Configuration Files" (precedência no flat config).

**Files:**
- Create (Opus): `vitest.config.mts` (só o projeto `unit` por enquanto: `src/**/*.test.{ts,tsx}` e `*.test.ts` da raiz, exceto `*.int.test.ts`; `resolve.tsconfigPaths: true`), `eslint.config.test.ts`
- Modify (Opus): `package.json` (scripts `lint`, `typecheck`, `test` da §9.1)
- Create (executor): `eslint.config.mjs`

**Interfaces:**
- Produces: `npm run lint`, `npm run typecheck`, `npm test`.

- [ ] **Step 1 (Opus): Vitest e scripts.** `vitest.config.mts` e scripts. Conferir que `npx vitest run` reconhece a configuração ("No test files found" é esperado neste ponto).
- [ ] **Step 2 (Opus): teste `eslint.config.test.ts`.** Usa a API Node do ESLint (`new ESLint({ cwd })`, `lintText(código, { filePath })`) e filtra as mensagens pelo `ruleId`. Casos (✗ = a regra indicada acusa; ✓ = nenhuma mensagem dessa regra):

  | Arquivo simulado | Código | Esperado |
  |---|---|---|
  | `src/domain/probe.ts` | `import { after } from 'next/server'` | ✗ `no-restricted-imports` |
  | `src/domain/probe.ts` | `import { Redis } from '@upstash/redis'` | ✗ |
  | `src/domain/probe.ts` | `import { randomBytes } from 'node:crypto'` | ✗ |
  | `src/domain/probe.ts` | `import x from '@/data/generated/prisma/client'` | ✗ |
  | `src/domain/probe.ts` | `import x from '../data/prisma-link-repository'` | ✗ (furo da `'!../*'`) |
  | `src/domain/probe.ts` | `import x from '../infra/local-fake-url-threat-checker'` | ✗ |
  | `src/domain/probe.ts` | `import x from '@/app/_lib/log'` | ✗ |
  | `src/domain/probe.ts` | `import { classifyLink } from './link'` | ✓ |
  | `src/domain/probe.ts` | `import { classifyLink } from '@/domain/link'` | ✓ |
  | `src/domain/__fakes__/probe.ts` | `import type { LinkRepository } from '../ports'` | ✓ |
  | `src/domain/__fakes__/probe.ts` | `import x from '../../data/prisma-client'` | ✗ |
  | `src/domain/probe.test.ts` | `import { describe } from 'vitest'` + `import { x } from './__fakes__/probe'` | ✓ |
  | `src/app/probe.ts` | `import x from '@/data/generated/prisma/client'` | ✗ |
  | `src/infra/probe.ts` | `import x from '../data/generated/prisma/client'` | ✗ |
  | `src/app/probe.ts` | `import { PrismaClient } from '@prisma/client'` | ✗ |
  | `src/app/probe.ts` | `import { Pool } from 'pg'` | ✗ |
  | `src/data/probe.ts` | `import { PrismaClient } from './generated/prisma/client'` e `import { Pool } from 'pg'` | ✓ |
  | `src/app/probe.tsx` | `<div dangerouslySetInnerHTML={{ __html: s }} />` | ✗ `react/no-danger` |
  | `src/data/probe.ts` | `prisma.$queryRawUnsafe('select 1')` | ✗ `no-restricted-properties` |
  | `src/data/probe.ts` | `prisma.$executeRawUnsafe('select 1')` | ✗ `no-restricted-properties` |
  | `src/data/probe.ts` | `Prisma.raw('x')` | ✗ `no-restricted-syntax` |
  | `src/data/probe.ts` | ``prisma.$queryRaw`select ${id}` `` | ✓ (nenhuma das três regras) |
  | `src/app/probe.ts` | `import { PNG } from 'pngjs'` (transitiva do `qrcode`, não declarada) | ✗ `import/no-extraneous-dependencies` |

  Mais: `eslint.isPathIgnored('src/data/generated/prisma/client.ts')` → `true`.
- [ ] **Step 3: vermelho.** `npx vitest run eslint.config.test.ts` → FAIL esperado: o ESLint não acha configuração (`eslint.config.mjs` ausente).
- [ ] **Step 4: delegar.** Produção: `eslint.config.mjs`. Spec §9.3, mais os ajustes da tabela "Ajustes na spec" (linha 9.3).
  - 🔎 A doc do `no-restricted-imports` avisa que reincluir arquivo de diretório excluído não funciona no estilo gitignore. Se o `group` não fechar os casos de `../`, usar `patterns[].regex` (do próprio ESLint 9) e registrar a escolha no relatório.
  - Os testes do domínio (`src/domain/**/*.test.ts`) ficam fora da lista branca, mas não fora das outras regras.
- [ ] **Step 5: verificação.** `npx vitest run eslint.config.test.ts`; `npm run lint` (sem erros no repositório inteiro); `npm run typecheck`.
- [ ] **Step 6:** revisão D7 (item 6 = esta tarefa é a própria trava das camadas) e pausa. Commit:
  `build(lint): barra imports fora da lista branca no domínio e SQL cru inseguro`

### Task 3: `next.config.ts` com travas e headers (RC4, RC6, trava 2)

**Quem:** Opus testa (e monta o `test:http`) → executor implementa. **QA:** sim (D6d: `next.config.ts`). Áreas: **headers e páginas**.

**Contexto (ler antes):** `security-core.md` (RC6), `architecture-local-dev.md` (trava 2), `security-rate-limit.md` (RC4), spec §9.4, §9.8; Next.js, "next.config.js: headers" e "How to set a Content Security Policy" (Without Nonces).

**Files:**
- Create (Opus): `next.config.test.ts`, `vitest.http.config.mts`, `tests/http/global-setup.ts`, `tests/http/global-headers.http.test.ts`
- Modify (Opus): `package.json` (script `test:http`)
- Create (executor): `next.config.ts`

**Interfaces:**
- Produces: `export default function nextConfig(phase: string): NextConfig` (spec §9.4). `npm run test:http` sobe o `next start` na porta 3000.

- [ ] **Step 1 (Opus): infraestrutura HTTP.** `vitest.http.config.mts` e `global-setup.ts` da §9.8:
  - o `global-setup` **recusa subir se `http://127.0.0.1:3000` já responder** (um `npm run dev` esquecido faria os testes rodarem contra os falsos);
  - sobe `next start -p 3000` com `DATABASE_URL` do `shorturl_test` e `APP_ORIGIN=http://localhost:3000`, **sem `USE_LOCAL_FAKES`** (apagar a variável do ambiente filho);
  - espera a porta responder (timeout de 30 s) e derruba o processo no `teardown`.
- [ ] **Step 2 (Opus): teste unitário `next.config.test.ts`** (`vi.stubEnv`, constantes de `next/constants`):
  - `USE_LOCAL_FAKES=true` + `PHASE_PRODUCTION_BUILD` → lança, e a mensagem cita `.env.development.local`;
  - `USE_LOCAL_FAKES=true` + `PHASE_PRODUCTION_SERVER` → lança;
  - `USE_LOCAL_FAKES=true` + `PHASE_DEVELOPMENT_SERVER` → não lança;
  - `USE_LOCAL_FAKES=TRUE` e `=1` + `PHASE_PRODUCTION_BUILD` → não lança (comparação estrita, coerente com a trava 1);
  - `VERCEL_ENV=preview` sem as três chaves → lança com os três nomes; só sem `SAFE_BROWSING_API_KEY` → a mensagem cita só ela; chave definida como `''` → conta como ausente; com as três → não lança;
  - sem `VERCEL_ENV` e sem chaves → não lança;
  - `UPSTASH_REDIS_REST_URL=https://segredo.example` e o token ausente → a mensagem **não** contém `segredo`;
  - `nextConfig(PHASE_PRODUCTION_BUILD)`: `poweredByHeader === false`; `headers()` devolve 2 regras, a primeira `source: '/:path*'` e a **última** `source: '/manage/:token'`;
  - CSP de produção igual, caractere por caractere, à string da §9.4 sem `'unsafe-eval'`; com `PHASE_DEVELOPMENT_SERVER`, o `script-src` contém `'unsafe-eval'`;
  - `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin` na regra global; `no-referrer`, `noindex` e `no-store` na regra da gestão.
- [ ] **Step 3 (Opus): teste HTTP `global-headers.http.test.ts`:**
  - `GET /` → os quatro headers globais com os valores de produção, sem `X-Powered-By`;
  - `GET /manage/qualquer-coisa` (ainda sem rota, responde 404 do Next) → `Referrer-Policy: no-referrer` (prova o "a última regra vence" no servidor real), `X-Robots-Tag: noindex`, `Cache-Control` contendo `no-store`, e o CSP global presente.
- [ ] **Step 4: vermelho.** `npx vitest run next.config.test.ts` → FAIL: módulo `./next.config` não encontrado. `npm run test:http` → FAIL nos headers (o build passa sem config).
- [ ] **Step 5: delegar.** Produção: `next.config.ts`, spec §9.4.
- [ ] **Step 6: verificação.** Comandos do ciclo padrão mais `npm run test:http`. Prova manual da trava 2: `USE_LOCAL_FAKES=true npm run build` → falha com a instrução.
- [ ] **Step 7: QA.** URL base `http://localhost:3000`; entregue: headers globais e CSP; área: headers e páginas (console sem erro de CSP no `/` e numa página 404). O Postgres do Docker só chega na Tarefa 5, e as páginas desta tarefa e da 4 não usam banco: o `npm run dev` sobe sem ele.
- [ ] **Step 8:** revisão e pausa. Commit:
  `feat(app): aplica CSP e headers de segurança e trava falsos e chaves no build`

### Task 4: Home provisória

**Quem:** Opus testa → executor implementa. **QA:** sim (D6d: `src/app/`). Áreas: **headers e páginas**.

**Contexto (ler antes):** `code-style.md`, spec §4.1, §12 (fatia 1: "home provisória publicada").

**Files:**
- Create (Opus): `tests/http/home.http.test.ts`
- Modify (executor): `src/app/page.tsx`, `src/app/layout.tsx` (só `metadata`)

**Interfaces:**
- Produces: `/` com `<title>short-url</title>`. A fatia 2 troca o conteúdo pelo formulário.

- [ ] **Step 1: teste `home.http.test.ts`.** `GET /` → `200`, `Content-Type` com `text/html`, corpo com `<html lang="pt-BR"`, `<title>short-url</title>`, um `<h1>` com `short-url`, o parágrafo `Encurtador de links com estatísticas. Em construção: a criação de links chega na próxima etapa.` e um link para `https://github.com/ribeirorafadev/url-shortener` com `rel="noopener noreferrer"`.
- [ ] **Step 2: vermelho.** `npm run test:http` → FAIL: título e parágrafo ausentes.
- [ ] **Step 3: delegar.** Produção: `page.tsx` com o componente `Card` do shadcn/ui, sem `'use client'`; `metadata` no `layout.tsx` (`title: 'short-url'`, `description` em pt-BR). Sem fonte externa, sem imagem externa (CSP).
- [ ] **Step 4: verificação.** Ciclo padrão mais `npm run test:http`.
- [ ] **Step 5: QA.** Área: headers e páginas (`/`, uma rota inexistente, console sem erro de CSP nem de hidratação).
- [ ] **Step 6:** revisão e pausa. Commit: `feat(app): publica a home provisória`

### Task 5: Postgres em Docker e `.env.example`

**Quem:** Opus (setup), depois dos pré-requisitos (Docker e major do Neon). **QA:** não.

**Contexto (ler antes):** `architecture-testing-ci.md` (Postgres em Docker), `architecture-local-dev.md`, `security-core.md` (segredos), spec §9.7, §9.9.

**Files:**
- Create: `compose.yml`, `docker/postgres-init.sql`, `.env.example`
- Create (local, ignorado pelo Git): `.env.development.local` (cópia do `.env.example`)

- [ ] **Step 1:** `compose.yml` da §9.7 com a `<MAJOR>` do Neon; `postgres-init.sql` com `CREATE DATABASE shorturl_test;`; `.env.example` da §9.9.
- [ ] **Step 2:** `cp .env.example .env.development.local`; `git status` não lista o `.env.development.local` e lista o `.env.example`.
- [ ] **Step 3 (verificação):**
  - `docker compose up -d --wait` → `healthy`;
  - `docker compose exec postgres psql -U shorturl -lqt | cut -d '|' -f1` → contém `shorturl` e `shorturl_test`;
  - `ss -ltn 'sport = :5432'` → escutando só em `127.0.0.1`;
  - `docker compose exec postgres psql -U shorturl -c 'show server_version'` → a major do Neon.
- [ ] **Step 4:** pausa (o que é um container, por que a porta presa ao `127.0.0.1`, por que dois bancos). Commit:
  `build(docker): sobe o Postgres local com os bancos de dev e de teste`

### Task 6: Prisma: schema, configuração e migration `init`

**Quem:** Opus testa (e monta o projeto `integration`) → executor implementa. **QA:** não (banco).

**Contexto (ler antes):** `data-model.md`, `architecture-persistence.md` (S1, `@next/env`), `architecture-layers.md`, spec §6.1, §9.5, §9.8; Prisma v7, "Config API" e "Upgrade to Prisma ORM 7".

**Files:**
- Create (Opus): `src/data/schema.int.test.ts`, `tests/setup/integration-setup.ts` (recusa host fora de `127.0.0.1`/`localhost`; `TRUNCATE click_events, links RESTART IDENTITY` antes de cada arquivo, com `pg`)
- Modify (Opus): `vitest.config.mts` (projeto `integration`, `fileParallelism: false`, `setupFiles`); `package.json` (scripts `postinstall`, `db:migrate` e `db:migrate:test` = `DATABASE_URL_UNPOOLED=postgresql://shorturl:shorturl-dev@127.0.0.1:5432/shorturl_test prisma migrate deploy`)
- Create (executor): `prisma/schema.prisma`, `prisma.config.ts`, `prisma/migrations/<timestamp>_init/migration.sql` (gerada)

**Interfaces:**
- Produces: tabelas `links` e `click_events`, enum `DeviceType`; client gerado em `src/data/generated/prisma/` (o caminho exato do `PrismaClient` vai para o ledger e é usado na fatia 2).

- [ ] **Step 1 (Opus): teste `schema.int.test.ts`** (consulta o `information_schema` e o `pg_catalog` com `pg`):
  - `links`: `id integer`, `slug text NOT NULL`, `destination_url text NOT NULL`, `manage_token_hash bytea NOT NULL`, `click_count integer NOT NULL DEFAULT 0`, `max_clicks integer NULL`, `expires_at`/`deactivated_at` `timestamp with time zone NULL` com `datetime_precision = 3`, `created_at timestamptz(3) NOT NULL` com default `CURRENT_TIMESTAMP`;
  - índices `UNIQUE` em `links(slug)` e em `links(manage_token_hash)`;
  - `click_events`: `id bigint`, `link_id integer NOT NULL`, `device_type` do tipo `DeviceType`, `referrer_host text NULL`, `clicked_at timestamptz(3) NOT NULL DEFAULT CURRENT_TIMESTAMP`;
  - **as colunas de `click_events` são exatamente** `{id, link_id, device_type, referrer_host, clicked_at}` (guarda do RNF05: nada de IP nem UA cru);
  - enum `DeviceType` = `MOBILE, DESKTOP, TABLET, BOT, UNKNOWN`, nessa ordem;
  - índice em `click_events (link_id, clicked_at)`, nessa ordem de colunas;
  - FK `click_events.link_id → links.id` com `delete_rule = 'RESTRICT'`;
  - comportamento: slug repetido → erro `23505`; apagar um link com evento → erro `23503`.
- [ ] **Step 2 (Opus):** projeto `integration` no `vitest.config.mts` e scripts no `package.json` (sem rodar `npm install` ainda; o `postinstall` precisa do schema).
- [ ] **Step 3: vermelho.** `npx vitest run --project integration` → FAIL no setup: `relation "links" does not exist`.
- [ ] **Step 4: delegar.** Produção: schema da §6.1, `prisma.config.ts` da §9.5. O executor roda `npx prisma generate` e `npx prisma migrate dev --name init` (lê o `.env.development.local` pelo `@next/env`; aplica no banco `shorturl`) e depois `npm run db:migrate:test`.
  - 🔎 Se o tipo do `defineConfig` não aceitar `url: undefined`, usar `?? ''` (§9.5) e registrar no relatório.
  - 🔎 Conferir à mão o `migration.sql`: `TIMESTAMPTZ(3)`, `BYTEA`, os dois `UNIQUE`, o índice composto e `ON DELETE RESTRICT`.
- [ ] **Step 5: verificação.**
  - `npx vitest run --project integration`, `npm test`, `npm run lint`, `npm run typecheck`;
  - `npm ci` do zero (prova o `postinstall`) e `ls src/data/generated/prisma/` (anotar no ledger o arquivo que exporta o `PrismaClient`);
  - sem `.env.development.local` (renomeado temporariamente): `npx prisma generate` funciona, e `npm run db:migrate` falha com erro explícito de URL ausente (S1).
- [ ] **Step 6:** revisão D7 (item 7: o schema não tem coluna de IP) e pausa. Commit:
  `feat(data): cria o schema e a migration init com Prisma 7`

### Task 7: Tipos do link e `classifyLink`

**Quem:** Opus testa → executor implementa. **QA:** não (domínio).

**Contexto:** `link-lifecycle.md`, `redirect.md` (precedência do 410), spec §5.1.

**Files:**
- Test: `src/domain/link.test.ts`
- Create: `src/domain/link.ts`

**Interfaces:**
- Produces: `DeviceType`, `GoneReason`, `ExpirationDuration`, `ExpirationChoice`, `LinkSnapshot`, `NewLink`, `EXPIRATION_DURATION_MS`, `MAX_CLICKS_RANGE`, `MAX_URL_LENGTH`, `MAX_EXPIRATION_YEARS`, `classifyLink(link: LinkSnapshot, now: Date): 'active' | GoneReason` (spec §5.1).

- [ ] **Step 1: teste.** Snapshot base: `{ id: 1, slug: 'aB3xZ9k', destinationUrl: 'https://exemplo.com/', clickCount: 0, maxClicks: null, expiresAt: null, deactivatedAt: null, createdAt }`, com `now = 2026-10-08T12:00:00.000Z`.
  - Constantes: `EXPIRATION_DURATION_MS` = `{ '1h': 3_600_000, '24h': 86_400_000, '7d': 604_800_000, '30d': 2_592_000_000 }`; `MAX_CLICKS_RANGE` = `{ min: 1, max: 1_000_000 }`; `MAX_URL_LENGTH` = 2048; `MAX_EXPIRATION_YEARS` = 5.
  - `classifyLink`:

    | Situação | Esperado |
    |---|---|
    | base | `'active'` |
    | `deactivatedAt` preenchido | `'deactivated'` |
    | `expiresAt = now − 1 ms` | `'expired'` |
    | **`expiresAt = now` (mesmo milissegundo)** | **`'expired'`** (Review Focus 3) |
    | `expiresAt = now + 1 ms` | `'active'` |
    | `maxClicks 10`, `clickCount 9` | `'active'` |
    | `maxClicks 10`, `clickCount 10` | `'exhausted'` |
    | `maxClicks 10`, `clickCount 11` | `'exhausted'` |
    | `maxClicks null`, `clickCount 1_000_000` | `'active'` |
    | desativado + expirado + esgotado | `'deactivated'` |
    | expirado + esgotado | `'expired'` |
- [ ] **Step 2: vermelho.** `npx vitest run src/domain/link.test.ts` → FAIL: `./link` não existe.
- [ ] **Step 3–7:** ciclo padrão. Commit: `feat(domain): define o link e a precedência do link inativo`

### Task 8: Slug (formato e gerador CSPRNG)

**Quem:** Opus testa → executor implementa. **QA:** não.

**Contexto:** `link-lifecycle.md` (Slug), `redirect.md` (pré-validação, B-4), spec §5.3.

**Files:**
- Test: `src/domain/slug.test.ts`
- Create: `src/domain/slug.ts`

**Interfaces:**
- Produces: `isValidSlugFormat(s: string): boolean`, `generateSlug(): string`.

- [ ] **Step 1: teste.**
  - `isValidSlugFormat`: ✓ `'aB3xZ9k'`, `'0000000'`, `'ZZZZZZZ'`; ✗ `'aB3xZ9'` (6), `'aB3xZ9kk'` (8), `'aB3-Z9k'`, `'aB3_Z9k'`, `'aB3xZ9ç'`, `''`, `'aB3xZ9k\n'`, `'manage'`, `'wp-login.php'`, `'.env'`.
  - `generateSlug`, 10.000 amostras: todas passam no `isValidSlugFormat`; os 62 caracteres aparecem; cada caractere fica entre 80% e 120% da média (10.000 × 7 / 62 ≈ 1.129); nenhuma repetida.
  - Amostragem por rejeição, com `vi.spyOn(crypto, 'getRandomValues')` preenchendo os lotes:
    - **lote inteiro com 255, depois lote com 0 → 7 caracteres iguais** (Review Focus 5: não para nem encurta);
    - lote com `248` (rejeitado) seguido de lote com `0` → mesmo resultado do lote com `0` (o 248 não entra);
    - lote com `247` e lote com `61` → o mesmo caractere (`247 % 62 = 61`, então 247 é aceito);
    - o espião confirma que o gerador usa `crypto.getRandomValues` (nada de `Math.random`).
- [ ] **Step 2: vermelho.** `npx vitest run src/domain/slug.test.ts` → FAIL: módulo inexistente.
- [ ] **Step 3–7:** ciclo padrão. Commit: `feat(domain): gera slug base62 com CSPRNG e valida o formato`

### Task 9: Token de gestão (formato, geração e hash)

**Quem:** Opus testa → executor implementa. **QA:** não.

**Contexto:** `security-token.md`, `link-creation.md` (Token), spec §5.3.

**Files:**
- Test: `src/domain/manage-token.test.ts`
- Create: `src/domain/manage-token.ts`

**Interfaces:**
- Produces: `isValidManageTokenFormat(t: string): boolean`, `generateManageToken(): string`, `hashManageToken(t: string): Promise<Uint8Array>`.

- [ ] **Step 1: teste** (vetores calculados no Node 24 com `Buffer.toString('base64url')` e `createHash('sha256')`):
  - formato: ✓ `'AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8'` (43); ✓ `'-_v7-_v7-_v7-_v7-_v7-_v7-_v7-_v7-_v7-_v7-_s'`; ✗ 42 e 44 caracteres; ✗ com `=` no fim; ✗ com `+` ou `/`; ✗ `''`;
  - `generateManageToken` com `getRandomValues` preenchendo os bytes `0..31` → `'AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8'`; com 32 bytes `0xff` → `'__________________________________________8'`; com 32 bytes `0xfb` → `'-_v7-_v7-_v7-_v7-_v7-_v7-_v7-_v7-_v7-_v7-_s'` (prova a troca de `+`→`-` e `/`→`_`);
  - 1.000 tokens reais: todos no formato, nenhum repetido;
  - `hashManageToken('AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8')` → `Uint8Array` de 32 bytes, hex `ea866a757e4c38babfa8127cbe9a409d3e1f93a00ff1488ff735fcf917afffd0`; tokens diferentes → hashes diferentes.
- [ ] **Step 2: vermelho.** `npx vitest run src/domain/manage-token.test.ts` → FAIL: módulo inexistente.
- [ ] **Step 3–7:** ciclo padrão (item 7 da D7: nenhum `console.*` com o token). Commit:
  `feat(domain): gera o token de gestão em base64url e calcula o hash SHA-256`

### Task 10: Tempo em `America/Sao_Paulo`

**Quem:** Opus testa → executor implementa. **QA:** não.

**Contexto:** `link-lifecycle.md` (Relógio, Expiração), `data-model.md` (dia das estatísticas), spec §5.4.

**Files:**
- Test: `src/domain/sao-paulo-time.test.ts`
- Create: `src/domain/sao-paulo-time.ts`

**Interfaces:**
- Produces: `todayInSaoPaulo(now: Date): string`, `saoPauloOffset(date: string, time: string): string`, `endOfDayInSaoPaulo(date: string): Date`, `startOfDayInSaoPaulo(date: string): Date`, `addDays(date: string, days: number): string`.

- [ ] **Step 1: teste.**
  - `todayInSaoPaulo`: `2026-10-08T02:59:59.999Z` → `'2026-10-07'`; `2026-10-08T03:00:00.000Z` → `'2026-10-08'`;
  - `saoPauloOffset('2026-10-30', '23:59:59.999')` → `'-03:00'`; `('2018-12-15', '12:00:00')` → `'-02:00'` (horário de verão);
  - `endOfDayInSaoPaulo('2026-10-30').toISOString()` → `'2026-10-31T02:59:59.999Z'`; `('2018-12-15')` → `'2018-12-16T01:59:59.999Z'`;
  - `startOfDayInSaoPaulo('2026-10-08').toISOString()` → `'2026-10-08T03:00:00.000Z'`;
  - `addDays`: `('2026-10-08', -29)` → `'2026-09-09'`; `('2026-12-31', 1)` → `'2027-01-01'`; `('2028-02-28', 1)` → `'2028-02-29'`; `('2026-03-01', -1)` → `'2026-02-28'`.
- [ ] **Step 2: vermelho.** `npx vitest run src/domain/sao-paulo-time.test.ts` → FAIL: módulo inexistente.
- [ ] **Step 3–7:** ciclo padrão. Commit: `feat(domain): converte datas do horário de Brasília sem biblioteca`

### Task 11: `UrlValidator` (R1 a R6)

**Quem:** Opus testa → executor implementa. **QA:** não (o QA da criação, na fatia 2, cobre pela tela).

**Contexto:** `url-validation.md` (inteiro), `security-core.md` (phishing), spec §5.5.

**Files:**
- Test: `src/domain/url-validator.test.ts`
- Create: `src/domain/url-validator.ts`

**Interfaces:**
- Consumes: `MAX_URL_LENGTH` (Tarefa 7).
- Produces: `UrlViolation`, `class UrlValidator { constructor(ownHosts: readonly string[]); validate(input: string): { ok: true; href: string; isInsecure: boolean } | { ok: false; violation: UrlViolation } }`.

- [ ] **Step 1: teste.** `new UrlValidator(['short.example.app', 'short-url.vercel.app'])`.
  - **Aceitas** (`href`, `isInsecure`):

    | Entrada | `href` | `isInsecure` |
    |---|---|---|
    | `https://exemplo.com` | `https://exemplo.com/` | `false` |
    | `exemplo.com/promo` (R6) | `https://exemplo.com/promo` | `false` |
    | `http://exemplo.com` | `http://exemplo.com/` | `true` |
    | `HTTPS://EXEMPLO.COM/Path` | `https://exemplo.com/Path` | `false` |
    | `https://аpple.com` (cirílico) | `https://xn--pple-43d.com/` | `false` |
    | `https://exemplo.com/ação?q=a b<c>` | `https://exemplo.com/a%C3%A7%C3%A3o?q=a%20b%3Cc%3E` | `false` |
    | `https://1.1.1.1/` | `https://1.1.1.1/` | `false` |
    | `https://sub.short.example.app/` | igual | `false` (só o host exato é próprio) |
    | fronteiras públicas: `100.63.255.255`, `100.128.0.0`, `172.15.255.255`, `172.32.0.0`, `198.17.255.255`, `198.20.0.0`, `223.255.255.255`, `11.0.0.0` | aceitas | — |
  - **Recusadas** (violação):
    - `'invalid'`: `https://%%%`, `exemplo com`;
    - `'protocol'`: `javascript:alert(1)`, `data:text/html,x`, `ftp://exemplo.com`, `file:///etc/passwd`, `localhost:3000`, `site.com:8080/x`;
    - `'credentials'`: `https://nubank.com.br@evil.com/login`, `https://user:@evil.com`, `https://:senha@evil.com`;
    - `'ipv6-literal'`: `http://[2001:db8::1]/`, `http://[::1]`, `http://[::ffff:8.8.8.8]`;
    - `'not-public'`: `http://localhost`, `http://app.localhost`, `http://printer.local`, `http://router.home.arpa`, `http://svc.internal`, `http://intranet`; IPv4 `0.0.0.0`, `10.0.0.1`, `100.64.0.1`, `100.127.255.255`, `127.0.0.1`, `169.254.169.254`, `172.16.0.1`, `172.31.255.255`, `192.0.0.1`, `192.0.2.1`, `192.168.0.1`, `198.18.0.1`, `198.19.255.255`, `198.51.100.1`, `203.0.113.1`, `224.0.0.1`, `239.255.255.255`, `240.0.0.1`, `255.255.255.255`; normalizados pelo parser: `http://0x7f000001`, `http://017700000001`, `http://127.1`, `http://3232235521`; **com ponto final: `http://localhost./`, `http://printer.local./`** (Review Focus 1);
    - `'own-domain'`: `https://short.example.app/abc`, `https://SHORT-URL.vercel.app/x`, **`https://short-url.vercel.app./x`** (Review Focus 1);
    - `'too-long'`: `'https://exemplo.com/' + 'a'.repeat(n)` com `href` de **2048** caracteres → aceita; com **2049** → `'too-long'`; `'https://exemplo.com/' + 'ç'.repeat(700)` (entrada curta, `href` com mais de 4.000 caracteres) → `'too-long'` (R5 medida no `href`).
  - **Ordem** (vale a primeira violação): `javascript://user:pw@localhost` → `'protocol'`; `https://user:pw@localhost` → `'credentials'`; `https://user@short.example.app` → `'credentials'`; `http://[::1]` → `'ipv6-literal'`, não `'not-public'`.
- [ ] **Step 2: vermelho.** `npx vitest run src/domain/url-validator.test.ts` → FAIL: módulo inexistente.
- [ ] **Step 3: delegar.** Spec §5.5 mais o ajuste do ponto final (tabela "Ajustes na spec"). Faixas IPv4 por comparação numérica dos 4 octetos, sem regex frágil.
- [ ] **Step 4–7:** ciclo padrão. Commit: `feat(domain): valida a URL de destino com as regras R1 a R6`

### Task 12: `isPreviewBot` (B-3)

**Quem:** Opus testa → executor implementa. **QA:** não (o navegador do QA tem UA fixo; D6d).

**Contexto:** `redirect.md` (Bots de preview, B-3), spec §5.6.

**Files:**
- Test: `src/domain/preview-bot.test.ts`
- Create: `src/domain/preview-bot.ts`

**Interfaces:**
- Produces: `isPreviewBot(userAgent: string | null): boolean`.

- [ ] **Step 0 (Opus) 🔎:** conferir na documentação de cada plataforma o UA e o padrão mais específico (WhatsApp, Slack "Slackbot", Meta "facebookexternalhit", X "Twitterbot", Telegram, LinkedIn, Discord) e anotar a fonte de cada UA num comentário do teste. Se algum padrão da §5.6 divergir da doc, parar e levar ao Rafael antes de delegar (é mudança de spec).
- [ ] **Step 1: teste.**
  - `true`: `WhatsApp/2.23.20.0 A`, `WhatsApp/2.2346.52 i`, `Slackbot-LinkExpanding 1.0 (+https://api.slack.com/robots)`, `Slackbot 1.0 (+https://api.slack.com/robots)`, `facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)`, `Twitterbot/1.0`, `TelegramBot (like TwitterBot)`, `LinkedInBot/1.0 (compatible; Mozilla/5.0; Apache-HttpClient +http://www.linkedin.com)`, `Mozilla/5.0 (compatible; Discordbot/2.0; +https://discordapp.com)` (os UAs exatos são os conferidos no Step 0);
  - `false`: Chrome no Windows, Safari no iPhone, Chrome no Android, **navegador embutido do Facebook** (`... [FBAN/FBIOS;FBAV/...]`), **do Instagram** (`... Instagram 300.0.0.0 ...`), `curl/8.5.0`, `NotWhatsApp/1.0`, `MyDiscordbotClone` (sem `/`), `''`, `null`.
- [ ] **Step 2: vermelho.** `npx vitest run src/domain/preview-bot.test.ts` → FAIL: módulo inexistente.
- [ ] **Step 3–7:** ciclo padrão. Commit: `feat(domain): reconhece os bots de preview sem falso positivo`

### Task 13: Dispositivo e referrer (`click-tracker.ts`)

**Quem:** Opus testa → executor implementa. **QA:** não.

**Contexto:** `data-model.md` (dispositivo, referrer), spec §5.6.

**Files:**
- Test: `src/domain/click-tracker.test.ts`
- Create: `src/domain/click-tracker.ts`

**Interfaces:**
- Consumes: `DeviceType` (Tarefa 7).
- Produces: `classifyDevice(h: { userAgent: string | null; secChUaMobile: string | null }): Exclude<DeviceType, 'BOT'>`, `extractReferrerHost(referer: string | null): string | null`.

- [ ] **Step 1: teste.**
  - `classifyDevice`: UA `null` → `UNKNOWN`; **UA `''` → `UNKNOWN`** (Review Focus 4); `secChUaMobile '?1'` com UA de Chrome no Windows → `MOBILE`; `'?0'` com UA de iPhone → `MOBILE`; UA de iPad (`Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X)...`) → `TABLET`; Firefox em tablet Android (`Mozilla/5.0 (Android 14; Tablet; rv:130.0) Gecko/130.0 Firefox/130.0`) → `TABLET`; Chrome em celular Android (`... Android 14; Pixel 8 ... Mobile Safari/537.36`) → `MOBILE`; Chrome no Windows → `DESKTOP`; Safari no Mac → `DESKTOP`; `curl/8.5.0` → `DESKTOP`.
  - `extractReferrerHost`: `null` → `null`; **`''` → `null`** (Review Focus 4); `https://www.Google.com/search?q=x` → `'google.com'`; `https://l.facebook.com/` → `'l.facebook.com'`; `http://exemplo.com:8080/a` → `'exemplo.com'`; `https://www.www.exemplo.com/` → `'www.exemplo.com'` (tira um `www.` só); `https://wwwexemplo.com/` → `'wwwexemplo.com'`; **`https://www./` → `null`** (host vazio depois do `www.`); `android-app://com.google.android.gm/` → `null`; `javascript:alert(1)` → `null`; `não é url` → `null`.
- [ ] **Step 2: vermelho.** `npx vitest run src/domain/click-tracker.test.ts` → FAIL: módulo inexistente.
- [ ] **Step 3–7:** ciclo padrão. Commit: `feat(domain): classifica o dispositivo e normaliza o referrer`

### Task 14: Portas, erros, fakes e `LinkService.create`

**Quem:** Opus testa (e escreve os fakes) → executor implementa. **QA:** não (domínio; a tela vem na fatia 2).

**Contexto:** `link-creation.md` (Fluxo, RC7), `link-lifecycle.md`, `url-validation.md` (R7: porta), `error-map.md`, spec §5.2, §5.7 (`create`), §6.5 (o domínio define `RepositoryUnavailableError`), §11.

**Files:**
- Create (Opus), usados também nas fatias 2 e 3:
  - `src/domain/__fakes__/in-memory-link-repository.ts`: `class InMemoryLinkRepository implements LinkRepository`, com a mesma semântica do SQL da §6.3 (inclusive `expires_at > now`); guarda os links num array; `constructor(options?: { takenSlugAttempts?: number })` devolve `'slug-taken'` nas primeiras N gravações; `insertCalls` registra as chamadas; `seed(link: LinkSnapshot & { manageTokenHash: Uint8Array })` insere direto;
  - `src/domain/__fakes__/in-memory-click-event-repository.ts`: `class InMemoryClickEventRepository implements ClickEventRepository`; `record` guarda em `events`; `getStats` devolve o `RawClickStats` de `programmedStats` e registra `(linkId, dailyFrom)` em `statsCalls`;
  - `src/domain/__fakes__/programmable-threat-checker.ts`: `class ProgrammableThreatChecker implements UrlThreatChecker`, `constructor(verdict: ThreatVerdict)`, `checkedUrls: string[]`;
  - `src/domain/__fakes__/fixed-clock.ts`: `class FixedClock implements Clock`, `constructor(date: Date)`, `now()`, `set(date: Date)`.
- Test: `src/domain/link-service.create.test.ts`
- Create (executor): `src/domain/ports.ts`, `src/domain/errors.ts`, `src/domain/link-service.ts` (só o construtor e o `create`)

**Interfaces:**
- Consumes: Tarefas 7 a 11.
- Produces: `Clock`, `ThreatVerdict`, `UrlThreatChecker`, `LinkRepository`, `ClickEventRepository`, `RawClickStats` (§5.2); `class RepositoryUnavailableError extends Error` (com `cause`); `CreateLinkInput`, `CreateLinkFieldError`, `CreateLinkResult`, `class LinkService` com `create` (§5.7).

- [ ] **Step 1 (Opus): fakes e teste.** `now = 2026-10-08T15:00:00.000Z` (12h em Brasília); `UrlValidator(['short.example.app'])`; veredito padrão `'safe'`.
  1. Mínimo (`https://exemplo.com`, `null`, `{ kind: 'none' }`) → `created`; `slug` e `manageToken` nos formatos; `isInsecureDestination: false`; o repositório tem um link com `destinationUrl 'https://exemplo.com/'`, `manageTokenHash` igual a `await hashManageToken(manageToken)`, `maxClicks null`, `expiresAt null`; o Google foi consultado uma vez com `'https://exemplo.com/'`.
  2. `http://exemplo.com` → `isInsecureDestination: true`.
  3. **Erros de todos os campos juntos:** `javascript:x`, `maxClicks 0`, `end-of-day '2026-10-07'` → `invalid` com `[{ field: 'url', code: 'protocol' }, { field: 'maxClicks', code: 'out-of-range' }, { field: 'expiration', code: 'past-date' }]`, nessa ordem; o Google **não** é consultado; repositório vazio.
  4. `maxClicks` 1 e 1.000.000 → aceitos; 1.000.001 → `out-of-range`.
  5. `end-of-day '2026-10-08'` (hoje) → aceito, `expiresAt = 2026-10-09T02:59:59.999Z`.
  6. **`now = 2026-10-09T02:30:00.000Z` (23h30 do dia 8 em Brasília) e `end-of-day '2026-10-08'` → aceito** (o "hoje" é o de Brasília, não o UTC).
  7. `'2031-10-08'` → aceito; `'2031-10-09'` → `too-far`. Com `now = 2028-02-29T15:00:00.000Z`: `'2033-02-28'` → aceito; `'2033-03-01'` → `too-far`.
  8. `{ kind: 'duration', duration: '24h' }` → `expiresAt = now + 86_400_000`.
  9. Veredito `'dangerous'` → `{ status: 'threat' }`, repositório vazio.
  10. Veredito `'unavailable'` → `{ status: 'unavailable', cause: 'threat-checker' }`, repositório vazio.
  11. 2 colisões e sucesso → `created`; `insert` chamado 3 vezes, com o mesmo `manageTokenHash` nas três.
  12. 3 colisões → `{ status: 'unavailable', cause: 'slug-collisions' }`; `insert` chamado **exatamente** 3 vezes.
  13. `insert` lança `RepositoryUnavailableError` → `create` rejeita com o mesmo erro.
  14. `https://short.example.app/x` → `invalid` com `{ field: 'url', code: 'own-domain' }`.
- [ ] **Step 2: vermelho.** `npx vitest run src/domain/link-service.create.test.ts` → FAIL: `../ports` e `./link-service` inexistentes.
- [ ] **Step 3–7:** ciclo padrão. Commit:
  `feat(domain): cria o link validando todos os campos antes da blocklist`

### Task 15: `LinkService.deactivate`

**Quem:** Opus testa → executor implementa. **QA:** não.

**Contexto:** `manage-page.md` (desativação irreversível e idempotente, IDOR), `security-token.md`, spec §5.7 (`deactivate`).

**Files:**
- Test: `src/domain/link-service.deactivate.test.ts`
- Modify: `src/domain/link-service.ts`

**Interfaces:**
- Produces: `LinkService.deactivate(manageToken: string): Promise<'deactivated' | 'already-deactivated' | 'not-found'>`.

- [ ] **Step 1: teste** (fakes da Tarefa 14; o link é criado pelo próprio `create`, para usar o token real):
  - token válido de link ativo → `'deactivated'`; `deactivatedAt` = `now` do relógio;
  - desativado em T0, nova chamada em T1 → `'already-deactivated'`, e `deactivatedAt` continua T0;
  - token no formato, mas inexistente → `'not-found'`;
  - formato inválido (`'abc'`, 44 caracteres) → `'not-found'`, e o repositório **não** é chamado (espião);
  - link expirado e ainda não desativado → `'deactivated'`.
- [ ] **Step 2: vermelho.** `npx vitest run src/domain/link-service.deactivate.test.ts` → FAIL: `deactivate is not a function`.
- [ ] **Step 3–7:** ciclo padrão. Commit: `feat(domain): desativa o link pelo token de forma idempotente`

### Task 16: `RedirectService`

**Quem:** Opus testa → executor implementa. **QA:** não (a rota vem na fatia 2).

**Contexto:** `redirect.md` (Fluxo, Bots de preview, `HEAD`, RC9), spec §5.8.

**Files:**
- Test: `src/domain/redirect-service.test.ts`
- Create: `src/domain/redirect-service.ts`

**Interfaces:**
- Consumes: `LinkRepository`, `Clock`, `classifyLink`.
- Produces: `RedirectMode`, `RedirectOutcome`, `class RedirectService { constructor(deps: { links: LinkRepository; clock: Clock }); resolve(slug: string, mode: RedirectMode): Promise<RedirectOutcome> }`.

- [ ] **Step 1: teste** (fake de repositório com links inseridos direto, `now = 2026-10-08T12:00:00.000Z`):
  - `visit`: ativo sem limite → `redirect` com `linkId` e `destinationUrl`, `clickCount` +1; limite 10 com 9 cliques → `redirect` e `clickCount` 10; a visita seguinte → `gone` `'exhausted'`; inexistente → `not-found`; desativado → `gone` `'deactivated'` e `clickCount` inalterado; **`expiresAt = now` → `gone` `'expired'`** (Review Focus 3); desativado + expirado + esgotado → `'deactivated'`;
  - **invariante:** fake com `consumeClick` devolvendo `null` e `findBySlug` devolvendo um link ativo → `resolve` rejeita com `Error` cuja mensagem cita a invariante;
  - `peek`: ativo sem limite → `redirect` e `clickCount` inalterado; ativo com limite → `limited-preview` com o `linkId`, `clickCount` inalterado, sem `destinationUrl` no objeto; inexistente → `not-found`; cada motivo de inativo → `gone` com o motivo; `consumeClick` **nunca** é chamado em `peek` (espião).
- [ ] **Step 2: vermelho.** `npx vitest run src/domain/redirect-service.test.ts` → FAIL: módulo inexistente.
- [ ] **Step 3–7:** ciclo padrão. Commit: `feat(domain): resolve o redirect sem consumir link em prévia nem HEAD`

### Task 17: Estatísticas (`click-stats.ts`)

**Quem:** Opus testa → executor implementa. **QA:** não.

**Contexto:** `manage-page.md` (janela, RC8, RC9), `data-model.md`, spec §5.9.

**Files:**
- Test: `src/domain/click-stats.test.ts`
- Create: `src/domain/click-stats.ts`

**Interfaces:**
- Consumes: `RawClickStats`, `todayInSaoPaulo`, `addDays`.
- Produces: `ClickStats`, `dailyWindow(createdAt: Date, now: Date): { fromDay: string; toDay: string }`, `buildClickStats(raw: RawClickStats, clickCount: number, window: { fromDay: string; toDay: string }): ClickStats`.

- [ ] **Step 1: teste.**
  - `dailyWindow`: criado em `2026-09-01T15:00Z`, `now 2026-10-08T15:00Z` → `{ fromDay: '2026-09-09', toDay: '2026-10-08' }`; criado hoje → `{ '2026-10-08', '2026-10-08' }`; criado em `2026-10-08T02:00Z` (dia 7 em Brasília) → `fromDay '2026-10-07'`; **`now = 2026-10-09T02:59:59.980Z` e `createdAt = 2026-10-09T03:00:00.030Z` (o banco 50 ms à frente, virando o dia) → `{ fromDay: '2026-10-08', toDay: '2026-10-08' }`** (Review Focus 2).
  - `buildClickStats`:
    - vazio, `clickCount 0`, janela de 3 dias → `humanTotal 0`, `botPreviews 0`, `byDevice []`, `topReferrers []`, `otherReferrers 0`, `daily` com 3 dias zerados, `detailBelowTotal false`;
    - `byDevice { MOBILE: 5, DESKTOP: 3, BOT: 4 }`, `clickCount 8` → `humanTotal 8`, `botPreviews 4`, `byDevice [{ MOBILE, 5 }, { DESKTOP, 3 }]`, `detailBelowTotal false`;
    - empate `{ TABLET: 2, DESKTOP: 2 }` → `DESKTOP` antes de `TABLET`;
    - `clickCount 10` e humanos 8 → `detailBelowTotal true`;
    - referrers: 12 hosts com contagens 12 a 1 e `null` com 5 → `topReferrers` com 10 itens, em ordem decrescente, incluindo o `null`; `otherReferrers` = soma dos que ficaram de fora; empate de contagem → host em ordem alfabética, `null` por último;
    - `daily` bruto `[{ '2026-10-07', 2 }, { '2026-10-01', 9 }]` com janela `2026-10-06..2026-10-08` → `[{ '2026-10-06', 0 }, { '2026-10-07', 2 }, { '2026-10-08', 0 }]` (dia fora da janela ignorado).
- [ ] **Step 2: vermelho.** `npx vitest run src/domain/click-stats.test.ts` → FAIL: módulo inexistente.
- [ ] **Step 3: delegar.** Spec §5.9 mais os ajustes da linha 5.9 da tabela "Ajustes na spec".
- [ ] **Step 4–7:** ciclo padrão. Commit: `feat(domain): agrega as estatísticas com a janela de 30 dias em Brasília`

### Task 18: `LinkService.getManagementView`

**Quem:** Opus testa → executor implementa. **QA:** não.

**Contexto:** `manage-page.md`, `security-token.md`, spec §5.7 (`getManagementView`), §5.9.

**Files:**
- Test: `src/domain/link-service.management-view.test.ts`
- Modify: `src/domain/link-service.ts`

**Interfaces:**
- Produces: `ManagementView` (§5.7); `LinkService.getManagementView(manageToken: string): Promise<ManagementView | null>`.

- [ ] **Step 1: teste** (fakes da Tarefa 14; `now = 2026-10-08T15:00:00.000Z`):
  - formato inválido → `null`, e nenhum repositório é chamado;
  - token no formato, inexistente → `null`;
  - link criado em `2026-09-01T15:00Z` com estatísticas programadas → todos os campos do snapshot, `state 'active'`, e `getStats` chamado com `(id, 2026-09-09T03:00:00.000Z)` (início do `fromDay` em Brasília); `stats` igual ao `buildClickStats` dos mesmos dados;
  - link esgotado → `state 'exhausted'`; desativado → `'deactivated'`.
- [ ] **Step 2: vermelho.** `npx vitest run src/domain/link-service.management-view.test.ts` → FAIL: `getManagementView is not a function`.
- [ ] **Step 3–7:** ciclo padrão. Commit: `feat(domain): monta a visão de gestão pelo hash do token`

### Task 19: CI no GitHub Actions

**Quem:** Opus (setup). **QA:** não.

**Contexto:** `architecture-testing-ci.md` (CI), `security-core.md` (CI sem segredos), spec §9.10.

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1:** buscar o SHA da release mais recente de cada ação: `git ls-remote --tags https://github.com/actions/checkout` e `.../actions/setup-node`, usando o commit desreferenciado (`^{}`) da tag `vX.Y.Z` mais alta. Conferir no GitHub (página da release) que o SHA é o da tag. Anotar no ledger.
- [ ] **Step 2:** `ci.yml` da §9.10, com a `<MAJOR>` do Neon, os dois SHAs (versão no comentário) e o job chamado `ci`.
- [ ] **Step 3 (verificação local):** a mesma sequência do CI, do zero: `npm ci && npm run db:migrate:test && npm run lint && npm run typecheck && npm test && npm run test:http`.
- [ ] **Step 4:** pausa com o Rafael (o que cada passo do YAML faz; por que o SHA; o que é *service container*). **Push da branch só com a autorização dele**; depois, acompanhar com ele a aba Actions até o ✓. Commit:
  `ci: roda lint, tipos, testes e testes HTTP com Postgres a cada push`

### Task 20: Vercel, Neon, Upstash, ruleset e Deployment Checks

**Quem:** Rafael nos painéis, com o Opus guiando; Opus escreve o `vercel.json`. **QA:** não.

**Contexto:** `architecture-persistence.md` (RC1, S1), `architecture-testing-ci.md` (publicação), `security-rate-limit.md` (RC4, previews), `security-blocklist.md`, spec §9.6, §9.11.

**Files:**
- Create: `vercel.json` (§9.6)

- [ ] **Step 1:** `vercel.json`; commit `build(vercel): aplica as migrations no build da Vercel` (com autorização).
- [ ] **Step 2 (Rafael):** importar o repositório na Vercel (Node 24.x, região da função = região do Neon); Neon-Managed Integration com "Automatically delete obsolete Neon branches"; `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN` e `SAFE_BROWSING_API_KEY` em **Production e Preview**; Standard Protection ligada.
- [ ] **Step 3 (verificação do preview da branch):** o build roda o `prisma migrate deploy` na branch `preview/feat/mvp-1-base` do Neon (log do build); a home abre logado; numa janela anônima, o preview pede login da Vercel (RC1 e RC2; anotar quais `*.vercel.app` abrem sem login).
- [ ] **Step 4 (Rafael):** Deployment Checks com o job `ci` (provider GitHub); ruleset na `main` exigindo o job `ci`, sem aprovação de revisor.
- [ ] **Step 5:** pausa: o que cada painel faz e que trava protege o quê.

### Task 21: Fim da fatia: QA, revisão da branch e primeira PR

**Quem:** Opus e Rafael juntos. **QA:** sim (passada de fim de fatia, D5 e D6d). Áreas: **headers e páginas**.

- [ ] **Step 1: QA da fatia** (`npm run dev` com falsos e Docker; fingerprint antes e depois): home, página inexistente, headers e console.
- [ ] **Step 2: revisão da branch inteira** (D5), junto com o Rafael: `git diff main...feat/mvp-1-base --stat` e arquivo por arquivo, com o checklist D7 aplicado à branch. Conferir os requisitos RF02, RF03, RF04, RF12 (regras), RF14 (travas), RNF03, RNF04, RNF06, RNF07, RNF08 e RNF10 da §16.
- [ ] **Step 3: documentação.** Marcar como `Implementado` na §16 da spec os requisitos que esta fatia fecha (RNF06, RNF07, RNF08 e RNF10; os outros dependem das fatias 2 e 3); registrar na spec o que as tarefas mudaram no "como" (🔎); atualizar o `HANDOFF.md`; anotar as "Versões escolhidas" abaixo.
- [ ] **Step 4: primeira PR, em conjunto** (o Rafael nunca usou PR): ele abre pelo site do GitHub (`feat/mvp-1-base` → `main`, título `feat: base do projeto, domínio completo e publicação na Vercel`), lê o "Files changed", acompanha o CI e, se algo falhar, a correção entra na mesma branch. Merge com o ✓.
- [ ] **Step 5: produção.** A Vercel publica a `main` depois do CI; `curl -I https://<produção>/` → headers globais, sem `X-Powered-By`, e **HSTS** presente (RC6; anotar o valor).
- [ ] **Step 6: Deployment Checks retêm o `*.vercel.app`?** (spec §9.11; ação na `main`, **só com autorização explícita do Rafael**): desligar o ruleset; push na `main` de um commit com um teste que falha de propósito; confirmar que o endereço de produção continua servindo a versão anterior; `git revert` e push; confirmar a publicação; religar o ruleset. Registrar o resultado no `architecture-testing-ci.md` ("A confirmar no setup").
- [ ] **Step 7:** apagar a branch remota (a integração do Neon apaga a branch do banco); conferir no Neon que a `preview/feat/mvp-1-base` sumiu.

## Versões escolhidas

Preenchido na Tarefa 1 (Step 4), com a data da consulta ao `npm view`.

| Pacote | Versão | Data |
|---|---|---|
| — | — | — |
