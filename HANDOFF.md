# short-url — Handoff

**Atualizado em:** 2026-10-03 · **Versões anteriores:** `git log -- HANDOFF.md` (a longa, com o histórico detalhado das sessões de design, é `git show a944166:HANDOFF.md`)

**Fase:** design pelo **caminho arquitetural** do `superpowers:brainstorming`. **Nenhum código escrito, de propósito.** O hard-gate só libera código depois de: spec escrita e aprovada → os **três planos** (`superpowers:writing-plans`, um por fatia) aprovados. O método de execução **já foi escolhido: inline** (ver "Fatias e execução").

**Próxima etapa:** decidir os **achados da releitura crítica**, um por mensagem, na ordem **RC1** → RC2 → RC4 → RC5 → RC3 → RC6 → RC7 a RC10 → baixos em bloco (ver "Pendências") → só então **escrever a spec**, quando o Rafael liberar → revisão do Rafael → **três planos**. A etapa 1 do harness (quebra dos arquivos de contexto) foi **concluída em 2026-10-03**.

## Como retomar

1. `git status -sb` deve mostrar `main...origin/main` limpo. Se não estiver, pergunte ao Rafael antes de mexer.
2. Invoque `superpowers:brainstorming` (caminho arquitetural, etapa "apresentar o design em seções").
3. **As regras agora estão quebradas por assunto.** A sessão já carrega o núcleo (`AGENTS.md`, `architecture-layers`, `security-core`, `code-style`). **Antes de propor algo sobre um tema, leia os arquivos que o índice do `AGENTS.md` aponta para ele.** Este HANDOFF é só um índice de decisões e pendências.
4. Apresente **uma decisão por mensagem** no formato de "Como apresentar decisões". Ao fechar, registre **na hora** no arquivo-fonte (o da tabela "Fontes da verdade") e marque aqui.
5. **Commite e dê push ao fim de cada bloco de decisões**, com autorização do Rafael na mensagem. Um Ctrl+Z no editor já apagou trabalho não commitado.
6. Regras do harness ao editar: cada arquivo com **no máximo 12 mil caracteres**; arquivo novo de regra sob demanda leva `trigger: model_decision` + `description` e entra no índice do `AGENTS.md`, **sem link** em `.claude/rules/` (só o núcleo tem link); detalhe de implementação novo vai marcado **[→ spec]** (critério em `spec-workflow.md`, §8).

## Prazo (decidido em 2026-09-30)

- A semana de trabalho **começa quando a spec e os três planos forem aprovados**. O design não conta.
- O Rafael dedica **no máximo 4 a 5 horas por dia**.
- **Nenhum corte de escopo:** todas as decisões foram pensadas para um MVP justo, honesto e bem documentado. Se o prazo apertar, as fatias garantem que sempre há uma versão no ar.
- Estimativa (não oficial): 28 a 35 h no total, ou 6 a 8 dias de 4 a 5 h. O que mais pesa é criar as contas, instalar o Docker, revisar os PRs e entender o código, e não escrever código.

## Fatias e execução (decidido em 2026-10-01)

**Três fatias, cada uma com plano, branch e PR próprios** (fonte: `code-style.md`, "Branches e fatias"):

| Fatia | Branch | Entrega | No ar ao final |
|---|---|---|---|
| 1. Base | `feat/mvp-1-base` | Setup, Docker, CI, ruleset, Vercel, Neon e o domínio com testes | Página inicial + CI verde; **primeira PR, feita em conjunto** |
| 2. Criar e redirecionar | `feat/mvp-2-create-redirect` | Criação (Google e rate limit), redirect, teste de concorrência e testes HTTP | Dá para encurtar e usar um link |
| 3. Gestão e entrega | `feat/mvp-3-manage` | Página de gestão (estatísticas, QR, desativar) e README | MVP completo |

- Uma spec só para o MVP, com as três branches no campo **Branch Alvo**. Três planos, um por fatia, **escritos e aprovados juntos** antes de começar: é aí que a semana começa.
- A spec e os planos vão direto na `main` (documentação, antes do ruleset).
- **Cada tarefa dos planos lista os arquivos de contexto que precisa ler** (decisão do harness: o plano é o gatilho do carregamento sob demanda).

