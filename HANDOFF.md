# short-url — Handoff

**Atualizado em:** 2026-10-08 · **Versões anteriores:** `git log -- HANDOFF.md`. A última versão longa, com o detalhe de cada achado da releitura crítica, é `git show 5105255:HANDOFF.md`; a do histórico das sessões de design é `git show a944166:HANDOFF.md`.

## Goal

Encurtador de links com analytics: o primeiro projeto do portfólio full-stack do Rafael, em Node.js/TypeScript, para diversificar a stack antes dos projetos em Java/Spring (IAM e CRM; roadmap em `~/Projetos/portfolio-roadmap.txt`). Escopo, fora de escopo e critério de "pronto" estão em `docs/superpowers/PRD.md`.

## Onde estamos

- **Fase:** fim do design pelo **caminho arquitetural** do `superpowers:brainstorming`. **Nenhum código escrito, de propósito.** Hard-gate: spec aprovada ✓ → três planos aprovados → só então código.
- **Design 100% fechado em 2026-10-07**, incluindo a releitura crítica (RC1 a RC10 e os baixos B-1 a B-4).
- **Lacunas achadas ao preparar a spec, fechadas em 2026-10-07:** S1 (migration no `buildCommand` do `vercel.json`, client gerado no `postinstall`, `db:migrate` local/CI e, por consequência, `process.env` em vez do `env()` no `prisma.config.ts`), S2 (AD-004 por lint com lista branca), S3 (sufixos de host do Safe Browsing pela regra da v4, sem a Public Suffix List), S4 (cache em memória das respostas do Google, exigido pelo protocolo; o fail-closed continua como desvio consciente) e S5 (gráfico próprio no servidor, sem Recharts). Nenhuma passa no critério de ADR. A varredura de todos os arquivos foi feita e eles já refletem S1 a S5.
- **Spec do MVP escrita em 2026-10-07 e APROVADA pelo Rafael em 2026-10-08** (`docs/superpowers/specs/2026-10-07-short-url-mvp-design.md`, status `Aprovada`, ~66 mil caracteres, 16 seções). Os trechos `[→ spec]` saíram de `.agents/` e viraram referências "spec, §N". Com a aprovação, os detalhes de "como" que a spec acrescentou também estão aprovados (lista em "Próximos passos", item 1).
- **Próxima etapa: aguardar o Rafael.** Ele pediu explicitamente para **não começar a implementação** nem os planos até o próximo prompt. Há 4 tópicos abertos levantados por ele em 2026-10-08 (ver "Tópicos abertos"), e só depois vem o `superpowers:writing-plans`.

## Como retomar

