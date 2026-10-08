# short-url MVP, fatia 2 (criação e redirect) — Plano de Implementação

> **Para executores agenticos:** execute pelo ciclo de `.agents/rules/execution-workflow.md` (teste do Opus → executor Sonnet → QA do Gemini quando a D6d mandar → revisão D7 → pausa com o Rafael), com `superpowers:subagent-driven-development` e os ajustes de lá. As etapas usam checkbox (`- [ ]`) para rastreamento.

**Objetivo:** criar links pela home (formulário, rate limit, Safe Browsing, card com token e QR) e redirecionar pelo link curto (302, 404, 410, 429, 503, bots e `HEAD`), com os adaptadores do banco, o teste de concorrência e os testes HTTP do redirect. Termina com a criação e o redirect funcionando em produção.
**Arquitetura:** os adaptadores (`src/data/` com Prisma; `src/infra/` com o Google) implementam as portas do domínio da fatia 1. A entrada é fina: `route.ts` e as Server Actions só montam as dependências e chamam *handlers* em `src/app/_lib/`, testados sem servidor. O ponto de montagem (`services.ts`) é o único lugar que instancia adaptadores.
**Stack Tecnológica:** Prisma 7.10.0 + `@prisma/adapter-pg` + `pg`, `@vercel/functions` (`attachDatabasePool`, `ipAddress`), `@upstash/ratelimit` + `@upstash/redis`, Google Safe Browsing v5 por `fetch` e `crypto.subtle`, `qrcode@1.5.4`, React 19 (`useActionState`), Vitest 5.
**Spec:** `docs/superpowers/specs/2026-10-07-short-url-mvp-design.md`
**Branch de Trabalho:** `feat/mvp-2-create-redirect`

## Como ler este plano

- **O como está na spec e não é repetido aqui** (`spec-workflow.md` §8). Cada tarefa cita a seção, e o executor lê a seção inteira. O plano traz a ordem, quem faz o quê, os **casos de teste com valores concretos**, os comandos de verificação e o critério de pronto.
- **Quem faz:** "Opus (setup)" mexe em `package.json`, `tests/`, `__fakes__/`, configs do Vitest ou painéis (a trava do executor barra esses caminhos, D4). "Opus testa → executor implementa" é o resto.
- **Os casos listados são o mínimo**; o Opus pode acrescentar, nunca tirar.
- 🔎 marca um item "(conferir na tarefa)" da spec, que vira passo de verificação.
- **Pré-condição:** a fatia 1 está na `main`, e a branch nasce dela depois do merge (`git switch main && git pull && git switch -c feat/mvp-2-create-redirect`). O `npm run db:migrate:test` já foi rodado no `shorturl_test`.

## Ciclo padrão de uma tarefa "Opus testa → executor implementa"

1. **Teste (D1):** o Opus lê a tarefa, a seção da spec e os arquivos de contexto, e escreve o teste com os casos da tarefa.
2. **Vermelho:** roda o comando do teste e confere que falha **pelo motivo esperado**.
3. **Delegar (D2, D3):** `Agent` com `subagent_type: "executor"`:
   ```
   Tarefa <N> do plano docs/superpowers/plans/2026-10-08-short-url-mvp-2-create-redirect.md (<nome>).
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
7. **Pausa com o Rafael** e ledger em `.superpowers/sdd/mvp-2-create-redirect/progress.md`.
8. **Commit só quando o Rafael mandar**; push só com autorização na mensagem.

Nas tarefas, "Steps finais: ciclo padrão" significa os passos 3 a 8 acima.

## Global Constraints

- Tudo da seção "Global Constraints" do plano da fatia 1 continua valendo (versões exatas, dependências recusadas, AD-004, kebab-case, pt-BR na interface).
- **Nenhuma dependência nova nesta fatia**: tudo o que ela usa foi instalado na Tarefa 1 da fatia 1.
- Timeouts: banco `connectionTimeoutMillis: 5000` e `idleTimeoutMillis: 5000`; Upstash `timeout: 1000`; Google `AbortSignal.timeout(2000)` (RNF09, spec §6.2, §7.1, §8.2).
- Rate limit: criação 10/min e depois 100/dia; redirect 300/min; chave `/64` no IPv6; `local-dev` só com `NODE_ENV === 'development'` (spec §8.2).
- Redirect: formato do slug antes de tudo; 302 com `Cache-Control: no-store`; `Location` = `href` gravado; query do link curto ignorada; `HEAD` e bots nunca incrementam; só link ativo gera evento; evento gravado no `after()` com valores já classificados (spec §8.4).
- Fail-open no redirect (rate limit) e fail-closed na criação (rate limit, Google, IP ausente, origem ausente) (spec §8.2, §8.3).
- Logs só com as chaves `slug`, `reason`, `errorName`, `variable`, `status`; **nunca** token, hash, URL de destino, IP, UA nem a URL da chamada ao Google (spec §4.4).
- Mensagens exatamente as do `.agents/context/error-map.md` e da tabela da spec §8.6.
- Páginas de status sem `<script>` e sem interpolar nada da requisição nem do link (RC6).
- `serverActions.allowedOrigins` **nunca** configurado (CSRF embutido).

## Review Focus

Entradas que a spec implica e nenhum caso da spec exercita, das mais prováveis de morder para as menos. Cada uma tem o teste na tarefa dona.

1. **`FormData` forjado com arquivo no lugar de texto ou com campo repetido** (`url` como `File`, dois `maxClicks`): `form.get()` devolve um `File`, e um `.trim()` direto vira `TypeError` e a mensagem genérica. Esperado: erro de formato do campo, sem exceção. → Tarefa 16.
2. **Query string no link curto** (`/aB3xZ9k?next=https://evil.com`): esperado o `Location` igual ao destino gravado, sem nada anexado (P2). → Tarefa 15.
3. **`x-real-ip` com porta ou zona** (`203.0.113.7:51234`, `fe80::1%eth0`): esperado `null` (conta como IP ausente: redirect segue, criação recusa), nunca uma chave com lixo. → Tarefa 10.
4. **Resposta do Google sem `cacheDuration` ou com valor fora do formato** (`"abc"`, `"-5s"`): esperado `'unavailable'` e nada gravado no cache (validade `NaN` nunca expiraria ou expiraria sempre). → Tarefa 6.
5. **Destino com caracteres fora do ASCII** (`https://exemplo.com/ação`): esperado `Location` ASCII igual ao `href` gravado (B-2); um header com caractere fora do ASCII faria o `new Response` lançar e virar `503`. → Tarefa 15.

## Ajustes na spec feitos por este plano

Detalhes de implementação novos (`spec-workflow.md` §8). **Aprovados pelo Rafael e aplicados na spec em 2026-10-08**, junto com a coluna "Tarefa" da §16. A tabela fica aqui como histórico do porquê.

| § | Ajuste | Motivo |
|---|---|---|
| 4.1 | Acrescentar `src/app/_lib/create-link-handler.ts`, `src/components/expiration-label.ts`, `tests/http/helpers/database.ts` | Entrada fina testável sem servidor (`architecture-testing-ci.md`) |
| 4.3 | Quinto *getter*: `getUrlThreatChecker(): UrlThreatChecker` (o `getLinkService` o usa) | Testar a escolha do adaptador sem rede nem banco |
| 6.2 | `createPrismaClient(options: { connectionString: string; max?: number; connectionTimeoutMillis?: number; logQueries?: boolean }): { prisma: PrismaClient; pool: Pool }`; o `getPrismaClient()` usa essa fábrica e o `attachDatabasePool` | O teste de concorrência (pool de 20), o de erro de conexão (porta fechada) e o log de queries precisam de clientes próprios |
| 6.5 | `isDatabaseUnavailableError(error: unknown): boolean` e `withDatabaseErrors<T>(operation: () => Promise<T>): Promise<T>` (traduz para `RepositoryUnavailableError` com `cause`) | Um lugar só para a tradução |
| 8.2 | `UpstashRateLimiter` recebe os três limitadores (`{ limit(key): Promise<{ success: boolean; reset: number; reason?: string }> }`); `createUpstashRateLimiter(env)` monta os reais; `rateLimitPrefix(vercelEnv, scope)` é função pura; `InMemoryRateLimiter` recebe `now?: () => number` | Testar as decisões sem rede |
| 8.3 | `FormFieldError` = `{ field: 'url'; code: 'required' \| 'too-long' } \| { field: 'maxClicks'; code: 'not-integer' } \| { field: 'expiration'; code: 'both' \| 'invalid-duration' \| 'invalid-date' }`; `toCreateLinkErrorState(failure: CreateLinkFailure)` (tipo na Tarefa 17); `handleCreateLink(form, deps)` em `create-link-handler.ts`; a action só monta as dependências | Assinaturas que a spec deixou em aberto; entrada fina |
| 8.3 | `formatExpirationLabel(date: string, now: Date): { kind: 'today' } \| { kind: 'date'; formatted: string }` em `src/components/expiration-label.ts` | Testar o rótulo da P7 sem navegador |
| 8.4 | `handleRedirect(request, slug, method, deps: { redirectService; clickEvents; rateLimiter; scheduleAfter: (task: () => Promise<void>) => void; nodeEnv })`; o `route.ts` passa o `after` real | Testar o handler sem servidor |