**Execução inline, com o Rafael acompanhando cada tarefa** (`superpowers:executing-plans`):
- O agente implementa as tarefas do plano na própria conversa, uma por vez, com TDD (teste falhando → código → teste passando → commit), na branch da fatia.
- **Ajuste pedido pelo Rafael:** a skill manda executar todas as tarefas sem parar, mas a instrução dele tem precedência. **Ao fim de cada tarefa, pausa curta** com o que foi feito, o teste que falhou e depois passou, e o commit. Ele responde e a próxima tarefa começa.
- **Comentários inline durante a implementação (pedido em 2026-10-02):** a cada etapa, explicar no próprio fluxo **como a peça se encaixa nas decisões** (ex.: ao criar o `.env.example`, por que o destino é o `.env.development.local` e como as duas travas agem; ao escrever o ponto de montagem, onde entram os falsos). O Rafael quer acompanhar todas as etapas e entender o encaixe na prática, não só o resultado.
- O progresso fica num *ledger* em `.superpowers/sdd/<plano>/progress.md` (ignorado pelo Git), que permite retomar depois de uma compactação de contexto ou de uma sessão nova sem refazer tarefa.
- **Pendente (decidir na fatia 1, junto com a etapa 2 do harness):** quem faz a **revisão final de cada fatia**. A skill pede um revisor com contexto novo antes do PR: um subagente no modelo mais capaz ou o Antigravity CLI (`agy -p`), que o `CLAUDE.md` global já indica para revisão de código.

## Goal

Encurtador de links com analytics: o primeiro projeto do portfólio full-stack do Rafael, em cerca de 1 semana, em Node.js/TypeScript, para diversificar a stack antes dos projetos em Java/Spring (IAM e CRM; roadmap em `~/Projetos/portfolio-roadmap.txt`). Escopo, fora de escopo e critério de "pronto" estão no PRD.

## Fontes da verdade (estrutura nova, 2026-10-03)

**Núcleo** (carregado em toda sessão; ~20,7 mil caracteres):

| Arquivo | Conteúdo |
|---|---|
| `AGENTS.md` | Projeto em um parágrafo, **glossário**, como as regras são carregadas e o **índice "ao mexer em X, leia Y"**. O Antigravity lê nativamente; o `CLAUDE.md` só faz `@AGENTS.md` |
| `.agents/rules/architecture-layers.md` | Camadas (`app`, `domain`, `data`, `infra`), árvore de pastas, **decisões não negociáveis** |
| `.agents/rules/security-core.md` | Superfície de risco, ameaças e mitigações, política (segredos, falsos só no dev, CI sem segredos, publicação protegida), **IP não persistido** |
| `.agents/rules/code-style.md` | Lint, kebab-case, Conventional Commits (descrição em pt-BR), branches e fatias, Pull Requests |

**Sob demanda** (lidos quando o índice do `AGENTS.md` aponta):

| Arquivo | Conteúdo |
|---|---|
| `.agents/rules/architecture-stack.md` | **Baseline de versões** (Node 24, Next 16.3.8, Prisma 7.10.0, TS 6.0.3), npm endurecido, framework, Upstash, Safe Browsing, `qrcode@1.5.4` |
| `.agents/rules/architecture-persistence.md` | Neon pooled/direct, **env da CLI do Prisma (`@next/env`)**, driver adapter e timeouts do pool |
| `.agents/rules/architecture-testing-ci.md` | Vitest, Postgres em Docker, testes HTTP, **CI**, deploy e **publicação só com CI verde** |
| `.agents/rules/architecture-local-dev.md` | **`npm run dev` sem chaves**: `USE_LOCAL_FAKES` no `.env.development.local`, falsos e as duas travas |
| `.agents/rules/security-token.md` | Hash SHA-256 e formato do token, **vazamentos do token** |
| `.agents/rules/security-rate-limit.md` | **Números do rate limit**, `/64` no IPv6, rate limiter indisponível |
| `.agents/rules/security-blocklist.md` | Safe Browsing: privacidade, custo, cota, API key, indisponibilidade, mensagem |
| `.agents/rules/spec-workflow.md` | Formato de spec, plano, ADR e índice de specs; **§8 regra × spec e o rótulo [→ spec]** |
| `.agents/context/url-validation.md` | `trim()`, **R1 a R7**, IDN |
| `.agents/context/link-lifecycle.md` | Slug e colisão, limite de cliques, expiração (P7) |
| `.agents/context/link-creation.md` | Token na criação, **contrato `CreateLinkState`**, P1 a P5, QR, fluxo de criação |
| `.agents/context/redirect.md` | Pré-validação do slug, **respostas 302/404/410/429/503**, parâmetros, **UPDATE atômico**, clique com `after()`, **bots e `HEAD`**, fluxo do redirect |
| `.agents/context/manage-page.md` | Gráfico de 30 dias, desativação irreversível e idempotente, QR na gestão, headers, fluxo de gestão |
| `.agents/context/data-model.md` | **Modelo de dados** fechado |
| `.agents/context/error-map.md` | **Mapa de erros** |
| `docs/superpowers/PRD.md` | Problema, público, escopo do MVP, fora de escopo, critério de "pronto" (inclui o conteúdo exigido do README) |
| `docs/superpowers/ADR.md` | AD-001 a AD-004. **Append-only: nunca editar** |

