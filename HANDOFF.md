# short-url — Handoff

**Atualizado em:** 2026-10-08 (fim da sessão do harness) · **Versões anteriores:** `git log -- HANDOFF.md`. A versão do fim do design (antes do harness) é `git show cc83c4b:HANDOFF.md`; a longa, com o detalhe da releitura crítica, `git show 5105255:HANDOFF.md`; a do histórico das sessões de design, `git show a944166:HANDOFF.md`.

## Goal

Encurtador de links com analytics: o primeiro projeto do portfólio full-stack do Rafael, em Node.js/TypeScript, para diversificar a stack antes dos projetos em Java/Spring (IAM e CRM; roadmap em `~/Projetos/portfolio-roadmap.txt`). Escopo, fora de escopo e critério de "pronto" estão em `docs/superpowers/PRD.md`.

## Onde estamos

- **Design:** 100% fechado (2026-10-07), incluindo a releitura crítica (RC1 a RC10, B-1 a B-4) e as lacunas S1 a S5.
- **Spec do MVP:** **aprovada** em 2026-10-08 (`docs/superpowers/specs/2026-10-07-short-url-mvp-design.md`, 16 seções).
- **Harness de execução:** **decidido, implementado e medido** em 2026-10-08 (D1 a D7, seção "Harness de execução"). Há dois agentes prontos, cada um com trava e testes próprios: o **executor** (Sonnet 5.5, Claude Code) e o **QA exploratório** (Gemini 3.8 Flash, `agy`).
- **Nenhum código da aplicação escrito, de propósito.** Hard-gate: spec aprovada ✓ → harness ✓ → **três planos aprovados** → só então código.
- **Próxima etapa: os planos (`superpowers:writing-plans`), SÓ QUANDO O RAFAEL MANDAR** (reafirmado por ele em 2026-10-08). Não começar por iniciativa própria.

## Como retomar (sessão limpa)

1. `git status -sb` deve mostrar `main...origin/main` limpo. Se não estiver, pergunte ao Rafael antes de mexer.
2. A sessão já carrega o **núcleo** (`AGENTS.md`, `architecture-layers`, `security-core`, `code-style`). **Antes de tratar um tema, leia os arquivos que o índice do `AGENTS.md` aponta.** Para planos e execução: **`.agents/rules/execution-workflow.md` primeiro**, depois `spec-workflow.md`.
3. Confira que o executor existe para o Claude Code: o tipo `executor` aparece entre os agentes do `Agent`. Se não aparecer, peça ao Rafael `/agents` ou reiniciar a sessão (os subagentes carregam no início).
4. **Aguarde o comando do Rafael.** Quando ele mandar começar: `superpowers:writing-plans`, três planos, um por fatia, escritos **para o executor** (ver "Próximos passos"). Antes da fatia 1, a pendência de setup do **Docker** precisa ser decidida com ele.
5. Decisões novas: **uma por mensagem**, no formato de "Como apresentar decisões". Ao fechar, registre **na hora** no arquivo-fonte e marque aqui.
6. Ao fim de cada bloco: **varredura de todos os arquivos afetados → atualização → HANDOFF → commit e push, só quando o Rafael mandar na mensagem** (um Ctrl+Z já apagou trabalho não commitado).
7. Regras do harness de documentação: cada arquivo de `.agents/` com **no máximo 12 mil caracteres** (`wc -m`; o `execution-workflow.md` está com ~11,7 mil, então mudança grande nele pede dividir o arquivo), e a `description` de uma regra com **no máximo 250** (limite do editor do Antigravity); regra nova sob demanda leva `trigger: model_decision` + `description`, entra no índice do `AGENTS.md` e **não** ganha link em `.claude/rules/` (só o núcleo tem); detalhe de implementação novo vai **direto para a spec**, e a regra cita "spec, §N" (`spec-workflow.md`, §8).

## Fontes da verdade