## Rastreabilidade (coluna "Tarefa" da spec §16)

| Requisito | Tarefas |
|---|---|
| RF01 | 18, 19, 20, 21 |
| RF02, RF03 (tela) | 16, 20 |
| RF04 (mensagens) | 17, 20 |
| RF05 | 5, 6, 7, 17 |
| RF06 | 19, 21 |
| RF07 | 14, 15 |
| RF08 | 4, 15 |
| RF09 | 15 |
| RF13 | 21 |
| RF14 (falsos) | 7, 11, 13 |
| RNF01 | 3 |
| RNF02 | 10, 11, 12, 15, 19 |
| RNF04 | 8, 19, 21 |
| RNF05 | 4, 15 |
| RNF09 | 1, 6, 12 |
| RNF11 | 14, 17, 20, 21 |

---

### Task 1: Client do Prisma e tradução dos erros de conexão

**Quem:** Opus testa → executor implementa. **QA:** não (banco).

**Contexto:** `architecture-persistence.md` (pool, timeouts, D1), `architecture-layers.md`, spec §6.2, §6.5.

**Files:**
- Test: `src/data/prisma-client.int.test.ts`, `src/data/database-errors.int.test.ts`
- Create: `src/data/prisma-client.ts`, `src/data/database-errors.ts`

**Interfaces:**
- Consumes: `RepositoryUnavailableError` (`src/domain/errors.ts`).
- Produces: `createPrismaClient(options): { prisma: PrismaClient; pool: Pool }`, `getPrismaClient(): PrismaClient`, `isDatabaseUnavailableError(error: unknown): boolean`, `withDatabaseErrors<T>(operation: () => Promise<T>): Promise<T>`.

- [ ] **Step 1: teste.**
  - `prisma-client.int.test.ts`: `createPrismaClient({ connectionString: process.env.DATABASE_URL! })` responde `` $queryRaw`select 1 as ok` ``; o `pool` devolvido tem `options.max` = 20 quando pedido, e `idleTimeoutMillis`/`connectionTimeoutMillis` = 5000 por padrão; `getPrismaClient()` devolve a mesma instância duas vezes; com `DATABASE_URL` apagada (`vi.stubEnv('DATABASE_URL', '')` e `vi.resetModules()`), `getPrismaClient()` lança erro que cita `DATABASE_URL` e não contém nenhuma URL.
  - `database-errors.int.test.ts`:
    - cliente para `127.0.0.1:1` (porta fechada) → a operação falha, `isDatabaseUnavailableError(e) === true`, e `withDatabaseErrors(() => op)` rejeita com `RepositoryUnavailableError` cujo `cause` é o erro original;
    - servidor TCP local mudo (`node:net` que aceita e nunca responde) com `connectionTimeoutMillis: 300` → `RepositoryUnavailableError`;
    - `P2002` real (slug repetido) → `withDatabaseErrors` repassa o erro original, **sem** traduzir;
    - `new Error('x')` → repassa sem traduzir.
- [ ] **Step 2: vermelho.** `npx vitest run --project integration src/data/prisma-client.int.test.ts src/data/database-errors.int.test.ts` → FAIL: módulos inexistentes.
- [ ] **Step 3: delegar.** Spec §6.2, §6.5 e os ajustes 6.2 e 6.5.
  - 🔎 Caminho do `PrismaClient` gerado: o anotado no ledger da fatia 1.
  - 🔎 Lista dos erros de conectividade: o executor imprime (num teste local temporário, apagado antes de entregar) o `name`, o `code` e a cadeia de `cause` dos erros reais dos dois cenários e baseia o `isDatabaseUnavailableError` neles; a lista final vai no relatório e no ledger. Prova com o Postgres parado de verdade (`docker compose stop postgres`, rodado pelo Opus no passo 4): a operação vira `RepositoryUnavailableError`.
  - 🔎 `$disconnect()` não fecha um pool externo: os testes encerram o `pool` com `pool.end()`.
- [ ] **Steps finais:** ciclo padrão. Commit: `feat(data): cria o client do Prisma com pool e traduz falhas de conexão`

### Task 2: `PrismaLinkRepository` (gravação, leitura e desativação)

**Quem:** Opus testa → executor implementa. **QA:** não.

**Contexto:** `data-model.md`, `link-lifecycle.md` (colisão na gravação), `manage-page.md` (idempotência), spec §6.3 (menos `consumeClick`).

**Files:**
- Test: `src/data/prisma-link-repository.int.test.ts`
- Create: `src/data/prisma-link-repository.ts`

**Interfaces:**
- Consumes: `LinkRepository`, `NewLink`, `LinkSnapshot` (domínio); `withDatabaseErrors` (Tarefa 1).
- Produces: `class PrismaLinkRepository implements LinkRepository { constructor(prisma: PrismaClient) }` (`consumeClick` lança `Error('não implementado')` até a Tarefa 3).

- [ ] **Step 1: teste** (hash de 32 bytes fixo por caso; `now = 2026-10-08T12:00:00.000Z`):
  - `insert` → `{ status: 'created', id }` com `id > 0`; mesmo slug de novo → `{ status: 'slug-taken' }`; outro slug com o mesmo `manageTokenHash` → rejeita (não é `slug-taken`);
  - `findBySlug` devolve o `LinkSnapshot` completo (datas como `Date`, `clickCount 0`); inexistente → `null`; `'ABCDEFG'` e `'abcdefg'` são links diferentes (caixa importa);
  - `findByTokenHash` acha pelo hash; hash desconhecido → `null`;
  - `deactivateByTokenHash(hash, now)` → `'deactivated'` e `deactivatedAt = now`; de novo com `now + 1 h` → `'unchanged'`, e a data continua `now`; hash desconhecido → `'unchanged'`;
  - repositório com cliente para a porta fechada → `findBySlug` rejeita com `RepositoryUnavailableError`.
- [ ] **Step 2: vermelho.** `npx vitest run --project integration src/data/prisma-link-repository.int.test.ts` → FAIL: módulo inexistente.
- [ ] **Steps finais:** ciclo padrão (item 7: o `P2002` é identificado pelo campo `slug` do erro, não por texto da mensagem). Commit:
  `feat(data): grava e busca links e desativa pelo hash do token`

### Task 3: UPDATE atômico (`consumeClick`) e teste de concorrência

**Quem:** Opus testa → executor implementa. **QA:** não.

**Contexto:** `redirect.md` (Incremento atômico), `architecture-layers.md` (RC3), spec §6.3 (`consumeClick`), §11 (concorrência).

**Files:**
- Test: `src/data/prisma-link-repository.consume-click.int.test.ts`
- Modify: `src/data/prisma-link-repository.ts`

**Interfaces:**
- Produces: `consumeClick(slug: string, now: Date): Promise<{ id: number; destinationUrl: string } | null>`.

