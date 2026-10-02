# short-url — Handoff

**Atualizado em:** 2026-10-02 · **Versão longa anterior:** `git show a944166:HANDOFF.md` (histórico detalhado das sessões)

**Fase:** design pelo **caminho arquitetural** do `superpowers:brainstorming`. **Nenhum código escrito, de propósito.** O hard-gate só libera código depois de: spec escrita e aprovada → os **três planos** (`superpowers:writing-plans`, um por fatia) aprovados. O método de execução **já foi escolhido: inline** (ver "Fatias e execução").

**Próxima etapa (2026-10-02):** o Rafael revisa os arquivos e volta → fechar os **três pontos** (Next, `qrcode`, env da CLI do Prisma) → decidir os **achados da releitura crítica** → **debate do harness** (agentes, skills, templates, hooks, quebra dos arquivos de contexto) → só então **escrever a spec** → revisão do Rafael → **três planos** → revisão do Rafael → começa a semana de implementação pela fatia 1. Fechados: cenários P1 a P7, testes e CI (T1 a T5), prazo, fatias, método de execução e `npm run dev` sem chaves (arquivo `.env.development.local`). **Não escrever a spec antes de o Rafael liberar.**

## Como retomar

1. `git status -sb` deve mostrar `main...origin/main` limpo. Se não estiver, pergunte ao Rafael antes de mexer.
2. Invoque `superpowers:brainstorming` (caminho arquitetural, etapa "apresentar o design em seções").
3. **As decisões estão nos arquivos-fonte, não aqui.** Este documento é um índice: leia a fonte indicada antes de propor algo sobre um tema.
4. Apresente **uma decisão por mensagem** no formato de "Como apresentar decisões". Ao fechar, registre **na hora** no arquivo-fonte e marque aqui.
5. **Commite e dê push ao fim de cada bloco de decisões**, com autorização do Rafael na mensagem. Um Ctrl+Z no editor já apagou trabalho não commitado.

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

**Execução inline, com o Rafael acompanhando cada tarefa** (`superpowers:executing-plans`):
- O agente implementa as tarefas do plano na própria conversa, uma por vez, com TDD (teste falhando → código → teste passando → commit), na branch da fatia.
- **Ajuste pedido pelo Rafael:** a skill manda executar todas as tarefas sem parar, mas a instrução dele tem precedência. **Ao fim de cada tarefa, pausa curta** com o que foi feito, o teste que falhou e depois passou, e o commit. Ele responde e a próxima tarefa começa.
- **Comentários inline durante a implementação (pedido em 2026-10-02):** a cada etapa, explicar no próprio fluxo **como a peça se encaixa nas decisões** (ex.: ao criar o `.env.example`, por que o destino é o `.env.development.local` e como as duas travas agem; ao escrever o ponto de montagem, onde entram os falsos). O Rafael quer acompanhar todas as etapas e entender o encaixe na prática, não só o resultado.
- O progresso fica num *ledger* em `.superpowers/sdd/<plano>/progress.md` (ignorado pelo Git), que permite retomar depois de uma compactação de contexto ou de uma sessão nova sem refazer tarefa.
- **Pendente (decidir antes da fatia 1):** quem faz a **revisão final de cada fatia**. A skill pede um revisor com contexto novo antes do PR: um subagente no modelo mais capaz ou o Antigravity CLI (`agy -p`), que o `CLAUDE.md` global já indica para revisão de código.

## Goal

Encurtador de links com analytics: o primeiro projeto do portfólio full-stack do Rafael, em cerca de 1 semana, em Node.js/TypeScript, para diversificar a stack antes dos projetos em Java/Spring (IAM e CRM; roadmap em `~/Projetos/portfolio-roadmap.txt`). Escopo, fora de escopo e critério de "pronto" estão no PRD.

## Fontes da verdade