## Índice das decisões (onde está cada uma)

Todas debatidas com trade-offs e aprovadas pelo Rafael. **Não reabrir sem motivo novo.**

| Tema | Decisões (resumo de uma linha) | Fonte |
|---|---|---|
| Base | Next.js full-stack na Vercel (AD-001); Prisma + Neon (AD-002); sem login, token de gestão (AD-003); camadas com domínio puro (AD-004) | ADR |
| Versões e ferramentas | Node 24, **Next 16.3.8** (correções de segurança; subiu da 16.3.6 em 2026-10-02, com `eslint-config-next` junto), Prisma 7.10.0 exato, TS 6.0.3; npm 11 endurecido; `qrcode@1.5.4` mantido após avaliação (29 pacotes, 0 vulnerabilidades, `yargs` só na CLI); kebab-case; pt-BR; Conventional Commits | `architecture-stack.md`, `code-style.md`, PRD |
| Dados (D1, 10e, 2026-10-02) | `@prisma/adapter-pg` + `pg.Pool` global + `attachDatabasePool`; `idleTimeoutMillis` 5 s; `connectionTimeoutMillis` 5 s → 503; **CLI do Prisma com `loadEnvConfig` de `@next/env`** no `prisma.config.ts` | `architecture-persistence.md` |
| Modelo de dados | PKs `SERIAL`/`BIGSERIAL`; hash SHA-256 do token (`BYTEA`); sem IP; dispositivo como enum; referrer só como host; dia em `America/Sao_Paulo`; `timestamptz(3)` | `data-model.md`, `security-token.md`, `security-core.md` |
| Criação (6a a 6c, P1 a P5, P7) | R1 a R6 da URL; limite 1 a 1.000.000; expiração por duração ou fim do dia; token base64url exibido uma vez num card; QR PNG 512 px e **opcional se falhar depois de gravar (P1)**; parâmetros ignorados (P2); botão desabilitado (P3); `trim()` (P4); destaque + `beforeunload` para o link de gestão (P5); momento da expiração exibido embaixo do seletor de data (P7) | `url-validation.md`, `link-lifecycle.md`, `link-creation.md` |
| Blocklist (R7, B1 a B3) | Google Safe Browsing v5 `hashes.search`, **só na criação**, só prefixos de hash saem; porta `UrlThreatChecker`; **fail-closed** com timeout de 2 s (B1); adaptador em `src/infra/` (B2); aviso "suspeito" + "Advisory provided by Google" com link (B3) | `url-validation.md` (R7), `security-blocklist.md` |
| Redirect (7a a 7e, P2, P6) | `GET` e `HEAD` próprios; formato do slug antes de tudo; evento com `after()`; HTML fixo para 404/410/429/503; 410 com motivo; `HEAD` e bot só leem; IDN aceito | `redirect.md`, `url-validation.md` (P6) |
| Gestão (8a, 8b, 9a, 9b, P1b) | Gráfico de 30 dias; token no path + `no-referrer`/`noindex`/`no-store`; desativação irreversível com confirmação; `deactivateLink` idempotente, pelo token; QR também na página | `manage-page.md`, `security-token.md` |
| Testes (T1 a T3) | Vitest 5 em dev (T1); Postgres dos testes e do dev em Docker via `compose.yml`, porta presa ao `127.0.0.1`, `TRUNCATE` antes de cada arquivo e arquivos em série (T2); entrada fina + testes HTTP com `fetch` contra `next start` (`npm run test:http`) (T3) | `architecture-testing-ci.md` |
| CI e publicação (T4, T5) | GitHub Actions completo (lint, tipos, `npm test`, `test:http`), **sem segredos**, ações fixadas por SHA, `contents: read` (T4); **ruleset na `main`** + **Deployment Checks da Vercel** (T5) | `architecture-testing-ci.md`, `security-core.md`, `code-style.md` |
| Erros e rate limit (10a a 10d) | Upstash fora: fail-open no redirect, fail-closed na criação; 10/min + 100/dia na criação, 300/min no redirect, timeout de 1 s; chave `/64` no IPv6; até 3 tentativas em colisão de slug; mapa de erros aprovado | `security-rate-limit.md`, `link-lifecycle.md`, `error-map.md` |
| `npm run dev` sem chaves (2026-10-01/02) | `USE_LOCAL_FAKES=true` no **`.env.development.local`** (só o `next dev` lê, e o Git ignora) troca Upstash e Google por falsos (o do Google marca só as URLs de teste oficiais); trava 1: só com `NODE_ENV === 'development'`; trava 2: o `next.config.ts` faz o build e o `next start` falharem com a variável ligada; chave ausente nunca ativa falso | `architecture-local-dev.md`, `security-core.md` |
| Prazo, fatias e execução (2026-09-30 e 2026-10-01) | Semana conta a partir da aprovação da spec e dos três planos, 4 a 5 h/dia, sem corte de escopo; três fatias com plano, branch e PR próprios; execução inline com pausa e comentários inline | PRD, `code-style.md`, "Fatias e execução" acima |
| Harness, etapa 1 (2026-10-02/03) | Escopo em duas etapas; corte **por assunto** (cada regra num lugar só); **núcleo sempre + índice, resto sob demanda**; `AGENTS.md` como índice único, `CLAUDE.md` = `@AGENTS.md`, links em `.claude/rules/` **só para o núcleo**; máximo de 12 mil caracteres por arquivo; **regra = o quê e por quê, spec = como** (rótulo [→ spec]) | "Harness" abaixo, `AGENTS.md`, `spec-workflow.md` §8 |