- [ ] **Step 1: teste** (`now = 2026-10-08T12:00:00.000Z`):
  - ativo sem limite → `{ id, destinationUrl }`, `click_count` 1;
  - limite 10 com 9 → devolve e vai a 10; a chamada seguinte → `null` e continua 10;
  - desativado → `null`, `click_count` inalterado;
  - **`expires_at = now` → `null`** (fronteira igual à do domínio); `expires_at = now + 1 ms` → devolve;
  - inexistente → `null`;
  - 🔎 **uma instrução só:** cliente com `logQueries: true`; durante um `consumeClick` sai exatamente **uma** instrução contra `links`, um `UPDATE` com `RETURNING`, e nenhum `SELECT`. Se aparecerem `BEGIN`/`COMMIT` em volta, anotar e levar ao Rafael antes de aprovar (latência no caminho quente);
  - **concorrência (RNF01):** link com `max_clicks = 100`; cliente com `max: 20`; 150 chamadas simultâneas (`Promise.all`) → exatamente 100 resultados não nulos e `click_count = 100`. Repetido 5 vezes no mesmo teste, com link novo a cada rodada.
- [ ] **Step 2: vermelho.** `npx vitest run --project integration src/data/prisma-link-repository.consume-click.int.test.ts` → FAIL: `não implementado`.
- [ ] **Step 3: delegar.** `updateManyAndReturn` da §6.3. Se o teste de "uma instrução só" falhar porque o Prisma divide a operação, trocar pelo `$queryRaw` com o SQL da §6.3 (RC3), registrar no relatório e mapear `destination_url` → `destinationUrl`.
- [ ] **Steps finais:** ciclo padrão (item 7: nada de `$queryRawUnsafe`). Commit:
  `feat(data): consome o clique num UPDATE atômico com teste de concorrência`

### Task 4: `PrismaClickEventRepository.record`

**Quem:** Opus testa → executor implementa. **QA:** não.

**Contexto:** `data-model.md` (sem IP, só categoria e host), `redirect.md` (Registro detalhado), spec §6.4 (`record`).

**Files:**
- Test: `src/data/prisma-click-event-repository.int.test.ts`
- Create: `src/data/prisma-click-event-repository.ts`

**Interfaces:**
- Produces: `class PrismaClickEventRepository implements ClickEventRepository { constructor(prisma: PrismaClient) }` (`getStats` lança `Error('não implementado')` até a fatia 3).

- [ ] **Step 1: teste:** `record({ linkId, deviceType: 'MOBILE', referrerHost: 'google.com' })` → uma linha com esses valores e `clicked_at` a menos de 5 s do `now()` do banco; `referrerHost: null` → coluna nula; `deviceType: 'BOT'` aceito; `linkId` inexistente → rejeita com erro de FK, **não** `RepositoryUnavailableError`; cliente para a porta fechada → `RepositoryUnavailableError`.
- [ ] **Step 2: vermelho.** `npx vitest run --project integration src/data/prisma-click-event-repository.int.test.ts` → FAIL: módulo inexistente.
- [ ] **Steps finais:** ciclo padrão. Commit: `feat(data): grava o evento de clique`

### Task 5: Canonicalização e expressões do Safe Browsing

**Quem:** Opus testa → executor implementa. **QA:** não.

**Contexto:** `security-blocklist.md` (S3), `url-validation.md` (R7), spec §7.1 ("Expressões"); Google, Safe Browsing v5 e v4, "URLs and Hashing".

**Files:**
- Test: `src/infra/safe-browsing-expressions.test.ts`
- Create: `src/infra/safe-browsing-expressions.ts`

**Interfaces:**
- Produces: `canonicalize(href: string): string`, `buildExpressions(canonical: string): string[]` (sem o esquema, como `host/caminho`, no máximo 30, sem repetição).

- [ ] **Step 0 (Opus) 🔎:** abrir "URLs and Hashing" da v4 e da v5 (firecrawl, `formats: ["query"]`, `mode: "directQuote"`), copiar os exemplos de canonicalização cuja entrada é um `href` válido do WHATWG (o `canonicalize` sempre recebe o `href` do `UrlValidator`) e anotar a fonte num comentário do teste.
- [ ] **Step 1: teste.**
  - `canonicalize` (casos da doc conferidos no Step 0; ponto de partida): `http://host/%25%32%35` → `http://host/%25`; `http://host/%25%32%35%25%32%35` → `http://host/%25%25`; `http://host/%2525252525252525` → `http://host/%25`; `http://host/asdf%25%32%35asd` → `http://host/asdf%25asd`; `http://www.google.com/blah/..` → `http://www.google.com/`; `http://www.evil.com/blah#frag` → `http://www.evil.com/blah`; `http://www.google.com.../` → `http://www.google.com/`; `http://www.google.com/q?r?s` → `http://www.google.com/q?r?s`; `http://evil.com/foo;` → `http://evil.com/foo;`; `http://www.gotaport.com:1234/` → `http://www.gotaport.com/`; `http://host.com//twoslashes?more//slashes` → `http://host.com/twoslashes?more//slashes`; `http://host.com/ab%23cd` → `http://host.com/ab%23cd`; `http://195.127.0.11/uploads/%20%20%20%20/.verify/` → igual.
  - `buildExpressions`:
    - `http://a.b.c/1/2.html?param=1` → exatamente `a.b.c/1/2.html?param=1`, `a.b.c/1/2.html`, `a.b.c/`, `a.b.c/1/`, `b.c/1/2.html?param=1`, `b.c/1/2.html`, `b.c/`, `b.c/1/` (8, em qualquer ordem);
    - `http://a.b.c.d.e.f.g/1.html` → hosts `a.b.c.d.e.f.g`, `c.d.e.f.g`, `d.e.f.g`, `e.f.g`, `f.g` (nunca `b.c.d.e.f.g` nem `g`) × caminhos `/1.html` e `/` = 10;
    - `http://1.2.3.4/1/` → `1.2.3.4/1/` e `1.2.3.4/` (IP sem sufixos);
    - `https://example.co.uk/` → `example.co.uk/` e `co.uk/` (desvio consciente da S3, sem `uk/`);
    - `https://a.b.c.d.e.f.com/1/2/3/4/5/6.html?x=1` → 30 expressões (5 hosts × 6 caminhos: com query, sem query, `/`, `/1/`, `/1/2/`, `/1/2/3/`);
    - `https://exemplo.com/` → só `exemplo.com/` (sem repetição).
- [ ] **Step 2: vermelho.** `npx vitest run src/infra/safe-browsing-expressions.test.ts` → FAIL: módulo inexistente.
- [ ] **Steps finais:** ciclo padrão. Commit:
  `feat(infra): canonicaliza a URL e gera as expressões do Safe Browsing`

### Task 6: `SafeBrowsingUrlThreatChecker` (consulta, cache e fail-closed)

**Quem:** Opus testa → executor implementa. **QA:** não (rede externa; o falso local cobre a tela).

**Contexto:** `security-blocklist.md` (B1, S4, API key), `url-validation.md` (R7), spec §7.1; Google, referência do `hashes.search` (v5).

**Files:**
- Test: `src/infra/safe-browsing-url-threat-checker.test.ts`
- Create: `src/infra/safe-browsing-url-threat-checker.ts`

**Interfaces:**
- Consumes: `UrlThreatChecker`, `ThreatVerdict` (domínio); `canonicalize`, `buildExpressions` (Tarefa 5).
- Produces: `class SafeBrowsingUrlThreatChecker implements UrlThreatChecker { constructor(deps: { apiKey: string; fetch?: typeof fetch; now?: () => number; maxCacheEntries?: number }) }`.