| Arquivo | Conteúdo |
|---|---|
| `docs/superpowers/PRD.md` | Problema, público, escopo do MVP, fora de escopo (com motivos), critério de "pronto" (inclui o conteúdo exigido do README) |
| `docs/superpowers/ADR.md` | AD-001 a AD-004. **Append-only: nunca editar** |
| `.agents/rules/architecture.md` | Stack e **baseline de versões**, npm endurecido, Neon pooled/direct, **driver adapter e timeouts do pool**, **árvore de pastas** (`app`, `domain`, `data`, `infra`), **testes (Vitest, Postgres em Docker, testes HTTP)**, **CI e publicação protegida**, decisões não negociáveis |
| `.agents/rules/security.md` | Ameaças e mitigações, política de segredos, hash do token, IP não persistido, **vazamentos do token**, **números do rate limit e `/64` no IPv6**, **rate limiter indisponível**, **blocklist (privacidade, custo, cota, API key)**, **CI sem segredos e publicação protegida** |
| `.agents/context/domain.md` | Glossário, **regras R1 a R7**, limite e expiração, slug e colisão, **respostas 302/404/410/429/503**, **SQL atômico**, registro com `after()`, token e **contrato `CreateLinkState`**, QR, **bots e `HEAD`**, **fluxos passo a passo**, **modelo de dados**, **página de gestão**, **mapa de erros** |
| `.agents/rules/code-style.md` | Lint (roda no CI), kebab-case, Conventional Commits (descrição em pt-BR), branches, **Pull Requests** |
| `.agents/rules/spec-workflow.md` | Formato obrigatório de spec, plano, ADR e índice de specs |
| `CLAUDE.md` | Índice mestre que carrega os arquivos acima |

## Índice das decisões (onde está cada uma)

Todas debatidas com trade-offs e aprovadas pelo Rafael. **Não reabrir sem motivo novo.**

| Tema | Decisões (resumo de uma linha) | Fonte |
|---|---|---|
| Base | Next.js full-stack na Vercel (AD-001); Prisma + Neon (AD-002); sem login, token de gestão (AD-003); camadas com domínio puro (AD-004) | ADR |
| Versões e ferramentas | Node 24, Next 16.3.6, Prisma 7.10.0 exato (a `latest` do CLI é um RC do 8), TS 6.0.3; npm 11 endurecido; kebab-case; pt-BR; Conventional Commits | `architecture.md`, `code-style.md`, PRD |
| Modelo de dados | PKs `SERIAL`/`BIGSERIAL`; hash SHA-256 do token (`BYTEA`); sem IP; dispositivo como enum; referrer só como host; dia em `America/Sao_Paulo`; `timestamptz(3)` | `domain.md` "Modelo de dados", `security.md` |
| Criação (6a a 6c, P1 a P5, P7) | R1 a R6 da URL; limite 1 a 1.000.000; expiração por duração ou fim do dia; token base64url exibido uma vez num card; QR PNG 512 px e **opcional se falhar depois de gravar (P1)**; parâmetros ignorados (P2); botão desabilitado (P3); `trim()` (P4); destaque + `beforeunload` para o link de gestão (P5); momento da expiração exibido embaixo do seletor de data, só na tela (P7) | `domain.md` |
| Blocklist (R7, B1 a B3) | Google Safe Browsing v5 `hashes.search`, **só na criação**, só prefixos de hash saem; porta `UrlThreatChecker`; **fail-closed** com timeout de 2 s (B1); adaptador em `src/infra/` (B2); aviso "suspeito" + "Advisory provided by Google" com link (B3) | `domain.md` R7, `security.md` "Blocklist" |
| Redirect (7a a 7e, P2, P6) | `GET` e `HEAD` próprios; formato do slug antes de tudo; evento com `after()`; HTML fixo para 404/410/429/503; 410 com motivo; `HEAD` e bot só leem; IDN aceito | `domain.md` "Fluxos" e "Respostas do redirect" |
| Gestão (8a, 8b, 9a, 9b, P1b) | Gráfico de 30 dias; token no path + `no-referrer`/`noindex`/`no-store`; desativação irreversível com confirmação; `deactivateLink` idempotente, pelo token; QR também na página | `domain.md` "Página de gestão", `security.md` |
| Dados (D1, 10e) | `@prisma/adapter-pg` + `pg.Pool` global + `attachDatabasePool`; `idleTimeoutMillis` 5 s; `connectionTimeoutMillis` 5 s → 503 | `architecture.md` |
| Testes (T1 a T3) | Vitest 5 em dev (T1); Postgres dos testes e do dev em Docker via `compose.yml`, porta presa ao `127.0.0.1`, `TRUNCATE` antes de cada arquivo e arquivos em série (T2); entrada fina + testes HTTP com `fetch` contra `next start` (`npm run test:http`), sem dependência nova (T3) | `architecture.md` "Testes" |
| CI e publicação (T4, T5) | GitHub Actions completo (lint, tipos, `npm test`, `test:http`), **sem segredos**, ações fixadas por SHA, `contents: read` (T4); **ruleset na `main`** (merge só por PR com ✓) + **Deployment Checks da Vercel** (publica só com ✓), só configuração em painel (T5) | `architecture.md`, `security.md`, `code-style.md` |
| Prazo, fatias e execução (2026-09-30 e 2026-10-01) | Semana conta a partir da aprovação da spec e dos três planos, 4 a 5 h/dia, sem corte de escopo; três fatias com plano, branch e PR próprios; execução inline com pausa ao fim de cada tarefa | PRD, `code-style.md`, "Fatias e execução" acima |
| `npm run dev` sem chaves (2026-10-01; arquivo em 2026-10-02) | `USE_LOCAL_FAKES=true`, no **`.env.development.local`** (só o `next dev` lê, e o Git ignora), troca Upstash e Google por falsos locais (o do Google marca só as URLs de teste oficiais como suspeitas); trava 1: só com `NODE_ENV === 'development'`; trava 2: o `next.config.ts` faz o build e o `next start` falharem com a variável ligada; chave ausente nunca ativa falso | `architecture.md` "`npm run dev` sem chaves", `security.md` |
| Erros e rate limit (10a a 10d) | Upstash fora: fail-open no redirect, fail-closed na criação; 10/min + 100/dia na criação, 300/min no redirect, timeout de 1 s; chave `/64` no IPv6; até 3 tentativas em colisão de slug; mapa de erros aprovado | `security.md`, `domain.md` "Mapa de erros" |

