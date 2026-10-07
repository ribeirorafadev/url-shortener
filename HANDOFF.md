# short-url — Handoff

**Atualizado em:** 2026-10-07 · **Versões anteriores:** `git log -- HANDOFF.md`. A última versão longa, com o detalhe de cada achado da releitura crítica, é `git show 5105255:HANDOFF.md`; a do histórico das sessões de design é `git show a944166:HANDOFF.md`.

## Goal

Encurtador de links com analytics: o primeiro projeto do portfólio full-stack do Rafael, em Node.js/TypeScript, para diversificar a stack antes dos projetos em Java/Spring (IAM e CRM; roadmap em `~/Projetos/portfolio-roadmap.txt`). Escopo, fora de escopo e critério de "pronto" estão em `docs/superpowers/PRD.md`.

## Onde estamos

- **Fase:** design pelo **caminho arquitetural** do `superpowers:brainstorming`. **Nenhum código escrito, de propósito.** Hard-gate: spec escrita e aprovada → três planos aprovados → só então código.
- **Design 100% fechado em 2026-10-07**, incluindo a releitura crítica (RC1 a RC10 e os baixos B-1 a B-4).
- **Próxima etapa:** **escrever a spec do MVP** (ver "Próximos passos").

## Como retomar

1. `git status -sb` deve mostrar `main...origin/main` limpo. Se não estiver, pergunte ao Rafael antes de mexer.
2. Invoque `superpowers:brainstorming` (caminho arquitetural). A etapa atual é "escrever o design doc" (spec).
3. A sessão já carrega o **núcleo** (`AGENTS.md`, `architecture-layers`, `security-core`, `code-style`). **Antes de tratar um tema, leia os arquivos que o índice do `AGENTS.md` aponta.** Este HANDOFF é só um índice de estado, pendências e forma de trabalhar.
4. Decisões novas: **uma por mensagem**, no formato de "Como apresentar decisões". Ao fechar, registre **na hora** no arquivo-fonte e marque aqui.
5. Ao fim de cada bloco: **varredura de todos os arquivos afetados → atualização → HANDOFF → commit e push**, com autorização do Rafael na mensagem (um Ctrl+Z já apagou trabalho não commitado).
6. Regras do harness: cada arquivo de `.agents/` com **no máximo 12 mil caracteres** (`wc -m`); regra nova sob demanda leva `trigger: model_decision` + `description`, entra no índice do `AGENTS.md` e **não** ganha link em `.claude/rules/` (só o núcleo tem link); detalhe de implementação novo vai marcado **[→ spec]** (`spec-workflow.md`, §8).

## Fontes da verdade

- **Índice "ao mexer em X, leia Y":** `AGENTS.md` (também traz o glossário). Lista dos arquivos de contexto: `.agents/context/README.md`.
- **Núcleo** (~24 mil caracteres, sempre carregado): `AGENTS.md`, `.agents/rules/architecture-layers.md`, `.agents/rules/security-core.md`, `.agents/rules/code-style.md`.
- **Sob demanda:** os demais `.agents/rules/*.md` e `.agents/context/*.md`, mais o PRD e o ADR (`docs/superpowers/ADR.md`, **append-only: nunca editar**).
- **Rastro das decisões:** toda decisão foi registrada no arquivo-fonte com o rótulo e a data (ex.: `(RC4, decidido em 2026-10-07)`, `(B1, …)`, `(P5, …)`, `(T3, …)`). Para achar onde está uma decisão: `grep -rn "RC4" .agents docs`.

## Índice das decisões

Todas debatidas com trade-offs e aprovadas pelo Rafael. **Não reabrir sem motivo novo.**

