# short-url MVP, fatia 3 (gestão e README) — Plano de Implementação

> **Para executores agenticos:** execute pelo ciclo de `.agents/rules/execution-workflow.md` (teste do Opus → executor Sonnet → QA do Gemini quando a D6d mandar → revisão D7 → pausa com o Rafael), com `superpowers:subagent-driven-development` e os ajustes de lá. As etapas usam checkbox (`- [ ]`) para rastreamento.

**Objetivo:** entregar a página de gestão (`/manage/[token]`), com estatísticas, gráfico de 30 dias, QR e desativação com confirmação, e o README completo do PRD. Fecha o critério de "pronto" do MVP: criar → compartilhar → clicar → ver estatísticas → desativar, em produção.
**Arquitetura:** a página é um Server Component dinâmico que chama um *loader* testável em `src/app/_lib/`; o gráfico é um Server Component sem JavaScript no navegador (S5); a desativação é uma Server Action fina sobre um *handler* testável. O domínio (`getManagementView`, `deactivate`, `buildClickStats`) já existe desde a fatia 1.
**Stack Tecnológica:** Next.js 16.3.8 (App Router, Server Components, Server Actions), Prisma 7.10.0 (`groupBy` e o único `$queryRaw` do projeto), `qrcode@1.5.4`, `react-dom/server` nos testes do gráfico, Vitest 5.
**Spec:** `docs/superpowers/specs/2026-10-07-short-url-mvp-design.md`
**Branch de Trabalho:** `feat/mvp-3-manage`

## Como ler este plano

- **O como está na spec e não é repetido aqui** (`spec-workflow.md` §8). Cada tarefa cita a seção, e o executor lê a seção inteira. O plano traz a ordem, quem faz o quê, os **casos de teste com valores concretos**, os comandos de verificação e o critério de pronto.
- **Quem faz:** "Opus (setup)" mexe em `package.json`, `tests/`, `__fakes__/`, configs do Vitest, painéis ou documentação; "Opus testa → executor implementa" é o resto.
- **Os casos listados são o mínimo**; o Opus pode acrescentar, nunca tirar.
- 🔎 marca um item "(conferir na tarefa)" da spec.
- **Pré-condição:** a fatia 2 está na `main`; a branch nasce dela depois do merge (`git switch main && git pull && git switch -c feat/mvp-3-manage`).

## Ciclo padrão de uma tarefa "Opus testa → executor implementa"

1. **Teste (D1):** o Opus lê a tarefa, a seção da spec e os arquivos de contexto, e escreve o teste com os casos da tarefa.
2. **Vermelho:** roda o comando do teste e confere que falha **pelo motivo esperado**.
3. **Delegar (D2, D3):** `Agent` com `subagent_type: "executor"`:
   ```
   Tarefa <N> do plano docs/superpowers/plans/2026-10-08-short-url-mvp-3-manage.md (<nome>).
   Leia: a tarefa <N> inteira no plano; a spec, <seções>; <arquivos de contexto>.
   Testes vermelhos (não edite): <caminhos>.
   Crie ou altere só: <arquivos de produção>.
   Verificação: <comando do teste>; npm test; npm run lint; npm run typecheck.
   Relatório no formato do seu agent.md.
   ```
   Correção depois de uma devolução: `SendMessage` para o mesmo agente.
4. **Verde de verdade (D7.1):** o Opus roda o comando do teste, `npm test`, `npm run lint`, `npm run typecheck` e, quando a tarefa pedir, `npm run test:http`; `git diff --stat` confirma que nenhum teste mudou.
5. **QA (D6d):** só com "QA: sim". `npm run dev` com `USE_LOCAL_FAKES=true` e o banco `shorturl` do Docker; fingerprint antes e depois; `agy --agent qa-explorer --model gemini-3.8-flash-high -p "<URL base, o que a tarefa entregou, áreas>"`. Defeito → teste vermelho do Opus → passo 3.
6. **Revisão (D7):** os 9 itens; veredito `APROVADO` ou `DEVOLVIDO`; na 3ª devolução, para e leva ao Rafael.
7. **Pausa com o Rafael** e ledger em `.superpowers/sdd/mvp-3-manage/progress.md`.
8. **Commit só quando o Rafael mandar**; push só com autorização na mensagem.