- [ ] **Step 1: teste** (`fetch` falso que registra as chamadas; relógio injetado; `apiKey: 'chave-secreta-de-teste'`; o Opus calcula os hashes no próprio teste com `crypto.subtle`):
  - **pedido:** um único `GET` para `https://safebrowsing.googleapis.com/v5/hashes:search`, com `key=chave-secreta-de-teste`, um `hashPrefixes` por prefixo distinto (4 bytes em base64 padrão), **sem** o texto da URL nem do host na URL do pedido, e com um `signal`;
  - **acerto:** resposta com o hash completo de `exemplo.com/` e `threatType: 'MALWARE'` → `'dangerous'`; o mesmo com `SOCIAL_ENGINEERING`, `UNWANTED_SOFTWARE` e `POTENTIALLY_HARMFUL_APPLICATION`;
  - **descartes:** só detalhe com atributo `CANARY` → `'safe'`; só `FRAME_ONLY` → `'safe'`; `threatType` desconhecido → `'safe'`; hash completo que não é de nenhuma expressão → `'safe'`;
  - **vazio:** `{ cacheDuration: '300s' }` → `'safe'`;
  - **falhas → `'unavailable'`:** `fetch` rejeita com `DOMException` `TimeoutError`; `fetch` rejeita com `TypeError('fetch failed')`; status 429; status 500; corpo que não é JSON; `fullHashes` que não é lista; **sem `cacheDuration`; `cacheDuration: 'abc'`; `cacheDuration: '-5s'`** (Review Focus 4: e a chamada seguinte vai à rede de novo, prova de que nada foi gravado);
  - **cache (S4):** segunda consulta da mesma URL dentro do prazo → sem rede; `'3.5s'` vale 3.500 ms; consulta depois de vencer → rede de novo; **nunca estendido**: consultas aos 200 s e aos 299 s usam o cache, aos 301 s vão à rede (prazo de 300 s contado da gravação); URL B do mesmo host com outro caminho → o pedido leva só os prefixos que faltam no cache; resposta vazia também é guardada;
  - **teto:** `maxCacheEntries: 3` → depois de gravar mais de 3 prefixos, a URL mais antiga volta a ir à rede;
  - **sigilo:** espião em `console.log/info/warn/error/debug` durante todos os casos → nenhuma chamada contém `chave-secreta-de-teste`, `key=` nem `exemplo.com`.
- [ ] **Step 2: vermelho.** `npx vitest run src/infra/safe-browsing-url-threat-checker.test.ts` → FAIL: módulo inexistente.
- [ ] **Steps finais:** ciclo padrão (item 7: a URL montada nunca vai para log nem para mensagem de erro). Commit:
  `feat(infra): consulta o Safe Browsing v5 por prefixos de hash com cache e fail-closed`

### Task 7: Checadores falso local e indisponível

**Quem:** Opus testa → executor implementa. **QA:** não.

**Contexto:** `architecture-local-dev.md`, `security-rate-limit.md` (RC4), spec §7.2, §7.3.

**Files:**
- Test: `src/infra/fake-and-unavailable-url-threat-checkers.test.ts`
- Create: `src/infra/local-fake-url-threat-checker.ts`, `src/infra/unavailable-url-threat-checker.ts`

**Interfaces:**
- Produces: `class LocalFakeUrlThreatChecker implements UrlThreatChecker`, `class UnavailableUrlThreatChecker implements UrlThreatChecker`.

- [ ] **Step 1: teste:** falso local → `'dangerous'` para `https://testsafebrowsing.appspot.com/s/phishing.html` e `.../s/malware.html`; `'safe'` para `https://exemplo.com/` e para `https://testsafebrowsing.appspot.com/s/outra.html`; `fetch` global espionado nunca é chamado. Indisponível → `'unavailable'` para qualquer URL, sem rede.
- [ ] **Step 2: vermelho.** `npx vitest run src/infra/fake-and-unavailable-url-threat-checkers.test.ts` → FAIL: módulos inexistentes.
- [ ] **Steps finais:** ciclo padrão. Commit: `feat(infra): cria os checadores falso local e indisponível`

### Task 8: Logs com lista branca (`log.ts`)

**Quem:** Opus testa → executor implementa. **QA:** não nesta tarefa (exceção da D6d: sem rota que use o arquivo; o QA da Tarefa 15 cobre).

**Contexto:** `security-core.md` (o que nunca vai para log), spec §4.4.

**Files:**
- Test: `src/app/_lib/log.test.ts`
- Create: `src/app/_lib/log.ts`

**Interfaces:**
- Produces: `LogEvent`, `SafeLogFields`, `logError(event: LogEvent, fields?: SafeLogFields): void`, `logWarn(event: LogEvent, fields?: SafeLogFields): void`.

- [ ] **Step 1: teste:** `logError('database-unavailable', { slug: 'aB3xZ9k', errorName: 'PrismaClientInitializationError' })` → uma chamada de `console.error` com **uma** string JSON com `level: 'error'`, `event` e os campos; `logWarn` usa `console.warn`; um objeto com chaves extras (`{ slug, token: 'x', url: 'https://...' } as never`) → só o `slug` sai (a lista branca vale em tempo de execução, não só no tipo); valores que não são string nem número são descartados.
- [ ] **Step 2: vermelho.** `npx vitest run src/app/_lib/log.test.ts` → FAIL: módulo inexistente.
- [ ] **Steps finais:** ciclo padrão. Commit: `feat(app): loga em JSON só com campos da lista branca`

### Task 9: Origem canônica (`resolveAppOrigin`)

**Quem:** Opus testa → executor implementa. **QA:** não nesta tarefa (exceção da D6d: sem rota que use o arquivo; o QA da Tarefa 20 cobre).

**Contexto:** `url-validation.md` (R3, RC2), spec §8.1.

**Files:**
- Test: `src/app/_lib/app-origin.test.ts`
- Create: `src/app/_lib/app-origin.ts`

**Interfaces:**
- Produces: `AppOrigin`, `resolveAppOrigin(env: Record<string, string | undefined>): AppOrigin | null`.

- [ ] **Step 1: teste (tabela):**

  | Variáveis | `origin` | `ownHosts` |
  |---|---|---|
  | `APP_ORIGIN=http://localhost:3000` | `http://localhost:3000` | `['localhost']` |
  | `APP_ORIGIN=https://Short.Example.app/` | `https://short.example.app` | `['short.example.app']` |
  | `APP_ORIGIN` + `VERCEL_PROJECT_PRODUCTION_URL=short-url.vercel.app` | o do `APP_ORIGIN` | `['localhost', 'short-url.vercel.app']` |
  | `VERCEL_ENV=production`, `VERCEL_PROJECT_PRODUCTION_URL=short-url.vercel.app` | `https://short-url.vercel.app` | `['short-url.vercel.app']` (sem repetir) |
  | `VERCEL_ENV=preview`, `VERCEL_BRANCH_URL=short-url-git-feat-x-rafael.vercel.app`, `VERCEL_PROJECT_PRODUCTION_URL=short-url.vercel.app` | `https://short-url-git-feat-x-rafael.vercel.app` | os dois |
  | `APP_ORIGIN` e as da Vercel juntas | o `APP_ORIGIN` vence | — |
  | `APP_ORIGIN=https://x.com/caminho`, `=https://x.com/?a=1`, `=ftp://x.com`, `=não é url` | `null` | — |
  | `VERCEL_ENV=preview` sem `VERCEL_BRANCH_URL`; `production` sem a URL de produção; `VERCEL_ENV=development`; nada | `null` | — |
- [ ] **Step 2: vermelho.** `npx vitest run src/app/_lib/app-origin.test.ts` → FAIL: módulo inexistente.
- [ ] **Steps finais:** ciclo padrão. Commit: `feat(app): resolve a origem canônica do site com fail-fast`

### Task 10: Chave do rate limit (`rateLimitKey`)

**Quem:** Opus testa → executor implementa. **QA:** não nesta tarefa (exceção da D6d: sem rota que use o arquivo; o QA da Tarefa 15 cobre).

**Contexto:** `security-rate-limit.md` (IP, RC5, `/64`), spec §8.2 ("Chave").

**Files:**
- Test: `src/app/_lib/client-ip.test.ts`
- Create: `src/app/_lib/client-ip.ts`

**Interfaces:**
- Produces: `rateLimitKey(ip: string | undefined, nodeEnv: string | undefined): string | null`.

- [ ] **Step 1: teste (tabela, `nodeEnv = 'production'` salvo indicação):**

  | `ip` | Esperado |
  |---|---|
  | `203.0.113.7` | `203.0.113.7` |
  | `::ffff:177.10.20.30` | `177.10.20.30` |
  | `2804:14c:5b80:9a10:1234:5678:9abc:def0` | `2804:014c:5b80:9a10::/64` |
  | `2804:14C:5B80:9A10::1` | `2804:014c:5b80:9a10::/64` |
  | `2001:db8::1` | `2001:0db8:0000:0000::/64` |
  | `::1` | `0000:0000:0000:0000::/64` |
  | `undefined`, `''`, `999.1.1.1`, `1.2.3`, `01.2.3.4`, `abc`, `1:2:3:4:5:6:7:8:9`, `1::2::3` | `null` |
  | **`203.0.113.7:51234`, `fe80::1%eth0`, `[2001:db8::1]`** | **`null`** (Review Focus 3) |
  | qualquer um, inclusive `undefined`, com `nodeEnv = 'development'` | `'local-dev'` |