1. `git status -sb` deve mostrar `main...origin/main` limpo. Se não estiver, pergunte ao Rafael antes de mexer.
2. O brainstorming terminou (spec aprovada). **Não invoque `superpowers:writing-plans` nem escreva código sem o Rafael pedir.** Quando ele pedir os planos: `superpowers:writing-plans`, três planos, um por fatia. Mudança na spec depois de aprovada: edite a spec (e a regra, se mudar o quê ou o porquê), rode a autorrevisão e peça nova aprovação.
3. A sessão já carrega o **núcleo** (`AGENTS.md`, `architecture-layers`, `security-core`, `code-style`). **Antes de tratar um tema, leia os arquivos que o índice do `AGENTS.md` aponta.** Este HANDOFF é só um índice de estado, pendências e forma de trabalhar.
4. Decisões novas: **uma por mensagem**, no formato de "Como apresentar decisões". Ao fechar, registre **na hora** no arquivo-fonte e marque aqui.
5. Ao fim de cada bloco: **varredura de todos os arquivos afetados → atualização → HANDOFF → commit e push**, com autorização do Rafael na mensagem (um Ctrl+Z já apagou trabalho não commitado).
6. Regras do harness: cada arquivo de `.agents/` com **no máximo 12 mil caracteres** (`wc -m`); regra nova sob demanda leva `trigger: model_decision` + `description`, entra no índice do `AGENTS.md` e **não** ganha link em `.claude/rules/` (só o núcleo tem link); detalhe de implementação novo vai **direto para a spec**, e a regra cita "spec, §N" (`spec-workflow.md`, §8).

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
| Versões (Node 24, Next 16.3.8, Prisma 7.10.0, TS 6.0.3), npm endurecido, `qrcode@1.5.4`, `@vercel/functions`; **Recharts e `tldts` recusados** | S3, S5 | `architecture-stack.md` |
| Banco: adapter `pg` + pool, timeouts, `@next/env` na CLI; **`migrate deploy` no `buildCommand` do `vercel.json` + branch do Neon por preview**, `postinstall`, `db:migrate`, `DATABASE_URL_UNPOOLED`, migration só aditiva | D1, 10e, RC1, S1 | `architecture-persistence.md` |
| Modelo de dados; gráfico diário com `$queryRaw` (único SQL cru); total = `click_count` | RC3, RC8 | `data-model.md`, `architecture-layers.md` |
| URL de destino R1 a R7, IDN, **origem canônica** (`resolveAppOrigin`), **IPv6 numérico recusado**, `url.href` | P4, P6, RC2, RC10, B-2 | `url-validation.md` |
| Slug, limite, expiração, **relógio `Clock`** | P7, B-1 | `link-lifecycle.md` |
| Criação: token, `CreateLinkState`, card, QR, **validação em duas rodadas** | 6a a 6c, P1 a P5, RC7 | `link-creation.md`, `error-map.md` |
| Redirect: formato do slug, 302/404/410/429/503, UPDATE atômico, `after()`, bots e `HEAD`, **só link ativo gera evento**, rota fixa de 7 caracteres proibida | 7a a 7e, RC9, B-3, B-4 | `redirect.md` |
| Gestão: gráfico de 30 dias (só humanos, **componente próprio no servidor**), desativação irreversível e idempotente, QR, headers | 8a, 8b, 9a, 9b, P1b, RC8, RC9, S5 | `manage-page.md`, `security-token.md` |
| Blocklist Google Safe Browsing v5, fail-closed, aviso "suspeito" + atribuição, **sufixos da v4**, **cache em memória** | R7, B1 a B3, S3, S4 | `security-blocklist.md`, `url-validation.md` |
| Rate limit (10/min + 100/dia na criação, 300/min no redirect, `/64`), `x-real-ip`, **IP ausente** e **configuração ausente = indisponível**, trava de build na Vercel | 10a a 10d, RC4, RC5 | `security-rate-limit.md` |
| **Headers globais e CSP sem nonce**, `react/no-danger`, ameaças, segredos, IP não persistido | RC6 | `security-core.md` |
| Testes (Vitest, Postgres em Docker, `test:http`), CI sem segredos, ruleset + Deployment Checks | T1 a T5 | `architecture-testing-ci.md` |
| `npm run dev` sem chaves (`USE_LOCAL_FAKES` no `.env.development.local`, duas travas) | — | `architecture-local-dev.md` |
| Lint (**AD-004 por lista branca**), kebab-case, Conventional Commits, branches e fatias, PR | S2 | `code-style.md` |
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