**Defeitos corrigidos:** o SQL atômico não checava `deactivated_at` (2026-09-30, `redirect.md`); o `USE_LOCAL_FAKES` estava no `.env.local`, que o `next build` também lê (2026-10-02, corrigido para `.env.development.local`).

## Harness

**Etapa 1 — concluída em 2026-10-03** (commit `docs(harness): quebra as regras por assunto…`):
- `architecture.md`, `security.md` e `domain.md` foram quebrados nos arquivos da tabela "Fontes da verdade", **movendo blocos inteiros sem reescrever o texto**. A conferência por script mostrou que todas as 415 linhas originais existem nos arquivos novos, exceto 14 cabeçalhos e a numeração dos três fluxos, removidos de propósito. Os originais estão no histórico do Git.
- O glossário foi para o `AGENTS.md`. As referências cruzadas foram atualizadas e verificadas por script.
- Trechos de implementação (SQL, tipos, pseudocódigo, `updateManyAndReturn`, `date_trunc`, conversão de fuso) estão marcados **[→ spec]** em `.agents/context/`. Na escrita da spec, eles são **movidos** para ela, e detalhes curtos em linha sem rótulo também são triados (`spec-workflow.md`, §8).
- **Medição com `claude -p`** (sessão nova no projeto, mesmo modelo): **65.459 → 39.073 tokens** de entrada. A parte global (CLAUDE.md do usuário, hooks) é ~31,5 mil; a do projeto caiu de ~34 mil para ~7,5 mil (~78% a menos). O agente respondeu certo usando o glossário e o índice.
- **Fatos verificados que sustentam a estrutura:**
  - **Claude Code** (teste empírico em diretório descartável, 2026-10-03): carrega os links de `.claude/rules/` (+7,3 mil tokens com uma regra de teste); o `@import` também carrega; com os dois juntos, o arquivo entra **uma vez só**; o frontmatter `trigger:` do Antigravity não atrapalha. Lê `AGENTS.md` quando o `CLAUDE.md` o importa (doc "How Claude remembers your project").
  - **Antigravity** (doc oficial via `agy`): lê `AGENTS.md` (sempre ativo) e não lê `CLAUDE.md`; `.agents/rules/` sem subpastas, com `trigger: always_on | model_decision | glob | manual`; o editor mostra limite de 12 mil caracteres por regra (a doc fala em truncar acima de 24 KB, e as regras `always_on` dividem um teto de 20 mil tokens); subagentes em `.agents/agents/`; skills em `.agents/skills/`; hooks em `.agents/hooks.json`; workflows descontinuados em 01/11/2026.