- **Índice "ao mexer em X, leia Y":** `AGENTS.md` (também traz o glossário).
- **Núcleo** (~24 mil caracteres, sempre carregado): `AGENTS.md`, `.agents/rules/architecture-layers.md`, `.agents/rules/security-core.md`, `.agents/rules/code-style.md`.
- **Sob demanda:** os demais `.agents/rules/*.md` (inclusive `execution-workflow.md`, criado em 2026-10-08) e `.agents/context/*.md`, mais o PRD e o ADR (`docs/superpowers/ADR.md`, **append-only: nunca editar**).
- **Rastro das decisões:** cada decisão está no arquivo-fonte com rótulo e data (ex.: `(RC4, decidido em 2026-10-07)`). Para achar: `grep -rn "RC4" .agents docs`. **Atenção à colisão de rótulos:** os D1 a D7 do harness (`execution-workflow.md`, formato `**D4 —`) não são o D1 antigo de persistência (`architecture-persistence.md`); busque com `grep -n "D4 —" .agents/rules/execution-workflow.md`.

## Índice das decisões

Todas debatidas com trade-offs e aprovadas pelo Rafael. **Não reabrir sem motivo novo.**

| Tema | Rótulos | Fonte |
|---|---|---|
| Base: Next na Vercel, Prisma + Neon, sem login (token), domínio puro | AD-001 a AD-004 | `ADR.md` |
| Versões (Node 24, Next 16.3.8, Prisma 7.10.0, TS 6.0.3), npm endurecido, `qrcode@1.5.4`, `@vercel/functions`; **Recharts e `tldts` recusados** | S3, S5 | `architecture-stack.md` |
| Banco: adapter `pg` + pool, timeouts, `@next/env` na CLI; **`migrate deploy` no `buildCommand` do `vercel.json` + branch do Neon por preview**, `postinstall`, `db:migrate`, `DATABASE_URL_UNPOOLED`, migration só aditiva | D1 (antigo), 10e, RC1, S1 | `architecture-persistence.md` |
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
| **Execução dos planos:** testes do Opus, executor Sonnet, travas, QA do Gemini, quando o QA roda, checklist da revisão | D1 a D7 (harness) | `execution-workflow.md` |

**Defeitos já corrigidos:** o SQL atômico não checava `deactivated_at` (2026-09-30); o `USE_LOCAL_FAKES` estava no `.env.local`, que o `next build` também lê (2026-10-02).

**Limitações documentadas** (entram no README; não são pendências): scanners de e-mail consomem links com limite; iPad aparece como DESKTOP; `click_count` pode divergir dos eventos; logs da Vercel e histórico guardam o token; a blocklist não pega golpe novo nem site que vira golpe depois; resposta perdida na rede perde o token; a R3 não cobre os endereços por deploy e por branch (RC2); a CSP aceita `'unsafe-inline'` (RC6); o `x-real-ip` só é confiável na Vercel (RC5); a R4 não resolve DNS (RC10).

## Harness de execução (decidido, implementado e medido em 2026-10-08)

**Origem:** o Rafael recusou o "subagente revisor" (Fable, exagero; Opus revisando o próprio código, erro) e trocou por um ciclo **maker-checker com TDD**. Regra completa: `.agents/rules/execution-workflow.md`.

### Quem faz o quê

| Papel | Quem | Onde |
|---|---|---|
| Escreve o teste (vermelho) e os fakes, revisa, faz commit quando mandado | **Opus 5.5 (high)**, sessão principal | — |
| Implementa o código de produção | **Sonnet 5.5 (high)**, subagente `executor` | `.agents/agents/executor/` + symlink `.claude/agents/executor.md` |
| QA exploratório no navegador, só leitura | **Gemini 3.8 Flash (High)** via `agy` | `.agents/agents/qa-explorer/` |
| Revisa e valida cada tarefa; manda commit e push | **Rafael** | — |

### Ciclo de cada tarefa (passo a passo)