| Tema | Rótulos | Fonte |
|---|---|---|
| Base: Next na Vercel, Prisma + Neon, sem login (token), domínio puro | AD-001 a AD-004 | `ADR.md` |
| Versões (Node 24, Next 16.3.8, Prisma 7.10.0, TS 6.0.3), npm endurecido, `qrcode@1.5.4`, `@vercel/functions` | — | `architecture-stack.md` |
| Banco: adapter `pg` + pool, timeouts, `@next/env` na CLI; **`migrate deploy` no build + branch do Neon por preview**, `DATABASE_URL_UNPOOLED`, migration só aditiva | D1, 10e, RC1 | `architecture-persistence.md` |
| Modelo de dados; gráfico diário com `$queryRaw` (único SQL cru); total = `click_count` | RC3, RC8 | `data-model.md`, `architecture-layers.md` |
| URL de destino R1 a R7, IDN, **origem canônica** (`resolveAppOrigin`), **IPv6 numérico recusado**, `url.href` | P4, P6, RC2, RC10, B-2 | `url-validation.md` |
| Slug, limite, expiração, **relógio `Clock`** | P7, B-1 | `link-lifecycle.md` |
| Criação: token, `CreateLinkState`, card, QR, **validação em duas rodadas** | 6a a 6c, P1 a P5, RC7 | `link-creation.md`, `error-map.md` |
| Redirect: formato do slug, 302/404/410/429/503, UPDATE atômico, `after()`, bots e `HEAD`, **só link ativo gera evento**, rota fixa de 7 caracteres proibida | 7a a 7e, RC9, B-3, B-4 | `redirect.md` |
| Gestão: gráfico de 30 dias (só humanos), desativação irreversível e idempotente, QR, headers | 8a, 8b, 9a, 9b, P1b, RC8, RC9 | `manage-page.md`, `security-token.md` |
| Blocklist Google Safe Browsing v5, fail-closed, aviso "suspeito" + atribuição | R7, B1 a B3 | `security-blocklist.md`, `url-validation.md` |
| Rate limit (10/min + 100/dia na criação, 300/min no redirect, `/64`), `x-real-ip`, **IP ausente** e **configuração ausente = indisponível**, trava de build na Vercel | 10a a 10d, RC4, RC5 | `security-rate-limit.md` |
| **Headers globais e CSP sem nonce**, `react/no-danger`, ameaças, segredos, IP não persistido | RC6 | `security-core.md` |
| Testes (Vitest, Postgres em Docker, `test:http`), CI sem segredos, ruleset + Deployment Checks | T1 a T5 | `architecture-testing-ci.md` |
| `npm run dev` sem chaves (`USE_LOCAL_FAKES` no `.env.development.local`, duas travas) | — | `architecture-local-dev.md` |
| Lint, kebab-case, Conventional Commits, branches e fatias, PR | — | `code-style.md` |
| Formato de spec/plano/ADR, regra × spec | — | `spec-workflow.md` |

**Defeitos já corrigidos:** o SQL atômico não checava `deactivated_at` (2026-09-30); o `USE_LOCAL_FAKES` estava no `.env.local`, que o `next build` também lê (2026-10-02).

**Limitações documentadas** (entram na spec e no README; não são pendências): scanners de e-mail consomem links com limite; iPad aparece como DESKTOP; `click_count` pode divergir dos eventos; logs da Vercel e histórico guardam o token; a blocklist não pega golpe novo nem site que vira golpe depois; resposta perdida na rede perde o token; a R3 não cobre os endereços por deploy e por branch (RC2); a CSP aceita `'unsafe-inline'` (RC6); o `x-real-ip` só é confiável na Vercel (RC5); a R4 não resolve DNS (RC10).

## Prazo, fatias e execução

- **Prazo:** a semana começa **quando a spec e os três planos forem aprovados**; no máximo 4 a 5 h por dia; **nenhum corte de escopo**. Estimativa não oficial: 28 a 35 h.
- **Três fatias, cada uma com plano, branch e PR próprios** (`code-style.md`, "Branches e fatias"):
  1. `feat/mvp-1-base`: setup, Docker, CI, ruleset, Vercel, Neon e domínio com testes. **Primeira PR, feita em conjunto** (o Rafael nunca usou PR: abrir pelo site do GitHub, ler "Files changed", acompanhar o CI, corrigir na mesma branch).
  2. `feat/mvp-2-create-redirect`: criação (Google e rate limit), redirect, teste de concorrência, testes HTTP.
  3. `feat/mvp-3-manage`: página de gestão e README.