Nas tarefas, "Steps finais: ciclo padrão" significa os passos 3 a 8 acima.

## Global Constraints

- Tudo das "Global Constraints" dos planos das fatias 1 e 2 continua valendo.
- **Nenhuma dependência nova**; Recharts recusada (S5): o gráfico é HTML/CSS renderizado no servidor.
- Gestão: o link é buscado **só pelo hash do token**, nunca pelo slug (IDOR); token fora do formato → `404` sem banco; token inexistente → a mesma `404` (spec §8.5, `error-map.md`).
- Headers da gestão: `Referrer-Policy: no-referrer`, `X-Robots-Tag: noindex`, `Cache-Control: no-store`, além dos globais (spec §8.5, §9.4).
- **Sem `loading.tsx`** em `src/app/manage/[token]/` (o `404` precisa ser `404` de verdade).
- Total de cliques pelo `click_count`; detalhamento só de humanos; bots num contador à parte; nota da RC8 só quando os humanos somam menos que o total (spec §5.9).
- Desativação irreversível, com confirmação, idempotente, sem rate limit; sem `serverActions.allowedOrigins` (spec §8.5).
- Destino e referrers exibidos só como texto (o React escapa); sem `dangerouslySetInnerHTML`.

## Review Focus

Entradas que a spec implica e nenhum caso da spec exercita, das mais prováveis de morder para as menos. Cada uma tem o teste na tarefa dona.

1. **Gráfico sem nenhum clique humano** (link novo, ou só prévias de bots): o maior dia é 0, e `count / max` vira `NaN%`. Esperado: barras com altura `0%`, sem `NaN`, e a nota da RC8 escondida quando `clickCount` também é 0. → Tarefas 2 e 3.
2. **Página de um link já desativado:** a spec não diz o que acontece com o botão. Esperado: estado "Desativado em DD/MM/AAAA às HH:MM" e **sem** o botão "Desativar" (a ação seria inócua e confunde). → Tarefa 4.
3. **Formulário de desativação forjado** (sem o campo `token`, `token` como arquivo, fora do formato): esperado "Não foi possível desativar: link não encontrado.", sem exceção e sem banco. → Tarefa 5.
4. **Link criado hoje e link com mais de 30 dias:** esperado 1 barra no primeiro e exatamente 30 no segundo. → Tarefa 2.
5. **Banco fora ao abrir a gestão:** esperado HTTP 200 com "Serviço indisponível. Tente novamente em instantes.", sem stack trace e sem 500 (limitação aceita da §13). → Tarefa 3.

## Ajustes na spec feitos por este plano

Detalhes de implementação novos (`spec-workflow.md` §8). **Aprovados pelo Rafael e aplicados na spec em 2026-10-08** (o comportamento do link desativado também no `manage-page.md`), junto com a coluna "Tarefa" da §16. A tabela fica aqui como histórico do porquê.

| § | Ajuste | Motivo |
|---|---|---|
| 4.1 | Acrescentar `src/app/_lib/manage-page-loader.ts`, `src/app/_lib/manage-labels.ts`, `src/app/_lib/deactivate-link-handler.ts` | Entrada fina testável sem servidor |
| 8.5 | `loadManagementPage(token, deps): Promise<{ kind: 'not-found' } \| { kind: 'unavailable' } \| { kind: 'ok'; view: ManagementView; shortUrl: string; qrCodeDataUrl: string \| null }>`; a página só renderiza o resultado | Testar 404, indisponível e QR sem servidor |
| 8.5 | `handleDeactivateLink(form, deps: { linkService: Pick<LinkService, 'deactivate'>; revalidate: (path: string) => void })`; a action só monta as dependências | Idem |
| 8.5 | Link desativado: a página mostra a data e esconde o botão "Desativar" | Review Focus 2 |
| 8.5 | Textos: rótulos de estado, de dispositivo e de total (Tarefa 3); `not-found.tsx` com "Página não encontrada" e "Confira se o endereço foi copiado inteiro." | A spec não fixava |
| 8.5 | Gráfico: altura `0%` quando o maior dia é 0; `title` no singular para 1 ("07/10: 1 clique") | Review Focus 1 |