**Defeito corrigido (2026-09-30):** o SQL atômico não checava `deactivated_at`. Já está corrigido em `domain.md`.

**Defeito corrigido (2026-10-02):** a primeira versão do `npm run dev` sem chaves punha o `USE_LOCAL_FAKES` no `.env.local`, que o `next build` também lê: a trava 2 quebraria o `npm run test:http` local. Corrigido para `.env.development.local`. **Releitura crítica feita em 2026-10-02:** achados em "Pendências".

## Pendências

**Três pontos a fechar (análise apresentada em 2026-10-02, aguardando o Rafael):**
1. **Baseline do Next:** a `latest` é a **16.3.8** (30/09), com correções de segurança (High: SSRF no Image Optimization, GHSA-cjq9-62q9-8jv4; Medium: cache poisoning e vazamentos de `use cache`). Recomendação: subir para 16.3.8 (e `eslint-config-next` junto).
2. **`qrcode@1.5.4`:** 29 pacotes, 2,6 MB, `npm audit` com 0 vulnerabilidades (2026-10-02), nenhum script de instalação. O código da biblioteca só importa `pngjs`, `dijkstrajs` e `fs`; o `yargs@15` é usado só pela CLI (`bin/`). Recomendação: manter. Alternativa: `qrcode-generator` (0 dependências) + codificador PNG próprio com `node:zlib` (`deflateSync` + `crc32`, nativos no Node 24).
3. **Env da CLI do Prisma:** o Prisma 7 não carrega `.env` sozinho (guia "Upgrade to Prisma ORM 7", "Environment variables"). Recomendação: `loadEnvConfig(process.cwd(), true)` de **`@next/env`** no `prisma.config.ts`. É a orientação do Next para "a root config file for an ORM" (doc "Environment Variables"), aplica as mesmas regras de precedência do `next dev` (lê o `.env.development.local`), não sobrescreve variáveis já definidas no shell e já vem como dependência do `next@16.3.8` (declarar explícito por causa do `import/no-extraneous-dependencies`). Alternativas: `dotenv` (dependência nova, lê `.env` por padrão) e `process.loadEnvFile()` nativo (precedência própria).