- **Execução inline** (`superpowers:executing-plans`), com TDD, na branch da fatia. **Ajustes do Rafael:** pausa curta ao fim de **cada tarefa** (o que foi feito, o teste que falhou e passou, o commit), e **comentários inline** explicando como cada peça se encaixa nas decisões. Progresso num *ledger* em `.superpowers/sdd/<plano>/progress.md` (ignorado pelo Git).
- **Cada tarefa dos planos lista os arquivos de contexto que precisa ler.**

## Próximos passos

**1. Escrever a spec** (`docs/superpowers/specs/2026-10-07-short-url-mvp-design.md`, formato de `spec-workflow.md` §7):
- Cabeçalho com **Branch Alvo** = as três branches. Seções numeradas, `## Alternativas consideradas e por que foram descartadas` e `## Requisitos rastreados` (RF/RNF, coluna de task apontando para o plano da fatia).
- Consolidar PRD + `.agents/context/` + `.agents/rules/`. **Mover os trechos [→ spec]** para a spec e deixar no lugar uma referência à seção; triar também detalhes curtos sem rótulo (§8). Isso alivia o `redirect.md` (11,4 mil) e o `url-validation.md` (11 mil), perto do limite.
- **Plano de testes:** domínio com fakes (`LinkRepository`, `UrlThreatChecker`, rate limiter, `Clock` fixo); testes de tabela das funções puras (`isValidSlugFormat`, `isPreviewBot` com UAs de navegadores embutidos, dispositivo, referrer, IP `/64`, formato do token, motivo do 410, `trim()`, fim do dia em `America/Sao_Paulo`, canonicalização do Safe Browsing, `resolveAppOrigin`, validação em duas rodadas, IPv6 numérico, adaptador "indisponível"); concorrência do limite com Postgres real; testes HTTP (302/404/410, `no-store`, `HEAD`, headers da gestão e globais).
- **Notas sobre o AD-004** (não editável): o QR saiu do domínio para a entrada, e os adaptadores ganharam `src/infra/`. Nenhuma das duas passa no critério de ADR.
- **Setup a especificar:** `.npmrc` + `allowScripts`; lint (`import/no-extraneous-dependencies`, `react/no-danger`, barreira ao SQL cru inseguro, candidata `no-restricted-imports`); `engines.node`; build `prisma migrate deploy && prisma generate && next build` (decidir onde fica e confirmar que a Vercel instala a CLI do Prisma); `.env.example` (`USE_LOCAL_FAKES`, `DATABASE_URL`, `DATABASE_URL_UNPOOLED`, `APP_ORIGIN`, chaves em branco); `prisma.config.ts` com `loadEnvConfig`; `next.config.ts` como função de `phase` (trava do `USE_LOCAL_FAKES`, trava das chaves na Vercel, headers globais com a regra da gestão por último); `compose.yml`; `vitest.config.mts`; scripts `test`, `test:http` (com `APP_ORIGIN`), `lint`, `typecheck`; workflow do CI (ações por SHA, `contents: read`, Postgres como *service container*); instalar sempre com versão explícita.
- Nota: o Prisma 8 renomeia `updateManyAndReturn` para `updateAll()` (o projeto fixa o 7).
- Linha no `docs/superpowers/specs/README.md` → autorrevisão → **revisão do Rafael**.

**2. Depois da spec aprovada:** seção RF/RNF no Excalidraw → `superpowers:writing-plans` para os **três planos** (`docs/superpowers/plans/`, um por fatia, com **Branch de Trabalho** e os arquivos de contexto de cada tarefa) → revisão do Rafael → execução inline da fatia 1. Spec e planos vão direto na `main`.