## Rastreabilidade (coluna "Tarefa" da spec §16)

| Requisito | Tarefas |
|---|---|
| RF10 | 1, 2, 3, 4 |
| RF11 | 3, 4 |
| RF12 (tela) | 5 |
| RNF03 (gestão) | 4 |
| RNF11 | 3, 4, 6 |
| RNF12 | 6 |

---

### Task 1: Estatísticas no banco (`getStats`)

**Quem:** Opus testa → executor implementa. **QA:** não (banco).

**Contexto:** `data-model.md` (dia em Brasília, RC3), `manage-page.md` (RC8, RC9), `architecture-layers.md` (SQL cru só em template marcado), spec §6.4 (`getStats`), §5.2 (`RawClickStats`).

**Files:**
- Test: `src/data/prisma-click-event-repository.stats.int.test.ts`
- Modify: `src/data/prisma-click-event-repository.ts`

**Interfaces:**
- Produces: `getStats(linkId: number, dailyFrom: Date): Promise<RawClickStats>`.

- [ ] **Step 1: teste** (eventos inseridos com `clickedAt` explícito pelo Prisma):
  - `byDevice`: 3 `MOBILE`, 2 `DESKTOP`, 4 `BOT` → `{ MOBILE: 3, DESKTOP: 2, BOT: 4 }` (inclui `BOT`);
  - `byReferrer`: `google.com` ×2, `null` ×1 de humanos e `t.co` ×5 só de `BOT` → `[{ host: 'google.com', count: 2 }, { host: null, count: 1 }]` em qualquer ordem, **sem** `t.co`;
  - `daily`: clique em `2026-10-08T02:30:00Z` (23h30 do dia 7 em Brasília) → `day: '2026-10-07'`; clique em `2026-10-08T03:00:00Z` → `'2026-10-08'`; eventos `BOT` fora; evento antes de `dailyFrom` fora; `count` é `number` (`typeof === 'number'`), não `bigint`;
  - eventos de outro link não entram; link sem eventos → `{ byDevice: {}, byReferrer: [], daily: [] }`;
  - cliente para a porta fechada → `RepositoryUnavailableError`.
- [ ] **Step 2: vermelho.** `npx vitest run --project integration src/data/prisma-click-event-repository.stats.int.test.ts` → FAIL: `não implementado`.
- [ ] **Step 3: delegar.** Spec §6.4: duas consultas `groupBy` e o `$queryRaw` em template marcado, em `Promise.all`. 🔎 O tipo do resultado do `$queryRaw` é declarado à mão e conferido pelo teste.
- [ ] **Steps finais:** ciclo padrão (item 7: só `` $queryRaw`...` ``, nunca `Unsafe` nem `Prisma.raw`). Commit:
  `feat(data): agrega os cliques por dispositivo, referrer e dia em Brasília`

### Task 2: Gráfico diário (`daily-clicks-chart.tsx`)

**Quem:** Opus testa → executor implementa. **QA:** não nesta tarefa (o componente só aparece na página da Tarefa 4, que roda o QA).

**Contexto:** `manage-page.md` (S5, janela, RC9), spec §8.5 ("Gráfico"); W3C WAI, "Complex Images".

**Files:**
- Test: `src/components/daily-clicks-chart.test.tsx`
- Create: `src/components/daily-clicks-chart.tsx`

**Interfaces:**
- Consumes: `ClickStats['daily']`.
- Produces: `<DailyClicksChart daily={{ day: string; count: number }[]} />` (Server Component, sem `'use client'`).