**Achados da releitura crítica (2026-10-02, aguardando decisão, um por mensagem):**
- **Altos (decisão nova):**
  - **RC1. Migrations em produção e banco dos previews:** ninguém definiu quem roda `prisma migrate deploy` no Neon, nem se os *previews* da Vercel usam o banco de produção.
  - **RC2. Origem canônica:** `shortUrl`, `manageUrl` e a R3 dependem do "domínio próprio por configuração", mas nenhuma variável foi definida, e o app responde em vários hosts `*.vercel.app` (um por deploy), o que permite contornar a R3.
  - **RC3. SQL escrito à mão no gráfico diário:** o `date_trunc(... AT TIME ZONE 'America/Sao_Paulo')` não cabe na API de consulta do Prisma; definir se `$queryRaw` com template parametrizado (ou TypedSQL) é permitido.
  - **RC4. Chave ausente em produção e no `test:http`:** se o cliente do Upstash ou do Google lançar exceção ao carregar o módulo, o redirect vira 500 em vez de fail-open. Regra proposta: configuração ausente = "serviço indisponível", checada na chamada.
  - **RC5. IP ausente:** o `ipAddress` lê `x-real-ip` (o `security.md` fala em `x-forwarded-for`) e devolve `undefined` fora da Vercel. Falta o comportamento: criação fail-closed? Redirect segue?
  - **RC6. Headers de segurança globais** (CSP, `X-Content-Type-Options`, `frame-ancestors`) nunca foram decididos.
- **Médios:**
  - **RC7.** Ordem de validação na criação: `maxClicks` e `expiration` não aparecem no fluxo; validar todos os campos locais antes de consultar o Google (não gasta cota e mostra todos os erros de uma vez).
  - **RC8.** Fonte do "total de cliques" no dashboard: `click_count` ou contagem de eventos (podem divergir).
  - **RC9.** `BOT` no gráfico diário e evento de bot em link 404/410: não definidos.
  - **RC10.** A R4 não pega domínio público que aponta para IP privado (`127.0.0.1.nip.io`, `localtest.me`), porque o servidor não resolve DNS: documentar ou bloquear. IPv6 literal público (`[2001:db8::1]`) cai na regra "host sem ponto".
- **Baixos (clareza na spec, sem decisão):** relógio (`now()` do banco × `new Date()` da função no Prisma); gravar `url.href` normalizado; regex de bots ancorada (`^WhatsApp/`); corrigir o texto do `x-forwarded-for` no `security.md`; rota estática de 7 letras (`/privacy`) sombrearia um slug igual (chance desprezível).

**Debate do harness (aberto em 2026-10-02):** agentes (`.agents/agents/` e `.claude/agents/`), skills, templates, hooks no `.claude/settings.json` e quebra dos arquivos de contexto. Fatos levantados:
- Tamanhos: `domain.md` 39.554 caracteres (245 linhas), `architecture.md` 22.240, `security.md` 14.940 (após o registro da C). O editor de regras do Antigravity mostra limite de 12.000 (print do Rafael); segundo a doc citada pelo `agy`, a regra é truncada acima de 24 KB, e as regras `always_on` dividem um teto de 20 mil tokens.
- O `CLAUDE.md` importa todas as regras, o `domain.md`, o PRD e o ADR em toda sessão (~100 KB). Os `.claude/rules/*.md` são links simbólicos para `.agents/rules/`, e o Claude Code carrega `.claude/rules/` sozinho: conferir com `/memory` se há carga duplicada.
- Recursos: o Claude Code tem `paths:` (regra condicional), `.claude/agents/`, `.claude/skills/` e hooks no `settings.json`. O Antigravity tem `trigger:` (`always_on`, `model_decision`, `glob`, `manual`), `.agents/agents/<nome>.md`, `.agents/skills/`, hooks em `.agents/hooks.json`, lê `AGENTS.md` e não lê `CLAUDE.md`; workflows são descontinuados em 01/11/2026 em favor de skills.

