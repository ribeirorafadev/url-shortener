# short-url — Handoff

**Atualizado em:** 2026-09-30 · **Versão longa anterior:** `git show a944166:HANDOFF.md` (histórico detalhado das sessões)

**Fase:** design pelo **caminho arquitetural** do `superpowers:brainstorming`. **Nenhum código escrito, de propósito.** O hard-gate só libera código depois de: spec escrita e aprovada → plano (`superpowers:writing-plans`) aprovado → método de execução escolhido.

**Próxima etapa:** decidir o **`npm run dev` sem chaves** (última pendência antes da spec, ver "Pendências") → **escrever a spec**. Os cenários P1 a P7 e a estratégia de testes e CI (T1 a T5) estão fechados.

## Como retomar

1. `git status -sb` deve mostrar `main...origin/main` limpo. Se não estiver, pergunte ao Rafael antes de mexer.
2. Invoque `superpowers:brainstorming` (caminho arquitetural, etapa "apresentar o design em seções").
3. **As decisões estão nos arquivos-fonte, não aqui.** Este documento é um índice: leia a fonte indicada antes de propor algo sobre um tema.
4. Apresente **uma decisão por mensagem** no formato de "Como apresentar decisões". Ao fechar, registre **na hora** no arquivo-fonte e marque aqui.
5. **Commite e dê push ao fim de cada bloco de decisões**, com autorização do Rafael na mensagem. Um Ctrl+Z no editor já apagou trabalho não commitado.

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
| Erros e rate limit (10a a 10d) | Upstash fora: fail-open no redirect, fail-closed na criação; 10/min + 100/dia na criação, 300/min no redirect, timeout de 1 s; chave `/64` no IPv6; até 3 tentativas em colisão de slug; mapa de erros aprovado | `security.md`, `domain.md` "Mapa de erros" |

**Defeito corrigido (2026-09-30):** o SQL atômico não checava `deactivated_at`. Já está corrigido em `domain.md`. Vale uma releitura crítica das regras antes da spec.

## Pendências

**`npm run dev` sem chaves (próxima decisão):** quem clona e roda o site completo sem as chaves do Upstash e do Google tem a criação recusada, porque a criação é fail-closed. A regra está certa para produção, mas impede quem clona de experimentar o site. Apresentar as opções no formato de sempre (ex.: só documentar as contas gratuitas no README, ou fakes ligados por uma variável explícita só em dev, com trava para nunca valer em produção).

**Pendências de setup (anotadas, sem decisão aberta):**
- Instalar o Docker na máquina do Rafael (hoje não há Docker nem Postgres) e escolher entre `sudo` e o modo *rootless*, porque o grupo `docker` equivale a root.
- Definir a versão major do Postgres ao criar o projeto no Neon (14 a 18); o `compose.yml` usa a mesma.
- Ativar o ruleset da `main` e os Deployment Checks junto com o CI, e confirmar com um commit que falha de propósito que o `*.vercel.app` também fica retido.
- O Rafael nunca trabalhou com PR: a primeira PR da `feat/mvp` vai ser guiada passo a passo.

**Para a spec** (`docs/superpowers/specs/2026-XX-XX-short-url-mvp-design.md`, formato de `spec-workflow.md`):
- Consolidar PRD, `domain.md`, `security.md` e `architecture.md`, com as seções `## Alternativas consideradas…` e `## Requisitos rastreados` (RF/RNF).
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
  - `.env.example` com `DATABASE_URL`, `DIRECT_URL`, os tokens do Upstash e `SAFE_BROWSING_API_KEY`;
  - `compose.yml` (Postgres), `vitest.config.mts` (`resolve.tsconfigPaths`, `fileParallelism: false`), scripts `test`, `test:http`, `lint` e `typecheck`;
  - workflow do CI em `.github/workflows/` (ações por SHA, `permissions: contents: read`, Postgres como *service container*);
  - instalar sempre com versão explícita.
- Reavaliar as dependências transitivas do `qrcode@1.5.4` (traz `yargs@15`).
- Nota: o Prisma 8 renomeia `updateManyAndReturn` para `updateAll()` (o projeto fixa o 7).
- O Next já tem a **16.3.7** (a baseline é a 16.3.6): decidir na spec se a baseline sobe.
- **Pré-requisito do Rafael, antes da implementação:** projeto no Google Cloud + API key **restrita à Safe Browsing API** (gratuito, sem faturamento; ver `security.md`).
- Adicionar a linha da spec em `docs/superpowers/specs/README.md`, fazer a autorrevisão e pedir a revisão do Rafael.

**Depois da spec aprovada:** seção RF/RNF no Excalidraw → `superpowers:writing-plans` → código só com o plano aprovado. A spec vai na branch dela (ex.: `feat/mvp`).

**Limitações já documentadas** (não são pendências; entram na spec e no README): scanners de e-mail consomem links com limite; iPad aparece como DESKTOP; `click_count` pode divergir dos eventos; logs da Vercel e histórico guardam o token; a blocklist não pega golpe novo nem site que vira golpe depois; resposta perdida na rede perde o token.

## Excalidraw (documentação visual, no navegador do Rafael)

- **Estado (2026-09-30):** 5 seções (REGRAS DE NEGÓCIO, STACKS, SYSTEM DESIGN, MODELO DE DADOS, ENTREGA (CI/CD)), **125 elementos**. Backup da versão anterior (93 elementos) em `excalidraw-backup-<ts>` no `localStorage`. Não exportado para o repositório. É o **resumo visual**; a verdade são os `.md`.
- **Atualizado em 2026-09-30:**
  - regras 11 a 15 (blocklist, destino público, sem reativação, rate limit de criação, aviso do P7);
  - STACKS com Blocklist, Testes e CI;
  - SYSTEM DESIGN com `HEAD`, 429/503, `«interface» UrlThreatChecker`, camada `src/infra` com `SafeBrowsingUrlThreatChecker`, caixa externa do Google Safe Browsing e as decisões de design reescritas (1 a 9);
  - seção nova ENTREGA (CI/CD): push → PR → CI → merge (ruleset) → Vercel (Deployment Checks) → produção.
- **Pendente:**
  - conferência visual pelo Rafael (a automação não consegue rolar o canvas);
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
- Ao fechar um bloco, pede **varredura com `grep` + atualização de todos os arquivos afetados + HANDOFF + commit/push**.
- Base em Java/Spring e segurança; está aprendendo Next.js, ORM e serverless. Nunca usou Docker, Neon, CI nem PR (explicados em 2026-09-30).
- Ação destrutiva: relatório primeiro (o quê, onde, risco), autorização depois.
- Pode acionar o Antigravity CLI (`agy -p "..."`) para pesquisa web e revisão.