- [ ] **Step 0 (Opus) 🔎:** confirmar que o projeto `unit` do Vitest transforma `.tsx` com o JSX automático do React (um teste mínimo com `renderToStaticMarkup(<p>x</p>)`); se não transformar, ajustar o `vitest.config.mts` (é do Opus) antes de escrever o teste.
- [ ] **Step 1: teste** (`renderToStaticMarkup` de `react-dom/server`):
  - `[{ '2026-10-06', 0 }, { '2026-10-07', 2 }, { '2026-10-08', 4 }]` → 3 barras com altura `0%`, `50%` e `100%`; `title` `06/10: 0 cliques`, `07/10: 2 cliques`, `08/10: 4 cliques`; um dia com 1 → `1 clique`;
  - **todos os dias com 0** → todas as alturas `0%`, nenhum `NaN` no HTML (Review Focus 1);
  - 1 dia → 1 barra; 30 dias → 30 barras (Review Focus 4);
  - rótulo `dias no horário de Brasília`; uma `<table>` com classe `sr-only`, uma linha por dia (`07/10` e `2`);
  - sem `<script` no HTML.
- [ ] **Step 2: vermelho.** `npx vitest run src/components/daily-clicks-chart.test.tsx` → FAIL: módulo inexistente.
- [ ] **Steps finais:** ciclo padrão. Commit: `feat(manage): desenha o gráfico de 30 dias no servidor, sem biblioteca`

### Task 3: *Loader* e rótulos da página de gestão

**Quem:** Opus testa → executor implementa. **QA:** não nesta tarefa (sem rota; a Tarefa 4 roda o QA).

**Contexto:** `manage-page.md`, `error-map.md` (gestão), `link-creation.md` (P1b), `url-validation.md` (RC2), spec §8.5 (passos 1 a 4), §5.7 (`ManagementView`), §5.9.

**Files:**
- Test: `src/app/_lib/manage-page-loader.test.ts`, `src/app/_lib/manage-labels.test.ts`
- Create: `src/app/_lib/manage-page-loader.ts`, `src/app/_lib/manage-labels.ts`

**Interfaces:**
- Consumes: `LinkService.getManagementView`, `isValidManageTokenFormat`, `resolveAppOrigin`, `generateQrCodeDataUrl`, `logError`.
- Produces: `loadManagementPage(token: string, deps: { linkService: Pick<LinkService, 'getManagementView'>; env: Record<string, string | undefined>; generateQrCode: (url: string) => Promise<string> })` (tipo do retorno nos "Ajustes na spec"); em `manage-labels.ts`: `describeLinkState(state: 'active' | GoneReason): string`, `formatClickTotal(clickCount: number, maxClicks: number | null, state: 'active' | GoneReason): string`, `formatDateTimeInSaoPaulo(date: Date): string`, `describeDevice(device: Exclude<DeviceType, 'BOT'>): string`, `describeReferrer(host: string | null): string`, `formatBotPreviews(count: number): string`.

- [ ] **Step 1: teste do *loader*** (`env = { APP_ORIGIN: 'http://localhost:3000' }`, `linkService` falso, espião no `console`):
  - token `'abc'` → `not-found`, e o `getManagementView` **não** é chamado;
  - token no formato e visão `null` → `not-found`;
  - `getManagementView` rejeita com `RepositoryUnavailableError` → `unavailable` e log `database-unavailable` (Review Focus 5);
  - `env = {}` → `unavailable` e `logError('app-origin-missing')`;
  - visão válida → `ok` com `shortUrl: 'http://localhost:3000/aB3xZ9k'` e o QR gerado a partir dele;
  - QR falhando → `ok` com `qrCodeDataUrl: null` e log `qr-failed` (P1b);
  - `Error` qualquer → o *loader* rejeita (a página de erro do Next responde 500);
  - nenhum log contém o token.