- [ ] **Step 2: vermelho.** `npx vitest run src/app/_lib/client-ip.test.ts` → FAIL: módulo inexistente.
- [ ] **Steps finais:** ciclo padrão (item 7: o IP nunca vai para log). Commit:
  `feat(app): normaliza o IP do rate limit com prefixo /64 no IPv6`

### Task 11: Rate limit: números, limitador em memória e indisponível

**Quem:** Opus testa → executor implementa. **QA:** não nesta tarefa (exceção da D6d: sem rota que use o arquivo; o QA da Tarefa 15 cobre).

**Contexto:** `security-rate-limit.md`, `architecture-local-dev.md`, spec §8.2.

**Files:**
- Test: `src/app/_lib/rate-limit.in-memory.test.ts`
- Create: `src/app/_lib/rate-limit.ts` (`RATE_LIMITS`, `RateLimitDecision`, `RateLimiter`, `InMemoryRateLimiter`, `UnavailableRateLimiter`)

**Interfaces:**
- Produces: os tipos da §8.2; `class InMemoryRateLimiter implements RateLimiter { constructor(deps?: { now?: () => number }) }`; `class UnavailableRateLimiter implements RateLimiter`.

- [ ] **Step 1: teste** (relógio injetado):
  - `RATE_LIMITS` igual ao objeto da §8.2;
  - criação: 10 permitidas no mesmo minuto; a 11ª → `{ outcome: 'limited', scope: 'minute', retryAfterSeconds }` com valor entre 1 e 60; 61 s depois da primeira → permitida (janela deslizante);
  - teto diário: 100 criações espalhadas (10 por minuto, minutos diferentes) → a 101ª, num minuto livre → `scope: 'day'`; 24 h depois da primeira → permitida;
  - quando o minuto barra, o contador diário **não** é gasto (a checagem diária só roda se a do minuto passou);
  - redirect: 300 no minuto; a 301ª → `limited`, `scope: 'minute'`;
  - chaves diferentes não se misturam;
  - `UnavailableRateLimiter` → `{ outcome: 'unavailable' }` nos dois métodos.
- [ ] **Step 2: vermelho.** `npx vitest run src/app/_lib/rate-limit.in-memory.test.ts` → FAIL: módulo inexistente.
- [ ] **Steps finais:** ciclo padrão. Commit: `feat(app): define os limites e o rate limiter em memória do npm run dev`

### Task 12: `UpstashRateLimiter`

**Quem:** Opus testa → executor implementa. **QA:** não nesta tarefa (exceção da D6d: sem rota que use o arquivo; o QA da Tarefa 15 cobre).

**Contexto:** `security-rate-limit.md` (timeout, fail-open × fail-closed, previews), spec §8.2.

**Files:**
- Test: `src/app/_lib/rate-limit.upstash.test.ts`
- Modify: `src/app/_lib/rate-limit.ts`

**Interfaces:**
- Produces: `class UpstashRateLimiter implements RateLimiter { constructor(deps: { createPerMinute: Limiter; createPerDay: Limiter; redirectPerMinute: Limiter; now?: () => number }) }`, `type Limiter = { limit(key: string): Promise<{ success: boolean; reset: number; reason?: string }> }`, `rateLimitPrefix(vercelEnv: string | undefined, scope: 'create-min' | 'create-day' | 'redirect'): string`, `createUpstashRateLimiter(env: { url: string; token: string; vercelEnv: string | undefined }): UpstashRateLimiter`.

- [ ] **Step 0 (Opus) 🔎:** `npm pack @upstash/ratelimit@<versão instalada>` no scratchpad e ler no código: a assinatura do construtor (`redis`, `limiter`, `prefix`, `timeout`, `analytics`), o que `limit()` devolve no timeout (`success: true`, `reason: 'timeout'`), a unidade do `reset` (milissegundos desde a época) e se `Ratelimit.slidingWindow` aceita `'1 m'` e `'24 h'`. Anotar no ledger; se divergir da §8.2, levar ao Rafael antes de delegar.
- [ ] **Step 1: teste** (limitadores falsos; `now = 1_000_000`):
  - `success: true` → `allowed`;
  - `success: false, reset: 1_041_500` → `limited`, `retryAfterSeconds: 42`;
  - `success: true, reason: 'timeout'` → `unavailable`, e um `logWarn('rate-limiter-unavailable')`;
  - `limit` rejeita → `unavailable` e o mesmo log; a chave (IP) não aparece em nenhum log;
  - criação: minuto barrado → o limitador diário **não** é chamado, `scope: 'minute'`; minuto ok e dia barrado → `scope: 'day'`; minuto `timeout` → `unavailable` sem chamar o diário;
  - `rateLimitPrefix('production', 'create-min')` → `'short-url:production:create-min'`; `(undefined, 'redirect')` → `'short-url:local:redirect'`; `('preview', 'create-day')` → `'short-url:preview:create-day'`.
- [ ] **Step 2: vermelho.** `npx vitest run src/app/_lib/rate-limit.upstash.test.ts` → FAIL: `UpstashRateLimiter` inexistente.
- [ ] **Step 3: delegar.** `createUpstashRateLimiter` monta os três `Ratelimit` da §8.2 com o que o Step 0 confirmou; ele não é testado com rede: a prova é o `typecheck` e o preview da Vercel (Tarefa 22).
- [ ] **Steps finais:** ciclo padrão. Commit: `feat(app): aplica o rate limit do Upstash com timeout de 1 s`

### Task 13: Ponto de montagem (`services.ts`)

**Quem:** Opus testa → executor implementa. **QA:** não nesta tarefa (exceção da D6d: sem rota que use o arquivo; o QA da Tarefa 15 cobre).

**Contexto:** `architecture-local-dev.md` (trava 1), `security-rate-limit.md` (RC4), `architecture-layers.md`, spec §4.3.

**Files:**
- Test: `src/app/_lib/services.test.ts`
- Create: `src/app/_lib/services.ts`

**Interfaces:**
- Consumes: Tarefas 1, 2, 4, 6, 7, 9, 11, 12; `LinkService`, `RedirectService`, `UrlValidator` (domínio).
- Produces: `getLinkService()`, `getRedirectService()`, `getClickEventRepository()`, `getRateLimiter()`, `getUrlThreatChecker()`.

- [ ] **Step 1: teste** (`vi.stubEnv`, `vi.resetModules()` e `await import()` a cada caso; espião em `fetch` e no `console`):
  - `NODE_ENV=development` + `USE_LOCAL_FAKES=true` → `InMemoryRateLimiter` e `LocalFakeUrlThreatChecker`;
  - **trava 1:** `NODE_ENV=production` + `USE_LOCAL_FAKES=true`, sem chaves → `UnavailableRateLimiter` e `UnavailableUrlThreatChecker` (os falsos nunca entram fora do `next dev`);
  - `NODE_ENV=development` + `USE_LOCAL_FAKES=TRUE` → não usa os falsos;
  - sem chaves (produção) → indisponíveis; `logError('config-missing', { variable })` **uma vez por variável**, mesmo chamando o *getter* duas vezes; a saída do log não contém nenhum valor de variável;
  - `UPSTASH_REDIS_REST_URL=http://inseguro.example` (sem `https:`), `=não é url` e token `''` → `UnavailableRateLimiter` + log;
  - URL `https://exemplo.upstash.io` e token `x` → `UpstashRateLimiter`, sem nenhuma chamada a `fetch` na construção;
  - `SAFE_BROWSING_API_KEY=k` → `SafeBrowsingUrlThreatChecker`;
  - *memoização:* o mesmo objeto em duas chamadas de cada *getter*;
  - importar o módulo sem `DATABASE_URL` não lança (nenhuma conexão no import).