1. **Teste (D1):** o Opus lê a tarefa do plano e os arquivos de contexto dela, escreve o teste a partir da spec (fakes e auxiliares em `__fakes__/` ao lado do código) e **roda para ver falhar pelo motivo certo**.
2. **Delegar (D2, D3):** ferramenta `Agent` com `subagent_type: "executor"` (roda em segundo plano; o resultado chega como notificação). O pedido traz: a tarefa, as seções da spec, os arquivos de teste, os arquivos a criar e o comando de verificação. O executor devolve `STATUS: VERDE | BLOQUEADO`, arquivos, verificação, decisões, o que a trava negou e dúvidas sobre o teste. Para devolver uma correção, continue o mesmo agente com `SendMessage`.
3. **Verificar (D7, item 1):** o Opus roda ele mesmo o teste da tarefa, `npm test`, `npm run lint` e `npm run typecheck`. O relato do executor não é evidência.
4. **QA (D6, D6d), só se o diff tocar `src/app/`, `src/components/` ou `next.config.ts`** (e uma passada no fim de cada fatia):
   - o Opus sobe `npm run dev` com `USE_LOCAL_FAKES=true` e o Postgres do Docker (banco de dev, nunca o `shorturl_test`);
   - `sh .agents/agents/qa-explorer/worktree-fingerprint.sh` antes;
   - `agy --agent qa-explorer --model gemini-3.8-flash-high -p "<URL base, o que a tarefa entregou, áreas do catálogo>"` (**o prompt vai por último**; áreas: headers e páginas, criação, redirect, gestão);
   - fingerprint depois: **hash diferente = descarta o QA**;
   - defeito achado → o Opus escreve o teste vermelho que o reproduz → volta ao passo 2.
5. **Revisão (D7):** checklist fixo de **9 itens em toda tarefa** (verde de verdade; testes intactos; sem trapaça; escopo; spec; camadas AD-004; segurança; erros; QA), item que não se aplica = "n/a" com motivo. Veredito `APROVADO` ou `DEVOLVIDO` com `arquivo:linha`, item violado e o que corrigir, sem o Opus escrever a correção. **Na 3ª devolução, para e leva ao Rafael.**
6. **Pausa com o Rafael (por tarefa):** o teste escrito, o que o executor entregou, as devoluções e o porquê, o resultado do QA, o placar do checklist (ex.: `9/9`) e a mensagem de commit proposta. Explicar como cada peça se encaixa nas decisões (ele precisa explicar tudo numa entrevista).
7. **Commit e push só quando o Rafael mandar.** O executor nunca faz commit (a trava barra).
8. **Fim da fatia (D5):** passada de QA da fatia inteira, depois revisão da branch inteira pelo Opus **junto com o Rafael**, e só então o PR.

Progresso num *ledger* em `.superpowers/sdd/<plano>/progress.md` (ignorado pelo Git). Base: `superpowers:subagent-driven-development`, com os ajustes do Rafael, que prevalecem sobre a skill: pausa a cada tarefa, o Opus revisa na sessão principal, executor fixo (a skill troca de modelo na 4ª rodada).

### As travas (D4 e D6c)

- **Executor** (`executor-guard.py`, hook `PreToolUse` no frontmatter, `matcher: "*"`): lista branca e fail-closed.
  - Ferramentas: só `Read`, `Grep`, `Glob`, `Edit`, `Write`, `Bash` e `SubagentHandback` (a que entrega o relatório no auto mode).
  - Escrita barrada: testes (`*.test.*`, `*.spec.*`, `tests/`, `__tests__/`, `__fakes__/`, `vitest.*`), `.agents/`, `docs/`, `.claude/`, `.git/`, `AGENTS.md`, `CLAUDE.md`, `HANDOFF.md`, `package.json`, lockfiles, `.npmrc`, `.gitignore`, `.env*` (o `.env.example` é liberado) e tudo fora do projeto (inclusive via symlink).
  - Leitura barrada: `.env*`, `*.pem`, `*.key` e fora do projeto.
  - Bash por lista branca: `npm test`/`run`/`ci`; `npx` só com `vitest`, `tsc`, `eslint`, `prettier`, `prisma`, `next`; `git` só leitura; utilitários de leitura; `mkdir`, `touch`, `mv`, `cp`, `rm` (sem `-r`) fora dos caminhos protegidos. Nega `$`, crase, subshell, várias linhas, `cd`, redirecionamento para arquivo, `vitest -u`, `prettier --write`/`eslint --fix` sem arquivo explícito, opções que escrevem arquivo (`-o`, `--outputFile`, `--outDir`, `--target-directory=`) e caminhos com `..` que saiam do projeto.
  - O hook **não emite nada quando passa** (um `allow` explícito pularia o sistema de permissões) e termina em `|| exit 2` (hook que quebra com outro código deixaria a ferramenta passar).
  - **Protege contra engano, não contra má-fé**; contra isso valem a revisão e o CI. Se o executor esbarrar num comando legítimo, ele relata e o Opus ajusta a lista **com teste primeiro**.