**1. Spec aprovada em 2026-10-08** (`docs/superpowers/specs/2026-10-07-short-url-mvp-design.md`):
- Estrutura: §1–3 contexto; §4 arquitetura (árvore de arquivos, ponto de montagem, logs); §5 domínio; §6 dados; §7 Safe Browsing; §8 entrada; §9 configuração; §10 erros; §11 testes; §12 fatias; §13 limitações; §14 notas sobre o AD-004; §15 alternativas; §16 requisitos (RF01–RF14, RNF01–RNF12).
- **Detalhes de "como" acrescentados pela spec e aprovados com ela** (não reabrir sem motivo novo): referrers em top 10 + "outros" (§5.9); R4 também recusa `.local`, `.home.arpa`, `.internal` e todas as faixas IPv4 de uso especial da RFC 6890 (§5.5); entrada `site.com:8080/x` cai na R1 (§5.5); dois bancos no container, `shorturl` e `shorturl_test` (§9.7); textos das páginas 404, 429 e da prévia de bot (§8.6); `poweredByHeader: false` (§9.4); gestão com banco fora responde 200 (§8.5, §13); detalhes `CANARY`/`FRAME_ONLY` ignorados no Safe Browsing (§7.1); `RedirectService` novo no domínio (§5.8, §14); `UrlThreatChecker` devolve `'unavailable'` em vez de lançar (§5.2); testes nunca leem `.env*` e recusam rodar fora de `127.0.0.1`/`localhost` (§9.8).
- Itens **(conferir na tarefa)**, que os planos precisam transformar em passo de verificação: `select` no `updateManyAndReturn` e um único `UPDATE … RETURNING` (senão `$queryRaw`); erros de conectividade do Prisma/`pg` (§6.5); API do `@upstash/ratelimit` (ler o código publicado); padrões dos UAs de bots; padrões da lista branca do ESLint; `revalidatePath` na desativação; `404` real da gestão sem `loading.tsx`; tipo do `defineConfig` com URL ausente.
- Valores de setup deixados em aberto de propósito: `<MAJOR>` do Postgres e `<SHA completo>` das ações do CI; região da função, do Neon e do Upstash (a mesma para os três, §9.11).
- O status muda para `Em andamento` quando a implementação da fatia 1 começar (`specs/README.md`).

**2. Quando o Rafael pedir (não antes):** resolver os "Tópicos abertos" → seção RF/RNF no Excalidraw → `superpowers:writing-plans` para os **três planos** (`docs/superpowers/plans/`, um por fatia, com **Branch de Trabalho** e os arquivos de contexto de cada tarefa) → revisão do Rafael → execução inline da fatia 1. Spec e planos vão direto na `main`.

**3. Na fatia 1 (harness, etapa 2; não antecipar):** hooks quando existirem `lint`, `typecheck` e `test` (skill `update-config`; candidato: medir o limite de 12 mil caracteres); **decidir quem revisa cada fatia** (subagente no modelo mais capaz ou `agy -p`) e criar o agente revisor (`.claude/agents/` e `.agents/agents/`); skills só quando algo se repetir (`superpowers:writing-skills`); `paths:`/`glob` só para arquivo que o agente comprovadamente deixe de ler.

**Tópicos abertos (levantados pelo Rafael em 2026-10-08; recomendações dadas, aguardando a resposta dele):**
1. **READMEs de `.agents/`:** recomendação: **apagar o `.agents/context/README.md`** (duplica o índice do `AGENTS.md` e já exigiu atualização paralela; ao apagar, tirar a menção em "Fontes da verdade" abaixo) e **manter** os de `.agents/agents/` e `.agents/skills/` (o Git não versiona pasta vazia, e eles explicam como ligar o agente/skill nativamente nas duas ferramentas). Apagar exige o relatório + autorização.
2. **Excalidraw:** recomendação: sim, agora (antes dos planos), em duas passadas: conteúdo (pendências da seção Excalidraw abaixo + S1 a S5 + RF/RNF) e depois visual. Ícones: o Rafael adiciona bibliotecas do libraries.excalidraw.com e solta cada ícone numa área de "paleta" com um texto-rótulo ao lado (ex.: `icon:vercel`); o agente clona por rótulo, já que identifica elemento por texto, nunca por posição. Uma seção por vez, com aprovação. Só com pedido explícito na mensagem (protocolo abaixo).
3. **README da raiz agora:** recomendação: sim, **mínimo e honesto**: o que é, status "em design, implementação em 3 fatias", stack, links para PRD, ADR e spec, roadmap das fatias com checkbox. Sem "como rodar" (não há código). A versão completa continua sendo entrega da fatia 3 (PRD).
4. **Agents e skills antes da implementação:** recomendação: **ainda não**, como já decidido ("harness, etapa 2", item 3 acima), mas **com data marcada**: o plano da fatia 1 ganha uma tarefa de harness depois que `lint`, `typecheck` e `test` existirem (hooks + agente revisor), e a decisão "quem revisa cada fatia" é apresentada ao Rafael ao escrever o plano 1. Skill só quando algo se repetir (a `superpowers:writing-skills` exige uma falha observada antes de escrever a skill).

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
- **Pendente, só na próxima edição pedida pelo Rafael:** ENTREGA (`feat/mvp-1-base` no lugar de `feat/mvp`; `migrate deploy` no `buildCommand` do `vercel.json` (S1), branch do Neon por preview, Standard Protection); STACKS (conferir Next 16.3.8); SYSTEM DESIGN (headers/CSP, origem canônica); seção RF/RNF depois da spec; melhorar a visualização (sem prazo); no fim, o Rafael exporta `.excalidraw` + SVG para `docs/`.
- **Protocolo (via `localStorage` com claude-in-chrome), só quando o Rafael pedir na própria mensagem:** ele fecha as abas do excalidraw.com → o agente abre uma aba sem tocar no canvas e confere a contagem → backup em `excalidraw-backup-<ts>` → ensaio em memória (`window.__newScene`, com asserts) → grava `excalidraw` + `version-dataState`, conferindo que a cena não mudou → fecha a aba → avisa.
- **Armadilhas:** identificar elementos por texto exato, nunca por posição; não imprimir IDs; aba em segundo plano não renderiza; a contagem cai quando o Excalidraw descarta `isDeleted`; a saída do `javascript_tool` é bloqueada com `=`, `?` ou `&` e cortada perto de 1.000 caracteres (ler em partes); o classificador nega neutralizar o `Storage.prototype.setItem` e nega gravar sem pedido explícito: **nunca tentar rota alternativa**.