- A estrutura veio da skill do Rafael `novo-projeto` (`~/.agents/skills/novo-projeto`, repositório `ribeirorafadev/estrutura-pastas-superpowers`). **Sugestão sem prazo:** levar para a skill o padrão de núcleo + índice no `AGENTS.md` e os links só para o núcleo. Hoje ela gera o `CLAUDE.md` importando as mesmas regras que os links já carregam.

**Etapa 2 — durante as fatias, em marcos** (não antecipar):
- **Hooks na fatia 1**, quando existirem `lint`, `typecheck` e `test`. Carregar a skill `update-config`. Candidato: medir o limite de 12 mil caracteres dos arquivos de `.agents/` a cada edição.
- **Agente revisor de fatia na fatia 1**, junto com a pendência "quem revisa" (subagente ou `agy -p`). Formatos: `.claude/agents/<nome>.md` e `.agents/agents/<nome>.md`.
- **Skills** só quando uma tarefa ou um erro se repetir, seguindo a `superpowers:writing-skills` ("no skill without a failing test first").
- `paths:` (Claude) ou `glob` (Antigravity) só para um arquivo que o agente comprovadamente deixe de ler.

## Pendências

**Achados da releitura crítica (2026-10-02, aguardando decisão, um por mensagem).** Ordem aprovada: RC1 → RC2 (ambientes da Vercel) → RC4 → RC5 ("falta algo") → RC3 → RC6 → RC7 a RC10 → baixos em bloco. Cada decisão é gravada no arquivo novo correspondente.
- **Altos (decisão nova):**
  - **RC1. Migrations em produção e banco dos previews:** ninguém definiu quem roda `prisma migrate deploy` no Neon, nem se os *previews* da Vercel usam o banco de produção. Ligado ao `@next/env`: uma variável definida no shell não é sobrescrita, então dá para apontar a CLI para outro banco na linha de comando. Fontes prováveis: `architecture-persistence.md`, `architecture-testing-ci.md`.
  - **RC2. Origem canônica:** `shortUrl`, `manageUrl` e a R3 dependem do "domínio próprio por configuração", mas nenhuma variável foi definida (nem no `.env.example`), e o app responde em vários hosts `*.vercel.app` (um por deploy), o que permite contornar a R3. Fontes: `url-validation.md` (R3), `link-creation.md`.
  - **RC3. SQL escrito à mão no gráfico diário:** o `date_trunc(... AT TIME ZONE 'America/Sao_Paulo')` não cabe na API de consulta do Prisma; definir se `$queryRaw` com template parametrizado (ou TypedSQL) é permitido pela regra "nada de SQL por concatenação" (`architecture-layers.md`). Fonte: `data-model.md`.
  - **RC4. Chave ausente em produção e no `test:http`:** se o cliente do Upstash ou do Google lançar exceção ao carregar o módulo, o redirect vira 500 em vez de fail-open. Regra proposta: configuração ausente = "serviço indisponível", checada na chamada. Fontes: `security-rate-limit.md`, `security-blocklist.md`.
  - **RC5. IP ausente:** o `ipAddress` de `@vercel/functions` lê `x-real-ip` (o `security-rate-limit.md` fala em `x-forwarded-for`), aceita `Request | Headers` (funciona com `headers()` na Server Action) e devolve `undefined` fora da Vercel. Falta o comportamento: criação fail-closed? Redirect segue? E no `npm run dev`?
  - **RC6. Headers de segurança globais** (CSP, `X-Content-Type-Options`, `frame-ancestors`) nunca foram decididos. Fonte: `security-core.md`.
- **Médios:**
  - **RC7.** Ordem de validação na criação: `maxClicks` e `expiration` não aparecem no fluxo de `link-creation.md`; validar todos os campos locais antes de consultar o Google (não gasta cota e mostra todos os erros de uma vez).
  - **RC8.** Fonte do "total de cliques" no dashboard: `click_count` ou contagem de eventos (podem divergir).
  - **RC9.** `BOT` no gráfico diário e evento de bot em link 404/410: não definidos.
  - **RC10.** A R4 não pega domínio público que aponta para IP privado (`127.0.0.1.nip.io`, `localtest.me`), porque o servidor não resolve DNS: documentar ou bloquear. IPv6 literal público (`[2001:db8::1]`) cai na regra "host sem ponto".