- [ ] **Step 2: vermelho.** `npx vitest run src/app/_lib/services.test.ts` → FAIL: módulo inexistente.
- [ ] **Step 3: delegar.** Spec §4.3 e o ajuste do quinto *getter*. O `UrlValidator` recebe `resolveAppOrigin(process.env)?.ownHosts ?? []`: sem origem, a action recusa antes de chamar o `create` (§8.3, passo 2; provado na Tarefa 19).
- [ ] **Steps finais:** ciclo padrão. Commit:
  `feat(app): monta os serviços com falsos só no next dev e indisponível sem chave`

### Task 14: Páginas de status (`status-pages.ts`)

**Quem:** Opus testa → executor implementa. **QA:** não nesta tarefa (sem rota; o QA da Tarefa 15 cobre).

**Contexto:** `redirect.md` (Corpo das respostas), `security-core.md` (RC6), spec §8.6.

**Files:**
- Test: `src/app/_lib/status-pages.test.ts`
- Create: `src/app/_lib/status-pages.ts`

**Interfaces:**
- Produces: `StatusPage`, `statusPageResponse(page: StatusPage, opts?: { retryAfterSeconds?: number; head?: boolean }): Response`.

- [ ] **Step 1: teste,** para cada uma das 7 páginas da tabela da §8.6:
  - status exato; corpo com `<html lang="pt-BR">`, `<meta charset="utf-8">`, o título e a frase da tabela, caractere por caractere;
  - `Content-Type: text/html; charset=utf-8` e `Cache-Control: no-store`;
  - sem `<script` (sem diferenciar maiúsculas);
  - link `<a href="/">Criar um novo link</a>` em todas, menos na `limited-preview`; a `limited-preview` tem as três `<meta>` da §8.6;
  - `retryAfterSeconds: 42` → `Retry-After: 42`; sem a opção → sem o header;
  - `head: true` → corpo `null` e os mesmos status e headers.
- [ ] **Step 2: vermelho.** `npx vitest run src/app/_lib/status-pages.test.ts` → FAIL: módulo inexistente.
- [ ] **Steps finais:** ciclo padrão (item 7: nenhuma interpolação; a assinatura nem recebe dado do link). Commit:
  `feat(app): gera as páginas fixas de 404, 410, 429, 503 e da prévia`

### Task 15: Redirect: *handler*, rota `GET`/`HEAD` e testes HTTP

**Quem:** Opus testa (e cria os auxiliares do HTTP) → executor implementa. **QA:** sim (D6d: `src/app/`). Áreas: **redirect**, **headers e páginas**.

**Contexto:** `redirect.md` (inteiro), `security-rate-limit.md`, `data-model.md`, spec §8.4, §8.6, §11 (HTTP).

**Files:**
- Create (Opus): `src/app/_lib/redirect-handler.test.ts`, `tests/http/helpers/database.ts` (cria cliente com `createPrismaClient` para o `shorturl_test`, `TRUNCATE` antes de cada teste, `insertLink(...)` com hash de token fixo e `clickEventsOf(linkId)`), `tests/http/redirect.http.test.ts`
- Create (executor): `src/app/_lib/redirect-handler.ts`, `src/app/[slug]/route.ts`

**Interfaces:**
- Consumes: `RedirectService`, `isValidSlugFormat`, `isPreviewBot`, `classifyDevice`, `extractReferrerHost`, `rateLimitKey`, `statusPageResponse`, `logWarn`/`logError`, os *getters* da Tarefa 13; `ipAddress` de `@vercel/functions`; `after` de `next/server`.
- Produces: `handleRedirect(request: Request, slug: string, method: 'GET' | 'HEAD', deps): Promise<Response>`; `GET` e `HEAD` em `src/app/[slug]/route.ts`.

- [ ] **Step 1: teste unitário** (`InMemoryLinkRepository`, `RedirectService` real e `FixedClock`; rate limiter falso; `scheduleAfter` que guarda as tarefas; `x-real-ip: 203.0.113.7` e `nodeEnv 'production'` salvo indicação):
  - `wp-login.php`, `aB3xZ9`, `.env` → 404, sem chamar o rate limiter nem o repositório;
  - rate limit `limited` com 42 s → 429 com `Retry-After: 42`; `unavailable` → segue (302); sem `x-real-ip` → segue, sem chamar o rate limiter, com `logWarn`;
  - **visita a link ativo** com UA de iPhone e `Referer: https://www.google.com/` → 302, `Location` exato, `Cache-Control: no-store`, corpo vazio; uma tarefa agendada que, executada, grava `{ linkId, deviceType: 'MOBILE', referrerHost: 'google.com' }`;
  - **`/aB3xZ9k?next=https://evil.com` → `Location` igual ao destino gravado** (Review Focus 2);
  - **destino criado pelo `UrlValidator` a partir de `https://exemplo.com/ação?q=a b`** → `Location: https://exemplo.com/a%C3%A7%C3%A3o?q=a%20b` (Review Focus 5);
  - bot (`WhatsApp/2.23.20.0 A`) em link com limite → 200 com a página `limited-preview`, sem `Location`, `clickCount` inalterado, tarefa que grava `BOT` sem referrer; bot em link sem limite → 302 sem incrementar e evento `BOT`;
  - `HEAD` em link com limite → 200 sem corpo; `HEAD` sem limite → 302 com `Location` e sem corpo; `HEAD` nunca agenda tarefa nem incrementa;
  - inexistente → 404 sem tarefa; desativado, expirado e esgotado → 410 com a frase de cada motivo, sem tarefa (RC9);
  - repositório lançando `RepositoryUnavailableError` → 503 com `Retry-After: 30` e log com o `slug`, sem o destino; `Error` qualquer → 503 e log `unexpected-error`;
  - a tarefa agendada com `record` rejeitando **não lança** e loga `click-event-failed` com o `slug`;
  - nenhuma saída de log contém o destino, o IP nem o UA.
- [ ] **Step 2: teste HTTP** (`tests/http/redirect.http.test.ts`, `redirect: 'manual'`):
  - 302 com `Location` e `Cache-Control: no-store`; o `click_count` sobe 1; o evento aparece no banco em até 2 s (o `after()` roda depois da resposta);
  - 404 para slug inexistente e para `/wp-login.php`; 410 para cada motivo, com a frase;
  - `HEAD` não muda o `click_count` nem grava evento;
  - UA de bot num link com limite → 200 com `og:title` neutro, sem `Location` e sem incremento;
  - headers globais (`Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`) nas respostas 404 e 410 do Route Handler.
- [ ] **Step 3: vermelho.** `npx vitest run src/app/_lib/redirect-handler.test.ts` → FAIL: módulo inexistente; `npm run test:http` → FAIL no `redirect.http.test.ts` (a rota não existe e responde o 404 do Next).
- [ ] **Step 4: delegar.** Spec §8.4 e o ajuste 8.4. O `route.ts` só lê o `slug` de `await ctx.params` e chama o *handler* com as dependências reais (`scheduleAfter: after`). O `HEAD` próprio é obrigatório.
- [ ] **Step 5: verificação.** Ciclo padrão mais `npm run test:http` e `npm run test:http` de novo com a linha `export async function HEAD` comentada temporariamente pelo Opus → o teste do `HEAD` falha (prova de que ele protege o link); desfazer.
- [ ] **Step 6: QA.** Antes, o Opus cria pelo banco de dev (`npx prisma studio` ou SQL) um link ativo sem limite, um com limite 1, um expirado e um desativado, todos para `https://example.com/...`, e passa os slugs no pedido. Áreas: redirect, headers e páginas.
- [ ] **Steps finais:** revisão e pausa. Commit:
  `feat(redirect): redireciona com 302 no-store e trata bots, HEAD, 404, 410, 429 e 503`

### Task 16: Rodada de formato do formulário (`parseCreateLinkForm`)

**Quem:** Opus testa → executor implementa. **QA:** não nesta tarefa (exceção da D6d: sem rota que use o arquivo; o QA da Tarefa 20 cobre).

**Contexto:** `link-creation.md` (RC7), `url-validation.md` (P4), `link-lifecycle.md`, `error-map.md`, spec §8.3 ("Rodada de formato").

**Files:**
- Test: `src/app/_lib/create-link-form.test.ts`
- Create: `src/app/_lib/create-link-form.ts`