**3. Na fatia 1 (harness, etapa 2; não antecipar):** hooks quando existirem `lint`, `typecheck` e `test` (skill `update-config`; candidato: medir o limite de 12 mil caracteres); **decidir quem revisa cada fatia** (subagente no modelo mais capaz ou `agy -p`) e criar o agente revisor (`.claude/agents/` e `.agents/agents/`); skills só quando algo se repetir (`superpowers:writing-skills`); `paths:`/`glob` só para arquivo que o agente comprovadamente deixe de ler.

**Pendências de setup** (anotadas, sem decisão aberta):
- Instalar o Docker (hoje não há Docker nem Postgres) e escolher entre `sudo` e *rootless* (o grupo `docker` equivale a root).
- Versão major do Postgres ao criar o projeto no Neon (14 a 18); o `compose.yml` usa a mesma.
- Neon-Managed Integration na Vercel, com limpeza automática de branches; confirmar a **Standard Protection** nos previews (RC1).
- Chaves do Upstash e do Google também no ambiente **Preview** (RC4).
- `curl -I` para conferir o HSTS (RC6) e janela anônima para ver quais `*.vercel.app` abrem sem login (RC2).
- Ruleset da `main` e Deployment Checks na fatia 1; confirmar com um commit que falha de propósito que o `*.vercel.app` também fica retido.
- **Pré-requisito do Rafael:** projeto no Google Cloud + API key **restrita à Safe Browsing API** (`security-blocklist.md`).
- Sugestão sem prazo: levar o padrão núcleo + índice no `AGENTS.md` para a skill `novo-projeto` do Rafael (`~/.agents/skills/novo-projeto`).

## Harness (etapa 1 concluída em 2026-10-03)

Regras quebradas por assunto (commit `fbbfe7e`): núcleo sempre carregado + índice no `AGENTS.md`, o resto sob demanda; `CLAUDE.md` = `@AGENTS.md`; links em `.claude/rules/` só para o núcleo; regra = o quê e por quê, spec = como. Medição com `claude -p`: **65.459 → 39.073 tokens** de entrada. Fatos verificados: o Claude Code carrega os links de `.claude/rules/` e, com link + `@import`, o arquivo entra uma vez só; o Antigravity lê `AGENTS.md` (não o `CLAUDE.md`), usa `.agents/rules/` sem subpastas com `trigger:`, subagentes em `.agents/agents/`, skills em `.agents/skills/`, e o editor limita a regra a 12 mil caracteres.

## Excalidraw (documentação visual, no navegador do Rafael)

- **Estado:** 5 seções (REGRAS DE NEGÓCIO, STACKS, SYSTEM DESIGN, MODELO DE DADOS, ENTREGA), 125 elementos, revisado em 2026-10-01. É o resumo visual; a verdade são os `.md`. Não exportado.
- **Pendente, só na próxima edição pedida pelo Rafael:** ENTREGA (`feat/mvp-1-base` no lugar de `feat/mvp`; `migrate deploy` no build, branch do Neon por preview, Standard Protection); STACKS (conferir Next 16.3.8); SYSTEM DESIGN (headers/CSP, origem canônica); seção RF/RNF depois da spec; melhorar a visualização (sem prazo); no fim, o Rafael exporta `.excalidraw` + SVG para `docs/`.
- **Protocolo (via `localStorage` com claude-in-chrome), só quando o Rafael pedir na própria mensagem:** ele fecha as abas do excalidraw.com → o agente abre uma aba sem tocar no canvas e confere a contagem → backup em `excalidraw-backup-<ts>` → ensaio em memória (`window.__newScene`, com asserts) → grava `excalidraw` + `version-dataState`, conferindo que a cena não mudou → fecha a aba → avisa.
- **Armadilhas:** identificar elementos por texto exato, nunca por posição; não imprimir IDs; aba em segundo plano não renderiza; a contagem cai quando o Excalidraw descarta `isDeleted`; a saída do `javascript_tool` é bloqueada com `=`, `?` ou `&` e cortada perto de 1.000 caracteres (ler em partes); o classificador nega neutralizar o `Storage.prototype.setItem` e nega gravar sem pedido explícito: **nunca tentar rota alternativa**.