- [ ] **Step 2: teste dos rótulos:**
  - `describeLinkState`: `active` → `Ativo`; `deactivated` → `Desativado`; `expired` → `Expirado`; `exhausted` → `Limite de cliques atingido`;
  - `formatClickTotal`: `(8, null, 'active')` → `8 cliques`; `(1, null, 'active')` → `1 clique`; `(0, null, 'active')` → `0 cliques`; `(3, 10, 'active')` → `3 de 10 cliques`; `(10, 10, 'exhausted')` → `10 de 10 cliques · esgotado`;
  - `formatDateTimeInSaoPaulo(new Date('2026-10-08T15:05:00Z'))` → `08/10/2026 às 12:05`;
  - `describeDevice`: `MOBILE` → `Celular`; `DESKTOP` → `Computador`; `TABLET` → `Tablet`; `UNKNOWN` → `Desconhecido`;
  - `describeReferrer(null)` → `Direto ou desconhecido`; `describeReferrer('google.com')` → `google.com`;
  - `formatBotPreviews(0)` → `Nenhuma pré-visualização por bots`; `(1)` → `Pré-visualizado 1× por bots`; `(3)` → `Pré-visualizado 3× por bots`.
- [ ] **Step 3: vermelho.** `npx vitest run src/app/_lib/manage-page-loader.test.ts src/app/_lib/manage-labels.test.ts` → FAIL: módulos inexistentes.
- [ ] **Steps finais:** ciclo padrão. Commit: `feat(manage): carrega a visão de gestão com 404, indisponível e QR`

### Task 4: Página de gestão e testes HTTP

**Quem:** Opus testa → executor implementa. **QA:** sim (D6d: `src/app/`, `src/components/`). Áreas: **gestão** (sem a desativação, que é a Tarefa 5), **headers e páginas**.

**Contexto:** `manage-page.md`, `security-token.md`, `error-map.md`, spec §8.5, §9.4, §11 (HTTP da gestão).

**Files:**
- Test: `tests/http/manage.http.test.ts` (usa os auxiliares de `tests/http/helpers/database.ts` da fatia 2; acrescenta `insertLinkWithToken(token, ...)` e `insertClickEvent(...)`, que são do Opus)
- Create: `src/app/manage/[token]/page.tsx`, `src/app/not-found.tsx`

**Interfaces:**
- Consumes: `loadManagementPage`, os rótulos e o gráfico (Tarefas 2 e 3), `getLinkService()`.

- [ ] **Step 1: teste HTTP** (token fixo no formato, hash gravado no banco):
  - token válido → `200`; o corpo contém o link curto `http://localhost:3000/<slug>`, o destino, `Ativo`, o total (`3 de 10 cliques`), `Celular`, `google.com`, `Direto ou desconhecido`, `Pré-visualizado 2× por bots`, a `<img` do QR em `data:image/png;base64,` e o rótulo `dias no horário de Brasília`;
  - token no formato e inexistente → `404`; token `abc` → `404`; os dois com o mesmo corpo (`Página não encontrada`);
  - headers da gestão em todas as respostas acima: `Referrer-Policy: no-referrer`, `X-Robots-Tag: noindex`, `Cache-Control` contendo `no-store`, e o `Content-Security-Policy` global;
  - link com `click_count 10` e 8 eventos humanos → a nota `o detalhamento pode ficar um pouco abaixo do total` aparece; com 10 e 10 → não aparece;
  - **link desativado → `Desativado em` com a data e sem o botão `Desativar`** (Review Focus 2); link ativo → o botão existe;
  - destino com `<b>` na query, gravado direto no banco → aparece escapado (`&lt;b&gt;`), sem tag.
- [ ] **Step 2: vermelho.** `npm run test:http` → FAIL: a rota não existe (`404` para o token válido).
- [ ] **Step 3: delegar.** Spec §8.5 (passos 1 a 4) e o ajuste do link desativado. A página é Server Component dinâmico; `token` de `await params`; `notFound()` para `not-found`; a tela de indisponível para `unavailable`; o botão de desativar entra como espaço reservado (`<p>` com "Desativar") até a Tarefa 5. **Sem `loading.tsx`.**
  - 🔎 O `404` do token inexistente é `404` de verdade (o teste HTTP prova; se vier `200`, procurar *streaming* iniciado antes do `notFound()`).