- **QA** (`agent.md` com `tools: [view_file]` + `inheritMcp: true`; `hooks.json` + `qa-guard.py`): só lê os schemas do Playwright e usa o navegador em `localhost`, `127.0.0.1` e `[::1]`; nega escrita, outros MCP, `browser_run_code_unsafe` e `browser_file_upload`. Camada B: `worktree-fingerprint.sh`. Links criados no QA apontam só para `https://example.com/` (RFC 2606). Limite aceito: um clique ou o 302 levam o navegador para fora do `localhost`.

### Medições (2026-10-08)

- **QA de ponta a ponta:** navegador, JavaScript e formulário funcionaram; escrita, `view_file` em `AGENTS.md`, `browser_run_code_unsafe`, `example.com` e `context7` negados; fingerprint igual.
- **Hook que quebra no `agy`:** bloqueia a ferramenta (fail-closed nativo). No Claude Code, o `|| exit 2` foi testado com o Python ausente: código 2, ação negada.
- **Executor de ponta a ponta** (sessão principal em auto mode, o hook do subagente rodou): sonda de 14 ações escolhidas para serem inofensivas se a trava falhasse. **6 permitidas passaram** (`Write`/`Read` de arquivo novo, `git status`, `echo > /dev/null`, `rm` do próprio arquivo) e **7 proibidas foram negadas pelo motivo certo** (`Write` em teste, `docs/` e `.agents/`; `git commit --dry-run`; `npm install --dry-run`; `echo > arquivo`; `ls ~`). O `Grep` não rodou porque a sessão principal não tem `Grep`/`Glob`, e aí o subagente também não recebe: o executor busca com `grep`/`rg` pelo Bash, e o caso do `Grep` está coberto pelos testes da trava. **Fingerprint idêntico antes e depois; nenhum commit.**
- **Achado da medição:** a primeira rodada perdeu o relatório do executor, porque a trava negava o `SubagentHandback`. Corrigido com teste (`test_passes_delivering_the_final_report`) e com a ferramenta no `tools:`.
- **Revisão de segurança antes do push:** `uvx ruff check` com as regras `S` (Bandit), `B`, `PLW`, `BLE`, `E`, `F`, `UP`, `PTH` e `RUF`: sem achados (os `noqa` restantes são intencionais e comentados: `BLE001` no fail-closed, `S603` no subprocess com argumentos fixos). Revisão manual achou e fechou, com teste primeiro: `cat ~/...` e `/etc/...` pelo Bash, `cat ../fora`, `Glob` com `..`, `cp --target-directory=`, `eslint -o`, `vitest --outputFile`, `tsc --outDir`. Os dois avisos do SonarQube do Rafael (`subprocess.run` sem `check`, senha do Postgres num teste) foram corrigidos; o caminho absoluto da máquina do Rafael saiu do `qa-guard.test.py` (agora é relativo ao projeto).
- **Testes das travas:** `cd .agents/agents/executor && python3 -I executor-guard.test.py` (31) e `cd .agents/agents/qa-explorer && python3 -I qa-guard.test.py` (14).