- **Baixos (clareza na spec, sem decisão):** relógio (`now()` do banco × `new Date()` da função no Prisma); gravar `url.href` normalizado; regex de bots ancorada (`^WhatsApp/`); corrigir o texto do `x-forwarded-for` no `security-rate-limit.md`; rota estática de 7 letras (`/privacy`) sombrearia um slug igual (chance desprezível).

**Pendências de setup (anotadas, sem decisão aberta):**
- Instalar o Docker na máquina do Rafael (hoje não há Docker nem Postgres) e escolher entre `sudo` e o modo *rootless*, porque o grupo `docker` equivale a root.
- Definir a versão major do Postgres ao criar o projeto no Neon (14 a 18); o `compose.yml` usa a mesma.
- Ativar o ruleset da `main` e os Deployment Checks na fatia 1, junto com o CI, e confirmar com um commit que falha de propósito que o `*.vercel.app` também fica retido.
- **Primeira PR feita em conjunto (combinado em 2026-09-30):** o Rafael nunca trabalhou com PR. A primeira PR, a da fatia 1 (`feat/mvp-1-base`), é feita **junto com ele, passo a passo**: abrir pelo site do GitHub (o `gh` não está instalado), ler o diff em "Files changed", acompanhar o CI e, se aparecer ✗, abrir o "Details", reproduzir localmente, corrigir na mesma branch e dar push. O ruleset exige **só o CI verde, sem aprovação**, porque o GitHub não deixa o autor aprovar o próprio PR.
- **Pré-requisito do Rafael, antes da implementação:** projeto no Google Cloud + API key **restrita à Safe Browsing API** (gratuito, sem faturamento; ver `security-blocklist.md`).

**Para a spec** (`docs/superpowers/specs/2026-XX-XX-short-url-mvp-design.md`, formato de `spec-workflow.md`):
- Consolidar o PRD, `.agents/context/` e `.agents/rules/`, com as seções `## Alternativas consideradas…` e `## Requisitos rastreados` (RF/RNF). Na tabela de requisitos, a coluna de task aponta para o plano da fatia correspondente.
- **Mover para a spec os trechos [→ spec]** de `.agents/context/` e deixar no lugar uma referência à seção da spec; triar também detalhes curtos em linha (`spec-workflow.md`, §8).
- Cabeçalho: **Branch Alvo** com as três branches das fatias.
- **Plano de testes** (T1 a T3 já decididos):
  - domínio com fakes em memória (`LinkRepository`, `UrlThreatChecker`, rate limiter);
  - funções puras com testes de tabela: `isValidSlugFormat`, `isPreviewBot`, classificação de dispositivo, host do referrer, normalização do IP para `/64`, formato do token, precedência do motivo do 410, `trim()`, conversão do "fim do dia" com o offset de `America/Sao_Paulo` e a **canonicalização do Safe Browsing** (com os exemplos da doc do Google);
  - teste de concorrência do limite de cliques com Postgres real (Docker);
  - testes HTTP: 302/404/410, `no-store`, `HEAD` sem incremento e headers da página de gestão.
- **Duas notas sobre o AD-004**, que não pode ser editado: o QR saiu do domínio para a entrada (o AD-004 ainda cita `QrCodeGenerator`), e os adaptadores ganharam `src/infra/` além de `src/data/`. Nenhuma das duas passa no critério de ADR.
- Setup:
  - `.npmrc` (`save-exact`, `min-release-age=1`, `strict-allow-scripts`) e `allowScripts` (revisar a cada dependência nova);
  - lint `import/no-extraneous-dependencies` e a candidata `no-restricted-imports` (domínio não importa `next/*`, `@/data/*` nem `@/infra/*`);
  - `engines.node`, script `prisma generate && next build`;
  - `.env.example` (copiado para `.env.development.local`) com `USE_LOCAL_FAKES=true`, `DATABASE_URL` do `compose.yml`, `DIRECT_URL`, os tokens do Upstash e `SAFE_BROWSING_API_KEY` em branco (+ a variável da origem canônica, se o RC2 a criar);
  - `prisma.config.ts` chamando `loadEnvConfig(process.cwd(), true)` de `@next/env` (`devDependency` explícita, na versão do `next`);
  - `next.config.ts` exportado como função de `phase`, com a trava do `USE_LOCAL_FAKES`;
  - `compose.yml` (Postgres), `vitest.config.mts` (`resolve.tsconfigPaths`, `fileParallelism: false`), scripts `test`, `test:http`, `lint` e `typecheck`;
  - workflow do CI em `.github/workflows/` (ações por SHA, `permissions: contents: read`, Postgres como *service container*);
  - instalar sempre com versão explícita.