**Pendências de setup (anotadas, sem decisão aberta):**
- Instalar o Docker na máquina do Rafael (hoje não há Docker nem Postgres) e escolher entre `sudo` e o modo *rootless*, porque o grupo `docker` equivale a root.
- Definir a versão major do Postgres ao criar o projeto no Neon (14 a 18); o `compose.yml` usa a mesma.
- Ativar o ruleset da `main` e os Deployment Checks na fatia 1, junto com o CI, e confirmar com um commit que falha de propósito que o `*.vercel.app` também fica retido.
- **Primeira PR feita em conjunto (combinado em 2026-09-30):** o Rafael nunca trabalhou com PR. A primeira PR, a da fatia 1 (`feat/mvp-1-base`), é feita **junto com ele, passo a passo**: abrir pelo site do GitHub (o `gh` não está instalado), ler o diff em "Files changed", acompanhar o CI e, se aparecer ✗, abrir o "Details", reproduzir localmente, corrigir na mesma branch e dar push. O ruleset exige **só o CI verde, sem aprovação**, porque o GitHub não deixa o autor aprovar o próprio PR.

**Para a spec** (`docs/superpowers/specs/2026-XX-XX-short-url-mvp-design.md`, formato de `spec-workflow.md`):
- Consolidar PRD, `domain.md`, `security.md` e `architecture.md`, com as seções `## Alternativas consideradas…` e `## Requisitos rastreados` (RF/RNF). Na tabela de requisitos, a coluna de task aponta para o plano da fatia correspondente.
- Cabeçalho: **Branch Alvo** com as três branches das fatias.
- **Plano de testes** (T1 a T3 já decididos):
  - domínio com fakes em memória (`LinkRepository`, `UrlThreatChecker`, rate limiter);
  - funções puras com testes de tabela: `isValidSlugFormat`, `isPreviewBot`, classificação de dispositivo, host do referrer, normalização do IP para `/64`, formato do token, precedência do motivo do 410, `trim()`, conversão do "fim do dia" com o offset de `America/Sao_Paulo` e a **canonicalização do Safe Browsing** (com os exemplos da doc do Google);
  - teste de concorrência do limite de cliques com Postgres real (Docker);
  - testes HTTP: 302/404/410, `no-store`, `HEAD` sem incremento e headers da página de gestão.
- **Duas notas sobre o AD-004**, que não pode ser editado: o QR saiu do domínio para a entrada (o AD-004 ainda cita `QrCodeGenerator`), e os adaptadores ganharam `src/infra/` além de `src/data/`. Nenhuma das duas passa no critério de ADR.
- Setup:
  - `.npmrc` (`save-exact`, `min-release-age=1`, `strict-allow-scripts`);
  - `allowScripts` (revisar a cada dependência nova);
  - lint `import/no-extraneous-dependencies` e a candidata `no-restricted-imports` (domínio não importa `next/*`, `@/data/*` nem `@/infra/*`);
  - `engines.node`, script `prisma generate && next build`;
  - `.env.example` (copiado para `.env.development.local`) com `USE_LOCAL_FAKES=true`, `DATABASE_URL` do `compose.yml`, `DIRECT_URL`, os tokens do Upstash e `SAFE_BROWSING_API_KEY` em branco;
  - `prisma.config.ts` carregando as variáveis (ponto 3 acima);
  - `next.config.ts` exportado como função de `phase`, com a trava do `USE_LOCAL_FAKES`;
  - `compose.yml` (Postgres), `vitest.config.mts` (`resolve.tsconfigPaths`, `fileParallelism: false`), scripts `test`, `test:http`, `lint` e `typecheck`;
  - workflow do CI em `.github/workflows/` (ações por SHA, `permissions: contents: read`, Postgres como *service container*);
  - instalar sempre com versão explícita.
- `qrcode@1.5.4`: ver ponto 2 acima.
- Nota: o Prisma 8 renomeia `updateManyAndReturn` para `updateAll()` (o projeto fixa o 7).
- Baseline do Next: ver ponto 1 acima.
- **Pré-requisito do Rafael, antes da implementação:** projeto no Google Cloud + API key **restrita à Safe Browsing API** (gratuito, sem faturamento; ver `security.md`).
- Adicionar a linha da spec em `docs/superpowers/specs/README.md`, fazer a autorrevisão e pedir a revisão do Rafael.

**Depois da spec aprovada:** seção RF/RNF no Excalidraw → `superpowers:writing-plans` para os **três planos** (um arquivo por fatia em `docs/superpowers/plans/`, cada um com a sua **Branch de Trabalho**) → revisão do Rafael → execução inline da fatia 1. A spec e os planos são commitados direto na `main`.