### Fatos verificados que o harness usa

- **Claude Code** (Docs, "Hooks reference", "Create custom subagents", "Tools reference"): `PreToolUse` recebe `tool_name`, `tool_input`, `cwd` (os caminhos das ferramentas de arquivo chegam absolutos); nega com `hookSpecificOutput.permissionDecision: "deny"`; `deny` de hook vale até no auto mode; o frontmatter aceita `model`, `effort`, `tools`, `disallowedTools`, `permissionMode`, `hooks`, `isolation`; `disallowedTools: Bash(git push *)` remove o Bash inteiro; com a sessão principal em auto mode, o subagente herda o modo; **hooks do frontmatter exigem a pasta confiável e não rodam num `claude -p`**; os subagentes carregam no início da sessão; `isolation: worktree` nasce do branch padrão (descartado).
- **`agy` 1.3.1:** o `-p` exige o prompt por último; só carrega os MCP de `~/.gemini/config/mcp_config.json` (o do `agy mcp`); `--mode plan` não bloqueia escrita no `-p` e `--sandbox` só bloqueia o terminal; agentes em `.agents/agents/<nome>/agent.md` (`tools` como lista branca, sem `call_mcp_tool`; o MCP vem por `inheritMcp: true`); `hooks.json` roda com `sh -c` no diretório do arquivo e responde `{"decision": "allow|deny", "reason": ...}`; `agy models` lista `gemini-3.8-flash-high`. O `agy` tolera o `agent.md` do executor (frontmatter do Claude Code) na mesma pasta: o QA continuou rodando.
- **Configuração global (fora do repo):** Playwright MCP fixado em `@playwright/mcp@0.0.83 --headless` no `agy mcp` e no `agy` interativo, e `@0.0.83` no Claude Code (escopo user). O `agy` do Rafael está em `always-proceed` e **não deve ser endurecido** (a opção C foi testada e negava até o navegador).

## Prazo, fatias e execução

- **Prazo:** a semana começa **quando os três planos forem aprovados**; no máximo 4 a 5 h por dia; **nenhum corte de escopo**. Estimativa não oficial: 28 a 35 h.
- **Três fatias, cada uma com plano, branch e PR próprios** (`code-style.md`, "Branches e fatias"):
  1. `feat/mvp-1-base`: setup, Docker, CI, ruleset, Vercel, Neon e domínio com testes. **Primeira PR, feita em conjunto** (o Rafael nunca usou PR: abrir pelo site do GitHub, ler "Files changed", acompanhar o CI, corrigir na mesma branch).
  2. `feat/mvp-2-create-redirect`: criação (Google e rate limit), redirect, teste de concorrência, testes HTTP.
  3. `feat/mvp-3-manage`: página de gestão e README.
- QA por fatia (D6d): na 1, só as tarefas da home provisória e do `next.config.ts`; na 2, criação, redirect, páginas de status e rate limit; na 3, gestão, gráfico e desativação.

## Próximos passos