- [ ] **Step 4: verificação.** Ciclo padrão mais `npm run test:http`.
- [ ] **Step 5: QA.** Antes, o Opus cria pela tela um link para `https://example.com/qa`, clica nele algumas vezes e passa o link de gestão no pedido. Áreas: gestão (sem desativar) e headers e páginas.
- [ ] **Steps finais:** revisão e pausa. Commit:
  `feat(manage): mostra as estatísticas, o gráfico e o QR na página de gestão`

### Task 5: Desativação com confirmação

**Quem:** Opus testa → executor implementa. **QA:** sim. Área: **gestão** (desativar).

**Contexto:** `manage-page.md` (irreversível, idempotente, IDOR), `error-map.md`, `security-core.md` (CSRF), spec §8.5 ("Desativação").

**Files:**
- Test: `src/app/_lib/deactivate-link-handler.test.ts`
- Create: `src/app/_lib/deactivate-link-handler.ts`, `src/app/actions/deactivate-link.ts`, `src/components/deactivate-link-form.tsx`
- Modify: `src/app/manage/[token]/page.tsx` (troca o espaço reservado pelo formulário)

**Interfaces:**
- Consumes: `LinkService.deactivate`, `RepositoryUnavailableError`, `logError`.
- Produces: `DeactivateState` (§8.5); `handleDeactivateLink(form: FormData, deps: { linkService: Pick<LinkService, 'deactivate'>; revalidate: (path: string) => void }): Promise<DeactivateState>`; `deactivateLink(prev: DeactivateState, form: FormData): Promise<DeactivateState>` (`'use server'`).

- [ ] **Step 1: teste:**
  - `deactivated` → `{ status: 'done', message: 'Link desativado.' }` e `revalidate('/manage/<token>')` chamado uma vez;
  - `already-deactivated` → o mesmo `done`;
  - `not-found` → `{ status: 'error', message: 'Não foi possível desativar: link não encontrado.' }`, sem `revalidate`;
  - **forjados** (Review Focus 3): sem o campo `token`, `token` como `File`, `token` `'abc'` → a mesma mensagem de não encontrado, e o `deactivate` não é chamado com nada que não seja string;
  - `deactivate` rejeita com `RepositoryUnavailableError` → `{ status: 'error', message: 'Não foi possível desativar agora. Tente em alguns minutos.' }` e log `database-unavailable`;
  - `Error` qualquer → a mesma mensagem de "agora" e log `unexpected-error`;
  - nenhum log contém o token.
- [ ] **Step 2: vermelho.** `npx vitest run src/app/_lib/deactivate-link-handler.test.ts` → FAIL: módulo inexistente.
- [ ] **Step 3: delegar.** *Handler* e action da §8.5 (a action passa `revalidatePath` como `revalidate`); `deactivate-link-form.tsx` (`'use client'`, `useActionState`): "Desativar" → "Tem certeza? Não dá para desfazer" com "Sim, desativar" e "Cancelar" → envia o token num `<input type="hidden">`; botão desabilitado durante o envio; mensagem do estado com `role="status"`. Sem `serverActions.allowedOrigins`.
  - 🔎 `revalidatePath` na página dinâmica: depois de "Sim, desativar", a página mostra `Desativado` sem recarregar à mão. Se não mostrar, o executor relata, e o Opus decide com o Rafael (por exemplo, `router.refresh()` no cliente).
- [ ] **Step 4: verificação.** Ciclo padrão mais `npm run test:http` (a página continua passando).
- [ ] **Step 5: QA.** Área: gestão (desativar pede confirmação; cancelar não desativa; depois de "Sim, desativar", o link curto dá `410`; repetir e voltar no histórico não quebram).
- [ ] **Step 6: roteiro manual do Rafael:** desativar com confirmação, pelo celular também.
- [ ] **Steps finais:** revisão e pausa. Commit: `feat(manage): desativa o link com confirmação e de forma idempotente`