## Como apresentar decisões (o que funcionou)

- **Formato:** de onde veio a decisão ("isto surgiu quando…") → **cenário concreto** ("a Maria…") → opções A/B/C em 1–2 frases com **mini linha do tempo** → **tabela curta sem jargão** → recomendação em poucas linhas + fonte numa linha. A verificação das fontes fica fora da mensagem.
- "Explique mais a fundo": **analogia do cotidiano** → situações numeradas → tabela situação × opção com ✓/✗. Analogias com Java/Spring funcionam bem (JDBC, `PreparedStatement`, HikariCP, `@Profile("dev")`, `app.base-url`).
- Tema abstrato (harness, estrutura): mostrar a árvore de pastas e exemplos encurtados.
- Tecnologia nova para ele (Docker, Neon, CI, PR, CSP): explicar a peça antes das opções e separar **produção** de **computador dele**.
- **Verificar antes de afirmar:** context7 para bibliotecas; firecrawl para docs (Vercel, Neon, Google, MDN, RFCs); `npm view` para versões; `agy -p` para o Antigravity. **Ferramenta se mede** (`claude -p --output-format json` em diretório descartável). **Biblioteca se lê no código publicado** (`npm pack <pacote>@<versão>` no scratchpad + `grep`; assim fecharam o RC4 e o RC5). Número não oficial é sinalizado.
- Assunto fora da pauta: relatório com varredura dos arquivos antes de decidir.
- Perguntas de "por que aceitar esse risco?" (ex.: `'unsafe-inline'` no RC6): responder com a análise concreta de impacto e, se couber, propor reforço barato na primeira barreira.

## O que não funcionou (não repetir)

- Mensagem de decisão densa, com jargão em células cheias ("não entendi nada… verbosa, confusa").
- Deixar edições sem commit (Ctrl+Z apagou parte do trabalho em 2026-09-30).
- Terminar um turno sem resposta (o Rafael acha que perdeu perguntas).
- Afirmar texto de aviso sem checar os termos do provedor (o primeiro texto da R7 violava os termos do Google).
- Afirmar comportamento de ferramenta sem medir (os links de `.claude/rules/` "não faziam nada": faziam).
- Registrar decisão sem testar o ciclo inteiro (o `USE_LOCAL_FAKES` no `.env.local` quebraria o `test:http`).

## Repositório

- Público: https://github.com/ribeirorafadev/url-shortener (`origin` via SSH, autenticado como `ribeirorafadev`). A `main` só tem documentação, commitada direto durante o design; com o setup (CI + ruleset), passa a aceitar só PR com ✓.
- **Push só com autorização explícita do Rafael na mensagem.** Commits em Conventional Commits (descrição em pt-BR), com o trailer do Claude.
- Tudo o que é commitado é público, inclusive este arquivo: nunca registrar segredos. `gh` e a CLI `vercel` não estão instalados. O README completo é entrega do PRD.

## Preferências do Rafael

- pt-BR, direto, Markdown estruturado, **negrito** em termos críticos; decisão não trivial com fonte real (doc oficial, RFC, lei, OWASP).
- Quer entender os trade-offs antes de decidir; nunca apresentar decisão como fato consumado. Às vezes pede "explique melhor o cenário" depois de fechar: é aprendizado, não dúvida. Registrar só quando ele liberar.
- Base em Java/Spring e segurança; aprendendo Next.js, ORM e serverless; nunca usou Docker, Neon, CI nem PR. Quer **acompanhar cada tarefa** da implementação, porque precisa explicar cada parte numa entrevista.
- Ação destrutiva: relatório primeiro (o quê, onde, risco), autorização depois.
- Pode acionar o Antigravity CLI (`agy -p "..."`) para pesquisa web e revisão.