- Nota: o Prisma 8 renomeia `updateManyAndReturn` para `updateAll()` (o projeto fixa o 7).
- Adicionar a linha da spec em `docs/superpowers/specs/README.md`, fazer a autorrevisão e pedir a revisão do Rafael.

**Depois da spec aprovada:** seção RF/RNF no Excalidraw → `superpowers:writing-plans` para os **três planos** (um arquivo por fatia em `docs/superpowers/plans/`, cada um com a sua **Branch de Trabalho** e, em cada tarefa, os arquivos de contexto a ler) → revisão do Rafael → execução inline da fatia 1. A spec e os planos são commitados direto na `main`.

**Limitações já documentadas** (não são pendências; entram na spec e no README): scanners de e-mail consomem links com limite; iPad aparece como DESKTOP; `click_count` pode divergir dos eventos; logs da Vercel e histórico guardam o token; a blocklist não pega golpe novo nem site que vira golpe depois; resposta perdida na rede perde o token.

## Excalidraw (documentação visual, no navegador do Rafael)

- **Estado (revisado pelo Rafael em 2026-10-01, sem correções):** 5 seções (REGRAS DE NEGÓCIO, STACKS, SYSTEM DESIGN, MODELO DE DADOS, ENTREGA (CI/CD)), **125 elementos**. Backup da versão anterior (93 elementos) em `excalidraw-backup-<ts>` no `localStorage`. Não exportado para o repositório. É o **resumo visual**; a verdade são os `.md`.
- **Pendente:**
  - **melhorar a visualização no futuro** (pedido do Rafael em 2026-10-01, sem prazo e sem urgência);
  - a caixa "git push na branch (ex.: feat/mvp)" da seção ENTREGA ficou desatualizada com as fatias: trocar por `feat/mvp-1-base` na próxima edição pedida pelo Rafael;
  - STACKS ainda mostra Next 16.3.6 se a versão aparecer lá: conferir na próxima edição;
  - seção RF/RNF só depois da spec aprovada;
  - no fim, o Rafael exporta (`.excalidraw` + SVG) para `docs/`.
- **Protocolo de edição (via localStorage, claude-in-chrome), só quando o Rafael pedir na própria mensagem:**
  1. ele fecha todas as abas do excalidraw.com;
  2. o agente abre uma aba, sem interagir com o canvas, e confere a contagem de elementos;
  3. faz backup em `excalidraw-backup-<ts>` e grava `excalidraw` + `version-dataState`;
  4. fecha a aba e só então avisa o Rafael.
- **Armadilhas:**
  - identificar elementos por texto exato, nunca por posição ou prefixo;
  - não imprimir IDs (o filtro de saída bloqueia);
  - aba em segundo plano não renderiza (sem screenshot ou clique);
  - a contagem cai quando o Excalidraw descarta elementos `isDeleted`;
  - a saída do `javascript_tool` é **bloqueada** quando o texto tem `=`, `?` ou `&` (parece query string) e **cortada** perto de 1.000 caracteres: ler em partes e trocar esses caracteres por espaço só na leitura, nunca na escrita;
  - fluxo que funcionou: ensaio em memória (`window.__newScene`, com asserts de contagem e largura) → gravação conferindo que a cena não mudou desde o ensaio → fechar a aba → reabrir e conferir;
  - o classificador **nega** neutralizar o `Storage.prototype.setItem` e nega gravar sem pedido explícito: nunca tente rotas alternativas.

## Como apresentar decisões (o que funcionou)

- **Formato aprovado:**
  1. um **cenário concreto** ("a Maria clica num link que expirou…");
  2. cada opção A/B/C em **1–2 frases** com uma **mini linha do tempo**;
  3. uma **tabela curta sem jargão**;
  4. a recomendação em poucas linhas e uma fonte numa linha.

  Verificação de fontes e roteiros ficam **fora** da mensagem.