**Interfaces:**
- Consumes: `CreateLinkInput`, `ExpirationChoice` (domínio).
- Produces: `FormFieldError` (ajuste 8.3), `parseCreateLinkForm(form: FormData): { ok: true; input: CreateLinkInput } | { ok: false; errors: FormFieldError[] }`.

- [ ] **Step 1: teste** (`FormData` montado no teste):
  - `url`: `'  https://exemplo.com  '` → `'https://exemplo.com'`; `''`, `'   '` e campo ausente → `required`; 2049 caracteres → `too-long`; 2048 → aceito;
  - `maxClicks`: `''` e ausente → `null`; `'10 '` → `10`; `'007'` → `7`; `'0'` → `0` (formato ok, o domínio recusa); `'10abc'`, `'1e3'`, `'-5'`, `'2.5'` → `not-integer`;
  - expiração: nenhum campo → `{ kind: 'none' }`; `' 7d '` → `{ kind: 'duration', duration: '7d' }`; `'2h'` → `invalid-duration`; `'2026-10-30'` → `{ kind: 'end-of-day', date: '2026-10-30' }`; `'2026-02-30'`, `'30/10/2026'`, `'2026-13-01'` → `invalid-date`; duração e data juntas → `both`;
  - erros juntos: `url` vazia + `maxClicks 'x'` + duração e data → 3 erros, um por campo, na ordem `url`, `maxClicks`, `expiration`;
  - **forjados** (Review Focus 1): `url` como `File` (`form.append('url', new Blob(['https://x.com']), 'a.txt')`) → `required`, sem exceção; `maxClicks` como `File` → `not-integer`; `url` repetido → vale o primeiro, sem exceção.
- [ ] **Step 2: vermelho.** `npx vitest run src/app/_lib/create-link-form.test.ts` → FAIL: módulo inexistente.
- [ ] **Steps finais:** ciclo padrão. Commit: `feat(create): valida o formato do formulário juntando os erros de todos os campos`

### Task 17: Estado e mensagens da criação (`toCreateLinkErrorState`)

**Quem:** Opus testa → executor implementa. **QA:** não nesta tarefa (exceção da D6d: sem rota que use o arquivo; o QA da Tarefa 20 cobre).

**Contexto:** `error-map.md` (inteiro), `url-validation.md` (B3, texto da R7), spec §8.3 ("Estado").

**Files:**
- Test: `src/app/_lib/create-link-state.test.ts`
- Create: `src/app/_lib/create-link-state.ts`

**Interfaces:**
- Consumes: `FormFieldError` (Tarefa 16), `CreateLinkResult` (domínio).
- Produces: `CreateLinkState` (§8.3); `type CreateLinkFailure = { kind: 'form'; errors: FormFieldError[] } | { kind: 'domain'; result: Exclude<CreateLinkResult, { status: 'created' }> } | { kind: 'rate-limited'; scope: 'minute' | 'day' } | { kind: 'unavailable' } | { kind: 'unexpected' }`; `toCreateLinkErrorState(failure: CreateLinkFailure): Extract<CreateLinkState, { status: 'error' }>`.

- [ ] **Step 1: teste:** **cada linha do `error-map.md`** da `createLink`, com o texto exato:
  - `fieldErrors.url` para `required`, `too-long`, `invalid`, `protocol`, `credentials`, `own-domain`, `not-public` e `ipv6-literal`;
  - `fieldErrors.maxClicks` para `not-integer` e `out-of-range`;
  - `fieldErrors.expiration` para `invalid-date`, `past-date`, `too-far`, `invalid-duration` e `both`;
  - `threat` → `fieldErrors.url` com o texto da R7 e `threatAdvisory: true`; nenhum outro erro tem `threatAdvisory`;
  - `rate-limited` minuto e dia → `message`; `unavailable` e `domain` com `cause` `threat-checker` ou `slug-collisions` → "Não foi possível criar o link agora. Tente em alguns minutos."; `unexpected` → "Algo deu errado. Tente novamente.";
  - erros de campos diferentes juntos → um `fieldErrors` com as três chaves.
- [ ] **Step 2: vermelho.** `npx vitest run src/app/_lib/create-link-state.test.ts` → FAIL: módulo inexistente.
- [ ] **Steps finais:** ciclo padrão (item 5: texto idêntico ao `error-map.md`). Commit:
  `feat(create): traduz os códigos de erro para as mensagens do mapa de erros`

### Task 18: QR code (`qr-code.ts`)

**Quem:** Opus testa → executor implementa. **QA:** não nesta tarefa (exceção da D6d: sem rota que use o arquivo; o QA da Tarefa 21 cobre).

**Contexto:** `link-creation.md` (QR code, P1), `architecture-stack.md` (`qrcode@1.5.4`), spec §8.3 ("QR").

**Files:**
- Test: `src/app/_lib/qr-code.test.ts`
- Create: `src/app/_lib/qr-code.ts`

**Interfaces:**
- Produces: `generateQrCodeDataUrl(shortUrl: string): Promise<string>`.

- [ ] **Step 1: teste:** `generateQrCodeDataUrl('https://short-url.vercel.app/aB3xZ9k')` começa com `data:image/png;base64,`; o PNG decodificado tem 512 × 512 (bytes 16 a 23 do cabeçalho IHDR); a mesma entrada gera o mesmo resultado; `'x'.repeat(5000)` (acima da capacidade) → rejeita.
- [ ] **Step 2: vermelho.** `npx vitest run src/app/_lib/qr-code.test.ts` → FAIL: módulo inexistente.
- [ ] **Steps finais:** ciclo padrão. Commit: `feat(app): gera o QR code em PNG de 512 px`

### Task 19: *Handler* e Server Action da criação

**Quem:** Opus testa → executor implementa. **QA:** não nesta tarefa (a action ainda não tem tela; o QA da Tarefa 20 cobre).

**Contexto:** `link-creation.md` (Fluxo, P1), `error-map.md`, `security-rate-limit.md` (fail-closed), `security-core.md` (CSRF), spec §8.3 ("Server Action").

**Files:**
- Test: `src/app/_lib/create-link-handler.test.ts`
- Create: `src/app/_lib/create-link-handler.ts`, `src/app/actions/create-link.ts`

**Interfaces:**
- Consumes: Tarefas 9, 10, 13, 16, 17, 18; `LinkService.create`.
- Produces: `handleCreateLink(form: FormData, deps: { ip: string | undefined; nodeEnv: string | undefined; env: Record<string, string | undefined>; rateLimiter: RateLimiter; linkService: Pick<LinkService, 'create'>; generateQrCode: (url: string) => Promise<string> }): Promise<CreateLinkState>`; `createLink(prev: CreateLinkState, form: FormData): Promise<CreateLinkState>` (`'use server'`).

- [ ] **Step 1: teste** (`env = { APP_ORIGIN: 'http://localhost:3000' }`, `nodeEnv 'production'`, `ip '203.0.113.7'`, `linkService` falso, espião no `console`):
  - rate limit `minute` → "Muitas tentativas. Aguarde um minuto."; `day` → "Você atingiu o limite de links por hoje. Tente amanhã."; `unavailable` → mensagem de indisponível + log; `ip undefined` → a mesma mensagem, o rate limiter **não** é chamado, e há log;
  - o rate limit roda **antes** do formato: formulário vazio com rate limit `allowed` → o rate limiter foi chamado uma vez;
  - `env = {}` (sem origem) → mensagem de indisponível, `logError('app-origin-missing')`, e o `create` **não** é chamado;
  - erro de formato → `fieldErrors`, e o `create` não é chamado;
  - `created` → `shortUrl: 'http://localhost:3000/aB3xZ9k'`, `manageUrl: 'http://localhost:3000/manage/<token>'`, `qrCodeDataUrl` do gerador (chamado com o `shortUrl`), `isInsecureDestination` repassado;
  - **QR falhando** → `success` com `qrCodeDataUrl: null` e `logError('qr-failed')` (P1: depois de gravar, nunca erro);
  - `invalid`, `threat`, `unavailable` (`threat-checker` com log `threat-checker-unavailable`; `slug-collisions` com `logError('slug-collisions')`) → o estado da Tarefa 17;
  - `create` rejeita com `RepositoryUnavailableError` → indisponível + log `database-unavailable`; `Error` qualquer → "Algo deu errado. Tente novamente." + log `unexpected-error`;
  - nenhuma saída de log contém o token, o `manageUrl`, a URL de destino nem o IP.