### Task 6: README completo

**Quem:** Opus escreve; o Rafael revisa o texto. **QA:** não.

**Contexto:** `docs/superpowers/PRD.md` (critério de "pronto"), spec §12 (fatia 3), §13 (limitações), `HANDOFF.md` ("Limitações documentadas"), `architecture-local-dev.md`, `security-blocklist.md` (aviso de falsos positivos e negativos), `redirect.md` (P2, "um link por canal").

**Files:**
- Modify: `README.md`

- [ ] **Step 1:** reescrever o `README.md` em pt-BR, com:
  - descrição e link da demo em produção;
  - stack, com as versões;
  - diagrama de system design (`docs/diagrams/short-url-design.svg`) e link para o ADR;
  - destaques de engenharia (os do README atual, agora com os números reais: o teste de concorrência e as travas);
  - **como rodar localmente:** Node 24 e Docker, `docker compose up -d --wait`, `cp .env.example .env.development.local`, `npm ci`, `npm run db:migrate`, `npm run dev`, sem conta em nenhum serviço; como trocar para as chaves reais (`USE_LOCAL_FAKES=false`);
  - **como rodar os testes:** `npm run db:migrate:test`, `npm test`, `npm run test:http`;
  - **"um link por canal"** (UTMs no destino, P2);
  - **aviso de que a checagem do Google Safe Browsing pode ter falsos positivos e falsos negativos** (termos do Google);
  - **"como escalaria"**: os itens do "Fora de escopo" do PRD e as evoluções documentadas (cache de redirect, fila para os eventos, Web Risk, CSP com nonce, página de confirmação para links com limite);
  - **limitações**: todas as da spec §13;
  - execução guiada por IA (o ciclo *maker-checker*, com link para `execution-workflow.md`).
- [ ] **Step 2 (verificação):** todos os links relativos do README apontam para arquivos que existem (`grep -o '](\([^)]*\))' README.md` e conferir cada um); cada item do critério de "pronto" do PRD que fala do README está presente; os comandos de "rodar localmente" e "rodar os testes" foram executados do zero num clone limpo (`git clone` no scratchpad).
- [ ] **Step 3:** pausa com o Rafael (revisão do texto). Commit: `docs: escreve o README completo com como rodar, testes e limitações`

### Task 7: Fim do MVP: QA, roteiro manual, revisão, PR e produção

**Quem:** Opus e Rafael juntos. **QA:** sim (passada de fim de fatia). Áreas: **criação**, **redirect**, **gestão**, **headers e páginas**.

- [ ] **Step 1: QA da fatia,** com o fluxo inteiro: criar → abrir o link curto → ver o clique na gestão → desativar → `410`.
- [ ] **Step 2: roteiro manual** (spec §11) completo das fatias 2 e 3, inclusive o QR pela câmera e a desativação pelo celular.
- [ ] **Step 3: revisão da branch** (D5) com o Rafael, com o checklist D7 na branch e os requisitos da tabela "Rastreabilidade".
- [ ] **Step 4: documentação.** Marcar o status de cada requisito restante da §16 como `Implementado`; registrar na spec o que as tarefas mudaram no "como" (🔎); atualizar o `HANDOFF.md`. Reexportar o diagrama do Excalidraw **só se o Rafael pedir** (protocolo no `HANDOFF.md`).
- [ ] **Step 5: PR** `feat: página de gestão com estatísticas, QR e desativação`; o Rafael revisa, acompanha o CI e faz o merge.
- [ ] **Step 6: produção, critério de "pronto" do PRD item por item:** criar → compartilhar → clicar → estatísticas → desativar em produção; 404 e 410; `curl -I` na gestão com os três headers; Safe Browsing real recusando a URL de teste do Google; rate limit ativo; CI verde na `main`; README publicado.
- [ ] **Step 7:** status da spec em `docs/superpowers/specs/README.md` → `Implementada`; apagar a branch remota.