- Quando o Rafael pede "explique mais a fundo" ou "explique melhor o cenário de uso": uma **analogia do cotidiano** (crachá × gaveta, regulamento do condomínio × planta da casa, extintor de treino), depois **situações numeradas** com as opções lado a lado, depois uma **tabela situação × opção** com ✓/✗. Ele pede isso porque está aprendendo, não como crítica.
- Analogias com Java/Spring (JDBC, HikariCP, `@Async`, `@Profile("dev")`, `application.properties` × `application-dev.properties`) funcionam bem.
- **Tema abstrato (harness, estrutura de arquivos): mostrar a árvore de pastas e exemplos encurtados dos arquivos.** Foi o que destravou a decisão da estrutura em 2026-10-03.
- **Toda decisão diz de onde veio** ("isto surgiu quando…") antes das opções. Uma decisão que nasceu de uma frase de passagem ("o detalhe de implementação vai para a spec") confundiu o Rafael até ser explicada desde a origem.
- **Verificar antes de afirmar:** context7 para bibliotecas, firecrawl para docs e termos (Vercel, Neon, Google, MDN, RFCs), `npm view` para versões e peers, `agy -p` para docs do Antigravity. **Comportamento de ferramenta se mede** (ex.: `claude -p --output-format json` comparando `usage` em diretório descartável). Números não oficiais são sinalizados como tal.
- Quando surge algo fora da pauta (ex.: a blocklist), fazer um **relatório com varredura dos arquivos** antes de decidir.
- **Tecnologia que o Rafael nunca usou** (Docker, Neon, CI, PR): antes das opções, explicar cada peça com uma analogia e separar sempre **o que roda em produção** do **que roda no computador dele**.

## O que não funcionou (não repetir)

- **Mensagem de decisão densa**, com jargão ("CTE", "waitUntil") em células cheias. Resposta do Rafael: "não entendi nada… verbosa, confusa".
- **Deixar edições sem commit**: um Ctrl+Z desfez parte do `domain.md` em 2026-09-30, e tudo foi refeito pelo histórico da conversa.
- **Terminar um turno sem resposta**: o Rafael acha que perdeu perguntas.
- Afirmar texto de aviso sem checar os termos do provedor: o primeiro texto proposto para a R7 ("identificado como perigoso") violava os termos do Google.
- **Afirmar comportamento de ferramenta sem medir:** em 2026-10-02 eu disse que os links de `.claude/rules/` "não faziam nada" com base só no `/memory`; o teste mostrou que eles carregam (só eram redundantes com os imports). O Rafael, autor da skill que os cria, ficou com razão em estranhar.
- **Registrar uma decisão sem testar o ciclo inteiro:** a primeira versão do `npm run dev` sem chaves (variável no `.env.local`) quebraria o `test:http` local; o defeito apareceu só ao revisar a ordem de leitura dos `.env` do Next.

## Repositório

- Público: https://github.com/ribeirorafadev/url-shortener (`origin` via SSH, já autenticado como `ribeirorafadev`). `main` só com commits de documentação, feitos direto na `main` durante o design. Com o setup (CI + ruleset), a `main` passa a aceitar só PR com ✓.
- **Push só com autorização explícita do Rafael na mensagem.** Commits seguem `code-style.md`, com o trailer do Claude.
- Tudo o que é commitado fica público, inclusive este arquivo: nunca registrar segredos. `gh` e a CLI `vercel` não estão instalados.
- README ainda não existe; o completo é entrega do PRD.

## Preferências do Rafael

- pt-BR, direto, Markdown estruturado, **negrito** em termos críticos; decisão não trivial com fonte real (doc oficial, RFC, lei, OWASP).
- Quer entender os trade-offs antes de decidir. Nunca apresentar decisão como fato consumado.
- Depois de fechar uma decisão, às vezes pede **"explique melhor o cenário de uso das opções"** antes de registrar: é para aprender, não é dúvida sobre a escolha. Registrar só quando ele liberar.
- Na implementação, quer **comentários inline** explicando o encaixe de cada peça (ver "Fatias e execução").
- Ao fechar um bloco, pede **varredura de todos os arquivos afetados + atualização + HANDOFF + commit/push**.
- Base em Java/Spring e segurança; estuda harness e mantém a própria skill de estrutura de projetos (`novo-projeto`); está aprendendo Next.js, ORM e serverless. Nunca usou Docker, Neon, CI nem PR (explicados em 2026-09-30). Quer **acompanhar cada tarefa** da implementação, porque o projeto também é aprendizado e ele precisa explicar cada parte numa entrevista.
- Ação destrutiva: relatório primeiro (o quê, onde, risco), autorização depois.
- Pode acionar o Antigravity CLI (`agy -p "..."`) para pesquisa web e revisão.