**1. Spec aprovada em 2026-10-08:**
- Estrutura: §1–3 contexto; §4 arquitetura (árvore de arquivos, ponto de montagem, logs); §5 domínio; §6 dados; §7 Safe Browsing; §8 entrada; §9 configuração; §10 erros; §11 testes; §12 fatias; §13 limitações; §14 notas sobre o AD-004; §15 alternativas; §16 requisitos (RF01–RF14, RNF01–RNF12).
- Acrescentado em 2026-10-08 (§4.1): fakes e auxiliares de teste em `__fakes__/`, protegidos pela trava do executor.
- **Detalhes de "como" aprovados com a spec** (não reabrir sem motivo novo): referrers em top 10 + "outros" (§5.9); R4 também recusa `.local`, `.home.arpa`, `.internal` e as faixas IPv4 de uso especial da RFC 6890 (§5.5); `site.com:8080/x` cai na R1 (§5.5); dois bancos no container, `shorturl` e `shorturl_test` (§9.7); textos das páginas 404, 429 e da prévia de bot (§8.6); `poweredByHeader: false` (§9.4); gestão com banco fora responde 200 (§8.5, §13); `CANARY`/`FRAME_ONLY` ignorados (§7.1); `RedirectService` no domínio (§5.8, §14); `UrlThreatChecker` devolve `'unavailable'` (§5.2); testes nunca leem `.env*` e recusam rodar fora de `127.0.0.1`/`localhost` (§9.8).
- Itens **(conferir na tarefa)**, que os planos precisam virar passo de verificação: `select` no `updateManyAndReturn` e um único `UPDATE … RETURNING` (senão `$queryRaw`); erros de conectividade do Prisma/`pg` (§6.5); API do `@upstash/ratelimit` (ler o código publicado); padrões dos UAs de bots; padrões da lista branca do ESLint; `revalidatePath` na desativação; `404` real da gestão sem `loading.tsx`; tipo do `defineConfig` com URL ausente.
- Valores de setup em aberto de propósito: `<MAJOR>` do Postgres e `<SHA completo>` das ações do CI; região da função, do Neon e do Upstash (a mesma para os três, §9.11).
- O status da spec muda para `Em andamento` quando a fatia 1 começar (`specs/README.md`).

**2. Quando o Rafael mandar (não antes): os planos.**
- `superpowers:writing-plans`, **três planos** em `docs/superpowers/plans/`, um por fatia, no formato do `spec-workflow.md` §7 (cabeçalho com **Branch de Trabalho**; o aviso "Para executores agenticos" já aponta para o `execution-workflow.md`).
- **Escritos para o executor:** cada tarefa diz os arquivos de contexto a ler, o teste que o Opus escreve primeiro (caminho e casos), os arquivos de produção que o executor cria, o comando de verificação, se o QA roda (gatilho D6d) e o critério de pronto. Tarefas pequenas, uma peça por vez (o Rafael acompanha e revisa cada uma).
- As tarefas de setup da fatia 1 que mexem em `package.json`, `.npmrc`, `.gitignore`, configs do Vitest ou `.github/` com dependências são do **Opus** (a trava barra o executor); o plano diz quem faz cada uma.
- Revisão do Rafael → aprovação → a semana começa → execução da fatia 1 na branch `feat/mvp-1-base`. Spec e planos vão direto na `main`.

**3. Na fatia 1 (não antecipar):** hooks de projeto quando existirem `lint`, `typecheck` e `test` (skill `update-config`; candidato: medir o limite de 12 mil caracteres); skills só quando algo se repetir (`superpowers:writing-skills`); `paths:`/`glob` só para arquivo que o agente comprovadamente deixe de ler.

## Pendências de setup (anotadas, sem decisão aberta)

- **Instalar o Docker** (hoje não há Docker nem Postgres) e escolher entre `sudo` e *rootless* (o grupo `docker` equivale a root). Necessário já na fatia 1 (migration `init`, testes de integração) e no QA (banco de dev).
- Versão major do Postgres ao criar o projeto no Neon (14 a 18); o `compose.yml` usa a mesma.
- Neon-Managed Integration na Vercel, com limpeza automática de branches; confirmar a **Standard Protection** nos previews (RC1).
- Chaves do Upstash e do Google também no ambiente **Preview** (RC4).
- `curl -I` para conferir o HSTS (RC6) e janela anônima para ver quais `*.vercel.app` abrem sem login (RC2).
- Ruleset da `main` e Deployment Checks na fatia 1; confirmar com um commit que falha de propósito que o `*.vercel.app` também fica retido.
- **Pré-requisito do Rafael:** projeto no Google Cloud + API key **restrita à Safe Browsing API** (`security-blocklist.md`).
- Sugestão sem prazo: levar o padrão núcleo + índice no `AGENTS.md` para a skill `novo-projeto` do Rafael (`~/.agents/skills/novo-projeto`).

## Harness de documentação (etapa 1, concluída em 2026-10-03)