**Limitações já documentadas** (não são pendências; entram na spec e no README): scanners de e-mail consomem links com limite; iPad aparece como DESKTOP; `click_count` pode divergir dos eventos; logs da Vercel e histórico guardam o token; a blocklist não pega golpe novo nem site que vira golpe depois; resposta perdida na rede perde o token.

## Excalidraw (documentação visual, no navegador do Rafael)

- **Estado (revisado pelo Rafael em 2026-10-01, sem correções):** 5 seções (REGRAS DE NEGÓCIO, STACKS, SYSTEM DESIGN, MODELO DE DADOS, ENTREGA (CI/CD)), **125 elementos**. Backup da versão anterior (93 elementos) em `excalidraw-backup-<ts>` no `localStorage`. Não exportado para o repositório. É o **resumo visual**; a verdade são os `.md`.
- **Atualizado em 2026-09-30:**
  - regras 11 a 15 (blocklist, destino público, sem reativação, rate limit de criação, aviso do P7);
  - STACKS com Blocklist, Testes e CI;
  - SYSTEM DESIGN com `HEAD`, 429/503, `«interface» UrlThreatChecker`, camada `src/infra` com `SafeBrowsingUrlThreatChecker`, caixa externa do Google Safe Browsing e as decisões de design reescritas (1 a 9);
  - seção nova ENTREGA (CI/CD): push → PR → CI → merge (ruleset) → Vercel (Deployment Checks) → produção.
- **Pendente:**
  - **melhorar a visualização no futuro** (pedido do Rafael em 2026-10-01, sem prazo e sem urgência);
  - a caixa "git push na branch (ex.: feat/mvp)" da seção ENTREGA ficou desatualizada com as fatias: trocar por `feat/mvp-1-base` na próxima edição pedida pelo Rafael;
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
- Quando o Rafael pede "explique mais a fundo": uma **analogia do cotidiano**, depois **situações numeradas** com as opções lado a lado, depois uma **tabela situação × opção** com ✓/✗. Ele pede isso porque está aprendendo, não como crítica.
- Analogias com Java/Spring (JDBC, HikariCP, `@Async`, pacotes `repository`/`integration`) funcionam bem.
- **Verificar antes de afirmar:** context7 para bibliotecas, firecrawl para docs e termos (Vercel, Neon, Google, MDN, RFCs), `npm view` para versões e peers. Números não oficiais são sinalizados como tal.
- Quando surge algo fora da pauta (ex.: a blocklist), fazer um **relatório com varredura dos arquivos** antes de decidir.
- **Tecnologia que o Rafael nunca usou** (Docker, Neon, CI, PR): antes das opções, explicar cada peça com uma analogia e separar sempre **o que roda em produção** do **que roda no computador dele**. Na decisão de testes, a confusão veio de misturar os dois.

## O que não funcionou (não repetir)

- **Mensagem de decisão densa**, com jargão ("CTE", "waitUntil") em células cheias. Resposta do Rafael: "não entendi nada… verbosa, confusa".
- **Deixar edições sem commit**: um Ctrl+Z desfez parte do `domain.md` em 2026-09-30, e tudo foi refeito pelo histórico da conversa.
- **Terminar um turno sem resposta**: o Rafael acha que perdeu perguntas.
- Afirmar texto de aviso sem checar os termos do provedor: o primeiro texto proposto para a R7 ("identificado como perigoso") violava os termos do Google.

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
- Ao fechar um bloco, pede **varredura com `grep` + atualização de todos os arquivos afetados + HANDOFF + commit/push**.
- Base em Java/Spring e segurança; está aprendendo Next.js, ORM e serverless. Nunca usou Docker, Neon, CI nem PR (explicados em 2026-09-30). Quer **acompanhar cada tarefa** da implementação, porque o projeto também é aprendizado e ele precisa explicar cada parte numa entrevista.
- Ação destrutiva: relatório primeiro (o quê, onde, risco), autorização depois.
- Pode acionar o Antigravity CLI (`agy -p "..."`) para pesquisa web e revisão.