## Como apresentar decisões (o que funcionou)

- **Formato:** de onde veio a decisão ("isto surgiu quando…") → **cenário concreto** ("a Maria…") → opções A/B/C em 1–2 frases com **mini linha do tempo** → **tabela curta sem jargão** → recomendação em poucas linhas + fonte numa linha. A verificação das fontes fica fora da mensagem.
- "Explique mais a fundo": **analogia do cotidiano** → situações numeradas → tabela situação × opção com ✓/✗. Analogias com Java/Spring funcionam bem (JDBC, `PreparedStatement`, HikariCP, `@Profile("dev")`, `app.base-url`).
- Tema abstrato (harness, estrutura): mostrar a árvore de pastas e exemplos encurtados.
- Tecnologia nova para ele (Docker, Neon, CI, PR, CSP): explicar a peça antes das opções e separar **produção** de **computador dele**.
- **Verificar antes de afirmar:** context7 para bibliotecas; firecrawl para docs (Vercel, Neon, Google, MDN, RFCs); `npm view` para versões; `agy -p` para o Antigravity. **Ferramenta se mede** (`claude -p --output-format json` em diretório descartável). **Biblioteca se lê no código publicado** (`npm pack <pacote>@<versão>` no scratchpad + `grep`; assim fecharam o RC4 e o RC5). Número não oficial é sinalizado.
- Assunto fora da pauta: relatório com varredura dos arquivos antes de decidir.
- **Ao especificar o "como", reler a doc oficial da API** (referência do método, não só a visão geral): assim apareceram S3 e S4, e o efeito colateral do `env()` na S1. Lacuna achada vira decisão nova, uma por mensagem, antes de escrever.
- Perguntas de "por que aceitar esse risco?" (ex.: `'unsafe-inline'` no RC6): responder com a análise concreta de impacto e, se couber, propor reforço barato na primeira barreira.

## O que não funcionou (não repetir)

- Mensagem de decisão densa, com jargão em células cheias ("não entendi nada… verbosa, confusa").
- Deixar edições sem commit (Ctrl+Z apagou parte do trabalho em 2026-09-30).
- Terminar um turno sem resposta (o Rafael acha que perdeu perguntas).
- Afirmar texto de aviso sem checar os termos do provedor (o primeiro texto da R7 violava os termos do Google).
- Afirmar comportamento de ferramenta sem medir (os links de `.claude/rules/` "não faziam nada": faziam).
- Registrar decisão sem testar o ciclo inteiro (o `USE_LOCAL_FAKES` no `.env.local` quebraria o `test:http`).
- Fechar regra de integração lendo só a visão geral da API: a R7 dizia "sem cache local obrigatório", mas a referência do `hashes.search` exige cache (corrigido na S4).

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