Regras quebradas por assunto (commit `fbbfe7e`): núcleo sempre carregado + índice no `AGENTS.md`, o resto sob demanda; `CLAUDE.md` = `@AGENTS.md`; links em `.claude/rules/` só para o núcleo; regra = o quê e por quê, spec = como. Medição com `claude -p`: **65.459 → 39.073 tokens** de entrada. Fatos verificados: o Claude Code carrega os links de `.claude/rules/` e, com link + `@import`, o arquivo entra uma vez só; o Antigravity lê `AGENTS.md` (não o `CLAUDE.md`), usa `.agents/rules/` sem subpastas com `trigger:`, subagentes em `.agents/agents/`, skills em `.agents/skills/`, e o editor limita a regra a 12 mil caracteres e a `description` a 250.

## Excalidraw (documentação visual, no navegador do Rafael)

- **Estado (2026-10-08):** cena redesenhada do zero, 665 elementos, 7 seções (regras de negócio, stack, system design, fluxos, modelo de dados, entrega, requisitos RF/RNF). É o resumo visual; a verdade são os `.md`. **Não mostra o harness de execução** (não foi pedido).
- Exportado em `docs/diagrams/short-url-design.svg` (vai para o README) e `.png` (para LinkedIn e anexos). Cada novo PNG soma ~2 MB ao histórico do Git: **reexportar só em marcos** (fim de cada fatia).
- **Gerador:** `.superpowers/excalidraw/build-scene.js` (local, ignorado pelo Git), com o teste `test-build.js`. **Próxima edição: alterar o gerador e regravar a cena inteira, não remendar elementos.** Fluxo: teste no Node → colar a função na página → conferir o SHA-256 de `buildScene.toString()` → ensaio em `window.__newScene` → checagens de sobreposição → gravar → reabrir → print. A cena antiga (125 elementos) está no backup `excalidraw-backup-1791469337800` do `localStorage`, além de 7 backups anteriores.
- **Biblioteca de ícones do Rafael:** IndexedDB `excalidraw-library-db`, store `excalidraw-library-store`, chave `libraryData` (354 itens). Índices usados: 17 cadeado, 18 firewall, 19 usuário, 22 servidor, 23 nuvem, 41 Docker, 44 Redis, 50 `</>`, 51 Postgres, 52 GitHub, 55 janela de navegador, 63 Relational DB, 70 Cache, 280 Shield. Sem logos de Vercel, Next.js, Google nem Node.
- **Protocolo (claude-in-chrome + `localStorage`), só quando o Rafael pedir na própria mensagem:** ele fecha as abas do excalidraw.com → o agente abre uma aba sem tocar no canvas e confere a contagem → backup `excalidraw-backup-<ts>` → ensaio em memória com asserts → grava `excalidraw` + `version-dataState` → fecha a aba → avisa.
- **Armadilhas:** a página não busca arquivo de servidor local (colar o código e conferir o hash); tema escuro inverte cores claras; identificar elementos por texto exato, nunca por posição; aba em segundo plano não renderiza; a saída do `javascript_tool` é bloqueada com `=`, `?` ou `&` e cortada perto de 1.000 caracteres; o classificador nega neutralizar o `Storage.prototype.setItem` e gravar sem pedido explícito: **nunca tentar rota alternativa**.

## Como apresentar decisões (o que funcionou)