- [ ] **Step 2: vermelho.** `npx vitest run src/app/_lib/create-link-handler.test.ts` → FAIL: módulo inexistente.
- [ ] **Step 3: delegar.** A action só faz `'use server'`, lê `ipAddress(await headers())`, `process.env.NODE_ENV` e `process.env`, e chama o *handler* com `getRateLimiter()`, `getLinkService()` e `generateQrCodeDataUrl`. Sem `serverActions.allowedOrigins`.
- [ ] **Steps finais:** ciclo padrão. Commit:
  `feat(create): orquestra a criação com rate limit, origem canônica e QR`

### Task 20: Formulário de criação e rótulo da expiração

**Quem:** Opus testa → executor implementa. **QA:** sim (D6d: `src/app/` e `src/components/`). Área: **criação** (sem o card, que é a Tarefa 21).

**Contexto:** `link-creation.md` (P3, P7), `link-lifecycle.md` (P7), `error-map.md`, `url-validation.md` (B3), spec §8.3 ("Campos" e "Tela").

**Files:**
- Test: `src/components/expiration-label.test.ts`
- Create: `src/components/expiration-label.ts`, `src/components/create-link-form.tsx`, `src/components/expiration-field.tsx`
- Modify: `src/app/page.tsx` (troca a home provisória pelo formulário)

**Interfaces:**
- Consumes: `createLink` (Tarefa 19), `CreateLinkState`, `todayInSaoPaulo` (domínio).
- Produces: `formatExpirationLabel(date: string, now: Date): { kind: 'today' } | { kind: 'date'; formatted: string }`; `<CreateLinkForm />` (o card entra na Tarefa 21).

- [ ] **Step 1: teste** (`expiration-label.test.ts`): `('2026-10-30', 2026-10-08T15:00Z)` → `{ kind: 'date', formatted: '30/10/2026' }`; `('2026-10-08', 2026-10-08T15:00Z)` → `{ kind: 'today' }`; `('2026-10-08', 2026-10-09T02:30Z)` → `{ kind: 'today' }` (ainda dia 8 em Brasília); `('2026-10-09', 2026-10-09T02:30Z)` → `date`.
- [ ] **Step 2: vermelho.** `npx vitest run src/components/expiration-label.test.ts` → FAIL: módulo inexistente.
- [ ] **Step 3: delegar.** Tela da §8.3: `useActionState(createLink, { status: 'idle' })`; campos `url`, `maxClicks`, `expirationDuration` e `expirationDate`; *radio* nativo com "sem expiração", "duração" e "até o fim do dia", e o campo não escolhido `disabled`; o botão "Encurtar" vira "Encurtando…" desabilitado com `isPending`; `fieldErrors` embaixo de cada campo e `message` acima do formulário, com `aria-describedby`; com `threatAdvisory`, a linha `Advisory provided by Google` com link para `https://developers.google.com/safe-browsing/v4/advisory` (`rel="noopener noreferrer"`, `target="_blank"`); o rótulo da P7 ("Expira em DD/MM/AAAA às 23:59 (horário de Brasília)" ou "Expira **hoje** às 23:59 (horário de Brasília)") só com data escolhida. Componentes do shadcn/ui. Sem `dangerouslySetInnerHTML`. O `success` mostra, por enquanto, só o `shortUrl` (o card completo é a Tarefa 21).
- [ ] **Step 4: verificação.** Ciclo padrão mais `npm run build`; o `home.http.test.ts` da fatia 1 é atualizado pelo Opus para o novo conteúdo (título `short-url`, `<form`), sem tirar os outros casos.
- [ ] **Step 5: QA.** Área: criação (os cenários de recusa, de aceite, de lista de bloqueio, de valores estranhos, de texto hostil, do rate limit e do duplo clique do `agent.md` do QA).
- [ ] **Steps finais:** revisão e pausa. Commit: `feat(create): cria o formulário com expiração em Brasília e erros por campo`

### Task 21: Card do resultado (token, QR, copiar, `beforeunload`)

**Quem:** executor implementa; **sem teste automatizado** (componente de cliente: a spec §11 põe a tela no roteiro manual e no QA). **QA:** sim. Área: **criação** (o card).

**Contexto:** `link-creation.md` (Token, P1, P5), `security-token.md`, spec §8.3 ("Tela").

**Files:**
- Create: `src/components/link-result-card.tsx`
- Modify: `src/components/create-link-form.tsx` (mostra o card no `success`)

**Interfaces:**
- Consumes: `Extract<CreateLinkState, { status: 'success' }>`.

- [ ] **Step 1: delegar** (pedido com a lista de comportamentos abaixo como critério de aceite):
  - link de gestão **acima** do link curto, com borda de alerta e o aviso "guarde este link: não há recuperação" (P5-C);
  - `beforeunload` ligado enquanto o link de gestão não foi copiado e removido no primeiro "copiar" dele (P5-B);
  - "copiar" com `navigator.clipboard.writeText` e retorno visual ("Copiado");
  - `<img>` do QR com `alt` descritivo e "baixar QR" com `<a href={qrCodeDataUrl} download="qr-<slug>.png">`; com `qrCodeDataUrl === null`, a mensagem "Não foi possível gerar o QR code" no lugar;
  - aviso "este destino não usa conexão segura" quando `isInsecureDestination`;
  - nada do token em `localStorage`, `sessionStorage`, cookie ou `console`.
- [ ] **Step 2: verificação.** `npm test`, `npm run lint`, `npm run typecheck`, `npm run build`; `grep -rn "localStorage\|sessionStorage\|document.cookie\|console\." src/components/link-result-card.tsx` → nada.
- [ ] **Step 3: QA.** Área: criação, com foco no card: copiar, baixar, recarregar descarta o card e o token não volta, texto hostil escapado.
- [ ] **Step 4: roteiro manual do Rafael** (spec §11): `beforeunload` antes e depois de copiar; F5 descarta o card; QR lido pela câmera do celular abre o link curto.
- [ ] **Steps finais:** revisão e pausa. Commit: `feat(create): mostra o card com o token uma única vez, QR e cópia`

### Task 22: Fim da fatia: QA, roteiro manual, revisão e PR

**Quem:** Opus e Rafael juntos. **QA:** sim (passada de fim de fatia). Áreas: **criação**, **redirect**, **headers e páginas**.

- [ ] **Step 1: QA da fatia** (fluxo inteiro: criar → copiar → abrir o link curto → 302; limite 1 → 410 no segundo acesso; rate limit do redirect e da criação com o limitador em memória).
- [ ] **Step 2: roteiro manual** (spec §11): criar com cada combinação de opções; aviso `http:`; aviso da R7 com `https://testsafebrowsing.appspot.com/s/phishing.html` (falso local); copiar e baixar; `beforeunload`; F5; QR pela câmera.
- [ ] **Step 3: revisão da branch** (D5) com o Rafael: `git diff main...feat/mvp-2-create-redirect`, checklist D7 na branch, requisitos da tabela "Rastreabilidade".
- [ ] **Step 4: documentação.** Marcar como `Implementado` na §16 da spec os requisitos que esta fatia fecha; registrar na spec o que as tarefas mudaram no "como" (🔎, ex.: a lista dos erros de conexão, o `$queryRaw` se o Prisma dividir o UPDATE); atualizar o `HANDOFF.md`.
- [ ] **Step 5: preview da Vercel** (com push autorizado): criar um link com as chaves reais; `https://testsafebrowsing.appspot.com/s/phishing.html` recusado pelo **Google de verdade**; 11 criações seguidas → a 11ª recusada pelo Upstash; o redirect do preview funciona.
- [ ] **Step 6: PR** `feat: criação de links e redirect com rate limit e Safe Browsing`; o Rafael lê o "Files changed", acompanha o CI e faz o merge com o ✓.
- [ ] **Step 7: produção:** o mesmo roteiro curto do Step 5 em produção; `curl -I` num link curto → 302 com `Cache-Control: no-store`; apagar a branch remota.