- **Formato:** de onde veio a decisão → **cenário concreto** → opções A/B/C em 1–2 frases com **mini linha do tempo** → **tabela curta sem jargão** → recomendação + fonte numa linha. A verificação das fontes fica fora da mensagem.
- "Explique mais a fundo": **analogia do cotidiano** → situações numeradas → tabela situação × opção com ✓/✗. Analogias com Java/Spring funcionam bem.
- Tema abstrato (harness, estrutura): árvore de pastas e exemplos encurtados. Tecnologia nova para ele: explicar a peça antes das opções e separar **produção** de **computador dele**.
- **Verificar antes de afirmar:** context7 para bibliotecas; firecrawl para docs (com `formats: ["query"]` e `mode: "directQuote"`; páginas grandes vão para arquivo e se leem com `python3 -I`); `npm view` para versões; `agy -p` para o Antigravity. **Ferramenta se mede.** **Biblioteca se lê no código publicado** (`npm pack` no scratchpad + `grep`).
- **Trava se mede de ponta a ponta** e com sondas **inofensivas se a trava falhar** (`--dry-run`, arquivo novo em vez de sobrescrever, `ls ~` em vez de ler segredo), com o fingerprint antes e depois.
- **Teste verde de primeira não basta:** conferir o **motivo** de cada negação. Foi assim que apareceram os furos de leitura fora do projeto.
- **Python que vai para o repo:** rodar `uvx ruff check --isolated --select S,PLW,B,E,F,UP,BLE,PTH,RUF` antes de entregar (o Rafael usa SonarQube e Ruff na IDE).
- **Delegar com teste de aceite:** escrever o teste antes, delegar a um modelo menor, rodar o teste e revisar.
- **Ao especificar o "como", reler a doc oficial da API** (referência do método, não só a visão geral).
- Perguntas de "por que aceitar esse risco?": análise concreta de impacto e, se couber, reforço barato na primeira barreira.

## O que não funcionou (não repetir)

- Mensagem de decisão densa, com jargão em células cheias.
- Deixar edições sem commit (Ctrl+Z apagou parte do trabalho em 2026-09-30).
- Terminar um turno sem resposta (o Rafael acha que perdeu perguntas).
- Afirmar texto de aviso sem checar os termos do provedor (a primeira R7 violava os termos do Google).
- Afirmar comportamento de ferramenta sem medir.
- Registrar decisão sem testar o ciclo inteiro (`USE_LOCAL_FAKES` no `.env.local`).
- Teste de aceite com palavra proibida sem limite de palavra (`\b` e maiúsculas; testar também o vocabulário obrigatório).
- Fechar regra de integração lendo só a visão geral da API (R7 × cache, corrigido na S4).
- **Trava fail-closed sem pensar nas ferramentas do próprio harness:** a primeira versão negava o `SubagentHandback` e o relatório do executor sumia. Ao mudar a lista branca, conferir as ferramentas que o Claude Code injeta no subagente.
- Propor configuração no lugar errado: "quando o QA roda" não cabe no hook (ele só vê uma chamada por vez); vai na regra e no `agent.md`.

## Repositório

- Público: https://github.com/ribeirorafadev/url-shortener (`origin` via SSH, autenticado como `ribeirorafadev`). A `main` tem documentação e o harness (agentes, travas e testes em Python); com o setup (CI + ruleset), passa a aceitar só PR com ✓.
- **Commit e push só com autorização explícita do Rafael na mensagem.** Conventional Commits (descrição em pt-BR), com o trailer do Claude.
- Tudo o que é commitado é público, inclusive este arquivo: **nunca registrar segredos nem caminhos pessoais**. `gh` e a CLI `vercel` não estão instalados.

## Preferências do Rafael

- pt-BR, direto, Markdown estruturado, **negrito** em termos críticos; decisão não trivial com fonte real (doc oficial, RFC, lei, OWASP).
- Quer entender os trade-offs antes de decidir; nunca apresentar decisão como fato consumado. Às vezes pede "explique melhor" depois de fechar: é aprendizado, não dúvida. Registrar só quando ele liberar.
- Base em Java/Spring e segurança; aprendendo Next.js, ORM e serverless; nunca usou Docker, Neon, CI nem PR. Quer **acompanhar cada tarefa** da implementação, porque precisa explicar cada parte numa entrevista.
- Usa SonarQube e Ruff na IDE e repassa os achados; trate como revisão de código (`superpowers:receiving-code-review`): analisar, corrigir com teste quando for comportamento, explicar quando for falso positivo.
- Ação destrutiva: relatório primeiro (o quê, onde, risco), autorização depois.
- Pode acionar o Antigravity CLI (`agy -p "..."`) para pesquisa web, QA e revisão.
